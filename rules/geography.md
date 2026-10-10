---
title: 地理・配置境界
rule_core_version: 0.18.0-preview-prohibited-hex-movement
source_set: SRCSET-20260925-RATE-BOUNDARY-001
status: reviewed
license: CC-BY-SA-4.0
last_verified: 2026-10-09
---

# 地理・配置境界

### RC-GEOGRAPHY-NAVAL-BOUNDARIES-001 海軍の黒線制約及びPRC橙ライン制約

Rule: PRC海軍に係る兆候及び海軍アセットは、橙ラインの西側かつ中国大陸黒線の東側にのみ配置・生成できる。中国大陸黒線より西側には、いずれの陣営の海軍も配置・生成・進入できない。
When: STC-NV-01〜08の兆候を新規配置するとき、海軍アセットを新規生成するとき、又は海軍ユニットが移動するとき。
Actor: 全陣営。橙ライン条件はPRCのみ。
Target: 兆候又は海軍アセットの配置・生成Hex、及び海軍移動先Hex。
Procedure: 橙ライン西側は`AREA-WEST-OF-RED-GENERATION-EASTERN-LIMIT`、中国大陸黒線東側・西側は完全な黒線共有辺でHex隣接グラフを分割した各Areaを用いる。PRC海軍合法範囲は橙ライン西側と黒線東側の積集合とする。
Result: 黒線西側を全陣営海軍の合法候補から除外し、PRC海軍については橙ライン外側も除外する。
Exceptions: 既存saveですでに旧合法性で配置・生成済みの兆候及び海軍アセットはReplay可能とし、既存未解決chainに限り完了できる。PRC航空兆候、偽兆候、ADA、陸上・宇宙・サイバーは橙ライン条件の対象外。
Interaction-Type: legality
Visibility-Effect: none
State-IDs: existing omen/card/unit state only
Event-IDs: existing placement/generation events only
Authority-Type: correction_decision
Source-Fragments: FRAG-MAP-0916-ALL-HEX-IDS, FRAG-MAP-0916-RED-GENERATION-EASTERN-LIMIT, FRAG-MAP-0916-AREA-WEST-OF-RED-GENERATION-EASTERN-LIMIT, FRAG-MAP-0916-PRC-MAINLAND-NAVAL-BLACK-LINE
Sources: SRC-MAP-0808-0916-PNG
Decision: DEC-GEOGRAPHY-NAVAL-BOUNDARIES-001
Status: approved

`RC-GEOGRAPHY-PRC-NAVAL-INLAND-001`は、黒線共有辺を不完全に機械化して西側を20 Hexへ誤拡張したため、本Ruleにより置換される。

### RC-GEOGRAPHY-PROHIBITED-HEX-MOVEMENT-001 進入禁止Hex

Rule: G5及びH4.5は、両陣営の部隊が進入できないHexである。移動の終点として指定することも、移動途中に通過することもできない。
When: 部隊が移動するとき。
Actor: 全陣営。
Target: 移動の終点及び移動途中に通過するHex。
Procedure: 所定の移動力の範囲内で、G5及びH4.5を経由しない経路が存在するかを確認する。
Result: 進入禁止Hexを経由しない経路が存在する場合、その移動は可能である。存在しない場合、その移動は不可能である。
Exceptions: none
Interaction-Type: legality
Visibility-Effect: none
State-IDs: none
Event-IDs: none
Authority-Type: addition_decision
Source-Fragments: FRAG-MAP-0916-ALL-HEX-IDS
Sources: SRC-MAP-0808-0916-PNG
Decision: DEC-GEOGRAPHY-PROHIBITED-HEX-MOVEMENT-001
Status: approved
