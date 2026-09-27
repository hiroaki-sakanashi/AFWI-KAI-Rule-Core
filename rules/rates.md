---
title: レート
rule_core_version: 0.14.0-preview-rate-boundary
source_set: SRCSET-20260925-RATE-BOUNDARY-001
status: reviewed
license: CC-BY-SA-4.0
rights_scope: AFWI-KAI original material; public release remains subject to ISSUE-RIGHTS-006
last_verified: 2026-09-23
---

# レート

この文書は、正式ルールPDF、現行A3ボード、および抽出用DOCXを照合して確認できた最小範囲を記述する。初期値、範囲、閾値、増減量、式およびシナリオ差分の正本は `rule-core/data/rates.yaml` であり、この文書では別の数値正本を作らない。

### RC-RATE-MODEL-001 レートの構成

Rule: 宇宙レートとサイバーレートは各陣営が個別に持ち、戦略レートは両陣営で一つを共有する。現在値は公開状態として保持する。  
When: セットアップ時およびレートを参照するとき。  
Procedure: `rates.*.initial_value` で初期化し、対応する `state_id` に現在値を保持する。  
Authority-Type: source_rule  
Source-Fragments: FRAG-RULE-0910-2-PDF-P3-P4-RATE-OVERVIEW; FRAG-RULE-0910-2-PDF-P15-RATES; FRAG-RULE-0910-2-PDF-P16-RATE-DISPLAY  
Status: reviewed

### RC-RATE-SPACE-RANGE-001 / RC-RATE-SPACE-PENALTY-001 宇宙レート

Rule: 宇宙レートは各陣営の宇宙活用度を表す。現在値が `rate_rules[RC-RATE-SPACE-PENALTY-001].parameters.effects` の各条件を満たす場合、その対象と結果を適用する。  
When: 対象となるロールまたはミサイル防衛の有効性を判定するとき。  
Procedure: 対応陣営の公開宇宙レートを参照し、条件を満たす効果だけを適用する。  
Exceptions: 同一ヘックスからの攻撃に関する例外は規範YAMLの該当効果に保持する。  
Authority-Type: source_rule  
Source-Fragments: FRAG-RULE-0910-2-PDF-P15-RATES; FRAG-BOARD-A3-0915-P1-RATE-BOARDS  
Status: reviewed

### RC-RATE-CYBER-RANGE-001 / RC-RATE-CYBER-INCREASE-001 サイバーレート

Rule: サイバーレートを上げる判定が規則上発生したとき、現在値に対応する閾値以上の出目なら変更し、未満なら変更しない。  
When: レートを上げる効果が発生したとき。  
Actor: 当該効果を適用する陣営。  
Procedure: `threshold_by_transition` を参照して固定されたD6出目を比較し、成功時に `increment_on_success` を適用する。  
Exceptions: どのカードが判定を発生させるか及び低下量はカードごとの規範に従う。端点での合法性、判定及び値制限は `RC-RATE-BOUNDARY-001` に従う。  
Authority-Type: source_rule  
Source-Fragments: FRAG-RULE-0910-2-PDF-P3-P4-RATE-OVERVIEW; FRAG-BOARD-A3-0915-P1-RATE-BOARDS  
Status: reviewed

### RC-RATE-CYBER-DOMINANCE-001 サイバードミナンス

Rule: ATOサイクル終了時にサイバーレート4の陣営は、次のATOサイクル中サイバードミナンスを達成する。達成陣営は確認数制限なく、相手の兆候マーカーと当該ATO選択イネーブラーを全公開させ、配備済みスコードロンをすべて捕捉状態にする。敵が達成している次ATOは、相手の現在の使用可能な指揮所活性から10を減らす。  
When: 各ATOサイクル終了時。  
Actor: automatic_resolution  
Target: 達成陣営の相手側兆候マーカー、当該ATO選択イネーブラー、全配備スコードロン及び使用可能指揮所活性。  
Procedure: 公開サイバーレートを閾値と比較し、成立した場合は`STATE-CYBER-DOMINANCE`と`EVENT-CYBER-DOMINANCE-ESTABLISHED`を記録する。指揮所活性への演算は、現在値をoperandとして10をsubtractするdecreaseであり、固定目標値はない。他の減少・拘束効果を解除又は上書きせず、計算結果が変わらない限り新しい適用順を設けない。効果は次ATO終了まで適用し、終了時に状態を失効させ`EVENT-CYBER-DOMINANCE-EXPIRED`を記録する。  
Result: 指定対象を公開又は捕捉状態とし、相手の現在の使用可能な指揮所活性から10を減らす。他の減少・拘束がない場合に40から30となるのは具体例であり、30へ設定する処理ではない。海底ケーブル切断による5減少が適用済みなら35からさらに10を減らして25とし、分散配置による3個の拘束も維持する。失効時に公開・捕捉状態を自動的に巻き戻さない。  
Interaction-Type: automatic_resolution  
Visibility-Effect: 相手兆候と当該ATO選択イネーブラーをpublic、全配備スコードロンを捕捉済みpublicとする。有効期間は次ATO中。  
Authority-Type: source_rule  
Source-Fragments: FRAG-RULE-0910-2-PDF-P15-RATES; FRAG-RULE-0910-2-PDF-P15-CYBER-DOMINANCE; FRAG-BOARD-A3-0915-P1-RATE-BOARDS  
Status: reviewed

### RC-RATE-INITIATIVE-001 / RC-RATE-INTEL-001 レートから導く処理

Rule: イニシアチブ修正と確認可能数は、各陣営の宇宙レートとサイバーレートから導く。式と適用条件は規範YAMLを正本とする。  
When: イニシアチブ判定またはインテル活動の確認数を求めるとき。  
Procedure: 対応する `rate_rules` の式を適用する。  
Authority-Type: source_rule  
Source-Fragments: FRAG-RULE-0910-2-PDF-P5-INITIATIVE-INTEL; FRAG-BOARD-A3-0915-P1-RATE-BOARDS  
Status: reviewed

### RC-RATE-STRATEGIC-RANGE-001 / RC-RATE-STRATEGIC-SCENARIO-001 戦略レート

Rule: 戦略レートは中央から各陣営優勢方向へ進む共有レートであり、シナリオ表またはイネーブラーカードの効果に従って変化する。  
When: 規範YAMLのシナリオ原因またはカード効果が成立したとき。  
Procedure: 対象シナリオの条件、方向および量を適用し、変更イベントを記録する。  
Exceptions: 係争地域を用いる条件は地理IDの検証済み転記までvector化しない。カード固有の変化はカード単位転記まで補わない。  
Authority-Type: source_rule  
Source-Fragments: FRAG-BOARD-A3-0915-P2-STRATEGIC-SCENARIO1; FRAG-BOARD-A3-0915-P3-STRATEGIC-SCENARIO2; FRAG-RULE-0910-2-PDF-P20-SCENARIO2-RATE  
Status: reviewed

### RC-RATE-STRATEGIC-END-001 戦略レートとゲーム終了

Rule: 通常終了時の優勢、ATOサイクル終了時の更送、およびシナリオ2固有の終了条件を、規範YAMLの各条件に従って判定する。  
When: 各条件に定めるゲーム終了時またはATOサイクル終了時。  
Procedure: 公開戦略レートと必要なシナリオ状態を参照する。A3ボードの二次元更送表で決まる具体的役職は、本試作では独自に単純化しない。  
Authority-Type: source_rule  
Source-Fragments: FRAG-RULE-0910-2-PDF-P3-P4-RATE-OVERVIEW; FRAG-RULE-0910-2-PDF-P15-RATES; FRAG-RULE-0910-2-PDF-P20-SCENARIO2-RATE; FRAG-BOARD-A3-0915-P2-STRATEGIC-SCENARIO1; FRAG-BOARD-A3-0915-P3-STRATEGIC-SCENARIO2  
Status: reviewed

### RC-RATE-VISIBILITY-001 公開状態

Rule: 各陣営の宇宙・サイバーレートと共有戦略レートの現在値は公開状態である。色や磁石などの物理表示方法は、規範状態IDの意味には含めない。  
Authority-Type: source_rule  
Source-Fragments: FRAG-RULE-0910-2-PDF-P16-RATE-DISPLAY  
Status: reviewed

### RC-RATE-BOUNDARY-001 レート上下限

Rule: 宇宙・サイバーレートの実値は0から4、共有戦略レートの実値は中央0から各陣営優勢方向6までに制限する。`4+`及び`6+`は表示上の端点であり、端点を越える隠れた値又は同方向への余剰変更量を保持しない。  
When: レート変更効果の合法候補を求めるとき、変更を解決するとき、又はATO終了時に端点効果を判定するとき。  
Procedure: 任意効果の唯一の効果が端点と同方向への変更で実値を変えない場合、その効果を合法候補にせず、宣言、判定、消費及び使用後処理を行わない。強制変更は起点処理を解決するが、値を端点に留め、実値が変わらなければ`EVENT-RATE-CHANGED`及びレート変更を条件とする後続triggerを生じさせない。複数の独立効果を持つカードは各効果を個別評価し、少なくとも一つが実際に状態を変えられる場合は使用できる。戦略レートの端点から反対方向へ動く場合は実値6を起点に変更量を差し引く。  
Exceptions: サイバーレート0でSTC-CY-05が元の上昇を取り消せる場合、取消しが実際の効果であるため使用できる。元の上昇を取り消し、追加-1は下限0で止め、カード状態は通常どおり更新する。取消しと追加低下を区別して記録し、値が変わらない追加低下について新しい`EVENT-RATE-CHANGED`を生じさせない。  
Result: 端点効果はATO終了時の実値で判定する。戦略レートが一度6へ到達しても、ATO終了前に反対方向へ移動して実値が6でなくなれば、その到達履歴だけでは更迭しない。  
Authority-Type: addition_decision  
Decision: DEC-RATE-BOUNDARY-001  
Source-Fragments: FRAG-RULE-0910-2-PDF-P15-RATES; FRAG-BOARD-A3-0915-P1-RATE-BOARDS; FRAG-BOARD-A3-0915-P2-STRATEGIC-SCENARIO1; FRAG-BOARD-A3-0915-P3-STRATEGIC-SCENARIO2; FRAG-ENABLER-0830-1-STC-CY-05  
Status: reviewed
