---
title: 戦闘
rule_core_version: 0.14.0-preview-rate-boundary
source_set: SRCSET-20260925-RATE-BOUNDARY-001
status: reviewed
license: CC-BY-SA-4.0
last_verified: 2026-09-23
---

# 戦闘

### RC-COMBAT-MD-001 ミサイル防衛の宣言

Rule: MD・盾マークを持つADA又は艦艇トークンは、残対空弾薬があり、防護対象と同一ヘックスに位置するとき、敵の対地・対艦攻撃にMDを宣言できる。潜水艦・UUVからの攻撃及び対空攻撃にはMDを宣言できない。  
When: 攻撃宣言直後、攻撃（命中）ロール前。  
Actor: 防御側プレイヤー。  
Target: 宣言済みの対地又は対艦攻撃。  
Cost: 宣言時に対空弾薬1。後の判定結果にかかわらず消費する。  
Procedure: 宣言するかしないかを命中結果を見る前に決定する。  
Result: 宣言時は`STATE-MD-LAYER-PENDING`となり、`EVENT-MD-DECLARED`を記録してMD解決へ進む。宣言しない場合は`EVENT-MD-PASSED`を記録して攻撃処理を続ける。  
Exceptions: 潜水艦・UUV攻撃及び対空攻撃。  
Interaction-Type: response_window  
Visibility-Effect: RC-COMBAT-MD-VISIBILITY-001  
State-IDs: STATE-MD-LAYER-PENDING; STATE-MD-ANTI-AIR-AMMUNITION  
Event-IDs: EVENT-MD-DECLARED; EVENT-MD-PASSED  
Authority-Type: source_rule  
Source-Fragments: FRAG-RULE-0910-2-PDF-P12-MD  
Sources: SRC-RULE-0910-2-PDF p.12  
Decision: DEC-COMBAT-MD-DICE-001; DEC-COMBAT-MD-VISIBILITY-001  
Status: reviewed

### RC-COMBAT-MD-RESOLUTION-001 MD判定と結果

Rule: MD判定にはD4を使用する。MDロールの出目4は完全迎撃、MD判定値以上4未満は部分迎撃、MD判定値未満は失敗とする。完全迎撃では攻撃を無効化するが攻撃側弾薬は消費する。部分迎撃では命中ロールとダメージロールをDISとする。失敗では攻撃を通常どおり続ける。ADA及びMD艦艇に置く物理的なD6は対空残弾数を示すカウンターであり、MD判定では振らない。Digitalの規範状態は整数の対空残弾数であり、物理的なD6表示へ依存しない。  
When: MD宣言及び宣言時弾薬消費後。  
Actor: automatic_resolution  
Target: 宣言されたMD1層と対象攻撃。  
Cost: RC-COMBAT-MD-001で消費済み。  
Procedure: D4のロール結果をMDトークン印字のMD値と比較する。残弾表示用D6は`fixed_randomness`、roll又はrandom inputとして扱わない。カード効果がMDを自動失敗させる場合は、そのカード印字に従う。  
Result: `EVENT-MD-RESOLVED`へ`full_intercept`、`partial_intercept`又は`failure`を記録し、`STATE-MD-LAYER-PENDING`を終了する。  
Exceptions: COMP-ENABLER-STC-RF-05はBLUEのMD宣言直後に当該MD1層を自動失敗させる。  
Interaction-Type: automatic_resolution  
Visibility-Effect: RC-COMBAT-MD-VISIBILITY-001  
State-IDs: STATE-MD-LAYER-PENDING; STATE-MD-ANTI-AIR-AMMUNITION  
Event-IDs: EVENT-MD-RESOLVED  
Authority-Type: source_rule  
Source-Fragments: FRAG-RULE-0910-2-PDF-P12-MD; FRAG-ENABLER-0830-1-STC-RF-05  
Sources: SRC-RULE-0910-2-PDF p.12; SRC-ENABLER-0830-1 p.41  
Decision: DEC-COMBAT-MD-DICE-001; DEC-COMBAT-MD-VISIBILITY-001  
Status: reviewed

### RC-COMBAT-MD-LAYERED-001 レイヤード防衛

Rule: 防護対象と同一ヘックスにMD可能な海軍アセットとADAの両方がある場合、海軍アセット、ADAの順に各1回MDを宣言できる。各層は独立に判定し、ADAのMDは海軍アセットの結果を見た後に実施可否を決められる。  
When: 両種類のMDアセットが使用資格を満たす攻撃。  
Actor: 防御側プレイヤー。  
Target: 同一の宣言済み攻撃。  
Cost: 宣言した各MD層について対空弾薬1。  
Procedure: 海軍アセットのresponse_windowと解決を完了し、その後ADAのresponse_windowを開く。  
Result: いずれかの層が完全迎撃すれば攻撃は無効。そうでなければ各層の結果を適用して攻撃処理へ戻る。  
Exceptions: not_stated  
Interaction-Type: response_window; automatic_resolution  
Visibility-Effect: RC-COMBAT-MD-VISIBILITY-001  
State-IDs: STATE-MD-LAYER-PENDING; STATE-MD-ANTI-AIR-AMMUNITION  
Event-IDs: EVENT-MD-DECLARED; EVENT-MD-PASSED; EVENT-MD-RESOLVED  
Authority-Type: source_rule  
Source-Fragments: FRAG-RULE-0910-2-PDF-P12-MD  
Sources: SRC-RULE-0910-2-PDF p.12  
Decision: DEC-COMBAT-MD-DICE-001; DEC-COMBAT-MD-VISIBILITY-001  
Status: reviewed
