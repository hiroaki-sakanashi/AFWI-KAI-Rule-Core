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
GENERATOR = RC / "pipeline/generate-strategic-rate-response-chain-review.py"
VECTOR = RC / "tests/rule-vectors/strategic-rate-response-chain-candidates.yaml"
REVIEW = RC / "generated/reviews/strategic-rate-response-chain-owner-review.json"
MANIFEST = RC / "generated/digital/strategic-rate-response-chain-manifest.json"
OUTPUTS = [
    RC / "generated/reviews/strategic-rate-response-chain-owner-review.md",
    REVIEW,
    RC / "governance/strategic-rate-response-chain-coverage-report.md",
    MANIFEST,
]
PROTECTED = {
    "tests/rule-vectors/immediate-enablers.yaml": "11f4b5fde7bfe2971e1f52613fef0f8d9f4fa2777c30e54f3a1f833f7b694fe1",
    "tests/rule-vectors/immediate-enablers-expansion.yaml": "98b04938a3034432a798ffcc3ea0a173b26179a4a3459499fb5e5cc1545dd816",
    "tests/rule-vectors/immediate-response-order-candidates.yaml": "a85b07b4855dcac756e704bc12e2bda4f01dda1a2dc4be03e63eac13e13be306",
    "tests/rule-vectors/md.yaml": "32b39bdf4050f49ecf1c7947f3c6ca603a72654dbb45ca9684ed658c79e7306b",
    "tests/rule-vectors/intel.yaml": "5e12e9a47c04e0725acced8e6fd5df110dab088213a9a1e6470291b278be4381",
    "tests/rule-vectors/cyber-dominance-candidates.yaml": "aa0f0810ff2f27683bf4ebbd16dad0ae4e5df21dc64e6c105f7c8f1ae05ef79e",
    "tests/rule-vectors/emi.yaml": "ce3514a6052864c60a2e06f29238ca787acab904cfcfdb2e73585d2bb87eeb8a",
    "tests/rule-vectors/emi-double-count-candidates.yaml": "bb42d910c43801113f57640b7f2e593e9e0fcdf36cf1c1f91b00d31eaa0f1dc1",
    "tests/rule-vectors/rates.yaml": "6bf5abb54ce7412a57a02421919691595749167b4d75da3b50e460b7378f9846",
    "governance/unresolved.yaml": "a5144703aa443c6ff2bb3f3c86f80eed5c195abd172861c300f20f57f08b3285",
}
PRE_APPROVAL_FINGERPRINTS = {
    "RV-ENABLER-STRATEGIC-CHAIN-US-SP-03-PASS-001": "8b5767c9460ecb5685ba3b6bea173ed3b68ec58f0b01b38bee77d552d38b21bf",
    "RV-ENABLER-STRATEGIC-CHAIN-US-SP-03-STC-IW-04-SUCCESS-001": "d92c45790f00d3c6b3f1adc567e559fa898341898d9da845ca53424b649790e8",
    "RV-ENABLER-STRATEGIC-CHAIN-US-SP-03-STC-IW-04-FAILURE-001": "d5bdef6369f315531579c4301a13673e82781fd24c0f97c286b3728b8b470123",
    "RV-ENABLER-STRATEGIC-CHAIN-US-IW-04-SOURCE-FAILURE-001": "743afa4bdf3429dfa08ffe0533f63bebd6e2c90fe6517e862a49a7a996fa2bb3",
    "RV-ENABLER-STRATEGIC-CHAIN-US-IW-04-PASS-001": "e401ce42864623dc6544c125537dfe02fe093dc03c9ecb19620279fb95ffe695",
    "RV-ENABLER-STRATEGIC-CHAIN-US-IW-04-STC-IW-04-SUCCESS-001": "fe9bad39c36b6b58dd43d2864f339c446cb37c021940642e54a19704970bc969",
    "RV-ENABLER-STRATEGIC-CHAIN-US-IW-04-STC-IW-04-FAILURE-001": "80e9cad5cd87aa6797934b3830997d50bb5577efd6e33582b5da3f02da33b5e7",
}


FP_FIELDS = [
    "vector_id", "title", "initial_state", "operation", "fixed_randomness",
    "expected_events", "expected_final_state", "duration", "visibility",
    "interaction_type", "rule_core_ids", "source_fragment_ids", "decision_ids",
]


def normative_fingerprint(vector: dict) -> str:
    payload = {field: vector.get(field) for field in FP_FIELDS}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def main() -> None:
    jsonschema.Draft202012Validator(load_json(RC / "schemas/rule-vector.schema.json")).validate(load_yaml(VECTOR))
    jsonschema.Draft202012Validator(load_json(RC / "schemas/strategic-rate-response-chain-owner-review.schema.json")).validate(load_json(REVIEW))
    jsonschema.Draft202012Validator(load_json(RC / "schemas/generated-manifest.schema.json")).validate(load_json(MANIFEST))

    document = load_yaml(VECTOR)
    vectors = document["vectors"]
    ids = [item["vector_id"] for item in vectors]
    assert document["status"] == "approved" and len(vectors) == 7 and len(set(ids)) == 7
    assert all(item["status"] == "approved" and item["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-25"} for item in vectors)
    assert {item["vector_id"]: normative_fingerprint(item) for item in vectors} == PRE_APPROVAL_FINGERPRINTS

    all_other_ids: set[str] = set()
    for path in (RC / "tests/rule-vectors").glob("*.yaml"):
        if path == VECTOR:
            continue
        value = load_yaml(path)
        all_other_ids |= {item["vector_id"] for item in value.get("vectors", [])}
    assert not (set(ids) & all_other_ids)

    components = {item["component_id"] for item in load_yaml(RC / "data/enablers.yaml")["components"]}
    fragments = {item["fragment_id"] for item in load_yaml(RC / "governance/source-fragment-register.yaml")["fragments"]}
    registry = load_yaml(RC / "governance/rule-id-registry.yaml")["rules"]
    rules = {item["rule_core_id"] for item in registry}
    deprecated = {item["rule_core_id"] for item in registry if item["status"] == "deprecated"}
    state_events = load_yaml(RC / "data/state-and-event-ids.yaml")
    states = {item["state_id"] for item in state_events["states"]}
    events = {item["event_id"] for item in state_events["events"]}
    for vector in vectors:
        assert collect_ids(vector, "COMP-") <= components
        assert collect_ids(vector, "STATE-") <= states
        assert collect_ids(vector, "EVENT-") <= events
        assert set(vector["rule_core_ids"]) <= rules and not (set(vector["rule_core_ids"]) & deprecated)
        assert set(vector["source_fragment_ids"]) <= fragments
        assert vector["interaction_type"] in {"response_window", "automatic_resolution"}
        assert vector["initial_state"]["strategic_rate"] == {"center": 0}
        assert vector["initial_state"]["RED_cyber_rate"] == 2
        assert vector["expected_final_state"]["source_processing_completed_count"] == 1

    source_failure = next(item for item in vectors if item["vector_id"].endswith("SOURCE-FAILURE-001"))
    assert source_failure["fixed_randomness"] == {"US_IW_04_D4": 1}
    assert source_failure["expected_final_state"]["strategic_rate"] == {"center": 0}
    assert not any(event.get("event_id") == "EVENT-RATE-CHANGED" for event in source_failure["expected_events"])
    assert any(event.get("assertion") == "no_response_window_for_COMP_ENABLER_STC_IW_04" for event in source_failure["expected_events"])

    for vector in vectors:
        fixed = vector["fixed_randomness"]
        if vector["vector_id"].startswith("RV-ENABLER-STRATEGIC-CHAIN-US-IW-04"):
            assert isinstance(fixed, dict) and "US_IW_04_D4" in fixed
        if "STC-IW-04-SUCCESS" in vector["vector_id"]:
            assert fixed["STC_IW_04_D4"] == 2
            assert vector["expected_final_state"]["strategic_rate"] == {"direction": "RED_advantage", "value": 1}
            assert sum(event.get("event_id") == "EVENT-RATE-CHANGED" for event in vector["expected_events"]) == 2
        if "STC-IW-04-FAILURE" in vector["vector_id"]:
            assert fixed["STC_IW_04_D4"] == 3
            assert vector["expected_final_state"]["strategic_rate"] == {"direction": "BLUE_advantage", "value": 1}
            assert sum(event.get("event_id") == "EVENT-RATE-CHANGED" for event in vector["expected_events"]) == 1

    review = load_json(REVIEW)
    assert review["vector_count"] == 7 and review["status_counts"] == {"candidate": 0, "approved": 7}
    assert {item["vector_id"] for item in review["vectors"]} == set(ids)
    assert all(item["owner_answer"] == {"answer": "この記述で正しい", "approved_by": "ルール所有者", "approved_at": "2026-09-25"} for item in review["vectors"])
    assert {item["vector_id"]: item["fingerprint_sha256"] for item in review["vectors"]} == PRE_APPROVAL_FINGERPRINTS

    report_historical_snapshot_status(RC, PROTECTED, "strategic-rate-response-chain")

    source_register = load_yaml(RC / "governance/source-register.yaml")
    source_by_id = {item["source_id"]: item for item in source_register["sources"]}
    snapshot = load_yaml(RC / "governance/source-set-snapshots/source-set-2026-09-23-initial.yaml")
    assert len(snapshot["sources"]) == 20
    for item in snapshot["sources"]:
        source = source_by_id[item["source_id"]]
        assert sha(ROOT / source["relative_path"]) == item["content_sha256"] == source["content_sha256"]

    manifest = load_json(MANIFEST)
    for artifact in manifest["artifacts"]:
        assert sha(ROOT / artifact["path"]) == artifact["sha256"], artifact["path"]

    before = [sha(path) for path in OUTPUTS]
    subprocess.run([sys.executable, str(GENERATOR)], check=True)
    middle = [sha(path) for path in OUTPUTS]
    subprocess.run([sys.executable, str(GENERATOR)], check=True)
    after = [sha(path) for path in OUTPUTS]
    assert before == middle == after

    print("PASS approved_vectors=7 coverage=7_covered blocked=0")
    print("PASS schema IDs references deprecated-check D4-purpose event-order manifest reproducibility")
    print("PASS normative fingerprints unchanged sources=20 unchanged unresolved unchanged Digital untouched")


if __name__ == "__main__":
    main()
