from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
RULE_CORE = ROOT / "rule-core"


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(vector: dict) -> str:
    canonical = json.dumps(vector, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normative_payload_fingerprint(vector: dict) -> str:
    payload = {key: value for key, value in vector.items() if key not in {"status", "approval"}}
    return fingerprint(payload)


def collect_prefixed(value, prefix: str) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for item in value.values():
            found |= collect_prefixed(item, prefix)
    elif isinstance(value, list):
        for item in value:
            found |= collect_prefixed(item, prefix)
    elif isinstance(value, str) and value.startswith(prefix):
        found.add(value)
    return found


def validate_schema(instance_path: Path, schema_path: Path) -> None:
    instance = json.loads(instance_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance),
        key=lambda item: list(item.path),
    )
    if errors:
        raise AssertionError(f"{instance_path}: {errors[0].message} at {list(errors[0].path)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    args = parser.parse_args()

    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    vector_path = RULE_CORE / "tests" / "rule-vectors" / "rates.yaml"
    vectors_doc = load_yaml(vector_path)
    vectors = vectors_doc["vectors"]
    vector_ids = [item["vector_id"] for item in vectors]
    assert len(vectors) == 18
    assert len(vector_ids) == len(set(vector_ids))
    assert vector_ids == baseline["vector_order"]
    assert sha256(vector_path) != baseline["vector_file_sha256"]

    after_full_fingerprints = {item["vector_id"]: fingerprint(item) for item in vectors}
    after_payload_fingerprints = {item["vector_id"]: normative_payload_fingerprint(item) for item in vectors}
    assert after_payload_fingerprints == baseline["normative_payload_fingerprints"]
    assert all(after_full_fingerprints[item] != baseline["full_record_fingerprints"][item] for item in vector_ids)
    assert baseline["legacy_review_fingerprints"] == baseline["full_record_fingerprints"]
    assert vectors_doc["status"] == "approved"
    for vector in vectors:
        assert vector["status"] == "approved"
        assert vector["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-23"}

    registry = load_yaml(RULE_CORE / "governance" / "rule-id-registry.yaml")["rules"]
    rule_ids = {item["rule_core_id"] for item in registry}
    fragments = load_yaml(RULE_CORE / "governance" / "source-fragment-register.yaml")["fragments"]
    fragment_ids = {item["fragment_id"] for item in fragments}
    issues = load_yaml(RULE_CORE / "governance" / "unresolved.yaml")["issues"]
    issue_ids = {item["issue_id"] for item in issues}
    continuing_issue_ids = {
        "ISSUE-RATE-CARD-TRANSCRIPTION-011",
        "ISSUE-RATE-GEOGRAPHY-012",
        "ISSUE-RATE-BOUNDARY-013",
        "ISSUE-RATE-DISMISSAL-MATRIX-014",
    }
    assert continuing_issue_ids <= issue_ids
    assert all(item["status"] == "open" for item in issues if item["issue_id"] in continuing_issue_ids)
    state_events = load_yaml(RULE_CORE / "data" / "state-and-event-ids.yaml")
    state_ids = {item["state_id"] for item in state_events["states"]}
    event_ids = {item["event_id"] for item in state_events["events"]}
    rates = load_yaml(RULE_CORE / "data" / "rates.yaml")["rates"]
    rate_ids = {item["rate_id"] for item in rates}
    trace = load_yaml(RULE_CORE / "governance" / "traceability.yaml")["mappings"]
    trace_by_id = {item["target_id"]: item for item in trace}

    for vector in vectors:
        targets = set(vector.get("target_rate_ids", [vector.get("target_rate_id")])) - {None}
        assert targets <= rate_ids
        assert set(vector["rule_core_ids"]) <= rule_ids
        assert set(vector["source_fragment_ids"]) <= fragment_ids
        assert collect_prefixed(vector.get("initial_public_state", {}), "STATE-") <= state_ids
        assert collect_prefixed(vector.get("expected_public_state", {}), "STATE-") <= state_ids
        assert collect_prefixed(vector["expected_events"], "EVENT-") <= event_ids
        assert vector["vector_id"] in trace_by_id
        mapping = trace_by_id[vector["vector_id"]]
        assert mapping["rule_vector_status"] == "approved"
        assert set(mapping["rule_core_ids"]) == set(vector["rule_core_ids"])
        assert set(mapping["source_fragment_ids"]) == set(vector["source_fragment_ids"])

    rate_registry = [item for item in registry if item["rule_core_id"].startswith("RC-RATE-")]
    registry_approved_ids = {
        vector_id
        for item in rate_registry
        for vector_id in item["rule_vector_coverage"]["approved_vector_ids"]
    }
    registry_candidate_ids = {
        vector_id
        for item in rate_registry
        for vector_id in item["rule_vector_coverage"]["candidate_vector_ids"]
    }
    assert registry_approved_ids == set(vector_ids)
    assert not registry_candidate_ids

    coverage = load_yaml(RULE_CORE / "governance" / "coverage.yaml")["inventories"]
    rate_coverage = next(item for item in coverage if item["inventory_id"] == "INV-RATES")
    assert rate_coverage["vector_coverage"] == "partial"
    assert rate_coverage["subcounts"]["approved_vectors"] == 18
    assert rate_coverage["subcounts"]["candidate_vectors"] == 0
    assert {
        "upper_and_lower_boundary_behavior_pending",
        "enabler_specific_increase_and_decrease_pending",
        "geography_dependent_scenario_branches_pending",
    } <= set(rate_coverage["required_outcomes"])

    metadata_path = RULE_CORE / "generated" / "reviews" / "rates-vector-owner-review.json"
    markdown_path = RULE_CORE / "generated" / "reviews" / "rates-vector-owner-review.md"
    validate_schema(metadata_path, RULE_CORE / "schemas" / "rate-vector-owner-review.schema.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    reviews = metadata["reviews"]
    assert metadata["target"]["vector_file_sha256"] == sha256(vector_path)
    assert {item["vector_id"] for item in reviews} == set(vector_ids)
    assert len(reviews) == 18
    assert len({item["vector_id"] for item in reviews}) == 18
    review_by_id = {item["vector_id"]: item for item in reviews}
    assert {item["fingerprint_sha256"] for item in reviews} == set(baseline["legacy_review_fingerprints"].values())
    assert all(item["status"] == "approved" for item in reviews)
    assert all(item["reviewability"] == "eligible_for_owner_review" for item in reviews)
    for review in reviews:
        vector_id = review["vector_id"]
        assert review["legacy_full_record_fingerprint_before_approval"] == baseline["full_record_fingerprints"][vector_id]
        assert review["full_record_fingerprint"] == after_full_fingerprints[vector_id]
        assert review["normative_payload_fingerprint_before_approval"] == baseline["normative_payload_fingerprints"][vector_id]
        assert review["normative_payload_fingerprint"] == after_payload_fingerprints[vector_id]
        assert {item["issue_id"] for item in review["related_issues"]} <= issue_ids
        assert not any(item["blocking"] for item in review["related_issues"])

    markdown = markdown_path.read_text(encoding="utf-8")
    detail_ids = re.findall(r"^### \d+\. (RV-RATE-[A-Z0-9-]+) —", markdown, flags=re.MULTILINE)
    assert len(detail_ids) == 18
    assert set(detail_ids) == set(vector_ids)
    assert markdown.count("- [x] この記述で正しい") == 18
    assert markdown.count("- [ ] 修正が必要") == 18
    assert markdown.count("- [ ] 保留") == 18
    assert markdown.count("- 確認者：ルール所有者") == 18
    assert markdown.count("- 確認日：2026-09-23") == 18
    assert "本確認票は規範正本ではない" in markdown
    assert "承認結果は元のrule vectorへ反映する" in markdown
    assert "未解決依存がある項目は承認対象外" in markdown

    source_register = load_yaml(RULE_CORE / "governance" / "source-register.yaml")["sources"]
    snapshot = load_yaml(RULE_CORE / "governance" / "source-set-snapshots" / "source-set-2026-09-23-initial.yaml")["sources"]
    snapshot_hashes = {item["source_id"]: item["content_sha256"] for item in snapshot}
    actual_source_hashes = {}
    for source in source_register:
        digest = sha256(ROOT / source["relative_path"])
        assert digest == source["content_sha256"]
        actual_source_hashes[source["source_id"]] = digest
    assert len(actual_source_hashes) == 20
    assert actual_source_hashes == snapshot_hashes
    assert baseline["sources"] == {
        path.relative_to(ROOT).as_posix(): sha256(path)
        for path in sorted((ROOT / "sources").rglob("*")) if path.is_file()
    }

    current_emi = {
        path.relative_to(ROOT).as_posix(): sha256(path)
        for path in sorted(RULE_CORE.rglob("*")) if path.is_file() and "emi" in path.name.lower()
    }
    emi_manifest_path = "rule-core/generated/digital/emi-manifest.json"
    assert {
        path: digest for path, digest in current_emi.items() if path != emi_manifest_path
    } == {
        path: digest for path, digest in baseline["emi"].items() if path != emi_manifest_path
    }
    assert current_emi[emi_manifest_path] != baseline["emi"][emi_manifest_path]
    current_other_vectors = {
        path.relative_to(ROOT).as_posix(): sha256(path)
        for path in [
            RULE_CORE / "tests" / "rule-vectors" / "emi.yaml",
            RULE_CORE / "tests" / "rule-vectors" / "emi-double-count-candidates.yaml",
        ]
    }
    assert current_other_vectors == baseline["other_vectors"]

    generated_paths = [markdown_path, metadata_path]
    before_regeneration = {path: sha256(path) for path in generated_paths}
    subprocess.run(
        [
            sys.executable,
            str(RULE_CORE / "pipeline" / "generate-rate-vector-owner-review.py"),
            "--generated-at",
            metadata["generated_at"],
            "--approval-baseline",
            str(args.baseline),
        ],
        cwd=ROOT,
        check=True,
    )
    after_regeneration = {path: sha256(path) for path in generated_paths}
    assert before_regeneration == after_regeneration

    print("RATE_VECTOR_OWNER_REVIEW_VALIDATION_OK")
    print("vectors=18")
    print("eligible_for_owner_review=18")
    print("blocked=0")
    print("traceability_errors=0")
    print("normative_payload_fingerprints_before_after_match=18")
    print("full_record_fingerprints_changed=18")
    print("all_vectors_approved=true")
    print("approved_by_and_at_valid=18")
    print("continuing_rate_issues_open=4")
    print("emi_payload_and_vector_files_unchanged={}".format(len(current_emi) - 1))
    print("emi_manifest_shared_traceability_hash_refreshed=true")
    print("sources_hashes_unchanged={}".format(len(actual_source_hashes)))
    print("review_generated_reproducible=true")


if __name__ == "__main__":
    main()
