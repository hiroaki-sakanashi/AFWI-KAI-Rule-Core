---
title: サイバー対象群
rule_core_version: next-rc-candidate
source_set: SRCSET-20260923-INITIAL
status: reviewed
authority: DEC-CYBER-TARGET-GROUP-001
normative_sections: [1, 2, 3, 4, 5, 7, 8]
non_normative_sections: [6, 9]
last_verified: 2026-09-27
---

# サイバー対象群（Cyber Target Group）

## 1. 位置づけと適用範囲

本書は、**サイバー機能停止の対象単位について、実装・裁定上の一貫性を確保するためのRule Core規範**である。サイバー対象群は、Digitalその他の実装および裁定において、US-CY-02／STC-CY-01の「同一名称トークン1種」を一意に処理するための規範分類である。両カードの効果が共通して波及するとみなすシステム群を、特定のDigital実装やUIから独立して定義する。

本書はプレイヤーが毎回参照するためのチャートではない。Digitalその他の実装は、プレイヤーが本書を別途見なくても対象範囲を理解できるよう、第4節の`Player Label`を選択肢に表示する。

**サイバー対象群（Cyber Target Group）**とは、AFWI-KAI上で、同一のサイバー機能停止効果が共通して波及するとみなすシステム群である。一般的な兵器カテゴリ、能力値、系列名、Digital実装の内部IDを分類基準とはしない。同じカテゴリ、能力値、系列名またはruntime typeIdを持つことだけを理由に、自動的に同一groupへ統合してはならない。

本書が定めるのは対象群の所属と表示識別子である。カードの発動条件、判定方法、ADV／DIS、選択可能時点、公開範囲、効果時間および停止可能な機能は、各カードと正式ルールの規定に従う。

対象群に属するトークンが盤上に存在しない場合でも、その対象群を指定できる。当日持続中に同じ対象群のトークンが新たに生成された場合、そのトークンにも既に発生している機能停止効果を適用する。

## 2. 三層構造

各サイバー対象群は、次の三要素を分離して保持する。

1. **Internal Group ID**：実装・裁定・検証で対象群を一意に識別する、陣営込みの安定ID。表示文言やruntime typeIdとして使用しない。
2. **Player Label**：UI上でプレイヤーへ示す名称。どの盤上トークンがまとめて影響を受けるかを、別表なしで理解できる表現とする。
3. **Included Tokens**：規範上、その対象群へ所属する正式な盤上トークン名。

対象群の同一性は`Internal Group ID`で判定する。`Player Label`の変更だけで保存済みまたは進行中の対象群の意味を変えてはならない。実装固有のruntime typeIdは、第6節の非規範mappingで`Internal Group ID`へ対応付ける。

## 3. 陣営境界とPlayer Label規則

- USとPRCをまたぐgroupを作成してはならない。すべての`Internal Group ID`は`us.`または`prc.`で始まる。
- 同じruntime typeIdを両陣営が共有していても、別groupへ対応付ける。
- `Player Label`は内部分類名ではなく、対象トークン名または対象トークンを明示する短い結合名を用いる。
- 複数トークンを含むgroupは、`F-35A/C`、`TG70.5 / TG70.8`、`SAG / CBG`のように対象範囲をラベル自体で示す。
- `Naval System`のように、どの盤上トークンが含まれるか判断できない広すぎる表示名は使用しない。
- `Mid-range ADA`のように両陣営で同じPlayer Labelが必要な場合、UIは必ず「敵US」「敵PRC」等の陣営文脈を同じ選択領域内に表示する。group IDは異なるため、データ上は曖昧にならない。

## 4. 規範Cyber Target Group表

この表が対象群所属、内部group IDおよびPlayer Labelの規範である。`Internal Group ID`は全陣営を通じて一意である。

### US

| Side | Internal Group ID | Player Label | Included Tokens | Notes |
| --- | --- | --- | --- | --- |
| US | `us.air.f-22` | F-22 | F-22 | 固有のF-22システム群。 |
| US | `us.air.f-15e` | F-15E | F-15E | F-15EXとは別group。 |
| US | `us.air.f-15ex` | F-15EX | F-15EX | F-15Eとは別group。 |
| US | `us.air.f-35` | F-35A/C | F-35A, F-35C | 作者確定。陸上型と艦載型へ同じ停止効果が波及する。 |
| US | `us.air.f-16c` | F-16C | F-16C | 固有のF-16Cシステム群。 |
| US | `us.air.b-1b` | B-1B | B-1B | 固有のB-1Bシステム群。 |
| US | `us.air.b-52h` | B-52H | B-52H | 固有のB-52Hシステム群。 |
| US | `us.air.p-8a` | P-8A | P-8A | PRC KQ-200とは別group。 |
| US | `us.air.e-7a` | E-7A | E-7A | USのAEW。PRC KJ-500とは別group。 |
| US | `us.air.kc-135r` | KC-135R | KC-135R | USのTanker。PRC YU-20とは別group。 |
| US | `us.air.mq-9` | MQ-9 | MQ-9 | USのAttack UAS。PRC TB-001とは別group。 |
| US | `us.air.rq-4` | RQ-4 | RQ-4 | USのRecon UAS。PRC WZ-10とは別group。 |
| US | `us.air.ea-37b` | EA-37B | EA-37B | 電子戦機。通常ATO航空機とは異なる生成経路でも対象に含む。 |
| US | `us.surface.sag` | TG70.5 / TG70.8 | TG70.5, TG70.8 | 作者確定。同一水上戦闘群系統。 |
| US | `us.surface.csg` | CSG | CSG | 作者確定。US SAGとは別group。F-35CはCSG本体ではなく`us.air.f-35`に属する。 |
| US | `us.ada.mid-range` | Mid-range ADA | Mid-range ADA | PRC Mid-range ADAとは別group。 |

### PRC

| Side | Internal Group ID | Player Label | Included Tokens | Notes |
| --- | --- | --- | --- | --- |
| PRC | `prc.air.j-20b` | J-20B | J-20B | 固有のJ-20Bシステム群。 |
| PRC | `prc.air.j-10` | J-10 | J-10 | 固有のJ-10システム群。 |
| PRC | `prc.air.jh-7` | JH-7 | JH-7 | 固有のJH-7システム群。 |
| PRC | `prc.air.j-16` | J-16 | J-16 | 固有のJ-16システム群。 |
| PRC | `prc.air.j-11` | J-11 | J-11 | 固有のJ-11システム群。 |
| PRC | `prc.air.h-6k` | H-6K | H-6K | 固有のH-6Kシステム群。 |
| PRC | `prc.air.kq-200` | KQ-200 | KQ-200 | US P-8Aとは別group。 |
| PRC | `prc.air.y-9g` | Y-9G | Y-9G | 電子戦機の固有システム群。 |
| PRC | `prc.air.kj-500` | KJ-500 | KJ-500 | PRCのAEW。US E-7Aとは別group。 |
| PRC | `prc.air.yu-20` | YU-20 | YU-20 | PRCのTanker。US KC-135Rとは別group。 |
| PRC | `prc.air.tb-001` | TB-001 | TB-001 | PRCのAttack UAS。US MQ-9とは別group。 |
| PRC | `prc.air.wz-10` | WZ-10 | WZ-10 | PRCのRecon UAS。US RQ-4とは別group。 |
| PRC | `prc.surface.major-combatant` | SAG / CBG | SAG-1, SAG-2, SAG-3, CBG | 作者確定。CBG本体のセンサ、対空、MD、対艦能力は護衛水上艦艇群の能力を表すため、SAGと同じgroup。 |
| PRC | `prc.air.j-15` | J-15 | J-15 | 作者確定。CBG艦載機はCBG本体とは別group。 |
| PRC | `prc.surface.missile-boat-squadron` | Missile Boat Squadron | Missile Boat Squadron | Major Surface Combatantとは別group。 |
| PRC | `prc.ada.mid-range` | Mid-range ADA | Mid-range ADA | Long-range ADAおよびUS Mid-range ADAとは別group。 |
| PRC | `prc.ada.long-range` | Long-range ADA | Long-range ADA | Mid-range ADAとは別group。 |

## 5. 所属と表示の不変条件

1. 盤上に存在し得るサイバー対象トークンは、同じ陣営内でちょうど1つのgroupに属する。
2. 同じトークンを複数groupへ所属させてはならない。
3. USとPRCのgroupを統合してはならない。
4. すべてのgroupは、少なくとも1件のDigital mappingまたは将来実装の同等mappingから到達できなければならない。
5. Player Label単独で複数トークンの対象範囲を誤認させてはならない。
6. 新トークン追加時は、既存groupへの所属または新group作成をルール所有者が明示する。名称、カテゴリ、能力値、系列または実装IDから所属を自動推論しない。
7. 盤上に所属トークンが存在しないgroupも指定可能な対象として扱う。
8. 当日持続中に新たに生成された所属トークンへ、同じgroupに既に発生している機能停止効果を適用する。

## 6. Digital implementation mapping（非規範）

> **この節は現行AFWI-KAI Digital実装用の非規範対応表である。Rule Core規範は第4節のCyber Target Group表である。将来の実装は異なる内部IDを使用してよい。**

対応キーは`(side, runtime typeId)`である。runtime typeIdだけでgroupを識別してはならない。UIはmapping先groupの`Player Label`を表示し、runtime typeIdやInternal Group IDをプレイヤー向け名称としてそのまま表示しない。

### US mapping

| Side | Digital runtime typeId | Internal Group ID | Player Label | Formal system represented |
| --- | --- | --- | --- | --- |
| US | `F-22` | `us.air.f-22` | F-22 | F-22 |
| US | `F-15E` | `us.air.f-15e` | F-15E | F-15E |
| US | `F-15EX` | `us.air.f-15ex` | F-15EX | F-15EX |
| US | `F-35A` | `us.air.f-35` | F-35A/C | F-35A |
| US | `F-35C` | `us.air.f-35` | F-35A/C | F-35C |
| US | `F-16C` | `us.air.f-16c` | F-16C | F-16C |
| US | `B-1` | `us.air.b-1b` | B-1B | B-1B |
| US | `B-52` | `us.air.b-52h` | B-52H | B-52H |
| US | `P-8A` | `us.air.p-8a` | P-8A | P-8A |
| US | `AEW` | `us.air.e-7a` | E-7A | E-7A |
| US | `Tanker` | `us.air.kc-135r` | KC-135R | KC-135R |
| US | `Attack UAS` | `us.air.mq-9` | MQ-9 | MQ-9 |
| US | `Recon UAS` | `us.air.rq-4` | RQ-4 | RQ-4 |
| US | `EA-37B` | `us.air.ea-37b` | EA-37B | EA-37B |
| US | `TG70.5` | `us.surface.sag` | TG70.5 / TG70.8 | TG70.5 |
| US | `TG70.8` | `us.surface.sag` | TG70.5 / TG70.8 | TG70.8 |
| US | `CSG` | `us.surface.csg` | CSG | CSG |
| US | `ADA-MR` | `us.ada.mid-range` | Mid-range ADA | Mid-range ADA |

### PRC mapping

| Side | Digital runtime typeId | Internal Group ID | Player Label | Formal system represented |
| --- | --- | --- | --- | --- |
| PRC | `J-20B` | `prc.air.j-20b` | J-20B | J-20B |
| PRC | `J-10` | `prc.air.j-10` | J-10 | J-10 |
| PRC | `JH-7` | `prc.air.jh-7` | JH-7 | JH-7 |
| PRC | `J-16` | `prc.air.j-16` | J-16 | J-16 |
| PRC | `J-11` | `prc.air.j-11` | J-11 | J-11 |
| PRC | `H-6K` | `prc.air.h-6k` | H-6K | H-6K |
| PRC | `KQ-200` | `prc.air.kq-200` | KQ-200 | KQ-200 |
| PRC | `Y-9G` | `prc.air.y-9g` | Y-9G | Y-9G |
| PRC | `AEW` | `prc.air.kj-500` | KJ-500 | KJ-500 |
| PRC | `Tanker` | `prc.air.yu-20` | YU-20 | YU-20 |
| PRC | `Attack UAS` | `prc.air.tb-001` | TB-001 | TB-001 |
| PRC | `Recon UAS` | `prc.air.wz-10` | WZ-10 | WZ-10 |
| PRC | `SAG-1` | `prc.surface.major-combatant` | SAG / CBG | SAG-1 |
| PRC | `SAG-2` | `prc.surface.major-combatant` | SAG / CBG | SAG-2 |
| PRC | `SAG-3` | `prc.surface.major-combatant` | SAG / CBG | SAG-3 |
| PRC | `CBG` | `prc.surface.major-combatant` | SAG / CBG | CBG本体 |
| PRC | `J-15` | `prc.air.j-15` | J-15 | J-15 |
| PRC | `Missile Boat Squadron` | `prc.surface.missile-boat-squadron` | Missile Boat Squadron | Missile Boat Squadron |
| PRC | `ADA-MR` | `prc.ada.mid-range` | Mid-range ADA | Mid-range ADA |
| PRC | `ADA-LR` | `prc.ada.long-range` | Long-range ADA | Long-range ADA |

現行Digitalでは、EA-37B、F-35CおよびJ-15が盤上に存在できる一方、サイバー対象候補の静的列挙から漏れている。本表はそれらを規範groupへ割り当てるが、現行Digitalの処理を変更するものではない。

## 7. 現行カード文言との関係

現時点ではUS-CY-02／STC-CY-01のカード文言を変更しない。現行の「同一名称トークン1種」は、Digitalでは内部的に第4節のCyber Target Groupへ対応付けて処理する方針とする。

対象選択時に当該groupのトークンが盤上に存在することは要件ではない。選択されたgroupへの当日持続効果は、選択時に存在した個別トークンの一覧ではなくgroup自体に対して成立し、その後同じ当日中に生成された所属トークンにも適用する。

Player Label自体が含まれる盤上トークンを明示するため、通常の選択時にプレイヤーへ本書や追加の参照表を要求しない。カード単体の運用を妨げる追加参照ルールとして本書を扱わない。

将来カード文言を改訂する場合の第一候補は次のとおりだが、本書の更新によって現行カード印字を変更したものとはみなさない。

> 成功時、敵のサイバー対象群1種を指定。当日終了まで、その対象群の［捕捉／対空／対地・対艦］のいずれか1機能を強制停止させる。

## 8. 機械的網羅性確認

現行Digitalで`CanonicalState.units`に入り得るruntime typeIdは33種類である。両陣営が同じruntime typeIdを共有するTanker、AEW、Attack UAS、Recon UAS、ADA-MRを陣営別に展開すると、確認対象は38件となる。

| Check | Result |
| --- | --- |
| 規範group | US 16group、PRC 17group、合計33group |
| Digital `(side, runtime typeId)` mapping | US 18件、PRC 20件、合計38件 |
| 全対象トークンがちょうど1groupに所属 | 適合 |
| 未分類 | 0件 |
| 重複所属 | 0件 |
| US/PRC跨ぎgroup | 0件 |
| Player Labelの意味上の曖昧性 | 0件。陣営共通表記のMid-range ADAは、UIの敵陣営文脈と陣営別group IDで区別する |
| Digital mappingから到達不能なgroup | 0件 |
| 既知の対象漏れ EA-37B / F-35C / J-15 | 3件とも分類済み |

## 9. 将来Digitalへ実装する場合の最小変更案

1. 第4節相当の定義を、`groupId`、`side`、`playerLabel`、`includedTokenTypeIds`を持つRule Core由来データとして取り込む。
2. `(side, runtime typeId)`から`groupId`を得る一意mappingを追加し、起動時またはbuild時に未分類・重複・陣営不一致・到達不能を検査する。
3. US-CY-02／STC-CY-01のlegal option生成を、個別runtime typeIdの列挙から、盤上に合法対象を持つ敵groupの列挙へ置き換える。
4. UIはoptionに付随する`playerLabel`と、必要ならIncluded Tokensの短い補足を表示する。`groupId`は表示しない。
5. legal optionは、盤上に所属トークンが存在しない敵groupも指定候補に含める。
6. 効果は選択時の個別unit ID集合ではなく、敵陣営と`groupId`に対して保持する。当日持続中は、選択groupに現在属する全runtime typeへ共通適用し、後から生成された所属トークンにも適用する。
7. 保存形式を変更する段階では、`targetSide`と`groupId`の保持、および既存`targetTypeId`からの変換を別途設計・承認する。本書だけを根拠に既存saveを移行しない。
8. 現行カード印字、Rules Engineのそれ以外の合法性、効果時間、機能選択、ADV／DISは変更しない。

## 10. 未決境界

現行33 runtime typeに対応する所属、Internal Group ID、Player Label、盤上不在groupの指定可否および当日中に後発生成された所属トークンへの効果適用について、追加の作者判断が必要な項目はない。将来、対象トークンが追加・改名された場合の所属とPlayer Labelは、その都度ルール所有者が確定する。

現行カード印字を将来いつ、どの版で新文言へ更新するかは、本書では裁定しない。
