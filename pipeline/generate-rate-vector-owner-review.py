from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


ROOT = Path(__file__).resolve().parents[2]
RULE_CORE = ROOT / "rule-core"
VECTOR_SOURCE = RULE_CORE / "tests" / "rule-vectors" / "rates.yaml"
RATE_SOURCE = RULE_CORE / "data" / "rates.yaml"
REGISTRY_SOURCE = RULE_CORE / "governance" / "rule-id-registry.yaml"
FRAGMENT_SOURCE = RULE_CORE / "governance" / "source-fragment-register.yaml"
ISSUE_SOURCE = RULE_CORE / "governance" / "unresolved.yaml"
MARKDOWN_OUTPUT = RULE_CORE / "generated" / "reviews" / "rates-vector-owner-review.md"
METADATA_OUTPUT = RULE_CORE / "generated" / "reviews" / "rates-vector-owner-review.json"
GENERATOR_PATH = "rule-core/pipeline/generate-rate-vector-owner-review.py"

FINGERPRINT_NORMALIZATION = (
    "YAMLを型付きデータへ読み込み、vectorの完全なmappingをUTF-8のcanonical JSONへ変換する。"
    "object keyは昇順、配列順序は保持、nullは明示、空白は除去する。"
)
FINGERPRINT_SCOPE = [
    "vector_id", "title", "status", "initial_state", "initial_public_state",
    "target_rate_id / target_rate_ids", "trigger", "required_context", "operation",
    "fixed_randomness", "expected_events", "expected_final_state", "expected_public_state",
    "rule_core_ids", "source_fragment_ids", "decision_ids", "approval", "rights_scope",
]
NORMATIVE_PAYLOAD_EXCLUDED_FIELDS = ["status", "approval.approved_by", "approval.approved_at", "レビュー用メタデータ"]
NORMATIVE_PAYLOAD_SCOPE = [
    "vector_id", "title", "initial_state", "initial_public_state",
    "target_rate_id / target_rate_ids", "trigger", "required_context", "operation",
    "fixed_randomness", "expected_events", "expected_final_state", "expected_public_state",
    "rule_core_ids", "source_fragment_ids", "decision_ids", "rights_scope",
]

CLASS_ORDER = {
    "eligible_for_owner_review": 0,
    "blocked_by_card_transcription": 1,
    "blocked_by_geography": 2,
    "blocked_by_boundary_rule": 3,
    "blocked_by_dismissal_matrix": 4,
    "blocked_by_multiple_dependencies": 5,
    "needs_traceability_correction": 6,
}

CLASS_LABELS = {
    "eligible_for_owner_review": "所有者確認可能",
    "blocked_by_card_transcription": "カード転記待ち",
    "blocked_by_geography": "地理ID待ち",
    "blocked_by_boundary_rule": "境界処理の確定待ち",
    "blocked_by_dismissal_matrix": "更送表転記待ち",
    "blocked_by_multiple_dependencies": "複数依存待ち",
    "needs_traceability_correction": "追跡情報の修正待ち",
}

BRANCHES = {
    "RV-RATE-INITIALIZE-001": "セットアップ時の5レート初期化",
    "RV-RATE-SPACE-TWO-DIS-001": "宇宙レート2での自軍UAS・USVへのDIS適用",
    "RV-RATE-SPACE-ONE-MD-LONG-RANGE-001": "宇宙レート1で1ヘックス以上離れた攻撃への自軍MD無効",
    "RV-RATE-SPACE-ONE-MD-SAME-HEX-001": "宇宙レート1でも同一ヘックス攻撃への自軍MDは無効化されない例外",
    "RV-RATE-CYBER-INCREASE-BELOW-001": "サイバー1→2判定の閾値未満による変化なし",
    "RV-RATE-CYBER-INCREASE-AT-001": "サイバー1→2判定の閾値到達による上昇",
    "RV-RATE-CYBER-DOMINANCE-001": "ATO終了時サイバー4による次ATOのサイバードミナンス成立",
    "RV-RATE-INITIATIVE-DIFFERENCE-001": "レート合計が上回る陣営だけへの差分加算",
    "RV-RATE-INITIATIVE-NO-ADVANTAGE-001": "レート合計同値時の差分加算なし",
    "RV-RATE-STRATEGIC-SQUADRON-SCENARIO1-001": "シナリオ1のスコードロンプレート撃破による戦略レート変化",
    "RV-RATE-STRATEGIC-SQUADRON-SCENARIO2-001": "シナリオ2のスコードロンプレート撃破による戦略レート変化",
    "RV-RATE-STRATEGIC-DISMISSAL-001": "ATO終了時の戦略レート6+による劣勢側更送とゲーム終了（具体役職は対象外）",
    "RV-RATE-CYBER-ZERO-TO-ONE-001": "サイバー0→1判定の閾値到達による上昇",
    "RV-RATE-CYBER-TWO-TO-THREE-001": "サイバー2→3判定の閾値到達による上昇",
    "RV-RATE-CYBER-THREE-TO-FOUR-001": "サイバー3→4判定の閾値到達による上昇",
    "RV-RATE-INTEL-COUNT-001": "サイバーと宇宙の合計によるインテル確認数",
    "RV-RATE-STRATEGIC-NORMAL-DRAW-001": "通常終了時の戦略レート0による引き分け",
    "RV-RATE-STRATEGIC-NORMAL-ADVANTAGE-001": "通常終了時の戦略レートUS側によるUS優勢",
}

RELATED_ISSUES = {
    "RV-RATE-CYBER-INCREASE-BELOW-001": [{
        "issue_id": "ISSUE-RATE-CARD-TRANSCRIPTION-011",
        "blocking": False,
        "relation": "固有カードの同定は本vectorの対象外。確認対象は、変更要求が成立した後の閾値処理だけである。",
    }],
    "RV-RATE-CYBER-INCREASE-AT-001": [{
        "issue_id": "ISSUE-RATE-CARD-TRANSCRIPTION-011",
        "blocking": False,
        "relation": "固有カードの同定は本vectorの対象外。確認対象は、変更要求が成立した後の閾値処理だけである。",
    }],
    "RV-RATE-CYBER-ZERO-TO-ONE-001": [{
        "issue_id": "ISSUE-RATE-CARD-TRANSCRIPTION-011",
        "blocking": False,
        "relation": "固有カードの同定は本vectorの対象外。確認対象は、変更要求が成立した後の閾値処理だけである。",
    }],
    "RV-RATE-CYBER-TWO-TO-THREE-001": [{
        "issue_id": "ISSUE-RATE-CARD-TRANSCRIPTION-011",
        "blocking": False,
        "relation": "固有カードの同定は本vectorの対象外。確認対象は、変更要求が成立した後の閾値処理だけである。",
    }],
    "RV-RATE-CYBER-THREE-TO-FOUR-001": [{
        "issue_id": "ISSUE-RATE-CARD-TRANSCRIPTION-011",
        "blocking": False,
        "relation": "固有カードの同定は本vectorの対象外。確認対象は、変更要求が成立した後の閾値処理だけである。",
    }],
    "RV-RATE-STRATEGIC-DISMISSAL-001": [{
        "issue_id": "ISSUE-RATE-DISMISSAL-MATRIX-014",
        "blocking": False,
        "relation": "具体的な更送役職は本vectorの期待結果に含めない。確認対象は劣勢側の更送とゲーム終了だけである。",
    }],
}

KEY_LABELS = {
    "phase": "フェーズ", "rates": "レート", "faction": "陣営", "scenario": "シナリオ",
    "space_rate": "宇宙レート", "cyber_rate": "サイバーレート", "strategic_rate": "戦略レート",
    "token_type": "トークン種別", "attack_range_hexes": "攻撃距離（ヘックス）",
    "self_missile_defense": "自軍MD", "state_id": "状態ID", "value": "値",
    "type": "種別", "transition": "遷移", "die": "ダイス", "results": "出目列",
    "event_id": "Event ID", "rate_id": "レートID", "from": "変更前", "to": "変更後",
    "threshold": "閾値", "result": "結果", "amount": "変化量", "direction": "方向",
    "modifier": "修正", "assertion": "期待される規則適用", "game_over": "ゲーム終了",
    "holder": "保持陣営", "active_during": "有効期間", "applies_during": "適用期間",
    "effects": "効果", "center": "中央値", "achiever": "達成陣営",
    "required_context": "必要文脈", "rolling_faction": "判定陣営",
}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(vector: dict) -> str:
    canonical = json.dumps(vector, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normative_payload_fingerprint(vector: dict) -> str:
    payload = {key: value for key, value in vector.items() if key not in {"status", "approval"}}
    return fingerprint(payload)


def scalar(value) -> str:
    if value is None:
        return "`null`"
    if isinstance(value, bool):
        return "`true`" if value else "`false`"
    if isinstance(value, (int, float)):
        return f"`{value}`"
    return f"`{str(value)}`"


def structure_lines(value, indent: int = 0) -> list[str]:
    prefix = "    " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            label = KEY_LABELS.get(key, key)
            label_text = f"{label} (`{key}`)" if label != key else f"`{key}`"
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}- {label_text}:")
                lines.extend(structure_lines(item, indent + 1))
            else:
                lines.append(f"{prefix}- {label_text}: {scalar(item)}")
        return lines or [f"{prefix}- （空のmapping）"]
    if isinstance(value, list):
        lines = []
        for index, item in enumerate(value, start=1):
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{index}. 項目")
                lines.extend(structure_lines(item, indent + 1))
            else:
                lines.append(f"{prefix}{index}. {scalar(item)}")
        return lines or [f"{prefix}- （空の配列）"]
    return [f"{prefix}- {scalar(value)}"]


def locator_text(fragment: dict) -> str:
    locator = fragment["locator"]
    parts = [f"source: `{fragment['source_id']}`", f"種別: `{locator.get('type', 'not_stated')}`"]
    for key in ("pages", "page", "section", "component", "position"):
        if key in locator:
            parts.append(f"{key}: `{locator[key]}`")
    parts.extend([
        f"規範状態: `{fragment['normative_status']}`",
        f"機械抽出: `{fragment['machine_extractability']}`",
        f"視覚確認: `{fragment['visual_reviewability']}`",
        f"転記状態: `{fragment['transcription_status']}`",
        f"評価状態: `{fragment['assessment_status']}`",
    ])
    return "; ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--approval-baseline", type=Path)
    args = parser.parse_args()

    vectors_doc = load_yaml(VECTOR_SOURCE)
    rates_doc = load_yaml(RATE_SOURCE)
    registry_doc = load_yaml(REGISTRY_SOURCE)
    fragment_doc = load_yaml(FRAGMENT_SOURCE)
    issue_doc = load_yaml(ISSUE_SOURCE)

    vectors = vectors_doc["vectors"]
    if len(vectors) != 18:
        raise ValueError(f"Expected 18 rate vectors, found {len(vectors)}")

    rates = {item["rate_id"]: item for item in rates_doc["rates"]}
    rules = {item["rule_core_id"]: item for item in registry_doc["rules"]}
    fragments = {item["fragment_id"]: item for item in fragment_doc["fragments"]}
    issues = {item["issue_id"]: item for item in issue_doc["issues"]}
    previous_metadata = json.loads(METADATA_OUTPUT.read_text(encoding="utf-8")) if METADATA_OUTPUT.exists() else {}
    previous_reviews = {item["vector_id"]: item for item in previous_metadata.get("reviews", [])}
    approval_baseline = json.loads(args.approval_baseline.read_text(encoding="utf-8")) if args.approval_baseline else {}

    reviews = []
    for source_index, vector in enumerate(vectors, start=1):
        vector_id = vector["vector_id"]
        target_rate_ids = vector.get("target_rate_ids", [vector.get("target_rate_id")])
        target_rate_ids = [item for item in target_rate_ids if item]
        missing = (
            [item for item in target_rate_ids if item not in rates]
            + [item for item in vector["rule_core_ids"] if item not in rules]
            + [item for item in vector["source_fragment_ids"] if item not in fragments]
        )
        related = RELATED_ISSUES.get(vector_id, [])
        missing.extend(item["issue_id"] for item in related if item["issue_id"] not in issues)
        reviewability = "needs_traceability_correction" if missing else "eligible_for_owner_review"
        previous = previous_reviews.get(vector_id, {})
        legacy_full_before = approval_baseline.get("full_record_fingerprints", {}).get(
            vector_id,
            previous.get("legacy_full_record_fingerprint_before_approval", previous.get("fingerprint_sha256")),
        )
        normative_before = approval_baseline.get("normative_payload_fingerprints", {}).get(
            vector_id,
            previous.get("normative_payload_fingerprint_before_approval"),
        )
        if not legacy_full_before or not normative_before:
            raise ValueError(f"Missing pre-approval fingerprint for {vector_id}")
        reviews.append({
            "source_index": source_index,
            "vector_id": vector_id,
            "title": vector["title"],
            "status": vector["status"],
            "reviewability": reviewability,
            "related_issues": related,
            "branch": BRANCHES[vector_id],
            "target_rate_ids": target_rate_ids,
            "rule_core_ids": vector["rule_core_ids"],
            "source_fragment_ids": vector["source_fragment_ids"],
            "fingerprint_sha256": legacy_full_before,
            "legacy_full_record_fingerprint_before_approval": legacy_full_before,
            "full_record_fingerprint": fingerprint(vector),
            "normative_payload_fingerprint_before_approval": normative_before,
            "normative_payload_fingerprint": normative_payload_fingerprint(vector),
        })

    generated_at = args.generated_at or datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")
    metadata = {
        "schema_version": "0.1.0",
        "review_type": "rule_vector_owner_review",
        "non_normative": True,
        "generated_at": generated_at,
        "generator": GENERATOR_PATH,
        "target": {
            "rule_core_version": vectors_doc["rule_core_version"],
            "source_set": vectors_doc["source_set"],
            "vector_file": "rule-core/tests/rule-vectors/rates.yaml",
            "vector_file_sha256": sha256(VECTOR_SOURCE),
            "vector_count": len(vectors),
        },
        "fingerprint": {
            "algorithm": "SHA-256",
            "normalization": FINGERPRINT_NORMALIZATION,
            "scope": FINGERPRINT_SCOPE,
        },
        "fingerprint_migration": {
            "reason": "従来fingerprintは承認情報を含む全mappingだったため、承認反映時の内容不変確認用に規範payload fingerprintを追加した。従来値は削除せず保持する。",
            "full_record": {
                "algorithm": "SHA-256",
                "normalization": FINGERPRINT_NORMALIZATION,
                "scope": FINGERPRINT_SCOPE,
            },
            "normative_payload": {
                "algorithm": "SHA-256",
                "normalization": FINGERPRINT_NORMALIZATION,
                "scope": NORMATIVE_PAYLOAD_SCOPE,
                "excluded_fields": NORMATIVE_PAYLOAD_EXCLUDED_FIELDS,
            },
        },
        "reviews": reviews,
    }

    review_by_id = {item["vector_id"]: item for item in reviews}
    sorted_vectors = sorted(
        vectors,
        key=lambda item: (CLASS_ORDER[review_by_id[item["vector_id"]]["reviewability"]], review_by_id[item["vector_id"]]["source_index"]),
    )

    lines = [
        "# レート rule vector 承認用確認票",
        "",
        f"- 対象Rule Core: `{vectors_doc['rule_core_version']}` / source set `{vectors_doc['source_set']}`",
        "- 対象vectorファイル: `rule-core/tests/rule-vectors/rates.yaml`",
        f"- 対象vector数: `{len(vectors)}`",
        f"- 生成日時: `{generated_at}`",
        f"- generator: `{GENERATOR_PATH}`",
        f"- `full_record_fingerprint`: `SHA-256`。{FINGERPRINT_NORMALIZATION} 承認状態・承認者・承認日を含む。",
        "- `normative_payload_fingerprint`: 同じ正規化方式で、`status`、`approval.approved_by`、`approval.approved_at`、レビュー用メタデータを除外する。入力、処理、固定出目、期待結果、Rule Core ID、source fragmentを含む。",
        "- fingerprint移行理由: 従来値は全mappingを対象として承認操作でも変化するため、内容不変確認用fingerprintを追加した。従来値は各項目に保持する。",
        "",
        "> **本確認票は規範正本ではない。**",
        ">",
        "> **承認結果は元のrule vectorへ反映する。**",
        ">",
        "> **未解決依存がある項目は承認対象外。**",
        "",
        "確認可能性はrule vectorの規範的statusではありません。18件はルール所有者により2026-09-23に承認され、元vectorへ反映済みです。",
        "",
        "## 確認可能性の判断範囲",
        "",
        "- `ISSUE-RATE-CARD-TRANSCRIPTION-011`: サイバー上昇5件では固有カードを期待結果へ含めず、変更要求成立後の閾値処理だけを確認するため非停止。カード固有vectorはこの18件に含まれません。",
        "- `ISSUE-RATE-GEOGRAPHY-012`: 地理依存vectorはこの18件に含まれないため、該当vectorなし。",
        "- `ISSUE-RATE-BOUNDARY-013`: 上下限外の変更vectorはこの18件に含まれないため、該当vectorなし。",
        "- `ISSUE-RATE-DISMISSAL-MATRIX-014`: 更送vectorは具体役職を期待結果へ含めず、劣勢側更送とゲーム終了だけを確認するため非停止。具体役職vectorはこの18件に含まれません。",
        "",
        "## 全18件一覧",
        "",
        "`eligible_for_owner_review`を先に置き、各分類内では元ファイルの配列順を保持しています。元ファイル自体の配列順は変更していません。",
        "",
        "| vector ID | 対象レート | 分岐種別 | 確認可能性 | 関連issue | 主要Rule Core ID | 主要source fragment | 所有者回答 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for vector in sorted_vectors:
        review = review_by_id[vector["vector_id"]]
        issue_text = "なし" if not review["related_issues"] else "<br>".join(
            f"`{item['issue_id']}`（{'停止' if item['blocking'] else '非停止'}）" for item in review["related_issues"]
        )
        lines.append(
            f"| `{vector['vector_id']}` | {'<br>'.join(f'`{item}`' for item in review['target_rate_ids'])} | "
            f"{review['branch']} | `{review['reviewability']}` | {issue_text} | "
            f"`{review['rule_core_ids'][0]}` | `{review['source_fragment_ids'][0]}` | この記述で正しい（ルール所有者、2026-09-23） |"
        )

    lines.extend(["", "## 個別確認票", ""])
    for display_index, vector in enumerate(sorted_vectors, start=1):
        review = review_by_id[vector["vector_id"]]
        issue_entries = review["related_issues"]
        blocking = [item for item in issue_entries if item["blocking"]]
        lines.extend([
            f"### {display_index}. {vector['vector_id']} — {vector['title']}",
            "",
            f"- **vector ID:** `{vector['vector_id']}`",
            f"- **短い識別名:** {vector['title']}",
            f"- **現在のstatus:** `{vector['status']}`",
            f"- **確認可能性:** `{review['reviewability']}`（{CLASS_LABELS[review['reviewability']]}）",
            "- **関連issue:** " + ("なし" if not issue_entries else " / ".join(
                f"`{item['issue_id']}`（{'停止依存' if item['blocking'] else '非停止・期待結果範囲外'}）— {item['relation']}" for item in issue_entries
            )),
            f"- **このvectorが確認する分岐:** {review['branch']}",
            "",
            "#### 初期入力状態",
            "",
            *structure_lines(vector["initial_state"]),
            "",
            "#### 初期公開状態",
            "",
            *structure_lines(vector.get("initial_public_state", "not_stated")),
            "",
            "#### 操作または規則上の契機",
            "",
            "**契機**",
            "",
            *structure_lines(vector.get("trigger", "not_stated")),
            "",
            "**前提・宣言・選択・処理順**",
            "",
            *structure_lines(vector.get("required_context", "not_stated")),
            "",
            "**処理**",
            "",
            *structure_lines(vector["operation"]),
            "",
            "#### 固定ダイス出目または乱数列",
            "",
            *structure_lines(vector["fixed_randomness"]),
            "",
            "#### 期待イベント",
            "",
            *structure_lines(vector["expected_events"]),
            "",
            "#### 期待最終状態",
            "",
            *structure_lines(vector["expected_final_state"]),
            "",
            "#### 期待知識・可視性",
            "",
            *structure_lines(vector.get("expected_public_state", "not_stated")),
            "",
            "#### 適用Rule Core ID",
            "",
            *[f"- `{rule_id}` — {rules[rule_id]['scope']}" for rule_id in vector["rule_core_ids"]],
            "",
            "#### source fragment",
            "",
            *[f"- `{fragment_id}`" for fragment_id in vector["source_fragment_ids"]],
            "",
            "#### 元資料のページ・節・現物位置",
            "",
            *[f"- `{fragment_id}` — {locator_text(fragments[fragment_id])}" for fragment_id in vector["source_fragment_ids"]],
            "",
            "#### 前提となる規則またはデータ",
            "",
            *[f"- `{rate_id}` — {rates[rate_id]['name_ja']}（status: `{rates[rate_id]['status']}`）" for rate_id in review["target_rate_ids"]],
            *[f"- `{rule_id}` — {rules[rule_id]['scope']}" for rule_id in vector["rule_core_ids"]],
            "",
            f"- **未解決依存の有無:** {'あり — ' + ', '.join(item['issue_id'] for item in blocking) if blocking else 'なし'}",
            f"- **従来の作業前fingerprint（全record・承認前）:** `{review['legacy_full_record_fingerprint_before_approval']}`",
            f"- **full_record_fingerprint（承認後）:** `{review['full_record_fingerprint']}`",
            f"- **normative_payload_fingerprint（承認前）:** `{review['normative_payload_fingerprint_before_approval']}`",
            f"- **normative_payload_fingerprint（承認後）:** `{review['normative_payload_fingerprint']}`",
            "",
            "#### ルール所有者回答欄",
            "",
            "- [x] この記述で正しい",
            "- [ ] 修正が必要",
            "- [ ] 保留",
            "- 確認者：ルール所有者",
            "- 確認日：2026-09-23",
            "- 修正が必要な場合の指示：",
            "",
        ])

    MARKDOWN_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN_OUTPUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    METADATA_OUTPUT.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
