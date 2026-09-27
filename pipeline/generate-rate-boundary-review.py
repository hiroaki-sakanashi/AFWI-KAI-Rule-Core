#!/usr/bin/env python3
"""Generate non-normative rate-boundary analysis and owner-review artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
REVIEW_DIR = ROOT / "rule-core" / "generated" / "reviews"
GENERATED_AT = "2026-09-25"

PROTECTED = {
    "rule-core/rules": "5b494e05b350f453a47b3799fa891f164bcbe3c42ce88bbdd61ce9ec01ff7d1a",
    "rule-core/data": "6d413ddc229abaa45abda54c465be3554f48f7d4f563747a5021402853f6516f",
    "rule-core/tests/rule-vectors": "e60c9f8b341b31686275f745f171216463cd06dfa7f96df7516c502889b37a37",
    "rule-core/governance/decisions.yaml": "fb764d1c8e1e304dce1caddeef1af5fd3042192513ea3d86f7d2b5bb392502c9",
    "rule-core/governance/unresolved.yaml": "a5144703aa443c6ff2bb3f3c86f80eed5c195abd172861c300f20f57f08b3285",
    "sources": "cded938f0d8b6523b138d7fca5aa39ad232aea5fa996c869771a93b9d55e31d7",
}

SOURCES = {
    "SRC-RULE-0910-2-PDF": {
        "filename": "ルール0910-2.pdf",
        "sha256": "5e8ce2fb6a8d7264b36c50bc1d66c7e099ad693dbd5de8117e0c76c21cff5c41",
    },
    "SRC-RULE-0910-2-DOCX": {
        "filename": "ルール0910-2.docx",
        "sha256": "4c203ab3923cf45ead330ab26f8f38b2460e84332938f814b6498516cdbe945d",
    },
    "SRC-BOARD-A3-0915": {
        "filename": "【A3判】ボード0915.pdf",
        "sha256": "b08634ad449bf84e0e4d92f8a54ad4a97f0133ccf394bafaaa43d6cdd678c18d",
    },
    "SRC-ENABLER-0830-1": {
        "filename": "イネーブラー0830-1.pdf",
        "sha256": "9658e389e222ea12bbc8fbd8688eb3f14a971d85ce5a94ba289c8cc968b010bd",
    },
}

VISUAL_REVIEW = {
    "reviewed_at": GENERATED_AT,
    "renderer": "bundled Poppler",
    "render_dpi": 180,
    "coordinate_note": "Rendered-page hashes identify review evidence only; they are not game-state data.",
    "rendered_pages": {
        "SRC-RULE-0910-2-PDF": {
            "page_3_sha256": "f3e699521b6a6a11d87ebdf9dff10b756ea12ea01808ac148c5471c870ac68b5",
            "page_4_sha256": "b356e3bb73b2c254645fd0c1da63139789519c3fe0911b6653d7ea2b0cafc441",
            "page_15_sha256": "a39f65020b060578ad6e9270b8a8774bf7d4a6984a19e4fdaf9c08bab8028630",
            "page_20_sha256": "ffab58d8abbaf128c621f4b970c8c02cda90c85389d17942807ecdb4ababe4a2",
        },
        "SRC-BOARD-A3-0915": {
            "page_1_sha256": "cd987cc7cdd5ac38466018f6708e8064bbf1b32b069212961c88493b8d11d4e2",
            "page_2_sha256": "3b8590dd99ca59f1e4b0fabc5b6d40123c65300ce629afb70c5da138029709d6",
            "page_3_sha256": "e360202be4e9fb5aeded907be919fd2f2ed01425b353d90c8384faa85644b24e",
        },
        "SRC-ENABLER-0830-1": {
            "page_1_sha256": "1dc9491919f7b566ce9b63212ee921903add072f9213dc97cee5fa68539d6910",
            "page_2_sha256": "9586832e9704bb8e34f06707a34e3af9c4682860f9a70c5bcac64a55d5005197",
            "page_3_sha256": "f1a1eed803ec5b0aad362cfad9dad9234a42783daaef42ff7c394828fa451ba5",
            "page_4_sha256": "f2c0e9c068000b4af4485b06fd7062b79a51239166e41b266428ed9dcf560428",
            "page_7_sha256": "3b83eb8933ca37536a9218a2aecefdcf07941be70a3807b918cfd6519f70d34e",
            "page_9_sha256": "fb2253cc518c08429d46b3c0cdb816317237904599d118dc93f126aed9eb38b1",
            "page_11_sha256": "820be3e7251445cf7ba7c70d1d1fab2df73451dc6a2c9a97e43d99ba5e1f55b6",
            "page_14_sha256": "d6bc9d46cb4be571d163ced77c887266800b7cd51238751ee67f68ea5f43780f",
            "page_16_sha256": "b5a2928029730222b3b85419022530a6de4f0a7b6ae1da86c9f41fe2375935fa",
            "page_17_sha256": "c7ec5d35cc608a05062a512f9d6214f44cc01fc2004d2916117bea0ba1007e25",
            "page_20_sha256": "ec116a8a49547f033d0126257a785acc38b18f90749e5d6b9e0e13fef985379f",
            "page_56_sha256": "d2f1beeb6a6b67e7b5102316f42a4d9e5254b1f7b47f49ce1d45eda9e50edee1",
            "page_57_sha256": "34a76eb19c75012a72459a51332724fcc1b6a4d652257aec0548115e09c87a4d",
            "page_61_sha256": "d8ac53ef00aacdeda57f3fff2e3d5a2059123db370f131f3245f46f2a9199538",
            "page_62_sha256": "7f0482370935938c7c5edd36f7acf17659701cb69fe63efe7e99ebb289fc371f",
        },
    },
}

RATE_ROWS = [
    {
        "rate_id": "RATE-SPACE-US", "name": "US宇宙レート", "minimum": 0, "maximum": 4,
        "printed_terminal": "4+", "initial": 3, "blue_direction": "increase", "red_direction": "decrease",
        "endpoint_effect": "0又は4への到達だけを契機とする追加効果は明記されていない。2以下・1以下の閾値効果は別規則。",
        "crossing_possible": "カードに+2、-1、-2があり、現在値によっては範囲外要求が発生し得る。",
        "boundary_behavior": "not_stated", "scenario_difference": "not_stated",
    },
    {
        "rate_id": "RATE-SPACE-PRC", "name": "PRC宇宙レート", "minimum": 0, "maximum": 4,
        "printed_terminal": "4+", "initial": 3, "blue_direction": "decrease", "red_direction": "increase",
        "endpoint_effect": "0又は4への到達だけを契機とする追加効果は明記されていない。2以下・1以下の閾値効果は別規則。",
        "crossing_possible": "カードに+1、-1があり、現在値によっては範囲外要求が発生し得る。",
        "boundary_behavior": "not_stated", "scenario_difference": "not_stated",
    },
    {
        "rate_id": "RATE-CYBER-US", "name": "USサイバーレート", "minimum": 0, "maximum": 4,
        "printed_terminal": "4+", "initial": 1, "blue_direction": "increase", "red_direction": "decrease",
        "endpoint_effect": "4の状態でATO終了時に、次ATO中のサイバードミナンスが成立する。",
        "crossing_possible": "上昇カードと低下カードがあり、4での上昇要求又は0での低下要求が発生し得る。",
        "boundary_behavior": "not_stated", "scenario_difference": "確認したシナリオ資料に差分なし。",
    },
    {
        "rate_id": "RATE-CYBER-PRC", "name": "PRCサイバーレート", "minimum": 0, "maximum": 4,
        "printed_terminal": "4+", "initial": 1, "blue_direction": "decrease", "red_direction": "increase",
        "endpoint_effect": "4の状態でATO終了時に、次ATO中のサイバードミナンスが成立する。",
        "crossing_possible": "上昇カードと低下カードがあり、4での上昇要求又は0での低下要求が発生し得る。",
        "boundary_behavior": "not_stated", "scenario_difference": "確認したシナリオ資料に差分なし。",
    },
    {
        "rate_id": "RATE-STRATEGIC", "name": "共有戦略レート", "minimum": "PRC 6+", "maximum": "US 6+",
        "printed_terminal": "両方向6+", "initial": 0, "blue_direction": "US優勢方向", "red_direction": "PRC優勢方向",
        "endpoint_effect": "ATO終了時に6+なら劣勢側プレイヤーを更迭し、ゲームを終了する。",
        "crossing_possible": "シナリオ表に+3、+2、+1、カードに+1があり、同一ATO中に6+到達後の追加変更も発生し得る。",
        "boundary_behavior": "not_stated", "scenario_difference": "変更原因と終了条件にシナリオ差分があるが、6+超過処理の差分は明記されていない。",
    },
]

CHANGES = [
    ("CHG-SPACE-STC-SP-01", "STC-SP-01", "RATE-SPACE-US", "BLUE宇宙レート-1", "page 1", "FRAG-CAND-ENABLER-0830-1-STC-SP-01"),
    ("CHG-SPACE-STC-SP-02", "STC-SP-02", "RATE-SPACE-US / RATE-SPACE-PRC", "BLUE宇宙-2、RED宇宙-1", "page 2", "FRAG-CAND-ENABLER-0830-1-STC-SP-02"),
    ("CHG-SPACE-STC-SP-03", "STC-SP-03", "RATE-SPACE-US", "BLUE宇宙レート-2", "page 3", "FRAG-CAND-ENABLER-0830-1-STC-SP-03"),
    ("CHG-SPACE-STC-SP-04", "STC-SP-04", "RATE-SPACE-PRC", "RED宇宙レート+1", "page 4", "FRAG-CAND-ENABLER-0830-1-STC-SP-04"),
    ("CHG-SPACE-US-SP-01", "US-SP-01", "RATE-SPACE-PRC", "RED宇宙レート-1", "page 7", "FRAG-CAND-ENABLER-0830-1-US-SP-01"),
    ("CHG-STRATEGIC-US-SP-03", "US-SP-03", "RATE-STRATEGIC", "BLUE方向+1", "page 9", "FRAG-ENABLER-0830-1-US-SP-03"),
    ("CHG-SPACE-US-SP-05", "US-SP-05", "RATE-SPACE-US", "BLUE宇宙レート+2", "page 11", "FRAG-CAND-ENABLER-0830-1-US-SP-05"),
    ("CHG-CYBER-STC-CY-03", "STC-CY-03", "RATE-CYBER-PRC", "成功時REDサイバーレート+1", "page 14", "FRAG-CAND-ENABLER-0830-1-STC-CY-03"),
    ("CHG-CYBER-STC-CY-05", "STC-CY-05", "RATE-CYBER-US", "上昇を無効化し、さらにBLUEサイバーレート-1", "page 16", "FRAG-ENABLER-0830-1-STC-CY-05"),
    ("CHG-CYBER-US-CY-01", "US-CY-01", "RATE-CYBER-US", "成功時BLUEサイバーレート+1", "page 17", "FRAG-CAND-ENABLER-0830-1-US-CY-01"),
    ("CHG-CYBER-US-CY-04", "US-CY-04", "RATE-CYBER-PRC", "成功時REDサイバーレート-1", "page 20", "FRAG-CAND-ENABLER-0830-1-US-CY-04"),
    ("CHG-STRATEGIC-US-IW-04", "US-IW-04", "RATE-STRATEGIC", "成功時BLUE方向+1", "page 56", "FRAG-ENABLER-0830-1-US-IW-04"),
    ("CHG-STRATEGIC-US-IW-05", "US-IW-05", "RATE-STRATEGIC", "成功時BLUE方向+1", "page 57", "FRAG-CAND-ENABLER-0830-1-US-IW-05"),
    ("CHG-STRATEGIC-STC-IW-03", "STC-IW-03", "RATE-STRATEGIC", "成功の都度RED方向+1", "page 61", "FRAG-CAND-ENABLER-0830-1-STC-IW-03"),
    ("CHG-STRATEGIC-STC-IW-04", "STC-IW-04", "RATE-STRATEGIC", "不利な1点変動を取消し、成功時RED方向+1", "page 62", "FRAG-ENABLER-0830-1-STC-IW-04"),
    ("CHG-STRATEGIC-CSG", "シナリオ1・2", "RATE-STRATEGIC", "US CSG撃破でPRC方向+3", "A3 pages 2-3", "FRAG-BOARD-A3-0915-P2-STRATEGIC-SCENARIO1 / FRAG-BOARD-A3-0915-P3-STRATEGIC-SCENARIO2"),
    ("CHG-STRATEGIC-CBG", "シナリオ1・2", "RATE-STRATEGIC", "PRC CBG撃破でUS方向+2", "A3 pages 2-3", "FRAG-BOARD-A3-0915-P2-STRATEGIC-SCENARIO1 / FRAG-BOARD-A3-0915-P3-STRATEGIC-SCENARIO2"),
    ("CHG-STRATEGIC-SQUADRON-SAG", "シナリオ1・2", "RATE-STRATEGIC", "スコードロンプレート又はSAG撃破で達成側+1", "A3 pages 2-3", "FRAG-BOARD-A3-0915-P2-STRATEGIC-SCENARIO1 / FRAG-BOARD-A3-0915-P3-STRATEGIC-SCENARIO2"),
    ("CHG-STRATEGIC-S1-CONTROL", "シナリオ1", "RATE-STRATEGIC", "ATO終了時の単独水上部隊存在で該当側+2", "A3 page 2", "FRAG-BOARD-A3-0915-P2-STRATEGIC-SCENARIO1"),
    ("CHG-STRATEGIC-S2-CONTROL", "シナリオ2", "RATE-STRATEGIC", "ATO終了時のPRC単独水上部隊存在でPRC方向+1", "A3 page 3", "FRAG-BOARD-A3-0915-P3-STRATEGIC-SCENARIO2"),
]

NON_CHANGES = [
    {"item": "Cyber Dominance", "classification": "source_rule", "finding": "サイバーレート4でATO終了した場合の派生効果であり、レート値自体を変更しない。"},
    {"item": "戦略レート更迭判定", "classification": "source_rule/component_data", "finding": "6+でATO終了した場合の終了判定であり、更迭がレートを変更するとは記載されない。"},
    {"item": "イニシアチブ／インテル", "classification": "source_rule", "finding": "宇宙・サイバーレートを参照する派生処理であり、レート値を変更しない。"},
]

QUESTIONS = [
    {
        "question_id": "Q-RATE-SPACE-LOWER-001", "rates": ["RATE-SPACE-US", "RATE-SPACE-PRC"],
        "situation": "宇宙レート0で、さらに低下させるカード効果が成立する。",
        "known": "正式ルールは宇宙レートを0から4までとし、カードは-1又は-2を指示する。",
        "unknown": "カードの合法性、判定・消費の有無、値、記録イベント。",
        "stops": "0未満を要求する宇宙カードの解決とrule vector期待結果。",
        "question": "宇宙レート0からさらに低下を要求した場合、カードの合法性、判定・使用状態、最終レート値及び記録すべき結果をどのように扱いますか。",
    },
    {
        "question_id": "Q-RATE-SPACE-UPPER-001", "rates": ["RATE-SPACE-US", "RATE-SPACE-PRC"],
        "situation": "宇宙レート4で、さらに上昇させるカード効果が成立する。",
        "known": "正式ルールは範囲を0から4とし、ボード端点は4+と印字する。カードには+1又は+2がある。",
        "unknown": "4+印字が超過値の蓄積を意味するか、カードの合法性、判定・消費、最終値、イベント。",
        "stops": "4を越える宇宙カードの解決とrule vector期待結果。",
        "question": "宇宙レート4からさらに上昇を要求した場合、4+の意味を含め、カードの合法性、判定・使用状態、最終レート値及び記録すべき結果をどのように扱いますか。",
    },
    {
        "question_id": "Q-RATE-CYBER-LOWER-001", "rates": ["RATE-CYBER-US", "RATE-CYBER-PRC"],
        "situation": "サイバーレート0で、さらに低下させる効果が成立する。STC-CY-05では直前の上昇取消し後に追加-1が生じ得る。",
        "known": "正式ルールはサイバーレートを0から4までとし、カードは-1を指示する。",
        "unknown": "カードの合法性、判定・消費、取消し部分と追加低下部分の扱い、最終値、イベント。",
        "stops": "0未満を要求するサイバー効果の解決とrule vector期待結果。",
        "question": "サイバーレート0からさらに低下を要求した場合、STC-CY-05の二段階効果を含め、カードの合法性、使用状態、最終レート値及び記録すべき結果をどのように扱いますか。",
    },
    {
        "question_id": "Q-RATE-CYBER-UPPER-001", "rates": ["RATE-CYBER-US", "RATE-CYBER-PRC"],
        "situation": "サイバーレート4で、さらに上昇判定を行うカードを使用しようとする。",
        "known": "3から4への閾値は明記されるが、4から上の閾値はない。4でATO終了するとサイバードミナンスとなる。",
        "unknown": "カードが合法候補か、判定を行うか、使用状態、最終値、4+印字の意味、イベント。",
        "stops": "4でのサイバー上昇カードの合法性及び解決。",
        "question": "サイバーレート4で上昇カードを使用しようとした場合、候補提示、判定、カードの使用状態、最終レート値及び記録すべき結果をどのように扱いますか。",
    },
    {
        "question_id": "Q-RATE-STRATEGIC-SAME-DIRECTION-001", "rates": ["RATE-STRATEGIC"],
        "situation": "戦略レートが既に一方の6+にあり、ATO終了前に同方向の+1、+2又は+3が発生する。",
        "known": "6+は印字端点で、ATO終了時に更迭・ゲーム終了となる。変更効果の方向と量は明記される。",
        "unknown": "6を越える量を内部的に保持するか、6+に留めるか、変更が成立するか、イベント。",
        "stops": "6+到達後の同方向変更と、その後の反対方向変更の基準値。",
        "question": "戦略レート6+で同方向の追加変更が発生した場合、変更の成立、保持する値及び記録すべき結果をどのように扱いますか。",
    },
    {
        "question_id": "Q-RATE-STRATEGIC-OPPOSITE-DIRECTION-001", "rates": ["RATE-STRATEGIC"],
        "situation": "戦略レートが6+にある間に、反対方向への変更が発生する。",
        "known": "通常の中間値では反対方向の1点変更が中央へ戻すことは承認済みvectorで確認されている。6+は値の上限表示でもある。",
        "unknown": "6+から1点戻すと5になるか、超過量を保持して6+のままか、別処理か。",
        "stops": "6+から反対方向へ動く場合の最終値とイベント。",
        "question": "戦略レート6+から反対方向への変更が発生した場合、変更量ごとの最終レート値及び記録すべき結果をどのように扱いますか。",
    },
]

FRAGMENT_CANDIDATES = [
    {"fragment_id": "FRAG-RULE-0910-2-PDF-P15-RATES", "disposition": "reuse_existing", "source_id": "SRC-RULE-0910-2-PDF", "locator": "page 15, section 1.5", "covers": ["ranges", "cyber_dominance", "strategic_6_plus_end"], "comparison": "DOCX paragraphs 369-405 and PDF page 15 exact semantic match"},
    {"fragment_id": "FRAG-BOARD-A3-0915-P1-RATE-BOARDS", "disposition": "reuse_existing", "source_id": "SRC-BOARD-A3-0915", "locator": "page 1", "covers": ["space/cyber printed endpoints", "cyber thresholds"], "comparison": "visual review confirmed 0,1,2,3,4+"},
    {"fragment_id": "FRAG-BOARD-A3-0915-P2-STRATEGIC-SCENARIO1", "disposition": "reuse_existing", "source_id": "SRC-BOARD-A3-0915", "locator": "page 2", "covers": ["scenario 1 changes", "both 6+ endpoints"]},
    {"fragment_id": "FRAG-BOARD-A3-0915-P3-STRATEGIC-SCENARIO2", "disposition": "reuse_existing", "source_id": "SRC-BOARD-A3-0915", "locator": "page 3", "covers": ["scenario 2 changes", "both 6+ endpoints"]},
]
for change in CHANGES:
    if change[5].startswith("FRAG-CAND-"):
        FRAGMENT_CANDIDATES.append({
            "fragment_id": change[5], "disposition": "candidate_not_registered", "source_id": "SRC-ENABLER-0830-1",
            "locator": change[4], "printed_code": change[1], "normalized_transcription": change[3],
            "verification": "Pass 1 PDF text extraction; Pass 2 rendered card visual review; semantic match",
        })


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aggregate(path: Path) -> str:
    if path.is_file():
        return sha256_file(path)
    lines = []
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = item.relative_to(ROOT).as_posix()
        lines.append(f"{rel}\t{sha256_file(item)}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def build_review() -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "document_type": "non_normative_owner_review",
        "generated_at": GENERATED_AT,
        "normative_authority": False,
        "issue_id": "ISSUE-RATE-BOUNDARY-013",
        "scope": "Rate boundary research only; no Rule Core or Digital behavior is established by this artifact.",
        "sources": SOURCES,
        "visual_review_evidence": VISUAL_REVIEW,
        "independent_review": {
            "pass_1": {"method": "DOCX/PDF text extraction and structured Rule Core inventory", "result": "ranges, effects, and locators extracted"},
            "pass_2": {"method": "fresh visual review of published rule PDF, A3 board pages 1-3, and 15 enabler card pages", "result": "numbers, symbols, printed endpoints, and card operations matched Pass 1"},
            "difference": "none in the reviewed scope",
            "absence_finding": "No reviewed normative carrier states how to resolve a request beyond a printed/rule range.",
        },
        "rates": RATE_ROWS,
        "change_effects": [
            {"change_id": c[0], "carrier": c[1], "rate_ids": c[2], "operation": c[3], "locator": c[4], "fragment": c[5], "boundary_text": "not_stated"}
            for c in CHANGES
        ],
        "related_non_change_effects": NON_CHANGES,
        "classification_summary": {
            "source_rule": ["rate ranges", "initial values", "card/scenario change directions and amounts", "cyber dominance at 4", "strategic dismissal at 6+ at ATO end"],
            "component_data": ["space/cyber printed 0-4+ tracks", "strategic printed 0 and both 6+ endpoints", "scenario change tables"],
            "approved_decision": [],
            "not_stated": [q["unknown"] for q in QUESTIONS],
            "not_applicable": ["Cyber Dominance, initiative, intel, and dismissal are not themselves rate-change operations."],
            "unresolved_candidate": [q["question_id"] for q in QUESTIONS],
        },
        "existing_vector_review": {
            "approved_rate_vectors": 18,
            "middle_or_in_range_only": [
                "RV-RATE-CYBER-ZERO-TO-ONE-001", "RV-RATE-CYBER-INCREASE-AT-001",
                "RV-RATE-CYBER-TWO-TO-THREE-001", "RV-RATE-CYBER-THREE-TO-FOUR-001",
                "RV-RATE-STRATEGIC-SQUADRON-SCENARIO1-001", "RV-RATE-STRATEGIC-SQUADRON-SCENARIO2-001",
            ],
            "endpoint_inputs_without_crossing": ["RV-RATE-CYBER-DOMINANCE-001", "RV-RATE-STRATEGIC-DISMISSAL-001"],
            "beyond_boundary_vectors": [],
            "clamp_expected_vectors": [],
            "invalid_change_expected_vectors": [],
            "finding": "No approved vector establishes behavior for a change request beyond a boundary.",
        },
        "candidate_vectors_created": [],
        "candidate_vector_reason": "All six boundary outcomes require owner rulings; expected results cannot yet be derived uniquely.",
        "owner_questions": QUESTIONS,
        "answer_fields": {q["question_id"]: {"owner_answer": None, "answered_by": None, "answered_at": None} for q in QUESTIONS},
        "protected_fingerprints": PROTECTED,
    }


def render_owner_markdown(review: dict[str, Any]) -> str:
    out = [
        "# レート上下限処理 ルール所有者確認票", "",
        f"生成日: {GENERATED_AT}", "",
        "本確認票は規範正本ではありません。正式資料で確定できる事実と、追加裁定が必要な処理を分離した確認資料です。回答前にRule CoreやDigitalへ上下限処理を実装しません。", "",
        "## 結論", "",
        "正式資料から、宇宙・サイバーは0から4、共有戦略レートは中央0から両方向6+までであること、端点で生じるサイバードミナンスと更迭判定は確認できました。範囲外の変更要求について、clamp、無効、カードの合法性・消費、余剰保持、イベント記録はいずれも明記されていません。", "",
        "## レート別上下限一覧", "",
        "| Rate ID | 名称 | 初期値 | 最小 | 最大 | 端点効果 | 超過処理 |", "|---|---|---:|---:|---:|---|---|",
    ]
    for r in review["rates"]:
        out.append(f"| `{r['rate_id']}` | {r['name']} | {r['initial']} | {r['minimum']} | {r['maximum']} | {r['endpoint_effect']} | `{r['boundary_behavior']}` |")
    out += ["", "注: A3ボードの宇宙・サイバー端点は `4+` と印字されていますが、正式ルール本文は範囲を0から4としています。印字上の端点と、4を越える値の保持方法は別問題として扱います。", "", "## 変更効果別の境界処理一覧", "", "| 処理 | 担体 | 対象 | 方向・量 | 位置 | 境界時の明文 |", "|---|---|---|---|---|---|" ]
    for c in review["change_effects"]:
        out.append(f"| `{c['change_id']}` | {c['carrier']} | {c['rate_ids']} | {c['operation']} | {c['locator']} | `{c['boundary_text']}` |")
    out += ["", "Cyber Dominance、イニシアチブ、インテル、更迭はレートを参照して生じる処理であり、それ自体をレート変更として数えていません。", "", "## 既存vectorの確認", "", "承認済みレートvectorは18件です。0→1、1→2、2→3、3→4、戦略レートの中央横断、サイバーレート4でのATO終了判定、戦略レート6+でのATO終了判定は含まれます。4から上、0から下、又は戦略6+到達後の追加変更を入力とするvector、clamp又は変更無効を期待するvectorはありません。", "", "## ルール所有者への質問", ""]
    for i, q in enumerate(review["owner_questions"], 1):
        out += [
            f"### {i}. {q['question_id']}", "", f"**実際に起こる状況:** {q['situation']}", "",
            f"**現在の正式資料で分かること:** {q['known']}", "", f"**現在の正式資料では決まらないこと:** {q['unknown']}", "",
            f"**決めない場合に停止する処理:** {q['stops']}", "", f"**質問:** {q['question']}", "",
            "回答:", "", "回答者:", "", "回答日:", "",
        ]
    out += ["## 技術的な追跡情報", "", "- 既存issue: `ISSUE-RATE-BOUNDARY-013`", "- Pass 1: `ルール0910-2.docx` の段落94-120、369-405及びPDFテキスト抽出", "- Pass 2: `ルール0910-2.pdf` 15ページ、A3ボード1-3ページ、該当カード15ページの新規レンダリングによる視覚確認", "- Pass間差異: なし", "- 上下限candidate vector: 0件。期待結果が一意でないため未作成", ""]
    return "\n".join(out)


def render_report(review: dict[str, Any]) -> str:
    return "\n".join([
        "# レート上下限処理 分析報告", "", f"調査日: {GENERATED_AT}", "",
        "## 判定", "", "調査は完了しましたが、上下限超過処理は開始不能です。5 Rate IDの範囲と端点効果は確定でき、超過時の処理は6論点すべて `not_stated` かつ `unresolved_candidate` です。Digitalの現行動作は根拠に使用していません。", "",
        "## 二回確認", "", "Pass 1では編集元DOCXとPDFテキスト抽出から数値・変更効果を抽出しました。Pass 2では正式PDF、A3ボード、カード現物を新規レンダリングして数値、4+・6+、矢印、変更量を直接確認しました。確認範囲の意味差はありません。", "",
        "## 確定事項", "", "- US/PRC宇宙レート: 初期3、範囲0-4。A3端点表示は4+。", "- US/PRCサイバーレート: 初期1、範囲0-4。3→4までの上昇閾値が存在し、4でATO終了すると次ATO中Cyber Dominance。", "- 共有戦略レート: 初期0、US/PRC両方向1-6+。ATO終了時6+なら更迭・ゲーム終了。", "- カード15処理、シナリオ5処理の方向と変更量を棚卸し済み。", "- 端点から反対方向へ動く一般的な中間値処理は既存承認vectorにあるが、6+からの戻り値は未確定。", "",
        "## 未確定事項", "", "宇宙・サイバーの上下端、戦略6+の同方向追加、戦略6+から反対方向の計6論点です。カードが合法か、判定・消費を行うか、値をどう保持するか、どのEventを記録するかを正式資料だけでは確定できません。", "",
        "## candidate vector", "", "作成していません。裁定前に期待結果を置くと、clamp、変更無効、カード不適格、余剰保持のいずれかを推測することになるためです。", "",
        "## 保護確認", "", "規範rules/data、decisions、unresolved、承認済みvector、sources及びDigital本体は生成対象外です。", "",
    ])


def render_diff() -> str:
    return "\n".join([
        "# レート上下限処理 Rule Core最小差分案", "", "この文書は規範変更案ではなく、所有者回答後に必要となる変更箇所だけを示す非規範の作業案です。処理内容は記入していません。", "",
        "1. `governance/decisions.yaml`: 正式資料にない上下限処理について、所有者確定文を追加裁定として1件登録する。Rate種別ごとの枝を同じ裁定内で分離する。", "2. `data/rates.yaml`: 5 Rate IDの `boundary_behavior: not_stated` を、承認された合法性、判定、消費、値、余剰保持、Event処理の構造へ置換する。", "3. `rules/rates.md`: 既存range項目とは分離した境界処理項目を追加し、追加裁定だけを出典とする。新しいRule Core IDとdecision IDは所有者回答後に既存台帳を確認して採番する。", "4. `data/state-and-event-ids.yaml`: 既存の `EVENT-RATE-CHANGE-ATTEMPTED`、`EVENT-RATE-CHANGED`、`EVENT-RATE-UNCHANGED` だけで裁定を完全に表せるか確認する。表せない場合だけ新規Event IDを所有者確認対象にする。", "5. governance台帳: source fragmentは既存の範囲・端点fragmentを再利用し、裁定は資料に明文のない処理だけを補う。traceability、coverage、rule-id-registry、field-ownershipを最小同期する。", "6. rule vector: 裁定後に、宇宙下端・上端、サイバー下端・上端、戦略6+同方向・反対方向を最低限覆うcandidateを作成する。US/PRC対称性を用いる場合も、適用対称性を明記する。", "7. 生成物とDigital: owner承認済みvector後にのみ再生成・適合実装へ進む。", "",
    ])


def write_outputs() -> None:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    review = build_review()
    outputs = {
        "rate-boundary-owner-review.json": json.dumps(review, ensure_ascii=False, indent=2) + "\n",
        "rate-boundary-owner-review.md": render_owner_markdown(review),
        "rate-boundary-analysis-report.md": render_report(review),
        "rate-boundary-source-fragment-candidates.json": json.dumps({"generated_at": GENERATED_AT, "normative_authority": False, "sources": SOURCES, "visual_review_evidence": VISUAL_REVIEW, "candidates": FRAGMENT_CANDIDATES}, ensure_ascii=False, indent=2) + "\n",
        "rate-boundary-minimal-diff-proposal.md": render_diff(),
    }
    for name, content in outputs.items():
        (REVIEW_DIR / name).write_text(content, encoding="utf-8", newline="\n")


def validate() -> None:
    review = json.loads((REVIEW_DIR / "rate-boundary-owner-review.json").read_text(encoding="utf-8"))
    assert len(review["rates"]) == 5
    assert {r["rate_id"] for r in review["rates"]} == {"RATE-SPACE-US", "RATE-SPACE-PRC", "RATE-CYBER-US", "RATE-CYBER-PRC", "RATE-STRATEGIC"}
    assert len(review["change_effects"]) == 20
    assert len(review["owner_questions"]) == 6
    assert not review["candidate_vectors_created"]
    assert all(r["boundary_behavior"] == "not_stated" for r in review["rates"])
    rates = yaml.safe_load((ROOT / "rule-core/data/rates.yaml").read_text(encoding="utf-8"))
    assert {r["rate_id"] for r in rates["rates"]} == {r["rate_id"] for r in review["rates"]}
    unresolved = yaml.safe_load((ROOT / "rule-core/governance/unresolved.yaml").read_text(encoding="utf-8"))
    assert any(i["issue_id"] == "ISSUE-RATE-BOUNDARY-013" and i["status"] == "open" for i in unresolved["issues"])
    fragments = yaml.safe_load((ROOT / "rule-core/governance/source-fragment-register.yaml").read_text(encoding="utf-8"))["fragments"]
    fragment_ids = {f["fragment_id"] for f in fragments}
    for f in FRAGMENT_CANDIDATES:
        if f["disposition"] == "reuse_existing":
            assert f["fragment_id"] in fragment_ids
        else:
            assert f["fragment_id"] not in fragment_ids
    for source_id, source in SOURCES.items():
        path = ROOT / "sources" / source["filename"]
        assert path.exists() and sha256_file(path) == source["sha256"], source_id
    snapshot = yaml.safe_load((ROOT / "rule-core/governance/source-set-snapshots/source-set-2026-09-23-initial.yaml").read_text(encoding="utf-8"))
    source_register = yaml.safe_load((ROOT / "rule-core/governance/source-register.yaml").read_text(encoding="utf-8"))
    observed_by_id = {s["source_id"]: s for s in source_register["sources"]}
    assert len(snapshot["sources"]) == 20
    for item in snapshot["sources"]:
        registered = observed_by_id[item["source_id"]]
        source_path = ROOT / "sources" / registered["observed_filename"]
        assert source_path.exists() and sha256_file(source_path) == item["content_sha256"]
    for rel, expected in PROTECTED.items():
        actual = aggregate(ROOT / rel)
        assert actual == expected, f"protected fingerprint changed: {rel}: {actual}"
    print("RATE_BOUNDARY_REVIEW_OK rates=5 changes=20 questions=6 candidates=0")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        write_outputs()
    validate()


if __name__ == "__main__":
    main()
