#!/usr/bin/env python3
"""外部向け月額プランの価格 同期チェック (2026-11-12・トリリオン AI学習アプリ 月¥2,500 の追加に合わせて新設)

`scripts/check_course_price_sync.py` が照合するのは通塾生の料金 (payment/courses.json ⇄ api/register-subscribe.py)
だけで、外部向けの月額プラン (AIコーチング) はどの検査にも入っていなかった。外部向けの値段は次の場所に分かれて書いてあり、
ずれると「画面で見た値段」と「実際にカードから引き落とす金額」が食い違う = 請求事故になる:

  server/main.py   PRICE_MAP           … 実際に Stripe へ渡す金額・表示名 (正)
                   PLAN_QUOTAS         … 月の上限 (問題生成 / 添削 / 参考書)
                   ENROLLMENT_FEE_EXEMPT / webhook の _VALID_PLAN_KEYS / LIGHT_TRIAL_DAYS
  plans.js         PLAN_CONFIG.plans / aiApp / studentAddon … 画面の値段・上限
  light.html       トリリオン AI学習アプリの申込ページ (受付スイッチ LIGHT_SIGNUP_ENABLED)
  legal.html       特定商取引法に基づく表記

検査すること (引数なし = 手元のファイルだけ。ネットワークに出ない):
  1. plans.js の各プランの price == PRICE_MAP の金額 (founder_special / premium / family / standard / studentAddon / aiApp)
  2. plans.js の quotas == PLAN_QUOTAS (standard / aiApp)
  3. trillion_light: 入塾金なし (ENROLLMENT_FEE_EXEMPT)・webhook の _VALID_PLAN_KEYS に入っている・
     体験日数 (LIGHT_TRIAL_DAYS 既定値) == plans.js aiApp.trialDays
  4. light.html: 月額は 2,500円だけを書いている (3,000円などの旧値が残っていない)・体験日数が一致・
     「永年」「先行50名」を書いていない (2026-11-12 塾長決定)
  5. legal.html: このプランの行があれば金額が一致すること。
     ★light.html の受付スイッチが true なのに legal.html に行が無ければ失敗 (表記なしで売らない)
--stripe を付けたときだけ:
  6. Stripe の lookup_key=trillion_light の価格が 2,500円・JPY・月払いか (読むだけ。env STRIPE_SECRET_KEY が要る)

Exit code:
  0  : 一致
  1  : 不一致を検出 (請求事故リスク・要修正)
  2  : ファイル不在 / 読み込み失敗
"""

import ast
import os
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
MAIN_PY = ROOT / "server" / "main.py"
PLANS_JS = ROOT / "plans.js"
LIGHT_HTML = ROOT / "light.html"
LEGAL_HTML = ROOT / "legal.html"

LIGHT_KEY = "trillion_light"
LIGHT_LABEL = "トリリオン AI学習アプリ"

PASS = "\033[32m✅\033[0m"
FAIL = "\033[31m❌\033[0m"
WARN = "\033[33m⚠️\033[0m"


def _module_assign(tree, name):
    """モジュール直下の `name = ...` の値ノードを返す (最後の代入)。"""
    node = None
    for st in tree.body:
        if isinstance(st, ast.Assign):
            for t in st.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    node = st.value
    return node


def load_server(src: str):
    """server/main.py をサーバを起動せずに読む (import すると DB 初期化が走るので ast で読む)。"""
    tree = ast.parse(src)
    out = {}
    pm = _module_assign(tree, "PRICE_MAP")
    if not isinstance(pm, ast.Dict):
        raise ValueError("PRICE_MAP が見つかりません")
    prices = {}
    for k, v in zip(pm.keys, pm.values):
        key = ast.literal_eval(k)
        if not isinstance(v, ast.Tuple) or len(v.elts) < 4:
            raise ValueError(f"PRICE_MAP['{key}'] の形が (price_id, 金額, 表示名, 人数) ではありません")
        prices[key] = {"amount": ast.literal_eval(v.elts[1]), "name": ast.literal_eval(v.elts[2])}
    out["PRICE_MAP"] = prices
    pq = _module_assign(tree, "PLAN_QUOTAS")
    out["PLAN_QUOTAS"] = ast.literal_eval(pq) if pq is not None else {}
    ex = _module_assign(tree, "ENROLLMENT_FEE_EXEMPT")
    out["ENROLLMENT_FEE_EXEMPT"] = set(ast.literal_eval(ex)) if ex is not None else set()
    # webhook の中のローカル変数なので正規表現で読む
    m = re.search(r"_VALID_PLAN_KEYS\s*=\s*\{([^}]*)\}", src, re.S)
    out["VALID_PLAN_KEYS"] = set(re.findall(r'"([a-z0-9_]+)"', m.group(1))) if m else set()
    for _name in ("LIGHT_TRIAL_DAYS", "LIGHT_ESSAYS_PER_MONTH", "LIGHT_TRIAL_ESSAYS", "LIGHT_CURRICULUM_PER_MONTH"):
        m = re.search(_name + r'\s*=\s*_env_int\(\s*"' + _name + r'"\s*,\s*(\d+)', src)
        out[_name] = int(m.group(1)) if m else None
    return out


def _js_block(src: str, key: str, start_at: int = 0):
    """`key: {` から対応する `}` までの文字列 (入れ子の {} を数える)。無ければ None。"""
    m = re.compile(r"(^|\n)\s*" + re.escape(key) + r"\s*:\s*\{").search(src, start_at)
    if not m:
        return None
    i = m.end() - 1
    depth = 0
    for j in range(i, len(src)):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return src[i:j + 1]
    return None


def _js_num(block: str, field: str):
    m = re.search(r"(^|[\s,{])" + re.escape(field) + r"\s*:\s*(\d+)", block)
    return int(m.group(2)) if m else None


def _js_quotas(block: str):
    q = _js_block(block, "quotas")
    if q is None:
        return None
    out = {}
    for k in ("problems", "essays", "textbooks"):
        m = re.search(r"\b" + k + r"\s*:\s*(null|\d+)", q)
        out[k] = None if (not m or m.group(1) == "null") else int(m.group(1))
    return out


def load_plans_js(src: str):
    plans_block = _js_block(src, "plans")
    if plans_block is None:
        raise ValueError("PLAN_CONFIG.plans が見つかりません")
    out = {}
    for key in ("founder_special", "premium", "family", "standard"):
        b = _js_block(plans_block, key)
        if b is not None:
            out[key] = {"price": _js_num(b, "price"), "quotas": _js_quotas(b)}
    for js_key, server_key in (("studentAddon", "student_addon"), ("aiApp", LIGHT_KEY)):
        b = _js_block(src, js_key)
        if b is not None:
            out[server_key] = {"price": _js_num(b, "price"), "quotas": _js_quotas(b),
                               "trialDays": _js_num(b, "trialDays"), "trialEssays": _js_num(b, "trialEssays"),
                               "curriculumPerMonth": _js_num(b, "curriculumPerMonth"),
                               "id": (re.search(r"id:\s*'([^']+)'", b) or [None, None])[1]}
    # aiApp を plans の中に置くと lp.html の料金カードに出てしまう (公開前に値段が出る)
    #   ★キー名だけでなく、aiApp ブロックごと移した場合 (aiApp: / id: 'trillion_light') も拾う
    out["_light_in_plans"] = bool(re.search(r"(^|\n)\s*" + LIGHT_KEY + r"\s*:\s*\{", plans_block)
                                  or re.search(r"(^|\n)\s*aiApp\s*:", plans_block)
                                  or re.search(r"['\"]" + LIGHT_KEY + r"['\"]", plans_block))
    return out


def _yen_amounts(text: str):
    """「2,500円」「¥2,500」の金額を全部拾う。"""
    vals = [int(x.replace(",", "")) for x in re.findall(r"(\d{1,3}(?:,\d{3})+|\d{3,})\s*円", text)]
    vals += [int(x.replace(",", "")) for x in re.findall(r"[¥￥]\s*(\d{1,3}(?:,\d{3})+|\d{3,})", text)]
    return vals


def _visible_text(html: str) -> str:
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", html)


def check_stripe(expected_amount: int, errors: list):
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key:
        errors.append("--stripe: env STRIPE_SECRET_KEY がありません (Stripe の価格を確かめられない)")
        return
    try:
        import stripe  # noqa
    except Exception:
        errors.append("--stripe: stripe パッケージがありません (pip install stripe)")
        return
    stripe.api_key = key
    res = stripe.Price.list(lookup_keys=[LIGHT_KEY], active=True, limit=5)
    data = list(res.data or [])
    if not data:
        errors.append(f"Stripe: lookup_key={LIGHT_KEY} の有効な価格がありません (受付を開ける前に作る)")
        return
    if len(data) > 1:
        errors.append(f"Stripe: lookup_key={LIGHT_KEY} の有効な価格が {len(data)} 件あります (1件にする)")
    p = data[0]
    rec = getattr(p, "recurring", None) or {}
    interval = rec.get("interval") if isinstance(rec, dict) else getattr(rec, "interval", None)
    count = rec.get("interval_count") if isinstance(rec, dict) else getattr(rec, "interval_count", None)
    problems = []
    if p.unit_amount != expected_amount:
        problems.append(f"金額 {p.unit_amount} (期待 {expected_amount})")
    if (p.currency or "").lower() != "jpy":
        problems.append(f"通貨 {p.currency}")
    if interval != "month" or (count not in (None, 1)):
        problems.append(f"周期 {interval}×{count} (期待 month×1)")
    if problems:
        errors.append(f"Stripe: {p.id} が一致しません: " + " / ".join(problems))
    else:
        print(f"  {PASS} Stripe {p.id}: ¥{p.unit_amount:,} / 月 (livemode={p.livemode})")


def main():
    want_stripe = "--stripe" in sys.argv[1:]
    print("=" * 64)
    print("  💴 外部向け月額プラン 価格同期チェック (server/main.py ⇄ plans.js ⇄ light.html ⇄ legal.html)")
    print("=" * 64)
    missing = [p for p in (MAIN_PY, PLANS_JS, LIGHT_HTML, LEGAL_HTML) if not p.exists()]
    if missing:
        for p in missing:
            print(f"  {FAIL} ファイルが見つかりません: {p}")
        return 2
    try:
        server = load_server(MAIN_PY.read_text(encoding="utf-8"))
        pjs = load_plans_js(PLANS_JS.read_text(encoding="utf-8"))
        light_src = LIGHT_HTML.read_text(encoding="utf-8")
        legal_src = LEGAL_HTML.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  {FAIL} 読み込みに失敗: {type(e).__name__}: {e}")
        return 2

    errors, warns = [], []
    prices = server["PRICE_MAP"]
    if not prices or not pjs:
        print(f"  {FAIL} PRICE_MAP か plans.js が空です — 読み込みに失敗している可能性があります")
        return 2

    # 1. 金額
    print("\n── 金額 (plans.js ⇄ PRICE_MAP) ──")
    for key in ("founder_special", "premium", "family", "standard", "student_addon", LIGHT_KEY):
        if key not in prices:
            errors.append(f"PRICE_MAP に '{key}' がありません")
            continue
        if key not in pjs:
            errors.append(f"plans.js に '{key}' がありません")
            continue
        sp, jp = prices[key]["amount"], pjs[key]["price"]
        if sp != jp:
            errors.append(f"'{key}' の金額が不一致: PRICE_MAP=¥{sp:,} / plans.js=¥{jp}")
        else:
            print(f"  {PASS} {key}: ¥{sp:,} ({prices[key]['name']})")

    # 2. 上限
    print("\n── 月の上限 (plans.js ⇄ PLAN_QUOTAS) ──")
    for key in ("standard", LIGHT_KEY):
        sq = server["PLAN_QUOTAS"].get(key)
        jq = (pjs.get(key) or {}).get("quotas")
        if sq is None or jq is None:
            errors.append(f"'{key}' の上限が片方にしかありません: PLAN_QUOTAS={sq} / plans.js={jq}")
        elif sq != jq:
            errors.append(f"'{key}' の上限が不一致: PLAN_QUOTAS={sq} / plans.js={jq}")
        else:
            print(f"  {PASS} {key}: {sq}")

    # 3. trillion_light の配線
    print(f"\n── {LIGHT_KEY} の配線 ──")
    light_amount = prices.get(LIGHT_KEY, {}).get("amount")
    if prices.get(LIGHT_KEY, {}).get("name") != LIGHT_LABEL:
        errors.append(f"PRICE_MAP['{LIGHT_KEY}'] の表示名が '{LIGHT_LABEL}' ではありません: {prices.get(LIGHT_KEY, {}).get('name')!r}")
    if LIGHT_KEY not in server["ENROLLMENT_FEE_EXEMPT"]:
        errors.append(f"ENROLLMENT_FEE_EXEMPT に '{LIGHT_KEY}' がありません (入塾金なしの約束と食い違う)")
    if LIGHT_KEY not in server["VALID_PLAN_KEYS"]:
        errors.append(f"webhook の _VALID_PLAN_KEYS に '{LIGHT_KEY}' がありません (新規の決済で生徒が作られない)")
    if pjs.get(LIGHT_KEY, {}).get("id") != LIGHT_KEY:
        errors.append(f"plans.js aiApp.id が '{LIGHT_KEY}' ではありません")
    if pjs.get("_light_in_plans"):
        errors.append(f"plans.js の plans の中に '{LIGHT_KEY}' があります (lp.html の料金カードに出てしまう。aiApp に置く)")
    td_s, td_j = server["LIGHT_TRIAL_DAYS"], pjs.get(LIGHT_KEY, {}).get("trialDays")
    if td_s is None or td_s != td_j:
        errors.append(f"体験日数が不一致: LIGHT_TRIAL_DAYS={td_s} / plans.js aiApp.trialDays={td_j}")
    _aj = pjs.get(LIGHT_KEY, {})
    for _sname, _jname, _jval in (
        ("LIGHT_ESSAYS_PER_MONTH", "quotas.essays", (_aj.get("quotas") or {}).get("essays")),
        ("LIGHT_TRIAL_ESSAYS", "trialEssays", _aj.get("trialEssays")),
        ("LIGHT_CURRICULUM_PER_MONTH", "curriculumPerMonth", _aj.get("curriculumPerMonth")),
    ):
        if server.get(_sname) is None or server.get(_sname) != _jval:
            errors.append(f"回数の上限が不一致: {_sname}={server.get(_sname)} / plans.js aiApp.{_jname}={_jval}")
    if not errors:
        print(f"  {PASS} 入塾金なし・webhook の有効キー・体験 {td_s}日間・添削 体験{server.get('LIGHT_TRIAL_ESSAYS')}回/月{server.get('LIGHT_ESSAYS_PER_MONTH')}回・学習計画 月{server.get('LIGHT_CURRICULUM_PER_MONTH')}回")

    # 4. light.html
    print("\n── light.html (申込ページ) ──")
    vis = _visible_text(light_src)
    amounts = [a for a in _yen_amounts(vis) if a not in (0, 10000)]  # 10,000円 = 「入塾金はかかりません」の説明
    bad = sorted({a for a in amounts if a != light_amount})
    if light_amount not in amounts:
        errors.append(f"light.html に月額 {light_amount:,}円 の表記がありません")
    if bad:
        errors.append(f"light.html に月額と違う金額があります: {', '.join(f'{a:,}円' for a in bad)}")
    if td_s and f"{td_s}日間" not in vis:
        errors.append(f"light.html に「{td_s}日間」の無料体験の表記がありません")
    for word in ("永年", "先行50名", "先行 50 名", "50名限定"):
        if word in vis:
            errors.append(f"light.html に「{word}」が残っています (2026-11-12 塾長決定: 永年・先着の枠は付けない)")
    if "トリリオン・ライト" in vis:
        errors.append("light.html に旧名「トリリオン・ライト」が残っています")
    m = re.search(r"var\s+PLAN_KEY\s*=\s*'([^']+)'", light_src)
    if not m or m.group(1) != LIGHT_KEY:
        errors.append(f"light.html の PLAN_KEY が '{LIGHT_KEY}' ではありません")
    sw = re.search(r"var\s+LIGHT_SIGNUP_ENABLED\s*=\s*(true|false)\s*;", light_src)
    signup_on = bool(sw and sw.group(1) == "true")
    if not sw:
        errors.append("light.html の受付スイッチ LIGHT_SIGNUP_ENABLED が読めません")
    print(f"  {'🟢' if signup_on else '⏸'} 受付スイッチ LIGHT_SIGNUP_ENABLED = {signup_on}")
    if signup_on and 'name="robots" content="noindex' in light_src:
        warns.append("受付中なのに light.html に noindex が残っています (検索に出ません)")

    # 5. legal.html
    print("\n── legal.html (特商法表記) ──")
    if LIGHT_LABEL in legal_src:
        lines = [ln for ln in _visible_text(legal_src).splitlines() if LIGHT_LABEL in ln]
        amts = sorted({a for ln in lines for a in _yen_amounts(ln)})
        if light_amount not in amts:
            errors.append(f"legal.html の「{LIGHT_LABEL}」の行に {light_amount:,}円 がありません (見つかった金額: {amts})")
        else:
            print(f"  {PASS} legal.html に {LIGHT_LABEL} {light_amount:,}円 の行あり")
    elif signup_on:
        errors.append(f"light.html の受付が開いているのに legal.html に「{LIGHT_LABEL}」の行がありません (特商法の表記なしで売らない)")
    else:
        warns.append(f"legal.html にまだ「{LIGHT_LABEL}」の行がありません (受付を開ける前に足す・塾長の「変えて」の後)")

    if want_stripe:
        print("\n── Stripe (読むだけ) ──")
        check_stripe(light_amount, errors)

    print("\n" + "=" * 64)
    for w in warns:
        print(f"  {WARN} {w}")
    if errors:
        print(f"  🔴 {FAIL} {len(errors)} 件の不一致を検出しました")
        for e in errors:
            print(f"     {FAIL} {e}")
        return 1
    print(f"  🎉 {PASS} 外部向け月額プランの金額・上限・{LIGHT_KEY} の配線が一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
