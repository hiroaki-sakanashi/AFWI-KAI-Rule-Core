from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
OUT = RC / "generated" / "reviews"
GENERATED_AT = "2026-09-25"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_fingerprint(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(payload.encode("utf-8"))


SOURCES = [
    {
        "source_id": "SRC-RULE-0910-2-PDF",
        "path": "sources/ルール0910-2.pdf",
        "sha256": "5e8ce2fb6a8d7264b36c50bc1d66c7e099ad693dbd5de8117e0c76c21cff5c41",
        "locators": ["pp.8-9 §1.3.1", "p.19 Scenario 1 Day 1", "ATO開始時処理", "ATO終了時帰還"],
        "role": "published_normative_source",
    },
    {
        "source_id": "SRC-RULE-0910-2-DOCX",
        "path": "sources/ルール0910-2.docx",
        "sha256": "4c203ab3923cf45ead330ab26f8f38b2460e84332938f814b6498516cdbe945d",
        "locators": ["paragraphs 125-143", "184-192", "257-268", "335-358", "536-541"],
        "role": "authoring_and_extraction_source",
    },
    {
        "source_id": "SRC-BOARD-A3-0915",
        "path": "sources/【A3判】ボード0915.pdf",
        "sha256": "b08634ad449bf84e0e4d92f8a54ad4a97f0133ccf394bafaaa43d6cdd678c18d",
        "locators": ["pp.4-5 指揮所活動スター掌握ボード"],
        "role": "published_normative_source_for_star_flow_and_activation_cost_placement",
    },
    {
        "source_id": "SRC-BOARD-A4-0815-01",
        "path": "sources/【A4判】 ボード 0815-01.pdf",
        "sha256": "e41842fce600a846c2fcef90b73c7b5c02318b22c7527843f81e69b95723ddbf",
        "locators": ["pp.1-6 基地群別整備補給・航空運用インフラ"],
        "role": "normative_component_source_canonical_record_pending",
    },
    {
        "source_id": "SRC-SQUADRON-0901",
        "path": "sources/スコードロン0901.pdf",
        "sha256": "8ebfd4ec42f782e30f591b770206a07e89969334cf68fecf4b8db71e6de7d8b7",
        "locators": ["p.2 STC-SQ-04 KJ-500", "p.3 STC-SQ-13 KQ-200"],
        "role": "published_normative_component_source",
    },
    {
        "source_id": "SRC-TOKEN-0901-1",
        "path": "sources/トークン類0901-1.pdf",
        "sha256": "bfe2d4baa8a91c217c0e9c8828a58f37f89676cfa3aa5559cc9e730ce9616871",
        "locators": ["pp.5-6 KJ-500/AEW and KQ-200 token faces"],
        "role": "published_normative_component_source",
    },
]


FRAGMENTS = {
    "activation_pdf": "FRAG-RULE-0910-2-PDF-P8-9-SQUADRON-ACTIVATION",
    "activation_docx": "FRAG-RULE-0910-2-DOCX-P184-192-SQUADRON-ACTIVATION",
    "scenario_pdf": "FRAG-RULE-0910-2-PDF-P19-SCENARIO1-PRC-DAY1-SQUADRONS",
    "scenario_docx": "FRAG-RULE-0910-2-DOCX-P536-541-SCENARIO1-PRC-DAY1-SQUADRONS",
    "a3": "FRAG-BOARD-A3-0915-ENTIRE",
    "a4": "FRAG-BOARD-A4-0815-01-ENTIRE",
    "kj_plate": "FRAG-SQUADRON-0901-P2-STC-SQ-04",
    "kj_token": "FRAG-TOKEN-0901-1-P5-6-KJ-500",
    "kq_plate": "FRAG-SQUADRON-0901-P3-STC-SQ-13",
    "kq_token": "FRAG-TOKEN-0901-1-P5-6-KQ-200",
}


RULE_PROPOSALS = [
    {
        "id": "RC-SQUADRON-DEPLOYMENT-001",
        "name_ja": "スコードロンプレートの配備",
        "definition": "ATO準備で選択したスコードロンプレートを基地群へ配備し、新規配備時は未捕捉とする共通規則。",
        "scope": "ATO開始時の展開準備解決、配備基地群、初期未捕捉状態",
        "excludes": "activation、出撃コスト、整備補給判定、トークン生成、捕捉判定",
        "actor": "各陣営プレイヤー",
        "target": "選択したスコードロンプレートと配備基地群",
        "interaction_type": "ordered_setup",
        "visibility": "not_stated",
        "source_fragment_ids": [FRAGMENTS["scenario_pdf"], FRAGMENTS["scenario_docx"], FRAGMENTS["a3"]],
        "decision_ids": [],
        "supersedes": [],
        "status": "proposal_not_registered",
    },
    {
        "id": "RC-SQUADRON-ACTIVATION-001",
        "name_ja": "スコードロン共通activation",
        "definition": "配備済みプレート、生成予定数及び配備基地群を選び、印字出撃コストと基地残余キャパシティを確認してコストを支払う共通規則。",
        "scope": "選択、生成予定数宣言、最大数・利用可能token確認、出撃可否、★支払、同一ATO内の再activation",
        "excludes": "整備補給D4、実生成数、地上断念、token配置、個別スコードロン性能",
        "actor": "当該スコードロンを管理するプレイヤー",
        "target": "配備済みスコードロンプレート、配備基地群、生成予定token",
        "interaction_type": "sequential_action",
        "visibility": "not_stated",
        "source_fragment_ids": [FRAGMENTS["activation_pdf"], FRAGMENTS["activation_docx"], FRAGMENTS["a3"]],
        "decision_ids": [],
        "supersedes": [],
        "status": "proposal_not_registered",
    },
    {
        "id": "RC-SQUADRON-GENERATION-001",
        "name_ja": "スコードロンtoken生成",
        "definition": "支払済みactivationについて基地群の整備補給欄に従いD4を解決し、実生成数、地上断念及びtoken配置を確定する共通規則。",
        "scope": "整備補給判定、実生成数、0以下、地上断念、分散配置時の除去、通常又は兆候marker経由の配置",
        "excludes": "activation合法性と支払、艦船・ADA生成、個別token性能、移動・捕捉・攻撃",
        "actor": "activationを宣言したプレイヤー及び自動判定",
        "target": "宣言した生成予定token、配備基地群、生成hex",
        "interaction_type": "automatic_resolution; placement choice exists only where the source rule offers multiple legal hexes, then sequential_action",
        "visibility": "not_stated",
        "source_fragment_ids": [FRAGMENTS["activation_pdf"], FRAGMENTS["activation_docx"], FRAGMENTS["a4"]],
        "decision_ids": [],
        "supersedes": [],
        "status": "proposal_not_registered",
    },
    {
        "id": "RC-SQUADRON-RETURN-001",
        "name_ja": "スコードロン由来航空機tokenの通常帰還",
        "definition": "ATO終了時又は規定された帰還契機に、残存する航空機tokenをtoken poolへ戻し、捕捉・弾薬・燃料をresetして再生成可能にする共通規則。",
        "scope": "通常帰還、ATO終了時帰還、token poolへの復帰と明記されたreset",
        "excludes": "撃破token、plate撃破時の飛行中token除去、艦載機の帰投先喪失、activation処理",
        "actor": "cleanup又は規定された自動処理",
        "target": "残存するスコードロン由来航空機token",
        "interaction_type": "automatic_resolution",
        "visibility": "not_stated",
        "source_fragment_ids": [FRAGMENTS["activation_pdf"]],
        "decision_ids": [],
        "supersedes": [],
        "status": "proposal_not_registered",
    },
]


STATE_PROPOSALS = [
    {
        "id": "STATE-SQUADRON-PLATE-DEPLOYMENT",
        "name_ja": "スコードロンプレート配備状態",
        "value_type": "record",
        "allowed_values": {"component_id": "COMP-SQUADRON-*", "base_group_id": "existing/proposed base ID", "deployed": "boolean"},
        "owner": "プレート管理陣営",
        "visibility": "not_stated",
        "persistence": "persistent across ATO unless a rule removes the plate",
        "basis": "ルールPDFの配備と維持、Scenario 1初期準備",
        "reason": "activation対象と通常生成位置を同定するため。捕捉は既存STATE-SQUADRON-ACQUIREDを再利用し、重複させない。",
        "status": "proposal_not_registered",
    },
    {
        "id": "STATE-SQUADRON-TOKEN-CUSTODY",
        "name_ja": "スコードロン由来token所在状態",
        "value_type": "record per physical token",
        "allowed_values": {"zone": ["token_pool", "map", "removed_tray"], "hex_id": "string or not_applicable", "source_plate_id": "COMP-SQUADRON-*"},
        "owner": "token管理陣営",
        "visibility": "not_stated; existing acquisition rules remain separate",
        "persistence": "persistent",
        "basis": "ルールPDF pp.8-9のpool/map/removed tray図、地上断念、帰還",
        "reason": "利用可能未生成数、盤上生成数、恒久喪失数を同一の物理token所在から導出し、別々の重複counterを作らないため。",
        "status": "proposal_not_registered",
    },
    {
        "id": "STATE-COMMAND-STARS-AVAILABLE",
        "name_ja": "使用可能★数",
        "value_type": "integer",
        "allowed_values": "0..40 per faction, subject to other approved rules",
        "owner": "各陣営",
        "visibility": "not_stated",
        "persistence": "persistent resource state",
        "basis": "A3 0915 pp.4-5 使用可能スター・プレース",
        "reason": "activation時に実際に支払える★と支払後残数を追跡するため。既存RATE IDはレートであり代替不可。",
        "status": "proposal_not_registered",
    },
    {
        "id": "STATE-BASE-SORTIE-CAPACITY",
        "name_ja": "基地群出撃キャパシティ状態",
        "value_type": "record per base group",
        "allowed_values": {"effective_capacity": "non-negative integer", "committed_cost": "non-negative integer", "remaining_capacity": "derived non-negative integer"},
        "owner": "基地群管理陣営",
        "visibility": "not_stated",
        "persistence": "persistent during an ATO; committed ★ return at ATO end",
        "basis": "ルールPDF pp.8-9、A3 0915 pp.4-5、A4 0815-01 base boards",
        "reason": "★の全体在庫と、基地ごとの出撃上限を混同せず合法性を判定するため。",
        "status": "proposal_not_registered",
    },
    {
        "id": "STATE-BASE-AIR-OPERATIONS-INFRASTRUCTURE-DAMAGE",
        "name_ja": "基地群航空運用インフラ被害",
        "value_type": "integer damage level per base group",
        "allowed_values": "printed board track for that base group",
        "owner": "基地群",
        "visibility": "not_stated",
        "persistence": "persistent; affects sortie capacity from the following day",
        "basis": "ルールDOCX 263-268、A4 0815-01 pp.1-6",
        "reason": "effective sortie capacityの規範入力。整備補給被害とは効果と時点が異なる。",
        "status": "proposal_not_registered",
    },
    {
        "id": "STATE-BASE-MAINTENANCE-SUPPLY-DAMAGE",
        "name_ja": "基地群整備補給基盤被害",
        "value_type": "integer damage level per base group",
        "allowed_values": "printed board track for that base group",
        "owner": "基地群",
        "visibility": "not_stated",
        "persistence": "persistent; affects token generation immediately",
        "basis": "ルールDOCX 191, 263-268、A4 0815-01 pp.1-6",
        "reason": "D4から実生成数を決める規範入力。航空運用インフラ被害とは別状態。",
        "status": "proposal_not_registered",
    },
    {
        "id": "STATE-SQUADRON-ACTIVATION-IN-PROGRESS",
        "name_ja": "スコードロンactivation進行中",
        "value_type": "temporary structured record",
        "allowed_values": {
            "plate_id": "COMP-SQUADRON-*",
            "base_group_id": "base ID",
            "requested_token_count": "positive integer",
            "maximum_token_count": "positive integer",
            "required_star_cost": "non-negative integer",
            "paid_star_cost": "non-negative integer",
            "maintenance_roll": "D4 result or not_yet_resolved",
            "actual_generated_count": "non-negative integer or not_yet_resolved",
            "ground_abort_count": "non-negative integer or not_yet_resolved",
        },
        "owner": "acting player and rules procedure",
        "visibility": "not_stated",
        "persistence": "temporary until EVENT-SQUADRON-ACTIVATION-COMPLETED",
        "basis": "正式手順が宣言、支払、判定、配置を順に区別する",
        "reason": "宣言後からD4・配置完了までの規則上の未完了処理を保存・Replayでき、要求数、実生成数、必要★、実支払★を混同しないため。continuation/stack/resume tokenは含めない。",
        "status": "proposal_not_registered_owner_confirmation_required",
    },
]


EVENT_PROPOSALS = [
    {
        "id": "EVENT-SQUADRON-PLATE-DEPLOYED",
        "name_ja": "スコードロンプレート配備",
        "condition": "ATO準備で部隊と基地群を確定したとき",
        "actor": "管理陣営プレイヤー",
        "target": "plate and base group",
        "payload": ["component_id", "base_group_id", "initial_acquisition_state"],
        "state_effect": "STATE-SQUADRON-PLATE-DEPLOYMENTを設定。捕捉はSTATE-SQUADRON-ACQUIREDで別管理。",
        "visibility": "not_stated",
        "source_fragment_ids": [FRAGMENTS["scenario_pdf"], FRAGMENTS["scenario_docx"], FRAGMENTS["a3"]],
        "why_not_existing": "既存Eventはrate、MD、即応、intelに限定され、plate配備を表さない。",
    },
    {
        "id": "EVENT-SQUADRON-ACTIVATION-DECLARED",
        "name_ja": "スコードロンactivation宣言",
        "condition": "plateと生成予定数を宣言したとき",
        "actor": "管理陣営プレイヤー",
        "target": "deployed squadron plate",
        "payload": ["plate_id", "base_group_id", "requested_token_count", "maximum_token_count", "available_pool_token_count", "required_star_cost"],
        "state_effect": "STATE-SQUADRON-ACTIVATION-IN-PROGRESSを開始",
        "visibility": "not_stated",
        "source_fragment_ids": [FRAGMENTS["activation_pdf"]],
        "why_not_existing": "EVENT-INTEL-TARGET-CONFIRMEDはintel対象選択でありactivation宣言へ意味拡張できない。",
    },
    {
        "id": "EVENT-SQUADRON-SORTIE-COST-PAID",
        "name_ja": "スコードロン出撃コスト支払",
        "condition": "利用可能★と基地残余キャパシティが必要額を満たし、★を基地群boardへ置いたとき",
        "actor": "管理陣営プレイヤー",
        "target": "faction star pool and base group",
        "payload": ["plate_id", "base_group_id", "required_star_cost", "paid_star_cost", "available_stars_before", "available_stars_after", "sortie_capacity_before", "sortie_capacity_after"],
        "state_effect": "STATE-COMMAND-STARS-AVAILABLE及びSTATE-BASE-SORTIE-CAPACITYを更新",
        "visibility": "not_stated",
        "source_fragment_ids": [FRAGMENTS["activation_pdf"], FRAGMENTS["activation_docx"], FRAGMENTS["a3"]],
        "why_not_existing": "既存rate change Eventは★resource移動を表さない。要求額と実支払額を別payloadに保持する。",
    },
    {
        "id": "EVENT-SQUADRON-MAINTENANCE-RESOLVED",
        "name_ja": "スコードロン整備補給判定解決",
        "condition": "支払後、配備基地群の印字整備補給欄に従うD4を解決したとき",
        "actor": "rules resolution",
        "target": "requested tokens and base maintenance profile",
        "payload": ["plate_id", "base_group_id", "requested_token_count", "D4_result", "maintenance_damage_level", "printed_formula", "computed_generation_limit", "actual_generated_count", "ground_abort_count"],
        "state_effect": "activation進行中recordの実生成数と地上断念数を確定",
        "visibility": "not_stated",
        "source_fragment_ids": [FRAGMENTS["activation_pdf"], FRAGMENTS["activation_docx"], FRAGMENTS["a4"]],
        "why_not_existing": "既存MD resolved Eventは別判定であり再利用不可。D4と生成数を一意に結び付ける。",
    },
    {
        "id": "EVENT-SQUADRON-GROUND-ABORT-RESOLVED",
        "name_ja": "スコードロン地上断念処理",
        "condition": "requested_token_countがactual_generated_countを上回るとき",
        "actor": "rules resolution",
        "target": "ungenerated physical tokens",
        "payload": ["plate_id", "base_group_id", "ground_abort_count", "tokens_remaining_in_pool", "dispersed_base", "removed_token_ids"],
        "state_effect": "通常はpool維持。分散配置中は地上断念tokenのうち1個をremoved trayへ移す。",
        "visibility": "not_stated",
        "source_fragment_ids": [FRAGMENTS["activation_pdf"], FRAGMENTS["activation_docx"], FRAGMENTS["a4"]],
        "why_not_existing": "単なる生成失敗ではなく、分散配置時のtoken除去を伴い得る独立した規範結果。",
    },
    {
        "id": "EVENT-SQUADRON-TOKENS-GENERATED",
        "name_ja": "スコードロンtoken生成・配置",
        "condition": "actual_generated_countが1以上で、合法な生成hexを確定したとき",
        "actor": "管理陣営プレイヤー及びrules resolution",
        "target": "generated physical tokens and map hexes",
        "payload": ["plate_id", "base_group_id", "requested_token_count", "actual_generated_count", "token_ids", "placement_hex_ids", "placement_rule"],
        "state_effect": "該当tokenのSTATE-SQUADRON-TOKEN-CUSTODYをpoolからmapへ変更",
        "visibility": "not_stated; acquisition/reveal state is governed separately",
        "source_fragment_ids": [FRAGMENTS["activation_pdf"], FRAGMENTS["activation_docx"]],
        "why_not_existing": "既存EVENT-COMPONENT-REVEALEDは公開であり、未捕捉tokenの生成・配置を表せない。",
    },
    {
        "id": "EVENT-SQUADRON-ACTIVATION-COMPLETED",
        "name_ja": "スコードロンactivation完了",
        "condition": "支払、整備補給、地上断念及び生成配置がすべて確定したとき",
        "actor": "rules resolution",
        "target": "one activation instance",
        "payload": ["plate_id", "base_group_id", "requested_token_count", "maximum_token_count", "required_star_cost", "paid_star_cost", "actual_generated_count", "ground_abort_count", "generated_token_ids"],
        "state_effect": "STATE-SQUADRON-ACTIVATION-IN-PROGRESSを終了。plate自体にはactivation済みflagを付けない。",
        "visibility": "not_stated",
        "source_fragment_ids": [FRAGMENTS["activation_pdf"], FRAGMENTS["activation_docx"], FRAGMENTS["a4"]],
        "why_not_existing": "同一plateを同一ATOで再activationできるため、完了instanceをplate状態と混同せずAARへ記録する必要がある。",
    },
    {
        "id": "EVENT-SQUADRON-TOKENS-RETURNED",
        "name_ja": "スコードロン由来航空機token通常帰還",
        "condition": "ATO終了時又は規定された通常帰還契機",
        "actor": "rules resolution",
        "target": "returning squadron-derived aircraft tokens",
        "payload": ["token_ids", "return_reason", "from_hex_ids", "to_zone", "reset_fields"],
        "state_effect": "custodyをmapからtoken_poolへ変更し、明記された捕捉・弾薬・燃料をreset",
        "visibility": "not_stated",
        "source_fragment_ids": [FRAGMENTS["activation_pdf"], FRAGMENTS["activation_docx"]],
        "why_not_existing": "既存Eventに航空機帰還と再生成可能化を表すものがない。",
    },
]


TRANSITIONS = [
    (1, "activation可能plate確認", "管理陣営", "配備済みplate", "plate配備、非破壊、token custody、base状態", "合法候補を確認", "none", "none", "候補集合", "none", "not_stated", "source_rule/component_data", [FRAGMENTS["activation_pdf"], FRAGMENTS["scenario_pdf"]]),
    (2, "activation plate選択", "管理陣営", "plate 1枚", "合法候補集合", "1枚を選択", "none", "none", "選択済みplate", "EVENT-SQUADRON-ACTIVATION-DECLAREDに包含", "not_stated", "source_rule", [FRAGMENTS["activation_pdf"]]),
    (3, "生成予定数宣言", "管理陣営", "physical token数", "maxとpool availability", "requested countを宣言", "none", "none", "requested_token_count", "EVENT-SQUADRON-ACTIVATION-DECLARED", "not_stated", "source_rule", [FRAGMENTS["activation_pdf"]]),
    (4, "最大生成数確認", "rules", "plate/component data", "printed maxとremoved token", "requestが上限内か確認", "none", "none", "maximum_token_count", "同上payload", "not_stated", "component_data/source_rule", [FRAGMENTS["kj_plate"], FRAGMENTS["kq_plate"], FRAGMENTS["activation_pdf"]]),
    (5, "必要★算出", "rules", "plate printed sortie cost", "plate component data", "activation 1回分を算出", "required_star_cost", "none", "必要★", "同上payload", "not_stated", "component_data/source_rule", [FRAGMENTS["kj_plate"], FRAGMENTS["kq_plate"], FRAGMENTS["activation_pdf"]]),
    (6, "★支払可否確認", "rules", "available stars/base remaining capacity", "必要★と2つのresource state", "双方が足りるか", "none", "none", "legal/illegal", "illegalならEventなし", "not_stated", "source_rule/component_data", [FRAGMENTS["activation_pdf"], FRAGMENTS["a3"], FRAGMENTS["a4"]]),
    (7, "★支払", "管理陣営", "star pool/base board", "legal activation", "基地群boardへ置く", "requiredとpaidを別記録", "none", "available減・committed増", "EVENT-SQUADRON-SORTIE-COST-PAID", "not_stated", "source_rule/component_data", [FRAGMENTS["activation_pdf"], FRAGMENTS["a3"]]),
    (8, "配備基地群と生成位置確認", "rules/管理陣営", "plate/base/map", "plate deployment", "通常base hex又は兆候marker範囲", "none", "none", "legal placement scope", "generation Eventへ包含", "not_stated", "source_rule", [FRAGMENTS["activation_pdf"]]),
    (9, "整備補給判定要否", "rules", "base maintenance profile", "damage levelとrequested count", "board記載制限を適用", "paid cost is retained", "base-specific", "roll pending/automatic formula", "none", "not_stated", "source_rule/component_data", [FRAGMENTS["activation_pdf"], FRAGMENTS["a4"]]),
    (10, "D4解決", "rules/random source", "maintenance profile", "cost paid", "D4をprofileへ適用", "none", "D4", "computed generation limit", "EVENT-SQUADRON-MAINTENANCE-RESOLVED", "not_stated", "source_rule/component_data", [FRAGMENTS["activation_pdf"], FRAGMENTS["a4"]]),
    (11, "実生成数確定", "rules", "requested tokens", "requested countと整備補給判定結果", "宣言した生成予定数について、整備補給欄の判定に従い実生成数を確定", "none", "resolved D4", "actual_generated_count", "maintenance Event payload", "not_stated", "source_rule/component_data", [FRAGMENTS["activation_pdf"], FRAGMENTS["a4"]]),
    (12, "未生成分確定", "rules", "remaining requested tokens", "requested - actual", "ground_abort_countを確定", "cost not refunded", "none", "通常pool残留", "EVENT-SQUADRON-GROUND-ABORT-RESOLVED", "not_stated", "source_rule", [FRAGMENTS["activation_pdf"]]),
    (13, "地上断念処理", "rules", "ground-abort tokens", "分散配置の有無", "通常pool維持、分散時1個除去", "no refund", "none", "custody更新", "EVENT-SQUADRON-GROUND-ABORT-RESOLVED", "not_stated", "source_rule/component_data", [FRAGMENTS["activation_pdf"], FRAGMENTS["a4"]]),
    (14, "plate状態更新", "rules", "selected plate", "activation完了", "activation済みflagは作らない", "none", "none", "配備・捕捉・damageは原則不変", "none", "not_stated", "source_rule/not_applicable", [FRAGMENTS["activation_pdf"]]),
    (15, "token盤上配置", "管理陣営/rules", "actual generated tokens", "legal placement scope", "token poolからmapへ", "none", "none", "custody=map and hex", "EVENT-SQUADRON-TOKENS-GENERATED", "not_stated", "source_rule", [FRAGMENTS["activation_pdf"]]),
    (16, "activation完了", "rules", "activation instance", "all prior results fixed", "summary確定", "required/paid preserved", "D4/result preserved", "temporary state終了", "EVENT-SQUADRON-ACTIVATION-COMPLETED", "not_stated", "source_rule plus proposed audit event", [FRAGMENTS["activation_pdf"], FRAGMENTS["activation_docx"]]),
]


REUSE = [
    {"id": "STATE-SQUADRON-ACQUIRED", "reuse": "yes_limited", "covers": "plate捕捉済み状態", "does_not_cover": "配備、activation、token生成・所在"},
    {"id": "STATE-COMPONENT-REVEALED", "reuse": "yes_limited", "covers": "別規則により公開済みとなったcomponent", "does_not_cover": "未捕捉plate又はtokenのactivation公開範囲"},
    {"id": "sequential_action", "reuse": "yes", "covers": "plateと生成予定数の選択・宣言、必要時の配置選択", "does_not_cover": "D4自動解決"},
    {"id": "automatic_resolution", "reuse": "yes", "covers": "整備補給D4、実生成数、cleanup帰還", "does_not_cover": "プレイヤー選択"},
    {"id": "ordered_setup", "reuse": "yes", "covers": "ATO開始時の展開準備", "does_not_cover": "turn中activation"},
]


APPLICATIONS = [
    {
        "name": "KJ-500",
        "component_id": "COMP-SQUADRON-STC-SQ-04",
        "plate": {"maximum_token_count": 1, "sortie_cost_stars": 2},
        "example": {"requested_token_count": 1, "required_star_cost": 2, "paid_star_cost": 2, "placement": "deployed_base_group_hex"},
        "rule_ids": ["RC-SQUADRON-ACTIVATION-001", "RC-SQUADRON-GENERATION-001"],
        "state_ids": ["STATE-SQUADRON-PLATE-DEPLOYMENT", "STATE-SQUADRON-TOKEN-CUSTODY", "STATE-COMMAND-STARS-AVAILABLE", "STATE-BASE-SORTIE-CAPACITY", "STATE-BASE-MAINTENANCE-SUPPLY-DAMAGE", "STATE-SQUADRON-ACTIVATION-IN-PROGRESS"],
        "event_sequence": ["EVENT-SQUADRON-ACTIVATION-DECLARED", "EVENT-SQUADRON-SORTIE-COST-PAID", "EVENT-SQUADRON-MAINTENANCE-RESOLVED", "EVENT-SQUADRON-TOKENS-GENERATED", "EVENT-SQUADRON-ACTIVATION-COMPLETED"],
        "note": "実生成数は基地群整備補給D4に従う。例はrule vectorではなく、成功して1 tokenを配備基地群hexへ置く語彙適用例。",
    },
    {
        "name": "KQ-200",
        "component_id": "COMP-SQUADRON-STC-SQ-13",
        "plate": {"maximum_token_count": 1, "sortie_cost_stars": 2},
        "example": {"requested_token_count": 1, "required_star_cost": 2, "paid_star_cost": 2, "placement": "deployed_base_group_hex"},
        "rule_ids": ["RC-SQUADRON-ACTIVATION-001", "RC-SQUADRON-GENERATION-001"],
        "state_ids": ["STATE-SQUADRON-PLATE-DEPLOYMENT", "STATE-SQUADRON-TOKEN-CUSTODY", "STATE-COMMAND-STARS-AVAILABLE", "STATE-BASE-SORTIE-CAPACITY", "STATE-BASE-MAINTENANCE-SUPPLY-DAMAGE", "STATE-SQUADRON-ACTIVATION-IN-PROGRESS"],
        "event_sequence": ["EVENT-SQUADRON-ACTIVATION-DECLARED", "EVENT-SQUADRON-SORTIE-COST-PAID", "EVENT-SQUADRON-MAINTENANCE-RESOLVED", "EVENT-SQUADRON-TOKENS-GENERATED", "EVENT-SQUADRON-ACTIVATION-COMPLETED"],
        "note": "実生成数は基地群整備補給D4に従う。例はrule vectorではなく、成功して1 tokenを配備基地群hexへ置く語彙適用例。",
    },
]


STOP_ITEMS = [
    {
        "id": "STOP-ACTIVATION-VISIBILITY",
        "classification": "unresolved_candidate",
        "finding": "正式資料はactivation宣言、plate identity、生成予定数、支払、D4、地上断念、生成配置をどの陣営へ公開するかを一意に定めない。物理的に見えることを規範公開契約へ自動変換しない。",
        "impact": "全proposal IDのvisibilityをapprovedとして登録できず、candidate rule vectorのknowledge/visibility期待値を作れない。",
        "owner_question": "activationの各段階について、BLUE・RED双方へ公開する項目と、管理陣営だけに保持する項目は何ですか。",
    },
    {
        "id": "STOP-BASE-BOARD-CANONICAL",
        "classification": "source_governance_confirmation_required",
        "finding": "基地群別の整備補給・航空運用インフラtrackはA3 0915ではなくA4 0815-01にあり、source registerではnormativeだがcanonical_recordはpending。",
        "impact": "共通Rule/State/Event語彙は提案できるが、基地別式を正式データへ登録する工程は停止。",
        "owner_question": "SRC-BOARD-A4-0815-01を現行基地群boardのcanonical published normative sourceとして使用してよいですか。",
    },
]


def proposal() -> dict:
    value = {
        "schema_version": "0.1.0",
        "document_type": "non_normative_id_proposal",
        "generated_at": GENERATED_AT,
        "normative_authority": False,
        "registration_performed": False,
        "candidate_vectors_created": 0,
        "scope": "common squadron deployment, activation, generation, ground abort, token custody, and return vocabulary",
        "source_review": {
            "sources": SOURCES,
            "pass_1": "DOCX paragraph extraction plus PDF text extraction",
            "pass_2": "fresh visual review of rule PDF pp.8-9, A3 0915 pp.4-5, A4 0815-01 PRC base-board pp.4-6, and existing independently verified KJ-500/KQ-200 component fragments",
            "result": "semantic_match_in_reviewed_scope",
        },
        "boundary_findings": {
            "activation": "plate and requested count declaration plus sortie legality and cost payment",
            "generation": "maintenance-supply D4, actual generated count, ground abort, and map placement",
            "boundary": "distinct ordered state transitions inside one activation procedure",
            "cost_timing": "paid on activation before maintenance-supply resolution and not refunded on zero generation",
            "damage_relationship": "air-operations infrastructure affects sortie capacity from the following day; maintenance-supply damage affects generation immediately",
            "plate_after_activation": "no activation-used flag; same plate may activate repeatedly in the same ATO if cost can be paid",
        },
        "existing_id_coverage": REUSE,
        "rule_core_id_proposals": RULE_PROPOSALS,
        "state_id_proposals": STATE_PROPOSALS,
        "event_id_proposals": EVENT_PROPOSALS,
        "transitions": [
            {
                "step": r[0], "name": r[1], "actor": r[2], "target": r[3], "input_state": r[4], "decision": r[5],
                "cost": r[6], "determination": r[7], "output_state": r[8], "event": r[9], "visibility": r[10],
                "authority": r[11], "source_fragment_ids": r[12]
            }
            for r in TRANSITIONS
        ],
        "applications": APPLICATIONS,
        "aar_relationship": {
            "normal_candidate_required_states": ["STATE-SQUADRON-PLATE-DEPLOYMENT", "STATE-SQUADRON-TOKEN-CUSTODY", "STATE-COMMAND-STARS-AVAILABLE", "STATE-BASE-SORTIE-CAPACITY", "STATE-BASE-AIR-OPERATIONS-INFRASTRUCTURE-DAMAGE"],
            "legality_rule_ids": ["RC-SQUADRON-ACTIVATION-001"],
            "aar_events": ["EVENT-SQUADRON-ACTIVATION-DECLARED", "EVENT-SQUADRON-SORTIE-COST-PAID", "EVENT-SQUADRON-MAINTENANCE-RESOLVED", "EVENT-SQUADRON-GROUND-ABORT-RESOLVED", "EVENT-SQUADRON-TOKENS-GENERATED", "EVENT-SQUADRON-ACTIVATION-COMPLETED"],
            "candidate_nature": "Digital projection, not Rule Core normative state",
            "protected_expected_candidate_count": 15,
            "change_performed": False,
        },
        "stop_items": STOP_ITEMS,
        "id_counts": {"rule_core": len(RULE_PROPOSALS), "state": len(STATE_PROPOSALS), "event": len(EVENT_PROPOSALS), "total": len(RULE_PROPOSALS) + len(STATE_PROPOSALS) + len(EVENT_PROPOSALS)},
        "naming_note": "ID prefix identifies the classification at first allocation and does not guarantee a current file location.",
        "status": "proposal_complete_registration_blocked_pending_owner_answers",
    }
    value["proposal_payload_fingerprint_sha256"] = canonical_fingerprint(value)
    return value


def md_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(v).replace("\n", "<br>") for v in row) + " |")
    return out


def analysis_md(p: dict) -> str:
    lines = [
        "# スコードロン共通activation ID語彙 分析報告",
        "",
        "> 非規範のproposalです。IDの正式登録、Rule Core規範変更、candidate vector作成、Digital変更は行っていません。",
        "",
        "## 結論",
        "",
        "正式資料では、activationは一つの手順ですが、宣言・支払と、整備補給D4・実生成・地上断念・配置は別の状態遷移です。既存IDにはこの意味を完全に表すものがありません。既存interaction typeの `ordered_setup`、`sequential_action`、`automatic_resolution` で表現でき、新しいinteraction typeは不要です。",
        "",
        "ただし公開範囲は `not_stated` です。また基地群別trackを担う `SRC-BOARD-A4-0815-01` はsource register上でcanonical未確定です。この2点の所有者確認までは正式登録とrule vector作成を停止します。",
        "",
        "## 正式資料の担体分担",
        "",
    ]
    lines += md_table(["資料", "担う範囲", "位置"], [[s["source_id"], s["role"], "; ".join(s["locators"])] for s in p["source_review"]["sources"]])
    lines += [
        "",
        "A3 0915は★の流れとactivation時の出撃コストを基地群boardへ置くことを担います。基地群別の出撃キャパシティ、整備補給D4及び損害trackはA4 0815-01が担います。両者を同じboardとして扱いません。",
        "",
        "## activationと生成の境界",
        "",
        "- activation: 配備済みplateと生成予定数を宣言し、最大数・物理token・利用可能★・基地残余キャパシティを確認して出撃コストを支払う段階。",
        "- generation: 支払後に基地群の整備補給欄に従ってD4を解決し、実生成数、地上断念、token所在及び配置hexを確定する段階。",
        "- 支払時点: 整備補給判定より前。実生成数が0でも返還しません。",
        "- plate状態: 同一ATOに複数回activationできるため、activation済みflagを持たせません。",
        "- 基地損害: 航空運用インフラは翌日以降の出撃キャパシティ、整備補給基盤は直ちに生成数へ影響します。",
        "",
        "## 16段階の状態遷移",
        "",
    ]
    lines += md_table(
        ["#", "段階", "Actor", "Target", "入力", "判断・判定", "Cost", "出力", "Event", "公開", "根拠"],
        [[r["step"], r["name"], r["actor"], r["target"], r["input_state"], r["decision"] + (" / " + r["determination"] if r["determination"] != "none" else ""), r["cost"], r["output_state"], r["event"], r["visibility"], r["authority"]] for r in p["transitions"]],
    )
    lines += ["", "## 既存IDカバレッジ", ""]
    lines += md_table(["既存ID／語彙", "再利用", "対応範囲", "非対応範囲"], [[r["id"], r["reuse"], r["covers"], r["does_not_cover"]] for r in p["existing_id_coverage"]])
    lines += ["", "既存のrate/resource IDはレート値を表し、★resource、基地出撃キャパシティ又はactivationを表さないため、意味拡張して流用しません。既存Component IDはKJ-500／KQ-200同定に再利用します。既存rule vector IDには共通activationの入力から生成完了までを検証するものはありません。", "", "## Rule Core ID proposal", ""]
    lines += md_table(["ID", "名称", "一文定義", "interaction", "公開", "状態"], [[r["id"], r["name_ja"], r["definition"], r["interaction_type"], r["visibility"], r["status"]] for r in p["rule_core_id_proposals"]])
    lines += ["", "## State ID proposal", ""]
    lines += md_table(["ID", "名称", "型", "永続性", "公開", "必要理由"], [[r["id"], r["name_ja"], r["value_type"], r["persistence"], r["visibility"], r["reason"]] for r in p["state_id_proposals"]])
    lines += ["", "生成予定数と実生成数、必要★と実支払★は `STATE-SQUADRON-ACTIVATION-IN-PROGRESS` の別fieldとして保持します。利用可能未生成数と生成済み数は物理token custodyから導出し、重複counter State IDを作りません。", "", "## Event ID proposal", ""]
    lines += md_table(["ID", "名称", "発生条件", "主要payload", "状態への影響", "公開"], [[r["id"], r["name_ja"], r["condition"], ", ".join(r["payload"]), r["state_effect"], r["visibility"]] for r in p["event_id_proposals"]])
    lines += ["", "## KJ-500／KQ-200への同一語彙適用", ""]
    for app in p["applications"]:
        lines += [f"### {app['name']}", "", f"`{app['component_id']}` は最大{app['plate']['maximum_token_count']} token、出撃コスト★{app['plate']['sortie_cost_stars']}です。1 tokenを宣言し、★2を支払い、整備補給結果が1なら配備基地群hexへ1 tokenを置きます。個別性能はactivation語彙へ埋め込みません。", "", "Event列: " + " → ".join(f"`{x}`" for x in app["event_sequence"]), ""]
    lines += [
        "## AAR候補との関係",
        "",
        "通常操作候補はDigitalの投影でありRule Coreの規範状態ではありません。合法性は提案Rule IDとStateへ追跡し、AARは宣言、支払、D4結果、地上断念、生成配置、完了Eventを記録します。UI候補IDはRule Coreへ追加しません。AAR期待15件は変更していません。",
        "",
        "## ID数と最小化",
        "",
        f"proposalはRule Core ID {p['id_counts']['rule_core']}、State ID {p['id_counts']['state']}、Event ID {p['id_counts']['event']}、合計{p['id_counts']['total']}です。plate捕捉には既存IDを再利用し、token数はcustodyから導出し、activation済みflag、KJ-500/KQ-200専用ID、UI候補ID、continuation/stack/resume token IDを作りません。",
        "",
        "## 停止事項",
        "",
    ]
    for stop in p["stop_items"]:
        lines += [f"### {stop['id']}", "", stop["finding"], "", f"影響: {stop['impact']}", "", f"所有者への質問: {stop['owner_question']}", ""]
    lines += ["## Fingerprint", "", f"proposal payload: `{p['proposal_payload_fingerprint_sha256']}`", ""]
    return "\n".join(lines)


def owner_review_md(p: dict) -> str:
    lines = [
        "# スコードロン共通activation ID語彙 所有者確認票",
        "",
        "> 本確認票は規範正本ではありません。採用結果は後の作業で正本台帳へ反映します。今回、Codexはチェックを付けていません。",
        "",
        "## 確認の要点",
        "",
        "KJ-500とKQ-200へ同じ共通語彙を適用します。activationは宣言・出撃コスト支払、generationは整備補給D4・実生成・地上断念・配置です。公開範囲とA4基地群boardのcanonical指定が未確定なので、IDはまだ登録しません。",
        "",
        "## Rule Core ID",
        "",
    ]
    for r in p["rule_core_id_proposals"]:
        lines += [f"### {r['id']} {r['name_ja']}", "", r["definition"], "", f"適用: {r['scope']}", "", f"除外: {r['excludes']}", "", f"interaction type: `{r['interaction_type']}` / visibility: `{r['visibility']}`", "", "- [ ] 採用", "- [ ] 修正", "- [ ] 不採用", "名称・定義・粒度・重複・公開範囲への指示:", ""]
    lines += ["## State ID", ""]
    for r in p["state_id_proposals"]:
        lines += [f"### {r['id']} {r['name_ja']}", "", f"型: `{r['value_type']}`", "", f"必要理由: {r['reason']}", "", f"永続性: {r['persistence']} / visibility: `{r['visibility']}`", "", "- [ ] 採用", "- [ ] 修正", "- [ ] 不採用", "規範状態としての必要性・粒度・公開範囲への指示:", ""]
    lines += ["## Event ID", ""]
    for r in p["event_id_proposals"]:
        lines += [f"### {r['id']} {r['name_ja']}", "", f"発生条件: {r['condition']}", "", f"payload: {', '.join(r['payload'])}", "", f"状態への影響: {r['state_effect']}", "", f"visibility: `{r['visibility']}`", "", "- [ ] 採用", "- [ ] 修正", "- [ ] 不採用", "Event粒度・payload・公開範囲への指示:", ""]
    lines += [
        "## KJ-500適用例",
        "",
        "STC-SQ-04 KJ-500は最大1 token、出撃コスト★2です。1 tokenを宣言し、支払後に配備基地群の整備補給D4を解決します。実生成数が1ならKJ-500 tokenを配備基地群hexへ置きます。0ならcostは戻らず、地上断念としてpoolに残します。",
        "",
        "- [ ] この共通語彙で正しい",
        "- [ ] 修正が必要",
        "- [ ] 現時点では採用できない",
        "指示:",
        "",
        "## KQ-200適用例",
        "",
        "STC-SQ-13 KQ-200は最大1 token、出撃コスト★2です。1 tokenを宣言し、支払後に配備基地群の整備補給D4を解決します。実生成数が1ならKQ-200 tokenを配備基地群hexへ置きます。0ならcostは戻らず、地上断念としてpoolに残します。",
        "",
        "- [ ] この共通語彙で正しい",
        "- [ ] 修正が必要",
        "- [ ] 現時点では採用できない",
        "指示:",
        "",
        "## 登録前に必須の回答",
        "",
    ]
    for stop in p["stop_items"]:
        lines += [f"### {stop['id']}", "", stop["owner_question"], "", "回答:", ""]
    lines += ["## 技術的な追跡情報", "", f"proposal fingerprint: `{p['proposal_payload_fingerprint_sha256']}`", "", f"提案ID数: {p['id_counts']['total']}（Rule {p['id_counts']['rule_core']} / State {p['id_counts']['state']} / Event {p['id_counts']['event']}）", "", "登録状態: `proposal_not_registered`", ""]
    return "\n".join(lines)


def state_diagram() -> str:
    return """%% 非規範proposal。Rule Core ID registryへ未登録。
flowchart TD
  A[ATO準備: plateを基地群へ配備] --> B[合法性確認: plate/token/★/基地残余capacity]
  B -->|不適格| X[activation不成立・状態不変]
  B -->|適格| C[plateと生成予定数を宣言]
  C --> D[出撃costを支払う]
  D --> E[基地群の整備補給D4を解決]
  E --> F{実生成数}
  F -->|1以上| G[token poolからmapへ配置]
  F -->|予定数未満| H[未生成分をGround Abort]
  H -->|通常基地| I[token poolに残す]
  H -->|分散配置中| J[うち1 tokenを除去trayへ]
  G --> K[activation完了]
  I --> K
  J --> K
  K --> L[ATO終了時: 残存航空機tokenを通常帰還]
  L --> M[token poolへ戻し捕捉・弾薬・燃料reset]
"""


def write_outputs(p: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    yaml_path = OUT / "squadron-activation-id-proposal.yaml"
    json_path = OUT / "squadron-activation-id-owner-review.json"
    analysis_path = OUT / "squadron-activation-state-transition-analysis.md"
    review_path = OUT / "squadron-activation-id-owner-review.md"
    diagram_path = OUT / "squadron-activation-state-transition.mmd"
    yaml_path.write_text(yaml.safe_dump(p, allow_unicode=True, sort_keys=False, width=140), encoding="utf-8")
    json_path.write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    analysis_path.write_text(analysis_md(p) + "\n", encoding="utf-8")
    review_path.write_text(owner_review_md(p) + "\n", encoding="utf-8")
    diagram_path.write_text(state_diagram(), encoding="utf-8")
    artifacts = [yaml_path, json_path, analysis_path, review_path, diagram_path]
    manifest = {
        "schema_version": "0.1.0",
        "document_type": "non_normative_audit_manifest",
        "generated_at": GENERATED_AT,
        "generator": "rule-core/pipeline/generate-squadron-activation-id-proposal.py",
        "proposal_fingerprint_sha256": p["proposal_payload_fingerprint_sha256"],
        "artifacts": [{"path": x.relative_to(ROOT).as_posix(), "sha256": sha256_file(x), "bytes": x.stat().st_size} for x in artifacts],
        "protected_baseline": {
            "aar_expected_15_test_sha256": "7aa0488af2fc81eba034221127604d98be5c584494fe7cdf7679d954e005551c",
            "approved_vector_count": 129,
            "approved_vector_set_fingerprint": "087a7cab44a2eccd56426d3d921febcf3935f85b6d365a3702c6c199d88d8467",
            "rule_vector_files_aggregate_sha256": "b3a2dfbb4178a920e04198376ab42720fe8d8fe29d74245f54a373c91ee72340",
            "sources_count": 20,
            "sources_files_aggregate_sha256": "cded938f0d8b6523b138d7fca5aa39ad232aea5fa996c869771a93b9d55e31d7",
            "unresolved_sha256": "3c47ef86dd16ae67520d0c7b2b2526a1f971a505753feaff0316fce591f4bf6e",
        },
        "registration_performed": False,
        "candidate_vectors_created": 0,
    }
    (OUT / "squadron-activation-id-proposal-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_outputs(proposal())
