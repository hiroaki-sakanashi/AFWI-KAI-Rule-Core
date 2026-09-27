---
title: AFWI-KAI Rule Core バージョン管理・リリース方針
document_version: 1.1
status: approved
created_at: 2026-09-26
supersedes_document_version: 1.0
approved_by: ルール所有者
approved_at: 2026-09-26
effective_at: 2026-09-26
governing_document: AFWI-KAI_Rule_Core_構想と作成手順-11.docx
scope: Rule Coreの多世代バージョン管理、公開、互換性及び履歴保全
---

# AFWI-KAI Rule Core バージョン管理・リリース方針

## 1. 文書の位置づけ

本書は、AFWI-KAI共有用Rule Coreを、一つの作業中ディレクトリではなく、複数世代を識別・参照・検証できる正式releaseの列として管理するための現行統治文書である。

本書は`AFWI-KAI_Rule_Core_構想と作成手順-11.docx`（以下「改訂11」）を上位の統治文書とし、改訂11が定める次の原則を具体化する。

- Rule CoreはDigital実装から独立した規範・互換性基準である。
- Rule Core releaseと各Digitalの対応状況は別に管理する。
- 公開時点のsource set、規範ファイル、承認済みrule vector、生成物及びhashを固定する。
- Rule Core ID、Component ID、State ID、Event ID等の安定IDは再利用しない。
- 旧版は通常参照パスから外れても、Git履歴及びrelease packageから再現可能にする。
- 生成物及び承認証拠は、規範正本と区別して保持する。

本書自体はゲームルールの規範出典ではなく、ゲーム規則、数値、カード効果又は裁定を追加しない。文書version 1.0は2026-09-26にルール所有者が承認し、同日付で現行release governanceとして発効した。本version 1.1は、`content_commit`、release metadata commit及びGit tagの関係を明確化する改訂として、2026-09-26にルール所有者が承認し、同日付で発効した。この改訂だけでは、具体的なRelease ID、Specification Version、Git tag、release manifest、catalog、公開又はDigital互換性宣言を確定しない。

## 2. 目的

本方針の目的は次のとおりである。

1. 頻繁な正式資料更新に対し、現行安定版を壊さずにNextを並行作業できるようにする。
2. ある時点のRule Coreを、release ID、`content_commit`、release metadata commitを指すGit tag及びmanifest hashで一意に指定できるようにする。
3. 外部開発者及び各Digitalが、依存するRule Core releaseを明示できるようにする。
4. 旧releaseを上書きせず、Replay、監査、差分確認及び互換性検証へ利用できるようにする。
5. 最新版への導線と過去版のArchiveを分離し、通常利用者と開発者の双方が誤った版を参照しにくくする。
6. 規範正本、生成物、承認証拠及びDigital適合状態を混同しない。

## 3. 用語

| 用語 | 定義 |
| --- | --- |
| Working Tree / Next | 次release候補を作成中の状態。正式releaseではなく、`Latest Stable`を置き換えない。 |
| Release | 一意のrelease ID、固定された`content_commit`、release metadata commit、Git tag、release manifest及びartifact集合を持つ公開又は内部配布可能な版。 |
| Release ID | releaseを一意に識別する不変ID。例示形式は`RC-YYYY.MM.DD-NN`。ここで`RC`はRule Coreを表し、`release-candidate`の略ではない。 |
| Specification Version | 改訂11が定める`v0.9`、`v1.x`等の仕様成熟度又は互換性系列。Release IDとは別軸である。 |
| content_commit | technical freeze gateで検証し、当該releaseのRule Core規範、Schema、validator及びgovernanceを固定するGit commit。Manifest及びCatalog自身を含む必要はない。 |
| validated_content_commit | technical freeze evidenceがclean checkoutで検証したcommit。Release Manifestの`content_commit`と一致しなければならない。 |
| Release Metadata Commit | 最終Release Manifest及びRelease Catalogを含むcommit。Manifest自身にはこのcommitのhashを必須記録しない。 |
| Latest Stable | 通常利用者及び新規実装が既定で参照する、現在推奨のstable releaseへの可変alias。release IDではない。 |
| Latest Preview | 検証又は先行実装向けの最新preview又はrelease-candidateへの可変alias。release IDではない。 |
| Archive | 過去に発行した全release、manifest、承認証拠及び必要な配布物をrelease ID単位で参照できる領域。 |
| Release Manifest | 当該releaseを構成する規範正本、承認済みvector、source set、生成物、証拠及びhashを固定する機械可読台帳。 |
| Release Catalog | 全releaseの現在の公開状態、前後関係、Latest alias及びwithdrawal noticeを記録する索引。release packageとは分離する。 |
| Normative Payload | 規範ルール、規範データ、Schema、承認済みdecision、安定ID台帳及び承認済みrule vectorのうちrelease対象とした集合。 |
| Approval Evidence | ルール所有者が確認した確認票、承認記録、fingerprint及び検証報告。規範正本ではなく、承認時点の履歴証拠である。 |
| Digital Compatibility | 特定Digital版が、特定Rule Core releaseを取込み、適合試験した範囲と結果。Rule Core releaseの存在又はstable判定とは別である。 |

## 4. 基本原則

### 4.1 Releaseは上書きしない

発行済みrelease ID、release package、Git tag及びrelease manifestのbyte列は変更しない。訂正が必要な場合は、新しいrelease IDを発行し、前版との関係及び変更理由を記録する。

### 4.2 最新導線と履歴を分離する

`Latest Stable`及び`Latest Preview`は利用者向けの可変aliasであり、規範参照、保存データ、Replay、監査及びDigital互換性宣言には使用しない。これらは必ず固定release IDとmanifest hashを記録する。

### 4.3 Statusとartifact identityを分離する

release package内の`status`は発行時点の状態として固定する。後日`stable`が`superseded`又は`withdrawn`となった事実は、過去manifestを書き換えず、Release Catalog及び追加のstatus recordで記録する。

### 4.4 ReleaseとDigitalを独立させる

Rule Coreがstableになっても、全Digitalが同時に対応する必要はない。Digital未対応はRule Core releaseの発行停止理由ではなく、Digital側の互換性状態として記録する。ただし、対象Digitalの適合をrelease目的に含めた場合は、その結果を既知事項としてmanifestへ記録する。

### 4.5 正本と生成物を分離する

生成Markdown、Digital取込み候補JSON、owner review及びvalidation reportは、規範正本から追跡できる成果物又は証拠である。生成物を直接修正して規範を変更しない。

## 5. Release ID及び版番号

### 5.1 推奨Release ID

推奨形式は次のとおりとする。

```text
RC-YYYY.MM.DD-NN
```

- `RC`は`Rule Core`を意味する。
- `YYYY.MM.DD`はrelease発行日であり、規則の`effective_date`とは別に保持する。
- `NN`は同一発行日の連番で、`01`から開始する。
- Release IDはstatus、互換性又は内容の大小を符号化しない。
- 発行前の作業では仮IDを正式参照へ使用せず、`unassigned`として扱う。
- 一度発行したRelease IDは別内容へ再利用しない。

### 5.2 Specification Versionとの関係

改訂11の`v0.9 preview`、`v1.0`及び`v1.x`は、仕様成熟度及び互換性系列として維持する。日付ベースRelease IDは個々の発行物を識別する。

例示上、同一releaseは次の二つを持ち得る。

```yaml
release_id: RC-2026.09.26-01
specification_version: 0.9.0
```

この例は命名方式の説明であり、現在のRule Coreへ当該IDを割り当てるものではない。

### 5.3 文書版

文書自身の改訂番号はrelease IDと分離する。規範Markdownは改訂11のfront matter方針に従い、少なくとも次を持つ。

- 文書又は規則を識別する安定ID
- `document_version`
- `introduced_in`
- `deprecated_in`又は`null`
- `status`
- 関連Rule Core ID
- source fragment又はdecision参照
- license及びrights scope

ファイル移動又は表示名変更だけでは文書ID及びRule Core IDを変更しない。生成物、承認証拠及び監査snapshotには規範文書と同じfront matterを強制せず、それぞれのmanifestで生成元、生成時点及び対象releaseを記録する。

## 6. Release lifecycle

### 6.1 正式状態

| 状態 | 用途 | 公開範囲 | 次の状態 |
| --- | --- | --- | --- |
| `preview` | 不完全な範囲を含む先行共有。未解決範囲と非収録範囲を明示する。 | 開発者、レビュー担当、限定利用者 | 新しい`preview`又は`release-candidate` |
| `release-candidate` | stable候補としてpayloadを凍結し、最終検証と所有者確認を行う。 | 開発者、所有者、適合試験担当 | 新しい`release-candidate`又は`stable` |
| `stable` | 所定のStable昇格条件を満たす通常参照版。 | 一般利用者及び外部開発者 | 後継stable発行後にcatalog上`superseded` |
| `superseded` | 後継stableが存在する旧stable。利用停止を意味せず、固定依存とReplayでは引き続き参照できる。 | Archive | そのまま保持、又は重大問題時`withdrawn` |
| `withdrawn` | 重大な規範誤り、権利問題又は安全上の理由で新規利用を停止した版。削除はしない。 | Archiveとwithdrawal notice | 原則終端 |

### 6.2 作業状態

`working`又は`next`はGit上の作業状態であり、正式release statusではない。正式なrelease manifest、tag及び配布packageを持たない。

### 6.3 状態遷移の不変性

公開済みmanifestの`status`は発行時の値を保持する。同じpayloadを`release-candidate`から`stable`へ昇格する場合でも、新しいrelease IDとmanifestを発行し、`content_equivalent_to`でcandidateとの同一payloadを示す。これにより、manifest hashに依存するDigital及びReplayを壊さない。

後継発行又はwithdrawalによる現在状態は、Release Catalogへappend-onlyのstatus recordとして追加する。

## 7. Latest Stable、Preview及びArchive

### 7.1 Latest Stable

- stableのうち、ルール所有者が新規利用向けに指定した一件を指す。
- aliasは固定release ID、manifest hash及び更新日時を返す。
- aliasの変更はrelease発行又は明示的な撤回記録に伴って行う。
- 保存データ及びDigital manifestにはaliasではなく解決後の固定値を記録する。

### 7.2 Latest Preview

- 最新のpreview又はrelease-candidateを指す。
- stableと誤認されない表示及びURLを使用する。
- 未解決事項、非収録範囲及び既知の非互換を同じ導線から参照可能にする。

### 7.3 Archive

Archiveは全releaseについて次を保持する。

- release ID、status at issuance及び現在のcatalog status
- `content_commit`、release metadata commitを指すGit tag
- release manifestとそのSHA-256
- release package又は再取得可能な不変URL
- source set snapshot
- change notes、known issues及びwithdrawal notice
- approval evidence
- 対応を宣言したDigital版へのリンク

Archiveは通常参照パスから旧版を外しても削除しない。第三者素材をpackageへ同梱できない場合でも、source ID、hash、取得条件及び権利状態を保持し、同梱不可を明示する。

## 8. Release manifest

### 8.1 責務

Release manifestは、そのreleaseを再現し、内容を検証し、Digital又は外部開発者が依存を固定するための正本台帳である。Release Catalog、Digital manifest及びsource registerの責務を重複させない。

### 8.2 必須項目

| 区分 | 必須項目 |
| --- | --- |
| 識別 | `release_id`、`specification_version`、`status`、`issued_at`、`effective_date` |
| 前後関係 | `supersedes`、`content_equivalent_to`、発行時点の`superseded_by` |
| Git | `content_commit`、`git_tag`、`repository` |
| Freeze evidence | `validated_content_commit`、clean checkout独立実行数、validator fingerprint及び検証結果 |
| Source | `source_set_id`、source set snapshot path、snapshot SHA-256 |
| 規範payload | rules、data、schemas、ID registries、decisions snapshot、各artifact SHA-256 |
| Rule vector | approved vector一覧、件数、集合fingerprint、candidate及び非収録範囲 |
| 統治 | coverage、traceability、field ownership、unresolved snapshot及び各hash |
| 生成物 | Digital JSON、人向けMarkdown、manifest、generator識別子及び各hash |
| 承認 | approver、approval date、approval evidence及びevidence hash |
| 変更 | change notes、breaking change、deprecation、known issues |
| 互換性 | Rule Core schema版、Digital互換性宣言の参照、互換性上の制限 |
| 権利 | license、rights status、同梱可否、第三者素材の参照条件 |

### 8.3 概念例

```yaml
release_id: unassigned
specification_version: 0.9.0
status: release-candidate
issued_at: null
effective_date: null
lineage:
  supersedes: null
  superseded_by: null
  content_equivalent_to: null
git:
  content_commit: null
  tag: null
source_set:
  id: null
  snapshot: null
  sha256: null
normative_payload:
  artifacts: []
  approved_vector_count: null
  approved_vector_fingerprint: null
governance_snapshots:
  decisions: null
  unresolved: null
  coverage: null
  traceability: null
generated_artifacts: []
approval_evidence: []
change_notes: []
known_issues: []
compatibility:
  rule_core_schema_version: null
  digital_declarations: []
```

これはschemaの確定又は現在releaseの発行ではない。`content_commit`はfreeze済みcontentを指し、Manifest自身を含むrelease metadata commitのhashはManifest内部の必須項目にしない。実装時には既存manifest及びSchemaとの移行設計を別途承認する。

### 8.4 Git参照の非循環契約

Releaseの参照関係は次の順とする。

```text
Git tag
  -> release metadata commit
      -> Release Catalog
          -> Manifest path + Manifest hash
              -> content_commit
                  -> frozen Rule Core content
```

- `content_commit`は、technical freeze gateのclean checkout検証対象である。
- technical freeze evidenceの`validated_content_commit`は、Manifestの`content_commit`と一致しなければならない。
- release metadata commitは、最終Manifest及びCatalogを含み、Git tagはこのcommitを指す。
- tag名はRelease IDと同一にする。
- Manifest内部には、Manifest自身を含むrelease metadata commitのhashを必須保持しない。これによりManifestとmetadata commitの自己参照循環を生じさせない。
- release metadata commitから`content_commit`へGit履歴上到達できなければならない。
- technical freezeとrelease metadata確定は別段階とし、freeze後にManifest及びCatalogを生成・承認する。

### 8.5 前方リンクの扱い

発行時点で未来の`superseded_by`は確定できないため、immutable manifestでは`null`を保持する。現在の前方リンクはRelease Catalogのstatus recordで表す。これにより、旧manifestのhashを変更せず、前後版を双方向に検索できる。

## 9. Stable IDの維持及び新規発行

### 9.1 維持する場合

次の場合は既存IDを維持する。

- ファイル移動、ディレクトリ再編又は表示順変更
- 誤字修正又は意味を変えない表現明確化
- source locator、traceability又は補助説明の追加で規範意味が変わらない場合
- 同じ規範概念のmachine-readable representationを追加する場合
- status、approval又はrelease metadataだけを更新する場合

### 9.2 新規IDが必要な場合

次の場合は新規IDを発行し、旧IDをdeprecated又はsupersededとして結び付ける。

- 合法性、条件、主体、対象、数値、処理順、例外、公開範囲又は期待結果の意味が変わる場合
- 一つの概念を複数の独立概念へ分割する場合
- 複数概念を一つへ統合し、旧IDとの一対一対応が失われる場合
- 既存consumerが同じIDのままでは誤った処理を行う非互換変更
- State又はEventの粒度若しくはfield-level visibility契約が変わる場合

### 9.3 禁止事項

- deprecated又は削除済みIDを別概念へ再利用しない。
- ファイルパスをIDの現在意味として解釈しない。
- releaseごとに全IDを採番し直さない。
- 表示名又は翻訳だけの変更で意味IDを変更しない。

registryは`introduced_in`、`deprecated_in`、`supersedes`、`superseded_by`、理由及び移行先を保持する。

## 10. Git運用方式

### 10.1 方式比較

| 方式 | 長所 | 短所 | 判定 |
| --- | --- | --- | --- |
| content commit + metadata commit + tag + immutable manifest | freeze対象とrelease metadataを分離し、自己参照なしで差分、再現、検証及び外部依存を固定できる。 | Git又はrelease配布基盤が必要。 | **推奨する正本方式** |
| releaseごとのdirectory copy | Gitを使わず閲覧しやすい。 | 重複、誤修正、生成物混在、差分困難が増える。 | mainline正本には不採用。配布package内だけ可 |
| release branch | 長期保守版のhotfixに向く。 | 多数の枝で規範が分岐し、どれが現行か不明瞭になる。 | 原則不採用。例外的保守時のみ承認制 |

### 10.2 推奨運用

1. `main`又は指定した統合branchに、次releaseの承認済み変更を統合する。
2. freeze対象commitを`content_commit`候補として固定する。
3. `content_commit`候補をclean checkoutから独立に二回検証し、technical freeze gateの一致を確認する。
4. Release ID及びSpecification Versionを確定し、PASSした`content_commit`を参照するRelease Manifest及びRelease Catalogを生成する。
5. 所有者がchange notes、known issues、unresolved、権利状態、公開範囲、Manifest及びCatalogを承認する。
6. 最終Manifest及びCatalogをrelease metadata commitとしてcommitする。
7. release metadata commitへannotated tagを付ける。tag名はRelease IDと一対一にする。
8. tagからrelease packageを作成し、manifest hashを公開する。
9. 必要なLatest aliasを更新する。

tag、release metadata commit、Manifest、Catalog及び`content_commit`の参照関係が一致しないreleaseは正式発行しない。tagを移動又は再利用しない。

### 10.3 Branchの役割

- 作業branchはNextの作成及びレビューに用いる。
- release branchを版の保管庫として常用しない。
- 旧stableの修正が必要な場合は、対象tagから一時保守branchを作り、修正releaseを新IDで発行する。
- 現行mainの未完成変更を、旧stableの修正packageへ混入させない。

## 11. 公開方式

### 11.1 公開面

公開先は少なくとも次の入口を分離する。

| 入口 | 対象 | 内容 |
| --- | --- | --- |
| Latest Stable | 通常利用者 | 現行stableの概要、release ID、change notes、利用可能な閲覧物 |
| Preview | 開発者・レビュー担当 | 最新preview/RC、非収録範囲、未解決事項、検証状態 |
| Archive | Replay・監査・外部開発者 | 全release、manifest、hash、tag、旧版資料、withdrawal notice |
| Developer | Digital開発者 | Schema、Digital JSON、互換性宣言方法、ID移行情報 |

### 11.2 配布package

配布packageは次を区別する。

- `normative`: 規範rules/data/schema/registry及びmanifest
- `developer`: normativeに加え、Digital JSON、rule vector、生成契約及び検証方法
- `review-evidence`: owner review、approval record、validation report
- `source-reference`: 再配布が許可されたsource又は取得情報

第三者素材又は権利未確認資料を、内部release packageから自動的に公開packageへ含めない。各artifactの公開可否はrights statusで判定する。

### 11.3 URL及び参照

外部開発者向けには、可変Latest URLに加え、release ID及びmanifest hashを含む不変URLを提供する。Digital内の規範表示は対応releaseの固定URLを使い、Latestへ暗黙追随しない。

## 12. Digital互換性宣言

各DigitalはRule Coreの構成品を再列挙せず、少なくとも次を宣言する。

```yaml
rule_core_release_id: null
rule_core_manifest_sha256: null
source_set_id: null
app_version: null
implementation_schema_versions: {}
compatibility_status: untested
tested_vector_sets: []
known_nonconformities: []
```

`compatibility_status`はDigital側の実装事実であり、Rule Coreのstatusを変更しない。少なくとも次を区別する。

- `untested`
- `partial`
- `conformant_for_declared_scope`
- `nonconformant`
- `unsupported`

`partial`又は`conformant_for_declared_scope`は対象Rule Core ID、approved vector集合、除外範囲及び試験証拠を伴う。Digitalが新しいreleaseを読み込めない場合、旧対応releaseを保持し、Rule CoreをDigitalの能力へ合わせて変更しない。

保存及びReplayは、開始時の固定release ID、manifest hash、source set ID及びDigital版を記録する。進行中sessionをLatest Stableへ自動移行しない。

## 13. 承認証拠及び履歴snapshot

### 13.1 原則

owner review、approval evidence、validation report及びfingerprintは、承認時点の内容を示す歴史的snapshotである。後日generatorが変わっても、過去snapshotを現在形式へ上書きしない。

### 13.2 必須メタデータ

各証拠は可能な範囲で次を記録する。

- 対象release ID又は発行前作業snapshot ID
- 対象artifact及びそのhash
- 承認対象ID集合とpayload fingerprint
- 承認者及び承認日
- generator又は作成手順の識別子
- 最新generatorから再現可能か、承認時snapshotとしてのみ保持するか
- 置換元又は後続証拠へのリンク

### 13.3 再生成物との区別

現在の正本から再生成する閲覧物と、承認時点の確認票を同じパスへ上書きしない。必要な場合は`current generated view`と`approval snapshot`を別artifactとしてmanifestへ登録する。

## 14. 新releaseを切る条件

### 14.1 必ず新releaseを発行する変更

- 規範ルール、規範データ、条件、数値、処理順、例外又は公開範囲の変更
- approved rule vectorの追加、削除又は規範payload変更
- decisionの追加、訂正又は廃止でゲーム結果へ影響するもの
- Rule Core ID、Component ID、State ID、Event ID又はinteraction/visibility契約の追加・廃止・意味変更
- source set又はcanonical normative sourceの変更
- Schemaのconsumer互換性へ影響する変更
- 公開済みpackageのartifact byte列を訂正する必要がある場合

### 14.2 内容に応じて新releaseを発行する変更

- traceability、coverage又はsource locatorの修正で、規範意味は不変だが公開packageの監査結果が変わる場合
- generator修正によりDigital JSON又は人向け生成物が変わる場合
- 権利状態又は公開範囲の変更
- 既知問題又は互換性宣言の重大な訂正

この場合、規範payloadが不変であることをfingerprintで示し、patch相当のSpecification Version変更又はmetadata-only releaseであることをchange notesへ記録する。

### 14.3 Rule Core releaseを不要とする変更

- release packageに含まれない内部作業メモ
- 規範及び配布artifactを変えないDigital実装変更
- 同じbyte列を再検証しただけの監査実行
- Next branch上の未承認candidate

ただし、証拠を正式Archiveへ追加する場合はRelease Catalog又はevidence indexの更新履歴を残す。

## 15. Stable昇格条件

Stableは、改訂11の完成判定をrelease単位で満たした場合に限る。最低限、次を確認する。

### 15.1 規範及び出典

- release対象の全規範内容がsource fragment又はapproved decisionへ追跡できる。
- source set、canonical/authoring/derivative/superseded関係及びSHA-256が固定されている。
- 同名別内容、別名同内容、現行版及び権利状態の未解決がrelease範囲へ影響しない。
- 数値、条件、表、記号及びコンポーネント印字の必要な独立照合が完了している。

### 15.2 ID及びSchema

- 全IDが一意で、再利用、重複及び不正なdeprecated参照がない。
- rules、data、schema、registry、generated artifactsの参照整合がある。
- `not_stated`、`not_applicable`、未解決及び非収録を0又は空値で代用していない。

### 15.3 rule vector

- release範囲で`vector_required`となる必要分岐が確認されている。
- stable対象のvectorは所有者承認済みで、承認者、承認日及びpayload fingerprintを持つ。
- 規範YAML、生成物及びvectorの対象ID集合が一致する。
- candidate又はblocked vectorはstable範囲から明示的に除外され、対象範囲を誤表示しない。

### 15.4 生成及び検証

- 全Schema検証、参照整合、manifest hash及び二回生成一致が合格する。
- Manifestの`content_commit`からcleanな環境でfreeze対象contentを検証でき、release metadata commitからManifest、Catalog及びpackageを再構築できる。
- approval evidence及びvalidation reportがmanifestから参照できる。
- 過去release、historical snapshot及び現在state validatorを混同していない。

### 15.5 unresolved及びknown issues

- 勝敗、合法性、資源、判定、処理順又は公開範囲へ影響する未解決事項がstable対象に残っていない。
- 範囲外又は影響しない未解決事項は、known issuesと非収録範囲に明示されている。
- Digital未対応及びlocalization未完成だけを理由にRule Core stableを停止しない。

### 15.6 権利及び承認

- 公開packageに含む各artifactのlicense及びrights scopeが確認されている。
- ルール所有者がrelease内容、change notes、known issues、非収録範囲及び公開先を承認している。
- release ID、tag、manifest hash及び配布package hashが発行記録へ保存されている。

## 16. Superseded及びWithdrawnの保存

### 16.1 Superseded

後継stable発行時、旧stableはcatalog上`superseded`とする。次を維持する。

- 旧tag、release metadata commit、`content_commit`、manifest及びpackage
- 旧source set及び権利情報
- 旧approval evidence及びvalidation report
- 対応Digital版及びReplay参照
- 後継release IDと移行上の注意

通常のLatest Stableからは外すが、依存中のDigital又はReplayへ自動置換しない。

### 16.2 Withdrawn

withdrawnでもartifactを削除せず、次を追加する。

- withdrawal理由
- 影響範囲
- 新規利用停止日
- 推奨後継release
- 既存保存・Replayの取扱い
- 権利問題がある場合の取得制限

機密又は権利上の理由でartifact公開を継続できない場合も、release ID、hash、status record及び除去理由の最小履歴を残す。

## 17. 現在のRule Coreへの適用案

### 17.1 現状の位置づけ

現在のRule Coreは、規範baseline、pipeline、生成物、承認証拠及び複数のpreview相当記録を持つ。したがって、最初の正式release候補を作成できる状態へ近づいているが、本書ではrelease ID、Specification Version、status又は公開日を確定しない。

既存の`0.x-preview-*`記録は作業履歴及びpre-release evidenceとして保持し、後から一つの正式releaseだったことに書き換えない。最初の正式release manifestは、採用する`content_commit`とartifact集合を改めて固定する。

### 17.2 最初の正式releaseまでの残作業

1. 本方針を所有者が承認し、Release ID、Specification Version及びtag命名規則を確定する。
2. release manifest、Release Catalog及び必要なJSON Schemaの最小構造を承認する。
3. 最初のrelease対象範囲、非収録範囲及びeffective dateを確定する。
4. `content_commit`、source set、decision、unresolved、coverage、traceability及びrights statusを凍結する。
5. approved vector集合、fingerprint、candidate/blocked除外及び生成物ID集合を再検証する。
6. clean checkoutから二回生成し、manifest hash及びpackage hashの再現性を確認する。
7. owner review、approval evidence、change notes、known issues及び公開可否を確認する。
8. `preview`又は`release-candidate`として発行するか、Stable条件を満たして`stable`として発行するかを所有者が決定する。
9. 発行後に各Digitalが固定release IDとmanifest hashで対応範囲を宣言する。

### 17.3 最初のreleaseで変更しないもの

- ゲーム規則又は承認済みdecisionの意味
- 承認済みrule vectorの入力及び期待結果
- source fileの内容及び原ファイル名
- Digital固有のUI、AI、保存又は通信方式

## 18. 改訂11との整合及び明確化事項

### 18.1 整合する事項

本方針は改訂11の次の規定と整合する。

- Gitを履歴、差分、tag、生成及び公開の正式な正本として推奨する。
- 旧版はGit履歴とrelease packageで保持し、通常参照パスには現行正本だけを置く。
- Rule Core releaseとDigital対応版を分離する。
- release manifestへversion、source set、artifact hash、`content_commit`及びGit tagを記録する。
- v0.9 previewとv1.xを段階的に公開する。
- Stable IDをファイルパスから独立させ、再利用を禁止する。
- owner approval、rule vector、unresolved、権利及び再現可能生成を公開条件とする。

### 18.2 追加で明確化する事項

| 論点 | 改訂11 | 本方針での明確化 |
| --- | --- | --- |
| 版名 | `v0.9`、`v1.x`を使用 | Specification Versionとして維持し、個別発行は日付ベースRelease IDで識別する。 |
| Latest | 現行正本を通常参照パスへ置く | `Latest Stable`と`Latest Preview`を可変aliasとして分離する。 |
| status変更 | release段階を定義 | 発行済みmanifestを変更せず、Release Catalogのstatus recordでsuperseded/withdrawnを表す。 |
| 前方リンク | superseded関係をregistryへ記録 | 発行時に未知の`superseded_by`はmanifestで`null`、後日catalogで追加する。 |
| approval evidence | 承認記録とmanifestを保持 | 最新generator出力と承認時snapshotを別artifactとして保存する。 |
| 外部依存 | Digitalが対応版を宣言 | aliasではなくrelease IDとmanifest hashを固定し、対応範囲を明示する。 |

### 18.3 競合判定

改訂11との直接の矛盾は確認されない。日付ベースRelease IDは、改訂11のSemantic Versioningを置き換えるものではなく、個々の発行物を不変に識別する追加軸である。

ただし、次は本方針の承認時に明示決定が必要である。

1. Specification Versionを公開名称に併記するか、内部互換性系列としてのみ用いるか。
2. annotated tag名をRelease IDと完全一致させるか、固定prefixを付けるか。
3. Release Catalog及びstatus recordの物理ファイル構成とSchema。
4. metadata-only releaseを通常release ID列へ含めるか、evidence/catalog更新として別管理するか。
5. 最初の正式releaseをpreview、release-candidate又はstableのどの状態で発行するか。

## 19. 推奨事項の要約

- **推奨版番号方式**: 不変な`RC-YYYY.MM.DD-NN` Release IDと、改訂11のSpecification Versionを併用する。
- **推奨lifecycle**: Working/Nextから、preview、release-candidate、stableへ進み、旧stableはcatalog上superseded、重大問題版はwithdrawnとする。
- **推奨Git方式**: `content_commit` + release metadata commit + tag + immutable release manifestを正本とし、directory copy及び常設release branchは正本にしない。
- **推奨公開方式**: Latest Stable、Latest Preview、Archive、Developerの入口を分離し、固定release URLとmanifest hashを提供する。
- **履歴保全**: 発行済みpackage、manifest、approval evidence及びfingerprintは上書きせず、状態変更はappend-only recordで示す。
- **最初の正式release**: 現在のRule Coreを候補として扱えるが、本書だけではrelease ID又はstatusを確定しない。manifest/catalog Schema、対象範囲、権利、Stable条件及び所有者承認を完了してから発行する。
