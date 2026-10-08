---
title: 地理・配置境界
rule_core_version: 0.16.0-preview-prc-naval-boundary
source_set: SRCSET-20260925-RATE-BOUNDARY-001
status: reviewed
license: CC-BY-SA-4.0
last_verified: 2026-10-08
---

# 地理・配置境界

### RC-GEOGRAPHY-PRC-NAVAL-INLAND-001 PRC海軍の内陸配置・生成禁止

Rule: PRCの海軍アセットに係る兆候及びその海軍アセットは、中国大陸の黒線より西側には配置・生成できない。
When: STC-NV-01〜08の兆候を新規配置するとき、又はPRC海軍アセットを新規生成するとき。
Actor: PRC。
Target: 兆候又は海軍アセットの配置・生成Hex。
Procedure: 中国大陸Hexの隣接グラフからMAP上の黒線共有辺を除き、C1を含む西側連結成分を不適格とする。
Result: 西側連結成分を合法候補集合から除外する。
Exceptions: 既存saveですでに西側へ配置済みのPRC海軍兆候は、その既存未解決chainに限り解決を完了できる。PRC航空兆候、偽兆候、ADA、陸上・宇宙・サイバー、US側は対象外。
Interaction-Type: legality
Visibility-Effect: none
State-IDs: existing omen/card/unit state only
Event-IDs: existing placement/generation events only
Authority-Type: addition_decision
Source-Fragments: FRAG-MAP-0916-ALL-HEX-IDS
Sources: SRC-MAP-0808-0916-PNG
Decision: DEC-GEOGRAPHY-PRC-NAVAL-INLAND-001
Status: approved
