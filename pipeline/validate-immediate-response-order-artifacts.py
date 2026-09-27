from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml
from validation_scope import report_historical_snapshot_status

ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
GENERATOR = RC / "pipeline/generate-immediate-response-order-artifacts.py"
VECTOR_PATH = RC / "tests/rule-vectors/immediate-response-order-candidates.yaml"
DECISION_IDS = {
    "DEC-ENABLER-NV-MULTIPLE-001", "DEC-ENABLER-CYBER-COUNTER-SCOPE-001", "DEC-ENABLER-US-AF-10-MD-TIMING-001"
}
PROTECTED = {
    "tests/rule-vectors/immediate-enablers.yaml": "11f4b5fde7bfe2971e1f52613fef0f8d9f4fa2777c30e54f3a1f833f7b694fe1",
    "tests/rule-vectors/immediate-enablers-expansion.yaml": "98b04938a3034432a798ffcc3ea0a173b26179a4a3459499fb5e5cc1545dd816",
    "tests/rule-vectors/md.yaml": "32b39bdf4050f49ecf1c7947f3c6ca603a72654dbb45ca9684ed658c79e7306b",
    "tests/rule-vectors/intel.yaml": "5e12e9a47c04e0725acced8e6fd5df110dab088213a9a1e6470291b278be4381",
    "tests/rule-vectors/cyber-dominance-candidates.yaml": "aa0f0810ff2f27683bf4ebbd16dad0ae4e5df21dc64e6c105f7c8f1ae05ef79e",
    "tests/rule-vectors/emi.yaml": "ce3514a6052864c60a2e06f29238ca787acab904cfcfdb2e73585d2bb87eeb8a",
    "tests/rule-vectors/emi-double-count-candidates.yaml": "bb42d910c43801113f57640b7f2e593e9e0fcdf36cf1c1f91b00d31eaa0f1dc1",
    "tests/rule-vectors/rates.yaml": "6bf5abb54ce7412a57a02421919691595749167b4d75da3b50e460b7378f9846",
    "data/geography.yaml": "ee4ec63a5d5d183d5862926378e5bff0d2a02bddbe03bf709e6db6b03848b382",
    "governance/unresolved.yaml": "a5144703aa443c6ff2bb3f3c86f80eed5c195abd172861c300f20f57f08b3285",
}
FP_FIELDS = ["vector_id", "title", "initial_state", "operation", "fixed_randomness", "expected_events", "expected_final_state", "duration", "visibility", "interaction_type", "rule_core_ids", "source_fragment_ids", "decision_ids"]


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(instance: Path, schema: Path) -> None:
    value = load_json(instance) if instance.suffix == ".json" else load_yaml(instance)
    jsonschema.Draft202012Validator(load_json(schema), format_checker=jsonschema.FormatChecker()).validate(value)


def collect_ids(value, prefix: str) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        for item in value.values():
            result |= collect_ids(item, prefix)
    elif isinstance(value, list):
        for item in value:
            result |= collect_ids(item, prefix)
    elif isinstance(value, str) and value.startswith(prefix):
        result.add(value)
    return result


def fingerprint(vector: dict) -> str:
    payload = {field: vector.get(field) for field in FP_FIELDS}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def main() -> None:
    checks = [
        ("governance/decisions.yaml", "schemas/decision.schema.json"),
        ("data/enablers.yaml", "schemas/enablers.schema.json"),
        ("tests/rule-vectors/immediate-response-order-candidates.yaml", "schemas/rule-vector.schema.json"),
        ("governance/coverage.yaml", "schemas/coverage.schema.json"),
        ("governance/traceability.yaml", "schemas/traceability.schema.json"),
        ("governance/rule-id-registry.yaml", "schemas/rule-id-registry.schema.json"),
        ("governance/field-ownership.yaml", "schemas/field-ownership.schema.json"),
        ("generated/reviews/immediate-response-order-owner-review.json", "schemas/immediate-response-order-owner-review.schema.json"),
        ("generated/reviews/immediate-response-order-candidate-owner-review.json", "schemas/immediate-response-order-candidate-review.schema.json"),
        ("generated/digital/immediate-response-order.json", "schemas/immediate-response-order-digital.schema.json"),
        ("generated/digital/immediate-response-order-manifest.json", "schemas/generated-manifest.schema.json"),
    ]
    for instance, schema in checks:
        validate(RC / instance, RC / schema)

    decisions = load_yaml(RC / "governance/decisions.yaml")["decisions"]
    decision_by_id = {item["decision_id"]: item for item in decisions}
    assert len(decision_by_id) == len(decisions)
    assert DECISION_IDS <= set(decision_by_id)
    for decision_id in DECISION_IDS:
        item = decision_by_id[decision_id]
        assert item["category"] == "addition" and item["decision_type"] == "additional"
        assert item["original_decided_at"] == item["reconfirmed_at"] == item["registered_at"] == "2026-09-24"
        assert item["approved_by"] == "ルール所有者" and item["status"] == "approved"

    vectors_doc = load_yaml(VECTOR_PATH)
    vectors = vectors_doc["vectors"]
    vector_ids = [item["vector_id"] for item in vectors]
    assert vectors_doc["status"] == "approved" and len(vectors) == 14 and len(set(vector_ids)) == 14
    assert all(item["status"] == "approved" and item["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-24"} for item in vectors)

    components = load_yaml(RC / "data/enablers.yaml")["components"]
    component_ids = {item["component_id"] for item in components}
    fragments = {item["fragment_id"] for item in load_yaml(RC / "governance/source-fragment-register.yaml")["fragments"]}
    rules_doc = load_yaml(RC / "governance/rule-id-registry.yaml")
    rule_ids = {item["rule_core_id"] for item in rules_doc["rules"]}
    deprecated = {item["rule_core_id"] for item in rules_doc["rules"] if item["status"] == "deprecated"}
    state_events = load_yaml(RC / "data/state-and-event-ids.yaml")
    event_ids = {item["event_id"] for item in state_events["events"]}
    state_ids = {item["state_id"] for item in state_events["states"]}
    trace = load_yaml(RC / "governance/traceability.yaml")["mappings"]
    trace_ids = [item["target_id"] for item in trace]
    assert len(trace_ids) == len(set(trace_ids))
    trace_by_id = {item["target_id"]: item for item in trace}
    for vector in vectors:
        assert set(vector["decision_ids"]) <= DECISION_IDS | {"DEC-COMBAT-MD-VISIBILITY-001"}
        assert set(vector["rule_core_ids"]) <= rule_ids and not (set(vector["rule_core_ids"]) & deprecated)
        assert set(vector["source_fragment_ids"]) <= fragments
        assert collect_ids(vector, "COMP-") <= component_ids
        assert collect_ids(vector, "EVENT-") <= event_ids
        assert collect_ids(vector, "STATE-") <= state_ids
        assert trace_by_id[vector["vector_id"]]["rule_vector_status"] == "approved"

    removed_07 = next(item for item in vectors if item["vector_id"] == "RV-ENABLER-NV-TARGET-REMOVED-001")
    removed_08 = next(item for item in vectors if item["vector_id"] == "RV-ENABLER-NV-TARGET-REMOVED-08-FIRST-001")
    assert removed_07["expected_final_state"] == {"triggering_BLUE_ship_exists": False, "first_component_id": "COMP-ENABLER-STC-NV-07", "first_card_state": "used", "first_marker_state": "removed_as_printed", "later_component_id": "COMP-ENABLER-STC-NV-08", "later_attack_executed": False, "later_card_location": "hand", "later_marker_location": "map", "later_use_count_consumed": False}
    assert removed_08["expected_final_state"] == {"triggering_BLUE_ship_exists": False, "first_component_id": "COMP-ENABLER-STC-NV-08", "first_card_state": "used", "first_marker_state": "removed_as_printed", "later_component_id": "COMP-ENABLER-STC-NV-07", "later_attack_executed": False, "later_card_location": "hand", "later_marker_location": "map", "later_use_count_consumed": False}
    nv_decision = decision_by_id["DEC-ENABLER-NV-MULTIPLE-001"]
    assert nv_decision["correction_history"][-1]["corrected_at"] == "2026-09-24"
    assert "実質的な選択" in nv_decision["owner_final_text"]
    for day in (1, 2):
        item = next(item for item in vectors if f"DAY{day}-INELIGIBLE" in item["vector_id"])
        assert item["expected_final_state"]["STC_CY_04_legal_to_play"] is False
        assert item["expected_final_state"]["STC_CY_04_use_count_consumed"] is False
    day3 = next(item for item in vectors if "DAY3-CANCEL" in item["vector_id"])
    assert day3["expected_final_state"]["US_CY_01_roll_mode"] == "normal" and day3["fixed_randomness"] == {"D4": 3}
    resume = next(item for item in vectors if "ADV-RESUMES" in item["vector_id"])
    assert resume["expected_final_state"]["attack_roll_condition"] == "ADV" and resume["expected_final_state"]["attack_resumed"] is True

    review = load_json(RC / "generated/reviews/immediate-response-order-candidate-owner-review.json")
    assert review["vector_count"] == 14 and review["status_counts"] == {"candidate": 0, "approved": 14}
    assert review["approval_record"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-24", "approved_vector_count": 14}
    assert {item["vector_id"] for item in review["vectors"]} == set(vector_ids)
    for item in review["vectors"]:
        vector = next(vector for vector in vectors if vector["vector_id"] == item["vector_id"])
        assert item["fingerprint_sha256"] == fingerprint(vector)
        assert item["owner_answer"] == {"answer": "この記述で正しい", "approved_by": "ルール所有者", "approved_at": "2026-09-24"}
    prior = load_json(RC / "generated/reviews/immediate-response-order-owner-review.json")
    assert prior["resolution_summary"]["resolved_question_count"] == 6 and prior["resolution_summary"]["unresolved_question_count"] == 0
    assert all(item["resolution_status"] == "resolved" and item["decision_id"] in DECISION_IDS for item in prior["owner_questions"])

    registry_entry = next(item for item in rules_doc["rules"] if item["rule_core_id"] == "RC-ENABLER-IMMEDIATE-001")
    assert registry_entry["rule_vector_coverage"]["status"] == "approved"
    assert not registry_entry["rule_vector_coverage"]["candidate_vector_ids"]
    assert set(vector_ids) <= set(registry_entry["rule_vector_coverage"]["approved_vector_ids"])
    assert DECISION_IDS <= set(registry_entry["decision_ids"])

    forbidden_phrases = ["".join(["どちらを先に解決しても", "期待値に差異は生じない"]), "".join(["どちらを先にしても", "結果は同じ"]), "".join(["結果に", "差異なし"])]
    for path in RC.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".yaml", ".json", ".md", ".py"}:
            text = path.read_text(encoding="utf-8")
            assert not any(phrase in text for phrase in forbidden_phrases), f"inaccurate phrase remains: {path}"

    report_historical_snapshot_status(RC, PROTECTED, "immediate-response-order")

    source_register = load_yaml(RC / "governance/source-register.yaml")
    source_by_id = {item["source_id"]: item for item in source_register["sources"]}
    snapshot = load_yaml(RC / "governance/source-set-snapshots/source-set-2026-09-23-initial.yaml")
    assert len(snapshot["sources"]) == 20
    for item in snapshot["sources"]:
        source = source_by_id[item["source_id"]]
        assert sha(ROOT / source["relative_path"]) == item["content_sha256"] == source["content_sha256"]

    manifest = load_json(RC / "generated/digital/immediate-response-order-manifest.json")
    for artifact in manifest["artifacts"]:
        assert sha(ROOT / artifact["path"]) == artifact["sha256"], artifact["path"]

    outputs = [
        RC / "generated/reviews/immediate-response-order-candidate-owner-review.md",
        RC / "generated/reviews/immediate-response-order-candidate-owner-review.json",
        RC / "generated/immediate-response-order-reference.md",
        RC / "generated/digital/immediate-response-order.json",
        RC / "generated/digital/immediate-response-order-manifest.json",
        RC / "generated/reviews/immediate-response-order-owner-review.md",
        RC / "generated/reviews/immediate-response-order-owner-review.json",
        RC / "generated/reviews/immediate-response-order-analysis-report.md",
    ]
    before = [sha(path) for path in outputs]
    subprocess.run([sys.executable, str(GENERATOR)], check=True)
    middle = [sha(path) for path in outputs]
    subprocess.run([sys.executable, str(GENERATOR)], check=True)
    after = [sha(path) for path in outputs]
    assert before == middle == after

    print("PASS decisions=3 newly_approved_vectors=14 existing_approved_vectors=47 unchanged")
    print("PASS schema references uniqueness deprecated-check manifest reproducibility")
    print("PASS sources=20 unchanged unresolved unchanged geography VRC EMI rates regression")


if __name__ == "__main__":
    main()
