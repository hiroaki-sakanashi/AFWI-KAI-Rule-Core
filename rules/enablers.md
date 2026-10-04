---
title: イネーブラー
rule_core_version: 0.14.0-preview-rate-boundary
source_set: SRCSET-20260925-RATE-BOUNDARY-001
status: reviewed
license: CC-BY-SA-4.0
last_verified: 2026-09-23
---

# イネーブラー

### RC-ENABLER-IMMEDIATE-001 即応カード

Rule: 「即応」の記載と黄色稲妻マークを持つカードは、発動準備スタンドを経由せず、カードに印字されたタイミングで手札から直接使用できる。  
When: `data/enablers.yaml`の各カードの`trigger`が成立したとき。  
Actor: 対応カードを手札に持つ陣営。  
Target: カードごとの`target`。  
Cost: カード印字に従う。  
Procedure: 成立したカード固有triggerについて`response_window`を開き、使用された場合は印字効果を適用する。  
Result: カードごとの`effect`と`card_state`を適用する。  
Exceptions: 「相手ターン中いつでも使用可能」という共通則は存在しない。  
Interaction-Type: response_window  
Visibility-Effect: 使用前の手札は非公開。使用時のカード自体の公開開始時点はnot_stated。  
State-IDs: not_stated  
Event-IDs: EVENT-IMMEDIATE-ENABLER-PLAYED  
Authority-Type: source_rule  
Source-Fragments: FRAG-RULE-0910-2-PDF-P16-IMMEDIATE-PUBLIC-DISPLAY; SRC-ENABLER-0830-1の18枚のカード単位fragment（`data/enablers.yaml`参照）  
Sources: SRC-RULE-0910-2-PDF p.16; SRC-ENABLER-0830-1 pp.9,10,15,16,19,21,28,29,41,45,49,52,54,55,56,58,59,62  
Decision: DEC-ENABLER-NV-MULTIPLE-001; DEC-ENABLER-CYBER-COUNTER-SCOPE-001; DEC-ENABLER-US-AF-10-MD-TIMING-001  
Status: approved

カード固有のtrigger、対象、判定、効果、持続、消費・再選択状態及び承認済みのカード間相互作用は`data/enablers.yaml`が構造化正本である。即応カード18枚と既存即応vector 47件は承認済みである。以下は2026-09-24の追加裁定による最小限の相互作用規則である。

#### US-IW-07 MAVEN SMART SYSTEM

自軍インテル活動開始時にカードを公開して発動する。そのインテル活動を含む当日終了まで、自軍が行うスコードロンプレート捕捉判定をすべて自動成功とし、対象となる捕捉判定ではダイスを振らない。艦艇等のトークン捕捉、インテル活動全体又は別種の判定へ効果を拡張しない。当日終了後は再選択可能とする。

本項は既存のMAVEN固有効果を本文に明記したものであり、作者裁定（2026-10-04）に従って対象範囲を明確化する。出典は`FRAG-ENABLER-0830-1-US-IW-07`。

#### STC-NV-07／STC-NV-08

同じBLUE艦の同じ移動終了が両カードの条件を満たす場合、REDは両方を使用でき、使用・解決順を決める。カードは一括して発動・消費せず、REDが選んだ順に1枚ずつ使用・解決する。両攻撃がBLUE艦へ与えるヒット数の期待値は順序で変わらないが、解決順はREDプレイヤーの実質的な選択である。先の攻撃後も対象艦が存在する場合だけ後続カードを使用・解決できる。先の攻撃で対象艦が撃破・除去された場合、先行カードは使用済みとなり、その兆候マーカーはカード記載どおり処理する。後続カードは未発動で手札に残り、対応マーカーも盤上に残り、使用回数を消費せず、後続攻撃を実行しない。このため、どちらを先に解決するかによって、対象艦除去後に残るカードと兆候マーカーが変わり、ゲーム状態に差異が生じ得る。

Authority-Type: addition_decision  
Decision: DEC-ENABLER-NV-MULTIPLE-001

#### サイバー対抗カードとミュトス

判定を持たないサイバー関連カードに対して、効果が生じないサイバー対抗カードを使用できず、合法候補として提示しない。不適格なカードは手札又は利用可能状態を維持し、使用回数を消費しない。

Day1及びDay2では、ミュトス（US-CY-05）によりUS-CY-01の判定が自動成功となる。自動成功はDIS化の対象ではなく、サイバーカウンターメジャー（STC-CY-04）は合法な対抗選択肢にならない。Day3以降では、ミュトスが同じUS-CY-01判定へADVを、サイバーカウンターメジャーがDISを与え、両者は相殺して通常のD4判定になる。この合法な使用ではSTC-CY-04の使用回数を消費する。

Authority-Type: addition_decision  
Decision: DEC-ENABLER-CYBER-COUNTER-SCOPE-001

#### US-AF-10とMD判断

BLUE航空機がADAを攻撃するときは、(1)攻撃宣言、(2)BLUEのUS-AF-10使用判断、(3)使用する場合のUS-AF-10宣言、(4)その宣言有無を知ったREDのMD使用判断、(5)REDがMDを宣言した場合のBLUEのUS-EW-03応答機会、(6)MD処理、(7)攻撃が未解決ならUS-AF-10のADVを維持した攻撃処理、の順に進める。

Authority-Type: addition_decision  
Decision: DEC-ENABLER-US-AF-10-MD-TIMING-001
