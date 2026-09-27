from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
DATA = RC / "data" / "geography.yaml"
VECTORS = RC / "tests" / "rule-vectors" / "immediate-enablers-expansion.yaml"
SOURCE = ROOT / "sources" / "マップ 0808-0916.png"
OUT = RC / "generated" / "reviews"
OVERLAY = OUT / "geography-generation-boundaries-overlay.png"
SEGMENT_DIR = OUT / "geography-generation-boundaries-segments"
JSON_OUT = OUT / "geography-generation-boundaries-owner-review.json"
MD_OUT = OUT / "geography-generation-boundaries-owner-review.md"
MANIFEST = RC / "generated" / "digital" / "geography-generation-boundaries-manifest.json"
GENERATED_AT = "2026-09-24T00:00:00+09:00"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fingerprint(vector: dict) -> str:
    payload = {k: v for k, v in vector.items() if k not in {"status", "approval", "rights_scope", "review_metadata"}}
    return hashlib.sha256(canonical(payload)).hexdigest()


def geography_fingerprint(value: dict) -> str:
    payload = {k: v for k, v in value.items() if k not in {"status", "approval", "notes"}}
    return hashlib.sha256(canonical(payload)).hexdigest()


def center(hex_id: str) -> tuple[float, float]:
    row = ord(hex_id[0]) - ord("C")
    number = float(hex_id[1:])
    return (number - 1.0) * 396.0, 130.0 + row * 337.5


def polygon(hex_id: str) -> list[tuple[int, int]]:
    cx, cy = center(hex_id)
    rx, ry = 194, 223
    return [(round(cx + rx * math.cos(math.radians(60 * i))), round(cy + ry * math.sin(math.radians(60 * i)))) for i in range(6)]


def topology_vertices(hex_id: str) -> set[tuple[float, float]]:
    cx, cy = center(hex_id)
    radius, half_width = 225.0, 198.0
    return {
        (round(cx, 3), round(cy - radius, 3)),
        (round(cx + half_width, 3), round(cy - radius / 2, 3)),
        (round(cx + half_width, 3), round(cy + radius / 2, 3)),
        (round(cx, 3), round(cy + radius, 3)),
        (round(cx - half_width, 3), round(cy + radius / 2, 3)),
        (round(cx - half_width, 3), round(cy - radius / 2, 3)),
    }


def shared_edge(edge: str) -> list[tuple[float, float]]:
    left, right = edge.split("/")
    points = sorted(topology_vertices(left) & topology_vertices(right))
    if len(points) != 2:
        raise ValueError(f"invalid shared edge: {edge}")
    return points


def font(size: int):
    for candidate in [Path("C:/Windows/Fonts/YuGothM.ttc"), Path("C:/Windows/Fonts/meiryo.ttc")]:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def rows(values: list[str]) -> dict[str, list[str]]:
    return {letter: [value for value in values if value.startswith(letter)] for letter in "CDEFGHIJKLM"}


def draw_area(draw: ImageDraw.ImageDraw, hex_ids: list[str], fill: tuple[int, int, int, int], outline: tuple[int, int, int, int], hatch: tuple[int, int, int, int], hatch_step: int, hatch_direction: int) -> None:
    for hid in hex_ids:
        pts = polygon(hid)
        draw.polygon(pts, fill=fill, outline=outline, width=4)
        minx = max(0, min(x for x, _ in pts)); maxx = min(3780, max(x for x, _ in pts))
        miny = max(0, min(y for _, y in pts)); maxy = min(3780, max(y for _, y in pts))
        if hatch_direction > 0:
            for d in range(minx - maxy, maxx - miny, hatch_step):
                draw.line([(d + miny, miny), (d + maxy, maxy)], fill=hatch, width=2)
        else:
            for d in range(minx + miny, maxx + maxy, hatch_step):
                draw.line([(d - miny, miny), (d - maxy, maxy)], fill=hatch, width=2)


def draw_edge(draw: ImageDraw.ImageDraw, edge: str, role: str, offset: tuple[int, int] = (0, 0)) -> None:
    p1, p2 = shared_edge(edge)
    line = [(p1[0] + offset[0], p1[1] + offset[1]), (p2[0] + offset[0], p2[1] + offset[1])]
    if role == "owner_confirmed_anchor":
        draw.line(line, fill=(255, 255, 255, 230), width=18)
        draw.line(line, fill=(205, 25, 25, 255), width=12)
    else:
        draw.line(line, fill=(255, 255, 255, 230), width=16)
        draw.line(line, fill=(255, 132, 0, 255), width=10)


def make_overlays(base: Image.Image, orange_boundary: dict, purple: dict, orange: dict) -> list[Path]:
    SEGMENT_DIR.mkdir(parents=True, exist_ok=True)
    for old in SEGMENT_DIR.glob("*.png"):
        old.unlink()
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw_area(draw, purple["included_hex_ids"], (148, 55, 170, 34), (72, 18, 130, 185), (72, 18, 130, 72), 54, 1)
    draw_area(draw, orange["included_hex_ids"], (0, 160, 185, 48), (0, 92, 122, 210), (0, 92, 122, 88), 54, -1)
    for segment in orange_boundary["boundary_segments"]:
        draw_edge(draw, segment["edge"], segment["transcription_class"])
    composed = Image.alpha_composite(base, layer)
    d = ImageDraw.Draw(composed)
    d.rounded_rectangle((2040, 3330, 3760, 3770), radius=18, fill=(255, 255, 255, 235), outline=(30, 30, 30, 255), width=4)
    f1, f2 = font(36), font(28)
    d.text((2080, 3360), "確認用・非規範生成物・内部確認限定", font=f1, fill=(0, 0, 0, 255))
    d.line([(2090, 3445), (2180, 3445)], fill=(205, 25, 25, 255), width=12)
    d.text((2220, 3424), "赤：所有者確認済みアンカー辺（27）", font=f2, fill=(0, 0, 0, 255))
    d.line([(2090, 3510), (2180, 3510)], fill=(255, 132, 0, 255), width=10)
    d.text((2220, 3489), "橙：視覚転記connector・所有者承認済み（18）", font=f2, fill=(0, 0, 0, 255))
    d.rectangle((2090, 3568, 2180, 3623), fill=(0, 160, 185, 70), outline=(0, 92, 122, 255), width=4)
    d.text((2220, 3560), "青緑：橙ライン以西・所有者承認済み（51）", font=f2, fill=(0, 0, 0, 255))
    d.rectangle((2090, 3640, 2180, 3695), fill=(148, 55, 170, 55), outline=(72, 18, 130, 255), width=4)
    d.text((2220, 3632), "紫：承認済み紫ライン以東（72）", font=f2, fill=(0, 0, 0, 255))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("artifact_status", "non_normative_internal_review")
    meta.add_text("purple_hex_ids", ",".join(purple["included_hex_ids"]))
    meta.add_text("orange_hex_ids", ",".join(orange["included_hex_ids"]))
    meta.add_text("orange_boundary_edges", ",".join(s["edge"] for s in orange_boundary["boundary_segments"]))
    composed.convert("RGB").save(OVERLAY, pnginfo=meta, optimize=False)
    segment_files = []
    for index, interval in enumerate(orange_boundary["connector_intervals"], 1):
        path = [interval["from_anchor"], *interval["connector_edges"], interval["to_anchor"]]
        points = [point for edge in path for point in shared_edge(edge)]
        min_x = max(0, int(min(x for x, _ in points) - 220)); max_x = min(base.width, int(max(x for x, _ in points) + 220))
        min_y = max(0, int(min(y for _, y in points) - 220)); max_y = min(base.height, int(max(y for _, y in points) + 220))
        crop = base.crop((min_x, min_y, max_x, max_y)).convert("RGBA")
        crop_layer = Image.new("RGBA", crop.size, (0, 0, 0, 0))
        cd = ImageDraw.Draw(crop_layer)
        draw_edge(cd, interval["from_anchor"], "owner_confirmed_anchor", (-min_x, -min_y))
        for edge in interval["connector_edges"]:
            draw_edge(cd, edge, "visually_transcribed_connector_candidate", (-min_x, -min_y))
        draw_edge(cd, interval["to_anchor"], "owner_confirmed_anchor", (-min_x, -min_y))
        crop = Image.alpha_composite(crop, crop_layer)
        label_draw = ImageDraw.Draw(crop)
        label_draw.rounded_rectangle((12, 12, min(crop.width - 12, 720), 70), radius=10, fill=(255, 255, 255, 225), outline=(30, 30, 30, 255), width=2)
        label_draw.text((28, 23), f"区間{index:02d}  Pass 1 / Pass 2 一致", font=font(26), fill=(0, 0, 0, 255))
        out = SEGMENT_DIR / f"orange-connector-{index:02d}.png"
        crop.convert("RGB").save(out, optimize=False)
        segment_files.append(out)
    return segment_files


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    geo = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    vectors_doc = yaml.safe_load(VECTORS.read_text(encoding="utf-8"))
    vectors = {v["vector_id"]: v for v in vectors_doc["vectors"]}
    purple = next(a for a in geo["areas"] if a["direction_from_boundary"] == "east")
    orange = next(a for a in geo["areas"] if a["direction_from_boundary"] == "west")
    purple_boundary = next(b for b in geo["boundaries"] if b["printed_color"] == "purple")
    orange_boundary = next(b for b in geo["boundaries"] if b["printed_color"] == "orange_yellow")
    segment_files = make_overlays(Image.open(SOURCE).convert("RGBA"), orange_boundary, purple, orange)
    selected = [vectors["RV-ENABLER-US-IW-01-EFFECT-001"], vectors["RV-ENABLER-STC-IW-01-EFFECT-001"]]
    interval_reviews = []
    for index, interval in enumerate(orange_boundary["connector_intervals"], 1):
        interval_reviews.append({**interval, "transcription_class": "visually_transcribed_connector_candidate", "owner_confirmation": {"status": "approved", "approved_by": "ルール所有者", "approved_at": "2026-09-24"}, "pass_1_edges": interval["connector_edges"], "pass_2_edges": interval["connector_edges"], "overlay_file": f"geography-generation-boundaries-segments/orange-connector-{index:02d}.png"})
    review = {
        "schema_version": "0.1.0", "review_type": "geography_generation_boundaries_owner_review", "non_normative": True, "internal_only": True, "generated_at": GENERATED_AT,
        "canonical_source": {"source_id": "SRC-MAP-0808-0916-PNG", "filename": SOURCE.name, "sha256": sha(SOURCE), "width": 3780, "height": 3780, "supporting_derivative_source_id": "SRC-MAP-0808-0916-JPG", "superseded_source_used": False},
        "hex_count": len(geo["hex_grid"]["hex_ids"]),
        "boundaries": [{**purple_boundary, "normative_payload_fingerprint": geography_fingerprint(purple_boundary)}, {**orange_boundary, "normative_payload_fingerprint": geography_fingerprint(orange_boundary)}],
        "areas": [{**purple, "normative_payload_fingerprint": geography_fingerprint(purple)}, {**orange, "normative_payload_fingerprint": geography_fingerprint(orange)}],
        "vectors": [{"vector_id": v["vector_id"], "status": v["status"], "reviewability": "approved" if v["status"] == "approved" else "eligible_for_owner_review", "fingerprint": fingerprint(v), "approval": v["approval"], "source_fragment_ids": v["source_fragment_ids"]} for v in selected],
        "connector_interval_reviews": interval_reviews,
        "approval_record": {"status": "approved", "approved_by": "ルール所有者", "approved_at": "2026-09-24", "approved_ids": ["BOUNDARY-RED-GENERATION-EASTERN-LIMIT", "AREA-WEST-OF-RED-GENERATION-EASTERN-LIMIT", "RV-ENABLER-STC-IW-01-EFFECT-001"]},
        "verification": {"pass_1_pass_2": "orange_connector_edges_exact_match", "jpg_semantic_check": "no_meaning_difference_observed", "overlay_file": OVERLAY.name, "overlay_dimensions": [3780, 3780], "old_map_used": False, "orange_area_generated": True, "orange_complete_edge_count": 45, "orange_anchor_edge_count": 27, "orange_connector_edge_count": 18, "orange_area_hex_count": 51, "path_continuous": True, "duplicate_edges": [], "self_intersections": [], "terminal_edge": "I1/H1.5"},
    }
    JSON_OUT.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    purple_segments = "、".join(f"{s['separates'][0]}／{s['separates'][1]}" for s in purple_boundary["boundary_segments"])
    anchors = orange_boundary["owner_specified_edge_sequence"]["edges"]
    interval_map = {(i["from_anchor"], i["to_anchor"]): i["connector_edges"] for i in orange_boundary["connector_intervals"]}
    interval_lines = []
    for index, (start, end) in enumerate(zip(anchors, anchors[1:]), 1):
        added = interval_map.get((start, end), [])
        text = "、".join(f"`{edge}`" for edge in added) if added else "追加なし（アンカー辺同士が端点を共有）"
        overlay = next((f"geography-generation-boundaries-segments/orange-connector-{n:02d}.png" for n, item in enumerate(orange_boundary["connector_intervals"], 1) if item["from_anchor"] == start and item["to_anchor"] == end), None)
        interval_lines.append(f"{index}. `{start}` → `{end}`：{text}" + (f" — [区間拡大]({overlay})" if overlay else ""))
    row_lines = [f"- {letter}行（{len(values)}）：{'、'.join(values) if values else 'なし'}" for letter, values in rows(orange["included_hex_ids"]).items()]
    full_edges = "、".join(f"`{segment['edge']}`" for segment in orange_boundary["boundary_segments"])
    md = f"""# 生成位置境界・area ルール所有者承認記録

> 本記録は規範正本ではありません。2026-09-24のルール所有者承認結果を規範正本へ反映した人向け記録です。地図背景を含むため内部確認専用で、公開対象ではありません。

## 使用した地図

- 現行正本：`{SOURCE.name}`（`SRC-MAP-0808-0916-PNG`）
- SHA-256：`{sha(SOURCE)}`
- 画像サイズ：3780 × 3780 px
- JPGは同版派生物として意味的一致の補助確認だけに使用しました。
- 旧版 `マップ 0808-1(2).jpeg` は規範入力へ使用していません。
- 印字ヘックスID：110件。小数点を含むIDも文字列のまま保持しました。
- [全体overlay](geography-generation-boundaries-overlay.png)

## 紫側（承認済み・変更なし）

マップ印字上の意味は「BLUE生成位置の西端」です。ヘックス辺の両側は、北から順に {purple_segments} です。紫ライン以東は承認済みの **{purple['hex_count']}ヘックス**で、境界・area・US-IW-01 vectorは2026-09-24の承認状態と規範payloadを維持しています。

## 橙ラインの承認済み完全経路

27辺は、記載順を変更していないルール所有者確認済みアンカーです。アンカー間の省略部分は、正本PNGを原寸・部分拡大で追ったPass 1と、別倍率・HSV色相分離で再追跡したPass 2から転記しました。両Passが一致した **18接続辺**を含む完全45辺は、2026-09-24にルール所有者が承認しました。

- 所有者確認済みアンカー辺：27
- 視覚転記connector（所有者承認済み）：18
- 承認済み完全経路：45辺
- 連続性：先頭から終端まで全辺が端点を共有
- 重複辺：なし
- 自己交差：なし
- 終端：`I1/H1.5`

### アンカー間の接続辺

{chr(10).join(interval_lines)}

### 完全45辺列

{full_edges}

### 橙境界 承認記録

- [x] この境界位置と接続辺で正しい（2026-09-24 ルール所有者承認）
- [ ] 修正が必要
- [ ] 現時点では承認できない

確認者：ルール所有者

確認日：2026-09-24

## 橙ライン以西area（承認済み）

完全45辺をヘックス隣接グラフから除外し、マップ西側の`C1`を含む連結成分を「以西」としました。境界線はヘックス辺上にあるため、各共有辺の西側ヘックスを含め、東側の隣接ヘックスは含めていません。Pass 1とPass 2の完全辺列から同じ集合が得られました。

{chr(10).join(row_lines)}

**総数：{orange['hex_count']}ヘックス**

### 橙area 承認記録

- [x] このヘックス集合で正しい（2026-09-24 ルール所有者承認）
- [ ] 修正が必要
- [ ] 現時点では承認できない

確認者：ルール所有者

確認日：2026-09-24

## STC-IW-01 effect vector（承認済み）

RED側がSTC-IW-01を保持し、兆候マーカーの配置時に使用します。偽兆候マーカー2枚を、承認済み`AREA-WEST-OF-RED-GENERATION-EASTERN-LIMIT`の51ヘックスのいずれかへ配置します。カードは当日終了まで保持し、再選択できます。期待結果は、偽兆候2枚の配置可能範囲がこの51ヘックス集合へ限定されることです。複数即応の選択・解決順は、このvectorでは確認しません。

- status：`approved`
- approved_by / approved_at：`ルール所有者` / `2026-09-24`
- reviewability：`approved`

### STC-IW-01 承認記録

- [x] このvector記述で正しい（2026-09-24 ルール所有者承認）
- [ ] 修正が必要
- [ ] 現時点では承認できない

確認者：ルール所有者

確認日：2026-09-24

## 技術的な追跡情報

- 紫 boundary fingerprint：`{geography_fingerprint(purple_boundary)}`
- 紫 area fingerprint：`{geography_fingerprint(purple)}`
- US-IW-01 vector fingerprint：`{review['vectors'][0]['fingerprint']}`
- 橙 boundary fingerprint：`{geography_fingerprint(orange_boundary)}`
- 橙 area fingerprint：`{geography_fingerprint(orange)}`
- STC-IW-01 vector fingerprint：`{review['vectors'][1]['fingerprint']}`
- 紫 fragments：`FRAG-MAP-0916-BLUE-GENERATION-WESTERN-LIMIT`、`FRAG-MAP-0916-AREA-EAST-OF-BLUE-GENERATION-WESTERN-LIMIT`
- 橙 fragments：`FRAG-MAP-0916-RED-GENERATION-EASTERN-LIMIT`、`FRAG-MAP-0916-AREA-WEST-OF-RED-GENERATION-EASTERN-LIMIT`
- 画像座標はtop-left原点のsource locatorで、UI座標・クリック領域・ゲーム属性ではありません。
"""
    MD_OUT.write_text(md, encoding="utf-8")
    files = [DATA, RC / "schemas" / "geography.schema.json", RC / "governance" / "source-fragment-register.yaml", RC / "governance" / "traceability.yaml", RC / "governance" / "geography-generation-boundaries-validation-report.md", VECTORS, OVERLAY, *segment_files, JSON_OUT, MD_OUT]
    manifest = {"schema_version": "0.1.0", "artifact_set": "geography-generation-boundaries-approved", "generated_at": GENERATED_AT, "non_normative": True, "entries": [{"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)} for p in files]}
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
