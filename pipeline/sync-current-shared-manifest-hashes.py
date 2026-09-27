from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIGITAL = ROOT / "rule-core/generated/digital"
SHARED = {
    "rule-core/governance/component-id-registry.yaml",
    "rule-core/governance/source-fragment-register.yaml",
    "rule-core/governance/coverage.yaml",
    "rule-core/governance/traceability.yaml",
    "rule-core/governance/field-ownership.yaml",
    "rule-core/governance/rule-id-registry.yaml",
}

for manifest_path in sorted(DIGITAL.glob("*-manifest.json")):
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    changed = False
    rows = document.get("artifacts", document.get("entries", []))
    for artifact in rows:
        if artifact.get("path") in SHARED:
            artifact["sha256"] = hashlib.sha256((ROOT / artifact["path"]).read_bytes()).hexdigest()
            changed = True
    if changed:
        manifest_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
