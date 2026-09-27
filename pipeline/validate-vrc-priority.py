from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
VECTOR_FILES = ["md.yaml", "immediate-enablers.yaml", "intel.yaml", "cyber-dominance-candidates.yaml"]
RELEASE_ID = "0.14.0-preview-rate-boundary"
SOURCE_SET_ID = "SRCSET-20260925-RATE-BOUNDARY-001"
SOURCE_SET_SNAPSHOT = "governance/source-set-snapshots/source-set-2026-09-25-rate-boundary-001.yaml"
UNRESOLVED_SHA256_BY_RELEASE = {
    RELEASE_ID: "3c47ef86dd16ae67520d0c7b2b2526a1f971a505753feaff0316fce591f4bf6e",
}


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.suffix in {".yaml", ".yml"} else json.loads(path.read_text(encoding="utf-8"))


def validate(instance: str, schema: str) -> None:
    doc, spec = load(RC / instance), load(RC / schema)
    errors = sorted(Draft202012Validator(spec).iter_errors(doc), key=lambda x: list(x.path))
    if errors:
        raise AssertionError(f"{instance}: {errors[0].message} at {list(errors[0].path)}")


def unique(values, label):
    values = list(values)
    assert len(values) == len(set(values)), f"duplicate {label}"
    return set(values)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    subprocess.run([sys.executable, str(RC / "pipeline/generate-vrc-priority-artifacts.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(RC / "pipeline/generate-rate-artifacts.py")], cwd=ROOT, check=True)
    pairs = [
        ("governance/source-register.yaml", "schemas/source-register.schema.json"),
        ("governance/source-fragment-register.yaml", "schemas/source-fragment-register.schema.json"),
        ("governance/component-id-registry.yaml", "schemas/component-id-registry.schema.json"),
        ("governance/rule-id-registry.yaml", "schemas/rule-id-registry.schema.json"),
        ("governance/traceability.yaml", "schemas/traceability.schema.json"),
        ("governance/field-ownership.yaml", "schemas/field-ownership.schema.json"),
        ("governance/coverage.yaml", "schemas/coverage.schema.json"),
        ("governance/decisions.yaml", "schemas/decision.schema.json"),
        ("governance/unresolved.yaml", "schemas/unresolved.schema.json"),
        (SOURCE_SET_SNAPSHOT, "schemas/source-set-snapshot.schema.json"),
        ("data/enablers.yaml", "schemas/enablers.schema.json"),
        ("data/rates.yaml", "schemas/rates.schema.json"),
        ("data/state-and-event-ids.yaml", "schemas/state-event-ids.schema.json"),
        *( (f"tests/rule-vectors/{name}", "schemas/rule-vector.schema.json") for name in VECTOR_FILES ),
        ("generated/digital/vrc-priority.json", "schemas/vrc-priority-digital-contract.schema.json"),
        ("generated/digital/vrc-priority-manifest.json", "schemas/generated-manifest.schema.json"),
        ("generated/reviews/md-d4-correction-owner-review.json", "schemas/md-d4-correction-owner-review.schema.json"),
    ]
    for instance, schema in pairs:
        validate(instance, schema)

    sources = load(RC / "governance/source-register.yaml")["sources"]
    source_ids = unique((x["source_id"] for x in sources), "source IDs")
    fragments = load(RC / "governance/source-fragment-register.yaml")["fragments"]
    fragment_ids = unique((x["fragment_id"] for x in fragments), "fragment IDs")
    rules = load(RC / "governance/rule-id-registry.yaml")["rules"]
    rule_ids = unique((x["rule_core_id"] for x in rules), "Rule Core IDs")
    deprecated = {x["rule_core_id"] for x in rules if x["status"] == "deprecated"}
    decisions = load(RC / "governance/decisions.yaml")["decisions"]
    decision_ids = unique((x["decision_id"] for x in decisions), "decision IDs")
    for rule in rules:
        assert set(rule.get("decision_ids", [])) <= decision_ids
    for decision in decisions:
        assert set(decision["affected_rule_core_ids"]) <= rule_ids
        assert set(decision.get("source_ids", [])) <= source_ids
        assert set(decision.get("source_fragment_ids", [])) <= fragment_ids
    component_registry = load(RC / "governance/component-id-registry.yaml")
    component_ids = unique((x["component_id"] for x in component_registry["components"]), "component IDs")
    enablers = load(RC / "data/enablers.yaml")["components"]
    enablers_doc = load(RC / "data/enablers.yaml")
    assert enablers_doc["rule_core_version"] == RELEASE_ID
    assert enablers_doc["source_set"] == SOURCE_SET_ID
    assert component_ids == {x["component_id"] for x in enablers}
    assert len(component_ids) == 18
    for item in enablers:
        assert item["component_id"] == f"COMP-ENABLER-{item['source_card_code']}"
        assert set(item["rule_core_ids"]) <= rule_ids
        assert set(item["source_fragment_ids"]) <= fragment_ids

    ids = load(RC / "data/state-and-event-ids.yaml")
    assert ids["rule_core_version"] == RELEASE_ID
    state_ids = unique((x["state_id"] for x in ids["states"]), "state IDs")
    event_ids = unique((x["event_id"] for x in ids["events"]), "event IDs")
    for item in [*ids["states"], *ids["events"]]:
        assert set(item["rule_core_ids"]) <= rule_ids
        assert not set(item["rule_core_ids"]) & deprecated
        assert set(item["source_fragment_ids"]) <= fragment_ids
        assert set(item.get("decision_ids", [])) <= decision_ids
    approved_vectors = []
    candidate_vectors = []
    for name in VECTOR_FILES:
        doc = load(RC / "tests/rule-vectors" / name)
        assert doc["rule_core_version"] == RELEASE_ID
        assert doc["source_set"] == SOURCE_SET_ID
        assert doc["status"] == "approved"
        for vector in doc["vectors"]:
            assert vector["status"] == "approved"
            assert vector["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-23"}
            approved_vectors.append(vector["vector_id"])
            assert set(vector["rule_core_ids"]) <= rule_ids
            assert not set(vector["rule_core_ids"]) & deprecated
            assert set(vector["source_fragment_ids"]) <= fragment_ids
            assert set(vector.get("decision_ids", [])) <= decision_ids
            for event in vector["expected_events"]:
                if "event_id" in event:
                    assert event["event_id"] in event_ids
    approved_vector_ids = unique(approved_vectors, "approved vector IDs")
    candidate_vector_ids = unique(candidate_vectors, "candidate vector IDs")
    vector_ids = approved_vector_ids | candidate_vector_ids
    assert len(approved_vector_ids) == 35
    assert candidate_vector_ids == set()
    assert len(vector_ids) == 35

    for fragment in fragments:
        assert fragment["source_id"] in source_ids
        assert set(fragment.get("rule_core_ids", [])) <= rule_ids
        assert set(fragment.get("component_ids", [])) <= component_ids | {"COMP-EMI-BLUE", "COMP-EMI-RED"}
        assert set(fragment.get("state_ids", [])) <= state_ids
        assert set(fragment.get("event_ids", [])) <= event_ids

    trace = load(RC / "governance/traceability.yaml")["mappings"]
    trace_ids = unique((x["target_id"] for x in trace), "trace target IDs")
    required_trace = component_ids | vector_ids | {
        "RC-COMBAT-MD-001", "RC-COMBAT-MD-RESOLUTION-001", "RC-COMBAT-MD-LAYERED-001", "RC-COMBAT-MD-VISIBILITY-001", "RC-ENABLER-IMMEDIATE-001", "RC-INTEL-ACTIVITY-001",
        "STATE-MD-LAYER-PENDING", "STATE-MD-ANTI-AIR-AMMUNITION", "STATE-INTEL-CONFIRMATIONS-REMAINING", "STATE-COMPONENT-REVEALED", "STATE-SQUADRON-ACQUIRED",
        "EVENT-MD-DECLARED", "EVENT-MD-PASSED", "EVENT-MD-RESOLVED", "EVENT-IMMEDIATE-ENABLER-PLAYED", "EVENT-INTEL-TARGET-CONFIRMED", "EVENT-COMPONENT-REVEALED", "EVENT-INTEL-ACQUISITION-SUCCEEDED", "EVENT-INTEL-ACQUISITION-FAILED", "EVENT-CYBER-DOMINANCE-EXPIRED",
    }
    assert required_trace <= trace_ids
    for mapping in trace:
        assert set(mapping["source_ids"]) <= source_ids
        assert set(mapping["source_fragment_ids"]) <= fragment_ids
        assert set(mapping["rule_core_ids"]) <= rule_ids
        assert not set(mapping["rule_core_ids"]) & deprecated
        assert set(mapping["decision_ids"]) <= decision_ids

    visibility_decision = next(x for x in decisions if x["decision_id"] == "DEC-COMBAT-MD-VISIBILITY-001")
    assert visibility_decision["category"] == "addition"
    assert visibility_decision["status"] == "approved"
    md_vectors = load(RC / "tests/rule-vectors/md.yaml")["vectors"]
    assert len(md_vectors) == 9
    assert all("RC-COMBAT-MD-VISIBILITY-001" in x["rule_core_ids"] for x in md_vectors)
    assert all("DEC-COMBAT-MD-VISIBILITY-001" in x["decision_ids"] for x in md_vectors)
    assert all("visibility" in x for x in md_vectors)

    unresolved = RC / "governance/unresolved.yaml"
    assert sha(unresolved) == UNRESOLVED_SHA256_BY_RELEASE[RELEASE_ID]
    forbidden = ["nested_response", "resume token", "parent ID", "continuation"]
    normative = [RC / "rules/combat.md", RC / "rules/enablers.md", RC / "rules/detection-and-intel.md", RC / "rules/interaction-and-visibility.md", RC / "data/enablers.yaml"]
    for path in normative:
        text = path.read_text(encoding="utf-8")
        assert all(term not in text for term in forbidden), path
    allowed = {"sequential_action", "response_window", "simultaneous_secret_commit", "ordered_setup", "automatic_resolution", "not_applicable", "not_stated"}
    observed = set(re.findall(r"(?:Interaction-Type: |interaction_type: |`)([a-z_]+)", "\n".join(p.read_text(encoding="utf-8") for p in normative)))
    assert {x for x in observed if x.endswith(("action", "window", "resolution", "stated", "applicable", "commit", "setup"))} <= allowed

    snapshot = load(RC / SOURCE_SET_SNAPSHOT)
    assert snapshot["source_set_id"] == SOURCE_SET_ID
    snapshot_hashes = {x["source_id"]: x["content_sha256"] for x in snapshot["sources"]}
    assert {x["source_id"]: sha(ROOT / x["relative_path"]) for x in sources} == snapshot_hashes

    manifest = load(RC / "generated/digital/vrc-priority-manifest.json")
    assert manifest["ruleCoreVersion"] == RELEASE_ID
    assert manifest["sourceSet"] == SOURCE_SET_ID
    assert all(sha(ROOT / x["path"]) == x["sha256"] for x in manifest["artifacts"])
    outputs = [RC / "generated/vrc-priority-reference.md", RC / "generated/digital/vrc-priority.json", RC / "generated/digital/vrc-priority-manifest.json"]
    before = {p: sha(p) for p in outputs}
    subprocess.run([sys.executable, str(RC / "pipeline/generate-vrc-priority-artifacts.py")], cwd=ROOT, check=True)
    assert before == {p: sha(p) for p in outputs}
    digital = load(RC / "generated/digital/vrc-priority.json")
    assert set(digital["approvedRuleVectorIds"]) == approved_vector_ids
    assert set(digital["candidateRuleVectorIds"]) == candidate_vector_ids
    print("VRC_PRIORITY_VALIDATION_OK")
    print(f"components={len(component_ids)} approved_vectors={len(approved_vector_ids)} candidate_vectors={len(candidate_vector_ids)}")
    print(f"states={len(state_ids)} events={len(event_ids)} sources_unchanged={len(snapshot_hashes)}")
    print("unresolved_unchanged=true generated_reproducible=true")


if __name__ == "__main__":
    main()
