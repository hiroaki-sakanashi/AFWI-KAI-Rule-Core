from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
GENERATOR = RC / "pipeline/generate-md-d4-correction-owner-review.py"
OUTPUTS = [RC / "generated/reviews/md-d4-correction-owner-review.md", RC / "generated/reviews/md-d4-correction-owner-review.json"]
TARGETS = {
    "RV-MD-FULL-INTERCEPT-001": ("D4", 4),
    "RV-MD-PARTIAL-INTERCEPT-001": ("D4", 3),
    "RV-MD-FAILURE-001": ("D4", 2),
    "RV-MD-LAYERED-ADA-DECISION-001": ("naval_D4", 2),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True)
    review = json.loads(OUTPUTS[1].read_text(encoding="utf-8"))
    schema = json.loads((RC / "schemas/md-d4-correction-owner-review.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(review))
    assert not errors, errors[0].message if errors else ""
    vectors = yaml.safe_load((RC / "tests/rule-vectors/md.yaml").read_text(encoding="utf-8"))["vectors"]
    by_id = {item["vector_id"]: item for item in vectors}
    assert {item["vector_id"] for item in review["reviews"]} == set(TARGETS)
    for vector_id, (die, roll) in TARGETS.items():
        vector = by_id[vector_id]
        assert vector["status"] == "approved"
        assert vector["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-23"}
        assert vector["fixed_randomness"] == {die: roll}
        assert "D6" not in json.dumps(vector["fixed_randomness"])
    assert sum(item["status"] == "candidate" for item in vectors) == 0
    assert sum(item["status"] == "approved" for item in vectors) == 9
    before = {path: sha(path) for path in OUTPUTS}
    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True)
    assert before == {path: sha(path) for path in OUTPUTS}
    print("MD_D4_CORRECTION_REVIEW_VALIDATION_OK")
    print("review_vectors=4 reapproved=4 md_approved=9 reproducible=true")


if __name__ == "__main__":
    main()
