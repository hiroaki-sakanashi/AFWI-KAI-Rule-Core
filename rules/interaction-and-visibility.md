---
title: 判断点と公開範囲
rule_core_version: 0.15.0-preview-squadron-activation
source_set: SRCSET-20260925-RATE-BOUNDARY-001
status: reviewed
license: CC-BY-SA-4.0
last_verified: 2026-09-25
---

# 判断点と公開範囲

本ファイルは改訂11の既存interaction typeだけを用いる。

| 規則・処理 | interaction type | visibility effect |
| --- | --- | --- |
| RC-COMBAT-MD-001 MD宣言判断 | `response_window` | `RC-COMBAT-MD-VISIBILITY-001` |
| RC-COMBAT-MD-RESOLUTION-001 MDロール・結果適用 | `automatic_resolution` | `RC-COMBAT-MD-VISIBILITY-001` |
| RC-COMBAT-MD-LAYERED-001 各MD層 | `response_window` → `automatic_resolution` | `RC-COMBAT-MD-VISIBILITY-001` |
| RC-ENABLER-IMMEDIATE-001 即応 | `response_window` | 使用前手札は非公開。使用時のカード公開開始時点は`not_stated` |
| US-AF-10→RED MD→US-EW-03 | `response_window` → `response_window` → `response_window` → `automatic_resolution` | US-AF-10の使用／不使用をREDが知ってMD判断。MD宣言後は既存MD公開契約 |
| RC-INTEL-ACTIVITY-001 対象選択 | `sequential_action` | 公開結果はpublic |
| RC-INTEL-ACTIVITY-001 捕捉判定 | `automatic_resolution` | 成功時はpublic |
| RC-RATE-CYBER-DOMINANCE-001 | `automatic_resolution` | 対象集合を次ATO中public／capturedにする |
| RC-SQUADRON-DEPLOYMENT-001 | `ordered_setup` | 未捕捉identityは管理陣営限定。開示は`STATE-SQUADRON-ACQUIRED`に従う |
| RC-SQUADRON-ACTIVATION-001 | `sequential_action` | 宣言・予定数・必要／支払★を公開し、未捕捉identityをredact |
| RC-SQUADRON-GENERATION-001 | `automatic_resolution`、配置選択時のみ`sequential_action` | D4・実生成数・地上断念数・生成数・配置hexを公開し、未捕捉identityと個別token対応をredact |
| RC-SQUADRON-RETURN-001 | `automatic_resolution` | 帰還数・帰還元hex・発生を公開し、未捕捉identityと出所対応をredact |

MDから即応、MD解決、攻撃処理へ戻る順序は、各規則とカードtriggerの先後関係で表す。

US-AF-10とMDの順序は`DEC-ENABLER-US-AF-10-MD-TIMING-001`に従う。Rule Coreが定めるのは「判断待ち・即応解決・MD解決・未解決攻撃への復帰」までであり、実装内部の保持方式は規範範囲外である。

### RC-COMBAT-MD-VISIBILITY-001 MD公開契約

Rule: MDの宣言、pass、弾薬消費・消費後残数、適用された判定条件及びMD結果は両陣営へ公開する。使用した個別アセットidentity及び生D4出目は相手陣営へMD処理を理由として追加公開しない。既に別規則で公開済みのidentityは再秘匿しない。  
When: MD response windowの開始から当該MD層の解決及び攻撃処理への復帰まで。レイヤードMDでは各層へ適用する。  
Actor: 公開対象情報を確定するMD処理。選択主体は防御側プレイヤー。  
Target: 宣言又はpass、宣言されたMD層、当該層の対空弾薬、判定条件、D4出目及び結果。  
Cost: not_applicable  
Procedure: 次のvisibility effectを適用する。  
Result: 公開対象は両陣営の既知情報として保持する。相手非公開対象はMD処理だけを理由に公開しない。  
Exceptions: 判定条件の原因となる別の秘密情報は、その情報を規律する別のRule Core契約に従う。STC-RF-05はBLUEのMD宣言公開後、通常のMDロール・結果確定前に応答する。  
Interaction-Type: not_applicable  
Visibility-Effect:
  - item: response_window
    initial_scope: defending_side
    reveal_trigger: response_window_opened
    recipients: [defending_side]
    content: [eligible_side, eligible_MD_asset_choices]
    duration: until_decision_completed
    revoke_trigger: not_applicable
  - item: declaration
    initial_scope: defending_side
    reveal_trigger: EVENT-MD-DECLARED
    recipients: [BLUE, RED]
    content: [MD_declared]
    duration: retained_as_known_information
    revoke_trigger: not_applicable
  - item: pass
    initial_scope: defending_side
    reveal_trigger: EVENT-MD-PASSED
    recipients: [BLUE, RED]
    content: [MD_not_performed]
    duration: retained_as_known_information
    revoke_trigger: not_applicable
  - item: asset_identity
    initial_scope: controlling_side_and_existing_rule_recipients
    reveal_trigger: not_applicable_for_MD
    recipients: [controlling_side, recipients_already_entitled_by_other_rules]
    content: [MD_asset_identity]
    duration: preserve_existing_knowledge_state
    revoke_trigger: not_applicable
  - item: ammunition
    initial_scope: controlling_side
    reveal_trigger: MD_declaration_and_ammunition_payment
    recipients: [BLUE, RED]
    content: [anti_air_ammunition_spent_1, anti_air_ammunition_remaining]
    duration: retained_as_known_information
    revoke_trigger: not_applicable
  - item: raw_D4
    initial_scope: defending_side_and_automatic_resolution
    reveal_trigger: MD_roll_completed
    recipients: [defending_side]
    content: [raw_D4_result]
    duration: retained_as_known_information
    revoke_trigger: not_applicable
  - item: roll_conditions
    initial_scope: automatic_resolution
    reveal_trigger: MD_roll_conditions_fixed
    recipients: [BLUE, RED]
    content: [applied_ADV, applied_DIS, other_applied_roll_conditions]
    duration: retained_as_known_information
    revoke_trigger: not_applicable
    cause_disclosure: governed_by_separate_rule_core_contract
  - item: outcome
    initial_scope: automatic_resolution
    reveal_trigger: EVENT-MD-RESOLVED
    recipients: [BLUE, RED]
    content: [full_intercept, partial_intercept, failure]
    duration: retained_as_known_information
    revoke_trigger: not_applicable
  - item: layered_first_outcome
    initial_scope: automatic_resolution
    reveal_trigger: first_EVENT-MD-RESOLVED
    recipients: [BLUE, RED]
    content: [first_layer_outcome, attack_progress_status]
    duration: before_second_response_window_and_retained_as_known_information
    revoke_trigger: not_applicable
State-IDs: STATE-MD-LAYER-PENDING; STATE-MD-ANTI-AIR-AMMUNITION  
Event-IDs: EVENT-MD-DECLARED; EVENT-MD-PASSED; EVENT-MD-RESOLVED  
Authority-Type: addition_decision  
Source-Fragments: none  
Sources: none  
Decision: DEC-COMBAT-MD-VISIBILITY-001  
Status: approved

### スコードロンactivation field-level visibility

`DEC-SQUADRON-ACTIVATION-VISIBILITY-001`に従い、管理陣営はactivation及びgenerationの全規範fieldを知る。相手陣営には、activation発生、生成予定数、必要・支払★、D4結果、実生成数、地上断念数、生成token数・配置hex及び処理完了を公開する。基地群出撃キャパシティ、航空運用インフラ被害及び整備補給基盤被害は両陣営へ公開する。

未捕捉スコードロンのComponent ID、plate identity、個別token ID及びtokenと出所plateの対応は管理陣営限定とする。相手陣営へのidentity開示は`STATE-SQUADRON-ACQUIRED`と捕捉・インテル規則に従う。通常帰還はtoken数、帰還元hex及び処理発生を公開するが、未捕捉identityと出所対応は公開しない。

State/Eventごとの正確な公開field、管理陣営限定field及びredactionは`data/state-and-event-ids.yaml`を正本とする。Digital内部のcontinuation、stack、resume tokenは規範公開状態ではない。
