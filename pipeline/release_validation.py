from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Iterable

import jsonschema
import yaml

from hash_profiles import hash_bytes


def _git(root: Path, *args: str, text: bool = False) -> bytes | str | None:
    completed = subprocess.run(
        ["git", *args], cwd=root, check=False, capture_output=True
    )
    if completed.returncode != 0:
        return None
    if text:
        return completed.stdout.decode("utf-8", errors="strict").strip()
    return completed.stdout


def git_blob(root: Path, commit: str, relative_path: str) -> bytes | None:
    value = _git(root, "show", f"{commit}:{relative_path}")
    return value if isinstance(value, bytes) else None


def git_commit_exists(root: Path, commit: str) -> bool:
    return _git(root, "cat-file", "-e", f"{commit}^{{commit}}") is not None


def load_bytes(data: bytes, path: str) -> Any:
    text = data.decode("utf-8-sig", errors="strict")
    if path.lower().endswith(".json"):
        return json.loads(text)
    return yaml.safe_load(text)


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


def _catalog_release_pointer(catalog: Any, release_id: str) -> dict[str, Any] | None:
    pending = [catalog]
    while pending:
        node = pending.pop()
        if isinstance(node, dict):
            if node.get("release_id") == release_id and isinstance(node.get("manifest_path"), str):
                return node
            pending.extend(node.values())
        elif isinstance(node, list):
            pending.extend(node)
    return None


def validate_historical_release(
    root: Path,
    *,
    release_id: str,
    manifest_path: str,
    catalog_path: str,
) -> dict[str, Any]:
    """Validate an immutable release entirely from its tag and historical Git trees."""
    errors: list[dict[str, Any]] = []
    tag_target = _git(root, "rev-parse", f"refs/tags/{release_id}^{{commit}}", text=True)
    if not isinstance(tag_target, str):
        return {
            "release_id": release_id,
            "status": "fail",
            "errors": [{"reason": "tag_or_metadata_commit_missing"}],
        }

    manifest_blob = git_blob(root, tag_target, manifest_path)
    catalog_blob = git_blob(root, tag_target, catalog_path)
    if manifest_blob is None:
        errors.append({"path": manifest_path, "reason": "missing_from_metadata_commit"})
    if catalog_blob is None:
        errors.append({"path": catalog_path, "reason": "missing_from_metadata_commit"})
    if errors:
        return {"release_id": release_id, "status": "fail", "tag_target": tag_target, "errors": errors}

    manifest = load_bytes(manifest_blob, manifest_path)
    catalog = load_bytes(catalog_blob, catalog_path)
    content_commit = manifest.get("content_commit")
    if not isinstance(content_commit, str) or not git_commit_exists(root, content_commit):
        errors.append({"reason": "content_commit_missing", "content_commit": content_commit})
    if manifest.get("release_id") != release_id or manifest.get("git_tag") != release_id:
        errors.append({"reason": "release_id_tag_mismatch"})
    validated_commit = manifest.get("technical_rc_freeze_validation", {}).get("validated_content_commit")
    if validated_commit != content_commit:
        errors.append({"reason": "validated_content_commit_mismatch"})
    reachable = isinstance(content_commit, str) and _git(
        root, "merge-base", "--is-ancestor", content_commit, tag_target
    ) is not None
    if not reachable:
        errors.append({"reason": "content_commit_not_reachable_from_metadata_commit"})

    pointer = _catalog_release_pointer(catalog, release_id)
    if pointer is None:
        errors.append({"reason": "catalog_release_pointer_missing"})
    else:
        actual_manifest_hash = hash_bytes(
            manifest_blob,
            hash_profile=pointer["manifest_hash_profile"],
            content_kind=pointer["manifest_content_kind"],
            media_type=pointer["manifest_media_type"],
        )
        if actual_manifest_hash != pointer["manifest_sha256"]:
            errors.append({"reason": "catalog_manifest_hash_mismatch"})
        if pointer.get("content_commit") != content_commit or pointer.get("git_tag") != release_id:
            errors.append({"reason": "catalog_release_semantics_mismatch"})

    schema_errors: list[str] = []
    artifact_errors: list[dict[str, Any]] = []
    if isinstance(content_commit, str) and git_commit_exists(root, content_commit):
        for instance, schema_path in (
            (manifest, "rule-core/schemas/release-manifest.schema.json"),
            (catalog, "rule-core/schemas/release-catalog.schema.json"),
        ):
            blob = git_blob(root, content_commit, schema_path)
            if blob is None:
                schema_errors.append(f"missing schema: {schema_path}")
                continue
            try:
                jsonschema.Draft202012Validator(load_bytes(blob, schema_path)).validate(instance)
            except Exception as exc:
                schema_errors.append(f"{schema_path}: {exc}")
        for ref in iter_artifact_refs(manifest.get("artifact_sets", [])):
            blob = git_blob(root, content_commit, ref["path"])
            if blob is None:
                artifact_errors.append({"path": ref["path"], "reason": "missing_from_content_commit"})
                continue
            actual = hash_bytes(
                blob,
                hash_profile=ref["hash_profile"],
                content_kind=ref["content_kind"],
                media_type=ref["media_type"],
            )
            if actual != ref["sha256"]:
                artifact_errors.append({"path": ref["path"], "reason": "content_commit_hash_mismatch"})

    legacy_errors: list[dict[str, Any]] = []
    legacy_manifest_count = 0
    legacy_reference_count = 0
    crlf_reference_count = 0
    raw_reference_count = 0
    if isinstance(content_commit, str) and git_commit_exists(root, content_commit):
        declaration_path = "rule-core/governance/release-integrity-declarations.yaml"
        declaration_blob = git_blob(root, content_commit, declaration_path)
        if declaration_blob is None:
            legacy_errors.append({"path": declaration_path, "reason": "missing_from_content_commit"})
        else:
            declarations = load_bytes(declaration_blob, declaration_path)
            legacy = declarations["legacy_manifest_compatibility"]
            crlf = {row["path"]: row for row in legacy["crlf_compatible_artifacts"]}
            evidence = {row["path"]: row for row in declarations["external_internal_evidence"]}
            seen_crlf: set[str] = set()
            seen_evidence: set[str] = set()
            for declaration in legacy["manifests"]:
                legacy_manifest_count += 1
                path = declaration["path"]
                blob = git_blob(root, content_commit, path)
                if blob is None:
                    legacy_errors.append({"path": path, "reason": "missing_historical_manifest"})
                    continue
                actual_manifest_hash = hash_bytes(
                    blob,
                    hash_profile=declaration["hash_profile"],
                    content_kind=declaration["content_kind"],
                    media_type=declaration["media_type"],
                )
                if actual_manifest_hash != declaration["sha256"]:
                    legacy_errors.append({"path": path, "reason": "immutable_manifest_hash_mismatch"})
                for ref in iter_artifact_refs(load_bytes(blob, path)):
                    legacy_reference_count += 1
                    relative = ref["path"].replace("\\", "/")
                    if relative in evidence:
                        seen_evidence.add(relative)
                        if ref["sha256"] != evidence[relative]["sha256"]:
                            legacy_errors.append({"path": relative, "reason": "evidence_receipt_hash_mismatch"})
                        continue
                    artifact_blob = git_blob(root, content_commit, relative)
                    if artifact_blob is None:
                        legacy_errors.append({"path": relative, "reason": "missing_historical_artifact"})
                        continue
                    compatibility = crlf.get(relative)
                    if compatibility is not None:
                        seen_crlf.add(relative)
                        actual = hash_bytes(
                            artifact_blob,
                            hash_profile=compatibility["compatibility_profile"],
                            content_kind=compatibility["content_kind"],
                            media_type=compatibility["media_type"],
                        )
                        crlf_reference_count += 1
                    else:
                        actual = hash_bytes(
                            artifact_blob,
                            hash_profile="raw-bytes-v0",
                            content_kind="binary",
                            media_type="application/octet-stream",
                        )
                        raw_reference_count += 1
                    if actual != ref["sha256"]:
                        legacy_errors.append({"path": relative, "reason": "historical_artifact_hash_mismatch"})
            if seen_crlf != set(crlf):
                legacy_errors.append({"reason": "crlf_compatibility_set_mismatch"})
            if seen_evidence != set(evidence):
                legacy_errors.append({"reason": "external_evidence_set_mismatch"})

    errors.extend({"reason": "schema_validation", "detail": item} for item in schema_errors)
    errors.extend(artifact_errors)
    errors.extend(legacy_errors)
    return {
        "release_id": release_id,
        "status": "pass" if not errors else "fail",
        "tag_target": tag_target,
        "content_commit": content_commit,
        "approved_vector_count": manifest.get("approved_vector_count"),
        "approved_fingerprint": manifest.get("approved_fingerprint"),
        "manifest_artifact_count": sum(len(row.get("artifacts", [])) for row in manifest.get("artifact_sets", [])),
        "legacy_manifest_count": legacy_manifest_count,
        "legacy_artifact_reference_count": legacy_reference_count,
        "legacy_crlf_reference_count": crlf_reference_count,
        "legacy_raw_bytes_reference_count": raw_reference_count,
        "errors": errors,
    }
