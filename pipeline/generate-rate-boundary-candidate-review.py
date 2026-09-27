from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
VECTOR_PATH = ROOT / "rule-core/tests/rule-vectors/rate-boundary-candidates.yaml"
REVIEW_JSON = ROOT / "rule-core/generated/reviews/rate-boundary-candidate-owner-review.json"
REVIEW_MD = ROOT / "rule-core/generated/reviews/rate-boundary-candidate-owner-review.md"
GENERATED_AT = "2026-09-25"

CASE_SUMMARIES = {
    "RV-RATE-BOUNDARY-SPACE-LOWER-OPTIONAL-INELIGIBLE-001": "US宇宙レートが0のとき、唯一の効果が1点低下である任意カードは候補にせず、判定も消費も行わず、レート0を維持します。",
    "RV-RATE-BOUNDARY-SPACE-UPPER-PLUS1-INELIGIBLE-001": "PRC宇宙レートが4のとき、唯一の効果が1点上昇である任意カードは候補にせず、カードとレートを変更しません。",
    "RV-RATE-BOUNDARY-SPACE-UPPER-PLUS2-INELIGIBLE-001": "US宇宙レートが4のとき、唯一の効果が2点上昇である任意カードは候補にせず、隠れた超過値を作りません。",
    "RV-RATE-BOUNDARY-SPACE-DIRECT-COMMAND-REJECTED-001": "US宇宙レート0からさらに低下させる不正な任意使用要求は、Eventを発生させず状態不変で拒否します。",
    "RV-RATE-BOUNDARY-SPACE-MULTI-EFFECT-001": "複数効果カードではUS宇宙レートの低下だけを下限0で止め、実際に変化できるPRC宇宙レートは1から0へ変更し、カードを使用済みにします。",
    "RV-RATE-BOUNDARY-CYBER-LOWER-OPTIONAL-INELIGIBLE-001": "PRCサイバーレートが0のとき、唯一の効果が1点低下である任意カードは候補にせず、判定も消費も行いません。",
    "RV-RATE-BOUNDARY-CYBER-UPPER-OPTIONAL-INELIGIBLE-001": "USサイバーレートが4のとき、唯一の効果が1点上昇である任意カードは候補にせず、上昇判定もカード消費も行いません。",
    "RV-RATE-BOUNDARY-STC-CY-05-ZERO-001": "USサイバーレート0でSTC-CY-05を使い、起点の上昇を取り消した後、追加の1点低下は下限0で止めます。カードは使用済みですが、値不変の追加低下についてRATE-CHANGEDは出しません。",
    "RV-RATE-BOUNDARY-STRATEGIC-OPTIONAL-INELIGIBLE-001": "戦略レートがUS優勢6のとき、さらにUS方向へ1点動かすUS-SP-03は候補にせず、カードを消費しません。",
    "RV-RATE-BOUNDARY-STRATEGIC-FORCED-PLUS1-001": "戦略レートUS優勢6で同方向の強制1点変更が生じても、起点処理だけを解決して値を6に保ち、RATE-CHANGEDとSTC-IW-04応答を発生させません。",
    "RV-RATE-BOUNDARY-STRATEGIC-FORCED-PLUS2-001": "戦略レートUS優勢6で同方向の強制2点変更が生じても、起点処理だけを解決して値を6に保ち、RATE-CHANGEDとSTC-IW-04応答を発生させません。",
    "RV-RATE-BOUNDARY-STRATEGIC-FORCED-PLUS3-001": "戦略レートPRC優勢6で同方向の強制3点変更が生じても、起点処理だけを解決して値を6に保ち、レート変更依存の応答を発生させません。",
    "RV-RATE-BOUNDARY-STRATEGIC-US6-TO-PRC1-001": "戦略レートUS優勢6からPRC方向へ1点変更すると、実値はUS優勢5になります。",
    "RV-RATE-BOUNDARY-STRATEGIC-US6-TO-PRC2-001": "戦略レートUS優勢6からPRC方向へ2点変更すると、実値はUS優勢4になります。",
    "RV-RATE-BOUNDARY-STRATEGIC-US6-TO-PRC3-001": "戦略レートUS優勢6からPRC方向へ3点変更すると、実値はUS優勢3になります。",
    "RV-RATE-BOUNDARY-STRATEGIC-PRC6-TO-US1-001": "戦略レートPRC優勢6からUS方向へ1点変更すると、実値はPRC優勢5になります。",
    "RV-RATE-BOUNDARY-STRATEGIC-PRC6-TO-US2-001": "戦略レートPRC優勢6からUS方向へ2点変更すると、実値はPRC優勢4になります。",
    "RV-RATE-BOUNDARY-STRATEGIC-PRC6-TO-US3-001": "戦略レートPRC優勢6からUS方向へ3点変更すると、実値はPRC優勢3になります。",
    "RV-RATE-BOUNDARY-STRATEGIC-RETURN5-NO-DISMISSAL-001": "ATO中に戦略レートがUS優勢6へ到達しても、ATO終了前にUS優勢5へ戻れば、ATO終了時に更迭も戦略レートによるゲーム終了も発生しません。",
    "RV-RATE-BOUNDARY-STRATEGIC-AT6-DISMISSAL-001": "ATO終了時の戦略レート実値がUS優勢6なら、PRC側を更迭してゲームを終了します。",
}


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def payload(vector: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in vector.items() if key not in {"status", "approval"}}


def fingerprint(vector: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(payload(vector))).hexdigest()


def display(value: Any) -> str:
    if value == "none":
        return "なし"
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build() -> dict[str, Any]:
    doc = yaml.safe_load(VECTOR_PATH.read_text(encoding="utf-8"))
    reviews = []
    for index, vector in enumerate(doc["vectors"], 1):
        final = vector["expected_final_state"]
        reviews.append({
            "number": index,
            "vector_id": vector["vector_id"],
            "title": vector["title"],
            "summary_ja": CASE_SUMMARIES[vector["vector_id"]],
            "status": vector["status"],
            "initial_rate": vector["initial_state"],
            "effect_kind": "forced" if vector["operation"]["type"] == "resolve_forced_rate_change" else "optional_or_rule_resolution",
            "origin": vector["initial_state"].get("component_id") or vector["initial_state"].get("source_card_code") or vector["initial_state"].get("forced_origin") or vector["operation"]["type"],
            "legal_candidate": final.get("legal_candidate", "not_applicable"),
            "determination_performed": final.get("determination_performed", "not_applicable"),
            "card_final_state": final.get("card_state", "not_applicable"),
            "requested_change": vector["operation"].get("requested_change") or vector["initial_state"].get("optional_effect") or vector["initial_state"].get("requested_effects") or vector["operation"].get("steps") or vector["operation"],
            "actual_change": final.get("actual_delta", final.get("additional_decrease_actual_delta", "see expected_final_state")),
            "final_rate": {k: v for k, v in final.items() if "rate" in k},
            "expected_events": vector["expected_events"],
            "events_not_emitted": final.get("forbidden_event_ids") or final.get("forbidden_event_ids_for_additional_decrease") or (["EVENT-RATE-CHANGED"] if final.get("no_rate_changed_event_for") else []),
            "downstream_trigger": final.get("response_window_for_COMP_ENABLER_STC_IW_04", final.get("rate_change_dependent_response_window", "not_applicable")),
            "rule_core_ids": vector["rule_core_ids"],
            "decision_ids": vector["decision_ids"],
            "source_fragment_ids": vector["source_fragment_ids"],
            "fingerprint_sha256": fingerprint(vector),
            "approval": vector["approval"],
            "owner_answer": "この記述で正しい",
        })
    return {
        "schema_version": "0.1.0",
        "document_type": "non_normative_owner_review",
        "generated_at": GENERATED_AT,
        "normative_authority": False,
        "source_vector_file": "rule-core/tests/rule-vectors/rate-boundary-candidates.yaml",
        "decision_id": "DEC-RATE-BOUNDARY-001",
        "rule_core_id": "RC-RATE-BOUNDARY-001",
        "vector_count": len(reviews),
        "fingerprint_method": "SHA-256 of canonical UTF-8 JSON; object keys sorted, array order preserved, no insignificant whitespace; status and approval excluded",
        "approval_record": {"status": "approved", "approved_by": "ルール所有者", "approved_at": "2026-09-25", "approved_vector_count": 20},
        "reviews": reviews,
    }


def render(review: dict[str, Any]) -> str:
    lines = [
        "# レート上下限 candidate rule vector 所有者確認票", "",
        f"生成日: {GENERATED_AT}", "",
        "本確認票は規範正本ではありません。2026-09-25のルール所有者承認を元のrule vectorへ反映した確認記録です。", "",
        f"対象: `{review['source_vector_file']}`（{review['vector_count']}件）", "",
        "## 確認の要点", "",
        "- `4+`と`6+`は表示上の端点で、隠れた超過値を持ちません。", "- 値を変えない単独任意効果は候補にならず、判定・消費・使用後処理を行いません。", "- 強制変更は起点処理を解決しますが、値不変ならレート変更Eventと後続triggerを生じません。", "- 複数効果は各効果を個別評価します。", "- 戦略レートの更迭はATO終了時の実値で判定します。", "",
        "## 一覧", "", "| # | vector ID | 確認内容 | 状態 | fingerprint |", "|---:|---|---|---|---|",
    ]
    for item in review["reviews"]:
        lines.append(f"| {item['number']} | `{item['vector_id']}` | {item['title']} | `approved` | `{item['fingerprint_sha256']}` |")
    for item in review["reviews"]:
        lines += [
            "", f"## {item['number']}. {item['vector_id']}", "", f"**確認内容:** {item['title']}。", "",
            item["summary_ja"], "",
            f"**初期状態:** {display(item['initial_rate'])}", "",
            f"**効果の性質・起点:** {item['effect_kind']}／{display(item['origin'])}", "",
            f"**合法候補:** {display(item['legal_candidate'])}", "",
            f"**判定:** {display(item['determination_performed'])}", "",
            f"**変更要求:** {display(item['requested_change'])}", "",
            f"**実際の変更量:** {display(item['actual_change'])}", "",
            f"**最終レート:** {display(item['final_rate'])}", "",
            f"**カードの最終状態:** {display(item['card_final_state'])}", "",
            f"**発生するEvent:** {display(item['expected_events'])}", "",
            f"**発生しないEvent:** {display(item['events_not_emitted'])}", "",
            f"**後続trigger:** {display(item['downstream_trigger'])}", "",
            f"**適用Rule Core ID:** {', '.join(f'`{x}`' for x in item['rule_core_ids'])}", "",
            f"**適用Decision ID:** {', '.join(f'`{x}`' for x in item['decision_ids'])}", "",
            f"**Fingerprint:** `{item['fingerprint_sha256']}`", "",
            "- [x] この記述で正しい", "- [ ] 修正が必要", "- [ ] 現時点では承認できない", "", "確認者：ルール所有者", "", "確認日：2026-09-25", "", "修正指示：なし", "",
        ]
    return "\n".join(lines)


def validate(review: dict[str, Any]) -> None:
    assert review["vector_count"] == 20
    assert len({item["vector_id"] for item in review["reviews"]}) == 20
    assert all(item["status"] == "approved" for item in review["reviews"])
    doc = yaml.safe_load(VECTOR_PATH.read_text(encoding="utf-8"))
    assert all(v["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-25"} for v in doc["vectors"])
    assert [item["fingerprint_sha256"] for item in review["reviews"]] == [fingerprint(v) for v in doc["vectors"]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    review = build()
    REVIEW_JSON.parent.mkdir(parents=True, exist_ok=True)
    expected_json = json.dumps(review, ensure_ascii=False, indent=2) + "\n"
    expected_md = render(review) + "\n"
    if args.check:
        assert REVIEW_JSON.read_text(encoding="utf-8") == expected_json
        assert REVIEW_MD.read_text(encoding="utf-8") == expected_md
    else:
        REVIEW_JSON.write_text(expected_json, encoding="utf-8", newline="\n")
        REVIEW_MD.write_text(expected_md, encoding="utf-8", newline="\n")
    validate(review)
    print(f"RATE_BOUNDARY_CANDIDATE_REVIEW_OK vectors={review['vector_count']}")


if __name__ == "__main__":
    main()
