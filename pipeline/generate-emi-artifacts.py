from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RULE_CORE = ROOT / "rule-core"
SOURCE = RULE_CORE / "data" / "emi-components.yaml"
APPROVED_VECTORS_SOURCE = RULE_CORE / "tests" / "rule-vectors" / "emi.yaml"
CANDIDATE_VECTORS_SOURCE = RULE_CORE / "tests" / "rule-vectors" / "emi-double-count-candidates.yaml"
HUMAN_OUTPUT = RULE_CORE / "generated" / "emi-components-reference.md"
DIGITAL_OUTPUT = RULE_CORE / "generated" / "digital" / "emi.json"
MANIFEST_OUTPUT = RULE_CORE / "generated" / "digital" / "emi-manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    data = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    approved_vectors_doc = yaml.safe_load(APPROVED_VECTORS_SOURCE.read_text(encoding="utf-8"))
    candidate_vectors_doc = yaml.safe_load(CANDIDATE_VECTORS_SOURCE.read_text(encoding="utf-8"))
    components = data["components"]
    approved_vector_ids = [vector["vector_id"] for vector in approved_vectors_doc["vectors"]]
    candidate_vector_ids = [vector["vector_id"] for vector in candidate_vectors_doc["vectors"]]
    ids = [component["component_id"] for component in components]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate EMI component IDs")

    HUMAN_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# EMIコンポーネント データ参照",
        "",
        "この文書は `rule-core/data/emi-components.yaml` から生成した人向け参照資料であり、独立した規範正本ではありません。",
        "",
        "| component ID | 名称 | 陣営 | 個数 | 形状 | 占有・表示単位 | 表示特性 | 識別表示 |",
        "| --- | --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for component in components:
        lines.append(
            "| `{component_id}` | {name_ja} | {faction} | {quantity} | 六角形 | "
            "マップ1ヘックスと同じ大きさ | 半透明 | {identifier} |".format(
                **component, identifier=component["display"]["identifier"]
            )
        )
    lines.extend(
        [
            "",
            "BLUE用とRED用は別々の物理コンポーネントです。PDF上のtop/bottomはsource fragmentの位置情報であり、ゲーム属性ではありません。",
            "",
            "出典・裁定: `SRC-EMI-0811`、`DEC-EMI-COMPONENT-001`。",
            "",
            "## Rule vector状態",
            "",
            "承認済み（2026-09-23、ルール所有者）:",
            "",
            *[f"- `{vector_id}`" for vector_id in approved_vector_ids],
            "",
            "未承認candidate:",
            "",
            *[f"- `{vector_id}`" for vector_id in candidate_vector_ids],
            "",
        ]
    )
    HUMAN_OUTPUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    digital = {
        "schemaVersion": "0.1.0",
        "digitalContractVersion": "0.1.0-candidate",
        "ruleCoreVersion": data["rule_core_version"],
        "sourceSet": data["source_set"],
        "artifactStatus": "candidate",
        "componentIds": ids,
        "components": [
            {
                "id": component["component_id"],
                "faction": component["faction"],
                "quantity": component["quantity"],
                "shape": component["shape"],
                "footprint": component["footprint"],
                "display": component["display"],
                "distinctFrom": component["distinct_component"]["from_component_id"],
                "ruleCoreIds": component["rule_core_ids"],
                "sourceFragmentIds": component["source_fragment_ids"],
                "decisionId": component["decision_id"],
            }
            for component in components
        ],
        "ruleVectorSet": {
            "approvedStatus": "approved",
            "approvedBy": "ルール所有者",
            "approvedAt": "2026-09-23",
            "approvedVectorIds": approved_vector_ids,
            "candidateVectorIds": candidate_vector_ids,
        },
    }
    DIGITAL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DIGITAL_OUTPUT.write_text(
        json.dumps(digital, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    artifacts = [
        ("rule-core/data/emi-components.yaml", "normative_data"),
        ("rule-core/rules/emi.md", "normative_rules"),
        ("rule-core/generated/emi-components-reference.md", "generated_human_reference"),
        ("rule-core/generated/digital/emi.json", "digital_candidate"),
        ("rule-core/tests/rule-vectors/emi.yaml", "rule_vector_approved"),
        ("rule-core/tests/rule-vectors/emi-double-count-candidates.yaml", "rule_vector_candidate"),
        ("rule-core/governance/traceability.yaml", "traceability"),
    ]
    manifest = {
        "schemaVersion": "0.1.0",
        "manifestStatus": "candidate",
        "ruleCoreVersion": data["rule_core_version"],
        "sourceSet": data["source_set"],
        "generatorVersion": "0.1.0",
        "digitalContractVersion": "0.1.0-candidate",
        "minDigitalVersion": None,
        "maxTestedDigitalVersion": None,
        "artifacts": [
            {"path": path, "sha256": sha256(ROOT / path), "role": role}
            for path, role in artifacts
        ],
    }
    MANIFEST_OUTPUT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
