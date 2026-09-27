from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from collections import deque
from pathlib import Path

import jsonschema
import yaml
from PIL import Image
from validation_scope import report_historical_snapshot_status

ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
GENERATOR = RC / "pipeline" / "generate-geography-generation-boundaries.py"
ANCHORS = [
    "C5/C6", "D5.5/D6.5", "E6/E7", "F8.5/F9.5", "G8/G9", "H7.5/H8.5", "I7/I8",
    "J6.5/J7.5", "J6.5/K7", "J6.5/K6", "J6.5/J5.5", "I5/I6", "I5/H5.5", "I5/H4.5",
    "I4/I5", "J3.5/J4.5", "K4/K5", "L3.5/L4.5", "L3.5/M4", "L3.5/M3", "L2.5/M3",
    "L2.5/M2", "L1.5/L2.5", "K2/K3", "J1.5/J2.5", "I1/I2", "I1/H1.5",
]
PROTECTED = {
    "tests/rule-vectors/md.yaml": "32b39bdf4050f49ecf1c7947f3c6ca603a72654dbb45ca9684ed658c79e7306b",
    "tests/rule-vectors/immediate-enablers.yaml": "11f4b5fde7bfe2971e1f52613fef0f8d9f4fa2777c30e54f3a1f833f7b694fe1",
    "tests/rule-vectors/intel.yaml": "5e12e9a47c04e0725acced8e6fd5df110dab088213a9a1e6470291b278be4381",
    "tests/rule-vectors/cyber-dominance-candidates.yaml": "aa0f0810ff2f27683bf4ebbd16dad0ae4e5df21dc64e6c105f7c8f1ae05ef79e",
    "tests/rule-vectors/emi.yaml": "ce3514a6052864c60a2e06f29238ca787acab904cfcfdb2e73585d2bb87eeb8a",
    "tests/rule-vectors/emi-double-count-candidates.yaml": "bb42d910c43801113f57640b7f2e593e9e0fcdf36cf1c1f91b00d31eaa0f1dc1",
    "tests/rule-vectors/rates.yaml": "6bf5abb54ce7412a57a02421919691595749167b4d75da3b50e460b7378f9846",
    "governance/unresolved.yaml": "a5144703aa443c6ff2bb3f3c86f80eed5c195abd172861c300f20f57f08b3285",
}


def y(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def j(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def vector_fingerprint(value: dict) -> str:
    payload = {k: v for k, v in value.items() if k not in {"status", "approval", "rights_scope", "review_metadata"}}
    return hashlib.sha256(canonical(payload)).hexdigest()


def geography_fingerprint(value: dict) -> str:
    payload = {k: v for k, v in value.items() if k not in {"status", "approval", "notes"}}
    return hashlib.sha256(canonical(payload)).hexdigest()


def validate(instance: Path, schema: Path) -> None:
    value = j(instance) if instance.suffix == ".json" else y(instance)
    jsonschema.Draft202012Validator(j(schema)).validate(value)


def vertices(hex_id: str) -> set[tuple[float, float]]:
    row = ord(hex_id[0]) - ord("C")
    number = float(hex_id[1:])
    cx, cy = math.sqrt(3) * (number - 1), 1.5 * row
    return {(round(cx + math.cos(math.radians(-90 + 60 * i)), 6), round(cy + math.sin(math.radians(-90 + 60 * i)), 6)) for i in range(6)}


def edge_vertices(edge: str) -> set[tuple[float, float]]:
    a, b = edge.split("/")
    return vertices(a) & vertices(b)


def main() -> None:
    for instance, schema in [
        (RC / "data/geography.yaml", RC / "schemas/geography.schema.json"),
        (RC / "tests/rule-vectors/immediate-enablers-expansion.yaml", RC / "schemas/rule-vector.schema.json"),
        (RC / "governance/coverage.yaml", RC / "schemas/coverage.schema.json"),
        (RC / "governance/traceability.yaml", RC / "schemas/traceability.schema.json"),
        (RC / "governance/field-ownership.yaml", RC / "schemas/field-ownership.schema.json"),
        (RC / "generated/reviews/geography-generation-boundaries-owner-review.json", RC / "schemas/geography-generation-boundaries-owner-review.schema.json"),
    ]:
        validate(instance, schema)

    geo = y(RC / "data/geography.yaml")
    vectors_doc = y(RC / "tests/rule-vectors/immediate-enablers-expansion.yaml")
    fragments_doc = y(RC / "governance/source-fragment-register.yaml")
    trace = y(RC / "governance/traceability.yaml")
    review = j(RC / "generated/reviews/geography-generation-boundaries-owner-review.json")
    source_register = y(RC / "governance/source-register.yaml")
    snapshot = y(RC / "governance/source-set-snapshots/source-set-2026-09-23-initial.yaml")

    hex_ids = geo["hex_grid"]["hex_ids"]
    assert len(hex_ids) == len(set(hex_ids)) == geo["hex_grid"]["hex_count"] == 110
    hex_set = set(hex_ids)
    boundaries = {b["boundary_id"]: b for b in geo["boundaries"]}
    areas = {a["area_id"]: a for a in geo["areas"]}
    purple_boundary = boundaries["BOUNDARY-BLUE-GENERATION-WESTERN-LIMIT"]
    purple_area = areas["AREA-EAST-OF-BLUE-GENERATION-WESTERN-LIMIT"]
    orange_boundary = boundaries["BOUNDARY-RED-GENERATION-EASTERN-LIMIT"]
    orange_area = areas["AREA-WEST-OF-RED-GENERATION-EASTERN-LIMIT"]

    assert purple_boundary["status"] == purple_area["status"] == "approved"
    assert purple_boundary["approval"] == purple_area["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-24"}
    assert geography_fingerprint(purple_boundary) == "0a5f5e1e7038ea3ec47c6ecf4372a3bf896d66cfe380188878c33356013b5aac"
    assert geography_fingerprint(purple_area) == "62cb5685d2ed2e8964050c7881b18b9136d8f50005f69cd2d3f08f2dca1bd985"
    assert len(purple_area["included_hex_ids"]) == purple_area["hex_count"] == 72

    assert orange_boundary["status"] == orange_area["status"] == "approved"
    assert orange_boundary["approval"] == orange_area["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-24"}
    assert geography_fingerprint(orange_boundary) == "678ebccfdff567bcce29f86e6ec8aa56fdc6edf78a1f9f6aac698ebd0601c760"
    assert geography_fingerprint(orange_area) == "19990eeddf345ae01fc6d9cfe403bd0776ec13943b5230d6945cbbe22a3c32ce"
    assert orange_boundary["owner_specified_edge_sequence"]["edges"] == ANCHORS
    segments = orange_boundary["boundary_segments"]
    assert len(segments) == 45 and len({s["edge"] for s in segments}) == 45
    assert sum(s["transcription_class"] == "owner_confirmed_anchor" for s in segments) == 27
    assert sum(s["transcription_class"] == "visually_transcribed_connector_candidate" for s in segments) == 18
    assert [s["edge"] for s in segments if s["transcription_class"] == "owner_confirmed_anchor"] == ANCHORS
    for segment in segments:
        assert set(segment["separates"]) <= hex_set
        assert len(edge_vertices(segment["edge"])) == 2
    points = [edge_vertices(s["edge"]) for s in segments]
    assert all(points[i] & points[i + 1] for i in range(len(points) - 1))
    assert segments[-1]["edge"] == "I1/H1.5"
    occurrences: dict[tuple[float, float], list[int]] = {}
    for index, edge_points in enumerate(points):
        for point in edge_points:
            occurrences.setdefault(point, []).append(index)
    assert not {p: ids for p, ids in occurrences.items() if len(ids) > 2 or (len(ids) == 2 and ids[1] != ids[0] + 1)}

    connector_edges = [edge for interval in orange_boundary["connector_intervals"] for edge in interval["connector_edges"]]
    assert len(orange_boundary["connector_intervals"]) == 14 and len(connector_edges) == 18
    assert set(connector_edges) == {s["edge"] for s in segments if s["transcription_class"] == "visually_transcribed_connector_candidate"}
    assert all(interval["comparison_result"] == "exact_match" for interval in orange_boundary["connector_intervals"])
    assert len(review["connector_interval_reviews"]) == 14
    for item in review["connector_interval_reviews"]:
        assert item["pass_1_edges"] == item["pass_2_edges"] == item["connector_edges"]

    blocked = {frozenset(s["separates"]) for s in segments}
    adjacency = {hex_id: set() for hex_id in hex_ids}
    for i, left in enumerate(hex_ids):
        for right in hex_ids[i + 1 :]:
            if len(vertices(left) & vertices(right)) == 2 and frozenset((left, right)) not in blocked:
                adjacency[left].add(right); adjacency[right].add(left)
    west = set(); queue = deque(["C1"])
    while queue:
        value = queue.popleft()
        if value in west:
            continue
        west.add(value); queue.extend(adjacency[value] - west)
    assert orange_area["included_hex_ids"] == [value for value in hex_ids if value in west]
    assert len(west) == orange_area["hex_count"] == 51
    assert len(orange_area["included_hex_ids"]) == len(set(orange_area["included_hex_ids"]))

    vectors = {v["vector_id"]: v for v in vectors_doc["vectors"]}
    us = vectors["RV-ENABLER-US-IW-01-EFFECT-001"]
    stc = vectors["RV-ENABLER-STC-IW-01-EFFECT-001"]
    assert us["status"] == "approved" and us["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-24"}
    assert vector_fingerprint(us) == "eb1d1ce4c1f81f5bce57f8f1ebdcb98280d926154e0d9219ee8ccf960c1292d3"
    assert stc["status"] == "approved" and stc["approval"] == {"approved_by": "ルール所有者", "approved_at": "2026-09-24"}
    assert vector_fingerprint(stc) == "6d361c1d3442abaf017c2cf5a45a7c44b494960c587c5149d3eb6adea559828b"
    assert stc["expected_final_state"]["eligible_hex_ids"] == orange_area["included_hex_ids"]
    assert "blocked_by_geography" not in stc["rights_scope"]
    assert review["vectors"][1]["reviewability"] == "approved"
    assert review["approval_record"] == {"status": "approved", "approved_by": "ルール所有者", "approved_at": "2026-09-24", "approved_ids": ["BOUNDARY-RED-GENERATION-EASTERN-LIMIT", "AREA-WEST-OF-RED-GENERATION-EASTERN-LIMIT", "RV-ENABLER-STC-IW-01-EFFECT-001"]}
    assert review["verification"]["orange_complete_edge_count"] == 45
    assert review["verification"]["orange_area_hex_count"] == 51

    fragment_ids = [f["fragment_id"] for f in fragments_doc["fragments"]]
    assert len(fragment_ids) == len(set(fragment_ids))
    expected_fragments = {"FRAG-MAP-0916-ALL-HEX-IDS", "FRAG-MAP-0916-BLUE-GENERATION-WESTERN-LIMIT", "FRAG-MAP-0916-RED-GENERATION-EASTERN-LIMIT", "FRAG-MAP-0916-AREA-EAST-OF-BLUE-GENERATION-WESTERN-LIMIT", "FRAG-MAP-0916-AREA-WEST-OF-RED-GENERATION-EASTERN-LIMIT"}
    assert expected_fragments <= set(fragment_ids)
    trace_ids = [m["target_id"] for m in trace["mappings"]]
    assert len(trace_ids) == len(set(trace_ids))
    assert set(boundaries) | set(areas) | {"MAP-HEX-GRID-0916", stc["vector_id"]} <= set(trace_ids)

    with Image.open(ROOT / "sources" / "マップ 0808-0916.png") as image:
        assert image.size == (3780, 3780)
    with Image.open(RC / "generated/reviews/geography-generation-boundaries-overlay.png") as image:
        assert image.size == (3780, 3780)
        assert image.text["purple_hex_ids"].split(",") == purple_area["included_hex_ids"]
        assert image.text["orange_hex_ids"].split(",") == orange_area["included_hex_ids"]
        assert image.text["orange_boundary_edges"].split(",") == [s["edge"] for s in segments]
    segment_files = sorted((RC / "generated/reviews/geography-generation-boundaries-segments").glob("orange-connector-*.png"))
    assert len(segment_files) == 14

    source_by_id = {s["source_id"]: s for s in source_register["sources"]}
    assert len(snapshot["sources"]) == 20
    for item in snapshot["sources"]:
        source = source_by_id[item["source_id"]]
        assert sha(ROOT / source["relative_path"]) == item["content_sha256"] == source["content_sha256"]
    report_historical_snapshot_status(RC, PROTECTED, "geography-generation-boundaries")

    generated = [RC / "generated/reviews/geography-generation-boundaries-overlay.png", RC / "generated/reviews/geography-generation-boundaries-owner-review.md", RC / "generated/reviews/geography-generation-boundaries-owner-review.json", RC / "generated/digital/geography-generation-boundaries-manifest.json", *segment_files]
    before = {path: sha(path) for path in generated}
    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True)
    middle = {path: sha(path) for path in generated}
    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True)
    after = {path: sha(path) for path in generated}
    assert before == middle == after
    manifest = j(RC / "generated/digital/geography-generation-boundaries-manifest.json")
    for entry in manifest["entries"]:
        assert sha(ROOT / entry["path"]) == entry["sha256"]

    print(json.dumps({"result": "approved", "hex_count": 110, "purple_protected": True, "anchor_edges": 27, "connector_edges": 18, "complete_edges": 45, "orange_area_hex_count": 51, "stc_vector": "approved", "sources_unchanged": 20, "reproducible": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
