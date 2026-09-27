from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
RULE_CORE = ROOT / "rule-core"


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate(instance_path: Path, schema_path: Path) -> None:
    instance = load_yaml(instance_path) if instance_path.suffix in {".yaml", ".yml"} else json.loads(instance_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(instance)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    schema_pairs = [
        (RULE_CORE / "governance/source-register.yaml", RULE_CORE / "schemas/source-register.schema.json"),
        (RULE_CORE / "governance/source-fragment-register.yaml", RULE_CORE / "schemas/source-fragment-register.schema.json"),
        (RULE_CORE / "governance/coverage.yaml", RULE_CORE / "schemas/coverage.schema.json"),
        (RULE_CORE / "governance/rule-id-registry.yaml", RULE_CORE / "schemas/rule-id-registry.schema.json"),
        (RULE_CORE / "governance/decisions.yaml", RULE_CORE / "schemas/decision.schema.json"),
        (RULE_CORE / "governance/unresolved.yaml", RULE_CORE / "schemas/unresolved.schema.json"),
        (RULE_CORE / "governance/source-set-snapshots/source-set-2026-09-23-initial.yaml", RULE_CORE / "schemas/source-set-snapshot.schema.json"),
        (RULE_CORE / "governance/traceability.yaml", RULE_CORE / "schemas/traceability.schema.json"),
        (RULE_CORE / "data/emi-components.yaml", RULE_CORE / "schemas/emi-components.schema.json"),
        (RULE_CORE / "tests/rule-vectors/emi.yaml", RULE_CORE / "schemas/rule-vector.schema.json"),
        (RULE_CORE / "tests/rule-vectors/emi-double-count-candidates.yaml", RULE_CORE / "schemas/rule-vector.schema.json"),
        (RULE_CORE / "generated/digital/emi.json", RULE_CORE / "schemas/digital-contract.schema.json"),
        (RULE_CORE / "generated/digital/emi-manifest.json", RULE_CORE / "schemas/generated-manifest.schema.json"),
    ]
    for instance, schema in schema_pairs:
        validate(instance, schema)

    sources = load_yaml(RULE_CORE / "governance/source-register.yaml")["sources"]
    source_ids = {item["source_id"] for item in sources}
    fragments = load_yaml(RULE_CORE / "governance/source-fragment-register.yaml")["fragments"]
    fragment_ids = {item["fragment_id"] for item in fragments}
    decisions = load_yaml(RULE_CORE / "governance/decisions.yaml")["decisions"]
    decision_ids = {item["decision_id"] for item in decisions}
    rules = load_yaml(RULE_CORE / "governance/rule-id-registry.yaml")["rules"]
    rule_ids = {item["rule_core_id"] for item in rules}

    components_doc = load_yaml(RULE_CORE / "data/emi-components.yaml")
    components = components_doc["components"]
    component_ids = {item["component_id"] for item in components}
    component_registry = load_yaml(RULE_CORE / "governance/component-id-registry.yaml")
    registered_component_ids = {
        item["component_id"] for item in component_registry["components"]
    }
    all_component_ids = component_ids | registered_component_ids
    assert component_ids == {"COMP-EMI-BLUE", "COMP-EMI-RED"}
    assert len(component_ids) == len(components)
    for component in components:
        assert set(component["source_fragment_ids"]) <= fragment_ids
        assert component["decision_id"] in decision_ids
        assert set(component["rule_core_ids"]) <= rule_ids

    for fragment in fragments:
        assert fragment["source_id"] in source_ids
        assert set(fragment.get("component_ids", [])) <= all_component_ids
        assert set(fragment.get("decision_ids", [])) <= decision_ids
        assert set(fragment.get("rule_core_ids", [])) <= rule_ids

    for decision in decisions:
        assert set(decision["affected_rule_core_ids"]) <= rule_ids
        assert set(decision.get("applies_to_component_ids", [])) <= all_component_ids
        assert set(decision.get("source_ids", [])) <= source_ids
        assert set(decision.get("source_fragment_ids", [])) <= fragment_ids

    vectors_doc = load_yaml(RULE_CORE / "tests/rule-vectors/emi.yaml")
    candidate_vectors_doc = load_yaml(RULE_CORE / "tests/rule-vectors/emi-double-count-candidates.yaml")
    assert vectors_doc["status"] == "approved"
    assert candidate_vectors_doc["status"] == "candidate"
    approved_vector_ids = {
        "RV-EMI-BELOW-THRESHOLD-001",
        "RV-EMI-AT-THRESHOLD-001",
        "RV-EMI-DOUBLE-COUNT-001",
        "RV-EMI-EXCLUDED-MARKERS-001",
        "RV-EMI-DIS-EFFECT-001",
        "RV-EMI-CONDITION-CEASES-001",
    }
    candidate_vector_ids = {
        "RV-EMI-DOUBLE-COUNT-ELECTRONIC-WARFARE-AIRCRAFT-001",
        "RV-EMI-DOUBLE-COUNT-MD-SHIP-001",
        "RV-EMI-DOUBLE-COUNT-MD-ADA-001",
    }
    approved_content_fingerprints = {
        "RV-EMI-BELOW-THRESHOLD-001": "b80d2005af6cf52e6a970418def6e1d183ff6c96c4e7529b0f7bb16b50423a6f",
        "RV-EMI-AT-THRESHOLD-001": "99b74f245d5f8bc993f791916076cfc263cd0fe0fe12973e8c62f73e11152aa5",
        "RV-EMI-DOUBLE-COUNT-001": "3c8b378d175abcc7f345249160f0722b92fb78c198efe1d7a785bfbcf5edf6e8",
        "RV-EMI-EXCLUDED-MARKERS-001": "84fc041278417571a674aadb449082fa4c8068f409afd555aaa36d7e3b386514",
        "RV-EMI-DIS-EFFECT-001": "2e2a72ba8d65a1928c0e961ab278c6197e94c82faae4da39ad238dfdeee3af6f",
        "RV-EMI-CONDITION-CEASES-001": "33bdda2292dd694f316a0209aa97655acb579bf63cc1ae1ab7c86602aa8a46ba",
    }
    vector_ids = set()
    for vector in vectors_doc["vectors"]:
        assert vector["vector_id"] not in vector_ids
        vector_ids.add(vector["vector_id"])
        assert set(vector["rule_core_ids"]) <= rule_ids
        assert set(vector["source_fragment_ids"]) <= fragment_ids
        assert set(vector["decision_ids"]) <= decision_ids
        assert vector["status"] == "approved"
        assert vector["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-23"}
        fingerprint_fields = ["vector_id", "initial_state", "operation", "expected_events", "expected_final_state"]
        fingerprint_payload = {field: vector[field] for field in fingerprint_fields}
        fingerprint = hashlib.sha256(
            json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        assert fingerprint == approved_content_fingerprints[vector["vector_id"]]
    assert vector_ids == approved_vector_ids

    for vector in candidate_vectors_doc["vectors"]:
        assert vector["vector_id"] not in vector_ids
        vector_ids.add(vector["vector_id"])
        assert set(vector["rule_core_ids"]) <= rule_ids
        assert set(vector["source_fragment_ids"]) <= fragment_ids
        assert set(vector["decision_ids"]) <= decision_ids
        assert vector["status"] == "candidate"
        assert vector["approval"] == {"approved_by": None, "approved_at": None}
    assert vector_ids == approved_vector_ids | candidate_vector_ids

    trace = load_yaml(RULE_CORE / "governance/traceability.yaml")
    trace_target_ids = set()
    for mapping in trace["mappings"]:
        assert mapping["target_id"] not in trace_target_ids
        trace_target_ids.add(mapping["target_id"])
        assert set(mapping["source_ids"]) <= source_ids
        assert set(mapping["source_fragment_ids"]) <= fragment_ids
        assert set(mapping["decision_ids"]) <= decision_ids
        assert set(mapping["rule_core_ids"]) <= rule_ids
    assert vector_ids <= trace_target_ids

    for rule in rules:
        coverage = rule.get("rule_vector_coverage")
        if coverage and rule["rule_core_id"].startswith("RC-EMI-"):
            assert set(coverage["approved_vector_ids"]) <= approved_vector_ids
            assert set(coverage["candidate_vector_ids"]) <= candidate_vector_ids

    human_text = (RULE_CORE / "generated/emi-components-reference.md").read_text(encoding="utf-8")
    human_ids = set(re.findall(r"COMP-EMI-(?:BLUE|RED)", human_text))
    digital = json.loads((RULE_CORE / "generated/digital/emi.json").read_text(encoding="utf-8"))
    digital_ids = set(digital["componentIds"])
    assert component_ids == human_ids == digital_ids
    assert set(digital["ruleVectorSet"]["approvedVectorIds"]) == approved_vector_ids
    assert set(digital["ruleVectorSet"]["candidateVectorIds"]) == candidate_vector_ids
    assert digital["ruleVectorSet"]["approvedBy"] == "ルール所有者"
    assert digital["ruleVectorSet"]["approvedAt"] == "2026-09-23"

    normative_data_text = (RULE_CORE / "data/emi-components.yaml").read_text(encoding="utf-8")
    digital_text = (RULE_CORE / "generated/digital/emi.json").read_text(encoding="utf-8")
    assert not re.search(r"\b(top|bottom)\b", normative_data_text, re.IGNORECASE)
    assert not re.search(r"\b(top|bottom)\b", digital_text, re.IGNORECASE)

    rules_text = (RULE_CORE / "rules/emi.md").read_text(encoding="utf-8")
    assert not re.search(r"印刷|切り抜き|貼付方法", rules_text)
    forbidden_product_terms = ["UI", "UX", "クリック", "アニメーション", "AI判断", "保存方法", "Digital内部状態"]
    normative_and_test_texts = [
        rules_text,
        normative_data_text,
        (RULE_CORE / "tests/rule-vectors/emi.yaml").read_text(encoding="utf-8"),
        (RULE_CORE / "tests/rule-vectors/emi-double-count-candidates.yaml").read_text(encoding="utf-8"),
        digital_text,
    ]
    for term in forbidden_product_terms:
        for checked_text in normative_and_test_texts:
            if term in {"UI", "UX"}:
                assert not re.search(rf"\b{term}\b", checked_text)
            else:
                assert term not in checked_text

    snapshot = load_yaml(RULE_CORE / "governance/source-set-snapshots/source-set-2026-09-23-initial.yaml")
    snapshot_hashes = {item["source_id"]: item["content_sha256"] for item in snapshot["sources"]}
    assert len(snapshot_hashes) == 20
    actual_hashes = {}
    for source in sources:
        path = ROOT / source["relative_path"]
        digest = sha256(path)
        assert digest == source["content_sha256"]
        actual_hashes[source["source_id"]] = digest
    assert actual_hashes == snapshot_hashes

    manifest = json.loads((RULE_CORE / "generated/digital/emi-manifest.json").read_text(encoding="utf-8"))
    for artifact in manifest["artifacts"]:
        assert sha256(ROOT / artifact["path"]) == artifact["sha256"]

    blue = next(item for item in fragments if item["fragment_id"] == "FRAG-EMI-0811-BLUE-COMPONENT")
    red = next(item for item in fragments if item["fragment_id"] == "FRAG-EMI-0811-RED-COMPONENT")
    for fragment in (blue, red):
        records = fragment["independent_transcription_records"]
        assert len(records) == 2
        assert records[0]["reading"] == records[1]["reading"]
        assert fragment["comparison_result"] == "exact_match"
        assert fragment["transcription_status"] == "verified"

    print("EMI_PROTOTYPE_VALIDATION_OK")
    print(f"components={sorted(component_ids)}")
    print(f"rule_core_ids={sorted(rule_ids)}")
    print(f"approved_vectors={len(approved_vector_ids)}")
    print(f"candidate_vectors={len(candidate_vector_ids)}")
    print(f"sources_hashes_unchanged={len(actual_hashes)}")


if __name__ == "__main__":
    main()
