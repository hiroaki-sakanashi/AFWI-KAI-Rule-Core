from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
OUTPUT_MD = RC / "generated/reviews/vrc-priority-vector-owner-review.md"
OUTPUT_JSON = RC / "generated/reviews/vrc-priority-vector-owner-review.json"
GENERATOR = "rule-core/pipeline/generate-vrc-priority-vector-owner-review.py"

SOURCES = [
    ("md", "MD", "tests/rule-vectors/md.yaml", 9),
    ("immediate_enablers", "即応", "tests/rule-vectors/immediate-enablers.yaml", 18),
    ("intel", "インテル", "tests/rule-vectors/intel.yaml", 6),
    ("cyber_dominance", "Cyber Dominance", "tests/rule-vectors/cyber-dominance-candidates.yaml", 2),
]

FINGERPRINT_METHOD = {
    "algorithm": "SHA-256",
    "serialization": "RFC 8259 JSON",
    "normalization": (
        "vectorの完全なmappingをcanonical JSON化する。object keyは昇順、配列順は保持、"
        "nullはJSON nullとして明示、UTF-8、ensure_ascii=false、区切りは(',', ':')、不要な空白なし。"
    ),
    "scope": [
        "vector_id", "title", "status", "initial_state", "operation", "fixed_randomness",
        "expected_events", "expected_final_state", "expected_public_state（存在する場合）",
        "rule_core_ids", "source_fragment_ids", "decision_ids", "approval", "rights_scope",
    ],
    "note": (
        "完全mappingを対象とするため、指定されたRule Core ID、source fragment、初期状態、操作、"
        "固定入力、期待イベント、期待最終状態、knowledge / visibility effect、interaction typeを"
        "表す既存フィールドを包含する。欠けているフィールドを補完してfingerprint対象へ加えない。"
    ),
}

RELATED_CANDIDATES = {
    "md": [{
        "candidate": "MDの公開範囲",
        "status": "not_stated",
        "relation": "正式資料に公開範囲の明記がない。vectorへ公開規則を補わない。",
    }],
    "immediate_enablers": [{
        "candidate": "同一タイミングに複数の即応が成立した場合の選択・解決順",
        "status": "not_stated",
        "relation": "各カードのtrigger成立・不成立だけを確認し、複数成立時の順序を補わない。",
    }],
    "intel": [{
        "candidate": "両陣営のインテル活動の実施順",
        "status": "not_stated",
        "relation": "各対象・判定・確認数だけを確認し、両陣営の実施順を補わない。",
    }],
    "cyber_dominance": [],
}

DOMAIN_NOT_CHECKED = {
    "md": "MDの公開範囲、および当該vectorの期待結果に記載されていないMD分岐。公開範囲は `not_stated` のままとする。",
    "immediate_enablers": "同一タイミングに複数の即応が成立した場合の選択権・優先順位・解決順、およびカード固有効果の解決。",
    "intel": "両陣営のインテル活動の実施順、および当該vectorの期待結果に記載されていない対象・判定。",
    "cyber_dominance": "当該vectorの期待結果に記載されていない効果。失効時の非巻戻し確認は、新しい効果を追加するものではない。",
}

REVIEW_SUMMARIES = {
    "RV-INTEL-SQUADRON-SUCCESS-001": (
        "確認数1を消費し、選択した配備済み未捕捉スコードロンプレート1枚だけについて捕捉判定を行う。"
    ),
    "RV-INTEL-SQUADRON-FAILURE-001": (
        "配備済み未捕捉スコードロンプレート1枚を選択して捕捉判定を行う。判定に失敗した場合、"
        "スコードロンの捕捉状態・公開状態その他の状態は一切変更せず、確認可能数だけを1消費する。"
    ),
    "RV-RATE-CYBER-DOMINANCE-DETAIL-001": (
        "Cyber Dominanceにより、相手の現在の★から10個を減らす。40から30になるのは、"
        "他の減少・拘束がない場合の例であり、固定値30への設定ではない。"
    ),
}

KEY_LABELS = {
    "active": "有効", "active_during": "有効期間", "acquired_squadrons": "捕捉済みスコードロン",
    "ADA_MD_eligible": "ADAのMD適格性", "ADA_decision_available": "ADA判断可否",
    "anti_air_ammunition": "対空弾薬", "attack_nullified": "攻撃無効", "attack_type": "攻撃種別",
    "component_id": "Component ID", "confirmations_remaining": "確認可能残数", "continue_attack": "攻撃継続",
    "cyber_dominance": "Cyber Dominance", "D4": "D4", "D6": "D6", "decision": "宣言選択",
    "deployed_squadrons_acquired": "配備済みスコードロン捕捉", "event_id": "Event ID",
    "hit_roll": "命中ロール", "hit_roll_started": "命中ロール開始済み", "holder": "保持陣営",
    "holder_has_component": "保持Component", "interaction_order": "処理順", "interaction_type": "interaction type",
    "legal": "合法", "legal_to_play": "使用可否", "layer": "層", "md_layer_pending": "MD層保留",
    "md_result_pending": "MD結果保留", "md_value": "MD値", "naval_D4": "海軍MD D4",
    "naval_MD_eligible": "海軍MD適格性", "naval_MD_resolved": "海軍MD解決済み",
    "observed_condition": "観測条件", "opponent_hand_card_revealed": "相手手札カード公開",
    "opponent_selected_enablers_revealed": "相手選択済みイネーブラー公開",
    "opponent_signs_revealed": "相手兆候公開", "opponent_usable_command_stars": "相手使用可能指揮所活性",
    "printed_trigger_condition": "印字trigger条件", "quantity": "数量", "result": "結果",
    "revealed_components": "公開済みComponent", "revealed_signs": "公開済み兆候",
    "squadron_acquired": "スコードロン捕捉", "squadron_deployed": "スコードロン配備済み",
    "record_only": "判定記録のみ", "state_change": "状態変更", "state_id": "State ID",
    "target_hex_signs": "対象Hexの兆候数", "target_type": "操作段階で選択する種別",
    "targeted_MD_layer": "対象MD層", "targets": "対象", "type": "操作種別", "visibility": "可視性",
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


def collect_prefixed(value, prefix: str) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for item in value.values():
            found |= collect_prefixed(item, prefix)
    elif isinstance(value, list):
        for item in value:
            found |= collect_prefixed(item, prefix)
    elif isinstance(value, str) and value.startswith(prefix):
        found.add(value)
    return found


def collect_state_ids(vector: dict) -> list[str]:
    ids = collect_prefixed(vector, "STATE-")
    keys = set()

    def walk(value):
        if isinstance(value, dict):
            keys.update(value.keys())
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(vector)
    if keys & {"md_layer_pending", "md_result_pending", "targeted_MD_layer"}:
        ids.add("STATE-MD-LAYER-PENDING")
    if "confirmations_remaining" in keys:
        ids.add("STATE-INTEL-CONFIRMATIONS-REMAINING")
    if keys & {"opponent_hand_card_revealed", "revealed_signs", "revealed_components", "opponent_signs_revealed", "opponent_selected_enablers_revealed"}:
        ids.add("STATE-COMPONENT-REVEALED")
    if keys & {"squadron_acquired", "acquired_squadrons", "deployed_squadrons_acquired"}:
        ids.add("STATE-SQUADRON-ACQUIRED")
    if keys & {"cyber_dominance", "holder", "active_during"} and any("CYBER-DOMINANCE" in item for item in vector["rule_core_ids"]):
        ids.add("STATE-CYBER-DOMINANCE")
    return sorted(ids)


def interaction_types(domain: str, vector: dict) -> list[str]:
    explicit = vector.get("expected_final_state", {}).get("interaction_type")
    if explicit:
        return [explicit]
    operation = vector["operation"]["type"]
    if domain == "md":
        if operation == "resolve_MD":
            return ["automatic_resolution"]
        if operation == "resolve_first_MD_then_offer_second":
            return ["automatic_resolution", "response_window"]
        return ["response_window"]
    if domain == "intel":
        if vector["operation"].get("target_type") == "deployed_unacquired_squadron":
            return ["sequential_action", "automatic_resolution"]
        return ["sequential_action"]
    if domain == "cyber_dominance":
        return ["automatic_resolution"]
    return ["not_stated"]


def visibility_effect(domain: str, vector: dict):
    if vector["vector_id"] == "RV-INTEL-SQUADRON-FAILURE-001":
        return {
            "squadron_acquisition_state_change": "none",
            "squadron_public_state_change": "none",
            "visibility_change": "none",
            "all_squadron_plates_state_change": "none",
            "confirmations_remaining_change": -1,
        }
    if domain in {"md", "immediate_enablers"}:
        return "not_stated"
    result = {}
    if "expected_public_state" in vector:
        result["expected_public_state"] = vector["expected_public_state"]
    visibility_keys = {
        key: value for key, value in vector["expected_final_state"].items()
        if key == "visibility" or "reveal" in key or "acquired" in key
    }
    if visibility_keys:
        result["expected_final_state"] = visibility_keys
    return result or "not_stated"


def scalar(value) -> str:
    if value is None:
        return "`null`"
    if isinstance(value, bool):
        return "`true`" if value else "`false`"
    if isinstance(value, (int, float)):
        return f"`{value}`"
    return f"`{value}`"


def structure_lines(value, indent: int = 0) -> list[str]:
    prefix = "    " * indent
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            label = KEY_LABELS.get(key, key)
            heading = f"{label} (`{key}`)" if label != key else f"`{key}`"
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}- {heading}:")
                lines.extend(structure_lines(item, indent + 1))
            else:
                lines.append(f"{prefix}- {heading}: {scalar(item)}")
        return lines or [f"{prefix}- （空）"]
    if isinstance(value, list):
        lines = []
        for index, item in enumerate(value, 1):
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{index}. 項目")
                lines.extend(structure_lines(item, indent + 1))
            else:
                lines.append(f"{prefix}{index}. {scalar(item)}")
        return lines or [f"{prefix}- （空）"]
    return [f"{prefix}- {scalar(value)}"]


def actor(vector: dict) -> str:
    for container in (vector.get("operation", {}), vector.get("initial_state", {})):
        for key in ("actor", "acting_faction", "faction"):
            if key in container:
                return str(container[key])
    return "not_stated"


def target(vector: dict) -> str:
    if vector["vector_id"] == "RV-INTEL-SQUADRON-FAILURE-001":
        return "操作段階で選択する配備済み未捕捉スコードロンプレート1枚"
    operation = vector.get("operation", {})
    for key in ("target", "target_type", "component_id"):
        if key in operation:
            return str(operation[key])
    return "not_stated"


def scenario_scope(vector: dict) -> str:
    for container in (vector.get("operation", {}), vector.get("initial_state", {})):
        for key in ("scenario", "scenario_id", "scenario_scope"):
            if key in container:
                return str(container[key])
    return "not_stated"


def locator(fragment: dict) -> str:
    loc = fragment["locator"]
    parts = [f"source `{fragment['source_id']}`", f"種別 `{loc.get('type', 'not_stated')}`"]
    for key in ("pages", "page", "section", "printed_code", "component", "position"):
        if key in loc:
            parts.append(f"{key} `{loc[key]}`")
    return "; ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--approval-baseline", type=Path)
    args = parser.parse_args()

    rules = {x["rule_core_id"]: x for x in load_yaml(RC / "governance/rule-id-registry.yaml")["rules"]}
    components = {x["component_id"]: x for x in load_yaml(RC / "governance/component-id-registry.yaml")["components"]}
    state_events = load_yaml(RC / "data/state-and-event-ids.yaml")
    states = {x["state_id"]: x for x in state_events["states"]}
    events = {x["event_id"]: x for x in state_events["events"]}
    fragments = {x["fragment_id"]: x for x in load_yaml(RC / "governance/source-fragment-register.yaml")["fragments"]}
    trace = {x["target_id"]: x for x in load_yaml(RC / "governance/traceability.yaml")["mappings"]}

    documents = []
    vectors = []
    for domain, label, relative, expected in SOURCES:
        path = RC / relative
        doc = load_yaml(path)
        if len(doc["vectors"]) != expected:
            raise ValueError(f"{relative}: expected {expected}, found {len(doc['vectors'])}")
        documents.append({
            "domain": domain, "label": label, "path": f"rule-core/{relative}",
            "sha256": sha256(path), "count": len(doc["vectors"]),
        })
        for source_index, vector in enumerate(doc["vectors"], 1):
            vectors.append((domain, label, relative, source_index, vector))
    if len(vectors) != 35:
        raise ValueError(f"Expected 35 vectors, found {len(vectors)}")

    generated_at = args.generated_at or datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")
    previous_metadata = json.loads(OUTPUT_JSON.read_text(encoding="utf-8")) if OUTPUT_JSON.exists() else {}
    previous_reviews = {x["vector_id"]: x for x in previous_metadata.get("reviews", [])}
    approval_baseline = json.loads(args.approval_baseline.read_text(encoding="utf-8")) if args.approval_baseline else {}
    reviews = []
    for overall_index, (domain, label, relative, source_index, vector) in enumerate(vectors, 1):
        component_ids = sorted(collect_prefixed(vector, "COMP-"))
        state_ids = collect_state_ids(vector)
        event_ids = sorted(collect_prefixed(vector.get("expected_events", []), "EVENT-"))
        missing = []
        missing += [f"Rule Core ID:{x}" for x in vector["rule_core_ids"] if x not in rules]
        missing += [f"deprecated Rule Core ID:{x}" for x in vector["rule_core_ids"] if x in rules and rules[x]["status"] == "deprecated"]
        missing += [f"Component ID:{x}" for x in component_ids if x not in components]
        missing += [f"State ID:{x}" for x in state_ids if x not in states]
        missing += [f"Event ID:{x}" for x in event_ids if x not in events]
        missing += [f"source fragment:{x}" for x in vector["source_fragment_ids"] if x not in fragments]
        if vector["vector_id"] not in trace:
            missing.append(f"traceability:{vector['vector_id']}")
        else:
            mapping = trace[vector["vector_id"]]
            if set(mapping["rule_core_ids"]) != set(vector["rule_core_ids"]):
                missing.append("traceability:Rule Core ID不一致")
            if set(mapping["source_fragment_ids"]) != set(vector["source_fragment_ids"]):
                missing.append("traceability:source fragment不一致")
            if mapping.get("rule_vector_status") != vector["status"]:
                missing.append("traceability:status不一致")
        current_fingerprint = fingerprint(vector)
        current_payload_fingerprint = normative_payload_fingerprint(vector)
        previous_review = previous_reviews.get(vector["vector_id"], {})
        previous_current_fingerprint = previous_review.get("pre_generation_fingerprint_sha256", current_fingerprint)
        baseline_fingerprint = previous_review.get(
            "baseline_fingerprint_sha256",
            previous_current_fingerprint,
        )
        if previous_current_fingerprint == current_fingerprint:
            previous_generation_fingerprint = previous_review.get(
                "previous_generation_fingerprint_sha256", previous_current_fingerprint,
            )
            changed_from_previous_generation = previous_review.get(
                "fingerprint_changed_from_previous_generation", False,
            )
        else:
            previous_generation_fingerprint = previous_current_fingerprint
            changed_from_previous_generation = previous_generation_fingerprint != current_fingerprint
        pre_approval_full_fingerprint = approval_baseline.get("full_record_fingerprints", {}).get(
            vector["vector_id"],
            previous_review.get("pre_approval_full_record_fingerprint_sha256", previous_current_fingerprint),
        )
        pre_approval_payload_fingerprint = approval_baseline.get("normative_payload_fingerprints", {}).get(
            vector["vector_id"],
            previous_review.get("pre_approval_normative_payload_fingerprint_sha256", current_payload_fingerprint),
        )
        reviews.append({
            "overall_index": overall_index,
            "source_index": source_index,
            "source_file": f"rule-core/{relative}",
            "domain": domain,
            "domain_label": label,
            "vector_id": vector["vector_id"],
            "title": vector["title"],
            "review_summary": REVIEW_SUMMARIES.get(vector["vector_id"], vector["title"]),
            "status": vector["status"],
            "reviewability": "needs_traceability_correction" if missing else "eligible_for_owner_review",
            "traceability_errors": missing,
            "rule_core_ids": vector["rule_core_ids"],
            "component_ids": component_ids,
            "state_ids": state_ids,
            "event_ids": event_ids,
            "source_fragment_ids": vector["source_fragment_ids"],
            "scenario_scope": scenario_scope(vector),
            "actor": actor(vector),
            "target": target(vector),
            "interaction_types": interaction_types(domain, vector),
            "knowledge_visibility_effect": visibility_effect(domain, vector),
            "related_unresolved_candidates": RELATED_CANDIDATES[domain],
            "baseline_fingerprint_sha256": baseline_fingerprint,
            "previous_generation_fingerprint_sha256": previous_generation_fingerprint,
            "pre_generation_fingerprint_sha256": current_fingerprint,
            "fingerprint_changed_from_baseline": baseline_fingerprint != current_fingerprint,
            "fingerprint_changed_from_previous_generation": changed_from_previous_generation,
            "pre_approval_full_record_fingerprint_sha256": pre_approval_full_fingerprint,
            "full_record_fingerprint_sha256": current_fingerprint,
            "pre_approval_normative_payload_fingerprint_sha256": pre_approval_payload_fingerprint,
            "normative_payload_fingerprint_sha256": current_payload_fingerprint,
            "approval": vector["approval"],
        })

    metadata = {
        "schema_version": "0.1.0",
        "review_type": "vrc_priority_rule_vector_owner_review",
        "non_normative": True,
        "generated_at": generated_at,
        "generator": GENERATOR,
        "rule_core_version": "0.11.0-preview-vrc",
        "source_set": "SRCSET-20260923-INITIAL",
        "target_count": len(vectors),
        "domain_counts": {domain: expected for domain, _, _, expected in SOURCES},
        "source_files": documents,
        "fingerprint_method": FINGERPRINT_METHOD,
        "approval": {
            "status": "approved" if all(v[4]["status"] == "approved" for v in vectors) else "mixed",
            "approved_by": "ルール所有者" if all(v[4]["approval"]["approved_by"] == "ルール所有者" for v in vectors) else None,
            "approved_at": "2026-09-23" if all(v[4]["approval"]["approved_at"] == "2026-09-23" for v in vectors) else None,
        },
        "reviews": reviews,
    }

    review_by_id = {x["vector_id"]: x for x in reviews}
    eligible = [x for x in reviews if x["reviewability"] == "eligible_for_owner_review"]
    corrections = [x for x in reviews if x["reviewability"] == "needs_traceability_correction"]
    lines = [
        "# VRC優先5件 candidate rule vector ルール所有者承認用確認票",
        "",
        "> **本確認票は規範正本ではありません。既存candidateから生成した人向けレビュー資料です。**",
        ">",
        "> **承認結果は元のrule vectorへ反映済みです。**",
        ">",
        "> **追跡情報に不整合がある項目は承認対象外です。**",
        "",
        f"- 対象Rule Core: `0.11.0-preview-vrc`（改訂11）",
        f"- source set: `SRCSET-20260923-INITIAL`",
        f"- 対象vector数: `{len(vectors)}`",
        f"- 生成日時: `{generated_at}`",
        f"- generator: `{GENERATOR}`",
        f"- fingerprint: `SHA-256`。{FINGERPRINT_METHOD['normalization']}",
        "- 既存candidateの入力・状態・参照・期待結果は変更していません。",
        "",
        "## 確認範囲",
        "",
        "- MD: 宣言あり／なし、完全迎撃、部分迎撃、失敗、宣言時弾薬消費、レイヤード防衛、海軍MD結果後のADA判断、STC-RF-05介入。公開範囲は `not_stated`。",
        "- 即応: 9枚それぞれの印字trigger成立／不成立。複数即応が同一タイミングに成立した場合の選択・解決順は補わない。",
        "- インテル: 相手手札、兆候所在Hex、捕捉成功／失敗、失敗時消費、確認数上限。両陣営の実施順は補わない。",
        "- Cyber Dominance: 相手兆候マーカーの公開、相手が当該ATOに選択したイネーブラーの公開、配備済みスコードロンの全捕捉、指揮所活性−10、次ATO終了までの有効期間、失効Eventを確認する。失効時には公開済み情報を再び隠さず、既知情報を忘れさせず、捕捉状態を自動解除しない。最後の3点は新しい効果ではなく、正式資料にない自動巻戻しを実装要件へ混入させないための確認。",
        "",
        "## 全35件一覧",
        "",
        "| vector ID | 対象領域 | 確認する分岐 | 確認可能性 | 関連する未解決候補 | 主要Rule Core ID | 主要source fragment | 所有者回答 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for review in eligible + corrections:
        related = review["related_unresolved_candidates"]
        related_text = "なし" if not related else "<br>".join(x["candidate"] for x in related)
        lines.append(
            f"| `{review['vector_id']}` | {review['domain_label']} | {review['review_summary']} | "
            f"`{review['reviewability']}` | {related_text} | `{review['rule_core_ids'][0]}` | "
            f"`{review['source_fragment_ids'][0]}` | この記述で正しい（ルール所有者、2026-09-23） |"
        )

    lines += ["", "## 追跡情報の修正が必要な項目", ""]
    if corrections:
        for item in corrections:
            lines.append(f"- `{item['vector_id']}` — {' / '.join(item['traceability_errors'])}")
    else:
        lines.append("- なし")
    lines += ["", "## 所有者確認可能な個別確認票", ""]

    vector_map = {v["vector_id"]: v for _, _, _, _, v in vectors}
    for display_index, review in enumerate(eligible, 1):
        vector = vector_map[review["vector_id"]]
        related = review["related_unresolved_candidates"]
        related_text = "なし" if not related else " / ".join(
            f"{x['candidate']}（`{x['status']}`）— {x['relation']}" for x in related
        )
        state_text = " / ".join(f"`{x}`" for x in review["state_ids"]) or "`not_applicable`"
        event_text = " / ".join(f"`{x}`" for x in review["event_ids"]) or "`not_applicable`"
        component_text = " / ".join(f"`{x}`" for x in review["component_ids"]) or "`not_applicable`"
        lines += [
            f"### {display_index}. {review['vector_id']} — {review['title']}",
            "",
            f"- **vector ID:** `{review['vector_id']}`",
            f"- **対象領域:** {review['domain_label']}",
            f"- **確認する規則・分岐:** {review['review_summary']}",
            f"- **現在のstatus:** `{review['status']}`",
            f"- **承認者:** `{review['approval']['approved_by']}`",
            f"- **承認日:** `{review['approval']['approved_at']}`",
            f"- **確認可能性:** `{review['reviewability']}`",
            f"- **適用Rule Core ID:** {' / '.join(f'`{x}`' for x in review['rule_core_ids'])}",
            f"- **Component ID:** {component_text}",
            f"- **使用するState ID:** {state_text}",
            f"- **使用するEvent ID:** {event_text}",
            f"- **source fragment:** {' / '.join(f'`{x}`' for x in review['source_fragment_ids'])}",
            f"- **scenario適用範囲:** `{review['scenario_scope']}`",
            f"- **Actor:** `{review['actor']}`",
            f"- **Target:** `{review['target']}`",
            f"- **interaction type:** {' / '.join(f'`{x}`' for x in review['interaction_types'])}",
            "",
            "#### 初期状態",
            "",
            *structure_lines(vector["initial_state"]),
            "",
            "#### 操作・宣言",
            "",
            *structure_lines(vector["operation"]),
            "",
            "#### 固定する出目または判定入力",
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
            "#### knowledge / visibility effect",
            "",
            *structure_lines(review["knowledge_visibility_effect"]),
            "",
            "#### 元資料のページ・節・現物位置",
            "",
            *[f"- `{fragment_id}` — {locator(fragments[fragment_id])}" for fragment_id in vector["source_fragment_ids"]],
            "",
            f"- **このvectorが確認しない事項:** {DOMAIN_NOT_CHECKED[review['domain']]} ",
            f"- **関連する未解決候補:** {related_text}",
            f"- **前回確認票baseline fingerprint:** `{review['baseline_fingerprint_sha256']}`",
            f"- **直前生成時fingerprint:** `{review['previous_generation_fingerprint_sha256']}`",
            f"- **今回fingerprint:** `{review['pre_generation_fingerprint_sha256']}`",
            f"- **baselineからの変更:** `{'yes' if review['fingerprint_changed_from_baseline'] else 'no'}`",
            f"- **直前生成時からの変更:** `{'yes' if review['fingerprint_changed_from_previous_generation'] else 'no'}`",
            f"- **承認前normative payload fingerprint:** `{review['pre_approval_normative_payload_fingerprint_sha256']}`",
            f"- **承認後normative payload fingerprint:** `{review['normative_payload_fingerprint_sha256']}`",
            "",
            "#### ルール所有者回答欄",
            "",
            "- [x] この記述で正しい",
            "- [ ] 修正が必要",
            "- [ ] 現時点では承認できない",
            "- 確認者：ルール所有者",
            "- 確認日：2026-09-23",
            "",
        ]

    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    OUTPUT_JSON.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
