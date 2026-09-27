from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import subprocess
import sys
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from hash_profiles import AFWI_CONTENT_SHA256_V1, hash_file


RELEASE_ID = "RC-2026.09.26-01"
PACKAGE_ID = "PUB-2026.09.26-01"
CONTENT_COMMIT = "cefaabf0596d11d04d643626583bd7c6a4a2bdb3"
METADATA_COMMIT = "a212688f7ef09bf46ad0bae261a5d5196d593d7d"
FREEZE_RECORD_COMMIT = "61c2fea3904062b38551d78784020394d21b6926"
MANIFEST_PATH = Path("rule-core/generated/releases/RC-2026.09.26-01-release-manifest-final-candidate.json")
CATALOG_PATH = Path("rule-core/generated/releases/release-catalog-final-candidate.json")
RIGHTS_PATH = Path("rule-core/governance/releases/RC-2026.09.26-01-rights-clearance.json")
PACKAGE_PATH = Path("rule-core/generated/publication/PUB-2026.09.26-01-publication-package.json")
RIGHTS_RECORD_ID = "RIGHTS-RC-2026.09.26-01-01"
FROZEN_MANIFEST_SHA256 = "5f83f5963a010a4dce4debf3599d504197a57c703ce24756b2840ac29590dd5e"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    explicit = {
        ".json": "application/json",
        ".yaml": "application/yaml",
        ".yml": "application/yaml",
        ".md": "text/markdown",
        ".py": "text/x-python",
        ".txt": "text/plain",
    }
    return explicit.get(suffix, mimetypes.guess_type(path.name)[0] or "application/octet-stream")


def content_hash(path: Path, root: Path) -> dict[str, str]:
    mt = media_type(path)
    kind = "text" if path.suffix.lower() in {".json", ".yaml", ".yml", ".md", ".py", ".txt"} else "binary"
    return {
        "hash_profile": AFWI_CONTENT_SHA256_V1,
        "content_kind": kind,
        "media_type": mt,
        "sha256": hash_file(path, hash_profile=AFWI_CONTENT_SHA256_V1, content_kind=kind, media_type=mt),
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def source_commit(root: Path, path: str) -> str | None:
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", path],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if tracked.returncode != 0:
        return None
    changed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", path],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    if changed.stdout.strip():
        return None
    commit = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", path],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return commit or None


def collect_vector_statuses(value: Any, found: list[tuple[str, str]]) -> None:
    if isinstance(value, dict):
        vector_id = value.get("id") or value.get("vector_id")
        status = value.get("status")
        if isinstance(vector_id, str) and vector_id.startswith("RV-") and isinstance(status, str):
            found.append((vector_id, status))
        for child in value.values():
            collect_vector_statuses(child, found)
    elif isinstance(value, list):
        for child in value:
            collect_vector_statuses(child, found)


def vector_inventory(root: Path) -> tuple[list[Path], list[str], int, int]:
    approved_files: list[Path] = []
    candidate_ids: list[str] = []
    approved_count = 0
    candidate_count = 0
    for path in sorted((root / "rule-core/tests/rule-vectors").glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        found: list[tuple[str, str]] = []
        collect_vector_statuses(data, found)
        statuses = {status for _, status in found}
        approved_count += sum(1 for _, status in found if status == "approved")
        candidate_count += sum(1 for _, status in found if status == "candidate")
        candidate_ids.extend(vector_id for vector_id, status in found if status == "candidate")
        if found and statuses == {"approved"}:
            approved_files.append(path)
        elif "approved" in statuses:
            raise RuntimeError(f"mixed approved/candidate vector file cannot be published atomically: {rel(path, root)}")
    if (approved_count, candidate_count) != (131, 3):
        raise RuntimeError(f"unexpected vector inventory: approved={approved_count}, candidate={candidate_count}")
    if len(approved_files) != 11:
        raise RuntimeError(f"expected 11 approved vector files, got {len(approved_files)}")
    return approved_files, sorted(candidate_ids), approved_count, candidate_count


def artifact_identity(path: Path, root: Path) -> tuple[str, str, str, str]:
    p = rel(path, root)
    if p.startswith("rule-core/rules/"):
        return "normative", "normative-rule", "CC-BY-SA-4.0", "normative Rule Core text"
    if p.startswith("rule-core/data/"):
        return "normative", "normative-data", "CC-BY-SA-4.0", "normative Rule Core data"
    if p.startswith("rule-core/tests/rule-vectors/"):
        return "normative", "approved-vector", "CC-BY-SA-4.0", "approved Rule Core vector"
    if p.startswith("rule-core/schemas/"):
        return "schema", "schema", "CC-BY-SA-4.0", "Rule Core-specific schema"
    if p.startswith("rule-core/pipeline/"):
        name = path.name
        role = "hash-processing" if name == "hash_profiles.py" else ("validator" if name.startswith("validate-") else "generator")
        return "validator", role, "MIT", "Rule Core pipeline software"
    if p.endswith("/decisions.yaml"):
        return "decision", "decision", "CC-BY-SA-4.0", "approved decision register"
    if p.endswith("rule-id-registry.yaml") or p.endswith("component-id-registry.yaml"):
        return "registry", "registry", "CC-BY-SA-4.0", "Rule Core ID registry"
    if p.endswith("coverage.yaml"):
        return "coverage", "coverage", "CC-BY-SA-4.0", "Rule Core coverage record"
    if p.endswith("traceability.yaml"):
        return "traceability", "traceability", "CC-BY-SA-4.0", "Rule Core traceability record"
    if p.endswith("field-ownership.yaml"):
        return "governance", "field-ownership", "CC-BY-SA-4.0", "Rule Core field ownership"
    if p == MANIFEST_PATH.as_posix() or p == CATALOG_PATH.as_posix():
        return "release-metadata", "release-metadata", "CC-BY-SA-4.0", "frozen release metadata"
    if p.endswith("/MIT.txt"):
        return "governance", "license", "MIT", "MIT license notice"
    if "/LICENSES/" in p or p.endswith("LICENSES.md"):
        return "governance", "license", "CC-BY-SA-4.0", "publication license declaration"
    if p.endswith("NOTICE.md"):
        return "governance", "notice", "CC-BY-SA-4.0", "publication notice"
    return "governance", "governance", "CC-BY-SA-4.0", "Rule Core release governance"


def public_paths(root: Path, approved_vector_files: list[Path]) -> list[Path]:
    paths: list[Path] = []
    paths.extend(sorted((root / "rule-core/rules").glob("*.md")))
    paths.extend(sorted((root / "rule-core/data").glob("*.yaml")))
    paths.extend(approved_vector_files)
    paths.extend(sorted((root / "rule-core/schemas").glob("*.json")))
    paths.extend(sorted((root / "rule-core/pipeline").glob("*.py")))
    for item in [
        "rule-core/governance/decisions.yaml",
        "rule-core/governance/rule-id-registry.yaml",
        "rule-core/governance/component-id-registry.yaml",
        "rule-core/governance/coverage.yaml",
        "rule-core/governance/traceability.yaml",
        "rule-core/governance/field-ownership.yaml",
        "rule-core/governance/scope-and-authority.md",
        "rule-core/governance/releases/RC-2026.09.26-01-technical-freeze.md",
        "rule-core/docs/design/AFWI-KAI_Rule_Core_バージョン管理・リリース方針-01.md",
        MANIFEST_PATH.as_posix(),
        CATALOG_PATH.as_posix(),
        "rule-core/LICENSES/CC-BY-SA-4.0.txt",
        "rule-core/LICENSES/MIT.txt",
        "rule-core/LICENSES.md",
        "rule-core/NOTICE.md",
    ]:
        paths.append(root / item)
    missing = [rel(path, root) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"publication artifact missing: {missing}")
    unique = {rel(path, root): path for path in paths}
    return [unique[key] for key in sorted(unique)]


def frozen_classifications(manifest: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for artifact_set in manifest["artifact_sets"]:
        classification = artifact_set["distribution_class"]
        for artifact in artifact_set["artifacts"]:
            result[artifact["path"]] = classification
    return result


def generic_hash(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "hash_profile": entry["hash_profile"],
        "content_kind": entry["content_kind"],
        "media_type": entry["media_type"],
        "sha256": entry["sha256"],
    }


def create_rights_record(
    root: Path,
    paths: list[Path],
    classifications: dict[str, str],
    integrity: dict[str, Any],
) -> dict[str, Any]:
    cleared = []
    for path in paths:
        p = rel(path, root)
        artifact_class, _, license_id, basis = artifact_identity(path, root)
        cleared.append({
            "path": p,
            "artifact_class": artifact_class,
            "release_manifest_classification": classifications.get(p, "not-in-frozen-manifest"),
            "artifact_hash": content_hash(path, root),
            "clearance_basis": basis + "; owner rights/publication decision dated 2026-09-26",
            "public_distribution_allowed": True,
            "raw_source_included": False,
            "license_reference": f"rule-core/LICENSES/{license_id}.txt",
        })

    restricted = []
    for receipt in integrity["external_fixed_source_receipts"]:
        restricted.append({
            "path": receipt["relative_path"],
            "artifact_class": "raw source",
            "release_manifest_classification": "rights-pending",
            "artifact_hash": {
                "hash_profile": receipt["hash_profile"],
                "content_kind": receipt["content_kind"],
                "media_type": receipt["media_type"],
                "sha256": receipt["sha256"],
            },
            "restriction_scope": "raw-source",
            "reason": "Raw source redistribution remains outside the public Rule Core package.",
            "public_distribution_allowed": False,
        })
    for evidence in integrity["external_internal_evidence"]:
        restricted.append({
            "path": evidence["path"],
            "artifact_class": "geography image evidence",
            "release_manifest_classification": "rights-pending",
            "artifact_hash": generic_hash(evidence),
            "restriction_scope": "image-pixels",
            "reason": "Image pixels and image-derived evidence remain restricted from public redistribution.",
            "public_distribution_allowed": False,
        })

    evidence_paths = [
        root / "rule-core/generated/reviews/rights-clearance-publication-owner-review.md",
        root / "rule-core/generated/reviews/rights-clearance-publication-owner-review.json",
        root / "rule-core/generated/reviews/publication-license-owner-review.md",
        root / "rule-core/generated/reviews/publication-license-owner-review.json",
    ]
    return {
        "schema_version": "1.0.0",
        "record_id": RIGHTS_RECORD_ID,
        "record_status": "approved",
        "release_id": RELEASE_ID,
        "manifest_hash": {
            "hash_profile": AFWI_CONTENT_SHA256_V1,
            "content_kind": "text",
            "media_type": "application/json",
            "sha256": FROZEN_MANIFEST_SHA256,
        },
        "content_commit": CONTENT_COMMIT,
        "decision_date": "2026-09-26",
        "approved_by": "ルール所有者",
        "normative_content_changed": False,
        "previous_rights_record": None,
        "decision_evidence": [
            {"path": rel(path, root), "hash": content_hash(path, root)} for path in evidence_paths
        ],
        "cleared_for_public_distribution": cleared,
        "still_restricted": restricted,
        "issue_updates": [{
            "issue_id": "ISSUE-RIGHTS-006",
            "previous_scope": "Rule Core全体のpublic publication blocker",
            "new_scope": "raw source／原画像／第三者素材の画素を含む派生画像のpublic redistribution blocker",
            "resolution_status": "open_scope_narrowed",
        }],
        "notes": [
            "This append-only record does not alter the frozen Release Manifest or Catalog.",
            "All 18 formerly rights-pending normalized normative artifacts are cleared for public distribution.",
            "Candidate vectors are excluded by approval status, not by this rights restriction.",
        ],
    }


def package_artifact(path: Path, root: Path) -> dict[str, Any]:
    artifact_class, role, license_id, _ = artifact_identity(path, root)
    return {
        "path": rel(path, root),
        "artifact_class": artifact_class,
        "role": role,
        "source_commit": source_commit(root, rel(path, root)),
        "hash": content_hash(path, root),
        "rights_clearance_record_id": RIGHTS_RECORD_ID,
        "license_id": license_id,
    }


def excluded_artifacts(candidate_ids: list[str], integrity: dict[str, Any]) -> list[dict[str, str]]:
    excluded = [
        {"identity": vector_id, "exclusion_class": "candidate-vector", "reason": "Candidate vector is not part of the approved normative set."}
        for vector_id in candidate_ids
    ]
    excluded.append({"identity": "rule-core/tests/rule-vectors/emi-double-count-candidates.yaml", "exclusion_class": "candidate-vector", "reason": "Candidate-only vector file; all three vectors remain unapproved."})
    for receipt in integrity["external_fixed_source_receipts"]:
        excluded.append({"identity": receipt["relative_path"], "exclusion_class": "raw-source", "reason": "Raw source is represented only by minimal public receipt metadata."})
    for evidence in integrity["external_internal_evidence"]:
        excluded.append({"identity": evidence["path"], "exclusion_class": "image-evidence", "reason": "Image pixels and image-derived evidence remain restricted."})
    excluded.extend([
        {"identity": "rule-core/generated/reviews/", "exclusion_class": "owner-review", "reason": "Owner reviews remain internal approval evidence."},
        {"identity": "rule-core/governance/digital-audit/", "exclusion_class": "digital-audit-history", "reason": "Historical Digital audit evidence remains internal."},
        {"identity": "rule-core/governance/unresolved.yaml", "exclusion_class": "internal-validation-snapshot", "reason": "The frozen hash remains in release metadata; the working issue register is not distributed."},
        {"identity": "rule-core/governance/release-integrity-declarations.yaml", "exclusion_class": "internal-validation-snapshot", "reason": "Only public-safe source receipts are projected into this declaration."},
        {"identity": "rule-core/governance/source-register.yaml", "exclusion_class": "internal-validation-snapshot", "reason": "Public package exposes only approved minimum source receipt metadata."},
        {"identity": "rule-core/governance/source-fragment-register.yaml", "exclusion_class": "internal-validation-snapshot", "reason": "Source fragments may contain original-source extracts and remain internal."},
        {"identity": "rule-core/docs/design/AFWI-KAI_Rule_Core_構想と作成手順-08～11.docx", "exclusion_class": "other", "reason": "Immutable design history is not a public package artifact."},
        {"identity": "rule-core/generated/releases/*-candidate.json except the frozen final candidates", "exclusion_class": "other", "reason": "Superseded proposal snapshots are not distributed."},
    ])
    return excluded


def build_package(root: Path, artifacts: list[dict[str, Any]], rights_hash: dict[str, Any], manifest: dict[str, Any], integrity: dict[str, Any], candidate_ids: list[str]) -> dict[str, Any]:
    canonical_artifact_bytes = json.dumps(artifacts, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    aggregate = hashlib.sha256(canonical_artifact_bytes).hexdigest()
    return {
        "schema_version": "1.0.0",
        "package_id": PACKAGE_ID,
        "package_status": "proposal",
        "release_id": RELEASE_ID,
        "release_manifest": {
            "path": MANIFEST_PATH.as_posix(),
            "hash": {
                "hash_profile": AFWI_CONTENT_SHA256_V1,
                "content_kind": "text",
                "media_type": "application/json",
                "sha256": FROZEN_MANIFEST_SHA256,
            },
        },
        "publication_date": None,
        "normative_content_changed": False,
        "rights_clearance_record": {"path": RIGHTS_PATH.as_posix(), "hash": rights_hash},
        "license_declaration": {
            "status": "approved",
            "copyright_holder": "SAKANASHI Hiroaki",
            "copyright_year": 2026,
            "attribution_display_name": "AFWI-KAI Project",
            "official_url": None,
            "copyright_notice": "Copyright © 2026 SAKANASHI Hiroaki",
            "attribution_notice": "AFWI-KAI Rule Core; Attribution: AFWI-KAI Project; Copyright © 2026 SAKANASHI Hiroaki; Licensed under CC BY-SA 4.0.",
            "non_software": {
                "license_id": "CC-BY-SA-4.0",
                "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
                "applies_to": ["All declaration artifacts marked CC-BY-SA-4.0"],
            },
            "software": {
                "license_id": "MIT",
                "scope_prefixes": ["rule-core/pipeline/"],
                "excluded_repository_prefixes": ["src/", "scripts/"],
            },
            "automatic_license_exclusions": [
                "raw-source", "map-or-board-image", "geography-image-evidence",
                "third-party-material", "original-afwi-derived-element",
                "individual-rights-declaration-required",
            ],
        },
        "artifacts": artifacts,
        "excluded_artifacts": excluded_artifacts(candidate_ids, integrity),
        "public_source_receipts": [{
            "source_id": receipt["source_id"],
            "sha256": receipt["sha256"],
            "media_type": receipt["media_type"],
            "size_bytes": receipt["size_bytes"],
            "authority_classification": receipt["authority_classification"],
            "raw_file_included": False,
        } for receipt in integrity["external_fixed_source_receipts"]],
        "package_integrity": {
            "hash_profile": AFWI_CONTENT_SHA256_V1,
            "artifact_count": len(artifacts),
            "aggregate_sha256": aggregate,
        },
        "known_issues": [issue["issue_id"] for issue in manifest["known_issues"]],
        "notes": [
            "Proposal is not published; publication_date remains null.",
            "Null source_commit is permitted only for proposal artifacts not yet contained in a Git commit; approved/published declarations require real commits.",
            "aggregate_sha256 = SHA-256 of UTF-8 canonical JSON (sorted keys, compact separators) for the path-sorted artifacts array.",
            "The full internal release-integrity declaration is excluded; only minimum public source receipt metadata is projected here.",
        ],
    }


def validate_schema(instance: Any, schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(instance)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify checked-in/generated outputs without writing")
    args = parser.parse_args()
    root = repo_root()
    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    integrity = yaml.safe_load((root / "rule-core/governance/release-integrity-declarations.yaml").read_text(encoding="utf-8"))
    approved_vector_files, candidate_ids, approved_count, candidate_count = vector_inventory(root)
    paths = public_paths(root, approved_vector_files)
    classifications = frozen_classifications(manifest)
    rights = create_rights_record(root, paths, classifications, integrity)
    validate_schema(rights, root / "rule-core/schemas/rights-clearance-record.schema.json")

    if args.check:
        existing_rights = json.loads((root / RIGHTS_PATH).read_text(encoding="utf-8"))
        if existing_rights != rights:
            raise RuntimeError("rights clearance record is not reproducible")
    else:
        write_json(root / RIGHTS_PATH, rights)

    rights_hash = content_hash(root / RIGHTS_PATH, root)
    package_paths = paths + [root / RIGHTS_PATH]
    artifacts = [package_artifact(path, root) for path in sorted(package_paths, key=lambda p: rel(p, root))]
    package = build_package(root, artifacts, rights_hash, manifest, integrity, candidate_ids)
    validate_schema(package, root / "rule-core/schemas/publication-package-declaration.schema.json")

    recalculated = hashlib.sha256(json.dumps(package["artifacts"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if recalculated != package["package_integrity"]["aggregate_sha256"]:
        raise RuntimeError("package aggregate is not reproducible")
    if any(item["path"].startswith("sources/") for item in artifacts):
        raise RuntimeError("raw source leaked into package")
    if any(item["path"].endswith((".png", ".jpg", ".jpeg", ".pdf", ".docx")) for item in artifacts):
        raise RuntimeError("binary/raw image or document leaked into package")
    if any("emi-double-count-candidates.yaml" in item["path"] for item in artifacts):
        raise RuntimeError("candidate-only vector file leaked into package")
    if len(candidate_ids) != 3:
        raise RuntimeError("candidate vector exclusion count changed")
    for item in artifacts:
        path = item["path"]
        if path.startswith("rule-core/pipeline/") and item["license_id"] != "MIT":
            raise RuntimeError(f"Rule Core software lacks MIT mapping: {path}")
        if item["license_id"] == "MIT" and not (
            path.startswith("rule-core/pipeline/") or path == "rule-core/LICENSES/MIT.txt"
        ):
            raise RuntimeError(f"MIT mapping escaped the approved Rule Core software scope: {path}")
    rights_pending_cleared = [
        item for item in rights["cleared_for_public_distribution"]
        if item["release_manifest_classification"] == "rights-pending"
    ]
    if len(rights_pending_cleared) != 18:
        raise RuntimeError(f"expected 18 frozen rights-pending artifacts to be cleared, got {len(rights_pending_cleared)}")
    if len(rights["still_restricted"]) != 18:
        raise RuntimeError("restricted raw-source/image evidence count changed")

    if args.check:
        existing_package = json.loads((root / PACKAGE_PATH).read_text(encoding="utf-8"))
        if existing_package != package:
            raise RuntimeError("publication package declaration is not reproducible")
    else:
        write_json(root / PACKAGE_PATH, package)

    result = {
        "rights_record": RIGHTS_PATH.as_posix(),
        "publication_package": PACKAGE_PATH.as_posix(),
        "package_status": package["package_status"],
        "public_artifact_count": len(artifacts),
        "excluded_artifact_count": len(package["excluded_artifacts"]),
        "package_aggregate_sha256": package["package_integrity"]["aggregate_sha256"],
        "approved_vector_count": approved_count,
        "candidate_vector_count": candidate_count,
        "candidate_ids": candidate_ids,
        "null_source_commit_count": sum(item["source_commit"] is None for item in artifacts),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
