from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
VECTOR = RC / "tests/rule-vectors/squadron-activation-candidates.yaml"
REVIEW = RC / "generated/reviews/squadron-activation-owner-review.json"
DIGITAL = RC / "generated/digital/squadron-activation-candidates.json"
MANIFEST = RC / "generated/digital/squadron-activation-candidates-manifest.json"
GENERATOR = RC / "pipeline/generate-squadron-activation-candidate-review.py"
OUTPUTS = [REVIEW, RC / "generated/reviews/squadron-activation-owner-review.md", DIGITAL, MANIFEST, RC / "governance/squadron-activation-candidate-validation-report.md"]
PRE_EXISTING_APPROVED_BASELINE = "15f47153ab1fa99b2677169013e776e2d9cea15ce7d0e2875d300a928facda2c"
APPROVED_131_BASELINE = "e85311eaa7bbbd61f93a116075ad3825df00a6271c74053282f460265d5e37ff"
PRE_EXISTING_VECTOR_FILES_AGGREGATE = "b3a2dfbb4178a920e04198376ab42720fe8d8fe29d74245f54a373c91ee72340"
UNRESOLVED_SHA = "3c47ef86dd16ae67520d0c7b2b2526a1f971a505753feaff0316fce591f4bf6e"
AAR_TEST_SHA = "b39f261f701b4449bd60d76a9e4c04817f4447779ef1cd629cd4af04a55b1e8d"
IDS = {"RV-SQUADRON-KJ-500-ACTIVATION-001", "RV-SQUADRON-KQ-200-ACTIVATION-001"}
NORMATIVE_FINGERPRINTS = {
    "RV-SQUADRON-KJ-500-ACTIVATION-001": "31e51714a1d7903c27d8c5cfb679faee4f2a56c7fb32f68acb61429b6760901c",
    "RV-SQUADRON-KQ-200-ACTIVATION-001": "8e42cc1b5a053c6371c9f1a728610b8c8b84f0ee23d41960a06a86b015050f92",
}
PRE_APPROVAL_FULL_FINGERPRINTS = {
    "RV-SQUADRON-KJ-500-ACTIVATION-001": "63b8cfc4f0477b7a3c7b715ffb28013f5636acfde53a3192e23eebf8ea8656b8",
    "RV-SQUADRON-KQ-200-ACTIVATION-001": "af60252f8639323a66a896a4c3cf3b18b307a192d1a536aa9229654e4b672eb5",
}
APPROVED_FULL_FINGERPRINTS = {
    "RV-SQUADRON-KJ-500-ACTIVATION-001": "1b998256270c240c5a36e20202efa6238b642f81608e9084193df8e8b756c58b",
    "RV-SQUADRON-KQ-200-ACTIVATION-001": "1b2b001c550386f277f981cf9a1986cf6b6afdd84f1439edae0acef018d1c9bd",
}
FP_FIELDS = ["vector_id", "title", "initial_state", "operation", "fixed_randomness", "expected_events", "expected_final_state", "visibility", "interaction_type", "rule_core_ids", "source_fragment_ids", "decision_ids"]


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def collect_ids(value, prefix: str) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for item in value.values(): found |= collect_ids(item, prefix)
    elif isinstance(value, list):
        for item in value: found |= collect_ids(item, prefix)
    elif isinstance(value, str) and value.startswith(prefix): found.add(value)
    return found


def main() -> None:
    vector_schema = load_json(RC / "schemas/rule-vector.schema.json")
    doc = load_yaml(VECTOR)
    jsonschema.Draft202012Validator(vector_schema).validate(doc)
    review = load_json(REVIEW)
    manifest = load_json(MANIFEST)
    jsonschema.Draft202012Validator(load_json(RC / "schemas/squadron-activation-owner-review.schema.json")).validate(review)
    jsonschema.Draft202012Validator(load_json(RC / "schemas/generated-manifest.schema.json")).validate(manifest)

    vectors = doc["vectors"]
    assert doc["status"] == "approved" and len(vectors) == 2
    assert {v["vector_id"] for v in vectors} == IDS
    assert all(v["status"] == "approved" and v["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-26"} for v in vectors)
    review_by_id = {item["vector_id"]: item for item in review["vectors"]}
    for vector in vectors:
        vector_id = vector["vector_id"]
        assert canonical_sha({key: vector.get(key) for key in FP_FIELDS}) == NORMATIVE_FINGERPRINTS[vector_id]
        assert canonical_sha(vector) == APPROVED_FULL_FINGERPRINTS[vector_id]
        assert review_by_id[vector_id]["fingerprint_sha256"] == NORMATIVE_FINGERPRINTS[vector_id]
        assert review_by_id[vector_id]["pre_approval_full_record_fingerprint_sha256"] == PRE_APPROVAL_FULL_FINGERPRINTS[vector_id]
        assert review_by_id[vector_id]["approved_full_record_fingerprint_sha256"] == APPROVED_FULL_FINGERPRINTS[vector_id]

    all_ids = []
    approved = []
    for path in sorted((RC / "tests/rule-vectors").glob("*.yaml")):
        content = load_yaml(path)
        for vector in content.get("vectors", []):
            all_ids.append(vector["vector_id"])
            if vector.get("status") == "approved": approved.append(vector)
    assert len(all_ids) == len(set(all_ids))
    assert len(approved) == 131
    pre_existing = [v for v in approved if v["vector_id"] not in IDS]
    assert len(pre_existing) == 129
    assert canonical_sha(sorted(pre_existing, key=lambda item: item["vector_id"])) == PRE_EXISTING_APPROVED_BASELINE
    assert canonical_sha(sorted(approved, key=lambda item: item["vector_id"])) == APPROVED_131_BASELINE
    assert manifest["approvedVectorCount"] == 131
    assert manifest["approvedVectorSetFingerprintSha256"] == APPROVED_131_BASELINE
    pre_existing_paths = [p for p in sorted((RC / "tests/rule-vectors").glob("*.yaml")) if p != VECTOR]
    rows = [f"{p.relative_to(ROOT).as_posix()}\t{sha(p)}" for p in pre_existing_paths]
    assert hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest() == PRE_EXISTING_VECTOR_FILES_AGGREGATE

    components = {item["component_id"] for item in load_yaml(RC / "data/squadrons.yaml")["squadrons"]}
    state_events = load_yaml(RC / "data/state-and-event-ids.yaml")
    states = {item["state_id"] for item in state_events["states"]}
    events = {item["event_id"] for item in state_events["events"]}
    fragments = {item["fragment_id"] for item in load_yaml(RC / "governance/source-fragment-register.yaml")["fragments"]}
    rules_data = load_yaml(RC / "governance/rule-id-registry.yaml")["rules"]
    rules = {item["rule_core_id"] for item in rules_data}
    deprecated = {item["rule_core_id"] for item in rules_data if item["status"] == "deprecated"}
    decisions = {item["decision_id"] for item in load_yaml(RC / "governance/decisions.yaml")["decisions"]}

    for vector in vectors:
        assert collect_ids(vector, "COMP-") <= components
        assert collect_ids(vector, "STATE-") <= states
        assert collect_ids(vector, "EVENT-") <= events
        assert set(vector["rule_core_ids"]) <= rules and not (set(vector["rule_core_ids"]) & deprecated)
        assert set(vector["source_fragment_ids"]) <= fragments
        assert set(vector["decision_ids"]) <= decisions
        initial, deployment = vector["initial_state"], vector["initial_state"]["plate_deployment"]
        assert initial["scenario_id"] == "scenario-1-day-1" and initial["day"] == 2
        assert deployment["selected_base_group_id"] == "GUANGDONG" and deployment["selected_base_hex"] == "H2.5"
        assert deployment["input_classification"] == "acceptance_fixture_choice"
        assert deployment["normative_scope"] == "any_legal_prc_base_group"
        assert deployment["legal_base_group_ids"] == ["HAINAN", "GUANGDONG", "HUNAN"]
        assert deployment["does_not_establish_component_home_base"] is True
        assert initial["base_state"]["maintenance_supply_damage"]["damage_level"] == 0
        assert initial["base_state"]["air_operations_infrastructure_damage"]["damage_level"] == 0
        assert initial["base_state"]["sortie_capacity"]["remaining_capacity"] == 6
        assert initial["available_command_stars"]["value"] == 33
        assert initial["token_custody"]["zone"] == "token_pool" and initial["token_custody"]["same_token_on_map"] is False
        assert vector["operation"]["requested_token_count"] == vector["initial_state"]["maximum_generated_tokens"] == 1
        assert vector["operation"]["required_star_cost"] == vector["operation"]["required_sortie_capacity"] == 2
        assert vector["fixed_randomness"] == {"maintenance_D4": 2} and vector["operation"]["random_input_use_count"] == 1
        assert [event["event_id"] for event in vector["expected_events"]] == ["EVENT-SQUADRON-ACTIVATION-DECLARED", "EVENT-SQUADRON-SORTIE-COST-PAID", "EVENT-SQUADRON-MAINTENANCE-RESOLVED", "EVENT-SQUADRON-GROUND-ABORT-RESOLVED", "EVENT-SQUADRON-TOKENS-GENERATED", "EVENT-SQUADRON-ACTIVATION-COMPLETED"]
        final = vector["expected_final_state"]
        assert final["available_command_stars"] == 31 and final["base_sortie_capacity"]["remaining_capacity"] == 4
        assert final["actual_generated_count"] == 1 and final["ground_abort_count"] == 0
        assert final["token_custody"]["from"] == "token_pool" and final["token_custody"]["to"] == "map" and final["token_custody"]["hex_id"] == "H2.5"
        assert final["acquisition_state"] == "unacquired" and final["activation_used_flag"] == "not_applicable"
        assert final["duplicate_generation_of_same_token_legal"] is False and final["normal_operation_candidate_count_for_component_after_generation"] == 0
        hidden = set(vector["visibility"]["opposing_side"]["hidden_while_unacquired"])
        assert {"component_id", "plate_id", "token_id", "token_to_plate_mapping"} <= hidden

    fixture = load_json(ROOT / "audits/20260912-live-turn-01/after.json")["snapshot"]["state"]
    assert fixture["scenarioId"] == "scenario-1-day-1" and fixture["day"] == 2
    assert fixture["stars"]["PRC"]["available"] == 33
    base = fixture["bases"]["GUANGDONG"]
    assert base == {"id": "GUANGDONG", "side": "PRC", "hex": "H2.5", "damage": 0, "sortieCapacity": 6}
    assert "infrastructureDamage" not in base
    for sid, type_id in (("PRC-SQ-KJ-500", "KJ-500"), ("PRC-SQ-KQ-200", "KQ-200")):
        squadron = fixture["squadrons"][sid]
        assert squadron["baseId"] == "GUANGDONG" and squadron["typeId"] == type_id
        assert len(squadron["availableUnitIds"]) == 1 and squadron["destroyedUnitIds"] == [] and squadron["detectedBy"] == []
        assert not any(unit["typeId"] == type_id for unit in fixture["units"].values())

    diagnostic = load_json(ROOT / "audits/20260925-rc-remaining-diagnostics/diagnostics.json")["aar_candidates"]
    assert diagnostic["expected_count"] == 15 and diagnostic["current_count"] == 17
    added = [item for item in diagnostic["rows"] if item["comparison"] == "added_two"]
    assert len(added) == 2
    assert {item["command"]["squadronId"] for item in added} == {"PRC-SQ-KJ-500", "PRC-SQ-KQ-200"}
    assert all(item["command"]["plannedCount"] == 1 and item["costs"]["stars"] == {"from": "available", "to": "baseSortie", "amount": 2, "baseId": "GUANGDONG"} for item in added)
    assert len({item["optionId"] for item in diagnostic["rows"]}) == 17

    assert sha(ROOT / "tests/aar-base-cost.test.ts") == AAR_TEST_SHA
    assert sha(RC / "governance/unresolved.yaml") == UNRESOLVED_SHA
    source_register = load_yaml(RC / "governance/source-register.yaml")
    by_id = {item["source_id"]: item for item in source_register["sources"]}
    snapshot = load_yaml(RC / "governance/source-set-snapshots/source-set-2026-09-23-initial.yaml")
    assert len(snapshot["sources"]) == 20
    for item in snapshot["sources"]:
        source = by_id[item["source_id"]]
        assert sha(ROOT / source["relative_path"]) == item["content_sha256"] == source["content_sha256"]

    digital = load_json(DIGITAL)
    assert {item["vectorId"] for item in digital["vectors"]} == IDS
    manifest = load_json(MANIFEST)
    for artifact in manifest["artifacts"]:
        assert sha(ROOT / artifact["path"]) == artifact["sha256"], artifact["path"]

    before = [sha(path) for path in OUTPUTS]
    subprocess.run([sys.executable, str(GENERATOR)], check=True)
    middle = [sha(path) for path in OUTPUTS]
    subprocess.run([sys.executable, str(GENERATOR)], check=True)
    after = [sha(path) for path in OUTPUTS]
    assert before == middle == after
    print("PASS newly_approved_vectors=2 approved_vectors=131 pre_existing_approved_vectors=129 aar_current=17 aar_expectation_updated=17 historical_expected=15")
    print(f"PASS approved_vector_set_fingerprint={APPROVED_131_BASELINE}")
    print("PASS schema IDs references fixture-legality D4 custody visibility fingerprints manifest reproducibility")
    print("PASS sources=20 unresolved unchanged Digital source untouched")


if __name__ == "__main__":
    main()
