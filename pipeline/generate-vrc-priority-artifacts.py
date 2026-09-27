from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
HUMAN = RC / "generated" / "vrc-priority-reference.md"
DIGITAL = RC / "generated" / "digital" / "vrc-priority.json"
MANIFEST = RC / "generated" / "digital" / "vrc-priority-manifest.json"
VECTOR_PATHS = [
    RC / "tests/rule-vectors/md.yaml",
    RC / "tests/rule-vectors/immediate-enablers.yaml",
    RC / "tests/rule-vectors/intel.yaml",
    RC / "tests/rule-vectors/cyber-dominance-candidates.yaml",
]


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    enablers = load(RC / "data/enablers.yaml")
    ids = load(RC / "data/state-and-event-ids.yaml")
    vectors = [v for path in VECTOR_PATHS for v in load(path)["vectors"]]
    approved_vectors = [v for v in vectors if v["status"] == "approved"]
    candidate_vectors = [v for v in vectors if v["status"] == "candidate"]
    # VRC優先35件の既存生成物は、承認済み9枚だけを対象に固定する。
    # 追加candidate 9枚は専用のexpansion生成経路で扱い、既存集合へ混在させない。
    approved_enablers = [x for x in enablers["components"] if x["status"] == "reviewed"]
    component_ids = [x["component_id"] for x in approved_enablers]
    relevant_rules = {"RC-COMBAT-MD-001", "RC-COMBAT-MD-RESOLUTION-001", "RC-COMBAT-MD-LAYERED-001", "RC-COMBAT-MD-VISIBILITY-001", "RC-ENABLER-IMMEDIATE-001", "RC-INTEL-ACTIVITY-001", "RC-RATE-CYBER-DOMINANCE-001"}
    states = [x for x in ids["states"] if relevant_rules.intersection(x["rule_core_ids"])]
    events = [x for x in ids["events"] if relevant_rules.intersection(x["rule_core_ids"])]
    assignments = [
        {"ruleCoreId": "RC-COMBAT-MD-001", "interactionType": "response_window", "visibilityEffect": "RC-COMBAT-MD-VISIBILITY-001"},
        {"ruleCoreId": "RC-COMBAT-MD-RESOLUTION-001", "interactionType": "automatic_resolution", "visibilityEffect": "RC-COMBAT-MD-VISIBILITY-001"},
        {"ruleCoreId": "RC-COMBAT-MD-LAYERED-001", "interactionType": "response_window", "visibilityEffect": "RC-COMBAT-MD-VISIBILITY-001"},
        {"ruleCoreId": "RC-COMBAT-MD-LAYERED-001", "interactionType": "automatic_resolution", "visibilityEffect": "RC-COMBAT-MD-VISIBILITY-001"},
        {"ruleCoreId": "RC-COMBAT-MD-VISIBILITY-001", "interactionType": "not_applicable", "visibilityEffect": "DEC-COMBAT-MD-VISIBILITY-001"},
        {"ruleCoreId": "RC-ENABLER-IMMEDIATE-001", "interactionType": "response_window", "visibilityEffect": "not_stated"},
        {"ruleCoreId": "RC-INTEL-ACTIVITY-001", "interactionType": "sequential_action", "visibilityEffect": "public_on_reveal"},
        {"ruleCoreId": "RC-INTEL-ACTIVITY-001", "interactionType": "automatic_resolution", "visibilityEffect": "public_on_success"},
        {"ruleCoreId": "RC-RATE-CYBER-DOMINANCE-001", "interactionType": "automatic_resolution", "visibilityEffect": "public_during_next_ATO"},
    ]
    HUMAN.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# VRC優先5件 参照", "", "規範YAML・規範Markdown・未承認rule vectorから生成した非規範の確認用資料です。", "", "## 即応カード", ""]
    lines += [f"- `{x['component_id']}`（印字コード `{x['source_card_code']}`）— `{x['trigger']['timing']}` `{x['trigger']['condition']}`" for x in approved_enablers]
    lines += ["", "## State ID", ""] + [f"- `{x['state_id']}` — {x['name_ja']}" for x in states]
    lines += ["", "## Event ID", ""] + [f"- `{x['event_id']}` — {x['name_ja']}" for x in events]
    lines += ["", "## 承認済みrule vector", ""] + ([f"- `{x['vector_id']}` — {x['title']}" for x in approved_vectors] or ["- なし"])
    lines += ["", "## 未承認candidate rule vector", ""] + ([f"- `{x['vector_id']}` — {x['title']}" for x in candidate_vectors] or ["- なし"])
    HUMAN.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    payload = {
        "schemaVersion": "0.1.0",
        "artifactStatus": "candidate",
        "ruleCoreVersion": enablers["rule_core_version"],
        "sourceSet": enablers["source_set"],
        "componentIds": component_ids,
        "stateIds": [x["state_id"] for x in states],
        "eventIds": [x["event_id"] for x in events],
        "interactionAssignments": assignments,
        "components": approved_enablers,
        "approvedRuleVectorIds": [x["vector_id"] for x in approved_vectors],
        "candidateRuleVectorIds": [x["vector_id"] for x in candidate_vectors],
    }
    DIGITAL.parent.mkdir(parents=True, exist_ok=True)
    DIGITAL.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    artifacts = [
        ("rule-core/data/enablers.yaml", "normative_data"),
        ("rule-core/data/state-and-event-ids.yaml", "normative_data"),
        ("rule-core/rules/combat.md", "normative_rules"),
        ("rule-core/rules/enablers.md", "normative_rules"),
        ("rule-core/rules/detection-and-intel.md", "normative_rules"),
        ("rule-core/rules/interaction-and-visibility.md", "normative_rules"),
        ("rule-core/rules/rates.md", "normative_rules"),
        *[
            (
                str(path.relative_to(ROOT)).replace("\\", "/"),
                "rule_vector_candidate" if any(v["status"] == "candidate" for v in load(path)["vectors"]) else "rule_vector_approved",
            )
            for path in VECTOR_PATHS
        ],
        ("rule-core/generated/vrc-priority-reference.md", "generated_human_reference"),
        ("rule-core/generated/digital/vrc-priority.json", "digital_candidate"),
    ]
    manifest = {
        "schemaVersion": "0.1.0", "manifestStatus": "candidate",
        "ruleCoreVersion": enablers["rule_core_version"], "sourceSet": enablers["source_set"],
        "generatorVersion": "0.1.0-vrc-priority", "digitalContractVersion": "0.1.0-candidate",
        "minDigitalVersion": None, "maxTestedDigitalVersion": None,
        "artifacts": [{"path": p, "sha256": sha(ROOT / p), "role": role} for p, role in artifacts],
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
