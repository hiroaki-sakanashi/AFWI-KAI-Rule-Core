from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
VECTOR_FILES = {
    "md": ("md.yaml", 9),
    "immediate_enablers": ("immediate-enablers.yaml", 18),
    "intel": ("intel.yaml", 6),
    "cyber_dominance": ("cyber-dominance-candidates.yaml", 2),
}
OUTPUT_MD = RC / "generated/reviews/vrc-priority-vector-owner-review.md"
OUTPUT_JSON = RC / "generated/reviews/vrc-priority-vector-owner-review.json"

PROTECTED_HASHES = {
    "rule-core/tests/rule-vectors/md.yaml": "a386e3a6abb2a3b5af600bef26d3329a29d49870c0f0bbda266ce98e4f288791",
    "rule-core/tests/rule-vectors/immediate-enablers.yaml": "11f4b5fde7bfe2971e1f52613fef0f8d9f4fa2777c30e54f3a1f833f7b694fe1",
    "rule-core/tests/rule-vectors/intel.yaml": "5e12e9a47c04e0725acced8e6fd5df110dab088213a9a1e6470291b278be4381",
    "rule-core/tests/rule-vectors/cyber-dominance-candidates.yaml": "aa0f0810ff2f27683bf4ebbd16dad0ae4e5df21dc64e6c105f7c8f1ae05ef79e",
    "rule-core/tests/rule-vectors/emi.yaml": "ce3514a6052864c60a2e06f29238ca787acab904cfcfdb2e73585d2bb87eeb8a",
    "rule-core/tests/rule-vectors/emi-double-count-candidates.yaml": "bb42d910c43801113f57640b7f2e593e9e0fcdf36cf1c1f91b00d31eaa0f1dc1",
    "rule-core/tests/rule-vectors/rates.yaml": "6bf5abb54ce7412a57a02421919691595749167b4d75da3b50e460b7378f9846",
    "rule-core/governance/unresolved.yaml": "a5144703aa443c6ff2bb3f3c86f80eed5c195abd172861c300f20f57f08b3285",
    "rule-core/generated/vrc-priority-reference.md": "cbfb221418196a9e481d70f3905192343275e88d2e136ace18082f16c28a7aea",
    "rule-core/generated/digital/vrc-priority.json": "05e75beef9b76ed464edf228434acc8cbed452c5e2eb15622b45550643d949f0",
    "rule-core/generated/digital/vrc-priority-manifest.json": "f1dbcf11dc920dae1c05abcf395f701258d3c76e252d6ed086bc4b1151444c4d",
    "rule-core/generated/reviews/vrc-unresolved-candidates.md": "b61045ba102e1f3a9f2ca8e50778b6069959a81f64ff821b32a636e5ee304e5a",
}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(vector: dict) -> str:
    canonical = json.dumps(vector, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normative_payload_fingerprint(vector: dict) -> str:
    return fingerprint({key: value for key, value in vector.items() if key not in {"status", "approval"}})


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


def main() -> None:
    metadata = json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))
    schema = json.loads((RC / "schemas/vrc-priority-vector-owner-review.schema.json").read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(metadata),
        key=lambda item: list(item.path),
    )
    if errors:
        raise AssertionError(f"review JSON schema: {errors[0].message} at {list(errors[0].path)}")

    vectors = []
    domain_by_id = {}
    vector_by_id = {}
    for domain, (name, expected) in VECTOR_FILES.items():
        doc = load_yaml(RC / "tests/rule-vectors" / name)
        assert doc["status"] == "approved"
        assert len(doc["vectors"]) == expected
        for vector in doc["vectors"]:
            assert vector["status"] == "approved"
            assert vector["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-23"}
            vectors.append(vector)
            domain_by_id[vector["vector_id"]] = domain
            vector_by_id[vector["vector_id"]] = vector

    vector_ids = [x["vector_id"] for x in vectors]
    assert len(vectors) == 35
    assert len(vector_ids) == len(set(vector_ids))
    assert Counter(domain_by_id.values()) == Counter({
        "md": 9, "immediate_enablers": 18, "intel": 6, "cyber_dominance": 2,
    })

    reviews = metadata["reviews"]
    review_ids = [x["vector_id"] for x in reviews]
    assert len(reviews) == 35
    assert set(review_ids) == set(vector_ids)
    assert len(review_ids) == len(set(review_ids))
    assert metadata["approval"] == {"status": "approved", "approved_by": "ルール所有者", "approved_at": "2026-09-23"}
    assert all(x["status"] == "approved" for x in reviews)
    assert all(x["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-23"} for x in reviews)
    assert Counter(x["domain"] for x in reviews) == Counter({
        "md": 9, "immediate_enablers": 18, "intel": 6, "cyber_dominance": 2,
    })
    assert all(x["fingerprint_changed_from_baseline"] for x in reviews)
    assert all(
        (x["baseline_fingerprint_sha256"] != x["pre_generation_fingerprint_sha256"])
        == x["fingerprint_changed_from_baseline"]
        for x in reviews
    )
    assert all(x["fingerprint_changed_from_previous_generation"] for x in reviews)
    assert all(
        (x["previous_generation_fingerprint_sha256"] != x["pre_generation_fingerprint_sha256"])
        == x["fingerprint_changed_from_previous_generation"]
        for x in reviews
    )

    rules = {x["rule_core_id"]: x for x in load_yaml(RC / "governance/rule-id-registry.yaml")["rules"]}
    components = {x["component_id"]: x for x in load_yaml(RC / "governance/component-id-registry.yaml")["components"]}
    fragments = {x["fragment_id"]: x for x in load_yaml(RC / "governance/source-fragment-register.yaml")["fragments"]}
    state_events = load_yaml(RC / "data/state-and-event-ids.yaml")
    state_ids = {x["state_id"] for x in state_events["states"]}
    event_ids = {x["event_id"] for x in state_events["events"]}
    trace = {x["target_id"]: x for x in load_yaml(RC / "governance/traceability.yaml")["mappings"]}

    for review in reviews:
        vector = vector_by_id[review["vector_id"]]
        assert review["domain"] == domain_by_id[review["vector_id"]]
        assert review["pre_generation_fingerprint_sha256"] == fingerprint(vector)
        assert review["full_record_fingerprint_sha256"] == fingerprint(vector)
        assert review["normative_payload_fingerprint_sha256"] == normative_payload_fingerprint(vector)
        assert review["pre_approval_normative_payload_fingerprint_sha256"] == normative_payload_fingerprint(vector)
        assert review["pre_approval_full_record_fingerprint_sha256"] != fingerprint(vector)
        assert set(vector["rule_core_ids"]) <= set(rules)
        assert not any(rules[x]["status"] == "deprecated" for x in vector["rule_core_ids"])
        assert set(vector["source_fragment_ids"]) <= set(fragments)
        assert set(review["component_ids"]) <= set(components)
        assert set(review["state_ids"]) <= state_ids
        assert set(review["event_ids"]) <= event_ids
        assert collect_prefixed(vector["expected_events"], "EVENT-") <= event_ids
        assert review["vector_id"] in trace
        mapping = trace[review["vector_id"]]
        assert mapping["rule_vector_status"] == "approved"
        assert set(mapping["rule_core_ids"]) == set(vector["rule_core_ids"])
        assert set(mapping["source_fragment_ids"]) == set(vector["source_fragment_ids"])
        assert review["reviewability"] == "eligible_for_owner_review"
        assert not review["traceability_errors"]

    immediate_components = {
        "COMP-ENABLER-US-SP-03", "COMP-ENABLER-US-SP-04", "COMP-ENABLER-STC-CY-04",
        "COMP-ENABLER-STC-CY-05", "COMP-ENABLER-US-CY-03", "COMP-ENABLER-US-CY-05",
        "COMP-ENABLER-STC-NV-07", "COMP-ENABLER-STC-NV-08", "COMP-ENABLER-STC-RF-05",
    }
    immediate_reviews = [x for x in reviews if x["domain"] == "immediate_enablers"]
    assert {c for x in immediate_reviews for c in x["component_ids"]} == immediate_components
    assert Counter(c for x in immediate_reviews for c in x["component_ids"]) == Counter({c: 2 for c in immediate_components})
    assert sum("-TRIGGER-" in x["vector_id"] and "-NO-TRIGGER-" not in x["vector_id"] for x in immediate_reviews) == 9
    assert sum("-NO-TRIGGER-" in x["vector_id"] for x in immediate_reviews) == 9

    for vector_id in (
        "RV-INTEL-SQUADRON-SUCCESS-001",
        "RV-INTEL-FAILURE-CONSUMES-001",
    ):
        vector = vector_by_id[vector_id]
        assert vector["operation"]["target_type"] == "deployed_unacquired_squadron_plate"
        assert vector["operation"]["target_quantity"] == 1
        assert vector["operation"]["confirmation_cost"] == 1
        assert vector["initial_state"]["other_deployed_squadron_plates"] == "existing_state"
        assert vector["expected_final_state"]["other_deployed_squadron_plates"] == "existing_state"
        assert "selected_squadron_plate_acquired" in vector["expected_final_state"]
        assert "deployed_squadrons_acquired" not in vector["expected_final_state"]

    failure = vector_by_id["RV-INTEL-SQUADRON-FAILURE-001"]
    assert failure["operation"] == {
        "type": "confirm_intel_target",
        "target_type": "deployed_unacquired_squadron_plate",
        "target_quantity": 1,
        "confirmation_cost": 1,
    }
    assert failure["initial_state"]["confirmations_remaining"] == 1
    assert failure["fixed_randomness"] == {"D4": 2}
    assert failure["expected_events"] == [{
        "event_id": "EVENT-INTEL-ACQUISITION-FAILED",
        "record_only": True,
        "state_change": "none",
    }]
    assert failure["expected_final_state"] == {
        "confirmations_remaining": 0,
        "judged_squadron_plate_acquisition_state_change": "none",
        "judged_squadron_plate_reveal_state_change": "none",
        "judged_squadron_plate_visibility_change": "none",
        "all_squadron_plates_state_change": "none",
    }
    assert failure["expected_public_state"] == {
        "judged_squadron_plate_public_state_change": "none",
        "all_squadron_plates_public_state_change": "none",
        "visibility_change": "none",
    }
    failure_outcome = json.dumps({
        "events": failure["expected_events"],
        "final": failure["expected_final_state"],
        "public": failure["expected_public_state"],
    }, ensure_ascii=False, sort_keys=True)
    assert "target" not in failure_outcome.lower()
    assert "EVENT-COMPONENT-REVEALED" not in failure_outcome
    assert "EVENT-INTEL-ACQUISITION-SUCCEEDED" not in failure_outcome
    failure_review = next(x for x in reviews if x["vector_id"] == "RV-INTEL-SQUADRON-FAILURE-001")
    assert failure_review["target"] == "操作段階で選択する配備済み未捕捉スコードロンプレート1枚"
    assert failure_review["knowledge_visibility_effect"] == {
        "squadron_acquisition_state_change": "none",
        "squadron_public_state_change": "none",
        "visibility_change": "none",
        "all_squadron_plates_state_change": "none",
        "confirmations_remaining_change": -1,
    }

    cyber = vector_by_id["RV-RATE-CYBER-DOMINANCE-DETAIL-001"]
    star_change = cyber["operation"]["command_star_change"]
    assert star_change == {
        "operation": "decrease",
        "operator": "subtract",
        "amount": 10,
        "operand": "current_star_value",
        "fixed_target_value": "none",
        "preserves_other_reductions": True,
        "preserves_other_constraints": True,
    }
    assert cyber["expected_final_state"]["deployed_squadrons_acquired"] is True
    assert cyber["expected_final_state"]["other_star_reductions"] == "preserved"
    assert cyber["expected_final_state"]["other_star_constraints"] == "preserved"
    assert not any(key in star_change for key in ("set", "fixed_value", "target_value"))
    rate_rules = load_yaml(RC / "data/rates.yaml")["rate_rules"]
    dominance = next(x for x in rate_rules if x["rule_core_id"] == "RC-RATE-CYBER-DOMINANCE-001")
    star_effect = next(x for x in dominance["parameters"]["effects"] if x.get("target") == "opponent_usable_command_stars")
    assert star_effect["operation"] == "decrease"
    assert star_effect["operator"] == "subtract"
    assert star_effect["amount"] == 10
    assert star_effect["operand"] == "current_star_value"
    assert star_effect["fixed_target_value"] == "none"
    assert star_effect["preserves_other_reductions"] is True
    assert star_effect["preserves_other_constraints"] is True

    markdown = OUTPUT_MD.read_text(encoding="utf-8")
    headings = re.findall(r"^### \d+\. (RV-[A-Z0-9-]+) —", markdown, flags=re.MULTILINE)
    assert len(headings) == 35
    assert set(headings) == set(vector_ids)
    assert markdown.count("- [x] この記述で正しい") == 35
    assert markdown.count("- [ ] 修正が必要") == 35
    assert markdown.count("- [ ] 現時点では承認できない") == 35
    assert markdown.count("- 確認者：ルール所有者") == 35
    assert markdown.count("- 確認日：2026-09-23") == 35
    assert "公開範囲は `not_stated`" in markdown
    assert "同一タイミングに複数の即応が成立した場合の選択・解決順" in markdown
    assert "両陣営のインテル活動の実施順" in markdown
    assert "公開済み情報を再び隠さず、既知情報を忘れさせず、捕捉状態を自動解除しない" in markdown
    assert "最後の3点は新しい効果ではなく" in markdown
    assert "確認数1を消費し、選択した配備済み未捕捉スコードロンプレート1枚だけについて捕捉判定を行う" in markdown
    assert "相手の現在の★から10個を減らす" in markdown
    assert "固定値30への設定ではない" in markdown
    assert "スコードロンの捕捉状態・公開状態その他の状態は一切変更せず、確認可能数だけを1消費する" in markdown
    for forbidden in ("nested_response", "resume token", "parent ID", "Digital内部状態"):
        assert forbidden not in markdown

    for relative, digest in PROTECTED_HASHES.items():
        assert sha256(ROOT / relative) == digest, relative

    emi = load_yaml(RC / "tests/rule-vectors/emi.yaml")["vectors"]
    assert len(emi) == 6 and all(x["status"] == "approved" for x in emi)
    emi_candidates = load_yaml(RC / "tests/rule-vectors/emi-double-count-candidates.yaml")["vectors"]
    assert len(emi_candidates) == 3 and all(x["status"] == "candidate" for x in emi_candidates)
    rates = load_yaml(RC / "tests/rule-vectors/rates.yaml")["vectors"]
    assert len(rates) == 18 and all(x["status"] == "approved" for x in rates)

    source_register = load_yaml(RC / "governance/source-register.yaml")["sources"]
    snapshot = load_yaml(RC / "governance/source-set-snapshots/source-set-2026-09-23-initial.yaml")["sources"]
    snapshot_hashes = {x["source_id"]: x["content_sha256"] for x in snapshot}
    actual_hashes = {x["source_id"]: sha256(ROOT / x["relative_path"]) for x in source_register}
    assert len(actual_hashes) == 20
    assert actual_hashes == snapshot_hashes

    before_regeneration = {OUTPUT_MD: sha256(OUTPUT_MD), OUTPUT_JSON: sha256(OUTPUT_JSON)}
    subprocess.run([
        sys.executable,
        str(RC / "pipeline/generate-vrc-priority-vector-owner-review.py"),
        "--generated-at", metadata["generated_at"],
    ], cwd=ROOT, check=True)
    assert before_regeneration == {OUTPUT_MD: sha256(OUTPUT_MD), OUTPUT_JSON: sha256(OUTPUT_JSON)}

    metadata_after = json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))
    after_fingerprints = {
        x["vector_id"]: fingerprint(x)
        for _, (name, _) in VECTOR_FILES.items()
        for x in load_yaml(RC / "tests/rule-vectors" / name)["vectors"]
    }
    assert after_fingerprints == {
        x["vector_id"]: x["pre_generation_fingerprint_sha256"] for x in metadata_after["reviews"]
    }

    print("VRC_PRIORITY_OWNER_REVIEW_VALIDATION_OK")
    print("vectors=35 domains=9,18,6,2")
    print("eligible_for_owner_review=35 needs_traceability_correction=0")
    print("fingerprints_before_after_match=35")
    print("normative_payload_fingerprints_pre_approval_match=35")
    print("full_record_fingerprints_changed_for_approval=35")
    print("all_vectors_approved=true approvals_recorded=35")
    print("emi_vectors_unchanged=9 rates_vectors_unchanged=18")
    print("unresolved_unchanged=true sources_unchanged=20")
    print("review_generated_reproducible=true")


if __name__ == "__main__":
    main()
