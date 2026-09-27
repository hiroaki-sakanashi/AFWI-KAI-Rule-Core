from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
VECTOR_PATH = RC / "tests/rule-vectors/md.yaml"
BASELINE_PATH = RC / "generated/reviews/vrc-priority-vector-owner-review.json"
OUTPUT_MD = RC / "generated/reviews/md-d4-correction-owner-review.md"
OUTPUT_JSON = RC / "generated/reviews/md-d4-correction-owner-review.json"
DECISION_ID = "DEC-COMBAT-MD-DICE-001"

CORRECTIONS = {
    "RV-MD-FULL-INTERCEPT-001": {"before": "D6", "after": "D4", "roll": 4},
    "RV-MD-PARTIAL-INTERCEPT-001": {"before": "D6", "after": "D4", "roll": 3},
    "RV-MD-FAILURE-001": {"before": "D6", "after": "D4", "roll": 2},
    "RV-MD-LAYERED-ADA-DECISION-001": {"before": "naval_D6", "after": "naval_D4", "roll": 2},
}

FINGERPRINT_METHOD = {
    "algorithm": "SHA-256",
    "serialization": "RFC 8259 JSON",
    "normalization": "object keyは昇順、配列順は保持、nullはJSON nullとして明示、UTF-8、ensure_ascii=false、区切りは(',', ':')、不要な空白なし。",
    "excluded_fields": ["status", "approval"],
    "note": "既存承認票のnormative payload方式を継承する。statusとapprovalだけを除外し、vectorの残る全mappingを対象とする。",
}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def fingerprint(value: dict) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normative_payload_fingerprint(vector: dict) -> str:
    return fingerprint({key: value for key, value in vector.items() if key not in {"status", "approval"}})


def render(value) -> str:
    return "`" + json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "`"


def main() -> None:
    doc = load_yaml(VECTOR_PATH)
    vectors = {item["vector_id"]: item for item in doc["vectors"]}
    baseline_doc = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    baseline = {item["vector_id"]: item["normative_payload_fingerprint_sha256"] for item in baseline_doc["reviews"]}

    reviews = []
    for vector_id, correction in CORRECTIONS.items():
        vector = vectors[vector_id]
        after = normative_payload_fingerprint(vector)
        reviews.append({
            "vector_id": vector_id,
            "title": vector["title"],
            "status": vector["status"],
            "approval": vector["approval"],
            "dice_type_before": correction["before"],
            "dice_type_after": correction["after"],
            "fixed_roll": correction["roll"],
            "expected_events": vector["expected_events"],
            "expected_final_state": vector["expected_final_state"],
            "expected_result_changed": False,
            "before_normative_payload_fingerprint_sha256": baseline[vector_id],
            "after_normative_payload_fingerprint_sha256": after,
            "source_fragment_ids": vector["source_fragment_ids"],
            "decision_ids": [DECISION_ID],
            "owner_response": {
                "selection": "D6からD4への訂正で正しい",
                "approved_by": "ルール所有者",
                "approved_at": "2026-09-23",
            },
        })

    payload = {
        "schema_version": "0.1.0",
        "review_type": "md_d4_correction_reapproval",
        "non_normative": True,
        "generated_at": "2026-09-23",
        "generator": "rule-core/pipeline/generate-md-d4-correction-owner-review.py",
        "target_vector_file": "rule-core/tests/rule-vectors/md.yaml",
        "target_count": len(reviews),
        "fingerprint_method": FINGERPRINT_METHOD,
        "decision_id": DECISION_ID,
        "reviews": reviews,
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    lines = [
        "# MD D4訂正 再承認用確認票",
        "",
        "本確認票は規範正本ではありません。ルール所有者の再承認結果を元のrule vectorへ反映済みです。",
        "",
        "- 対象vectorファイル: `rule-core/tests/rule-vectors/md.yaml`",
        f"- 対象vector数: {len(reviews)}",
        "- 生成日: 2026-09-23",
        "- generator: `rule-core/pipeline/generate-md-d4-correction-owner-review.py`",
        "- 訂正decision: `DEC-COMBAT-MD-DICE-001`",
        "- fingerprint: statusとapprovalを除外したvector mappingのcanonical JSON（key昇順、配列順保持、UTF-8、空白なし）のSHA-256",
        "",
        "MD判定にはD4を使用します。ADA及びMD艦艇に置く物理的なD6は対空残弾数を示すカウンターであり、MD判定では振りません。",
        "",
    ]
    for index, review in enumerate(reviews, 1):
        lines += [
            f"## {index}. `{review['vector_id']}` — {review['title']}",
            "",
            f"- 現在のstatus: `{review['status']}`",
            f"- 訂正前のダイス種別: `{review['dice_type_before']}`",
            f"- 訂正後のダイス種別: `{review['dice_type_after']}`",
            f"- 固定出目: `{review['fixed_roll']}`",
            f"- 期待イベント: {render(review['expected_events'])}",
            f"- 期待最終状態: {render(review['expected_final_state'])}",
            "- 期待結果の変更: `なし`（ダイス種別だけを訂正）",
            f"- 訂正前fingerprint: `{review['before_normative_payload_fingerprint_sha256']}`",
            f"- 訂正後fingerprint: `{review['after_normative_payload_fingerprint_sha256']}`",
            f"- source fragment: {', '.join(f'`{item}`' for item in review['source_fragment_ids'])}",
            f"- decision ID: `{DECISION_ID}`",
            "",
            "### ルール所有者承認欄",
            "",
            "- [x] D6からD4への訂正で正しい",
            "- [ ] 修正が必要",
            "- [ ] 現時点では承認できない",
            "- 確認者：ルール所有者",
            "- 確認日：2026-09-23",
            "- 指示：4件とも、D6からD4への訂正および記載された期待結果で正しい。再承認します。",
            "",
        ]
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
