# AFWI-KAI Rule Core

AFWI-KAI Rule Coreは、AFWI-KAIのルールを実装非依存の文書、データ、Schema、rule vectorとして扱うための規範仕様です。このrepository候補は公開配布専用であり、private development repositoryで承認・freezeされたRule Core ReleaseとPublication Packageから一方向に生成します。public側で規範を直接編集しません。

## Current formal content

`main`は **Version 1 / revision 0 / formal** のCorrection反映済みcurrent contentです。D1／D2／D3は既存意味の訂正・明確化であり、Version／revisionを変更しません。[Current formal identity / provenance](governance/current-formal.json)及び[作者Decision](governance/decisions.yaml)を参照してください。

`RC-2026.09.27-01 / PUB-2026.09.27-01`は訂正前のhistorical distribution snapshotです。旧tag、Release、manifest及び配布物は不変で、現在の`main`の内容hashを証明するものではありません。以下の旧制度metadataはそのsnapshotについての記録であり、D07 identityとは別です。

## Historical distribution snapshot（2026-09-27）

- Latest Release Candidate: `RC-2026.09.27-01`
- Specification Version: `v0.9.1`
- Publication Package: `PUB-2026.09.27-01`
- Package state: **proposal / unpublished**
- Release status: **Release Candidate**
- Latest Stable: なし
- Approved rule vectors: 141件
- Active Rule Core IDs: 32件
- Normative baseline: `VERIFIED`

これはStable releaseではありません。coverageは宣言範囲ベースであり、AFWI-KAIの全規則を完全収録したものではありません。candidate vector 3件はapproved normative setにもpublic packageにも含まれません。

## Digital compatibility

`Digital compatibility: conformant_for_declared_scope`

確認済みscopeは次の7 Rule Core IDです。

- `RC-TURN-BASE-STAR-PAYMENT-001`
- `RC-CYBER-TARGET-GROUP-MODEL-001`
- `RC-CYBER-TARGET-GROUP-MEMBERSHIP-001`
- `RC-CYBER-TARGET-GROUP-SELECTION-001`
- `RC-CYBER-TARGET-GROUP-PERSISTENCE-001`
- `RC-GEOGRAPHY-NAVAL-BOUNDARIES-001`
- `RC-GEOGRAPHY-PROHIBITED-HEX-MOVEMENT-001`

この表示は、Digital全体またはrepository全体のrelease readinessを意味しません。Digital全体のRC suiteには、既存dirty tree由来のFAILが残っています。本packageはRule Core公開用であり、Digitalアプリのdeploy packageではありません。

## Normative / excluded scope

正確なRule Core ID、Component ID、vector ID、normative scope、excluded scopeは[Release Manifest](generated/releases/RC-2026.09.27-01-release-manifest-final.json)を参照してください。raw source、board PDF、map画像、geography overlay／segment画像、owner review、internal audit、Digitalの`src/`・tests・build artifact・cacheは収録していません。

## Known issues

1. `KNOWN-HISTORICAL-FIXTURE-SOURCE-ATTRIBUTE-HASH` — Legacy save-fixture hash difference caused by the later source attribute.
2. `KNOWN-HISTORICAL-FIXTURE-0910-PAYLOAD-01` — Historical 0910 replay/payload differs from the current reducer.
3. `KNOWN-HISTORICAL-FIXTURE-PLAN-01` — Historical Plan snapshot difference 1.
4. `KNOWN-HISTORICAL-FIXTURE-PLAN-02` — Historical Plan snapshot difference 2.
5. `KNOWN-ENVIRONMENT-WEB-LOCK-TIMEOUT` — Environment-dependent Web Lock timeout.
6. `KNOWN-CREDENTIAL-SCANNER-SHAPE` — Existing credential-shape scanner defect.

上記は宣言済みRule Core scopeのtechnical freezeを妨げない既知事項です。Digital全体のreadinessは別工程です。

## Historical release metadata

- [Release Manifest](generated/releases/RC-2026.09.27-01-release-manifest-final.json)
- [Release Catalog](generated/releases/RC-2026.09.27-01-release-catalog-final.json)
- Content commit: `a8f5f0ab5bb96411142934c45a2b8ff0f0f9fc2f`
- Approved fingerprint: `57e0d74701fc85d955886c60cb616986240a460daa9dce49c0b91189db19b1d2`
- Source aggregate: `6290bc5ff64a44003e34bdd19d7eefb9ebe4d0519aa3b8766c91ce98ce690786`
- Normative Audit fingerprint: `5945bbe6c43c758b9a49a54a08593367efa8fb6989fc445a4262030c848f72e6`

## Download

旧公開snapshotのZIP及び`SHA256SUMS.txt`は[既存GitHub Release](https://github.com/hiroaki-sakanashi/AFWI-KAI-Rule-Core/releases/tag/RC-2026.09.27-01)から取得できます。今回のCorrectionを含む新しい配布artifactは作成していません。

## License

- AFWI-KAI作者が独自に作成・正規化した非software Rule Core: [CC BY-SA 4.0](LICENSES/CC-BY-SA-4.0.txt)
- `pipeline/`配下のRule Core software: [MIT License](LICENSES/MIT.txt)
- 詳細: [LICENSES.md](LICENSES.md) / [NOTICE.md](NOTICE.md)

raw source、画像、第三者素材には上記licenseを自動適用していません。

Copyright © 2026 SAKANASHI Hiroaki  
Attribution: AFWI-KAI Project
