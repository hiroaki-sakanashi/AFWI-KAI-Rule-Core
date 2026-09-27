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
RULE_CORE = ROOT / "rule-core"
RELEASE_ID = "0.14.0-preview-rate-boundary"
SOURCE_SET_ID = "SRCSET-20260925-RATE-BOUNDARY-001"
SOURCE_SET_SNAPSHOT = "governance/source-set-snapshots/source-set-2026-09-25-rate-boundary-001.yaml"


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_instance(path: Path):
    if path.suffix in {".yaml", ".yml"}:
        return load_yaml(path)
    return json.loads(path.read_text(encoding="utf-8"))


def validate(instance_path: Path, schema_path: Path) -> None:
    instance = load_instance(instance_path)
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda item: list(item.path))
    if errors:
        raise AssertionError(f"{instance_path}: {errors[0].message} at {list(errors[0].path)}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique(values, label: str) -> set[str]:
    values = list(values)
    assert len(values) == len(set(values)), f"Duplicate {label}"
    return set(values)


def main() -> None:
    subprocess.run([sys.executable, str(RULE_CORE / "pipeline/generate-rate-artifacts.py")], cwd=ROOT, check=True)
    schema_pairs = [
        ("governance/source-register.yaml", "schemas/source-register.schema.json"),
        ("governance/source-fragment-register.yaml", "schemas/source-fragment-register.schema.json"),
        ("governance/coverage.yaml", "schemas/coverage.schema.json"),
        ("governance/rule-id-registry.yaml", "schemas/rule-id-registry.schema.json"),
        ("governance/decisions.yaml", "schemas/decision.schema.json"),
        ("governance/unresolved.yaml", "schemas/unresolved.schema.json"),
        ("governance/traceability.yaml", "schemas/traceability.schema.json"),
        ("governance/field-ownership.yaml", "schemas/field-ownership.schema.json"),
        (SOURCE_SET_SNAPSHOT, "schemas/source-set-snapshot.schema.json"),
        ("data/emi-components.yaml", "schemas/emi-components.schema.json"),
        ("data/rates.yaml", "schemas/rates.schema.json"),
        ("data/state-and-event-ids.yaml", "schemas/state-event-ids.schema.json"),
        ("tests/rule-vectors/emi.yaml", "schemas/rule-vector.schema.json"),
        ("tests/rule-vectors/emi-double-count-candidates.yaml", "schemas/rule-vector.schema.json"),
        ("tests/rule-vectors/rates.yaml", "schemas/rule-vector.schema.json"),
        ("tests/rule-vectors/rate-boundary-candidates.yaml", "schemas/rule-vector.schema.json"),
        ("generated/digital/emi.json", "schemas/digital-contract.schema.json"),
        ("generated/digital/emi-manifest.json", "schemas/generated-manifest.schema.json"),
        ("generated/digital/rates.json", "schemas/rates-digital-contract.schema.json"),
        ("generated/digital/rates-manifest.json", "schemas/generated-manifest.schema.json"),
        ("generated/reviews/rate-boundary-candidate-owner-review.json", "schemas/rate-boundary-owner-review.schema.json"),
    ]
    for instance, schema in schema_pairs:
        validate(RULE_CORE / instance, RULE_CORE / schema)

    sources = load_yaml(RULE_CORE / "governance/source-register.yaml")["sources"]
    source_ids = unique((item["source_id"] for item in sources), "source IDs")
    fragments = load_yaml(RULE_CORE / "governance/source-fragment-register.yaml")["fragments"]
    fragment_ids = unique((item["fragment_id"] for item in fragments), "fragment IDs")
    decisions = load_yaml(RULE_CORE / "governance/decisions.yaml")["decisions"]
    decision_ids = unique((item["decision_id"] for item in decisions), "decision IDs")
    registry = load_yaml(RULE_CORE / "governance/rule-id-registry.yaml")["rules"]
    rule_ids = unique((item["rule_core_id"] for item in registry), "Rule Core IDs")
    deprecated_rule_ids = {item["rule_core_id"] for item in registry if item["status"] == "deprecated"}

    rates_doc = load_yaml(RULE_CORE / "data/rates.yaml")
    assert rates_doc["rule_core_version"] == RELEASE_ID
    assert rates_doc["source_set"] == SOURCE_SET_ID
    rates = rates_doc["rates"]
    rate_ids = unique((item["rate_id"] for item in rates), "rate IDs")
    ids_doc = load_yaml(RULE_CORE / "data/state-and-event-ids.yaml")
    assert ids_doc["rule_core_version"] == RELEASE_ID
    state_ids = unique((item["state_id"] for item in ids_doc["states"]), "state IDs")
    event_ids = unique((item["event_id"] for item in ids_doc["events"]), "event IDs")
    assert rate_ids == {"RATE-SPACE-US", "RATE-SPACE-PRC", "RATE-CYBER-US", "RATE-CYBER-PRC", "RATE-STRATEGIC"}

    for fragment in fragments:
        assert fragment["source_id"] in source_ids
        assert set(fragment.get("rule_core_ids", [])) <= rule_ids
        assert set(fragment.get("decision_ids", [])) <= decision_ids
        assert set(fragment.get("rate_ids", [])) <= rate_ids
        assert set(fragment.get("state_ids", [])) <= state_ids
        assert set(fragment.get("event_ids", [])) <= event_ids

    verified_rate_fragments = [item for item in fragments if item["fragment_id"].startswith(("FRAG-RULE-0910-2-PDF-P3-P4-RATE", "FRAG-RULE-0910-2-PDF-P5-", "FRAG-RULE-0910-2-PDF-P15-RATES", "FRAG-RULE-0910-2-PDF-P16-RATE", "FRAG-RULE-0910-2-PDF-P20-", "FRAG-BOARD-A3-0915-P1-RATE", "FRAG-BOARD-A3-0915-P2-", "FRAG-BOARD-A3-0915-P3-"))]
    assert len(verified_rate_fragments) == 8
    for fragment in verified_rate_fragments:
        assert fragment["transcription_status"] == "verified"
        assert fragment["comparison_result"] == "exact_match"
        records = fragment["independent_transcription_records"]
        assert len(records) == 2
        assert records[0]["normalized_text_sha256"] == records[1]["normalized_text_sha256"] == fragment["normalized_text_sha256"]
        assert hashlib.sha256(fragment["normalized_transcription"].encode("utf-8")).hexdigest() == fragment["normalized_text_sha256"]

    for rate in rates:
        assert rate["state_id"] in state_ids
        assert set(rate["rule_core_ids"]) <= rule_ids
        assert set(rate["source_fragment_ids"]) <= fragment_ids
        assert set(rate["decision_ids"]) <= decision_ids
        assert not (set(rate["rule_core_ids"]) & deprecated_rule_ids)
    for rule in rates_doc["rate_rules"]:
        assert rule["rule_core_id"] in rule_ids
        assert set(rule["source_fragment_ids"]) <= fragment_ids
        assert set(rule.get("decision_ids", [])) <= decision_ids

    vectors_doc = load_yaml(RULE_CORE / "tests/rule-vectors/rates.yaml")
    assert vectors_doc["rule_core_version"] == RELEASE_ID
    assert vectors_doc["source_set"] == SOURCE_SET_ID
    assert vectors_doc["status"] == "approved"
    vector_ids = unique((item["vector_id"] for item in vectors_doc["vectors"]), "rate vector IDs")
    assert len(vector_ids) == 18
    for vector in vectors_doc["vectors"]:
        assert vector["status"] == "approved"
        assert vector["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-23"}
        target_rate_ids = set(vector.get("target_rate_ids", [vector.get("target_rate_id")]))
        target_rate_ids.discard(None)
        assert target_rate_ids and target_rate_ids <= rate_ids
        assert set(vector["rule_core_ids"]) <= rule_ids
        assert not (set(vector["rule_core_ids"]) & deprecated_rule_ids)
        assert set(vector["source_fragment_ids"]) <= fragment_ids
        assert set(vector["decision_ids"]) <= decision_ids
        for event in vector["expected_events"]:
            if "event_id" in event:
                assert event["event_id"] in event_ids

    boundary_vectors_doc = load_yaml(RULE_CORE / "tests/rule-vectors/rate-boundary-candidates.yaml")
    assert boundary_vectors_doc["rule_core_version"] == RELEASE_ID
    assert boundary_vectors_doc["source_set"] == SOURCE_SET_ID
    assert boundary_vectors_doc["status"] == "approved"
    boundary_vectors = boundary_vectors_doc["vectors"]
    boundary_vector_ids = unique((item["vector_id"] for item in boundary_vectors), "rate boundary vector IDs")
    assert len(boundary_vector_ids) == 20
    for vector in boundary_vectors:
        assert vector["status"] == "approved"
        assert vector["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-25"}
        assert set(vector["rule_core_ids"]) <= rule_ids
        assert not (set(vector["rule_core_ids"]) & deprecated_rule_ids)
        assert set(vector["source_fragment_ids"]) <= fragment_ids
        assert set(vector["decision_ids"]) <= decision_ids
        for event in vector["expected_events"]:
            if "event_id" in event:
                assert event["event_id"] in event_ids

    trace = load_yaml(RULE_CORE / "governance/traceability.yaml")["mappings"]
    trace_ids = unique((item["target_id"] for item in trace), "trace target IDs")
    assert rate_ids | state_ids | event_ids | {item["rule_core_id"] for item in rates_doc["rate_rules"]} | vector_ids | boundary_vector_ids <= trace_ids
    for mapping in trace:
        assert set(mapping["source_ids"]) <= source_ids
        assert set(mapping["source_fragment_ids"]) <= fragment_ids
        assert set(mapping["decision_ids"]) <= decision_ids
        assert set(mapping["rule_core_ids"]) <= rule_ids
        assert not (set(mapping["rule_core_ids"]) & deprecated_rule_ids)
    for vector_id in vector_ids:
        mapping = next(item for item in trace if item["target_id"] == vector_id)
        assert mapping["rule_vector_status"] == "approved"
    for vector_id in boundary_vector_ids:
        mapping = next(item for item in trace if item["target_id"] == vector_id)
        assert mapping["rule_vector_status"] == "approved"

    rate_registry = [item for item in registry if item["rule_core_id"].startswith("RC-RATE-")]
    approved_registry_vectors = {
        vector_id
        for item in rate_registry
        for vector_id in item["rule_vector_coverage"]["approved_vector_ids"]
    }
    candidate_registry_vectors = {
        vector_id
        for item in rate_registry
        for vector_id in item["rule_vector_coverage"]["candidate_vector_ids"]
    }
    related_vrc_vector_ids = {
        "RV-RATE-CYBER-DOMINANCE-DETAIL-001",
        "RV-RATE-CYBER-DOMINANCE-EXPIRY-001",
        "RV-INTEL-HAND-REVEAL-001",
        "RV-INTEL-SIGN-HEX-REVEAL-001",
        "RV-INTEL-SQUADRON-SUCCESS-001",
        "RV-INTEL-SQUADRON-FAILURE-001",
        "RV-INTEL-FAILURE-CONSUMES-001",
        "RV-INTEL-LIMIT-001",
        "RV-ENABLER-STRATEGIC-CHAIN-US-SP-03-PASS-001",
        "RV-ENABLER-STRATEGIC-CHAIN-US-SP-03-STC-IW-04-SUCCESS-001",
        "RV-ENABLER-STRATEGIC-CHAIN-US-SP-03-STC-IW-04-FAILURE-001",
        "RV-ENABLER-STRATEGIC-CHAIN-US-IW-04-SOURCE-FAILURE-001",
        "RV-ENABLER-STRATEGIC-CHAIN-US-IW-04-PASS-001",
        "RV-ENABLER-STRATEGIC-CHAIN-US-IW-04-STC-IW-04-SUCCESS-001",
        "RV-ENABLER-STRATEGIC-CHAIN-US-IW-04-STC-IW-04-FAILURE-001",
    }
    assert approved_registry_vectors == vector_ids | boundary_vector_ids | related_vrc_vector_ids
    assert candidate_registry_vectors == set()

    coverage = load_yaml(RULE_CORE / "governance/coverage.yaml")["inventories"]
    rate_coverage = next(item for item in coverage if item["inventory_id"] == "INV-RATES")
    assert rate_coverage["vector_coverage"] == "partial"
    assert rate_coverage["subcounts"]["approved_vectors"] == 40
    assert rate_coverage["subcounts"]["candidate_vectors"] == 0

    issues = load_yaml(RULE_CORE / "governance/unresolved.yaml")["issues"]
    continuing_rate_issue_ids = {
        "ISSUE-RATE-CARD-TRANSCRIPTION-011",
        "ISSUE-RATE-GEOGRAPHY-012",
        "ISSUE-RATE-DISMISSAL-MATRIX-014",
    }
    assert all(item["status"] == "open" for item in issues if item["issue_id"] in continuing_rate_issue_ids)
    assert continuing_rate_issue_ids <= {item["issue_id"] for item in issues}
    boundary_issue = next(item for item in issues if item["issue_id"] == "ISSUE-RATE-BOUNDARY-013")
    assert boundary_issue["status"] == "resolved"
    assert boundary_issue["decision_ids"] == ["DEC-RATE-BOUNDARY-001"]

    human = (RULE_CORE / "generated/rates-reference.md").read_text(encoding="utf-8")
    human_rate_ids = set(re.findall(r"RATE-(?:SPACE|CYBER)-(?:US|PRC)|RATE-STRATEGIC", human))
    digital = json.loads((RULE_CORE / "generated/digital/rates.json").read_text(encoding="utf-8"))
    assert rate_ids == human_rate_ids == set(digital["rateIds"])
    assert state_ids == set(digital["stateIds"])
    assert event_ids == set(digital["eventIds"])
    assert vector_ids | boundary_vector_ids == set(digital["approvedRuleVectorIds"])
    assert set(digital["candidateRuleVectorIds"]) == set()
    assert {item["vector_id"] for item in digital["candidateRuleVectors"]} == set()

    forbidden_terms = ["UI", "UX", "クリック", "アニメーション", "AI判断", "保存方法", "Digital内部状態"]
    checked = [RULE_CORE / "data/rates.yaml", RULE_CORE / "data/state-and-event-ids.yaml", RULE_CORE / "rules/rates.md", RULE_CORE / "tests/rule-vectors/rates.yaml", RULE_CORE / "generated/digital/rates.json"]
    for path in checked:
        content = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in {"UI", "UX"}:
                assert not re.search(rf"\b{term}\b", content), f"Forbidden product term {term} in {path}"
            else:
                assert term not in content, f"Forbidden product term {term} in {path}"

    snapshot = load_yaml(RULE_CORE / SOURCE_SET_SNAPSHOT)
    assert snapshot["source_set_id"] == SOURCE_SET_ID
    snapshot_hashes = {item["source_id"]: item["content_sha256"] for item in snapshot["sources"]}
    assert len(snapshot_hashes) == 20
    actual_hashes = {}
    for source in sources:
        digest = sha256(ROOT / source["relative_path"])
        assert digest == source["content_sha256"]
        actual_hashes[source["source_id"]] = digest
    assert actual_hashes == snapshot_hashes

    manifest = json.loads((RULE_CORE / "generated/digital/rates-manifest.json").read_text(encoding="utf-8"))
    assert manifest["ruleCoreVersion"] == RELEASE_ID
    assert manifest["sourceSet"] == SOURCE_SET_ID
    for artifact in manifest["artifacts"]:
        assert sha256(ROOT / artifact["path"]) == artifact["sha256"]

    generated_paths = [RULE_CORE / "generated/rates-reference.md", RULE_CORE / "generated/digital/rates.json", RULE_CORE / "generated/digital/rates-manifest.json"]
    before = {path: sha256(path) for path in generated_paths}
    subprocess.run([sys.executable, str(RULE_CORE / "pipeline/generate-rate-artifacts.py")], cwd=ROOT, check=True)
    after = {path: sha256(path) for path in generated_paths}
    assert before == after
    subprocess.run([sys.executable, str(RULE_CORE / "pipeline/generate-rate-boundary-candidate-review.py"), "--check"], cwd=ROOT, check=True)

    print("RATE_PROTOTYPE_VALIDATION_OK")
    print(f"rates={sorted(rate_ids)}")
    print(f"rule_core_ids={len(rates_doc['rate_rules'])}")
    print(f"states={len(state_ids)} events={len(event_ids)}")
    print(f"approved_vectors={len(vector_ids)} related_approved_vectors={len(related_vrc_vector_ids)} boundary_approved_vectors={len(boundary_vector_ids)}")
    print(f"verified_rate_fragments={len(verified_rate_fragments)}")
    print(f"sources_hashes_unchanged={len(actual_hashes)}")
    print("generated_reproducible=true")


if __name__ == "__main__":
    main()
