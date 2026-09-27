from __future__ import annotations

import hashlib
from pathlib import Path


AFWI_CONTENT_SHA256_V1 = "afwi-content-sha256-v1"
CANONICAL_TEXT_V1 = "canonical-text-v1"
RAW_BINARY_V1 = "raw-binary-v1"
RAW_BYTES_V0 = "raw-bytes-v0"
LEGACY_TEXT_CRLF_V0 = "legacy-text-crlf-v0"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_text_bytes(data: bytes) -> bytes:
    """Return canonical-text-v1 bytes without changing textual content."""
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    text = data.decode("utf-8", errors="strict")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.encode("utf-8")


def legacy_crlf_text_bytes(data: bytes) -> bytes:
    """Reconstruct the historical Windows working-tree representation."""
    had_bom = data.startswith(b"\xef\xbb\xbf")
    if had_bom:
        data = data[3:]
    text = data.decode("utf-8", errors="strict")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    encoded = text.encode("utf-8")
    return (b"\xef\xbb\xbf" + encoded) if had_bom else encoded


def hash_bytes(
    data: bytes,
    *,
    hash_profile: str,
    content_kind: str,
    media_type: str,
) -> str:
    if content_kind not in {"text", "binary"}:
        raise ValueError(f"unsupported content_kind: {content_kind}")
    if not media_type:
        raise ValueError("media_type is required")

    if hash_profile == AFWI_CONTENT_SHA256_V1:
        if content_kind == "text":
            return _sha256(canonical_text_bytes(data))
        return _sha256(data)
    if hash_profile == CANONICAL_TEXT_V1:
        if content_kind != "text":
            raise ValueError("canonical-text-v1 requires content_kind=text")
        return _sha256(canonical_text_bytes(data))
    if hash_profile == RAW_BINARY_V1:
        if content_kind != "binary":
            raise ValueError("raw-binary-v1 requires content_kind=binary")
        return _sha256(data)
    if hash_profile == RAW_BYTES_V0:
        return _sha256(data)
    if hash_profile == LEGACY_TEXT_CRLF_V0:
        if content_kind != "text":
            raise ValueError("legacy-text-crlf-v0 requires content_kind=text")
        return _sha256(legacy_crlf_text_bytes(data))
    raise ValueError(f"unsupported hash_profile: {hash_profile}")


def hash_file(
    path: Path,
    *,
    hash_profile: str,
    content_kind: str,
    media_type: str,
) -> str:
    return hash_bytes(
        path.read_bytes(),
        hash_profile=hash_profile,
        content_kind=content_kind,
        media_type=media_type,
    )
