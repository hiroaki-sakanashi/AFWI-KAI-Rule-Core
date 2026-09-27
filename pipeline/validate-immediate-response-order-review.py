from __future__ import annotations

import hashlib
import json
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[2]
RULE_CORE = ROOT / "rule-core"
REVIEW = RULE_CORE / "generated" / "reviews" / "immediate-response-order-owner-review.json"
SCHEMA = RULE_CORE / "schemas" / "immediate-response-order-owner-review.schema.json"
GENERATOR = RULE_CORE / "pipeline" / "generate-immediate-response-order-review.py"


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise AssertionError(message)


def validate_reproducibility(paths: list[Path]) -> None:
    before = {path: sha(path) for path in paths}
    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True, capture_output=True, text=True)
    first = {path: sha(path) for path in paths}
    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True, capture_output=True, text=True)
    second = {path: sha(path) for path in paths}
    if first != second:
        fail("two regeneration passes differ")
    if before != second:
        fail("checked-in generated review differs from regenerated output")


def main() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(review)

    enablers = load_yaml(RULE_CORE / "data" / "enablers.yaml")["components"]
    component_ids = [item["component_id"] for item in enablers]
    if len(component_ids) != 18 or len(set(component_ids)) != 18:
        fail("immediate card count or uniqueness mismatch")
    if review["scope"]["card_ids"] != component_ids:
        fail("review card IDs differ from normative card order")

    fragments = {
        item["fragment_id"]
        for item in load_yaml(RULE_CORE / "governance" / "source-fragment-register.yaml")["fragments"]
    }
    vector_ids: set[str] = set()
    vector_count = 0
    for path in [
        RULE_CORE / "tests" / "rule-vectors" / "immediate-enablers.yaml",
        RULE_CORE / "tests" / "rule-vectors" / "immediate-enablers-expansion.yaml",
    ]:
        for vector in load_yaml(path)["vectors"]:
            vector_count += 1
            if vector["vector_id"] in vector_ids:
                fail(f"duplicate vector ID: {vector['vector_id']}")
            vector_ids.add(vector["vector_id"])
            if vector.get("status") != "approved":
                fail(f"vector is not approved: {vector['vector_id']}")
    if vector_count != 47:
        fail(f"expected 47 approved immediate vectors, found {vector_count}")

    for card in review["cards"]:
        for fragment_id in card["source_fragment_ids"]:
            if fragment_id not in fragments:
                fail(f"missing source fragment: {fragment_id}")
        for vector_id in card["applicable_rule_vectors"]:
            if vector_id not in vector_ids:
                fail(f"missing applicable vector: {vector_id}")
        if card["interaction_type"] != "response_window":
            fail(f"unexpected interaction type for {card['component_id']}")

    analysis_ids = [
        item["analysis_id"]
        for key in ["same_trigger_groups", "chain_edges", "combinations", "owner_questions"]
        for item in review[key]
    ]
    if len(analysis_ids) != len(set(analysis_ids)):
        fail("duplicate analysis ID")
    registry_text = (RULE_CORE / "governance" / "rule-id-registry.yaml").read_text(encoding="utf-8")
    component_registry_text = (RULE_CORE / "governance" / "component-id-registry.yaml").read_text(encoding="utf-8")
    if any(analysis_id in registry_text or analysis_id in component_registry_text for analysis_id in analysis_ids):
        fail("analysis-only ID was registered as a normative ID")

    if len(review["owner_questions"]) != 6:
        fail("owner question count mismatch")
    if not review["integrity"]["source_snapshot"]["all_match_initial_snapshot"]:
        fail("sources do not match initial snapshot")
    if review["integrity"]["source_snapshot"]["source_count"] != 20:
        fail("source count mismatch")

    for relative, expected in review["integrity"]["protected_file_sha256"].items():
        actual = sha(ROOT / relative)
        if actual != expected:
            fail(f"protected file changed after analysis generation: {relative}")

    deprecated_ids = set()
    registry = load_yaml(RULE_CORE / "governance" / "rule-id-registry.yaml")
    for key in ("rules", "states", "events", "ids"):
        for entry in registry.get(key, []):
            if entry.get("status") == "deprecated":
                deprecated_ids.add(entry.get("id") or entry.get("rule_core_id"))
    review_text = REVIEW.read_text(encoding="utf-8")
    used_deprecated = sorted(item for item in deprecated_ids if item and item in review_text)
    if used_deprecated:
        fail(f"deprecated IDs referenced: {used_deprecated}")

    generated_paths = [
        REVIEW,
        RULE_CORE / "generated" / "reviews" / "immediate-response-order-owner-review.md",
        RULE_CORE / "generated" / "reviews" / "immediate-response-order-analysis-report.md",
    ]
    validate_reproducibility(generated_paths)

    print("PASS schema validation")
    print("PASS 18 approved immediate cards assessed")
    print("PASS 47 approved immediate vectors unchanged and referenced")
    print("PASS source fragments and analysis IDs")
    print("PASS no deprecated ID reference")
    print("PASS sources 20/20 match initial snapshot")
    print("PASS protected Rule Core fingerprints")
    print("PASS two-pass regeneration reproducibility")


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("validate-immediate-response-order-artifacts.py")), run_name="__main__")
