from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
GENERATOR = "rule-core/pipeline/generate-immediate-response-order-artifacts.py"
VECTOR_PATH = RC / "tests/rule-vectors/immediate-response-order-candidates.yaml"
DATA_PATH = RC / "data/enablers.yaml"
DECISION_PATH = RC / "governance/decisions.yaml"
REVIEW_MD = RC / "generated/reviews/immediate-response-order-candidate-owner-review.md"
REVIEW_JSON = RC / "generated/reviews/immediate-response-order-candidate-owner-review.json"
REFERENCE_MD = RC / "generated/immediate-response-order-reference.md"
DIGITAL_JSON = RC / "generated/digital/immediate-response-order.json"
MANIFEST = RC / "generated/digital/immediate-response-order-manifest.json"
PRIOR_REVIEW_JSON = RC / "generated/reviews/immediate-response-order-owner-review.json"
PRIOR_REVIEW_MD = RC / "generated/reviews/immediate-response-order-owner-review.md"
ANALYSIS_REPORT = RC / "generated/reviews/immediate-response-order-analysis-report.md"

DECISION_IDS = [
    "DEC-ENABLER-NV-MULTIPLE-001",
    "DEC-ENABLER-CYBER-COUNTER-SCOPE-001",
    "DEC-ENABLER-US-AF-10-MD-TIMING-001",
]
COMPONENT_IDS = [
    "COMP-ENABLER-STC-NV-07", "COMP-ENABLER-STC-NV-08",
    "COMP-ENABLER-STC-CY-04", "COMP-ENABLER-US-CY-03", "COMP-ENABLER-US-CY-05",
    "COMP-ENABLER-US-AF-10", "COMP-ENABLER-US-EW-03",
]
FP_FIELDS = [
    "vector_id", "title", "initial_state", "operation", "fixed_randomness",
    "expected_events", "expected_final_state", "duration", "visibility",
    "interaction_type", "rule_core_ids", "source_fragment_ids", "decision_ids",
]

CASE_TEXT = {
    "RV-ENABLER-NV-BOTH-LEGAL-001": ("両カードの合法候補", "同じBLUE艦が両マーカーの条件を同じ移動終了で満たし、REDが両カードを手札に持ちます。", "REDにSTC-NV-07とSTC-NV-08の両方を合法候補として示し、順序選択を待ちます。", "両カードは未消費のままで、REDが順序を決めます。"),
    "RV-ENABLER-NV-ORDER-07-08-001": ("07→08の逐次解決", "両カードが合法で、対象BLUE艦は二つの攻撃後も残る耐久状態です。", "REDが07を選び、07の使用・攻撃を完了してから08を使用・解決します。", "解決順は07→08となり、両カードと両マーカーを各解決後に消費・除去します。"),
    "RV-ENABLER-NV-ORDER-08-07-001": ("08→07の逐次解決", "両カードが合法で、対象BLUE艦は二つの攻撃後も残る耐久状態です。", "REDが08を選び、08の使用・攻撃を完了してから07を使用・解決します。", "解決順は08→07となり、両カードと両マーカーを各解決後に消費・除去します。"),
    "RV-ENABLER-NV-TARGET-REMAINS-001": ("対象艦が残る場合", "STC-NV-07を先行、STC-NV-08を後続として選び、先行攻撃後も対象艦が残ります。", "先行攻撃を解決後、対象艦が存在することを再確認して後続カードを使用・解決します。", "後続攻撃を実行し、後続カードを消費し、後続マーカーを除去します。"),
    "RV-ENABLER-NV-TARGET-REMOVED-001": ("07先行で対象艦が除去された場合", "STC-NV-07を先行、STC-NV-08を後続として選び、07の攻撃により対象艦が除去される条件です。", "07を使用・解決した後に対象艦の存在を再確認し、存在しないため08を発動しません。", "07は使用済みで対応マーカーを除去し、08は未発動で手札、対応マーカーは盤上、使用回数は未消費、2回目の攻撃は不実行です。"),
    "RV-ENABLER-NV-TARGET-REMOVED-08-FIRST-001": ("08先行で対象艦が除去された場合", "STC-NV-08を先行、STC-NV-07を後続として選び、08の攻撃により対象艦が除去される条件です。", "08を使用・解決した後に対象艦の存在を再確認し、存在しないため07を発動しません。", "08は使用済みで対応マーカーを除去し、07は未発動で手札、対応マーカーは盤上、使用回数は未消費、2回目の攻撃は不実行です。"),
    "RV-ENABLER-CYBER-NO-DETERMINATION-INELIGIBLE-001": ("判定のないカードへの対抗不可", "相手のサイバー関連カードに判定がなく、対抗カードは未使用です。", "効果を生じない対抗カードを合法候補から除外します。", "カードは手札又は利用可能状態を維持し、使用回数を消費しません。"),
    "RV-ENABLER-CYBER-US-CY-05-DAY1-INELIGIBLE-001": ("Day1のミュトス", "Day1にミュトスがUS-CY-01を自動成功にし、STC-CY-04は未使用です。", "自動成功をDIS化できないため、サイバーカウンターメジャーを合法候補へ示しません。", "US-CY-01は自動成功のまま、STC-CY-04の使用回数は未消費です。"),
    "RV-ENABLER-CYBER-US-CY-05-DAY2-INELIGIBLE-001": ("Day2のミュトス", "Day2にミュトスがUS-CY-01を自動成功にし、STC-CY-04は未使用です。", "自動成功をDIS化できないため、サイバーカウンターメジャーを合法候補へ示しません。", "US-CY-01は自動成功のまま、STC-CY-04の使用回数は未消費です。"),
    "RV-ENABLER-CYBER-US-CY-05-DAY3-CANCEL-001": ("Day3以降のADV／DIS相殺", "Day3にミュトスがUS-CY-01判定へADVを与え、STC-CY-04を使用できます。", "同じ判定へのADVとDISを相殺し、固定出目3の通常D4を1個だけ採用します。", "判定方式は通常D4となり、STC-CY-04の使用回数を消費します。"),
    "RV-ENABLER-US-AF-10-PASS-BEFORE-MD-001": ("AF-10不使用後のMD判断", "BLUE航空機がADAを攻撃し、BLUEのUS-AF-10判断とREDのMD判断はいずれも未完了です。", "BLUEがUS-AF-10を使わないと確定した後、REDのMD判断機会を開始します。", "REDはUS-AF-10不使用を知り、攻撃判定は通常状態のままMDを判断します。"),
    "RV-ENABLER-US-AF-10-DECLARED-BEFORE-MD-001": ("AF-10宣言後のMD判断", "BLUE航空機がADAを攻撃し、BLUEはUS-AF-10を保持しています。", "BLUEがUS-AF-10を宣言してから、REDのMD判断機会を開始します。", "REDはUS-AF-10使用を知り、攻撃判定がADVであることを前提にMDを判断します。"),
    "RV-ENABLER-US-EW-03-AFTER-RED-MD-001": ("RED MD宣言後のUS-EW-03", "US-AF-10の判断は完了し、REDがMDを判断する段階です。BLUEはUS-EW-03を保持しています。", "REDがMDを宣言した直後、MDのD4判定前にBLUEへUS-EW-03の応答機会を与えます。", "MDは宣言済み、US-EW-03は合法候補、MDのD4は未開始です。"),
    "RV-ENABLER-US-AF-10-ADV-RESUMES-AFTER-MD-001": ("MD後のADV維持と攻撃復帰", "US-AF-10は使用済みで攻撃はADV、REDはMDを宣言し、攻撃は未終了です。", "MD値2に対しD4出目1でMD失敗を解決し、未解決の攻撃へ戻ります。", "攻撃は終了せず再開し、US-AF-10のADVを当該攻撃に維持します。"),
}

RESOLUTIONS = {
    "ANALYSIS-UNRESOLVED-NV-MULTIPLE-USE": "DEC-ENABLER-NV-MULTIPLE-001",
    "ANALYSIS-UNRESOLVED-NV-ORDER": "DEC-ENABLER-NV-MULTIPLE-001",
    "ANALYSIS-UNRESOLVED-NV-TARGET-CEASES": "DEC-ENABLER-NV-MULTIPLE-001",
    "ANALYSIS-UNRESOLVED-CYBER-INEFFECTIVE-PLAY": "DEC-ENABLER-CYBER-COUNTER-SCOPE-001",
    "ANALYSIS-UNRESOLVED-US-CY-05-TARGET": "DEC-ENABLER-CYBER-COUNTER-SCOPE-001",
    "ANALYSIS-UNRESOLVED-US-AF-10-MD-TIMING": "DEC-ENABLER-US-AF-10-MD-TIMING-001",
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


def update_prior_analysis(decisions_by_id: dict[str, dict]) -> None:
    prior = json.loads(PRIOR_REVIEW_JSON.read_text(encoding="utf-8"))
    for question in prior["owner_questions"]:
        decision_id = RESOLUTIONS[question["analysis_id"]]
        question["resolution_status"] = "resolved"
        question["decision_id"] = decision_id
        question["owner_response"] = {
            "approved_by": "ルール所有者",
            "approved_at": "2026-09-24",
            "decision_id": decision_id,
            "owner_final_text": decisions_by_id[decision_id]["owner_final_text"],
        }
    prior["resolution_summary"] = {
        "resolved_question_count": 6,
        "unresolved_question_count": 0,
        "decision_ids": DECISION_IDS,
        "approved_vector_count": 14,
        "candidate_vector_count": 0,
    }
    PRIOR_REVIEW_JSON.write_text(json.dumps(prior, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# 複数即応の選択権・優先順位・解決順　裁定反映記録", "",
        "> 本資料は非規範の確認記録です。規範正本は`governance/decisions.yaml`、`rules/enablers.md`及び`data/enablers.yaml`です。", "",
        "- 裁定者: ルール所有者", "- 裁定日: 2026-09-24", "- 前回の所有者確認質問: 6件", "- 解決済み: 6件", "- 未回答: 0件", "",
        "## 解決対応", "",
        "| 前回の分析項目 | 解決decision | 状態 |", "| --- | --- | --- |",
    ]
    for analysis_id, decision_id in RESOLUTIONS.items():
        lines.append(f"| `{analysis_id}` | `{decision_id}` | resolved |")
    lines += ["", "## 裁定後の確認結果", "", "裁定内容を検証する14件のrule vectorは、2026-09-24にルール所有者が記載内容どおり承認しました。一般的な全カード共通の優先順位規則は新設していません。", ""]
    PRIOR_REVIEW_MD.write_text("\n".join(lines), encoding="utf-8")

    report = [
        "# 複数即応順序 分析報告（裁定反映後）", "",
        "## 結論", "",
        "前回抽出した6件の所有者質問は、2026-09-24の3件の追加裁定で全件解決しました。", "",
        "- STC-NV-07／08: REDが両方を使用でき、順序を選び、1枚ずつ解決します。攻撃のヒット数の期待値は順序で変わりませんが、先行攻撃で対象艦を除去した場合、先行カードは使用済み、後続カードは未発動となるため、残るカードと兆候マーカーは選択順により変わり得ます。",
        "- サイバー対抗: 判定がなく効果を生じないカードは使用不可です。ミュトスへのサイバーカウンターメジャーはDay1・2で不可、Day3以降はADVとDISを相殺します。",
        "- US-AF-10／MD: AF-10判断、RED MD判断、US-EW-03応答、MD処理、未解決攻撃への復帰の順です。", "",
        "## 正式資料で既に確定していた部分", "",
        "即応の手札からの直接使用、カード固有trigger、兆候配置の敗者→勝者順、MD宣言後のカード応答、STC-CY-05判定へのUS-CY-03のDIS、戦略レート変更からSTC-IW-04への連鎖は従来どおりです。", "",
        "## 実装との境界", "",
        "Rule Coreが定めるのは判断待ち、逐次解決、対象再確認、MD後の未解決攻撃への復帰です。continuation、stack、resume token、parent ID等の内部方式は規範化していません。", "",
        "## 承認結果", "", "14件のrule vectorは2026-09-24にルール所有者が承認済みです。承認済み範囲を正本としてDigital response windowの適合試験対象を固定できます。", "",
    ]
    ANALYSIS_REPORT.write_text("\n".join(report), encoding="utf-8")


def main() -> None:
    vectors_doc = load_yaml(VECTOR_PATH)
    data = load_yaml(DATA_PATH)
    decisions_doc = load_yaml(DECISION_PATH)
    decisions_by_id = {item["decision_id"]: item for item in decisions_doc["decisions"]}
    vectors = vectors_doc["vectors"]
    components_by_id = {item["component_id"]: item for item in data["components"]}
    selected_components = [components_by_id[item] for item in COMPONENT_IDS]

    reviews = []
    for vector in vectors:
        branch, initial_jp, process_jp, final_jp = CASE_TEXT[vector["vector_id"]]
        reviews.append({
            "vector_id": vector["vector_id"], "title": vector["title"], "status": vector["status"], "branch": branch,
            "initial_state": vector["initial_state"], "operation": vector["operation"], "fixed_randomness": vector["fixed_randomness"],
            "expected_events": vector["expected_events"], "expected_final_state": vector["expected_final_state"], "visibility": vector["visibility"],
            "component_ids": collect_ids(vector, "COMP-"), "rule_core_ids": vector["rule_core_ids"],
            "source_fragment_ids": vector["source_fragment_ids"], "decision_ids": vector["decision_ids"],
            "fingerprint_sha256": fingerprint(vector), "owner_answer": {"answer": "この記述で正しい", "approved_by": vector["approval"]["approved_by"], "approved_at": vector["approval"]["approved_at"]},
            "_initial_jp": initial_jp, "_process_jp": process_jp, "_final_jp": final_jp,
        })

    review_json = {
        "schema_version": "0.1.0", "review_type": "immediate_response_order_candidate_owner_review", "non_normative": True,
        "generated_at": "2026-09-24", "generator": GENERATOR, "vector_count": len(reviews),
        "status_counts": {"candidate": sum(item["status"] == "candidate" for item in reviews), "approved": sum(item["status"] == "approved" for item in reviews)},
        "approval_record": {"approved_by": "ルール所有者", "approved_at": "2026-09-24", "approved_vector_count": 14},
        "fingerprint_method": {"algorithm": "SHA-256", "serialization": "canonical JSON; UTF-8; object keys sorted; array order preserved; null explicit; no insignificant whitespace", "fields": FP_FIELDS},
        "vectors": [{key: value for key, value in item.items() if not key.startswith("_")} for item in reviews],
    }
    REVIEW_JSON.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_JSON.write_text(json.dumps(review_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = [
        "# 複数即応の追加裁定 rule vector 承認用確認票", "",
        "> 本確認票は規範正本ではありません。2026-09-24のルール所有者承認を元のrule vectorへ反映した確認記録です。14件はすべてapprovedです。", "",
        "- Rule Core: `0.11.0-preview-vrc`", f"- 対象vector: `{VECTOR_PATH.relative_to(ROOT).as_posix()}`", "- 対象数: 14件", "- 生成日: 2026-09-24",
        f"- 生成処理: `{GENERATOR}`", "- 出典: 正式カードfragment、正式ルールfragment、2026-09-24承認済みdecision", "",
        "## STC-NV-07／STC-NV-08の順序選択で確認する点", "",
        "REDが使用・解決順を選びます。二つの潜水艦攻撃がBLUE艦へ与えるヒット数の期待値は順序で変わりません。ただし、1枚目の攻撃で対象艦が除去されると2枚目は未発動となるため、どちらのカードと兆候マーカーが残るかは選択順によって変わり、ゲーム状態に差異が生じ得ます。以下では07先行と08先行を別々の最終状態として確認します。", "",
        "## 一覧", "", "| vector ID | 分岐 | decision | status | 所有者回答 |", "| --- | --- | --- | --- | --- |",
    ]
    for item in reviews:
        md.append(f"| `{item['vector_id']}` | {item['branch']} | {', '.join(f'`{x}`' for x in item['decision_ids'])} | `approved` | この記述で正しい |")
    for index, item in enumerate(reviews, 1):
        random_text = "なし" if item["fixed_randomness"] == "none" else f"`{dump(item['fixed_randomness'])}`"
        md += [
            "", f"## {index}. {item['title']}", "", f"- vector ID: `{item['vector_id']}`", f"- 確認する分岐: {item['branch']}", "",
            "### 最初の状態", "", item["_initial_jp"], "", "### 判断主体と選択", "",
            ("REDプレイヤーが順序又は使用を判断します。" if "NV-" in item["vector_id"] else "カード保持陣営又はMD判断側が、裁定で定めた順序に従って判断します。"), "",
            "### 処理順", "", item["_process_jp"], "", "### 固定出目", "", random_text, "", "### 期待イベント", "",
        ]
        if item["expected_events"]:
            md += [f"- `{dump(event)}`" for event in item["expected_events"]]
        else:
            md.append("- なし。合法候補の除外又は状態維持だけを確認します。")
        md += ["", "### 期待最終状態", "", item["_final_jp"], "", "### 使用済み／未使用カード、マーカー、公開範囲", ""]
        md += [f"- `{dump(item['expected_final_state'])}`", f"- visibility: `{dump(item['visibility'])}`", "", "### 技術的な追跡情報", "",
               f"- Component ID: {', '.join(f'`{x}`' for x in item['component_ids']) or '該当なし'}",
               f"- Rule Core ID: {', '.join(f'`{x}`' for x in item['rule_core_ids'])}",
               f"- source fragment: {', '.join(f'`{x}`' for x in item['source_fragment_ids'])}",
               f"- decision ID: {', '.join(f'`{x}`' for x in item['decision_ids'])}",
               f"- fingerprint: `{item['fingerprint_sha256']}`", "", "### ルール所有者回答欄", "",
               "- [x] この記述で正しい", "- [ ] 修正が必要", "- [ ] 現時点では承認できない", "", "確認者：ルール所有者", "", "確認日：2026-09-24", "", "修正が必要な場合の指示：", ""]
    REVIEW_MD.write_text("\n".join(md), encoding="utf-8")

    ref = ["# 複数即応・連鎖処理 データ参照", "", "> 規範正本ではありません。承認済みdecisionと`data/enablers.yaml`から生成した人向け参照です。", ""]
    for decision_id in DECISION_IDS:
        decision = decisions_by_id[decision_id]
        ref += [f"## {decision_id}", "", decision["scope"], "", f"- 適用Component ID: {', '.join(f'`{x}`' for x in decision['applies_to_component_ids'])}", f"- 影響Rule Core ID: {', '.join(f'`{x}`' for x in decision['affected_rule_core_ids'])}", ""]
    REFERENCE_MD.write_text("\n".join(ref), encoding="utf-8")

    digital = {
        "schemaVersion": "0.1.0", "status": "candidate", "nonNormativeCandidate": True,
        "decisionIds": DECISION_IDS, "componentIds": COMPONENT_IDS,
        "approvedVectorIds": [item["vector_id"] for item in vectors], "candidateVectorIds": [],
        "components": selected_components, "vectors": vectors,
    }
    DIGITAL_JSON.parent.mkdir(parents=True, exist_ok=True)
    DIGITAL_JSON.write_text(json.dumps(digital, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    update_prior_analysis(decisions_by_id)

    manifest_inputs = [
        (DECISION_PATH, "governance"), (RC / "rules/enablers.md", "normative_rules"),
        (RC / "rules/interaction-and-visibility.md", "normative_rules"), (DATA_PATH, "normative_data"),
        (VECTOR_PATH, "rule_vector_candidate"), (RC / "governance/coverage.yaml", "governance"),
        (RC / "governance/traceability.yaml", "traceability"), (RC / "governance/rule-id-registry.yaml", "governance"),
        (RC / "governance/field-ownership.yaml", "governance"), (REFERENCE_MD, "generated_human_reference"),
        (DIGITAL_JSON, "digital_candidate"), (REVIEW_MD, "generated_human_reference"), (REVIEW_JSON, "governance"),
        (PRIOR_REVIEW_MD, "generated_human_reference"), (PRIOR_REVIEW_JSON, "governance"),
        (ANALYSIS_REPORT, "governance"),
    ]
    manifest = {
        "schemaVersion": "0.1.0", "manifestStatus": "candidate", "ruleCoreVersion": "0.11.0-preview-vrc",
        "sourceSet": "SRCSET-20260923-INITIAL", "generatorVersion": "1.0.0",
        "digitalContractVersion": "0.1.0", "minDigitalVersion": None, "maxTestedDigitalVersion": None,
        "artifacts": [{"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path), "role": role} for path, role in manifest_inputs],
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
