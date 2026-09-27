from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
RULE_CORE = ROOT / "rule-core"
OUTPUT_DIR = RULE_CORE / "generated" / "reviews"
JSON_OUTPUT = OUTPUT_DIR / "immediate-response-order-owner-review.json"
MD_OUTPUT = OUTPUT_DIR / "immediate-response-order-owner-review.md"
REPORT_OUTPUT = OUTPUT_DIR / "immediate-response-order-analysis-report.md"

ENABLERS = RULE_CORE / "data" / "enablers.yaml"
VECTOR_FILES = [
    RULE_CORE / "tests" / "rule-vectors" / "immediate-enablers.yaml",
    RULE_CORE / "tests" / "rule-vectors" / "immediate-enablers-expansion.yaml",
]
FRAGMENTS = RULE_CORE / "governance" / "source-fragment-register.yaml"
SOURCE_REGISTER = RULE_CORE / "governance" / "source-register.yaml"
SOURCE_SNAPSHOT = RULE_CORE / "governance" / "source-set-snapshots" / "source-set-2026-09-23-initial.yaml"

GENERAL_RULE_FRAGMENT = "FRAG-RULE-0910-2-PDF-P16-IMMEDIATE-PUBLIC-DISPLAY"
SETUP_LOCATOR = "SRC-RULE-0910-2-PDF p.5 §1.2.3（既存fragment未分割のsource locator）"
MD_FRAGMENT = "FRAG-RULE-0910-2-PDF-P12-MD"


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vector_index() -> tuple[dict[str, list[str]], dict[str, str], int]:
    by_component: dict[str, list[str]] = {}
    fingerprints: dict[str, str] = {}
    count = 0
    for path in VECTOR_FILES:
        for vector in load_yaml(path)["vectors"]:
            count += 1
            component_id = vector.get("trigger", vector.get("operation", {})).get("component_id")
            if component_id:
                by_component.setdefault(component_id, []).append(vector["vector_id"])
            fingerprints[vector["vector_id"]] = canonical_sha(vector)
    return by_component, fingerprints, count


def fragment_index() -> dict[str, dict[str, Any]]:
    return {fragment["fragment_id"]: fragment for fragment in load_yaml(FRAGMENTS)["fragments"]}


def source_integrity() -> dict[str, Any]:
    register = load_yaml(SOURCE_REGISTER)["sources"]
    snapshot = load_yaml(SOURCE_SNAPSHOT)
    expected = {entry["source_id"]: entry["content_sha256"] for entry in snapshot["sources"]}
    results = []
    for source in register:
        path = ROOT / source["relative_path"]
        actual = file_sha(path)
        results.append(
            {
                "source_id": source["source_id"],
                "relative_path": source["relative_path"],
                "expected_sha256": expected[source["source_id"]],
                "actual_sha256": actual,
                "matches": actual == expected[source["source_id"]],
            }
        )
    return {
        "source_count": len(results),
        "all_match_initial_snapshot": len(results) == 20 and all(item["matches"] for item in results),
        "sources": results,
    }


SAME_TRIGGER_GROUPS = [
    {
        "analysis_id": "ANALYSIS-TRIGGER-GROUP-NV-AMBUSH",
        "signature": "immediately_after|BLUE_ship_finishes_move_within_adjacent_hex_of_marker",
        "cards": ["COMP-ENABLER-STC-NV-07", "COMP-ENABLER-STC-NV-08"],
        "same_side": True,
        "classification": "unresolved_candidate",
        "finding": "同じBLUE艦の同一移動終了が、両カードに対応する各マーカーの隣接条件を同時に満たし得る。複数枚使用の可否、順序、先行攻撃で対象が失われた場合の扱いは明記されない。",
    },
    {
        "analysis_id": "ANALYSIS-TRIGGER-GROUP-SIGN-PLACEMENT",
        "signature": "during|sign_marker_placement",
        "cards": ["COMP-ENABLER-US-IW-01", "COMP-ENABLER-STC-IW-01"],
        "same_side": False,
        "classification": "source_rule",
        "finding": "文字列上のtriggerは同じだが、正式ルールp.5でイニシアチブ敗者が自軍分を全配置し、勝者が確認後に自軍分を全配置する。各カードは各陣営の配置工程に属し、同時・交互配置ではない。",
    },
    {
        "analysis_id": "ANALYSIS-TRIGGER-GROUP-CYBER-COUNTER-SYMMETRY",
        "signature": "immediately_after|opponent_plays_cyber_related_enabler",
        "cards": ["COMP-ENABLER-STC-CY-04", "COMP-ENABLER-US-CY-03"],
        "same_side": False,
        "classification": "source_rule_with_unresolved_effect_scope",
        "finding": "互いに相手陣営のサイバー関連カード使用をtriggerとする対称カードで、連鎖し得る。各カードは1ATOサイクル1回なので無限反復はしない。判定を持たないカードに対する効果は無効だが、無効になる使用自体が可能かは明記されない。",
    },
    {
        "analysis_id": "ANALYSIS-TRIGGER-GROUP-MD-SYMMETRY",
        "signature": "immediately_after|opponent_declares_MD",
        "cards": ["COMP-ENABLER-STC-RF-05", "COMP-ENABLER-US-EW-03"],
        "same_side": False,
        "classification": "source_rule",
        "finding": "STC-RF-05はBLUEのMD宣言、US-EW-03はREDのMD宣言だけに反応する。同一MD宣言の宣言陣営は一方なので、同じ宣言から両カードは同時成立しない。どちらも宣言後、D4判定前に当該1層を自動失敗させる。",
    },
]


CHAIN_EDGES = [
    {
        "analysis_id": "ANALYSIS-CHAIN-US-SP-03-STC-IW-04",
        "from": "COMP-ENABLER-US-SP-03",
        "to": "COMP-ENABLER-STC-IW-04",
        "generated_fact": "戦略レートをBLUE方向へ1変更",
        "classification": "source_rule",
        "resolution": "戦略レート変更成立後にSTC-IW-04の使用判断を行う。成功時は当該変動を打ち消し、さらにRED方向へ1変更する。",
    },
    {
        "analysis_id": "ANALYSIS-CHAIN-US-IW-04-STC-IW-04",
        "from": "COMP-ENABLER-US-IW-04",
        "to": "COMP-ENABLER-STC-IW-04",
        "generated_fact": "成功時に戦略レートをBLUE方向へ1変更",
        "classification": "source_rule",
        "resolution": "US-IW-04の成功による変更の直後にSTC-IW-04が成立する。失敗時はレート変更がないため成立しない。",
    },
    {
        "analysis_id": "ANALYSIS-CHAIN-STC-CY-05-US-CY-03",
        "from": "COMP-ENABLER-STC-CY-05",
        "to": "COMP-ENABLER-US-CY-03",
        "generated_fact": "REDが判定を持つサイバー関連イネーブラーをプレイ",
        "classification": "source_rule",
        "resolution": "US-CY-03を使用する場合、STC-CY-05のD4判定より前にDISを適用し、その後STC-CY-05の判定へ戻る。",
    },
    {
        "analysis_id": "ANALYSIS-CHAIN-STC-CY-04-US-CY-03",
        "from": "COMP-ENABLER-STC-CY-04",
        "to": "COMP-ENABLER-US-CY-03",
        "generated_fact": "REDがサイバー関連イネーブラーをプレイ",
        "classification": "unresolved_candidate",
        "resolution": "trigger文言は一致するがSTC-CY-04自体に判定はなく、US-CY-03の効果は無効。効果が無効になる使用自体の可否が未記載。",
    },
    {
        "analysis_id": "ANALYSIS-CHAIN-US-CY-03-STC-CY-04",
        "from": "COMP-ENABLER-US-CY-03",
        "to": "COMP-ENABLER-STC-CY-04",
        "generated_fact": "BLUEがサイバー関連イネーブラーをプレイ",
        "classification": "unresolved_candidate",
        "resolution": "trigger文言は一致するがUS-CY-03自体に判定はなく、STC-CY-04の効果は無効。効果が無効になる使用自体の可否が未記載。",
    },
    {
        "analysis_id": "ANALYSIS-CHAIN-US-CY-05-STC-CY-04",
        "from": "COMP-ENABLER-US-CY-05",
        "to": "COMP-ENABLER-STC-CY-04",
        "generated_fact": "BLUEがサイバー関連イネーブラーをプレイ",
        "classification": "unresolved_candidate",
        "resolution": "US-CY-05はUS-CY-01の判定を変更するが、US-CY-05自身に独立した判定はない。STC-CY-04の『その判定』がUS-CY-01判定を指すかが未記載。",
    },
]


COMBINATIONS = [
    {
        "analysis_id": "ANALYSIS-COMBO-NV-07-NV-08",
        "cards": ["COMP-ENABLER-STC-NV-07", "COMP-ENABLER-STC-NV-08"],
        "kind": "simultaneous_same_side",
        "trigger": "同じBLUE艦が対応する両マーカーの隣接ヘックス以内で移動を終了",
        "actor": "PRC_player_holding_cards",
        "target": "triggering_BLUE_ship",
        "interaction_type": "response_window",
        "visibility_effect": "not_stated",
        "scenario_scope": "not_stated",
        "selection_right": "unresolved_candidate",
        "multiple_use": "unresolved_candidate",
        "priority": "not_stated",
        "resolution_order": "unresolved_candidate",
        "reevaluate_after_first": True,
        "interrupt_original_process": True,
        "return_point": "BLUE艦の移動終了後の処理。先行攻撃で艦が失われた場合の後続扱いはunresolved_candidate。",
        "applicable_rule_vectors": ["RV-ENABLER-STC-NV-07-TRIGGER-001", "RV-ENABLER-STC-NV-08-TRIGGER-001"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-STC-NV-07", "FRAG-ENABLER-0830-1-STC-NV-08", GENERAL_RULE_FRAGMENT],
    },
    {
        "analysis_id": "ANALYSIS-COMBO-IW-01-PLACEMENT",
        "cards": ["COMP-ENABLER-US-IW-01", "COMP-ENABLER-STC-IW-01"],
        "kind": "ordered_setup_not_simultaneous",
        "trigger": "各陣営の兆候マーカー配置工程",
        "actor": "initiative_loser_then_initiative_winner",
        "target": "each_side_false_sign_markers",
        "interaction_type": "ordered_setup + response_window",
        "visibility_effect": "配置位置は後手が確認可能、マーカー正体は裏向き。カード使用時の公開開始はnot_stated。",
        "scenario_scope": "not_stated",
        "selection_right": "各カード保持者",
        "multiple_use": "not_applicable（同じ瞬間ではなく陣営別工程）",
        "priority": "source_rule: initiative_loser_then_winner",
        "resolution_order": "source_rule",
        "reevaluate_after_first": False,
        "interrupt_original_process": False,
        "return_point": "not_applicable",
        "applicable_rule_vectors": ["RV-ENABLER-US-IW-01-EFFECT-001", "RV-ENABLER-STC-IW-01-EFFECT-001"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-US-IW-01", "FRAG-ENABLER-0830-1-STC-IW-01", SETUP_LOCATOR],
    },
    {
        "analysis_id": "ANALYSIS-COMBO-MD-SYMMETRIC",
        "cards": ["COMP-ENABLER-STC-RF-05", "COMP-ENABLER-US-EW-03"],
        "kind": "mutually_exclusive_symmetric_trigger",
        "trigger": "相手陣営がMDを宣言した直後、D4判定前",
        "actor": "non_declaring_opponent_card_holder",
        "target": "declared_MD_layer_quantity_1",
        "interaction_type": "response_window",
        "visibility_effect": "DEC-COMBAT-MD-VISIBILITY-001",
        "scenario_scope": "not_stated",
        "selection_right": "対応カード保持者",
        "multiple_use": "not_applicable（同一宣言で両カード条件は同時成立しない）",
        "priority": "not_applicable",
        "resolution_order": "source_rule: MD宣言→即応判断・効果→D4を振らず当該層失敗",
        "reevaluate_after_first": False,
        "interrupt_original_process": True,
        "return_point": "当該MD層の失敗確定後、通常の攻撃処理又は次MD層へ戻る。",
        "applicable_rule_vectors": ["RV-ENABLER-STC-RF-05-TRIGGER-001", "RV-ENABLER-US-EW-03-EFFECT-001"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-STC-RF-05", "FRAG-ENABLER-0830-1-US-EW-03", MD_FRAGMENT],
    },
    {
        "analysis_id": "ANALYSIS-COMBO-SPACE-SAME-ORIGIN",
        "cards": ["COMP-ENABLER-US-SP-04", "COMP-ENABLER-US-SP-03"],
        "kind": "sequential_same_origin",
        "trigger": "同じRED宇宙イネーブラーがBLUE宇宙能力を妨害し、解決結果としてBLUE宇宙レートを2低下させる場合",
        "actor": "US_player_holding_cards",
        "target": "triggering_determination_then_strategic_rate",
        "interaction_type": "response_window",
        "visibility_effect": "not_stated",
        "scenario_scope": "not_stated",
        "selection_right": "USカード保持者",
        "multiple_use": "両方の個別triggerが順に成立すれば各々判断可能",
        "priority": "source_rule: US-SP-04がカードプレイ直後、US-SP-03が実際の2低下直後",
        "resolution_order": "source_rule",
        "reevaluate_after_first": True,
        "interrupt_original_process": True,
        "return_point": "元のRED宇宙イネーブラー解決へ戻る。",
        "applicable_rule_vectors": ["RV-ENABLER-US-SP-04-TRIGGER-001", "RV-ENABLER-US-SP-03-TRIGGER-001"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-US-SP-04", "FRAG-ENABLER-0830-1-US-SP-03", GENERAL_RULE_FRAGMENT],
    },
    {
        "analysis_id": "ANALYSIS-COMBO-CYBER-SAME-ORIGIN",
        "cards": ["COMP-ENABLER-STC-CY-04", "COMP-ENABLER-STC-CY-05"],
        "kind": "sequential_same_origin",
        "trigger": "同じBLUEサイバー関連カードが判定後にBLUEサイバーレートを上昇させる場合",
        "actor": "PRC_player_holding_cards",
        "target": "triggering_determination_then_BLUE_cyber_rate_increase",
        "interaction_type": "response_window",
        "visibility_effect": "not_stated",
        "scenario_scope": "not_stated",
        "selection_right": "PRCカード保持者",
        "multiple_use": "両方の個別triggerが順に成立すれば各々判断可能",
        "priority": "source_rule: STC-CY-04がカードプレイ直後、実際に上昇した場合だけSTC-CY-05が上昇直後",
        "resolution_order": "source_rule",
        "reevaluate_after_first": True,
        "interrupt_original_process": True,
        "return_point": "元のBLUEサイバー関連カード解決へ戻る。",
        "applicable_rule_vectors": ["RV-ENABLER-STC-CY-04-TRIGGER-001", "RV-ENABLER-STC-CY-05-TRIGGER-001"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-STC-CY-04", "FRAG-ENABLER-0830-1-STC-CY-05", GENERAL_RULE_FRAGMENT],
    },
    {
        "analysis_id": "ANALYSIS-COMBO-CYBER-NESTED-DETERMINATION",
        "cards": ["COMP-ENABLER-STC-CY-05", "COMP-ENABLER-US-CY-03"],
        "kind": "nested_chain",
        "trigger": "STC-CY-05をプレイした直後",
        "actor": "US_player_holding_US-CY-03",
        "target": "STC-CY-05_D4_determination",
        "interaction_type": "response_window",
        "visibility_effect": "not_stated",
        "scenario_scope": "not_stated",
        "selection_right": "US-CY-03保持者",
        "multiple_use": "カードごとの1ATOサイクル1回制限内",
        "priority": "source_rule: US-CY-03判断はSTC-CY-05のD4判定より前",
        "resolution_order": "source_rule",
        "reevaluate_after_first": True,
        "interrupt_original_process": True,
        "return_point": "US-CY-03解決後、DIS条件を反映してSTC-CY-05のD4判定へ戻る。",
        "applicable_rule_vectors": ["RV-ENABLER-STC-CY-05-TRIGGER-001", "RV-ENABLER-US-CY-03-TRIGGER-001"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-STC-CY-05", "FRAG-ENABLER-0830-1-US-CY-03", GENERAL_RULE_FRAGMENT],
    },
    {
        "analysis_id": "ANALYSIS-COMBO-CYBER-COUNTER-CYCLE",
        "cards": ["COMP-ENABLER-STC-CY-04", "COMP-ENABLER-US-CY-03"],
        "kind": "bounded_mutual_chain",
        "trigger": "一方のサイバー対抗即応カードのプレイ",
        "actor": "opponent_card_holder",
        "target": "triggering_card_determination",
        "interaction_type": "response_window",
        "visibility_effect": "not_stated",
        "scenario_scope": "not_stated",
        "selection_right": "カード保持者。ただし無効効果となる使用自体の可否はunresolved_candidate。",
        "multiple_use": "各カードは1ATOサイクル1回までなので同一カードの再帰再使用は不可",
        "priority": "source_rule: 後からプレイされた対抗カードのwindowが先行カードの効果解決前に生じる",
        "resolution_order": "partial: trigger順は一意、無効効果カードの使用可否は未確定",
        "reevaluate_after_first": True,
        "interrupt_original_process": True,
        "return_point": "最後のresponse解決後に一つ前のカード効果へ戻る。親子continuationの保持方法はimplementation_only。",
        "applicable_rule_vectors": ["RV-ENABLER-STC-CY-04-TRIGGER-001", "RV-ENABLER-US-CY-03-TRIGGER-001"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-STC-CY-04", "FRAG-ENABLER-0830-1-US-CY-03", GENERAL_RULE_FRAGMENT],
    },
    {
        "analysis_id": "ANALYSIS-COMBO-US-SP-03-STC-IW-04",
        "cards": ["COMP-ENABLER-US-SP-03", "COMP-ENABLER-STC-IW-04"],
        "kind": "event_generated_chain",
        "trigger": "US-SP-03が戦略レートをBLUE方向へ1変更",
        "actor": "PRC_player_holding_STC-IW-04",
        "target": "triggering_strategic_rate_change",
        "interaction_type": "response_window",
        "visibility_effect": "レート現在値はpublic、カード公開開始はnot_stated",
        "scenario_scope": "not_stated",
        "selection_right": "STC-IW-04保持者",
        "multiple_use": "not_applicable",
        "priority": "source_rule: レート変更成立後",
        "resolution_order": "source_rule",
        "reevaluate_after_first": True,
        "interrupt_original_process": True,
        "return_point": "STC-IW-04解決後、US-SP-03を生じさせた元の宇宙イネーブラー処理へ戻る。",
        "applicable_rule_vectors": ["RV-ENABLER-US-SP-03-TRIGGER-001", "RV-ENABLER-STC-IW-04-TRIGGER-001", "RV-ENABLER-STC-IW-04-SUCCESS-001", "RV-ENABLER-STC-IW-04-FAILURE-001"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-US-SP-03", "FRAG-ENABLER-0830-1-STC-IW-04"],
    },
    {
        "analysis_id": "ANALYSIS-COMBO-US-IW-04-STC-IW-04",
        "cards": ["COMP-ENABLER-US-IW-04", "COMP-ENABLER-STC-IW-04"],
        "kind": "event_generated_chain",
        "trigger": "US-IW-04の成功で戦略レートをBLUE方向へ1変更",
        "actor": "PRC_player_holding_STC-IW-04",
        "target": "triggering_strategic_rate_change",
        "interaction_type": "response_window",
        "visibility_effect": "レート現在値はpublic、カード公開開始はnot_stated",
        "scenario_scope": "not_stated",
        "selection_right": "STC-IW-04保持者",
        "multiple_use": "not_applicable",
        "priority": "source_rule: US-IW-04成功・変更成立後",
        "resolution_order": "source_rule",
        "reevaluate_after_first": True,
        "interrupt_original_process": True,
        "return_point": "STC-IW-04解決後、元の基地群攻撃失敗後処理へ戻る。",
        "applicable_rule_vectors": ["RV-ENABLER-US-IW-04-SUCCESS-001", "RV-ENABLER-STC-IW-04-TRIGGER-001", "RV-ENABLER-STC-IW-04-SUCCESS-001", "RV-ENABLER-STC-IW-04-FAILURE-001"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-US-IW-04", "FRAG-ENABLER-0830-1-STC-IW-04"],
    },
    {
        "analysis_id": "ANALYSIS-COMBO-AF-05-EW-03-MD",
        "cards": ["COMP-ENABLER-US-AF-05", "COMP-ENABLER-US-EW-03"],
        "kind": "sequential_attack_windows",
        "trigger": "BLUEがRED基地へ対地攻撃を宣言し、その後REDがMDを宣言",
        "actor": "US_player_holding_cards",
        "target": "triggering_ground_attack_then_declared_RED_MD_layer",
        "interaction_type": "response_window",
        "visibility_effect": "MD部分はDEC-COMBAT-MD-VISIBILITY-001、カード公開開始はnot_stated",
        "scenario_scope": "not_stated",
        "selection_right": "各カード保持者（同一US側）",
        "multiple_use": "個別triggerが順に成立すれば両方使用可能",
        "priority": "source_rule: US-AF-05は攻撃宣言時、US-EW-03はREDのMD宣言直後",
        "resolution_order": "source_rule",
        "reevaluate_after_first": True,
        "interrupt_original_process": True,
        "return_point": "MD層解決後、採用済み命中出目4を用いる攻撃処理へ戻る。",
        "applicable_rule_vectors": ["RV-ENABLER-US-AF-05-EFFECT-001", "RV-ENABLER-US-EW-03-EFFECT-001"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-US-AF-05", "FRAG-ENABLER-0830-1-US-EW-03", MD_FRAGMENT],
    },
    {
        "analysis_id": "ANALYSIS-COMBO-RF-05-AB-05-MD",
        "cards": ["COMP-ENABLER-STC-RF-05", "COMP-ENABLER-US-AB-05"],
        "kind": "sequential_attack_windows",
        "trigger": "REDの対地攻撃にBLUEがMDを宣言し、STC-RF-05で当該層が失敗した後、攻撃の命中判定が成功",
        "actor": "PRC_player_holding_STC-RF-05_then_US_player_holding_US-AB-05",
        "target": "declared_BLUE_MD_layer_then_triggering_RED_ground_attack_hits",
        "interaction_type": "response_window",
        "visibility_effect": "MD部分はDEC-COMBAT-MD-VISIBILITY-001、US-AB-05使用公開時点はnot_stated",
        "scenario_scope": "not_stated",
        "selection_right": "各時点の対応カード保持者",
        "multiple_use": "個別triggerが順に成立すれば各々判断可能",
        "priority": "source_rule: STC-RF-05はBLUEのMD宣言直後、US-AB-05は後続命中成功後・ダメージロール前",
        "resolution_order": "source_rule",
        "reevaluate_after_first": True,
        "interrupt_original_process": True,
        "return_point": "STC-RF-05後は攻撃命中判定へ、US-AB-05後は全hitを無効化して当該攻撃を終了する。",
        "applicable_rule_vectors": ["RV-ENABLER-STC-RF-05-TRIGGER-001", "RV-ENABLER-US-AB-05-EFFECT-001"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-STC-RF-05", "FRAG-ENABLER-0830-1-US-AB-05", MD_FRAGMENT],
    },
    {
        "analysis_id": "ANALYSIS-COMBO-AF-10-EW-03-MD",
        "cards": ["COMP-ENABLER-US-AF-10", "COMP-ENABLER-US-EW-03"],
        "kind": "overlapping_attack_windows",
        "trigger": "BLUE航空機がADAを攻撃し、当該攻撃にREDがMDを宣言できる場合",
        "actor": "US_player_holding_cards",
        "target": "triggering_attack_and_declared_RED_MD_layer",
        "interaction_type": "response_window",
        "visibility_effect": "MD部分はDEC-COMBAT-MD-VISIBILITY-001、US-AF-10使用公開時点はnot_stated",
        "scenario_scope": "not_stated",
        "selection_right": "各カード保持者（同一US側）",
        "multiple_use": "個別triggerが成立すれば両方候補",
        "priority": "unresolved_candidate",
        "resolution_order": "US-EW-03はMD宣言直後と一意だが、US-AF-10の『攻撃する際』がMD判断の前後どちらかは未記載",
        "reevaluate_after_first": True,
        "interrupt_original_process": True,
        "return_point": "US-AF-10の相対タイミング確定まで、MD選択時に防御側がADV適用を知るか確定できない。",
        "applicable_rule_vectors": ["RV-ENABLER-US-AF-10-EFFECT-001", "RV-ENABLER-US-EW-03-EFFECT-001"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-US-AF-10", "FRAG-ENABLER-0830-1-US-EW-03", MD_FRAGMENT],
    },
]


OWNER_QUESTIONS = [
    {
        "analysis_id": "ANALYSIS-UNRESOLVED-NV-MULTIPLE-USE",
        "situation": "同じBLUE艦が、STC-NV-07とSTC-NV-08の各マーカーから隣接ヘックス以内で移動を終了し、REDが両カードを手札に持つ。",
        "known": "両カードの個別trigger、対象、攻撃内容は同一で、各カードは使い切りタイプである。",
        "unknown": "同じ一回の移動終了に対して両カードを使用できるか、一方だけか。",
        "stop_point": "最初のresponse windowで提示する合法カード集合と、1枚使用後にもう1枚のwindowを開くかを確定できない。",
        "question": "同じBLUE艦の一回の移動終了が両マーカーの条件を満たす場合、REDはSTC-NV-07とSTC-NV-08の両方を使用できますか、それとも一方だけですか。",
        "affected_cards": ["COMP-ENABLER-STC-NV-07", "COMP-ENABLER-STC-NV-08"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-STC-NV-07", "FRAG-ENABLER-0830-1-STC-NV-08", GENERAL_RULE_FRAGMENT],
        "owner_response": None,
    },
    {
        "analysis_id": "ANALYSIS-UNRESOLVED-NV-ORDER",
        "situation": "上記状況で両カードの使用が認められる場合。",
        "known": "両カードの使用主体は同じRED側で、各攻撃は個別に判定・解決する必要がある。",
        "unknown": "どちらを先に解決するかを誰が、いつ選ぶか。",
        "stop_point": "二つの攻撃の先後を確定できない。",
        "question": "STC-NV-07とSTC-NV-08を同じ移動終了に両方使用できる場合、解決順は誰が決めますか。",
        "affected_cards": ["COMP-ENABLER-STC-NV-07", "COMP-ENABLER-STC-NV-08"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-STC-NV-07", "FRAG-ENABLER-0830-1-STC-NV-08", GENERAL_RULE_FRAGMENT],
        "owner_response": None,
    },
    {
        "analysis_id": "ANALYSIS-UNRESOLVED-NV-TARGET-CEASES",
        "situation": "両カードを使用でき、先に解決した潜水艦攻撃で対象BLUE艦が撃破・除去された。",
        "known": "各カードは『当該BLUE艦に攻撃実行』し、攻撃解決後に各マーカーを除去する。",
        "unknown": "後続カードが未使用に戻るのか、使用済みになるが攻撃しないのか、対象消失前に宣言済みなら攻撃を解決するのか。",
        "stop_point": "後続カードと対応マーカーの状態、二回目の攻撃実施を確定できない。",
        "question": "先の潜水艦攻撃で当該BLUE艦が撃破・除去された場合、後続のSTC-NV-07又はSTC-NV-08とそのマーカーをどのように扱いますか。",
        "affected_cards": ["COMP-ENABLER-STC-NV-07", "COMP-ENABLER-STC-NV-08"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-STC-NV-07", "FRAG-ENABLER-0830-1-STC-NV-08"],
        "owner_response": None,
    },
    {
        "analysis_id": "ANALYSIS-UNRESOLVED-CYBER-INEFFECTIVE-PLAY",
        "situation": "US-CY-03又はSTC-CY-04のプレイが、相手側の対称カードをtriggerするが、trigger元カード自体には判定がない。",
        "known": "カード印字は『判定がないカードには無効』とする。各再選択可カードは1ATOサイクル1回までである。",
        "unknown": "効果が無効になることを承知でカードをプレイし、当該ATOの使用機会を消費できるか。",
        "stop_point": "連鎖response windowに当該カードを合法候補として提示するか確定できない。",
        "question": "判定を持たないサイバー関連イネーブラーに対して、US-CY-03又はSTC-CY-04を効果なしで使用し、そのATOの使用機会を消費することはできますか。",
        "affected_cards": ["COMP-ENABLER-STC-CY-04", "COMP-ENABLER-US-CY-03"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-STC-CY-04", "FRAG-ENABLER-0830-1-US-CY-03", GENERAL_RULE_FRAGMENT],
        "owner_response": None,
    },
    {
        "analysis_id": "ANALYSIS-UNRESOLVED-US-CY-05-TARGET",
        "situation": "BLUEがUS-CY-05を使用し、REDがSTC-CY-04で応答する。",
        "known": "US-CY-05はUS-CY-01の判定直前に使用し、Day1・2は自動成功、Day3以降は当該判定をADVにする。STC-CY-04はBLUEのサイバー関連カードの『その判定』をDISにする。",
        "unknown": "STC-CY-04の『その判定』がUS-CY-05が変更するUS-CY-01判定を指すか、US-CY-05自体に独立判定がないため無効か。",
        "stop_point": "Day3以降のUS-CY-01判定へADVとDISの両方を適用するか確定できない。",
        "question": "STC-CY-04をUS-CY-05に応答して使用した場合、『その判定』はUS-CY-01の判定を指しますか、それともUS-CY-05には独立した判定がないためSTC-CY-04は無効ですか。",
        "affected_cards": ["COMP-ENABLER-US-CY-05", "COMP-ENABLER-STC-CY-04"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-US-CY-05", "FRAG-ENABLER-0830-1-STC-CY-04"],
        "owner_response": None,
    },
    {
        "analysis_id": "ANALYSIS-UNRESOLVED-US-AF-10-MD-TIMING",
        "situation": "BLUE航空機がADAを攻撃し、その攻撃についてREDがMDを宣言でき、BLUEがUS-AF-10を手札に持つ。",
        "known": "US-AF-10は『航空機トークンがADAを攻撃する際』に使用して攻撃をADVにする。MD判断は攻撃宣言直後、命中ロール前。REDがMDを宣言した後はUS-EW-03が成立し得る。",
        "unknown": "US-AF-10の使用判断をREDのMD判断より前に行うか、後に行えるか。",
        "stop_point": "REDがMD判断を行う時点でUS-AF-10のADV適用を知るか、またUS-EW-03との順序を確定できない。",
        "question": "BLUE航空機がADAを攻撃する場合、US-AF-10の使用判断はREDのMD宣言判断より前ですか、後ですか。",
        "affected_cards": ["COMP-ENABLER-US-AF-10", "COMP-ENABLER-US-EW-03"],
        "source_fragment_candidates": ["FRAG-ENABLER-0830-1-US-AF-10", "FRAG-ENABLER-0830-1-US-EW-03", MD_FRAGMENT],
        "owner_response": None,
    },
]


SOURCE_RULE_FINDINGS = [
    "即応カードは発動準備スタンドを経由せず、印字タイミングで手札から直接使用でき、通常のイネーブラー運用1回には数えない。",
    "再選択可タイプは1ATOサイクルに1回、使い切りタイプはゲーム中1回である。",
    "兆候配置はイニシアチブ敗者が自軍分を全配置し、その配置を確認した勝者が自軍分を全配置する。交互配置ではない。",
    "STC-RF-05とUS-EW-03は相手陣営のMD宣言直後、D4判定前に当該MD1層を自動失敗させる。",
    "STC-CY-05に対するUS-CY-03は、STC-CY-05の判定へDISを適用してからその判定へ戻る必要がある。",
    "US-SP-03又はUS-IW-04が生むBLUE方向の戦略レート1変更は、STC-IW-04の印字triggerと一致する。",
]


NOT_STATED_FINDINGS = [
    "同一タイミングに複数の即応が成立した場合の一般的な複数枚使用可否、優先権及び解決順。",
    "US-IW-07を除く即応カードについて、使用時にカード自体をいつ誰へ公開するか。",
    "各即応カードの明示的なscenario適用範囲。",
    "US-AF-10の『攻撃する際』がMD宣言判断の前後どちらか。",
    "判定を持たないカードへサイバー対抗カードを効果なしで使用できるか。",
]


NOT_APPLICABLE_FINDINGS = [
    "US-IW-01とSTC-IW-01の両陣営同時優先権。正式ルールのordered setupにより陣営別工程となる。",
    "STC-RF-05とUS-EW-03の同一MD宣言での競合。同じ宣言では片方の陣営条件しか成立しない。",
    "Rule Coreにおけるparent continuation、resume token、response stackの内部表現。これらはVersus/Digitalの実装方式である。",
]


EFFECT_TRACE = {
    "COMP-ENABLER-US-SP-03": (["EVENT-IMMEDIATE-ENABLER-PLAYED", "EVENT-RATE-CHANGED"], ["strategic_rate toward BLUE +1"]),
    "COMP-ENABLER-US-SP-04": (["EVENT-IMMEDIATE-ENABLER-PLAYED"], ["triggering determination gains DIS once"]),
    "COMP-ENABLER-STC-CY-04": (["EVENT-IMMEDIATE-ENABLER-PLAYED"], ["triggering determination gains DIS; no effect when no determination"]),
    "COMP-ENABLER-STC-CY-05": (["EVENT-IMMEDIATE-ENABLER-PLAYED", "EVENT-RATE-CHANGED"], ["on success invalidate BLUE cyber-rate increase and decrease BLUE cyber rate by 1"]),
    "COMP-ENABLER-US-CY-03": (["EVENT-IMMEDIATE-ENABLER-PLAYED"], ["triggering determination gains DIS; no effect when no determination"]),
    "COMP-ENABLER-US-CY-05": (["EVENT-IMMEDIATE-ENABLER-PLAYED"], ["US-CY-01 determination automatic success on Day1/2 or ADV on Day3+"]),
    "COMP-ENABLER-STC-NV-07": (["EVENT-IMMEDIATE-ENABLER-PLAYED"], ["attack triggering BLUE ship; remove corresponding marker after resolution"]),
    "COMP-ENABLER-STC-NV-08": (["EVENT-IMMEDIATE-ENABLER-PLAYED"], ["attack triggering BLUE ship; remove corresponding marker after resolution"]),
    "COMP-ENABLER-STC-RF-05": (["EVENT-IMMEDIATE-ENABLER-PLAYED", "EVENT-MD-RESOLVED"], ["declared BLUE MD layer becomes failure"]),
    "COMP-ENABLER-US-AB-05": (["EVENT-IMMEDIATE-ENABLER-PLAYED"], ["all hits from triggering RED ground attack invalidated"]),
    "COMP-ENABLER-US-EW-03": (["EVENT-IMMEDIATE-ENABLER-PLAYED", "EVENT-MD-RESOLVED"], ["declared RED MD layer becomes failure"]),
    "COMP-ENABLER-US-AF-05": (["EVENT-IMMEDIATE-ENABLER-PLAYED"], ["hit roll skipped; adopted roll 4; damage roll remains normal"]),
    "COMP-ENABLER-US-AF-10": (["EVENT-IMMEDIATE-ENABLER-PLAYED"], ["triggering attack roll gains ADV"]),
    "COMP-ENABLER-US-IW-01": (["EVENT-IMMEDIATE-ENABLER-PLAYED"], ["place two false sign markers in approved BLUE geography area"]),
    "COMP-ENABLER-US-IW-04": (["EVENT-IMMEDIATE-ENABLER-PLAYED", "EVENT-RATE-CHANGED"], ["on success strategic rate toward BLUE +1"]),
    "COMP-ENABLER-US-IW-07": (["EVENT-IMMEDIATE-ENABLER-PLAYED"], ["own squadron acquisition determinations automatic success until day end"]),
    "COMP-ENABLER-STC-IW-01": (["EVENT-IMMEDIATE-ENABLER-PLAYED"], ["place two false sign markers in approved RED geography area"]),
    "COMP-ENABLER-STC-IW-04": (["EVENT-IMMEDIATE-ENABLER-PLAYED", "EVENT-RATE-CHANGED"], ["on success invalidate triggering change and strategic rate toward RED +1"]),
}


def build_review() -> dict[str, Any]:
    enabler_doc = load_yaml(ENABLERS)
    components = enabler_doc["components"]
    if len(components) != 18:
        raise ValueError(f"Expected 18 immediate cards, found {len(components)}")
    by_component, vector_fingerprints, vector_count = vector_index()
    if vector_count != 47:
        raise ValueError(f"Expected 47 approved immediate vectors, found {vector_count}")
    fragments = fragment_index()
    cards = []
    for component in components:
        fragment_ids = component.get("source_fragment_ids", [])
        missing = [fragment_id for fragment_id in fragment_ids if fragment_id not in fragments]
        if missing:
            raise ValueError(f"Missing fragment for {component['component_id']}: {missing}")
        cards.append(
            {
                "component_id": component["component_id"],
                "source_card_code": component["source_card_code"],
                "side": component["side"],
                "trigger": component["trigger"],
                "actor": component["actor"],
                "target": component["target"],
                "effect": component["effect"],
                "effect_generated_event_ids": EFFECT_TRACE[component["component_id"]][0],
                "effect_changed_state_or_roll": EFFECT_TRACE[component["component_id"]][1],
                "duration": component.get("duration", "not_stated"),
                "card_state": component["card_state"],
                "interaction_type": component["interaction_type"],
                "visibility_effect": component["visibility_effect"],
                "scenario_scope": "not_stated",
                "source_fragment_ids": fragment_ids,
                "applicable_rule_vectors": by_component.get(component["component_id"], []),
                "payload_fingerprint_sha256": canonical_sha(component),
            }
        )
    protected_paths = [
        ENABLERS,
        *VECTOR_FILES,
        RULE_CORE / "data" / "geography.yaml",
        RULE_CORE / "generated" / "reviews" / "geography-generation-boundaries-owner-review.json",
        RULE_CORE / "governance" / "unresolved.yaml",
        RULE_CORE / "tests" / "rule-vectors" / "md.yaml",
        RULE_CORE / "tests" / "rule-vectors" / "intel.yaml",
        RULE_CORE / "tests" / "rule-vectors" / "cyber-dominance-candidates.yaml",
        RULE_CORE / "tests" / "rule-vectors" / "emi.yaml",
        RULE_CORE / "tests" / "rule-vectors" / "emi-double-count-candidates.yaml",
        RULE_CORE / "tests" / "rule-vectors" / "rates.yaml",
    ]
    integrity = {
        "canonical_json_method": "UTF-8; object keys sorted; array order preserved; null explicit; no insignificant whitespace; SHA-256",
        "immediate_vector_count": vector_count,
        "immediate_vector_statuses": {
            "approved": sum(
                vector.get("status") == "approved"
                for path in VECTOR_FILES
                for vector in load_yaml(path)["vectors"]
            )
        },
        "vector_fingerprints_sha256": vector_fingerprints,
        "protected_file_sha256": {str(path.relative_to(ROOT)).replace("\\", "/"): file_sha(path) for path in protected_paths},
        "source_snapshot": source_integrity(),
    }
    return {
        "schema_version": "0.1.0",
        "review_type": "immediate_response_order_owner_review",
        "non_normative": True,
        "generated_at": "2026-09-24",
        "generator": "rule-core/pipeline/generate-immediate-response-order-review.py",
        "scope": {
            "card_count": len(cards),
            "card_ids": [card["component_id"] for card in cards],
            "rule_core_release": enabler_doc["rule_core_version"],
            "source_set": enabler_doc["source_set"],
        },
        "integrity": integrity,
        "cards": cards,
        "same_trigger_groups": SAME_TRIGGER_GROUPS,
        "chain_edges": CHAIN_EDGES,
        "combinations": COMBINATIONS,
        "determinations": {
            "source_rule": SOURCE_RULE_FINDINGS,
            "not_stated": NOT_STATED_FINDINGS,
            "not_applicable": NOT_APPLICABLE_FINDINGS,
            "unresolved_candidate": [question["analysis_id"] for question in OWNER_QUESTIONS],
        },
        "owner_questions": OWNER_QUESTIONS,
        "digital_observations": {
            "normative_authority": False,
            "current_fact": "既存Digital監査は、承認済み即応カード用の共通trigger評価、直接手札使用Command、response window及び即応Eventをnot_implementedと記録する。Digital固有のcontinuation又はpending decisionは本分析の規範根拠にしていない。",
            "versus_information_already_available": [
                "triggerの意味とbefore/after/duringの相対時点",
                "判断主体となるカード保持陣営",
                "対象、カードごとの効果、持続及び使用回数状態",
                "兆候配置の敗者→勝者順",
                "MD宣言→カード応答→当該層失敗→攻撃又は次層へ復帰する順序",
                "STC-CY-05に対するUS-CY-03の割込みとDIS適用後の判定復帰",
                "US-SP-03／US-IW-04からSTC-IW-04へ至るレート変更trigger",
            ],
            "implementation_only_information": [
                "未完了処理の保存表現",
                "parent continuation又はresume token",
                "response stackのデータ構造",
                "AIの選択方法、通信、UI、保存・再開",
            ],
            "blocked_before_common_response_window_implementation": [question["analysis_id"] for question in OWNER_QUESTIONS],
        },
    }


def table_cell(value: Any) -> str:
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def render_owner_review(review: dict[str, Any]) -> str:
    lines = [
        "# 複数即応の選択権・優先順位・解決順　ルール所有者確認票",
        "",
        "> 本確認票は非規範の分析生成物です。Rule Core規範、decision、unresolved、Digital実装を変更しません。",
        "",
        f"- 対象Rule Core: `{review['scope']['rule_core_release']}` / `{review['scope']['source_set']}`",
        f"- 対象: 承認済み即応カード {review['scope']['card_count']}枚、既承認即応vector {review['integrity']['immediate_vector_count']}件",
        "- 正式資料: `ルール0910-2.pdf`、`イネーブラー0830-1.pdf`、承認済みdecision",
        "- 補助資料: 既存Digital監査（規範根拠には不使用）",
        "- 生成日: 2026-09-24",
        "",
        "## 結論の要約",
        "",
        "- `US-IW-01`と`STC-IW-01`は同時配置ではありません。正式ルールにより、イニシアチブ敗者が全配置し、勝者が確認後に全配置します。",
        "- `STC-RF-05`と`US-EW-03`は同じMD宣言で競合しません。宣言側がBLUEかREDかで成立するカードが一意に分かれます。",
        "- `US-SP-03`／`US-IW-04`がBLUE方向の戦略レート変更を生じさせると、`STC-IW-04`のtriggerになります。",
        "- `STC-CY-05`のプレイに`US-CY-03`を使用する場合、DISを適用してからSTC-CY-05のD4判定へ戻る順序はカード文面から一意です。",
        "- 現在の18枚で所有者回答が必要なのは6項目です。一般的なcontinuation、stack、resume tokenの設計は規範ではなく実装事項です。",
        "",
        "## 同一trigger候補",
        "",
        "| 分析用ID | カード | 判定 | 調査結果 |",
        "| --- | --- | --- | --- |",
    ]
    for group in review["same_trigger_groups"]:
        lines.append(
            f"| `{group['analysis_id']}` | {', '.join(f'`{card}`' for card in group['cards'])} | `{group['classification']}` | {group['finding']} |"
        )
    lines += [
        "",
        "## 連鎖関係",
        "",
        "```mermaid",
        "flowchart LR",
        "  USP03[US-SP-03] -->|戦略レート BLUE +1| STCIW04[STC-IW-04]",
        "  USIW04[US-IW-04 成功] -->|戦略レート BLUE +1| STCIW04",
        "  STCCY05[STC-CY-05] -->|REDサイバーカード使用| USCY03[US-CY-03]",
        "  STCCY04[STC-CY-04] -.->|判定なし・効果無効| USCY03",
        "  USCY03 -.->|判定なし・効果無効| STCCY04",
        "  USCY05[US-CY-05] -.->|対象判定の解釈未確定| STCCY04",
        "```",
        "",
        "破線は、trigger自体は候補になるものの、効果対象又は使用可否に所有者回答が必要な関係です。",
        "",
        "## 正式資料だけで確定できる事項",
        "",
    ]
    lines += [f"- {item}" for item in review["determinations"]["source_rule"]]
    lines += ["", "## 原文に明記がない事項", ""]
    lines += [f"- {item}" for item in review["determinations"]["not_stated"]]
    lines += ["", "## 所有者回答が必要な事項", ""]
    for index, question in enumerate(review["owner_questions"], 1):
        lines += [
            f"### {index}. {question['analysis_id']}",
            "",
            f"- 実際に起こる状況: {question['situation']}",
            f"- 現在の正式資料で分かること: {question['known']}",
            f"- 現在の正式資料では決まらないこと: {question['unknown']}",
            f"- 決めない場合に停止する位置: {question['stop_point']}",
            f"- ルール所有者への質問: **{question['question']}**",
            f"- 技術的な追跡情報: {', '.join(f'`{item}`' for item in question['affected_cards'] + question['source_fragment_candidates'])}",
            "",
            "回答：",
            "",
            "確認者：",
            "",
            "確認日：",
            "",
        ]
    lines += [
        "## Versusへ既に返せる情報",
        "",
    ]
    lines += [f"- {item}" for item in review["digital_observations"]["versus_information_already_available"]]
    lines += [
        "",
        "Versus/Digitalは未完了処理を保持して即応後に復帰できる必要がありますが、親子continuation、resume token、stack等の内部表現はRule Core規範ではありません。",
        "",
        "## 参照資料",
        "",
        "- `SRC-RULE-0910-2-PDF` p.5 §1.2.3、p.12 MD、p.16 即応カード・公開状態",
        "- `SRC-ENABLER-0830-1` pp.9, 10, 15, 16, 19, 21, 28, 29, 41, 45, 49, 52, 54, 55, 56, 58, 59, 62",
        "- `DEC-COMBAT-MD-VISIBILITY-001`（MD公開契約のみ）",
        "",
    ]
    return "\n".join(lines)


def render_analysis_report(review: dict[str, Any]) -> str:
    lines = [
        "# 即応カード18枚　重複trigger・連鎖trigger分析報告",
        "",
        "> 非規範の分析報告。正式資料と承認済みRule Coreを分類し、裁定案又は既定値は示さない。",
        "",
        "## 調査範囲と方法",
        "",
        "正式ルールPDFのp.5（兆候配置順）、p.12（MD）、p.16（即応カード）を視覚確認し、カードPDFの18枚の現物単位fragmentと`data/enablers.yaml`を照合した。18枚のtrigger、actor、target、interaction type、visibility、効果、持続、カード状態、scenario scopeを比較し、同一signatureとカード効果から別カードtriggerへ至る有向辺を抽出した。Digital監査は実装事実の確認にだけ用いた。",
        "",
        "## 全18枚の機械的比較",
        "",
        "| # | Component ID | trigger | Actor / Target | 効果 | Event / State変更 | interaction / visibility | 持続・カード状態 | scenario | 関連vector |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for index, card in enumerate(review["cards"], 1):
        lines.append(
            "| " + " | ".join(
                [
                    str(index),
                    f"`{card['component_id']}`",
                    table_cell(card["trigger"]),
                    f"`{card['actor']}`<br>{table_cell(card['target'])}",
                    table_cell(card["effect"]),
                    "<br>".join(f"`{event}`" for event in card["effect_generated_event_ids"]) + "<br>" + "<br>".join(card["effect_changed_state_or_roll"]),
                    f"`{card['interaction_type']}`<br>`{card['visibility_effect']}`",
                    f"`{card['duration']}` / `{card['card_state']}`",
                    f"`{card['scenario_scope']}`",
                    "<br>".join(f"`{vector}`" for vector in card["applicable_rule_vectors"]),
                ]
            ) + " |"
        )
    lines += [
        "",
        "## 同一trigger signature",
        "",
    ]
    for group in review["same_trigger_groups"]:
        lines += [
            f"### {group['analysis_id']}",
            "",
            f"- signature: `{group['signature']}`",
            f"- cards: {', '.join(f'`{card}`' for card in group['cards'])}",
            f"- classification: `{group['classification']}`",
            f"- result: {group['finding']}",
            "",
        ]
    lines += ["## 効果→triggerの有向グラフ", "", "| 分析用ID | from | to | 生成事実 | 分類 | 結果 |", "| --- | --- | --- | --- | --- | --- |"]
    for edge in review["chain_edges"]:
        lines.append(
            f"| `{edge['analysis_id']}` | `{edge['from']}` | `{edge['to']}` | {edge['generated_fact']} | `{edge['classification']}` | {edge['resolution']} |"
        )
    lines += ["", "## 組合せ別調査", ""]
    for combo in review["combinations"]:
        lines += [
            f"### {combo['analysis_id']}",
            "",
            f"- 対象カード: {', '.join(f'`{card}`' for card in combo['cards'])}",
            f"- 種別: `{combo['kind']}`",
            f"- trigger: {combo['trigger']}",
            f"- Actor / Target: `{combo['actor']}` / `{combo['target']}`",
            f"- interaction / visibility / scenario: `{combo['interaction_type']}` / `{combo['visibility_effect']}` / `{combo['scenario_scope']}`",
            f"- 選択権: {combo['selection_right']}",
            f"- 複数枚使用: {combo['multiple_use']}",
            f"- 優先権: {combo['priority']}",
            f"- 解決順: {combo['resolution_order']}",
            f"- 後続trigger再評価: `{str(combo['reevaluate_after_first']).lower()}`",
            f"- 元処理の中断: `{str(combo['interrupt_original_process']).lower()}`",
            f"- 復帰点: {combo['return_point']}",
            f"- applicable rule vector: {', '.join(f'`{vector}`' for vector in combo['applicable_rule_vectors'])}",
            f"- source fragment候補: {', '.join(f'`{fragment}`' for fragment in combo['source_fragment_candidates'])}",
            "",
        ]
    lines += [
        "## nested responseの規範境界",
        "",
        "規則として必要なのは、(1) 元処理がまだ完了していないこと、(2) 新たな即応使用判断を待つこと、(3) 使用された即応効果を解決すること、(4) その結果を反映して元の判定又は処理へ戻ることです。STC-CY-05→US-CY-03は、US-CY-03のDISがSTC-CY-05の判定へ作用するため、この順序をカード文面から一意に導けます。",
        "",
        "一方、親子continuation、resume token、stack、parent ID、通信payload、AI判断方法は実装方式です。分析用IDはRule Core IDではなく、registryへ登録していません。",
        "",
        "## 分類集計",
        "",
        f"- source_rule: {len(review['determinations']['source_rule'])}事項",
        f"- not_stated: {len(review['determinations']['not_stated'])}事項",
        f"- not_applicable: {len(review['determinations']['not_applicable'])}事項",
        f"- unresolved_candidate: {len(review['owner_questions'])}事項",
        "",
        "## Digital実装事実（非規範）",
        "",
        review["digital_observations"]["current_fact"],
        "",
        "既存Digitalに順序処理がないことは、ゲーム規則が未確定である根拠にはしていない。現在確定済みの因果順はVersusへ返せるが、6件の質問に関係する合法手・順序は回答後まで実装へ固定しない。",
        "",
        "## 保全情報",
        "",
        f"- 即応カード: {review['scope']['card_count']}枚",
        f"- 既承認即応vector: {review['integrity']['immediate_vector_count']}件（approved {review['integrity']['immediate_vector_statuses']['approved']}件）",
        f"- sources: {review['integrity']['source_snapshot']['source_count']}件、初回snapshot一致=`{str(review['integrity']['source_snapshot']['all_match_initial_snapshot']).lower()}`",
        "- 詳細fingerprintと保護ファイルSHA-256は構造化確認票JSONに記録。",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    review = build_review()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MD_OUTPUT.write_text(render_owner_review(review), encoding="utf-8")
    REPORT_OUTPUT.write_text(render_analysis_report(review), encoding="utf-8")
    print(f"generated {JSON_OUTPUT.relative_to(ROOT)}")
    print(f"generated {MD_OUTPUT.relative_to(ROOT)}")
    print(f"generated {REPORT_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("generate-immediate-response-order-artifacts.py")), run_name="__main__")
