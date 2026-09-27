from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "rule-core"
GENERATOR = "rule-core/pipeline/generate-immediate-enablers-expansion-artifacts.py"
NEW_CODES = ["US-AB-05", "US-EW-03", "US-AF-05", "US-AF-10", "US-IW-01", "US-IW-04", "US-IW-07", "STC-IW-01", "STC-IW-04"]
VECTOR_SOURCE = RC / "tests/rule-vectors/immediate-enablers-expansion.yaml"
DATA_SOURCE = RC / "data/enablers.yaml"
OUT_MD = RC / "generated/reviews/immediate-enablers-expansion-owner-review.md"
OUT_JSON = RC / "generated/reviews/immediate-enablers-expansion-owner-review.json"
REF_MD = RC / "generated/immediate-enablers-expansion-reference.md"
DIGITAL_JSON = RC / "generated/digital/immediate-enablers-expansion.json"
MANIFEST = RC / "generated/digital/immediate-enablers-expansion-manifest.json"

FP_FIELDS = ["vector_id", "rule_core_ids", "component_id", "source_fragment_ids", "initial_state", "operation", "fixed_randomness", "expected_events", "expected_final_state", "duration", "visibility", "interaction_type"]
PRE_APPROVAL_FINGERPRINTS = {
    "RV-ENABLER-US-AB-05-TRIGGER-001": "748a5464f807294313a956ba672a2089234336eee5fa6bf497d0e90c9d118634",
    "RV-ENABLER-US-AB-05-NO-TRIGGER-001": "1278054df62e02ef40221a621131b58ba486386bd9a845f0f99cac9df86a1bac",
    "RV-ENABLER-US-EW-03-TRIGGER-001": "d7b61813888ed58bc3a93984797d850d06320df4f52aecb572af56b12e794488",
    "RV-ENABLER-US-EW-03-NO-TRIGGER-001": "31cd1f58beb3e4fcc0c009a8127bda7b87039f238b9038270af926664afdd946",
    "RV-ENABLER-US-AF-05-TRIGGER-001": "52f077bb430184b8ad6a4b85dd10c609546186cc0ad17bcccb036e1ec3b9bd7f",
    "RV-ENABLER-US-AF-05-NO-TRIGGER-001": "9c0f416789189f2fa378d2b77a55d184a878747fa592c1a2f7bcd70fb27e7837",
    "RV-ENABLER-US-AF-10-TRIGGER-001": "9b5f03fe8ba0257debaa7ceb75f22d82e10cbf5fd327b8e9c381cad8b8d7224b",
    "RV-ENABLER-US-AF-10-NO-TRIGGER-001": "dac774bc16ec693fbc2c9fdf069b03c7c5fedb10786cad47841c7b33af7cede8",
    "RV-ENABLER-US-IW-01-TRIGGER-001": "e1f84789fc667a653d4e784ef1ad78547e307523a283a3024f7d286eba185bc8",
    "RV-ENABLER-US-IW-01-NO-TRIGGER-001": "3834462b4dbd575fa685c836b00cad9fdc645a3ce1f71359eb19b64966bfac79",
    "RV-ENABLER-US-IW-04-TRIGGER-001": "befe8b319ae408f81a4882ef9345d970e61ae008e1d0c8cc80093dd937674859",
    "RV-ENABLER-US-IW-04-NO-TRIGGER-001": "7458931dac2a8c2bac0d07e2e28cd0e0369548d4d29d30b690dafb32f62504bb",
    "RV-ENABLER-US-IW-07-TRIGGER-001": "e4d09f0c674735abd6f8230a1e10d702205e7adfc1729f9089fde1098f24c16f",
    "RV-ENABLER-US-IW-07-NO-TRIGGER-001": "a873568d89ff35428829e5cde92ab05cde5005503f0b81b29101dfc1761ba810",
    "RV-ENABLER-STC-IW-01-TRIGGER-001": "b51f18f1294454ffe55e426f87dc304bd546d393f061a35379724729f299ce95",
    "RV-ENABLER-STC-IW-01-NO-TRIGGER-001": "336f3595590ed8152f4faaa88f6b8d9e8bdc084e6cb807ded2c77ee87b2070ba",
    "RV-ENABLER-STC-IW-04-TRIGGER-001": "16cc5b3e95da56b54f89385bc68150ad2f0ad1e6bc2be70b396b8f654abc3699",
    "RV-ENABLER-STC-IW-04-NO-TRIGGER-001": "b2ba55a90d6d6630d48f4f0f7957ebe66389288659b43c9442a26fd0af32730d",
    "RV-ENABLER-US-AB-05-EFFECT-001": "d5eccdf0ca9e1ba6bc646c885e690dac585e3c643d089878c8282ed8bb3159db",
    "RV-ENABLER-US-EW-03-EFFECT-001": "44380d4dc81b41aede318e0f3490ba5ff18a3e35f7a7e00753a93b6ddc36ef5a",
    "RV-ENABLER-US-AF-05-EFFECT-001": "bb6fd4d5fd6283f798d50334d7e83952ad343420548da339e28653ab9cc9a6e5",
    "RV-ENABLER-US-AF-10-EFFECT-001": "17753d467a42c5b25115a41e87bc079e95470e20788c30f6dd54de49ff4849a7",
    "RV-ENABLER-US-IW-01-EFFECT-001": "c9f4b9ef3d92a130db7ceb7f77fb5036b252756ea8f98e65400b69dc2ca384a1",
    "RV-ENABLER-US-IW-04-SUCCESS-001": "f2593a11f7df8a586f147aad44dfbece84bfad4ee05ecdca49c56acd2c0cffe1",
    "RV-ENABLER-US-IW-04-FAILURE-001": "59945e482fe6dd4b4e583ef6a386b7123e1b364cc08919de795c247f53c19e82",
    "RV-ENABLER-US-IW-07-EFFECT-001": "70bc9f3fd0e00111dd86c1ac16173b46ce8ed12a213ba10b94b32aa61942ea24",
    "RV-ENABLER-STC-IW-01-EFFECT-001": "17095c51ea0906c15682c511b340bfea952b287de4cbd71b695d40d96aa22ae8",
    "RV-ENABLER-STC-IW-04-SUCCESS-001": "f03feb5f6e9d8b278ec7b5d7924ba95beb18f37de407e51f80a98ef5f82a1141",
    "RV-ENABLER-STC-IW-04-FAILURE-001": "6628890ada194d142385c912a77541ad888226f1f4d332b9ac0dbb668f68017b",
}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def component_id(vector: dict) -> str:
    return vector["operation"].get("component_id") or vector["initial_state"]["holder_has_component"]


def fingerprint(vector: dict) -> str:
    payload = {key: (component_id(vector) if key == "component_id" else vector.get(key)) for key in FP_FIELDS}
    return hashlib.sha256(canonical(payload)).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


PAGE_BY_CODE = {"US-AB-05": 45, "US-EW-03": 49, "US-AF-05": 52, "US-AF-10": 54, "US-IW-01": 55, "US-IW-04": 56, "US-IW-07": 58, "STC-IW-01": 59, "STC-IW-04": 62}

CARD_TEXT = {
    "US-AB-05": {
        "summary": "REDによる対地攻撃の命中ロールが成功した直後、ダメージロール前に使用します。この時点ではhit数はまだ決まっていません。効果により、当該攻撃から生じるhitをすべて無効にします。",
        "timing": "REDの対地攻撃の命中ロールが成功した直後、かつダメージロールを始める前です。命中前やダメージ解決後には使用できません。",
        "faction": "BLUE（US）側のカード保持者が使用します。", "target": "命中ロールに成功した当該RED対地攻撃と、その攻撃から生じるすべてのhitです。",
        "process": "カードを使用すると、ダメージロールを行うかどうかにかかわらず、当該攻撃から生じるhitをすべて無効にし、有効なhit数を0にします。", "determination": "このカードには追加の判定はありません。ダメージロールそのものを必ず省略するという規則は、この承認内容には含まれません。",
        "success": "成功・失敗の分岐はありません。使用すれば全hitを無効にします。", "failure": "成功・失敗の分岐はありません。",
        "duration": "当該攻撃のhitを無効にする即時効果です。", "disposition": "使用後は捨て札にします（使い切り）。",
        "visibility": "カード印字には公開開始時点の明記がありません。", "not_decided": "同じタイミングで他の即応も成立した場合の選択・解決順は今回確定しません。",
    },
    "US-EW-03": {
        "summary": "REDがMDを宣言した直後、D4によるMD判定の前に使用し、宣言されたMD1回（1層）だけを自動失敗させるカードです。STC-RF-05の陣営を反転した効果です。",
        "timing": "REDがMDを宣言した直後、D4によるMD判定を行う前です。", "faction": "BLUE（US）側のカード保持者が使用します。",
        "target": "直前にREDが宣言したMD1回（1層）だけです。", "process": "カードを使用すると、対象のMD層についてD4を振らず、自動失敗（迎撃突破）として処理します。他のMD層へは波及しません。",
        "determination": "このカードには追加の判定はありません。対象MD層のD4判定も行いません。", "success": "成功・失敗の分岐はなく、対象MD層を自動失敗にします。",
        "failure": "成功・失敗の分岐はありません。", "duration": "宣言された当該MD1層だけに適用する即時効果です。", "disposition": "使用後は捨て札にします（使い切り）。",
        "visibility": "カード印字には公開開始時点の明記がありません。", "not_decided": "別のMD層の処理や、同時に成立する他の即応の順序は今回確定しません。",
    },
    "US-AF-05": {
        "summary": "RED基地への対地攻撃を宣言したときに使用し、命中ロールを省略して、その出目を4として扱うカードです。ダメージロールは通常どおり行います。",
        "timing": "RED基地に対する対地攻撃を宣言した時点です。", "faction": "BLUE（US）側のカード保持者が使用します。", "target": "宣言したRED基地への当該対地攻撃です。",
        "process": "命中ロールは振らず、命中ロールの出目を4として扱います。その後のダメージロールは通常どおり行います。",
        "determination": "命中ロールは行いません。出目4を採用するための追加判定もありません。", "success": "成功・失敗の分岐ではなく、出目4として命中処理へ進みます。",
        "failure": "このカード固有の失敗分岐はありません。", "duration": "当該攻撃の命中処理だけに適用します。", "disposition": "使用後は捨て札にします（使い切り）。",
        "visibility": "カード印字には公開開始時点の明記がありません。", "not_decided": "出目4として扱った後の通常ダメージ処理そのものは、この確認票では変更しません。",
    },
    "US-AF-10": {
        "summary": "自軍航空機トークンがADAを攻撃するとき、その攻撃をADV（有利）にするカードです。",
        "timing": "自軍航空機トークンがADAを攻撃するときです。", "faction": "BLUE（US）側のカード保持者が使用します。", "target": "当該航空機トークンによるADAへの攻撃です。",
        "process": "当該攻撃の判定をADV（有利）にします。", "determination": "カード使用のための追加判定はありません。実際の攻撃判定はADVとして行います。",
        "success": "成功・失敗の分岐はありません。使用した攻撃がADVになります。", "failure": "このカード固有の失敗分岐はありません。",
        "duration": "当該攻撃の間だけ有効です。", "disposition": "使用後は再選択可能なカードとして扱います。", "visibility": "カード印字には公開開始時点の明記がありません。",
        "not_decided": "攻撃結果そのものはこの確認票では変更しません。US-AF-10判断、REDのMD判断、US-EW-03応答、MD処理、未解決攻撃への復帰順はDEC-ENABLER-US-AF-10-MD-TIMING-001で確定しています。",
    },
    "US-IW-01": {
        "summary": "兆候マーカーを配置するとき、偽兆候マーカー2枚を紫ライン以東へ配置し、当日終了まで手札に保持するカードです。",
        "timing": "兆候マーカーの配置時です。", "faction": "BLUE（US）側のカード保持者が使用します。", "target": "紫ライン以東へ配置する偽兆候マーカー2枚です。",
        "process": "偽兆候マーカー2枚を紫ライン以東へ配置し、このカードを当日終了まで手札に保持します。", "determination": "このカードには追加の判定はありません。",
        "success": "成功・失敗の分岐はありません。", "failure": "成功・失敗の分岐はありません。", "duration": "カードは当日終了まで手札に保持します。",
        "disposition": "当日終了後は再選択可能なカードとして扱います。", "visibility": "カード印字には公開開始時点の明記がありません。",
        "not_decided": "紫ライン以東72ヘックスの地理候補は独立二回一致していますが、境界・area・効果vectorは所有者未承認です。複数即応の順序も確定しません。",
    },
    "US-IW-04": {
        "summary": "PRCによる基地群攻撃の命中判定が失敗した直後にD4を振り、2以上なら戦略レートをBLUE方向へ1動かすカードです。",
        "timing": "PRCの基地群攻撃の命中判定が失敗した直後です。", "faction": "BLUE（US）側のカード保持者が使用します。", "target": "共有の戦略レートです。",
        "process": "D4を1回振ります。出目が2以上なら戦略レートをBLUE方向へ1動かし、1なら変更しません。", "determination": "D4の出目が2以上なら成功です。",
        "success": "戦略レートをBLUE方向へ1動かします。", "failure": "戦略レートは変更しません。", "duration": "判定結果を直ちに適用します。",
        "disposition": "使用後は再選択可能なカードとして扱います。", "visibility": "カード印字には公開開始時点の明記がありません。",
        "not_decided": "この変動から別の即応が連鎖する場合の選択・解決順は今回確定しません。",
    },
    "US-IW-07": {
        "summary": "自軍のインテル活動開始時に公開して発動し、その活動を含め、当日終了まで自軍が行うスコードロン捕捉判定をすべて自動成功にするカードです。",
        "timing": "自軍のインテル活動を開始したときです。", "faction": "BLUE（US）側のカード保持者が使用します。", "target": "発動の契機となった活動を含む、当日中の自軍スコードロン捕捉判定です。",
        "process": "カードを公開して発動し、対象となるスコードロン捕捉判定をD4なしで自動成功にします。", "determination": "対象のスコードロン捕捉判定は自動成功となるため、判定ダイスを振りません。",
        "success": "対象となる自軍スコードロン捕捉判定はすべて成功します。", "failure": "このカードが有効な間、対象判定の失敗分岐はありません。",
        "duration": "発動の契機となったインテル活動を含め、当日終了まで有効です。", "disposition": "当日終了後は再選択可能なカードとして扱います。",
        "visibility": "発動時にカードを公開します。", "not_decided": "自動成功をインテル活動全体や別種の判定へ拡張しません。両陣営のインテル活動順も今回確定しません。",
    },
    "STC-IW-01": {
        "summary": "兆候マーカーを配置するとき、偽兆候マーカー2枚を橙ライン以西へ配置し、当日終了まで手札に保持するカードです。",
        "timing": "兆候マーカーの配置時です。", "faction": "RED（PRC）側のカード保持者が使用します。", "target": "橙ライン以西へ配置する偽兆候マーカー2枚です。",
        "process": "偽兆候マーカー2枚を橙ライン以西へ配置し、このカードを当日終了まで手札に保持します。", "determination": "このカードには追加の判定はありません。",
        "success": "成功・失敗の分岐はありません。", "failure": "成功・失敗の分岐はありません。", "duration": "カードは当日終了まで手札に保持します。",
        "disposition": "当日終了後は再選択可能なカードとして扱います。", "visibility": "カード印字には公開開始時点の明記がありません。",
        "not_decided": "橙ラインはH行以南で単一経路を一意に追跡できず、配置可能ヘックス集合と効果ケースは承認対象外です。複数即応の順序も確定しません。",
    },
    "STC-IW-04": {
        "summary": "戦略レートがREDに不利な方向へ1点変動した直後にD4を振り、出目がREDサイバーレート以下なら、まず直前の不利な変動を打ち消し、続いて戦略レートをRED方向へ1動かすカードです。",
        "timing": "戦略レートがREDに不利な方向へ1点変動した直後です。", "faction": "RED（PRC）側のカード保持者が使用します。", "target": "直前のREDに不利な戦略レート変動と、共有の戦略レートです。",
        "process": "D4を1回振ります。成功時は、(1)直前の不利な1点変動を打ち消し、(2)さらに戦略レートをRED方向へ1動かします。この二つを順に適用します。",
        "determination": "D4の出目が現在のREDサイバーレート以下なら成功です。", "success": "直前の不利な変動を打ち消したうえで、戦略レートをRED方向へ1動かします。",
        "failure": "直前の不利な変動を打ち消さず、その変動を残します。RED方向への追加変動も行いません。", "duration": "判定結果を直ちに適用します。",
        "disposition": "使用後は捨て札にします（使い切り）。", "visibility": "カード印字には公開開始時点の明記がありません。",
        "not_decided": "このカードが連鎖的に成立する場合の選択・解決順は今回確定しません。",
    },
}

EFFECT_CASES = {
    "RV-ENABLER-US-AB-05-EFFECT-001": ("RED対地攻撃から生じる全hitを無効にする場合", ["BLUE側がUS-AB-05を保持しています。", "REDによる対地攻撃の命中ロールは成功しています。", "ダメージロールはまだ行われていません。", "この攻撃によるhit数はまだ決まっていません。"], "BLUE側が、命中ロール成功直後かつダメージロール前にUS-AB-05を使用します。", "このケースではダイスを振りません。", ["US-AB-05を使い切りにします。", "当該攻撃から生じるhitをすべて無効にします。"], ["当該攻撃による有効なhit数は0です。", "他の攻撃や他のカードの状態は変更しません。"]),
    "RV-ENABLER-US-EW-03-EFFECT-001": ("宣言されたREDのMD1層だけを自動失敗にする場合", ["BLUE側がUS-EW-03を保持しています。", "REDは海軍MDの1層を宣言済みです。", "別のADA層も存在しますが、D4判定はまだ始まっていません。"], "BLUE側がUS-EW-03を使用し、宣言された海軍MD層を指定します。", "このケースではMD判定のD4を振りません。", ["カードの使用を記録します。", "指定した海軍MD層を自動失敗として確定します。"], ["指定した海軍MD層だけが失敗になります。", "ADA層の状態は変わりません。", "カードは捨て札になります。"]),
    "RV-ENABLER-US-AF-05-EFFECT-001": ("命中ロールを省略して出目4を採用する場合", ["BLUE側がUS-AF-05を保持しています。", "攻撃対象はRED基地です。", "命中ロールはまだ始まっていません。"], "BLUE側がUS-AF-05を使用します。", "命中ロールは振らず、出目4を固定して採用します。", ["カードの使用を記録します。", "命中ロールを省略し、出目4として命中処理を行います。", "その後のダメージロールは通常どおり行います。"], ["命中ロールは実施されません。", "採用する命中ロールの出目は4です。", "ダメージロールの手順は変更されません。", "カードは捨て札になります。"]),
    "RV-ENABLER-US-AF-10-EFFECT-001": ("自軍航空機のADA攻撃をADV（有利）にする場合", ["BLUE側がUS-AF-10を保持しています。", "自軍航空機トークンがADAを攻撃します。", "攻撃判定はまだ通常状態です。"], "BLUE側がUS-AF-10を使用します。", "このケースではカード効果のためのダイスを振りません。", ["カードの使用を記録します。", "当該攻撃の判定をADV（有利）にします。"], ["当該攻撃の判定条件はADVになります。", "カードは再選択可能な状態になります。"]),
    "RV-ENABLER-US-IW-04-SUCCESS-001": ("US-IW-04の判定に成功する場合", ["BLUE側がUS-IW-04を保持しています。", "PRC基地群攻撃の命中判定が失敗しました。", "変更前の戦略レートをSとします。"], "BLUE側がUS-IW-04を使用して判定します。", "D4の出目を2に固定して確認します。", ["カードの使用を記録します。", "出目2は成功条件の2以上を満たします。", "戦略レートをBLUE方向へ1動かします。"], ["戦略レートはSからBLUE方向へ1変化します。", "カードは再選択可能な状態になります。"]),
    "RV-ENABLER-US-IW-04-FAILURE-001": ("US-IW-04の判定に失敗する場合", ["BLUE側がUS-IW-04を保持しています。", "PRC基地群攻撃の命中判定が失敗しました。", "変更前の戦略レートをSとします。"], "BLUE側がUS-IW-04を使用して判定します。", "D4の出目を1に固定して確認します。", ["カードの使用を記録します。", "出目1は成功条件の2以上を満たしません。", "戦略レートを変更しません。"], ["戦略レートはSのままです。", "カードは再選択可能な状態になります。"]),
    "RV-ENABLER-US-IW-07-EFFECT-001": ("当該活動を含む当日の捕捉判定を自動成功にする場合", ["BLUE側がUS-IW-07を保持しています。", "自軍のインテル活動を開始します。"], "BLUE側がUS-IW-07を公開して使用します。", "対象となるスコードロン捕捉判定ではダイスを振りません。", ["カードの使用を記録し、公開します。", "発動の契機となった活動の捕捉判定を自動成功にします。", "同じ日の後続の自軍スコードロン捕捉判定も自動成功にします。", "当日終了時に効果を終了します。"], ["当日中の対象捕捉判定は自動成功になります。", "翌日には効果を持ち越しません。", "カードは再選択可能な状態になります。"]),
    "RV-ENABLER-STC-IW-04-SUCCESS-001": ("STC-IW-04の判定に成功する場合", ["RED側がSTC-IW-04を保持しています。", "戦略レートがREDに不利なBLUE方向へ1動きました。", "変動前の戦略レートをS、REDサイバーレートを3とします。"], "RED側がSTC-IW-04を使用して判定します。", "D4の出目を3に固定して確認します。", ["カードの使用を記録します。", "出目3はREDサイバーレート3以下なので成功です。", "最初に、直前のBLUE方向への1点変動を打ち消します。", "次に、戦略レートをRED方向へ1動かします。"], ["直前の不利な変動は無効になります。", "戦略レートは変動前のSからRED方向へ1変化します。", "カードは捨て札になります。"]),
    "RV-ENABLER-STC-IW-04-FAILURE-001": ("STC-IW-04の判定に失敗する場合", ["RED側がSTC-IW-04を保持しています。", "戦略レートがREDに不利なBLUE方向へ1動きました。", "変動前の戦略レートをS、REDサイバーレートを2とします。"], "RED側がSTC-IW-04を使用して判定します。", "D4の出目を3に固定して確認します。", ["カードの使用を記録します。", "出目3はREDサイバーレート2以下ではないため失敗です。", "直前の変動を打ち消さず、RED方向への追加変動も行いません。"], ["直前のBLUE方向への1点変動は残ります。", "戦略レートはSからBLUE方向へ1変化した状態です。", "カードは捨て札になります。"]),
}

GEO_CASES = {
    "RV-ENABLER-US-IW-01-EFFECT-001": ("偽兆候2枚を紫ライン以東へ配置する場合", ["BLUE側がUS-IW-01を保持しています。", "兆候マーカーの配置時です。", "紫ライン以東のcandidate areaは72ヘックスです。"], "BLUE側がUS-IW-01を使用し、偽兆候マーカー2枚を配置しようとします。", "このケースではダイスを振りません。", ["カード印字にある枚数と範囲表現を確認します。", "候補areaの72ヘックス集合を参照します。"], ["偽兆候マーカーの枚数は2枚です。", "カードは当日終了まで手札に保持します。", "配置可能候補はAREA-EAST-OF-BLUE-GENERATION-WESTERN-LIMITの72ヘックスです。"]),
    "RV-ENABLER-STC-IW-01-EFFECT-001": ("偽兆候2枚を橙ライン以西へ配置する場合", ["RED側がSTC-IW-01を保持しています。", "兆候マーカーの配置時です。", "承認済み橙ライン完全経路と、その以西51ヘックスを参照します。"], "RED側がSTC-IW-01を使用し、偽兆候マーカー2枚を配置しようとします。", "このケースではダイスを振りません。", ["カード印字にある枚数と範囲表現を確認します。", "配置可能ヘックス集合としてAREA-WEST-OF-RED-GENERATION-EASTERN-LIMITの51ヘックスを参照します。"], ["偽兆候マーカーの枚数は2枚です。", "カードは当日終了まで手札に保持します。", "配置可能範囲はAREA-WEST-OF-RED-GENERATION-EASTERN-LIMITの51ヘックスです。"]),
}


def collect_ids(value, prefix: str) -> list[str]:
    found = set()
    if isinstance(value, dict):
        for item in value.values():
            found.update(collect_ids(item, prefix))
    elif isinstance(value, list):
        for item in value:
            found.update(collect_ids(item, prefix))
    elif isinstance(value, str) and value.startswith(prefix):
        found.add(value)
    return sorted(found)


def trigger_case(rv: dict, text: dict) -> tuple[str, list[str], str, str, list[str], list[str]]:
    is_no_trigger = "-NO-TRIGGER-" in rv["vector_id"]
    if is_no_trigger:
        return ("カードの使用条件を満たさない場合", ["カード保持者は当該カードを手札に持っています。", "カードに印字された使用タイミングまたは条件は成立していません。"], "カードを使用せず、使用機会が成立するかを確認します。", "このケースではダイスを振りません。", ["印字条件が成立していないため、このカードの使用判断の機会を開始しません。", "カード固有効果も適用しません。"], ["カードは使用可能になりません。", "カードが参照する対象・レート・攻撃・判定の状態は変わりません。"])
    return ("カードの使用条件を満たす場合", ["カード保持者は当該カードを手札に持っています。", text["timing"]], "カード保持者が、このカードを使用するか判断します。", "このケースではダイスを振りません。", ["印字されたtriggerが成立したことを確認します。", "カード保持者に使用するかどうかの判断機会を与えます。", "このケースではカード固有効果そのものはまだ解決しません。"], ["このカードを使用できる状態になります。", "使用するかどうかはカード保持者の判断として残ります。"])


def case_text(rv: dict, card_text: dict):
    if "-TRIGGER-" in rv["vector_id"]:
        return trigger_case(rv, card_text)
    if rv["vector_id"] in EFFECT_CASES:
        return EFFECT_CASES[rv["vector_id"]]
    return GEO_CASES[rv["vector_id"]]


def append_case(md: list[str], rv: dict, vector: dict, card_text: dict, blocked: bool = False) -> None:
    heading, initial, action, dice, process, final = case_text(rv, card_text)
    md += [f"### 確認ケース：{heading}", "", "**最初の状態**", ""]
    md += [f"- {line}" for line in initial]
    md += ["", "**プレイヤーが行うこと**", "", action, "", "**固定するダイス目**", "", dice, "", "**期待される処理**", ""]
    md += [f"1. {line}" for line in process]
    md += ["", "**処理後の状態**", ""] + [f"- {line}" for line in final]
    not_checked = card_text["not_decided"]
    if "-TRIGGER-" in rv["vector_id"]:
        not_checked += " このtrigger境界ケースでは、カード固有効果の結果までは確認しません。"
    if blocked:
        not_checked += " 検証済み地理IDがないため、このケースは今回の承認対象外です。"
    if rv["status"] == "approved":
        answers = ["- [x] この記述で正しい（2026-09-24 ルール所有者承認）", "- [ ] 修正が必要", "- [ ] 現時点では承認できない"]
    else:
        answers = ["- [ ] この記述で正しい", "- [ ] 修正が必要", "- [ ] 現時点では承認できない"]
    dependency = "blocked_by_geography" if blocked else ("eligible_for_owner_review" if rv["status"] == "candidate" else "approved")
    md += ["", "**このケースで確認しないこと**", "", not_checked, "", "**回答欄**", "", *answers, "", "**技術的な追跡情報**", "", f"- vector ID: `{rv['vector_id']}`", f"- Component ID: `{rv['component_id']}`", f"- Rule Core ID: {', '.join(f'`{x}`' for x in rv['rule_core_ids'])}", f"- State ID: {', '.join(f'`{x}`' for x in collect_ids(vector, 'STATE-')) or '該当なし'}", f"- Event ID: {', '.join(f'`{x}`' for x in collect_ids(vector, 'EVENT-')) or '該当なし'}", f"- source fragment: {', '.join(f'`{x}`' for x in rv['source_fragment_ids'])}", f"- source page: `SRC-ENABLER-0830-1 p.{PAGE_BY_CODE[rv['component_id'].removeprefix('COMP-ENABLER-')]}`", f"- 承認前fingerprint: `{rv['pre_approval_fingerprint_sha256']}`", f"- 現在のfingerprint: `{rv['fingerprint_sha256']}`", f"- fingerprint変更: `{'changed' if rv['fingerprint_changed'] else 'unchanged'}`", f"- status: `{rv['status']}`", f"- approved by / at: `{rv['approval']['approved_by']}` / `{rv['approval']['approved_at']}`", f"- dependency status: `{dependency}`", ""]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-only", action="store_true", help="確認票Markdown/JSONだけを再生成する")
    args = parser.parse_args()
    data = load_yaml(DATA_SOURCE)
    vectors_doc = load_yaml(VECTOR_SOURCE)
    cards = [c for c in data["components"] if c["source_card_code"] in NEW_CODES]
    cards.sort(key=lambda c: NEW_CODES.index(c["source_card_code"]))
    vectors = vectors_doc["vectors"]
    reviews = []
    for vector in vectors:
        cid = component_id(vector)
        blocked = False
        reviewability = "blocked_by_geography" if blocked else ("approved" if vector["status"] == "approved" else "eligible_for_owner_review")
        current_fingerprint = fingerprint(vector)
        reviews.append({
            "vector_id": vector["vector_id"], "title": vector["title"], "component_id": cid,
            "status": vector["status"], "reviewability": reviewability,
            "initial_state": vector["initial_state"], "operation": vector["operation"], "fixed_randomness": vector["fixed_randomness"],
            "expected_events": vector["expected_events"], "expected_final_state": vector["expected_final_state"],
            "duration": vector["duration"], "visibility": vector["visibility"], "interaction_type": vector["interaction_type"],
            "rule_core_ids": vector["rule_core_ids"], "source_fragment_ids": vector["source_fragment_ids"],
            "pre_approval_fingerprint_sha256": PRE_APPROVAL_FINGERPRINTS[vector["vector_id"]],
            "fingerprint_sha256": current_fingerprint,
            "fingerprint_changed": current_fingerprint != PRE_APPROVAL_FINGERPRINTS[vector["vector_id"]],
            "approval": vector["approval"],
        })
    card_reviews = []
    for card in cards:
        card_reviews.append({
            "component_id": card["component_id"], "source_card_code": card["source_card_code"], "card_name": card["card_name"],
            "faction": card["side"], "trigger": card["trigger"], "actor": card["actor"], "target": card["target"],
            "determination": card["determination"], "effect": card["effect"], "duration": card["duration"],
            "consumption": card["consumption"], "card_state": card["card_state"], "interaction_type": card["interaction_type"],
            "status": card["status"],
            "visibility": card["visibility_effect"], "source_fragment_ids": card["source_fragment_ids"],
            "candidate_vector_ids": [r["vector_id"] for r in reviews if r["component_id"] == card["component_id"]],
            "dependencies": [],
            "not_stated": ([] if card["visibility_effect"] != "not_stated" else ["visibility"]),
        })
    simultaneous = [
        {"question": "STC-NV-07とSTC-NV-08の同時成立", "status": "approved_decision", "related": ["DEC-ENABLER-NV-MULTIPLE-001により両方使用可、REDが順序を決め、1枚ずつ解決。対象消失時の後続は未発動。"]},
        {"question": "判定のないカードへのサイバー対抗", "status": "approved_decision", "related": ["DEC-ENABLER-CYBER-COUNTER-SCOPE-001により効果のない対抗カードは使用不可。"]},
        {"question": "ミュトスとサイバーカウンターメジャー", "status": "approved_decision", "related": ["Day1・2は対抗不可。Day3以降はADVとDISを相殺して通常D4。"]},
        {"question": "US-AF-10とMD判断", "status": "approved_decision", "related": ["DEC-ENABLER-US-AF-10-MD-TIMING-001によりAF-10判断→RED MD判断→US-EW-03応答→MD→攻撃復帰。"]},
    ]
    review = {
        "schema_version": "0.1.0", "review_type": "immediate_enablers_expansion_owner_review", "non_normative": True,
        "generated_at": "2026-09-24T00:00:00+09:00", "generator": GENERATOR,
        "card_count": len(cards), "vector_count": len(vectors), "trigger_vector_count": 18, "effect_vector_count": 11,
        "approved_count": sum(r["status"] == "approved" for r in reviews),
        "geography_reviewable_count": sum(r["reviewability"] == "eligible_for_owner_review" for r in reviews),
        "geography_blocked_count": sum(r["reviewability"] == "blocked_by_geography" for r in reviews),
        "approval_record": {"approved_by": "ルール所有者", "approved_at": "2026-09-24", "approved_vector_count": 29, "candidate_vector_count": 0, "corrected_vector_id": "RV-ENABLER-US-AB-05-EFFECT-001", "pre_correction_fingerprint_sha256": PRE_APPROVAL_FINGERPRINTS["RV-ENABLER-US-AB-05-EFFECT-001"], "post_correction_fingerprint_sha256": next(r["fingerprint_sha256"] for r in reviews if r["vector_id"] == "RV-ENABLER-US-AB-05-EFFECT-001"), "geography_approval": {"vector_id": "RV-ENABLER-STC-IW-01-EFFECT-001", "normative_payload_fingerprint_before": next(r["fingerprint_sha256"] for r in reviews if r["vector_id"] == "RV-ENABLER-STC-IW-01-EFFECT-001"), "normative_payload_fingerprint_after": next(r["fingerprint_sha256"] for r in reviews if r["vector_id"] == "RV-ENABLER-STC-IW-01-EFFECT-001")}},
        "fingerprint_method": {"algorithm": "SHA-256", "serialization": "canonical JSON; UTF-8; object keys sorted; array order preserved; null explicit; no insignificant whitespace", "fields": FP_FIELDS},
        "cards": card_reviews, "vectors": reviews, "simultaneous_timing_review": simultaneous,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    vector_by_id = {v["vector_id"]: v for v in vectors}
    md = ["# 未収録即応カード9枚 ルール所有者承認記録", "", "> 本確認票は規範正本ではありません。承認結果は元のrule vectorへ反映済みです。", "", "## 第1部：確認方法と承認結果", "", "この確認票では、未収録だった9枚の即応カードを1枚ずつ確認します。各カードについて、カード印字の転記内容と、その内容を試すrule vectorをまとめて掲載しています。", "", "- ルール所有者は、US-AB-05の訂正、US-IW-01地理効果、STC-IW-01地理効果を含む29件すべてを2026-09-24に承認しました。", "- STC-IW-01地理効果は、承認済み橙ライン完全経路45辺と以西51ヘックスへ接続しています。", "- 9枚のカード印字転記とtrigger dataは承認済みです。", "- 複数の即応が同時または連鎖して成立する場合の選択・解決順は、今回決めていません。", "", "## 第2部：カード別確認", ""]
    for card in card_reviews:
        text = CARD_TEXT[card["source_card_code"]]
        md += [f"## {card['card_name']}（{card['source_card_code']}）", "", text["summary"], "", "### カード名・カードコード", "", f"{card['card_name']}（`{card['source_card_code']}`）", "", "### このカードを使えるタイミング", "", text["timing"], "", "### 使用する陣営", "", text["faction"], "", "### 対象", "", text["target"], "", "### 使用したときの処理", "", text["process"], "", "### 判定方法", "", text["determination"], "", "### 成功した場合", "", text["success"], "", "### 失敗した場合", "", text["failure"], "", "### 効果の持続期間", "", text["duration"], "", "### 使用後のカードの扱い", "", text["disposition"], "", "### 公開状態", "", text["visibility"], "", "### 今回確定しない事項", "", text["not_decided"], "", "### 確認対象vector", ""]
        eligible = [r for r in reviews if r["component_id"] == card["component_id"] and r["reviewability"] == "approved"]
        for rv in eligible:
            append_case(md, rv, vector_by_id[rv["vector_id"]], text)
        md += ["### ルール所有者回答欄", "", "- [x] このカードの転記内容は正しい（2026-09-24 ルール所有者承認）", "- [ ] 修正が必要", "- [ ] 現時点では承認できない", "", "確認者：ルール所有者", "", "確認日：2026-09-24", "", "### カードの技術的な追跡情報", "", f"- Component ID: `{card['component_id']}`", f"- source fragment: `{card['source_fragment_ids'][0]}`", f"- source page: `SRC-ENABLER-0830-1 p.{PAGE_BY_CODE[card['source_card_code']]}`", f"- card transcription status: `{card['status']}`", f"- trigger data status: `approved`", f"- geographic effect coverage: `{'pending' if card['dependencies'] else 'not_applicable'}`", ""]
    md += ["## 第3部：地理効果の承認記録", "", "US-IW-01の紫ライン以東72ヘックスとeffect vector、およびSTC-IW-01の橙ライン完全45辺・以西51ヘックスとeffect vectorは、いずれも2026-09-24承認済みです。", ""]
    md += ["## 第4部：複数即応の選択・解決順", "", "前回未確定だったSTC-NV-07／08、サイバー対抗範囲、US-AF-10とMDの順序は、2026-09-24の追加裁定3件で確定しました。裁定を検証する14件も同日にルール所有者が承認済みです。", ""]
    for item in simultaneous:
        md += [f"- **{item['question']}** — {' / '.join(item['related'])}"]
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    if args.review_only:
        return
    DIGITAL_JSON.parent.mkdir(parents=True, exist_ok=True)
    digital = {"schemaVersion": "0.1.0", "status": "approved", "nonNormativeCandidate": True,
               "componentIds": [c["component_id"] for c in cards], "components": cards,
               "approvedVectorIds": [v["vector_id"] for v in vectors if v["status"] == "approved"],
               "candidateVectorIds": [v["vector_id"] for v in vectors if v["status"] == "candidate"], "vectors": vectors}
    DIGITAL_JSON.write_text(json.dumps(digital, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ref = ["# 即応イネーブラー追加9枚 データ参照", "", "> 規範正本ではありません。`data/enablers.yaml`から生成した参照です。9枚のカード転記は2026-09-24にルール所有者が承認しています。", "", "- 承認済みvector: 29件", "- 地理依存による保留: 0件", ""]
    for card in card_reviews:
        ref += [f"## {card['source_card_code']} — {card['card_name']}", "", f"- Component ID: `{card['component_id']}`", f"- faction: `{card['faction']}`", f"- trigger: `{dump(card['trigger'])}`", f"- Actor: `{card['actor']}`", f"- Target: `{dump(card['target'])}`", f"- 判定: `{dump(card['determination'])}`", f"- effect: `{dump(card['effect'])}`", f"- duration: `{dump(card['duration'])}`", f"- consumption / state: `{card['consumption']}` / `{card['card_state']}`", f"- interaction type / visibility: `{card['interaction_type']}` / `{card['visibility']}`", f"- source fragment: `{card['source_fragment_ids'][0]}`", ""]
    REF_MD.write_text("\n".join(ref), encoding="utf-8")
    manifest = {"schemaVersion": "0.1.0", "manifestStatus": "candidate", "ruleCoreVersion": "0.11.0-preview-vrc", "sourceSet": "SRCSET-20260923-INITIAL", "generatorVersion": "1.0.0", "digitalContractVersion": "0.1.0", "minDigitalVersion": None, "maxTestedDigitalVersion": None,
                "artifacts": [{"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path), "role": role} for path, role in [
                    (DATA_SOURCE, "normative_data"), (VECTOR_SOURCE, "rule_vector_approved"),
                    (RC / "governance/source-fragment-register.yaml", "governance"),
                    (RC / "governance/component-id-registry.yaml", "governance"),
                    (RC / "governance/coverage.yaml", "governance"),
                    (RC / "governance/traceability.yaml", "traceability"),
                    (RC / "governance/rule-id-registry.yaml", "governance"),
                    (RC / "governance/field-ownership.yaml", "governance"),
                    (RC / "governance/immediate-enablers-expansion-validation-report.md", "governance"),
                    (REF_MD, "generated_human_reference"), (DIGITAL_JSON, "digital_candidate"),
                    (OUT_MD, "generated_human_reference"), (OUT_JSON, "governance")]]}
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
