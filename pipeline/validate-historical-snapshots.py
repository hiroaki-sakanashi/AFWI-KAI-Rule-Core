from __future__ import annotations

import ast
import argparse
import contextlib
import io
import json
import sys
from pathlib import Path

from release_validation import validate_historical_release
from validation_scope import report_historical_snapshot_status


ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
HISTORICAL_VALIDATORS = {
    "geography-generation-boundaries": ("validate-geography-generation-boundaries.py", "PROTECTED"),
    "immediate-enablers-expansion": ("validate-immediate-enablers-expansion.py", "PROTECTED"),
    "immediate-response-order": ("validate-immediate-response-order-artifacts.py", "PROTECTED"),
    "strategic-rate-response-chain": ("validate-strategic-rate-response-chain-review.py", "PROTECTED"),
    "vrc-priority-owner-review": ("validate-vrc-priority-vector-owner-review.py", "PROTECTED_HASHES"),
}
DEFAULT_RELEASE_ID = "RC-2026.09.26-01"
DEFAULT_MANIFEST = "rule-core/generated/releases/RC-2026.09.26-01-release-manifest-final-candidate.json"
DEFAULT_CATALOG = "rule-core/generated/releases/release-catalog-final-candidate.json"


def literal_assignment(path: Path, name: str) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                value = node.value
                parsed = ast.literal_eval(value)
                if not isinstance(parsed, dict):
                    raise TypeError(f"{name} in {path.name} is not a mapping")
                return parsed
    raise KeyError(f"{name} not found in {path.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate immutable releases from their historical Git trees.")
    parser.add_argument("--release-id", default=DEFAULT_RELEASE_ID)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    args = parser.parse_args()

    frozen_release = validate_historical_release(
        ROOT,
        release_id=args.release_id,
        manifest_path=args.manifest,
        catalog_path=args.catalog,
    )
    results = []
    for validator_id, (filename, variable) in HISTORICAL_VALIDATORS.items():
        protected = literal_assignment(RC / "pipeline" / filename, variable)
        protected = {
            path.removeprefix("rule-core/"): digest
            for path, digest in protected.items()
        }
        with contextlib.redirect_stdout(io.StringIO()):
            mismatches = report_historical_snapshot_status(RC, protected, validator_id)
        results.append({
            "validator": validator_id,
            "scope": "historical_snapshot_validator",
            "status": "historical_input_unavailable" if mismatches else "historical_snapshot_matches_current_files",
            "mismatch_count": len(mismatches),
        })
    summary = {
        "entrypoint": "rule-core-historical-snapshots",
        "scope": "historical_snapshot_validator",
        "current_state_validator_invoked": False,
        "result_classification": "frozen releases are verified from tag/content_commit trees; older ad hoc snapshots remain informational",
        "status": frozen_release["status"],
        "frozen_release": frozen_release,
        "informational_snapshot_results": results,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if frozen_release["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
