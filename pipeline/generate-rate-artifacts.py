from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RULE_CORE = ROOT / "rule-core"
RATES_SOURCE = RULE_CORE / "data" / "rates.yaml"
STATE_EVENT_SOURCE = RULE_CORE / "data" / "state-and-event-ids.yaml"
VECTORS_SOURCE = RULE_CORE / "tests" / "rule-vectors" / "rates.yaml"
BOUNDARY_VECTORS_SOURCE = RULE_CORE / "tests" / "rule-vectors" / "rate-boundary-candidates.yaml"
HUMAN_OUTPUT = RULE_CORE / "generated" / "rates-reference.md"
DIGITAL_OUTPUT = RULE_CORE / "generated" / "digital" / "rates.json"
MANIFEST_OUTPUT = RULE_CORE / "generated" / "digital" / "rates-manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display(value) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return str(value)


def main() -> None:
    subprocess.run(
        [sys.executable, str(RULE_CORE / "pipeline/generate-rate-boundary-candidate-review.py")],
        cwd=ROOT,
        check=True,
    )
    rates_doc = yaml.safe_load(RATES_SOURCE.read_text(encoding="utf-8"))
    ids_doc = yaml.safe_load(STATE_EVENT_SOURCE.read_text(encoding="utf-8"))
    vectors_doc = yaml.safe_load(VECTORS_SOURCE.read_text(encoding="utf-8"))
    boundary_vectors_doc = yaml.safe_load(BOUNDARY_VECTORS_SOURCE.read_text(encoding="utf-8"))
    all_vectors = vectors_doc["vectors"] + boundary_vectors_doc["vectors"]
    rates = rates_doc["rates"]
    rate_ids = [item["rate_id"] for item in rates]
    state_ids = [item["state_id"] for item in ids_doc["states"]]
    event_ids = [item["event_id"] for item in ids_doc["events"]]
    approved_vector_ids = [item["vector_id"] for item in all_vectors if item["status"] == "approved"]
    candidate_vector_ids = [item["vector_id"] for item in all_vectors if item["status"] == "candidate"]

    if len(rate_ids) != len(set(rate_ids)):
        raise ValueError("Duplicate rate IDs")
    if len(state_ids) != len(set(state_ids)) or len(event_ids) != len(set(event_ids)):
        raise ValueError("Duplicate state or event IDs")

    HUMAN_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# レート データ参照",
        "",
        "この文書は `rule-core/data/rates.yaml` と `rule-core/data/state-and-event-ids.yaml` から生成した人向け参照資料であり、独立した規範正本ではありません。",
        "",
        "| rate ID | 名称 | 保持主体 | 初期値 | 下限 | 上限／方向端 | 公開状態ID |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for rate in rates:
        bounds = rate["bounds"]
        upper = bounds.get("maximum_display", bounds.get("maximum", bounds.get("direction_limits")))
        lines.append(
            f"| `{rate['rate_id']}` | {rate['name_ja']} | {rate['holder']} | {display(rate['initial_value'])} | "
            f"{display(bounds.get('minimum'))} | {display(upper)} | `{rate['state_id']}` |"
        )
    lines.extend([
        "",
        "## Rule Core ID",
        "",
        *[f"- `{item['rule_core_id']}` — {item['type']}" for item in rates_doc["rate_rules"]],
        "",
        "## 公開状態ID",
        "",
        *[f"- `{item['state_id']}` — {item['name_ja']}" for item in ids_doc["states"]],
        "",
        "## Event ID",
        "",
        *[f"- `{item['event_id']}` — {item['name_ja']}" for item in ids_doc["events"]],
        "",
        "## 承認済みrule vector",
        "",
        *[f"- `{item['vector_id']}` — {item['title']}" for item in all_vectors if item["status"] == "approved"],
        "",
        "## 未承認rule vector候補",
        "",
        *([f"- `{item['vector_id']}` — {item['title']}" for item in all_vectors if item["status"] == "candidate"] or ["- なし"]),
        "",
        "範囲外変更は `DEC-RATE-BOUNDARY-001` と `RC-RATE-BOUNDARY-001` で確定し、境界20件は2026-09-25に承認済みです。カード固有の未収録増減、地理IDを要する分岐、二次元更送表の役職マッピングは引き続き収録範囲外です。",
        "",
    ])
    HUMAN_OUTPUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    digital = {
        "schemaVersion": "0.1.0",
        "digitalContractVersion": "0.1.0-candidate",
        "ruleCoreVersion": rates_doc["rule_core_version"],
        "sourceSet": rates_doc["source_set"],
        "artifactStatus": "candidate",
        "rateIds": rate_ids,
        "stateIds": state_ids,
        "eventIds": event_ids,
        "rates": rates,
        "rateRules": rates_doc["rate_rules"],
        "approvedRuleVectorIds": approved_vector_ids,
        "candidateRuleVectorIds": candidate_vector_ids,
        "candidateRuleVectors": [item for item in all_vectors if item["status"] == "candidate"],
    }
    DIGITAL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DIGITAL_OUTPUT.write_text(json.dumps(digital, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    artifacts = [
        ("rule-core/data/rates.yaml", "normative_data"),
        ("rule-core/data/state-and-event-ids.yaml", "normative_data"),
        ("rule-core/rules/rates.md", "normative_rules"),
        ("rule-core/tests/rule-vectors/rates.yaml", "rule_vector_approved"),
        ("rule-core/tests/rule-vectors/rate-boundary-candidates.yaml", "rule_vector_approved"),
        ("rule-core/governance/decisions.yaml", "governance"),
        ("rule-core/governance/field-ownership.yaml", "governance"),
        ("rule-core/governance/traceability.yaml", "traceability"),
        ("rule-core/governance/coverage.yaml", "governance"),
        ("rule-core/governance/rule-id-registry.yaml", "governance"),
        ("rule-core/governance/unresolved.yaml", "governance"),
        ("rule-core/governance/rate-prototype-validation-report.md", "governance"),
        ("rule-core/governance/rate-boundary-validation-report.md", "governance"),
        ("rule-core/generated/rates-reference.md", "generated_human_reference"),
        ("rule-core/generated/reviews/rates-vector-owner-review.md", "generated_human_reference"),
        ("rule-core/generated/reviews/rates-vector-owner-review.json", "generated_human_reference"),
        ("rule-core/generated/reviews/rate-boundary-candidate-owner-review.md", "generated_human_reference"),
        ("rule-core/generated/reviews/rate-boundary-candidate-owner-review.json", "generated_human_reference"),
        ("rule-core/generated/digital/rates.json", "digital_candidate"),
    ]
    manifest = {
        "schemaVersion": "0.1.0",
        "manifestStatus": "candidate",
        "ruleCoreVersion": rates_doc["rule_core_version"],
        "sourceSet": rates_doc["source_set"],
        "generatorVersion": "0.3.0-rate-boundary",
        "digitalContractVersion": "0.1.0-candidate",
        "minDigitalVersion": None,
        "maxTestedDigitalVersion": None,
        "artifacts": [
            {"path": path, "sha256": sha256(ROOT / path), "role": role}
            for path, role in artifacts
        ],
    }
    MANIFEST_OUTPUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
