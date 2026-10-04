---
title: 捕捉・インテル
rule_core_version: 0.14.0-preview-rate-boundary
source_set: SRCSET-20260925-RATE-BOUNDARY-001
status: reviewed
license: CC-BY-SA-4.0
last_verified: 2026-09-23
---

# 捕捉・インテル

### RC-INTEL-ACTIVITY-001 インテル活動

Rule: 各陣営の確認可能数は自軍のサイバーレートと宇宙レートの合計であり、1対象につき1を消費する。  
When: インテル活動。  
Actor: 自軍の確認可能数を使用する陣営。  
Target: 相手手札イネーブラー1枚、兆候マーカー所在ヘックス1つ、又は選択した配備済み未捕捉スコードロンプレート1枚。  
Cost: 対象1つにつき確認可能数1。  
Procedure: 対象を選択する。手札カードは当該カードを公開する。兆候ヘックスはヘックス内の全兆候を公開する。スコードロンは、確認数1につき選択したプレート1枚だけについてD4を振り、印字捕捉値以上なら当該1枚を捕捉・公開する。スコードロン判定は成否にかかわらず確認可能数を1消費する。  
Result: 公開が生じた対象を`STATE-COMPONENT-REVEALED`とする。成功した場合は選択したスコードロンプレート1枚だけを`STATE-SQUADRON-ACQUIRED`とする。他の配備済みスコードロンプレートの状態は変更しない。残確認数を更新する。  
Exceptions: US-IW-07 MAVEN SMART SYSTEMが有効な間は、自軍スコードロンプレート捕捉判定をダイスを振らずに自動成功とする。発動時機、持続期間及び対象範囲は[イネーブラーのMAVEN固有効果](enablers.md#us-iw-07-maven-smart-system)に従う。<br>
Interaction-Type: 対象選択はsequential_action。スコードロン捕捉ロールはautomatic_resolution。  
Visibility-Effect: インテル活動で公開された対象は面を上にして公開し、publicとなる。明示的な再非公開化契機はnot_stated。  
State-IDs: STATE-INTEL-CONFIRMATIONS-REMAINING; STATE-COMPONENT-REVEALED; STATE-SQUADRON-ACQUIRED  
Event-IDs: EVENT-INTEL-TARGET-CONFIRMED; EVENT-COMPONENT-REVEALED; EVENT-INTEL-ACQUISITION-SUCCEEDED; EVENT-INTEL-ACQUISITION-FAILED  
Authority-Type: source_rule  
Source-Fragments: FRAG-RULE-0910-2-PDF-P5-INITIATIVE-INTEL; FRAG-RULE-0910-2-PDF-P6-INTEL-TARGETS; FRAG-RULE-0910-2-PDF-P16-IMMEDIATE-PUBLIC-DISPLAY  
Sources: SRC-RULE-0910-2-PDF pp.5-6,16  
Decision: none  
Status: reviewed

両陣営のインテル活動の実施順は、正式資料の再確認後も明文を確認できないため、本項では補完しない。
