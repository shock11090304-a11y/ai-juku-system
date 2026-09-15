#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""教材サブスク（Stripe 定期課金）の機械ゲート。

    python3 scripts/material_sub/check_material_sub.py

★このゲートが守っているのは、いちばん外せない 1 点:
  **教材サブスクの決済が students テーブルを書き換えないこと。**
  Stripe の webhook を受ける口は 2 つあり、それぞれ次の条件で skip する。
     api/stripe-webhook.py（Vercel・月謝）… metadata.system == "juku-payment-monthly" 以外は skip
     server/main.py     （Railway・AIコーチング）… metadata.system が "juku-payment" で始まると skip
  だから教材サブスクのタグは **juku-payment で始めなければならない**。
  "material-sub" のような別名にすると main.py の skip を外れ、教材サブスクの決済が
  「AIコーチングの購入」として students を触る（メールで既存生徒に当たると上書きが起きる）。
  metadata が checkout.session に載らない場合に備えた plink id の保険も、消えていないか見る。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CATALOG = ROOT / "payment" / "material-subscriptions.json"
PAGE = ROOT / "material-subscription.html"
SETUP = ROOT / "scripts" / "material_sub" / "setup_stripe.py"
MAIN = ROOT / "server" / "main.py"
VERCEL_HOOK = ROOT / "api" / "stripe-webhook.py"

# 申込ボタンが受け付けてよい URL の形。★ここを緩めると決済ページを別サイトに向けられる。
URL_RE = re.compile(r"^https://buy\.stripe\.com/[A-Za-z0-9]+$")
REQUIRED = ("id", "name", "price", "tagline", "summary", "features", "level", "stripe_url")
ERR = []


def err(m):
    ERR.append(f"[NG] {m}")


def main():
    if not CATALOG.exists():
        err(f"カタログが無い: {CATALOG}")
        print("\n".join(ERR))
        return 1
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    page = PAGE.read_text(encoding="utf-8") if PAGE.exists() else ""
    setup = SETUP.read_text(encoding="utf-8") if SETUP.exists() else ""
    main_py = MAIN.read_text(encoding="utf-8") if MAIN.exists() else ""
    hook = VERCEL_HOOK.read_text(encoding="utf-8") if VERCEL_HOOK.exists() else ""

    # ---------- ① いちばん外せない: system タグ ----------
    tag = cat.get("_system_tag", "")
    if not tag.startswith("juku-payment"):
        err(f"_system_tag が {tag!r}。**juku-payment で始めること**。"
            "外すと server/main.py の skip に掛からず、教材サブスクの決済が students を書き換える")
    if 'startswith("juku-payment")' not in main_py:
        err("server/main.py の webhook から startswith(\"juku-payment\") の skip が消えている")
    if '"juku-payment-monthly"' not in hook:
        err("api/stripe-webhook.py の月謝判定が変わっている（教材サブスクが月謝として処理される恐れ）")
    # plink id の保険
    if "MATERIAL_SUB_PLINK_IDS" not in main_py:
        err("server/main.py の MATERIAL_SUB_PLINK_IDS（plink id による二重の保険）が消えている")
    if 'handled": "material_subscription"' not in main_py:
        err("server/main.py の教材サブスク divert 分岐が消えている")
    # setup スクリプトがタグをカタログから取っているか（べた書きしていないか）
    if setup and '_system_tag' not in setup:
        err("setup_stripe.py がカタログの _system_tag を読んでいない（タグのべた書きは禁止）")

    # ---------- ② カタログの中身 ----------
    items = cat.get("items") or []
    if not items:
        err("items が空")
    ids = set()
    for i, it in enumerate(items):
        w = f'items[{i}] ({it.get("id", "?")})'
        for k in REQUIRED:
            if k not in it:
                err(f"{w}: {k} が無い")
        if it.get("id") in ids:
            err(f"{w}: id が重複")
        ids.add(it.get("id"))
        p = it.get("price")
        if not isinstance(p, int) or p <= 0:
            err(f"{w}: price が整数の正の値でない: {p!r}")
        elif p % 1 != 0:
            err(f"{w}: 円は最小単位。小数は使えない")
        u = it.get("stripe_url", "")
        if u and not URL_RE.match(u):
            err(f"{w}: stripe_url が buy.stripe.com の形でない: {u!r}")
        if not (it.get("features") or []):
            err(f"{w}: features が空")
    if cat.get("billing", {}).get("interval") != "month":
        err("billing.interval が month でない（定期課金の単位）")
    if not (cat.get("billing", {}).get("note") or "").strip():
        err("billing.note（更新と解約の説明）が空。申込画面に出す文言なので必須")

    # ---------- ③ 画面が正典を読んでいるか ----------
    if not page:
        err(f"申込ページが無い: {PAGE}")
    else:
        if "payment/material-subscriptions.json" not in page:
            err("申込ページがカタログを読んでいない（価格のべた書きは表示と請求のズレを生む）")
        # 価格のべた書き検出: ¥3,000 のような表記が固定で入っていないか
        for it in items:
            for lit in (f'¥{it["price"]:,}', f'{it["price"]}円', str(it["price"])):
                if lit in re.sub(r"<script[\s\S]*?</script>", "", page):
                    err(f"申込ページに価格 {lit} がべた書きされている（カタログから描くこと）")
                    break
        if "buy\\.stripe\\.com" not in page:
            err("申込ページに Stripe URL の形の検査が無い（別サイトへ誘導されうる）")
        if "legal.html" not in page:
            err("申込ページから特定商取引法に基づく表記（legal.html）への導線が無い")
        for must in ("解約", "返金", "自動更新"):
            if must not in page:
                err(f"申込ページに「{must}」の説明が無い（定期課金の表示として必要）")
        # ★申込画面のリンク切れは「押しても何も起きない」で終わるので機械で止める。
        #   contact.html を書いて実在しなかった（この塾の問い合わせは mailto）。
        # ★<script> の中はテンプレート文字列（href="${...}"）なので除く。
        page_html = re.sub(r"<script[\s\S]*?</script>", "", page)
        for href in re.findall(r'href="(?!https?:|mailto:|#)([^"]+)"', page_html):
            if not (ROOT / href.split("?")[0].split("#")[0]).exists():
                err(f"申込ページのリンク先が無い: {href}")

    # ---------- 集計 ----------
    ready = [i for i in items if i.get("stripe_url")]
    print("=" * 70)
    print(f"教材サブスク {len(items)} 件 / system タグ: {tag}")
    for it in items:
        u = it.get("stripe_url") or "（未作成：画面は「準備中」を出す）"
        print(f"  {it.get('id','?'):10s} ¥{it.get('price',0):,}/月  {it.get('name','')}  {u}")
    print(f"申込URL が入っているもの: {len(ready)}/{len(items)}")
    print("=" * 70)
    if not ready:
        print("[info] まだ Stripe に作っていない。作るには:")
        print("  STRIPE_SECRET_KEY=sk_... python3 scripts/material_sub/setup_stripe.py --apply")
    if ERR:
        print(f"\n*** 検査に通らなかった項目 {len(ERR)} 件 ***")
        for e in ERR:
            print(e)
        return 1
    print("NG 0 件 / ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
