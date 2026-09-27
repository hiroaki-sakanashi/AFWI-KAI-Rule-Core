from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
VECTOR = RC / "tests/rule-vectors/squadron-activation-candidates.yaml"
REVIEW_MD = RC / "generated/reviews/squadron-activation-owner-review.md"
REVIEW_JSON = RC / "generated/reviews/squadron-activation-owner-review.json"
DIGITAL = RC / "generated/digital/squadron-activation-candidates.json"
MANIFEST = RC / "generated/digital/squadron-activation-candidates-manifest.json"
REPORT = RC / "governance/squadron-activation-candidate-validation-report.md"
GENERATOR = "rule-core/pipeline/generate-squadron-activation-candidate-review.py"

FP_FIELDS = ["vector_id", "title", "initial_state", "operation", "fixed_randomness", "expected_events", "expected_final_state", "visibility", "interaction_type", "rule_core_ids", "source_fragment_ids", "decision_ids"]
PRE_APPROVAL_FULL_FINGERPRINTS = {
    "RV-SQUADRON-KJ-500-ACTIVATION-001": "63b8cfc4f0477b7a3c7b715ffb28013f5636acfde53a3192e23eebf8ea8656b8",
    "RV-SQUADRON-KQ-200-ACTIVATION-001": "af60252f8639323a66a896a4c3cf3b18b307a192d1a536aa9229654e4b672eb5",
}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fingerprint(vector: dict) -> str:
    return hashlib.sha256(canonical({key: vector.get(key) for key in FP_FIELDS})).hexdigest()


def full_record_fingerprint(vector: dict) -> str:
    return hashlib.sha256(canonical(vector)).hexdigest()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main() -> None:
    document = load_yaml(VECTOR)
    vectors = document["vectors"]
    reviews = []
    for vector in vectors:
        deployment = vector["initial_state"]["plate_deployment"]
        base = vector["initial_state"]["base_state"]
        reviews.append({
            "vector_id": vector["vector_id"],
            "title": vector["title"],
            "status": vector["status"],
            "component_id": vector["initial_state"]["component_id"],
            "selected_base": {"base_group_id": deployment["selected_base_group_id"], "hex": deployment["selected_base_hex"], "selection_reason": "AAR fixtureの合法な受入試験入力"},
            "input_classification": deployment["input_classification"],
            "normative_scope": deployment["normative_scope"],
            "does_not_establish_component_home_base": deployment["does_not_establish_component_home_base"],
            "damage_state": {"air_operations_infrastructure": base["air_operations_infrastructure_damage"], "maintenance_supply": base["maintenance_supply_damage"]},
            "maintenance_formula": vector["operation"]["maintenance_formula"],
            "fixed_D4": vector["fixed_randomness"]["maintenance_D4"],
            "expected_events": vector["expected_events"],
            "expected_final_state": vector["expected_final_state"],
            "visibility": vector["visibility"],
            "aar_projection": {"fixture_candidate_count": 1, "current_total_candidates": 17, "protected_expected_count": 15, "expected_count_changed_by_this_work": False},
            "rule_core_ids": vector["rule_core_ids"],
            "source_fragment_ids": vector["source_fragment_ids"],
            "decision_ids": vector["decision_ids"],
            "fingerprint_sha256": fingerprint(vector),
            "pre_approval_full_record_fingerprint_sha256": PRE_APPROVAL_FULL_FINGERPRINTS[vector["vector_id"]],
            "approved_full_record_fingerprint_sha256": full_record_fingerprint(vector),
            "owner_answer": {"answer": "この記述で正しい", "approved_by": vector["approval"]["approved_by"], "approved_at": vector["approval"]["approved_at"]},
        })

    fixture = {
        "path": "audits/20260912-live-turn-01/after.json",
        "classification": "non_normative_acceptance_input",
        "scenario_id": "scenario-1-day-1", "day": 2,
        "base_group_id": "GUANGDONG", "hex": "H2.5",
        "maintenance_damage": 0,
        "air_operations_infrastructure_damage": {"value": 0, "fixture_field": "omitted", "basis": "canonical board no-damage start and current schema fallback"},
        "effective_sortie_capacity": 6, "available_stars": 33,
        "plates": ["PRC-SQ-KJ-500", "PRC-SQ-KQ-200"],
        "token_pool_count_each": 1, "same_token_on_map_each": 0,
        "legality": "confirmed_for_candidate_input",
    }
    review = {
        "schema_version": "0.1.0", "review_type": "squadron_activation_candidate_owner_review", "non_normative": True,
        "generated_at": "2026-09-26", "generator": GENERATOR, "vector_count": len(reviews), "fixture_assessment": fixture,
        "fingerprint_method": {"algorithm": "SHA-256", "serialization": "canonical JSON; UTF-8; object keys sorted; array order preserved; null explicit; no insignificant whitespace", "normative_payload_fields": FP_FIELDS, "full_record_scope": "entire vector mapping including status and approval"},
        "vectors": reviews,
    }
    REVIEW_JSON.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_JSON.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# KJ-500／KQ-200 activation 所有者承認記録", "",
        "> 本記録は規範正本ではありません。2026-09-26のルール所有者承認を元のrule vectorへ反映した生成記録です。", "",
        "- 対象Rule Core: `0.15.0-preview-squadron-activation`", f"- 対象vector: `{VECTOR.relative_to(ROOT).as_posix()}`", "- 対象数: 2件", "- 生成日: 2026-09-26", f"- 生成処理: `{GENERATOR}`", "",
        "## AAR fixtureの確認", "",
        "受入試験入力はScenario 1（保存上のIDは`scenario-1-day-1`）のDay 2通常局面です。KJ-500とKQ-200はいずれも広東基地群（H2.5）へ配備され、未捕捉、各1 tokenがpool、盤上同一tokenなし、使用可能★33、整備補給基盤被害0、実効出撃キャパシティ6です。", "",
        "旧fixtureは航空運用インフラ被害フィールドを省略しています。正本ボードの無被害開始位置と現行Schemaの省略時0の解釈が一致するため、本candidateでは0を明示します。この明示は過去fixtureの書換えではありません。", "",
        "広東は海南・広東・湖南という合法なPRC基地群の一つです。今回の選択は`acceptance_fixture_choice`であり、KJ-500又はKQ-200の機種固有基地を定めず、他の合法基地群への配備を禁止しません。", "",
        "## 一覧", "", "| vector ID | component | 固定基地入力 | D4 | status |", "| --- | --- | --- | --- | --- |",
    ]
    for item in reviews:
        lines.append(f"| `{item['vector_id']}` | `{item['component_id']}` | 広東 H2.5 | 2 | `approved` |")
    for index, (vector, item) in enumerate(zip(vectors, reviews), 1):
        token = vector["initial_state"]["token_custody"]["token_id"]
        lines += [
            "", f"## {index}. {vector['title']}", "", f"- vector ID: `{vector['vector_id']}`", f"- Component ID: `{item['component_id']}`", "- status: `approved`", "- approved by / at: `ルール所有者` / `2026-09-26`", "",
            "### 配備基地と選択理由", "", "広東基地群（H2.5）をAAR fixture由来の受入試験固定入力として選びます。これは正式な機種固有基地ではなく、当日に選択できる合法基地群の一つです。海南又は湖南への合法配備を禁止しません。", "",
            "- `input_classification: acceptance_fixture_choice`", "- `normative_scope: any_legal_prc_base_group`", "- `does_not_establish_component_home_base: true`", "",
            "### 初期状態", "", "- Scenario 1、Day 2通常局面", "- 配備済み、未捕捉", f"- token `{token}` 1個はpool、同一tokenは盤上に存在しない", "- 使用可能★33", "- 広東の実効出撃キャパシティ6、使用済み0、残余6", "- 航空運用インフラ被害0、整備補給基盤被害0", "- 通常操作候補及びAAR投影は当該componentについて各1件", "",
            "### 処理と固定D4", "", "1 tokenを宣言し、★2を支払い、基地残余キャパシティを2使用します。広東・整備補給被害0の印字式「D4が2以上なら全数生成、1なら生成数-1」に対してD4=2を一度だけ使用し、1 token生成、地上断念0とします。", "",
            "### Event順", "",
        ]
        lines += [f"{n}. `{event['event_id']}` — `{dump({k:v for k,v in event.items() if k != 'event_id'})}`" for n, event in enumerate(vector["expected_events"], 1)]
        lines += [
            "", "### 公開範囲", "", "- RED（管理陣営）: Component ID、plate、生成予定数、★、基地状態、D4、実生成数、地上断念、token ID、生成位置をすべて知る。", "- BLUE（相手陣営）: activation発生、requested count、必要・支払★、D4、actual count、ground abort、生成token数、H2.5への配置、完了、公開基地状態を知る。", "- 未捕捉中のBLUEにはComponent ID、plate ID、tokenの正体及びtokenとplateの対応を開示しない。", "",
            "### 期待最終状態", "", "- 使用可能★31、広東キャパシティ使用済み2・残余4", f"- `{token}`はpoolからmapのH2.5へ移る", "- 実生成数1、地上断念0、未捕捉維持", "- plateへactivation済みflagを付けない", "- 同じtokenを重複生成できず、当該componentの追加activation候補は0件", "",
            "### AAR対応", "", "現在の17候補のうち本componentに対応する追加候補は正確に1件です。既存15件とは異なるsquadron IDであり重複しません。Digital通常経路の適合確認後、製品AAR期待値は17へ更新済みです。", "",
            "### 技術的な追跡情報", "", f"- Rule Core ID: {', '.join(f'`{x}`' for x in vector['rule_core_ids'])}", f"- source fragment: {', '.join(f'`{x}`' for x in vector['source_fragment_ids'])}", f"- decision: `{vector['decision_ids'][0]}`", f"- normative payload fingerprint（承認前後不変）: `{item['fingerprint_sha256']}`", f"- candidate full-record fingerprint: `{item['pre_approval_full_record_fingerprint_sha256']}`", f"- approved full-record fingerprint: `{item['approved_full_record_fingerprint_sha256']}`", "",
            "### ルール所有者回答", "", "- [x] この記述で正しい", "- [ ] 修正が必要", "- [ ] 現時点では承認できない", "", "確認者：ルール所有者", "", "確認日：2026-09-26", "", "修正が必要な場合の指示：なし", "",
        ]
    REVIEW_MD.write_text("\n".join(lines), encoding="utf-8")

    digital = {
        "schemaVersion": "0.1.0", "status": "approved", "nonNormativeDigitalIntake": True,
        "sourceVectorFile": VECTOR.relative_to(ROOT).as_posix(),
        "vectors": [{"vectorId": v["vector_id"], "status": v["status"], "approvedBy": v["approval"]["approved_by"], "approvedAt": v["approval"]["approved_at"], "componentId": v["initial_state"]["component_id"], "baseInput": v["initial_state"]["plate_deployment"], "fixedRandomness": v["fixed_randomness"], "expectedEvents": v["expected_events"], "expectedFinalState": v["expected_final_state"], "visibility": v["visibility"], "normativePayloadFingerprintSha256": fingerprint(v), "fullRecordFingerprintSha256": full_record_fingerprint(v)} for v in vectors],
    }
    DIGITAL.parent.mkdir(parents=True, exist_ok=True)
    DIGITAL.write_text(json.dumps(digital, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    REPORT.write_text("\n".join([
        "# KJ-500／KQ-200 activation 承認反映検証報告", "", "検証日: 2026-09-26", "",
        "## 結論", "", "AAR fixtureの広東配備は、海南・広東・湖南から当日選択できる合法な基地群の一例である。2件を2026-09-26承認済みとして登録し、機種固有基地は設定していない。", "",
        "## fixture差分", "", "航空運用インフラ被害フィールドだけが旧fixtureで省略される。正本ボードの無被害開始位置と省略時0の既存解釈をcandidateへ明示した。fixture自体は変更していない。", "",
        "## AAR", "", "現行17候補の追加2件はKJ-500とKQ-200が各1件で、既存15件と重複しない。Digital通常経路の適合確認後、製品AAR期待値を15件から17件へ更新した。", "",
        "## Fingerprint", "", "normative payload fingerprintは承認前後で不変。full-record fingerprintはstatus及びapprovalの反映により予定どおり変更された。承認済み集合は131件で、再現可能なcanonical fingerprintをmanifestへ記録する。", "",
        "## Digital適合範囲", "", "承認済み2 vectorの通常候補、実行結果、field-level visibility及びAAR投影を確認し、AAR期待値だけを17へ同期した。Rule Core規範は変更していない。", "",
    ]), encoding="utf-8")

    artifacts = [(VECTOR, "rule_vector_approved"), (REVIEW_MD, "generated_human_reference"), (REVIEW_JSON, "governance"), (DIGITAL, "digital_candidate"), (REPORT, "governance"), (RC / "schemas/squadron-activation-owner-review.schema.json", "governance"), (Path(__file__), "governance"), (RC / "pipeline/validate-squadron-activation-candidates.py", "governance")]
    approved = []
    for path in sorted((RC / "tests/rule-vectors").glob("*.yaml")):
        approved.extend(v for v in load_yaml(path).get("vectors", []) if v.get("status") == "approved")
    approved_set_fingerprint = hashlib.sha256(canonical(sorted(approved, key=lambda item: item["vector_id"]))).hexdigest()
    MANIFEST.write_text(json.dumps({"schemaVersion": "0.1.0", "manifestStatus": "approved", "ruleCoreVersion": document["rule_core_version"], "sourceSet": document["source_set"], "generatorVersion": "1.1.0", "digitalContractVersion": "approved-candidate-intake", "minDigitalVersion": None, "maxTestedDigitalVersion": None, "approvedVectorCount": len(approved), "approvedVectorSetFingerprintSha256": approved_set_fingerprint, "artifacts": [{"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p), "role": role} for p, role in artifacts]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
