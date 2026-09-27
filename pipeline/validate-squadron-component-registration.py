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

def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.suffix in {".yaml", ".yml"} else json.loads(path.read_text(encoding="utf-8"))

def validate(instance: str, schema: str):
    errors = list(Draft202012Validator(load(RC / schema)).iter_errors(load(RC / instance)))
    assert not errors, f"{instance}: {errors[0].message if errors else ''}"

def sha(path: Path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    subprocess.run([sys.executable, str(RC / "pipeline/generate-squadron-component-artifacts.py")], cwd=ROOT, check=True)
    for instance, schema in [
        ("data/squadrons.yaml", "schemas/squadrons.schema.json"),
        ("generated/digital/squadrons.json", "schemas/squadrons-digital-contract.schema.json"),
        ("governance/component-id-registry.yaml", "schemas/component-id-registry.schema.json"),
        ("governance/source-fragment-register.yaml", "schemas/source-fragment-register.schema.json"),
        ("governance/coverage.yaml", "schemas/coverage.schema.json"),
        ("governance/traceability.yaml", "schemas/traceability.schema.json"),
        ("governance/field-ownership.yaml", "schemas/field-ownership.schema.json"),
        ("generated/digital/squadrons-manifest.json", "schemas/generated-manifest.schema.json"),
    ]: validate(instance, schema)
    data = load(RC / "data/squadrons.yaml")
    ids = [x["component_id"] for x in data["squadrons"]]
    assert ids == ["COMP-SQUADRON-STC-SQ-04", "COMP-SQUADRON-STC-SQ-12", "COMP-SQUADRON-STC-SQ-13"]
    assert len(ids) == len(set(ids))
    assert data["activation_vector_status"]["approved_vectors"] == 2
    assert data["activation_vector_status"]["approved_by"] == "ルール所有者"
    assert data["activation_vector_status"]["approved_at"] == "2026-09-26"
    assert set(data["activation_vector_status"]["approved_vector_ids"]) == {"RV-SQUADRON-KJ-500-ACTIVATION-001", "RV-SQUADRON-KQ-200-ACTIVATION-001"}
    relationship = data["identity_relationships"][0]
    assert relationship["relationship"] == "none"
    fragments = load(RC / "governance/source-fragment-register.yaml")["fragments"]
    fragment_ids = [x["fragment_id"] for x in fragments]
    assert len(fragment_ids) == len(set(fragment_ids))
    for row in data["squadrons"]:
        assert set(row["source_fragment_ids"]) <= set(fragment_ids)
    registry = load(RC / "governance/component-id-registry.yaml")
    registered = [x["component_id"] for x in registry["components"]]
    assert len(registered) == len(set(registered))
    assert set(ids) <= set(registered)
    manifest = load(RC / "generated/digital/squadrons-manifest.json")
    for artifact in manifest["artifacts"]:
        assert sha(ROOT / artifact["path"]) == artifact["sha256"]
    assert sha(ROOT / "tests/aar-base-cost.test.ts") == "7aa0488af2fc81eba034221127604d98be5c584494fe7cdf7679d954e005551c"
    assert sha(RC / "governance/unresolved.yaml") == "3c47ef86dd16ae67520d0c7b2b2526a1f971a505753feaff0316fce591f4bf6e"
    print("squadron component registration validation: PASS (3 component IDs, 9 verified fragments, 2 approved activation vectors)")

if __name__ == "__main__": main()
