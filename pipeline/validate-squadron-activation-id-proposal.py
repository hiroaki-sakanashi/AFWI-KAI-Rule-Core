from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml
from jsonschema import validate


ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
OUT = RC / "generated" / "reviews"
GEN = RC / "pipeline" / "generate-squadron-activation-id-proposal.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aggregate(paths) -> str:
    rows = [f"{p.relative_to(ROOT).as_posix()}\t{sha(p)}" for p in sorted(paths)]
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def ids_from(value: object) -> set[str]:
    return set(re.findall(r"\b(?:RC|STATE|EVENT|COMP|RV|FRAG)-[A-Z0-9-]+\b", json.dumps(value, ensure_ascii=False)))


def main() -> None:
    subprocess.run([sys.executable, str(GEN)], cwd=ROOT, check=True)
    proposal = yaml.safe_load((OUT / "squadron-activation-id-proposal.yaml").read_text(encoding="utf-8"))
    review = json.loads((OUT / "squadron-activation-id-owner-review.json").read_text(encoding="utf-8"))
    assert proposal == review
    assert proposal["normative_authority"] is False
    assert proposal["registration_performed"] is False
    assert proposal["candidate_vectors_created"] == 0
    assert len(proposal["transitions"]) == 16
    assert proposal["id_counts"] == {"rule_core": 4, "state": 7, "event": 8, "total": 19}
    for source in proposal["source_review"]["sources"]:
        assert sha(ROOT / source["path"]) == source["sha256"]

    proposal_ids = {x["id"] for key in ("rule_core_id_proposals", "state_id_proposals", "event_id_proposals") for x in proposal[key]}
    assert len(proposal_ids) == 19
    governed = [
        RC / "governance" / "rule-id-registry.yaml",
        RC / "data" / "state-and-event-ids.yaml",
        RC / "governance" / "component-id-registry.yaml",
        RC / "data" / "rates.yaml",
    ] + sorted((RC / "tests" / "rule-vectors").glob("*.yaml"))
    existing_ids: set[str] = set()
    for path in governed:
        existing_ids |= ids_from(yaml.safe_load(path.read_text(encoding="utf-8")))
    registered = proposal_ids & existing_ids
    assert registered == proposal_ids, f"approved proposal IDs not fully registered: {sorted(proposal_ids - registered)}"

    schema_pairs = [
        (RC / "governance" / "source-register.yaml", RC / "schemas" / "source-register.schema.json"),
        (RC / "governance" / "decisions.yaml", RC / "schemas" / "decision.schema.json"),
        (RC / "governance" / "rule-id-registry.yaml", RC / "schemas" / "rule-id-registry.schema.json"),
        (RC / "data" / "state-and-event-ids.yaml", RC / "schemas" / "state-event-ids.schema.json"),
        (RC / "data" / "squadron-activation.yaml", RC / "schemas" / "squadron-activation.schema.json"),
        (RC / "governance" / "coverage.yaml", RC / "schemas" / "coverage.schema.json"),
        (RC / "governance" / "traceability.yaml", RC / "schemas" / "traceability.schema.json"),
        (RC / "governance" / "field-ownership.yaml", RC / "schemas" / "field-ownership.schema.json"),
    ]
    for document_path, schema_path in schema_pairs:
        validate(yaml.safe_load(document_path.read_text(encoding="utf-8")), json.loads(schema_path.read_text(encoding="utf-8")))

    rule_registry = yaml.safe_load((RC / "governance" / "rule-id-registry.yaml").read_text(encoding="utf-8"))["rules"]
    assert len({x["rule_core_id"] for x in rule_registry}) == len(rule_registry)

    source_register = yaml.safe_load((RC / "governance" / "source-register.yaml").read_text(encoding="utf-8"))
    a4 = next(x for x in source_register["sources"] if x["source_id"] == "SRC-BOARD-A4-0815-01")
    assert a4["canonical_record"] is True
    assert {"canonical_record", "published_normative_source"} <= set(a4["source_roles"])

    decisions = yaml.safe_load((RC / "governance" / "decisions.yaml").read_text(encoding="utf-8"))["decisions"]
    assert len({x["decision_id"] for x in decisions}) == len(decisions)
    visibility_decision = next(x for x in decisions if x["decision_id"] == "DEC-SQUADRON-ACTIVATION-VISIBILITY-001")
    assert visibility_decision["approved_by"] == "ルール所有者" and visibility_decision["status"] == "approved"
    assert visibility_decision["affected_rule_core_ids"] == [
        "RC-SQUADRON-DEPLOYMENT-001", "RC-SQUADRON-ACTIVATION-001", "RC-SQUADRON-GENERATION-001", "RC-SQUADRON-RETURN-001"
    ]

    activation = yaml.safe_load((RC / "data" / "squadron-activation.yaml").read_text(encoding="utf-8"))
    assert {x["rule_core_id"] for x in activation["rule_core_ids"]} == {x["id"] for x in proposal["rule_core_id_proposals"]}
    assert {x["component_id"] for x in activation["application_examples"]} == {"COMP-SQUADRON-STC-SQ-04", "COMP-SQUADRON-STC-SQ-13"}
    assert all(x["status"] == "approved" for x in activation["application_examples"])

    state_event = yaml.safe_load((RC / "data" / "state-and-event-ids.yaml").read_text(encoding="utf-8"))
    states = {x["state_id"]: x for x in state_event["states"]}
    events = {x["event_id"]: x for x in state_event["events"]}
    assert len(states) == len(state_event["states"])
    assert len(events) == len(state_event["events"])
    approved_state_ids = {x["id"] for x in proposal["state_id_proposals"]}
    approved_event_ids = {x["id"] for x in proposal["event_id_proposals"]}
    assert approved_state_ids <= states.keys() and approved_event_ids <= events.keys()
    for item in [states[x] for x in approved_state_ids] + [events[x] for x in approved_event_ids]:
        assert item["decision_ids"] == ["DEC-SQUADRON-ACTIVATION-VISIBILITY-001"]
    assert events["EVENT-SQUADRON-TOKENS-GENERATED"]["public_content"] == ["actual_generated_count", "placement_hex_ids"]
    assert {"component_id", "plate_id", "token_ids", "token_to_source_plate_mapping"} <= set(events["EVENT-SQUADRON-TOKENS-GENERATED"]["hidden_from_opponent"])
    assert events["EVENT-SQUADRON-TOKENS-RETURNED"]["public_content"] == ["event_occurrence", "from_hex_ids"]
    assert "token_idsの件数" in events["EVENT-SQUADRON-TOKENS-RETURNED"]["public_projection"]
    assert states["STATE-BASE-SORTIE-CAPACITY"]["visibility"] == "public"
    assert states["STATE-BASE-AIR-OPERATIONS-INFRASTRUCTURE-DAMAGE"]["visibility"] == "public"
    assert states["STATE-BASE-MAINTENANCE-SUPPLY-DAMAGE"]["visibility"] == "public"
    assert states["STATE-SQUADRON-ACTIVATION-IN-PROGRESS"]["internal_fields_excluded"] == ["continuation", "stack", "resume_token"]
    for item in [states[x] for x in approved_state_ids] + [events[x] for x in approved_event_ids]:
        assert not (set(item.get("public_content", [])) & set(item.get("hidden_from_opponent", [])))

    fragment_register = yaml.safe_load((RC / "governance" / "source-fragment-register.yaml").read_text(encoding="utf-8"))
    fragment_ids = {x["fragment_id"] for x in fragment_register["fragments"]}
    used_fragments = {x for x in ids_from(proposal) if x.startswith("FRAG-")}
    assert used_fragments <= fragment_ids, sorted(used_fragments - fragment_ids)

    # The proposal remains a historical pre-approval artifact. The approved visibility contract is held by the decision and registries above.
    assert all(x["visibility"].startswith("not_stated") for group in (proposal["rule_core_id_proposals"], proposal["state_id_proposals"], proposal["event_id_proposals"]) for x in group)
    assert {x["interaction_type"] for x in proposal["rule_core_id_proposals"]} <= {
        "ordered_setup", "sequential_action", "automatic_resolution",
        "automatic_resolution; placement choice exists only where the source rule offers multiple legal hexes, then sequential_action",
    }
    text = json.dumps(proposal, ensure_ascii=False)
    assert "continuation/stack/resume tokenは含めない" in text
    assert "Y-9G" not in text

    manifest_path = OUT / "squadron-activation-id-proposal-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for row in manifest["artifacts"]:
        assert sha(ROOT / row["path"]) == row["sha256"]
    for shared_manifest_name in (
        "emi-manifest.json",
        "geography-generation-boundaries-manifest.json",
        "immediate-enablers-expansion-manifest.json",
        "immediate-response-order-manifest.json",
        "rates-manifest.json",
        "squadrons-manifest.json",
        "vrc-priority-manifest.json",
    ):
        shared_manifest = json.loads((RC / "generated" / "digital" / shared_manifest_name).read_text(encoding="utf-8"))
        for row in shared_manifest.get("artifacts", shared_manifest.get("entries", [])):
            assert sha(ROOT / row["path"]) == row["sha256"], f"stale manifest: {shared_manifest_name}: {row['path']}"

    assert sha(ROOT / "tests" / "aar-base-cost.test.ts") == "7aa0488af2fc81eba034221127604d98be5c584494fe7cdf7679d954e005551c"
    assert sha(RC / "governance" / "unresolved.yaml") == "3c47ef86dd16ae67520d0c7b2b2526a1f971a505753feaff0316fce591f4bf6e"
    approved_vectors = []
    for path in sorted((RC / "tests" / "rule-vectors").glob("*.yaml")):
        approved_vectors.extend(x for x in yaml.safe_load(path.read_text(encoding="utf-8"))["vectors"] if x["status"] == "approved")
    assert len(approved_vectors) == 131
    newly_approved_ids = {"RV-SQUADRON-KJ-500-ACTIVATION-001", "RV-SQUADRON-KQ-200-ACTIVATION-001"}
    pre_existing_vectors = [item for item in approved_vectors if item["vector_id"] not in newly_approved_ids]
    assert len(pre_existing_vectors) == 129
    assert canonical_sha(sorted(pre_existing_vectors, key=lambda item: item["vector_id"])) == "15f47153ab1fa99b2677169013e776e2d9cea15ce7d0e2875d300a928facda2c"
    assert canonical_sha(sorted(approved_vectors, key=lambda item: item["vector_id"])) == "e85311eaa7bbbd61f93a116075ad3825df00a6271c74053282f460265d5e37ff"
    assert aggregate((ROOT / "sources").glob("*")) == "cded938f0d8b6523b138d7fca5aa39ad232aea5fa996c869771a93b9d55e31d7"

    before = {p.name: sha(p) for p in OUT.glob("squadron-activation-*")}
    subprocess.run([sys.executable, str(GEN)], cwd=ROOT, check=True)
    after = {p.name: sha(p) for p in OUT.glob("squadron-activation-*")}
    assert before == after
    print("squadron activation registration validation: PASS (19 IDs registered, field-level visibility approved, 0 vectors created, proposal reproducible)")


if __name__ == "__main__":
    main()
