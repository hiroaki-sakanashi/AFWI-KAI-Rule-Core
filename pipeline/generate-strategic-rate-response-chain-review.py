from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
GENERATOR = "rule-core/pipeline/generate-strategic-rate-response-chain-review.py"
VECTOR_PATH = RC / "tests/rule-vectors/strategic-rate-response-chain-candidates.yaml"
REVIEW_MD = RC / "generated/reviews/strategic-rate-response-chain-owner-review.md"
REVIEW_JSON = RC / "generated/reviews/strategic-rate-response-chain-owner-review.json"
REPORT = RC / "governance/strategic-rate-response-chain-coverage-report.md"
MANIFEST = RC / "generated/digital/strategic-rate-response-chain-manifest.json"
SCHEMA = RC / "schemas/strategic-rate-response-chain-owner-review.schema.json"
VALIDATOR = RC / "pipeline/validate-strategic-rate-response-chain-review.py"

FP_FIELDS = [
    "vector_id", "title", "initial_state", "operation", "fixed_randomness",
    "expected_events", "expected_final_state", "duration", "visibility",
    "interaction_type", "rule_core_ids", "source_fragment_ids", "decision_ids",
]

EXISTING_VECTORS = [
    "RV-ENABLER-US-SP-03-TRIGGER-001", "RV-ENABLER-US-SP-03-NO-TRIGGER-001",
    "RV-ENABLER-US-IW-04-TRIGGER-001", "RV-ENABLER-US-IW-04-NO-TRIGGER-001",
    "RV-ENABLER-US-IW-04-SUCCESS-001", "RV-ENABLER-US-IW-04-FAILURE-001",
    "RV-ENABLER-STC-IW-04-TRIGGER-001", "RV-ENABLER-STC-IW-04-NO-TRIGGER-001",
    "RV-ENABLER-STC-IW-04-SUCCESS-001", "RV-ENABLER-STC-IW-04-FAILURE-001",
]

CASE_TEXT = {
    "RV-ENABLER-STRATEGIC-CHAIN-US-SP-03-PASS-001": {
        "branch": "US-SP-03 → STC-IW-04 pass",
        "reason": "別の宇宙イネーブラー1枚の発動でBLUE宇宙レートが2点低下した直後にUS-SP-03を使用します。US-SP-03により共有戦略レートがBLUE方向へ1点変わるため、STC-IW-04が合法候補になります。",
        "result": "REDがpassするため、BLUE方向への1点変更を維持し、戦略レートはBLUE優勢1です。",
    },
    "RV-ENABLER-STRATEGIC-CHAIN-US-SP-03-STC-IW-04-SUCCESS-001": {
        "branch": "US-SP-03 → STC-IW-04使用 → 成功",
        "reason": "別の宇宙イネーブラー1枚の発動でBLUE宇宙レートが2点低下した直後にUS-SP-03を使用します。そのBLUE方向1点変更を対象としてSTC-IW-04を使用し、REDサイバーレート2に対するD4出目2で成功します。",
        "result": "起点のBLUE方向1点を無効化し、起点前の中央0からRED方向へ1点変更するため、戦略レートはRED優勢1です。",
    },
    "RV-ENABLER-STRATEGIC-CHAIN-US-SP-03-STC-IW-04-FAILURE-001": {
        "branch": "US-SP-03 → STC-IW-04使用 → 失敗",
        "reason": "別の宇宙イネーブラー1枚の発動でBLUE宇宙レートが2点低下した直後にUS-SP-03を使用します。そのBLUE方向1点変更を対象としてSTC-IW-04を使用し、REDサイバーレート2に対するD4出目3で失敗します。",
        "result": "起点のBLUE方向1点変更が残るため、戦略レートはBLUE優勢1です。",
    },
    "RV-ENABLER-STRATEGIC-CHAIN-US-IW-04-SOURCE-FAILURE-001": {
        "branch": "US-IW-04自身が失敗 → STC-IW-04なし",
        "reason": "PRC基地群攻撃失敗後にUS-IW-04を使用しますが、US-IW-04のD4出目1は成功条件2以上を満たしません。",
        "result": "戦略レート変更が発生しないためSTC-IW-04のwindowは開かず、戦略レートは中央0です。",
    },
    "RV-ENABLER-STRATEGIC-CHAIN-US-IW-04-PASS-001": {
        "branch": "US-IW-04成功 → STC-IW-04 pass",
        "reason": "US-IW-04のD4出目2でBLUE方向1点変更が発生し、STC-IW-04が合法候補になります。",
        "result": "REDがpassするため、BLUE方向への1点変更を維持し、戦略レートはBLUE優勢1です。",
    },
    "RV-ENABLER-STRATEGIC-CHAIN-US-IW-04-STC-IW-04-SUCCESS-001": {
        "branch": "US-IW-04成功 → STC-IW-04使用 → 成功",
        "reason": "US-IW-04のD4出目2でBLUE方向1点変更が発生します。REDサイバーレート2に対するSTC-IW-04のD4出目2は成功です。",
        "result": "起点のBLUE方向1点を無効化し、起点前の中央0からRED方向へ1点変更するため、戦略レートはRED優勢1です。",
    },
    "RV-ENABLER-STRATEGIC-CHAIN-US-IW-04-STC-IW-04-FAILURE-001": {
        "branch": "US-IW-04成功 → STC-IW-04使用 → 失敗",
        "reason": "US-IW-04のD4出目2でBLUE方向1点変更が発生します。REDサイバーレート2に対するSTC-IW-04のD4出目3は失敗です。",
        "result": "起点のBLUE方向1点変更が残るため、戦略レートはBLUE優勢1です。",
    },
}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fingerprint(vector: dict) -> str:
    return hashlib.sha256(canonical({field: vector.get(field) for field in FP_FIELDS})).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_ids(value, prefix: str) -> list[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for item in value.values():
            found.update(collect_ids(item, prefix))
    elif isinstance(value, list):
        for item in value:
            found.update(collect_ids(item, prefix))
    elif isinstance(value, str) and value.startswith(prefix):
        found.add(value)
    return sorted(found)


def dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main() -> None:
    document = load_yaml(VECTOR_PATH)
    vectors = document["vectors"]
    reviews = []
    for vector in vectors:
        reviews.append({
            "vector_id": vector["vector_id"],
            "title": vector["title"],
            "status": vector["status"],
            "coverage_before": "partially_covered",
            "initial_state": vector["initial_state"],
            "operation": vector["operation"],
            "fixed_randomness": vector["fixed_randomness"],
            "expected_events": vector["expected_events"],
            "expected_final_state": vector["expected_final_state"],
            "component_ids": collect_ids(vector, "COMP-"),
            "state_ids": collect_ids(vector, "STATE-"),
            "event_ids": collect_ids(vector, "EVENT-"),
            "rule_core_ids": vector["rule_core_ids"],
            "source_fragment_ids": vector["source_fragment_ids"],
            "decision_ids": vector["decision_ids"],
            "fingerprint_sha256": fingerprint(vector),
            "owner_answer": {"answer": "この記述で正しい", "approved_by": "ルール所有者", "approved_at": "2026-09-25"},
        })

    review = {
        "schema_version": "0.1.0",
        "review_type": "strategic_rate_response_chain_owner_approval_record",
        "non_normative": True,
        "generated_at": "2026-09-25",
        "generator": GENERATOR,
        "vector_count": len(reviews),
        "status_counts": {"candidate": 0, "approved": len(reviews)},
        "fingerprint_method": {
            "algorithm": "SHA-256",
            "serialization": "canonical JSON; UTF-8; object keys sorted; array order preserved; null explicit; no insignificant whitespace",
            "fields": FP_FIELDS,
        },
        "coverage_summary": {"covered": 7, "partially_covered": 0, "not_covered": 0, "blocked": 0, "approved_vectors": 7},
        "vectors": reviews,
    }
    REVIEW_JSON.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_JSON.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# 戦略レート即応連鎖 rule vector 所有者承認記録", "",
        "> 本記録は規範正本ではありません。2026-09-25のルール所有者承認を元のrule vectorへ反映した人向け記録です。", "",
        "- Rule Core: `0.11.0-preview-vrc`", f"- 対象vector: `{VECTOR_PATH.relative_to(ROOT).as_posix()}`",
        "- 対象数: 7件", "- 生成日: 2026-09-25", f"- 生成処理: `{GENERATOR}`",
        "- 初期共有戦略レート: 中央0", "- REDサイバーレート: 2", "- 上下限・境界処理: 今回の試験対象外", "",
        "## イベント順", "", "```text", "起点カード使用 → BLUE方向1点変更 → STC-IW-04判断",
        "  ├─ pass → 起点の1点変更を維持 → 元処理完了", "  └─ 使用 → STC-IW-04 D4",
        "       ├─ 成功 → 起点変更を無効化 → RED方向1点変更 → 元処理完了",
        "       └─ 失敗 → 起点変更を維持 → 元処理完了", "```", "",
        "US-IW-04自身の判定が失敗した場合は戦略レート変更が発生しないため、STC-IW-04判断へ進みません。", "",
        "## 一覧", "", "| vector ID | 分岐 | 最終戦略レート | status |", "| --- | --- | --- | --- |",
    ]
    for vector in vectors:
        text = CASE_TEXT[vector["vector_id"]]
        lines.append(f"| `{vector['vector_id']}` | {text['branch']} | `{dump(vector['expected_final_state']['strategic_rate'])}` | `approved` |")

    for index, vector in enumerate(vectors, 1):
        text = CASE_TEXT[vector["vector_id"]]
        random_text = "なし" if vector["fixed_randomness"] == "none" else f"`{dump(vector['fixed_randomness'])}`"
        lines += [
            "", f"## {index}. {vector['title']}", "", f"- vector ID: `{vector['vector_id']}`",
            f"- 分岐: {text['branch']}", "", "### 最初の状態", "",
            f"- 共有戦略レート: `{dump(vector['initial_state']['strategic_rate'])}`",
            f"- REDサイバーレート: `{vector['initial_state']['RED_cyber_rate']}`",
            f"- 保持カード: `{dump(vector['initial_state']['holder_has_components'])}`", "",
            "### 最初に使用するカード", "", f"`{vector['operation']['source_component_id']}`", "",
            "### 固定D4", "", random_text, "", "### STC-IW-04が候補になる理由と処理", "", text["reason"], "",
            "### 期待イベント順", "",
        ]
        lines += [f"{number}. `{dump(event)}`" for number, event in enumerate(vector["expected_events"], 1)]
        resume_text = ("US-IW-04自身の失敗を確定して処理を一度だけ完了します。戦略レート変更もSTC-IW-04の応答待ちも発生しません。"
                       if vector["vector_id"].endswith("SOURCE-FAILURE-001") else
                       "STC-IW-04の使用／pass及び必要な判定を完了した後、起点カードの未完了処理へ一度だけ戻り、その処理を完了します。")
        lines += ["", "### 期待最終状態", "", text["result"], "", f"- `{dump(vector['expected_final_state'])}`", "",
                  "### 元処理への復帰", "", resume_text, "",
                  "### 技術的な追跡情報", "", f"- Rule Core ID: {', '.join(f'`{x}`' for x in vector['rule_core_ids'])}",
                  f"- source fragment: {', '.join(f'`{x}`' for x in vector['source_fragment_ids'])}",
                  f"- fingerprint: `{fingerprint(vector)}`", "", "### ルール所有者回答", "",
                  "- [x] この記述で正しい", "- [ ] 修正が必要", "- [ ] 現時点では承認できない", "", "確認者：ルール所有者", "", "確認日：2026-09-25", ""]
    REVIEW_MD.write_text("\n".join(lines), encoding="utf-8")

    report = [
        "# 戦略レート即応連鎖 カバレッジ分析報告", "", "分析日: 2026-09-25", "",
        "## 結論", "",
        "既存の承認済み10 vectorは各カードを個別に確認します。複合経路を補う7 vectorは2026-09-25にルール所有者が承認し、起点カードから応答待ち、pass又は使用、D4判定、元処理への一度だけの復帰までの7分岐が承認済みとなりました。", "",
        "## 調査した既存vector", "",
    ]
    report += [f"- `{item}`" for item in EXISTING_VECTORS]
    report += ["", "## 分岐別判定", "", "| 必要分岐 | 承認前の既存coverage | 承認済み複合vector | blocked |", "| --- | --- | --- | --- |"]
    for vector in vectors:
        text = CASE_TEXT[vector["vector_id"]]
        report.append(f"| {text['branch']} | `partially_covered` | `{vector['vector_id']}`（2026-09-25承認済み） | なし |")
    report += [
        "", "## 数値とイベント順の根拠", "",
        "初期戦略レートは上下限に接しない中央0、REDサイバーレートは2としました。US-IW-04はD4=2で成功、D4=1で失敗します。STC-IW-04はREDサイバーレート2に対しD4=2で成功、D4=3で失敗します。複数D4は`US_IW_04_D4`と`STC_IW_04_D4`へ分離しました。", "",
        "STC-IW-04成功時は、承認済み`RV-ENABLER-STC-IW-04-SUCCESS-001`と同じく、起点のBLUE方向1点変更を無効化し、その起点前の値からRED方向へ1点変更するイベント列を使用します。内部的な相殺方法は指定していません。", "",
        "## ID語彙", "",
        "既存の`STATE-RATE-STRATEGIC`、`STATE-RATE-CYBER-PRC`、`EVENT-IMMEDIATE-ENABLER-PLAYED`、`EVENT-RATE-CHANGED`、`response_window`で表現できます。新しいRule Core ID、State ID、Event ID、interaction typeは不要です。", "",
        "## 対象外", "", "戦略レート上下限、境界外変更、Digital内部continuation／stack／resume token、一般的な即応優先順位、Digital実装は対象外です。", "",
    ]
    REPORT.write_text("\n".join(report), encoding="utf-8")

    artifacts = [
        (VECTOR_PATH, "rule_vector_approved"), (REVIEW_MD, "generated_human_reference"),
        (REVIEW_JSON, "governance"), (REPORT, "governance"), (SCHEMA, "governance"),
        (Path(__file__), "governance"), (VALIDATOR, "governance"),
    ]
    manifest = {
        "schemaVersion": "0.1.0", "manifestStatus": "candidate", "ruleCoreVersion": document["rule_core_version"],
        "sourceSet": document["source_set"], "generatorVersion": "1.0.0", "digitalContractVersion": "not_applicable",
        "minDigitalVersion": None, "maxTestedDigitalVersion": None,
        "artifacts": [{"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path), "role": role} for path, role in artifacts],
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
