from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import jsonschema
import yaml

from hash_profiles import (
    AFWI_CONTENT_SHA256_V1,
    LEGACY_TEXT_CRLF_V0,
    RAW_BINARY_V1,
    RAW_BYTES_V0,
    hash_bytes,
    hash_file,
)
from release_validation import validate_historical_release


ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
EXPECTED_UNRESOLVED_SHA256 = "3c47ef86dd16ae67520d0c7b2b2526a1f971a505753feaff0316fce591f4bf6e"
INTEGRITY_DECLARATIONS = RC / "governance/release-integrity-declarations.yaml"
DEFAULT_CANDIDATE = RC / "generated/releases/next-rc-manifest-candidate.json"
HISTORICAL_RELEASE_ID = "RC-2026.09.26-01"
HISTORICAL_MANIFEST = "rule-core/generated/releases/RC-2026.09.26-01-release-manifest-final-candidate.json"
HISTORICAL_CATALOG = "rule-core/generated/releases/release-catalog-final-candidate.json"

SCHEMA_INSTANCES = {
    "data/emi-components.yaml": "schemas/emi-components.schema.json",
    "data/enablers.yaml": "schemas/enablers.schema.json",
    "data/geography.yaml": "schemas/geography.schema.json",
    "data/rates.yaml": "schemas/rates.schema.json",
    "data/squadron-activation.yaml": "schemas/squadron-activation.schema.json",
    "data/squadrons.yaml": "schemas/squadrons.schema.json",
    "data/state-and-event-ids.yaml": "schemas/state-event-ids.schema.json",
    "governance/component-id-registry.yaml": "schemas/component-id-registry.schema.json",
    "governance/coverage.yaml": "schemas/coverage.schema.json",
    "governance/decisions.yaml": "schemas/decision.schema.json",
    "governance/field-ownership.yaml": "schemas/field-ownership.schema.json",
    "governance/release-integrity-declarations.yaml": "schemas/release-integrity-declarations.schema.json",
    "governance/rule-id-registry.yaml": "schemas/rule-id-registry.schema.json",
    "governance/source-fragment-register.yaml": "schemas/source-fragment-register.schema.json",
    "governance/source-register.yaml": "schemas/source-register.schema.json",
    "governance/traceability.yaml": "schemas/traceability.schema.json",
    "governance/unresolved.yaml": "schemas/unresolved.schema.json",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def integrity_declarations() -> dict[str, Any]:
    return load(INTEGRITY_DECLARATIONS)


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load(path: Path) -> Any:
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8-sig"))
    return yaml.safe_load(path.read_text(encoding="utf-8-sig"))


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8"
    )
    return completed.stdout.strip()


def git_succeeds(*args: str) -> bool:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=False, capture_output=True
    ).returncode == 0


def git_blob(commit: str, relative_path: str) -> bytes | None:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    return completed.stdout if completed.returncode == 0 else None


def git_tracked_files() -> set[str]:
    return set(git("-c", "core.quotepath=false", "ls-files").splitlines())


def add_check(report: dict[str, Any], name: str, passed: bool, **details: Any) -> None:
    report["checks"].append({"name": name, "status": "pass" if passed else "fail", **details})
    if not passed:
        report["status"] = "fail"


def validate_schema_definitions(report: dict[str, Any]) -> None:
    paths = sorted((RC / "schemas").glob("*.schema.json"))
    errors: list[str] = []
    for path in paths:
        try:
            jsonschema.Draft202012Validator.check_schema(load(path))
        except Exception as exc:  # schema diagnostics must include the file
            errors.append(f"{path.relative_to(ROOT).as_posix()}: {exc}")
    add_check(report, "schema_definitions", not errors, schema_count=len(paths), errors=errors)


def validate_instances(report: dict[str, Any]) -> None:
    errors: list[str] = []
    validated: list[str] = []
    for instance_rel, schema_rel in SCHEMA_INSTANCES.items():
        instance_path = RC / instance_rel
        schema_path = RC / schema_rel
        try:
            jsonschema.Draft202012Validator(load(schema_path)).validate(load(instance_path))
            validated.append(instance_rel)
        except Exception as exc:
            errors.append(f"{instance_rel} against {schema_rel}: {exc}")

    vector_schema = load(RC / "schemas/rule-vector.schema.json")
    for vector_path in sorted((RC / "tests/rule-vectors").glob("*.yaml")):
        try:
            jsonschema.Draft202012Validator(vector_schema).validate(load(vector_path))
            validated.append(vector_path.relative_to(RC).as_posix())
        except Exception as exc:
            errors.append(f"{vector_path.relative_to(RC).as_posix()}: {exc}")

    snapshot_schema = load(RC / "schemas/source-set-snapshot.schema.json")
    for snapshot_path in sorted((RC / "governance/source-set-snapshots").glob("*.yaml")):
        try:
            jsonschema.Draft202012Validator(snapshot_schema).validate(load(snapshot_path))
            validated.append(snapshot_path.relative_to(RC).as_posix())
        except Exception as exc:
            errors.append(f"{snapshot_path.relative_to(RC).as_posix()}: {exc}")

    add_check(report, "current_schema_instances", not errors, validated_count=len(validated), errors=errors)


def all_vectors() -> list[dict[str, Any]]:
    vectors: list[dict[str, Any]] = []
    for path in sorted((RC / "tests/rule-vectors").glob("*.yaml")):
        document = load(path)
        for vector in document.get("vectors", []):
            copy = dict(vector)
            copy["__source_file"] = path.relative_to(ROOT).as_posix()
            vectors.append(copy)
    return vectors


def validate_vectors(
    report: dict[str, Any], expectation: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    vectors = all_vectors()
    ids = [v["vector_id"] for v in vectors]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    approved_raw = [{k: val for k, val in v.items() if k != "__source_file"} for v in vectors if v["status"] == "approved"]
    candidate = [v for v in vectors if v["status"] == "candidate"]
    approved = sorted(approved_raw, key=lambda item: item["vector_id"])
    fingerprint = hashlib.sha256(canonical(approved)).hexdigest()
    approval_errors = [
        v["vector_id"]
        for v in approved
        if v.get("approval", {}).get("approved_by") != "ルール所有者"
        or not v.get("approval", {}).get("approved_at")
    ]
    candidate_approval_errors = [
        v["vector_id"]
        for v in candidate
        if v.get("approval") != {"approved_by": None, "approved_at": None}
    ]
    passed = (
        not duplicates
        and len(approved) == expectation["approved_vector_count"]
        and len(candidate) == expectation["candidate_vector_count"]
        and fingerprint == expectation["approved_fingerprint"]
        and not approval_errors
        and not candidate_approval_errors
    )
    add_check(
        report,
        "approved_vector_set",
        passed,
        approved_count=len(approved),
        candidate_count=len(candidate),
        approved_fingerprint=fingerprint,
        duplicate_ids=duplicates,
        approved_approval_errors=approval_errors,
        candidate_approval_errors=candidate_approval_errors,
        expected_from=expectation["__source_file"],
    )
    return approved, candidate


def load_candidate_expectation(path: Path) -> dict[str, Any]:
    candidate = load(path)
    required = (
        "approved_vector_count",
        "candidate_vector_count",
        "approved_fingerprint",
        "normative_scope",
        "normative_baseline",
        "source_set_count",
        "source_aggregate",
        "unresolved_sha256",
    )
    missing = [key for key in required if key not in candidate]
    if missing:
        raise ValueError(f"candidate declaration missing fields: {missing}")
    candidate["__source_file"] = path.relative_to(ROOT).as_posix()
    return candidate


def validate_candidate_declaration(
    report: dict[str, Any],
    expectation: dict[str, Any],
    approved: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> None:
    registry = load(RC / "governance/rule-id-registry.yaml")
    active_ids = sorted(row["rule_core_id"] for row in registry["rules"] if row["status"] == "active")
    approved_ids = sorted(row["vector_id"] for row in approved)
    declared_scope = expectation["normative_scope"]
    baseline_ref = expectation["normative_baseline"]
    baseline_path = ROOT / baseline_ref["path"]
    baseline = load(baseline_path) if baseline_path.exists() else {}
    source_snapshot_path = sorted((RC / "governance/source-set-snapshots").glob("*.yaml"))[-1]
    source_snapshot = load(source_snapshot_path)
    unresolved_sha256 = sha256(RC / "governance/unresolved.yaml")
    passed = (
        expectation.get("candidate_format") == "next-rc-manifest-candidate-v1"
        and expectation.get("immutable") is False
        and expectation.get("freeze_pending") is True
        and expectation.get("candidate_vectors_included_as_normative") is False
        and declared_scope.get("rule_core_ids") == active_ids
        and declared_scope.get("approved_vector_ids") == approved_ids
        and len(active_ids) == 32
        and len(approved) == expectation["approved_vector_count"]
        and len(candidates) == expectation["candidate_vector_count"]
        and baseline.get("status") == "VERIFIED"
        and baseline.get("audit_fingerprint") == baseline_ref.get("audit_fingerprint")
        and baseline.get("approved_fingerprint") == expectation["approved_fingerprint"]
        and baseline.get("active_rule_ids") == active_ids
        and len(source_snapshot.get("sources", [])) == expectation["source_set_count"]
        and source_snapshot.get("aggregate_sha256") == expectation["source_aggregate"]
        and unresolved_sha256 == expectation["unresolved_sha256"]
        and expectation.get("release_id") == "RC-2026.09.27-01"
        and expectation.get("specification_version") == "v0.9.1"
        and expectation.get("git_tag") == "RC-2026.09.27-01"
        and expectation.get("content_commit") is None
    )
    add_check(
        report,
        "current_candidate_declaration",
        passed,
        declaration=expectation["__source_file"],
        release_id=expectation.get("release_id"),
        specification_version=expectation.get("specification_version"),
        active_rule_id_count=len(active_ids),
        active_rule_ids=active_ids,
        approved_vector_count=len(approved),
        candidate_vector_count=len(candidates),
        normative_baseline_status=baseline.get("status"),
        normative_audit_fingerprint=baseline.get("audit_fingerprint"),
        source_set_count=len(source_snapshot.get("sources", [])),
        source_aggregate=source_snapshot.get("aggregate_sha256"),
        unresolved_sha256=unresolved_sha256,
    )


def recursively_collect(value: Any, prefixes: tuple[str, ...]) -> set[str]:
    found: set[str] = set()
    if isinstance(value, str):
        if value.startswith(prefixes):
            found.add(value)
    elif isinstance(value, dict):
        for child in value.values():
            found.update(recursively_collect(child, prefixes))
    elif isinstance(value, list):
        for child in value:
            found.update(recursively_collect(child, prefixes))
    return found


def validate_ids(report: dict[str, Any], approved: list[dict[str, Any]]) -> None:
    rule_registry = load(RC / "governance/rule-id-registry.yaml")
    component_registry = load(RC / "governance/component-id-registry.yaml")
    state_event_registry = load(RC / "data/state-and-event-ids.yaml")
    source_register = load(RC / "governance/source-register.yaml")
    fragment_register = load(RC / "governance/source-fragment-register.yaml")
    decision_register = load(RC / "governance/decisions.yaml")

    registries = {
        "RC-": {row["rule_core_id"] for row in rule_registry["rules"]},
        "COMP-": {row["component_id"] for row in component_registry["components"]},
        "STATE-": {row["state_id"] for row in state_event_registry["states"]},
        "EVENT-": {row["event_id"] for row in state_event_registry["events"]},
        "SRC-": {row["source_id"] for row in source_register["sources"]},
        "FRAG-": {row["fragment_id"] for row in fragment_register["fragments"]},
        "DEC-": {row["decision_id"] for row in decision_register["decisions"]},
    }
    duplicate_registry_ids: list[str] = []
    for prefix, values in registries.items():
        raw: list[str]
        if prefix == "RC-":
            raw = [row["rule_core_id"] for row in rule_registry["rules"]]
        elif prefix == "COMP-":
            raw = [row["component_id"] for row in component_registry["components"]]
        elif prefix == "STATE-":
            raw = [row["state_id"] for row in state_event_registry["states"]]
        elif prefix == "EVENT-":
            raw = [row["event_id"] for row in state_event_registry["events"]]
        elif prefix == "SRC-":
            raw = [row["source_id"] for row in source_register["sources"]]
        elif prefix == "FRAG-":
            raw = [row["fragment_id"] for row in fragment_register["fragments"]]
        else:
            raw = [row["decision_id"] for row in decision_register["decisions"]]
        duplicate_registry_ids.extend(sorted({item for item in raw if raw.count(item) > 1}))

    missing: dict[str, list[str]] = {}
    for prefix, registry in registries.items():
        refs: set[str] = set()
        for vector in approved:
            refs.update(recursively_collect(vector, (prefix,)))
        absent = sorted(refs - registry)
        if absent:
            missing[prefix] = absent

    deprecated_rule_ids = {
        row["rule_core_id"] for row in rule_registry["rules"] if row.get("status") == "deprecated"
    }
    deprecated_component_ids = {
        row["component_id"] for row in component_registry["components"] if row.get("status") == "deprecated"
    }
    used = set().union(*(recursively_collect(vector, ("RC-", "COMP-")) for vector in approved))
    deprecated_refs = sorted(used & (deprecated_rule_ids | deprecated_component_ids))
    add_check(
        report,
        "id_uniqueness_and_references",
        not duplicate_registry_ids and not missing and not deprecated_refs,
        duplicate_registry_ids=duplicate_registry_ids,
        missing_references=missing,
        deprecated_references=deprecated_refs,
    )


def validate_source_snapshot(report: dict[str, Any]) -> None:
    register = load(RC / "governance/source-register.yaml")
    declarations = integrity_declarations()
    receipts = {row["source_id"]: row for row in declarations["external_fixed_source_receipts"]}
    tracked = git_tracked_files()
    snapshots = sorted((RC / "governance/source-set-snapshots").glob("*.yaml"))
    snapshot_path = snapshots[-1]
    snapshot = load(snapshot_path)
    by_id = {row["source_id"]: row for row in register["sources"]}
    mismatches: list[dict[str, Any]] = []
    aggregate_rows: list[str] = []
    external_verified: list[dict[str, Any]] = []
    tracked_verified: list[str] = []
    for row in snapshot["sources"]:
        source = by_id.get(row["source_id"])
        if source is None:
            mismatches.append({"source_id": row["source_id"], "reason": "not_in_source_register"})
            continue
        relative = source["relative_path"].replace("\\", "/")
        path = ROOT / relative
        expected = row["content_sha256"]
        if source["content_sha256"] != expected:
            mismatches.append(
                {"source_id": row["source_id"], "reason": "register_snapshot_hash_mismatch", "expected": expected}
            )
        receipt = receipts.get(row["source_id"])
        if receipt is not None:
            receipt_errors: list[str] = []
            expected_receipt = {
                "filename": Path(relative).name,
                "relative_path": relative,
                "sha256": expected,
                "size_bytes": source.get("size_bytes"),
            }
            for key, value in expected_receipt.items():
                if receipt.get(key) != value:
                    receipt_errors.append(f"{key}: expected {value!r}, got {receipt.get(key)!r}")
            if receipt.get("availability_status") != "external_fixed":
                receipt_errors.append("availability_status is not external_fixed")
            if receipt.get("raw_file_in_git") is not False:
                receipt_errors.append("raw_file_in_git is not false")
            if relative in tracked:
                receipt_errors.append("raw source is unexpectedly Git tracked")
            raw_present = path.exists()
            if raw_present:
                actual = hash_file(
                    path,
                    hash_profile=RAW_BINARY_V1,
                    content_kind=receipt["content_kind"],
                    media_type=receipt["media_type"],
                )
                actual_size = path.stat().st_size
                if actual != receipt["sha256"]:
                    receipt_errors.append(f"raw hash: expected {receipt['sha256']}, got {actual}")
                if actual_size != receipt["size_bytes"]:
                    receipt_errors.append(f"raw size: expected {receipt['size_bytes']}, got {actual_size}")
            external_verified.append(
                {"source_id": row["source_id"], "raw_file_present": raw_present, "receipt_errors": receipt_errors}
            )
            if receipt_errors:
                mismatches.append(
                    {"source_id": row["source_id"], "reason": "external_fixed_receipt_mismatch", "errors": receipt_errors}
                )
        else:
            actual = sha256(path) if path.exists() else "missing"
            if relative not in tracked:
                mismatches.append({"source_id": row["source_id"], "reason": "tracked_source_not_git_tracked"})
            if actual != expected:
                mismatches.append({"source_id": row["source_id"], "expected": expected, "actual": actual})
            else:
                tracked_verified.append(row["source_id"])
        aggregate_rows.append(f"{relative}\0{expected}")
    aggregate = hashlib.sha256("\n".join(sorted(aggregate_rows)).encode("utf-8")).hexdigest()
    if aggregate != snapshot["aggregate_sha256"]:
        mismatches.append({"source_id": "aggregate", "expected": snapshot["aggregate_sha256"], "actual": aggregate})
    add_check(
        report,
        "source_set_snapshot",
        not mismatches and len(snapshot["sources"]) == 20 and len(receipts) == 3,
        snapshot=snapshot_path.relative_to(ROOT).as_posix(),
        source_count=len(snapshot["sources"]),
        aggregate_sha256=aggregate,
        git_tracked_source_count=len(tracked_verified),
        external_fixed_source_count=len(external_verified),
        external_fixed_sources=external_verified,
        mismatches=mismatches,
    )


def iter_artifact_refs(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
            yield {
                key: value[key]
                for key in ("path", "sha256", "hash_profile", "content_kind", "media_type")
                if key in value
            }
        for child in value.values():
            yield from iter_artifact_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_artifact_refs(child)


def validate_current_integrity(report: dict[str, Any]) -> None:
    """Validate current declarations without comparing historical hashes to today's tree."""
    declarations = integrity_declarations()
    tracked = git_tracked_files()
    errors: list[dict[str, Any]] = []
    evidence = declarations.get("external_internal_evidence", [])
    for row in evidence:
        relative = row["path"].replace("\\", "/")
        fields_valid = (
            row.get("artifact_class") == "external evidence"
            and row.get("distribution_class") == "internal archive"
            and row.get("rights_status") == "rights-pending"
            and row.get("public_normative_artifact") is False
            and row.get("raw_file_in_git") is False
        )
        if not fields_valid:
            errors.append({"path": relative, "reason": "invalid_evidence_classification"})
        if relative in tracked:
            errors.append({"path": relative, "reason": "external_evidence_unexpectedly_git_tracked"})
        path = ROOT / relative
        if path.exists():
            actual = hash_file(
                path,
                hash_profile=row["hash_profile"],
                content_kind=row["content_kind"],
                media_type=row["media_type"],
            )
            if actual != row["sha256"]:
                errors.append({"path": relative, "reason": "evidence_raw_file_hash_mismatch"})
    add_check(
        report,
        "current_release_integrity_validation",
        not errors
        and declarations.get("current_hash_profile") == AFWI_CONTENT_SHA256_V1
        and len(evidence) == 15,
        hash_profile=declarations.get("current_hash_profile"),
        external_internal_evidence_count=len(evidence),
        errors=errors,
    )


def validate_historical_release_gate(report: dict[str, Any]) -> None:
    result = validate_historical_release(
        ROOT,
        release_id=HISTORICAL_RELEASE_ID,
        manifest_path=HISTORICAL_MANIFEST,
        catalog_path=HISTORICAL_CATALOG,
    )
    add_check(
        report,
        "historical_release_validation",
        result["status"] == "pass",
        **{key: value for key, value in result.items() if key != "status"},
    )


def validate_governance_approval(report: dict[str, Any]) -> None:
    policy = (RC / "docs/design/AFWI-KAI_Rule_Core_バージョン管理・リリース方針-01.md").read_text(encoding="utf-8-sig")
    review = load(RC / "generated/reviews/initial-release-candidate-owner-review.json")
    semantics_review = load(RC / "generated/reviews/content-commit-semantics-owner-review.json")
    answers = review.get("decisions_requested", [])
    approval = review.get("approval", {})
    semantics_answers = semantics_review.get("decisions_requested", [])
    semantics_approval = semantics_review.get("approval", {})
    passed = (
        "document_version: 1.1" in policy
        and "status: approved" in policy
        and "approved_by: ルール所有者" in policy
        and "effective_at: 2026-09-26" in policy
        and "`content_commit`" in policy
        and len(answers) == 11
        and all(
            item.get("owner_answer")
            == {"status": "approved", "approved_by": "ルール所有者", "approved_at": "2026-09-26"}
            for item in answers
        )
        and approval
        == {
            "status": "approved",
            "approved_by": "ルール所有者",
            "approved_at": "2026-09-26",
            "effective_at": "2026-09-26",
        }
        and len(semantics_answers) == 5
        and all(
            item.get("owner_answer")
            == {"status": "approved", "approved_by": "ルール所有者", "approved_at": "2026-09-26"}
            for item in semantics_answers
        )
        and semantics_approval
        == {
            "status": "approved",
            "approved_by": "ルール所有者",
            "approved_at": "2026-09-26",
            "effective_at": "2026-09-26",
        }
    )
    add_check(
        report,
        "release_governance_approval",
        passed,
        decision_count=len(answers),
        approval=approval,
        content_commit_decision_count=len(semantics_answers),
        content_commit_approval=semantics_approval,
        content_commit_semantics_present="`content_commit`" in policy,
    )


def validate_snapshots(report: dict[str, Any]) -> None:
    unresolved = sha256(RC / "governance/unresolved.yaml")
    add_check(
        report,
        "governance_snapshots",
        unresolved == EXPECTED_UNRESOLVED_SHA256,
        unresolved_sha256=unresolved,
        decisions_sha256=sha256(RC / "governance/decisions.yaml"),
        coverage_sha256=sha256(RC / "governance/coverage.yaml"),
        traceability_sha256=sha256(RC / "governance/traceability.yaml"),
        field_ownership_sha256=sha256(RC / "governance/field-ownership.yaml"),
    )


def validate_release_instance(
    report: dict[str, Any],
    manifest_path: Path,
    catalog_path: Path,
    mode: str,
    approved_count: int,
    approved_fingerprint: str,
) -> None:
    manifest = load(manifest_path)
    catalog = load(catalog_path)
    try:
        jsonschema.Draft202012Validator(load(RC / "schemas/release-manifest.schema.json")).validate(manifest)
        jsonschema.Draft202012Validator(load(RC / "schemas/release-catalog.schema.json")).validate(catalog)
        schema_errors: list[str] = []
    except Exception as exc:
        schema_errors = [str(exc)]
    content_commit = manifest.get("content_commit")
    content_commit_exists = isinstance(content_commit, str) and git_succeeds(
        "cat-file", "-e", f"{content_commit}^{{commit}}"
    )
    freeze_evidence = manifest.get("technical_rc_freeze_validation", {})
    freeze_commit_matches = (
        isinstance(freeze_evidence, dict)
        and freeze_evidence.get("validated_content_commit") == content_commit
    )

    artifact_errors: list[dict[str, str]] = []
    if content_commit_exists:
        for ref in iter_artifact_refs(manifest):
            relative = ref["path"]
            blob = git_blob(content_commit, relative)
            if blob is None:
                artifact_errors.append({"path": relative, "reason": "missing_from_content_commit"})
                continue
            actual = hash_bytes(
                blob,
                hash_profile=ref["hash_profile"],
                content_kind=ref["content_kind"],
                media_type=ref["media_type"],
            )
            if actual != ref["sha256"]:
                artifact_errors.append({"path": relative, "reason": "content_commit_hash_mismatch"})

    catalog_manifest_errors: list[str] = []
    catalog_nodes: list[Any] = [catalog]
    while catalog_nodes:
        node = catalog_nodes.pop()
        if isinstance(node, dict):
            if isinstance(node.get("manifest_path"), str) and isinstance(node.get("manifest_sha256"), str):
                path = ROOT / node["manifest_path"]
                actual = hash_file(
                    path,
                    hash_profile=node["manifest_hash_profile"],
                    content_kind=node["manifest_content_kind"],
                    media_type=node["manifest_media_type"],
                ) if path.exists() else "missing"
                if actual != node["manifest_sha256"]:
                    catalog_manifest_errors.append(node["manifest_path"])
            catalog_nodes.extend(node.values())
        elif isinstance(node, list):
            catalog_nodes.extend(node)
    head = git("rev-parse", "HEAD")
    release_id = manifest.get("release_id")
    git_tag = manifest.get("git_tag")
    tag_matches_release_id = isinstance(git_tag, str) and git_tag == release_id
    tag_exists = isinstance(git_tag, str) and git_succeeds("rev-parse", "--verify", f"refs/tags/{git_tag}^{{commit}}")
    tag_target = git("rev-parse", f"refs/tags/{git_tag}^{{commit}}") if tag_exists else None
    tag_targets_metadata_commit = tag_target == head if tag_exists else False
    content_reachable_from_metadata = (
        content_commit_exists
        and git_succeeds("merge-base", "--is-ancestor", content_commit, head)
    )

    catalog_release_pointers: list[dict[str, Any]] = []
    catalog_nodes = [catalog]
    while catalog_nodes:
        node = catalog_nodes.pop()
        if isinstance(node, dict):
            if node.get("release_id") == release_id and "manifest_path" in node:
                catalog_release_pointers.append(node)
            catalog_nodes.extend(node.values())
        elif isinstance(node, list):
            catalog_nodes.extend(node)
    catalog_semantics_match = bool(catalog_release_pointers) and all(
        pointer.get("content_commit") == content_commit
        and pointer.get("git_tag") == git_tag
        and pointer.get("git_tag") == pointer.get("release_id")
        for pointer in catalog_release_pointers
    )

    metadata_artifact_errors: list[str] = []
    if mode == "release":
        for path in (manifest_path, catalog_path):
            try:
                relative = path.relative_to(ROOT).as_posix()
            except ValueError:
                metadata_artifact_errors.append(f"outside_repository:{path}")
                continue
            blob = git_blob(head, relative)
            if blob is None:
                metadata_artifact_errors.append(f"missing_from_metadata_commit:{relative}")
            elif hash_bytes(
                blob,
                hash_profile=AFWI_CONTENT_SHA256_V1,
                content_kind="text",
                media_type="application/json",
            ) != hash_file(
                path,
                hash_profile=AFWI_CONTENT_SHA256_V1,
                content_kind="text",
                media_type="application/json",
            ):
                metadata_artifact_errors.append(f"worktree_differs_from_metadata_commit:{relative}")

    tag_condition = not tag_exists if mode == "prefreeze" else tag_targets_metadata_commit
    passed = (
        not schema_errors
        and not artifact_errors
        and not catalog_manifest_errors
        and not metadata_artifact_errors
        and manifest.get("approved_vector_count") == approved_count
        and manifest.get("approved_fingerprint") == approved_fingerprint
        and manifest.get("candidate_vectors_included_as_normative") is False
        and content_commit_exists
        and freeze_commit_matches
        and tag_matches_release_id
        and tag_condition
        and content_reachable_from_metadata
        and catalog_semantics_match
    )
    add_check(
        report,
        "release_manifest_and_catalog_instance",
        passed,
        schema_errors=schema_errors,
        content_commit=content_commit,
        content_commit_exists=content_commit_exists,
        freeze_evidence_matches_content_commit=freeze_commit_matches,
        artifact_hash_errors=artifact_errors,
        catalog_manifest_hash_errors=catalog_manifest_errors,
        catalog_semantics_match=catalog_semantics_match,
        metadata_artifact_errors=metadata_artifact_errors,
        head=head,
        git_tag=git_tag,
        tag_exists=tag_exists,
        tag_target=tag_target,
        tag_matches_release_id=tag_matches_release_id,
        tag_targets_metadata_commit=tag_targets_metadata_commit,
        content_reachable_from_metadata_commit=content_reachable_from_metadata,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the current Rule Core release state without invoking historical validators.")
    parser.add_argument("--mode", choices=["prefreeze", "release"], default="prefreeze")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()

    candidate_path = args.candidate.resolve()
    expectation = load_candidate_expectation(candidate_path)

    report: dict[str, Any] = {
        "validator": "rule-core-current-release",
        "scope": "current_state_release_validator",
        "mode": args.mode,
        "historical_validators_invoked": True,
        "candidate_declaration": candidate_path.relative_to(ROOT).as_posix(),
        "status": "pass",
        "checks": [],
    }
    validate_schema_definitions(report)
    validate_instances(report)
    approved, candidate_vectors = validate_vectors(report, expectation)
    validate_ids(report, approved)
    validate_source_snapshot(report)
    validate_candidate_declaration(report, expectation, approved, candidate_vectors)
    validate_current_integrity(report)
    validate_historical_release_gate(report)
    validate_governance_approval(report)
    validate_snapshots(report)

    if args.require_clean:
        dirty = git("status", "--porcelain").splitlines()
        add_check(report, "clean_checkout", not dirty, dirty_paths=dirty)

    if args.manifest is not None or args.catalog is not None:
        if args.manifest is None or args.catalog is None:
            add_check(report, "release_manifest_and_catalog_instance", False, error="--manifest and --catalog must be provided together")
        else:
            validate_release_instance(
                report,
                args.manifest.resolve(),
                args.catalog.resolve(),
                args.mode,
                len(approved),
                hashlib.sha256(canonical(approved)).hexdigest(),
            )
    elif args.mode == "release":
        add_check(report, "release_manifest_and_catalog_instance", False, error="--manifest and --catalog are required in release mode")
    else:
        report["release_instance_status"] = "not_created_by_owner_instruction"

    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
