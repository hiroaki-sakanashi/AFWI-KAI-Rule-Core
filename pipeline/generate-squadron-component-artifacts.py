from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def main() -> None:
    data_path = RC / "data/squadrons.yaml"
    data = yaml.safe_load(data_path.read_text(encoding="utf-8"))
    rows = data["squadrons"]
    detailed = [row for row in rows if row["status"] == "approved"]
    all_fragments = [
        "FRAG-RULE-0910-2-PDF-P8-9-SQUADRON-ACTIVATION",
        "FRAG-RULE-0910-2-DOCX-P184-192-SQUADRON-ACTIVATION",
        "FRAG-RULE-0910-2-PDF-P19-SCENARIO1-PRC-DAY1-SQUADRONS",
        "FRAG-RULE-0910-2-DOCX-P536-541-SCENARIO1-PRC-DAY1-SQUADRONS",
        "FRAG-SQUADRON-0901-P2-STC-SQ-04",
        "FRAG-SQUADRON-0901-P3-STC-SQ-12",
        "FRAG-SQUADRON-0901-P3-STC-SQ-13",
        "FRAG-TOKEN-0901-1-P5-6-KJ-500",
        "FRAG-TOKEN-0901-1-P5-6-KQ-200",
    ]

    reference = [
        "# スコードロン部分データ参照",
        "",
        "> 非規範生成物です。正本は `rule-core/data/squadrons.yaml` と出典fragmentです。",
        "",
        "## 収録範囲",
        "",
        "KJ-500とKQ-200はルール所有者承認済みの詳細転記です。Y-9Gは名称、印字コード、陣営、KQ-200と別コンポーネントであることだけを収録し、性能を補っていません。",
        "",
    ]
    for row in rows:
        reference += [f"## {row['printed_name']}（{row['printed_code']}）", "", f"- Component ID: `{row['component_id']}`", f"- 状態: `{row['status']}`"]
        if row["status"] == "approved":
            token = row["token"]
            reference += [f"- 物理プレート: {row['physical_plate_count']}枚", f"- 最大生成: {row['max_generated_tokens']}トークン", f"- 出撃コスト: ★{row['sortie_cost_stars']}", f"- 通常生成位置: 配備基地群hex", f"- トークン: 移動{token['movement_hexes']}、センサ{token['sensor']}"]
        else:
            reference += ["- 性能・コスト・能力: `not_stated`（今回未転記）"]
        reference += [""]
    reference += ["## アクティベートvector", "", "KJ-500とKQ-200のend-to-end vectorを各1件登録しました。広東はAAR fixture由来の合法な受入試験入力であり、機種固有基地を定めません。2件は2026-09-26にルール所有者承認済みです。", ""]
    (RC / "generated/squadrons-reference.md").write_text("\n".join(reference), encoding="utf-8")

    digital = {
        "schemaVersion": "0.1.0-candidate",
        "normative": False,
        "ruleCoreVersion": data["rule_core_version"],
        "sourceSet": data["source_set"],
        "scopeStatus": "partial",
        "componentIds": [row["component_id"] for row in rows],
        "components": rows,
        "activationContract": {"status": data["activation_vector_status"]["status"], "reason": data["activation_vector_status"]["reason"], "ruleVectorIds": data["activation_vector_status"]["approved_vector_ids"], "approvedBy": data["activation_vector_status"]["approved_by"], "approvedAt": data["activation_vector_status"]["approved_at"]},
    }
    digital_path = RC / "generated/digital/squadrons.json"
    write_json(digital_path, digital)

    review = {
        "schemaVersion": 2,
        "title": "KJ-500／KQ-200 Rule Core登録確認記録",
        "normative": False,
        "status": "owner_approved_transcription_registered",
        "approvedBy": "ルール所有者",
        "approvedAt": "2026-09-25",
        "componentIds": [row["component_id"] for row in rows],
        "detailedComponents": [row["component_id"] for row in detailed],
        "identityOnlyComponents": [row["component_id"] for row in rows if row["status"] == "partial"],
        "identityRelationship": {"components": ["COMP-SQUADRON-STC-SQ-12", "COMP-SQUADRON-STC-SQ-13"], "relationship": "none"},
        "activationVectors": {"count": 2, "status": "approved", "ids": data["activation_vector_status"]["approved_vector_ids"], "approvedBy": data["activation_vector_status"]["approved_by"], "approvedAt": data["activation_vector_status"]["approved_at"]},
        "sourceFragmentIds": all_fragments,
        "componentNormativePayloadFingerprints": {row["component_id"]: fingerprint(row) for row in rows},
    }
    write_json(RC / "generated/reviews/kj-500-kq-200-owner-review.json", review)
    review_md = """# KJ-500／KQ-200 登録確認記録

本書は規範正本ではありません。2026-09-25のルール所有者承認をRule Coreへ反映した人向け記録です。

## 登録結果

- `COMP-SQUADRON-STC-SQ-04`: KJ-500。詳細転記を承認済みとして登録。
- `COMP-SQUADRON-STC-SQ-12`: Y-9G。名称、印字コード、陣営、別コンポーネントであることだけを登録。性能等は未転記。
- `COMP-SQUADRON-STC-SQ-13`: KQ-200。詳細転記を承認済みとして登録。

Y-9GとKQ-200は別コンポーネントであり、改名、前身、後継または置換の関係にありません。

## KJ-500

PRCのSTC-SQ-04。物理プレート1枚、最大1トークン、出撃コスト★2、通常は配備基地群hexへ生成します。AEWトークンは移動1、センサ2、捕捉ADV、捕捉ステップごと2回です。既存Digital ID `PRC-SQ-KJ-500` は非規範対応として保持します。

## KQ-200

PRCのSTC-SQ-13。物理プレート1枚、最大1トークン、出撃コスト★2、通常は配備基地群hexへ生成します。トークンは移動1、センサ1で、距離1以内の自軍艦による潜水艦攻撃をDIS化します。既存Digital ID `PRC-SQ-KQ-200` は非規範対応として保持します。

## 独立二回照合

ルールPDF、スコードロンPDF、トークンPDFを異なる解像度で別々に読み取り、DOCX抽出位置とも照合しました。登録fragmentはすべて `transcription_status: verified`、`comparison_result: exact_match` です。

## アクティベートvector

共通Rule／State／Eventの承認後、KJ-500とKQ-200のend-to-end candidateを各1件作成しました。広東基地群はAAR fixture由来の合法な受入試験入力で、機種固有基地ではありません。所有者承認まで未承認candidateとし、AARの15候補期待値とDigital本体は変更していません。
"""
    (RC / "generated/reviews/kj-500-kq-200-owner-review.md").write_text(review_md, encoding="utf-8")

    fragment_summary = {
        "schemaVersion": 2,
        "normative": False,
        "status": "registered_verified",
        "legacyFilenameNote": "Filename retained for continuity; entries are registered fragments, not unapproved candidates.",
        "fragmentIds": all_fragments,
        "activationRuleFragments": ["FRAG-RULE-0910-2-PDF-P8-9-SQUADRON-ACTIVATION", "FRAG-RULE-0910-2-DOCX-P184-192-SQUADRON-ACTIVATION"],
        "scenarioFragments": ["FRAG-RULE-0910-2-PDF-P19-SCENARIO1-PRC-DAY1-SQUADRONS", "FRAG-RULE-0910-2-DOCX-P536-541-SCENARIO1-PRC-DAY1-SQUADRONS"],
    }
    write_json(RC / "generated/reviews/kj-500-kq-200-source-fragment-candidates.json", fragment_summary)

    artifacts = [
        ("rule-core/data/squadrons.yaml", "normative_data"),
        ("rule-core/governance/component-id-registry.yaml", "governance"),
        ("rule-core/governance/source-fragment-register.yaml", "governance"),
        ("rule-core/governance/traceability.yaml", "traceability"),
        ("rule-core/governance/coverage.yaml", "governance"),
        ("rule-core/governance/field-ownership.yaml", "governance"),
        ("rule-core/governance/squadron-component-registration-validation-report.md", "governance"),
        ("rule-core/schemas/squadrons.schema.json", "governance"),
        ("rule-core/schemas/squadrons-digital-contract.schema.json", "governance"),
        ("rule-core/generated/squadrons-reference.md", "generated_human_reference"),
        ("rule-core/generated/reviews/kj-500-kq-200-owner-review.md", "generated_human_reference"),
        ("rule-core/generated/reviews/kj-500-kq-200-owner-review.json", "generated_human_reference"),
        ("rule-core/generated/reviews/kj-500-kq-200-source-fragment-candidates.json", "generated_human_reference"),
        ("rule-core/generated/digital/squadrons.json", "digital_candidate"),
    ]
    manifest = {
        "schemaVersion": "0.1.0", "manifestStatus": "candidate", "ruleCoreVersion": data["rule_core_version"], "sourceSet": data["source_set"],
        "generatorVersion": "0.1.0-squadron-partial", "digitalContractVersion": "0.1.0-candidate", "minDigitalVersion": None, "maxTestedDigitalVersion": None,
        "artifacts": [{"path": path, "sha256": sha256(ROOT / path), "role": role} for path, role in artifacts],
    }
    write_json(RC / "generated/digital/squadrons-manifest.json", manifest)


if __name__ == "__main__":
    main()
