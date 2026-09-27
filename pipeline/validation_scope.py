from __future__ import annotations

import hashlib
import json
from pathlib import Path


def report_historical_snapshot_status(
    root: Path,
    protected: dict[str, str],
    validator_id: str,
) -> list[dict[str, str]]:
    """Evaluate legacy hashes without treating today's shared files as historical inputs.

    The expected hashes are retained as historical evidence.  When the original bytes
    were not archived and the current shared file has legitimately moved on, replay of
    that old snapshot is unavailable; current-state validation must use current schemas
    and manifests instead of rewriting the historical hash.
    """
    mismatches: list[dict[str, str]] = []
    for relative, expected in protected.items():
        path = root / relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "missing"
        if actual != expected:
            mismatches.append({"path": relative, "expected_sha256": expected, "current_sha256": actual})
    print(json.dumps({
        "validator": validator_id,
        "scope": "historical_snapshot_validator",
        "status": "historical_input_unavailable" if mismatches else "historical_snapshot_matches_current_files",
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }, ensure_ascii=False, sort_keys=True))
    return mismatches
