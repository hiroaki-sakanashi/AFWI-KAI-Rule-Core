# スコードロン配備・activation・生成・帰還

本書はスコードロン共通処理の意味正本である。数値・ID・field-level visibilityの構造化正本は`data/squadron-activation.yaml`及び`data/state-and-event-ids.yaml`とする。Digital内部のcontinuation、stack、resume token、UI操作及び保存表現は規範に含めない。

## 配備 — RC-SQUADRON-DEPLOYMENT-001

ATO準備で選択したスコードロンプレートを基地群へ配備し、新規配備時は未捕捉とする。捕捉状態は`STATE-SQUADRON-ACQUIRED`で別に管理する。

## Activation — RC-SQUADRON-ACTIVATION-001

管理陣営は配備済みプレートと生成予定token数を宣言する。印字最大数、利用可能な物理token、使用可能★及び配備基地群の残余出撃キャパシティを確認し、合法な場合に出撃コストを支払う。支払は整備補給判定より前に行い、実生成数が0でも返還しない。同一plateは、必要なコストを支払える限り同一ATO中に複数回activationできるため、plateへactivation済みflagを設定しない。

## Generation — RC-SQUADRON-GENERATION-001

支払済みactivationについて、配備基地群の整備補給欄に従いD4を解決し、実生成数を確定する。生成できなかった分は地上断念として処理する。通常はtoken poolに残し、分散配置中は正式資料に従って地上断念tokenのうち1個を除去する。実生成tokenは合法な生成hexへ配置する。

実生成tokenの生成位置は、各スコードロンプレートに印字された生成位置規則に従う。兆候マーカーを参照するスコードロンでは、マーカーが存在する場合はプレート記載どおりそのマーカーに従って生成する。プレートに「マーカーがなければ配備基地ヘックス上に生成」と記載されている場合は、その指示に従う。兆候マーカーは生成位置を規定するものであり、その不存在そのものをactivation不可条件としない。

同一ATO中の再出撃にも、利用可能token、使用可能★、出撃費、配備基地群の残余出撃キャパシティ及び整備補給等の通常条件を適用する。生成位置は再出撃時も各プレートの記載に従う。

航空運用インフラ被害は翌日以降の出撃キャパシティに影響し、整備補給基盤被害はtoken生成へ直ちに影響する。両状態を混同しない。

以上の生成位置及び再出撃の明確化は、作者裁定（2026-10-04）による。

## 通常帰還 — RC-SQUADRON-RETURN-001

ATO終了時又は規定された通常帰還契機に、残存するスコードロン由来航空機tokenをtoken poolへ戻す。正式資料に明記された捕捉、弾薬及び燃料状態をresetし、再生成可能にする。撃破token、plate撃破時の飛行中token除去、艦載機の帰投先喪失は本規則の対象外とする。

## 公開契約

管理陣営はComponent ID、plate、生成予定数、★、基地状態、D4、実生成数、地上断念、個別token ID及び生成位置をすべて知る。

相手陣営には、activationの発生、生成予定数、必要・支払★、D4結果、実生成数、地上断念数、生成token数、盤上位置及び処理完了を公開する。基地群の出撃キャパシティ、航空運用インフラ被害及び整備補給基盤被害も両陣営へ公開する。

未捕捉スコードロンのComponent ID、plate identity、個別token IDと出所plateの対応は管理陣営だけが知る。相手陣営への正体開示は`STATE-SQUADRON-ACQUIRED`及び捕捉・インテル規則に従う。token生成時は数と配置hexだけを相手陣営へ公開し、通常帰還時はtoken数、帰還元hex及び帰還処理の発生だけを公開する。

## KJ-500／KQ-200適用例

- `COMP-SQUADRON-STC-SQ-04`（KJ-500）：最大1 token、出撃コスト★2。1 tokenを宣言し、★2を支払い、整備補給結果に従って正しい基地群hexへ生成する。
- `COMP-SQUADRON-STC-SQ-13`（KQ-200）：最大1 token、出撃コスト★2。1 tokenを宣言し、★2を支払い、整備補給結果に従って正しい基地群hexへ生成する。

両例は同じ共通Rule／State／Event語彙を使用し、機種固有性能をactivation規則へ埋め込まない。

## 出典

- `FRAG-RULE-0910-2-PDF-P8-9-SQUADRON-ACTIVATION`
- `FRAG-RULE-0910-2-DOCX-P184-192-SQUADRON-ACTIVATION`
- `FRAG-RULE-0910-2-PDF-P19-SCENARIO1-PRC-DAY1-SQUADRONS`
- `FRAG-RULE-0910-2-DOCX-P536-541-SCENARIO1-PRC-DAY1-SQUADRONS`
- `FRAG-BOARD-A3-0915-ENTIRE`
- `FRAG-BOARD-A4-0815-01-ENTIRE`
- `FRAG-SQUADRON-0901-P2-STC-SQ-04`
- `FRAG-SQUADRON-0901-P3-STC-SQ-13`
- `FRAG-TOKEN-0901-1-P5-6-KJ-500`
- `FRAG-TOKEN-0901-1-P5-6-KQ-200`
- `DEC-SQUADRON-ACTIVATION-VISIBILITY-001`
