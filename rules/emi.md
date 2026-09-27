---
title: 電磁干渉 EMI
rule_core_version: 0.9.0-preview-emi
source_set: SRCSET-20260923-INITIAL
status: reviewed
license: CC-BY-SA-4.0
rights_scope: AFWI-KAI original material; public release remains subject to ISSUE-RIGHTS-006
last_verified: 2026-09-23
---

# 電磁干渉 EMI

この文書は、正式ルールのEMI節、EMIコンポーネントの印字、および承認済み追加裁定から確認できる最小範囲だけを記述する。

### RC-EMI-STACK-001 自軍EMSスタック値

Rule: 各陣営は、同一ヘックス内に存在する自軍トークンについて、通常のトークンを1枚につき1カウント、AEW、電子戦機およびMDトークン（艦艇・ADA）を1枚につき2カウントとして合計し、そのヘックスの自軍EMSスタック値とする。ダメージ表示の赤キューブ、セル、ダイスその他のマーカー類は、自軍EMSスタック値に含めない。  
When: 同一ヘックスの自軍EMSスタック値を求めるとき。  
Actor: 各陣営。  
Target: 同一ヘックス内に存在する自軍トークン。  
Cost: なし。  
Procedure: 対象トークンを規定のカウントで合計する。  
Result: 自軍EMSスタック値を得る。  
Exceptions: ダメージ表示の赤キューブ、セル、ダイスその他のマーカー類を含めない。  
Authority-Type: source_rule  
Source-Fragments: FRAG-RULE-0910-2-PDF-P13-EMI; FRAG-RULE-0910-2-DOCX-EMI-SECTION  
Sources: SRC-RULE-0910-2-PDF p.13; SRC-RULE-0910-2-DOCX paragraphs 313-318  
Decision: none  
Status: reviewed

### RC-EMI-STATE-001 EMI状態

Rule: 自軍トークンは、自軍EMSスタック値が7以上のヘックスに所在する間、EMI状態となる。  
When: 自軍トークンがヘックスに所在している間。  
Actor: 各陣営。  
Target: 自軍EMSスタック値が7以上のヘックスに所在する自軍トークン。  
Cost: なし。  
Procedure: RC-EMI-STACK-001で求めた自軍EMSスタック値が7以上か確認する。  
Result: 条件を満たす間、対象トークンはEMI状態となる。  
Exceptions: 今回確認したEMI fragmentでは追加例外を構造化しない。  
Authority-Type: source_rule  
Source-Fragments: FRAG-RULE-0910-2-PDF-P13-EMI; FRAG-RULE-0910-2-DOCX-EMI-SECTION; FRAG-EMI-0811-BLUE-COMPONENT; FRAG-EMI-0811-RED-COMPONENT  
Sources: SRC-RULE-0910-2-PDF p.13; SRC-RULE-0910-2-DOCX paragraphs 320-321; SRC-EMI-0811 p.1  
Decision: none  
Status: reviewed

### RC-EMI-EFFECT-001 EMIの効果

Rule: EMI状態のトークンが行う捕捉ロール、攻撃ロールおよびMDロールにDISを適用する。  
When: EMI状態のトークンが捕捉ロール、攻撃ロールまたはMDロールを行うとき。  
Actor: EMI状態のトークンを使用する陣営。  
Target: 当該捕捉ロール、攻撃ロールまたはMDロール。  
Cost: なし。  
Procedure: 対象ロールにDISを適用する。  
Result: 対象ロールをDISとして扱う。  
Exceptions: 今回確認したEMI fragmentでは追加例外を構造化しない。  
Authority-Type: source_rule  
Source-Fragments: FRAG-RULE-0910-2-PDF-P13-EMI; FRAG-RULE-0910-2-DOCX-EMI-SECTION; FRAG-EMI-0811-BLUE-COMPONENT; FRAG-EMI-0811-RED-COMPONENT  
Sources: SRC-RULE-0910-2-PDF p.13; SRC-RULE-0910-2-DOCX paragraphs 323-324; SRC-EMI-0811 p.1  
Decision: none  
Status: reviewed

### RC-EMI-COMPONENT-001 EMI物理コンポーネント

Rule: EMI物理コンポーネントは、マップ上の1ヘックスと全く同じ大きさの半透明六角形ボードである。BLUE用1個とRED用1個を、それぞれ対応するEMIシールで識別し、別々の完成コンポーネントとして扱う。  
When: EMI物理コンポーネントの仕様、識別または占有・表示単位を参照するとき。  
Actor: なし。  
Target: COMP-EMI-BLUEおよびCOMP-EMI-RED。  
Cost: なし。  
Procedure: なし。この項目は物理仕様を定め、資料にない配置・回収タイミングを追加しない。  
Result: 各コンポーネントの占有・表示単位はマップ1ヘックスである。  
Exceptions: PDF上のtop/bottomはsource locatorだけであり、ゲーム上の上下関係、配置順、優先順位、表裏関係、1個の両面コンポーネント、または2個を重ねることを意味しない。製作レイアウトおよび製作手順をゲーム属性として扱わない。  
Authority-Type: addition_decision  
Source-Fragments: FRAG-EMI-0811-BLUE-COMPONENT; FRAG-EMI-0811-RED-COMPONENT  
Sources: SRC-EMI-0811 p.1  
Decision: DEC-EMI-COMPONENT-001  
Status: reviewed
