from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml
from validation_scope import report_historical_snapshot_status

ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
NEW_CODES = ["US-AB-05", "US-EW-03", "US-AF-05", "US-AF-10", "US-IW-01", "US-IW-04", "US-IW-07", "STC-IW-01", "STC-IW-04"]
ALL_IMMEDIATE_CODES = ["US-SP-03", "US-SP-04", "STC-CY-04", "STC-CY-05", "US-CY-03", "US-CY-05", "STC-NV-07", "STC-NV-08", "STC-RF-05"] + NEW_CODES
RESPONSE_ORDER_APPROVED = {
    "RV-ENABLER-NV-BOTH-LEGAL-001", "RV-ENABLER-NV-ORDER-07-08-001", "RV-ENABLER-NV-ORDER-08-07-001",
    "RV-ENABLER-NV-TARGET-REMAINS-001", "RV-ENABLER-NV-TARGET-REMOVED-001", "RV-ENABLER-NV-TARGET-REMOVED-08-FIRST-001",
    "RV-ENABLER-CYBER-NO-DETERMINATION-INELIGIBLE-001", "RV-ENABLER-CYBER-US-CY-05-DAY1-INELIGIBLE-001",
    "RV-ENABLER-CYBER-US-CY-05-DAY2-INELIGIBLE-001", "RV-ENABLER-CYBER-US-CY-05-DAY3-CANCEL-001",
    "RV-ENABLER-US-AF-10-PASS-BEFORE-MD-001", "RV-ENABLER-US-AF-10-DECLARED-BEFORE-MD-001",
    "RV-ENABLER-US-EW-03-AFTER-RED-MD-001", "RV-ENABLER-US-AF-10-ADV-RESUMES-AFTER-MD-001",
}
HISTORICALLY_CHANGED = {"RV-ENABLER-US-AB-05-EFFECT-001", "RV-ENABLER-STC-IW-01-EFFECT-001"}
CANDIDATE_PRE = {"RV-ENABLER-STC-IW-01-EFFECT-001": "17095c51ea0906c15682c511b340bfea952b287de4cbd71b695d40d96aa22ae8"}
CORRECTED = "RV-ENABLER-US-AB-05-EFFECT-001"
PRE_CORRECTION_FP = "d5eccdf0ca9e1ba6bc646c885e690dac585e3c643d089878c8282ed8bb3159db"
POST_CORRECTION_FP = "424795d5612b7eef7775720680fcdfbc4fa969ec59a67fe24e78da7560a4c6ed"
FP_FIELDS = ["vector_id", "rule_core_ids", "component_id", "source_fragment_ids", "initial_state", "operation", "fixed_randomness", "expected_events", "expected_final_state", "duration", "visibility", "interaction_type"]
PROTECTED = {
    "governance/component-id-registry.yaml": "4f2caf4356a374b42d94e5914871ca18b640a20908657cd8fb109282953de982",
    "data/state-and-event-ids.yaml": "5009e86a4273ec7a92ed4ab5e691e723810215743aa83f293449b69287087fcd",
    "tests/rule-vectors/md.yaml": "32b39bdf4050f49ecf1c7947f3c6ca603a72654dbb45ca9684ed658c79e7306b",
    "tests/rule-vectors/immediate-enablers.yaml": "11f4b5fde7bfe2971e1f52613fef0f8d9f4fa2777c30e54f3a1f833f7b694fe1",
    "tests/rule-vectors/intel.yaml": "5e12e9a47c04e0725acced8e6fd5df110dab088213a9a1e6470291b278be4381",
    "tests/rule-vectors/cyber-dominance-candidates.yaml": "aa0f0810ff2f27683bf4ebbd16dad0ae4e5df21dc64e6c105f7c8f1ae05ef79e",
    "tests/rule-vectors/emi.yaml": "ce3514a6052864c60a2e06f29238ca787acab904cfcfdb2e73585d2bb87eeb8a",
    "tests/rule-vectors/emi-double-count-candidates.yaml": "bb42d910c43801113f57640b7f2e593e9e0fcdf36cf1c1f91b00d31eaa0f1dc1",
    "tests/rule-vectors/rates.yaml": "6bf5abb54ce7412a57a02421919691595749167b4d75da3b50e460b7378f9846",
    "data/emi-components.yaml": "22ba7a2358281c1818b291f64808aef273511f0b976dbefc6d157393977ff775",
    "rules/emi.md": "e77486851f2ff49ceda71e0105608bc1d415e3bd6918097e504d6e6daf205396",
    "generated/emi-components-reference.md": "67a64f39cdd1b1639403af96266242c39104e1086c364edfd1a1dc6fefc7ebeb",
    "generated/digital/emi.json": "fdcb94601f9a13afbb6800358ab87975329967bbf6d83efba8be904f1a9fb4d4",
    "governance/unresolved.yaml": "a5144703aa443c6ff2bb3f3c86f80eed5c195abd172861c300f20f57f08b3285",
}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(instance: Path, schema: Path) -> None:
    value = load_json(instance) if instance.suffix == ".json" else load_yaml(instance)
    jsonschema.Draft202012Validator(load_json(schema), format_checker=jsonschema.FormatChecker()).validate(value)


def unique(values, label: str) -> set[str]:
    assert len(values) == len(set(values)), f"duplicate {label}"
    return set(values)


def component_id(vector: dict) -> str:
    return vector["operation"].get("component_id") or vector["initial_state"]["holder_has_component"]


def fingerprint(vector: dict) -> str:
    payload = {key: (component_id(vector) if key == "component_id" else vector.get(key)) for key in FP_FIELDS}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    validations = [
        ("data/enablers.yaml", "schemas/enablers.schema.json"),
        ("tests/rule-vectors/immediate-enablers-expansion.yaml", "schemas/rule-vector.schema.json"),
        ("governance/source-fragment-register.yaml", "schemas/source-fragment-register.schema.json"),
        ("governance/component-id-registry.yaml", "schemas/component-id-registry.schema.json"),
        ("governance/coverage.yaml", "schemas/coverage.schema.json"),
        ("governance/traceability.yaml", "schemas/traceability.schema.json"),
        ("governance/rule-id-registry.yaml", "schemas/rule-id-registry.schema.json"),
        ("governance/field-ownership.yaml", "schemas/field-ownership.schema.json"),
        ("generated/reviews/immediate-enablers-expansion-owner-review.json", "schemas/immediate-enablers-expansion-owner-review.schema.json"),
        ("generated/digital/immediate-enablers-expansion.json", "schemas/immediate-enablers-expansion-digital-contract.schema.json"),
        ("generated/digital/immediate-enablers-expansion-manifest.json", "schemas/generated-manifest.schema.json"),
        ("generated/digital/emi-manifest.json", "schemas/generated-manifest.schema.json"),
    ]
    for instance, schema in validations:
        validate(RC / instance, RC / schema)

    data = load_yaml(RC / "data/enablers.yaml")
    vectors_doc = load_yaml(RC / "tests/rule-vectors/immediate-enablers-expansion.yaml")
    fragments_doc = load_yaml(RC / "governance/source-fragment-register.yaml")
    components_doc = load_yaml(RC / "governance/component-id-registry.yaml")
    trace = load_yaml(RC / "governance/traceability.yaml")
    registry = load_yaml(RC / "governance/rule-id-registry.yaml")
    states = load_yaml(RC / "data/state-and-event-ids.yaml")
    source_register = load_yaml(RC / "governance/source-register.yaml")
    snapshot = load_yaml(RC / "governance/source-set-snapshots/source-set-2026-09-23-initial.yaml")
    review = load_json(RC / "generated/reviews/immediate-enablers-expansion-owner-review.json")
    digital = load_json(RC / "generated/digital/immediate-enablers-expansion.json")

    fragment_ids = unique([x["fragment_id"] for x in fragments_doc["fragments"]], "fragment IDs")
    component_ids = unique([x["component_id"] for x in components_doc["components"]], "component IDs")
    rule_ids = unique([x["rule_core_id"] for x in registry["rules"]], "rule IDs")
    state_ids = unique([x["state_id"] for x in states["states"]], "state IDs")
    event_ids = unique([x["event_id"] for x in states["events"]], "event IDs")
    unique([x["source_id"] for x in source_register["sources"]], "source IDs")
    vector_ids = unique([x["vector_id"] for x in vectors_doc["vectors"]], "new vector IDs")
    trace_by_id = {x["target_id"]: x for x in trace["mappings"]}
    assert len(trace_by_id) == len(trace["mappings"])

    new_cards = [x for x in data["components"] if x["source_card_code"] in NEW_CODES]
    immediate_cards = [x for x in data["components"] if x["source_card_code"] in ALL_IMMEDIATE_CODES]
    assert data["status"] == "reviewed"
    assert len(new_cards) == 9 and len(immediate_cards) == 18
    assert all(x["status"] == "reviewed" for x in immediate_cards)
    assert {x["component_id"] for x in new_cards} == {f"COMP-ENABLER-{x}" for x in NEW_CODES}
    assert vectors_doc["status"] == "approved" and len(vectors_doc["vectors"]) == 29
    approved = [x for x in vectors_doc["vectors"] if x["status"] == "approved"]
    candidates = [x for x in vectors_doc["vectors"] if x["status"] == "candidate"]
    assert len(approved) == 29 and not candidates
    assert all(x["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-24"} for x in approved)
    us_geo = next(x for x in approved if x["vector_id"] == "RV-ENABLER-US-IW-01-EFFECT-001")
    assert us_geo["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-24"}
    assert fingerprint(us_geo) == "c9f4b9ef3d92a130db7ceb7f77fb5036b252756ea8f98e65400b69dc2ca384a1"
    stc_geo = next(x for x in approved if x["vector_id"] == "RV-ENABLER-STC-IW-01-EFFECT-001")
    assert "blocked_by_geography" not in stc_geo["rights_scope"]
    assert len(stc_geo["expected_final_state"]["eligible_hex_ids"]) == 51
    assert fingerprint(stc_geo) == "b7f72ae600a3792b923bbb5fe93000cb4222a697b695cd0d7fd645a3b4c93056"

    corrected = next(x for x in vectors_doc["vectors"] if x["vector_id"] == CORRECTED)
    assert corrected["initial_state"] == {"holder_has_component": "COMP-ENABLER-US-AB-05", "RED_ground_attack_hit_roll": "success", "damage_roll": "not_started", "damage_hits": "not_determined"}
    assert corrected["expected_final_state"]["effective_hits_from_triggering_attack"] == 0
    assert "triggering_attack_hits" not in json.dumps(corrected, ensure_ascii=False)
    assert fingerprint(corrected) == POST_CORRECTION_FP

    assert review["approved_count"] == 29 and review["geography_reviewable_count"] == 0 and review["geography_blocked_count"] == 0
    assert review["approval_record"]["approved_by"] == "ルール所有者" and review["approval_record"]["approved_at"] == "2026-09-24"
    assert review["approval_record"]["approved_vector_count"] == 29 and review["approval_record"]["candidate_vector_count"] == 0
    assert review["approval_record"]["geography_approval"]["normative_payload_fingerprint_before"] == review["approval_record"]["geography_approval"]["normative_payload_fingerprint_after"] == "b7f72ae600a3792b923bbb5fe93000cb4222a697b695cd0d7fd645a3b4c93056"
    assert {x["vector_id"] for x in review["vectors"]} == vector_ids
    for item in review["vectors"]:
        source = next(x for x in vectors_doc["vectors"] if x["vector_id"] == item["vector_id"])
        current = fingerprint(source)
        assert item["fingerprint_sha256"] == current
        assert item["fingerprint_changed"] == (item["vector_id"] in HISTORICALLY_CHANGED)
        expected_pre = PRE_CORRECTION_FP if item["vector_id"] == CORRECTED else (CANDIDATE_PRE[item["vector_id"]] if item["vector_id"] == "RV-ENABLER-STC-IW-01-EFFECT-001" else current)
        assert item["pre_approval_fingerprint_sha256"] == expected_pre

    assert set(digital["componentIds"]) == {x["component_id"] for x in new_cards}
    assert set(digital["approvedVectorIds"]) == {x["vector_id"] for x in approved}
    assert not digital["candidateVectorIds"]
    assert {x["vector_id"] for x in digital["vectors"]} == vector_ids

    for card in new_cards:
        assert card["component_id"] in component_ids and card["component_id"] in trace_by_id
        assert set(card["source_fragment_ids"]) <= fragment_ids
        assert set(card["rule_core_ids"]) <= rule_ids
    for vector in vectors_doc["vectors"]:
        assert set(vector["source_fragment_ids"]) <= fragment_ids
        assert set(vector["rule_core_ids"]) <= rule_ids
        assert trace_by_id[vector["vector_id"]]["rule_vector_status"] == vector["status"]
        nested = json.dumps(vector, ensure_ascii=False)
        for prefix, known in [("STATE-", state_ids), ("EVENT-", event_ids), ("COMP-", component_ids)]:
            for token in nested.replace('"', " ").replace(",", " ").replace(":", " ").split():
                if token.startswith(prefix):
                    assert token in known, f"unknown reference {token}"
    assert not any(x.get("status") == "deprecated" and x["rule_core_id"] in json.dumps(vectors_doc, ensure_ascii=False) for x in registry["rules"])

    enabler_rule = next(x for x in registry["rules"] if x["rule_core_id"] == "RC-ENABLER-IMMEDIATE-001")
    coverage = enabler_rule["rule_vector_coverage"]
    assert set(coverage["approved_vector_ids"]) >= {x["vector_id"] for x in approved}
    assert not coverage["candidate_vector_ids"]
    assert RESPONSE_ORDER_APPROVED <= set(coverage["approved_vector_ids"])

    source_by_id = {x["source_id"]: x for x in source_register["sources"]}
    assert len(snapshot["sources"]) == 20
    for item in snapshot["sources"]:
        source = source_by_id[item["source_id"]]
        path = ROOT / source["relative_path"]
        assert sha(path) == item["content_sha256"] == source["content_sha256"]
    report_historical_snapshot_status(RC, PROTECTED, "immediate-enablers-expansion")

    md_path = RC / "generated/reviews/immediate-enablers-expansion-owner-review.md"
    md = md_path.read_text(encoding="utf-8")
    assert "3hit" not in md and "hit数はまだ決まっていません" in md and "有効なhit数は0" in md
    assert "ダメージロールは開始されません" not in md
    for code in NEW_CODES:
        assert code in md
    for vector_id in vector_ids:
        assert md.count(f"`{vector_id}`") == 1
    for heading in ["**最初の状態**", "**プレイヤーが行うこと**", "**固定するダイス目**", "**期待される処理**", "**処理後の状態**", "**このケースで確認しないこと**", "**回答欄**"]:
        assert md.count(heading) == 29
    assert md.count("[x] この記述で正しい") == 29

    manifest = load_json(RC / "generated/digital/immediate-enablers-expansion-manifest.json")
    for artifact in manifest["artifacts"]:
        assert sha(ROOT / artifact["path"]) == artifact["sha256"], artifact["path"]
    emi_manifest = load_json(RC / "generated/digital/emi-manifest.json")
    for artifact in emi_manifest["artifacts"]:
        assert sha(ROOT / artifact["path"]) == artifact["sha256"], artifact["path"]

    generated = [RC / "generated/reviews/immediate-enablers-expansion-owner-review.md", RC / "generated/reviews/immediate-enablers-expansion-owner-review.json", RC / "generated/immediate-enablers-expansion-reference.md", RC / "generated/digital/immediate-enablers-expansion.json", RC / "generated/digital/immediate-enablers-expansion-manifest.json"]
    before = [sha(x) for x in generated]
    subprocess.run([sys.executable, str(RC / "pipeline/generate-immediate-enablers-expansion-artifacts.py")], check=True)
    middle = [sha(x) for x in generated]
    subprocess.run([sys.executable, str(RC / "pipeline/generate-immediate-enablers-expansion-artifacts.py")], check=True)
    after = [sha(x) for x in generated]
    assert before == middle == after

    print("PASS immediate enablers expansion approval")
    print("cards=18 structured=18 existing_approved=9 newly_transcribed_approved=9")
    print("new_vectors=29 approved=29 geography_pending=0")
    print(f"US-AB-05-effect fingerprint={PRE_CORRECTION_FP}->{POST_CORRECTION_FP}")
    print("sources20=unchanged unresolved=unchanged VRC35=unchanged EMI=normative-unchanged manifest-synced reproducible=yes")


if __name__ == "__main__":
    main()
