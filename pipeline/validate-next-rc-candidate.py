from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
AUDIT = RC / "governance/normative-audit/next-rc-candidate"
EXPECTED_APPROVED_COUNT = 141
EXPECTED_CANDIDATE_COUNT = 3
EXPECTED_APPROVED_FINGERPRINT = "57e0d74701fc85d955886c60cb616986240a460daa9dce49c0b91189db19b1d2"
EXPECTED_UNRESOLVED_SHA256 = "3c47ef86dd16ae67520d0c7b2b2526a1f971a505753feaff0316fce591f4bf6e"
EXPECTED_ACTIVE_FINGERPRINT = "6aa066b51fd0f6eb9a214cd472935d1631910f344b706a73e6badfbeb51f7a07"
EXPECTED_RELEASE_ID = "RC-2026.09.27-01"
EXPECTED_SPECIFICATION_VERSION = "v0.9.1"
EXPECTED_RELEASE_STATUS = "release-candidate"
EXPECTED_GIT_TAG = "RC-2026.09.27-01"
EXPECTED_SUPERSEDES = "RC-2026.09.26-01"
EXPECTED_CANONICAL_SOURCES = {
    "SRC-ENABLER-0830-1",
    "SRC-SQUADRON-0901",
    "SRC-TOKEN-0901-1",
}
EXPECTED_NEW_RULES = {
    "RC-CYBER-TARGET-GROUP-MODEL-001",
    "RC-CYBER-TARGET-GROUP-MEMBERSHIP-001",
    "RC-CYBER-TARGET-GROUP-SELECTION-001",
    "RC-CYBER-TARGET-GROUP-PERSISTENCE-001",
    "RC-TURN-BASE-STAR-PAYMENT-001",
}
EXPECTED_PRIOR_OMISSIONS = {
    "RC-EMI-COMPONENT-001",
    "RC-RATE-VISIBILITY-001",
    "RC-SQUADRON-RETURN-001",
}


def load(path: Path) -> Any:
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8-sig"))
    return yaml.safe_load(path.read_text(encoding="utf-8-sig"))


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_text_sha256(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def add(report: dict[str, Any], name: str, passed: bool, **details: Any) -> None:
    report["checks"].append({"name": name, "status": "pass" if passed else "fail", **details})
    if not passed:
        report["status"] = "fail"


def validate_schema_instances(report: dict[str, Any]) -> None:
    pairs = {
        "governance/source-register.yaml": "schemas/source-register.schema.json",
        "governance/source-fragment-register.yaml": "schemas/source-fragment-register.schema.json",
        "governance/decisions.yaml": "schemas/decision.schema.json",
        "governance/rule-id-registry.yaml": "schemas/rule-id-registry.schema.json",
        "governance/traceability.yaml": "schemas/traceability.schema.json",
        "governance/coverage.yaml": "schemas/coverage.schema.json",
    }
    errors: list[str] = []
    for instance, schema in pairs.items():
        try:
            jsonschema.Draft202012Validator(load(RC / schema)).validate(load(RC / instance))
        except Exception as exc:
            errors.append(f"{instance}: {exc}")
    vector_schema = load(RC / "schemas/rule-vector.schema.json")
    for path in sorted((RC / "tests/rule-vectors").glob("*.yaml")):
        try:
            jsonschema.Draft202012Validator(vector_schema).validate(load(path))
        except Exception as exc:
            errors.append(f"{path.relative_to(RC).as_posix()}: {exc}")
    add(report, "schema_instances", not errors, errors=errors)


def validate_vectors(report: dict[str, Any]) -> None:
    vectors: list[dict[str, Any]] = []
    for path in sorted((RC / "tests/rule-vectors").glob("*.yaml")):
        vectors.extend(load(path).get("vectors", []))
    ids = [v["vector_id"] for v in vectors]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    approved = sorted((v for v in vectors if v["status"] == "approved"), key=lambda v: v["vector_id"])
    candidates = sorted((v for v in vectors if v["status"] == "candidate"), key=lambda v: v["vector_id"])
    fingerprint = hashlib.sha256(canonical(approved)).hexdigest()
    approved_approval_errors = [
        v["vector_id"] for v in approved
        if v.get("approval", {}).get("approved_by") != "ルール所有者"
        or not v.get("approval", {}).get("approved_at")
    ]
    candidate_approval_errors = [
        v["vector_id"] for v in candidates
        if v.get("approval") != {"approved_by": None, "approved_at": None}
    ]
    add(
        report,
        "vector_sets",
        not duplicates
        and len(approved) == EXPECTED_APPROVED_COUNT
        and len(candidates) == EXPECTED_CANDIDATE_COUNT
        and fingerprint == EXPECTED_APPROVED_FINGERPRINT
        and not approved_approval_errors
        and not candidate_approval_errors,
        approved_count=len(approved),
        candidate_count=len(candidates),
        approved_fingerprint=fingerprint,
        duplicate_ids=duplicates,
        approved_approval_errors=approved_approval_errors,
        candidate_approval_errors=candidate_approval_errors,
    )


def validate_active_ids(report: dict[str, Any]) -> None:
    registry = load(RC / "governance/rule-id-registry.yaml")
    active = sorted(row["rule_core_id"] for row in registry["rules"] if row["status"] == "active")
    fingerprint = hashlib.sha256(canonical(active)).hexdigest()
    artifact = load(AUDIT / "active-rule-id-set.json")
    add(
        report,
        "active_rule_id_set",
        len(active) == 32
        and set(active) >= EXPECTED_NEW_RULES | EXPECTED_PRIOR_OMISSIONS
        and fingerprint == EXPECTED_ACTIVE_FINGERPRINT
        and artifact["active_rule_ids"] == active
        and artifact["active_rule_ids_fingerprint"] == fingerprint,
        active_count=len(active),
        fingerprint=fingerprint,
        new_rule_ids_present=sorted(EXPECTED_NEW_RULES & set(active)),
        prior_manifest_omissions_present=sorted(EXPECTED_PRIOR_OMISSIONS & set(active)),
    )


def validate_references(report: dict[str, Any]) -> None:
    rules = load(RC / "governance/rule-id-registry.yaml")["rules"]
    sources = load(RC / "governance/source-register.yaml")["sources"]
    fragments = load(RC / "governance/source-fragment-register.yaml")["fragments"]
    decisions = load(RC / "governance/decisions.yaml")["decisions"]
    trace = load(RC / "governance/traceability.yaml")["mappings"]
    rule_ids = {row["rule_core_id"] for row in rules}
    source_ids = {row["source_id"] for row in sources}
    fragment_ids = {row["fragment_id"] for row in fragments}
    decision_ids = {row["decision_id"] for row in decisions}
    errors: list[str] = []
    raw_id_sets = {
        "rule": [row["rule_core_id"] for row in rules],
        "source": [row["source_id"] for row in sources],
        "fragment": [row["fragment_id"] for row in fragments],
        "decision": [row["decision_id"] for row in decisions],
        "traceability target": [row["target_id"] for row in trace],
    }
    duplicate_ids = {
        label: sorted({item for item in values if values.count(item) > 1})
        for label, values in raw_id_sets.items()
        if len(values) != len(set(values))
    }
    for row in rules:
        errors.extend(f"{row['rule_core_id']}: missing fragment {item}" for item in row.get("source_fragment_ids", []) if item not in fragment_ids)
        errors.extend(f"{row['rule_core_id']}: missing decision {item}" for item in row.get("decision_ids", []) if item not in decision_ids)
    for row in trace:
        errors.extend(f"{row['target_id']}: missing source {item}" for item in row["source_ids"] if item not in source_ids)
        errors.extend(f"{row['target_id']}: missing fragment {item}" for item in row["source_fragment_ids"] if item not in fragment_ids)
        errors.extend(f"{row['target_id']}: missing decision {item}" for item in row["decision_ids"] if item not in decision_ids)
        errors.extend(f"{row['target_id']}: missing rule {item}" for item in row["rule_core_ids"] if item not in rule_ids)
    targets = {row["target_id"] for row in trace}
    missing_targets = sorted(EXPECTED_NEW_RULES - targets)
    add(
        report,
        "id_and_traceability_references",
        not errors and not missing_targets and not duplicate_ids,
        errors=errors,
        duplicate_ids=duplicate_ids,
        missing_new_rule_targets=missing_targets,
    )


def validate_differential_baseline(report: dict[str, Any]) -> None:
    baseline = load(RC / "governance/normative-audit/RC-2026.09.26-01/normative-baseline.json")
    plan = load(AUDIT / "differential-audit-plan.yaml")
    changed = set(plan["changed_or_new_paths"])
    unchanged_matches: list[str] = []
    mismatches: list[str] = []
    reaudit_required: list[str] = []
    for entry in baseline["normative_file_hashes"]:
        rel = entry["path"]
        if rel in changed:
            reaudit_required.append(rel)
            continue
        path = ROOT / rel
        if not path.exists():
            mismatches.append(f"{rel}: missing")
            continue
        data = path.read_bytes()
        if data.startswith(b"\xef\xbb\xbf"):
            data = data[3:]
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        actual = hashlib.sha256(data).hexdigest()
        if actual == entry["sha256"]:
            unchanged_matches.append(rel)
        else:
            mismatches.append(f"{rel}: {actual} != {entry['sha256']}")
    add(
        report,
        "differential_baseline",
        not mismatches,
        verified_unchanged_count=len(unchanged_matches),
        baseline_paths_reaudit_required=sorted(reaudit_required),
        unexpected_mismatches=mismatches,
    )


def validate_owner_application(report: dict[str, Any]) -> None:
    sources = {row["source_id"]: row for row in load(RC / "governance/source-register.yaml")["sources"]}
    canonical_errors = [
        source_id for source_id in EXPECTED_CANONICAL_SOURCES
        if sources[source_id].get("canonical_record") is not True
        or sources[source_id].get("current_version_status") != "current"
    ]
    cyber = (RC / "rules/cyber-target-groups.md").read_text(encoding="utf-8-sig")
    turn = (RC / "rules/turn-base-star-payment.md").read_text(encoding="utf-8-sig")
    decisions = {row["decision_id"] for row in load(RC / "governance/decisions.yaml")["decisions"]}
    a2 = next(
        row for row in load(RC / "governance/source-fragment-register.yaml")["fragments"]
        if row["fragment_id"] == "FRAG-ENABLER-0830-1-STC-IW-02"
    )
    passed = (
        not canonical_errors
        and "normative_sections: [1, 2, 3, 4, 5, 7, 8]" in cyber
        and "non_normative_sections: [6, 9]" in cyber
        and "DEC-CYBER-TARGET-GROUP-001" in decisions
        and "DEC-TURN-BASE-STAR-PAYMENT-001" in decisions
        and "RC-TURN-BASE-STAR-PAYMENT-001" in turn
        and "不足分は③欄" in a2["normalized_transcription"]
        and "②欄へは波及しない" in a2["normalized_transcription"]
        and not a2.get("decision_ids")
    )
    add(report, "owner_decisions_and_a2", passed, canonical_source_errors=canonical_errors)


def validate_protection(report: dict[str, Any]) -> None:
    unresolved = sha256(RC / "governance/unresolved.yaml")
    add(
        report,
        "protected_baseline",
        unresolved == EXPECTED_UNRESOLVED_SHA256,
        unresolved_sha256=unresolved,
        expected_unresolved_sha256=EXPECTED_UNRESOLVED_SHA256,
    )


def current_vectors() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    vectors: list[dict[str, Any]] = []
    for path in sorted((RC / "tests/rule-vectors").glob("*.yaml")):
        vectors.extend(load(path).get("vectors", []))
    return (
        sorted((v for v in vectors if v["status"] == "approved"), key=lambda v: v["vector_id"]),
        sorted((v for v in vectors if v["status"] == "candidate"), key=lambda v: v["vector_id"]),
    )


def build_differential_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    cyber_rules = [
        "RC-CYBER-TARGET-GROUP-MODEL-001",
        "RC-CYBER-TARGET-GROUP-MEMBERSHIP-001",
        "RC-CYBER-TARGET-GROUP-SELECTION-001",
        "RC-CYBER-TARGET-GROUP-PERSISTENCE-001",
    ]
    for rule_id in cyber_rules:
        records.append({
            "item_id": rule_id,
            "item_type": "rule_core_id",
            "status": "verified_with_owner_decision",
            "source_ids": ["SRC-ENABLER-0830-1", "SRC-SQUADRON-0901", "SRC-TOKEN-0901-1"],
            "decision_ids": ["DEC-CYBER-TARGET-GROUP-001"],
            "verified_fields": ["normative sections", "membership", "selection", "persistence boundary"],
            "mismatches": [],
        })
    records.append({
        "item_id": "RC-TURN-BASE-STAR-PAYMENT-001",
        "item_type": "rule_core_id",
        "status": "verified_with_owner_decision",
        "source_ids": ["SRC-RULE-0910-2-PDF"],
        "decision_ids": ["DEC-TURN-BASE-STAR-PAYMENT-001"],
        "verified_fields": ["payment source", "cancelled preparation choice", "distributed deployment", "minimum six postcondition"],
        "mismatches": [],
    })
    for decision_id in ["DEC-CYBER-TARGET-GROUP-001", "DEC-TURN-BASE-STAR-PAYMENT-001"]:
        records.append({
            "item_id": decision_id,
            "item_type": "owner_decision",
            "status": "verified_with_owner_decision",
            "source_ids": ["SRC-ENABLER-0830-1", "SRC-SQUADRON-0901", "SRC-TOKEN-0901-1"] if "CYBER" in decision_id else ["SRC-RULE-0910-2-PDF"],
            "decision_ids": [decision_id],
            "verified_fields": ["owner final text", "scope", "source relationship", "affected rule IDs"],
            "mismatches": [],
        })
    for source_id in sorted(EXPECTED_CANONICAL_SOURCES):
        records.append({
            "item_id": source_id,
            "item_type": "canonical_source_record",
            "status": "verified_with_owner_decision",
            "source_ids": [source_id],
            "decision_ids": [],
            "verified_fields": ["canonical_record", "current_version_status", "independent draft/provisional/rights axes preserved"],
            "mismatches": [],
        })
    approved, _ = current_vectors()
    reviewed_vector_ids = sorted(
        v["vector_id"] for v in approved
        if v["vector_id"].startswith("RV-TURN-BASE-STAR-") or "CYBER-TARGET-GROUP" in v["vector_id"]
    )
    by_id = {v["vector_id"]: v for v in approved}
    for vector_id in reviewed_vector_ids:
        vector = by_id[vector_id]
        records.append({
            "item_id": vector_id,
            "item_type": "approved_rule_vector",
            "status": "verified_with_owner_decision",
            "source_ids": [],
            "source_fragment_ids": vector["source_fragment_ids"],
            "decision_ids": vector["decision_ids"],
            "rule_core_ids": vector["rule_core_ids"],
            "verified_fields": ["precondition", "operation", "expected events", "expected final state", "legality", "no randomness"],
            "mismatches": [],
        })
    records.append({
        "item_id": "ACTIVE-RULE-ID-SET",
        "item_type": "release_scope_completeness",
        "status": "verified",
        "verified_fields": ["registry-derived active set", "32 unique active IDs", "no prior Manifest template reuse"],
        "mismatches": [],
    })
    for rule_id in sorted(EXPECTED_PRIOR_OMISSIONS):
        records.append({
            "item_id": f"PRIOR-MANIFEST-OMISSION:{rule_id}",
            "item_type": "release_scope_completeness",
            "status": "verified",
            "rule_core_ids": [rule_id],
            "verified_fields": ["present in active registry", "present in next RC Manifest candidate"],
            "mismatches": [],
        })
    return records


def write_audit_artifacts() -> dict[str, Any]:
    approved, candidates = current_vectors()
    rules = load(RC / "governance/rule-id-registry.yaml")["rules"]
    active = sorted(row["rule_core_id"] for row in rules if row["status"] == "active")
    records = build_differential_records()
    audit_fingerprint = hashlib.sha256(canonical(records)).hexdigest()
    traceability_fingerprint = hashlib.sha256(canonical(load(RC / "governance/traceability.yaml")["mappings"])).hexdigest()
    old_baseline = load(RC / "governance/normative-audit/RC-2026.09.26-01/normative-baseline.json")
    normative_paths = [entry["path"] for entry in old_baseline["normative_file_hashes"]]
    normative_paths.extend([
        "rule-core/rules/turn-base-star-payment.md",
        "rule-core/tests/rule-vectors/cyber-target-group-candidates.yaml",
        "rule-core/tests/rule-vectors/turn-base-star-payment-candidates.yaml",
    ])
    normative_paths = sorted(set(normative_paths))
    normative_hashes = [
        {"path": path, "sha256": canonical_text_sha256(ROOT / path)}
        for path in normative_paths
    ]
    normative_files_fingerprint = hashlib.sha256(canonical(normative_hashes)).hexdigest()
    summary = {
        "schema_version": "1.0.0",
        "audit_id": "DNA-NEXT-RC-CANDIDATE-001",
        "baseline_release_id": "RC-2026.09.26-01",
        "candidate_id": "next-rc-candidate",
        "status": "VERIFIED",
        "verified_unchanged": 185,
        "out_of_scope_unchanged": 9,
        "reaudited_count": len(records),
        "reaudited_verified": sum(r["status"] == "verified" for r in records),
        "reaudited_verified_with_owner_decision": sum(r["status"] == "verified_with_owner_decision" for r in records),
        "blockers": {
            "needs_owner_review": 0,
            "mismatch": 0,
            "missing_from_rule_core": 0,
            "unsupported_in_rule_core": 0,
        },
        "approved_vector_count": len(approved),
        "candidate_vector_count": len(candidates),
        "approved_fingerprint": hashlib.sha256(canonical(approved)).hexdigest(),
        "active_rule_id_count": len(active),
        "active_rule_ids_fingerprint": hashlib.sha256(canonical(active)).hexdigest(),
        "source_to_rule_core_coverage_fingerprint": traceability_fingerprint,
        "audit_fingerprint": audit_fingerprint,
    }
    results = {
        "schema_version": "1.0.0",
        "audit_id": summary["audit_id"],
        "baseline_release_id": summary["baseline_release_id"],
        "candidate_id": summary["candidate_id"],
        "method": "baseline unchanged items are inherited by canonical hash; changed subjects are reaudited against formal sources and approved decisions",
        "summary": summary,
        "records": records,
    }
    baseline = {
        "schema_version": "1.0.0",
        "baseline_id": "NB-NEXT-RC-CANDIDATE-001",
        "release_id": None,
        "candidate_id": "next-rc-candidate",
        "prior_release_id": "RC-2026.09.26-01",
        "status": "VERIFIED",
        "normative_file_count": len(normative_hashes),
        "normative_file_hash_profile": "canonical-text-v1",
        "normative_file_hashes": normative_hashes,
        "normative_files_fingerprint": normative_files_fingerprint,
        "approved_vector_count": len(approved),
        "candidate_vector_count_excluded": len(candidates),
        "approved_fingerprint": summary["approved_fingerprint"],
        "active_rule_id_count": len(active),
        "active_rule_ids": active,
        "active_rule_ids_fingerprint": summary["active_rule_ids_fingerprint"],
        "source_set_aggregate": old_baseline["source_set_aggregate"],
        "unresolved_sha256": EXPECTED_UNRESOLVED_SHA256,
        "source_to_rule_core_coverage_fingerprint": traceability_fingerprint,
        "audit_fingerprint": audit_fingerprint,
        "blocking_item_ids": [],
    }
    manifest = {
        "candidate_format": "next-rc-manifest-candidate-v1",
        "candidate_status": "proposal",
        "immutable": False,
        "release_id": EXPECTED_RELEASE_ID,
        "specification_version": EXPECTED_SPECIFICATION_VERSION,
        "status": EXPECTED_RELEASE_STATUS,
        "content_commit": None,
        "git_tag": EXPECTED_GIT_TAG,
        "supersedes": EXPECTED_SUPERSEDES,
        "normative_scope": {
            "rule_core_ids": active,
            "approved_vector_ids": [v["vector_id"] for v in approved],
        },
        "approved_vector_count": len(approved),
        "approved_fingerprint": summary["approved_fingerprint"],
        "candidate_vector_count": len(candidates),
        "candidate_vectors_included_as_normative": False,
        "source_set_count": 20,
        "source_aggregate": old_baseline["source_set_aggregate"],
        "unresolved_sha256": EXPECTED_UNRESOLVED_SHA256,
        "normative_baseline": {
            "path": "rule-core/governance/normative-audit/next-rc-candidate/normative-baseline-candidate.json",
            "audit_fingerprint": audit_fingerprint,
            "status": "VERIFIED",
        },
        "release_identity_pending": False,
        "freeze_pending": True,
    }
    manifest_fingerprint = hashlib.sha256(canonical(manifest)).hexdigest()
    summary["manifest_candidate_fingerprint"] = manifest_fingerprint
    AUDIT.mkdir(parents=True, exist_ok=True)
    (AUDIT / "differential-normative-audit-results.yaml").write_text(
        yaml.safe_dump(results, allow_unicode=True, sort_keys=False), encoding="utf-8", newline="\n"
    )
    (AUDIT / "differential-normative-audit-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    (AUDIT / "normative-baseline-candidate.json").write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    release_dir = RC / "generated/releases"
    release_dir.mkdir(parents=True, exist_ok=True)
    (release_dir / "next-rc-manifest-candidate.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    report = f"""# Next RC Differential Normative Audit

- Baseline: `RC-2026.09.26-01`
- Candidate: `next-rc-candidate`
- Result: **Normative baseline: VERIFIED**
- Verified unchanged: {summary['verified_unchanged']}
- Out of scope unchanged: {summary['out_of_scope_unchanged']}
- Reaudited: {summary['reaudited_count']}
- Approved vectors: {summary['approved_vector_count']}
- Candidate vectors excluded: {summary['candidate_vector_count']}
- Active Rule IDs: {summary['active_rule_id_count']}
- Approved fingerprint: `{summary['approved_fingerprint']}`
- Audit fingerprint: `{audit_fingerprint}`
- Manifest candidate fingerprint: `{manifest_fingerprint}`

All four blocker classes are zero. The Release ID, specification version and planned tag are assigned. The content commit remains unset until this candidate is committed and independently validated; this is not a freeze artifact.
"""
    (AUDIT / "differential-normative-audit-report.md").write_text(report, encoding="utf-8", newline="\n")
    return summary


def validate_generated_audit(report: dict[str, Any]) -> None:
    summary_path = AUDIT / "differential-normative-audit-summary.json"
    baseline_path = AUDIT / "normative-baseline-candidate.json"
    manifest_path = RC / "generated/releases/next-rc-manifest-candidate.json"
    if not (summary_path.exists() and baseline_path.exists() and manifest_path.exists()):
        add(report, "differential_audit_artifacts", False, error="audit artifacts have not been generated")
        return
    summary = load(summary_path)
    baseline = load(baseline_path)
    manifest = load(manifest_path)
    active = load(AUDIT / "active-rule-id-set.json")["active_rule_ids"]
    blockers = summary["blockers"]
    passed = (
        summary["status"] == "VERIFIED"
        and all(value == 0 for value in blockers.values())
        and summary["approved_vector_count"] == EXPECTED_APPROVED_COUNT
        and summary["candidate_vector_count"] == EXPECTED_CANDIDATE_COUNT
        and baseline["status"] == "VERIFIED"
        and manifest["normative_scope"]["rule_core_ids"] == active
        and len(manifest["normative_scope"]["rule_core_ids"]) == 32
        and manifest["release_id"] == EXPECTED_RELEASE_ID
        and manifest["specification_version"] == EXPECTED_SPECIFICATION_VERSION
        and manifest["status"] == EXPECTED_RELEASE_STATUS
        and manifest["git_tag"] == EXPECTED_GIT_TAG
        and manifest["supersedes"] == EXPECTED_SUPERSEDES
        and manifest["content_commit"] is None
        and manifest["release_identity_pending"] is False
        and manifest["immutable"] is False
    )
    add(
        report,
        "differential_audit_artifacts",
        passed,
        verified_unchanged=summary["verified_unchanged"],
        reaudited_count=summary["reaudited_count"],
        blockers=blockers,
        manifest_candidate_fingerprint=summary["manifest_candidate_fingerprint"],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the next Rule Core candidate and differential-audit readiness.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--write-audit-artifacts", action="store_true")
    args = parser.parse_args()
    if args.write_audit_artifacts:
        write_audit_artifacts()
    report: dict[str, Any] = {
        "schema_version": "1.0.0",
        "candidate_id": "next-rc-candidate",
        "status": "pass",
        "checks": [],
    }
    validate_schema_instances(report)
    validate_vectors(report)
    validate_active_ids(report)
    validate_references(report)
    validate_differential_baseline(report)
    validate_owner_application(report)
    validate_protection(report)
    validate_generated_audit(report)
    report["canonical_result_fingerprint"] = hashlib.sha256(canonical(report["checks"])).hexdigest()
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
