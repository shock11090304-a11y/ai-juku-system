#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""教材サブスクの Stripe 定期課金（Product → Price → Payment Link）を作る。

    python3 scripts/material_sub/setup_stripe.py                 # 何を作るかを見るだけ（既定）
    STRIPE_SECRET_KEY=sk_live_... python3 scripts/material_sub/setup_stripe.py --apply

★既定は dry-run。`--apply` を付けたときだけ Stripe に実物を作る。
★同じものを二度作らない。metadata.material_id で既存を探して再利用し、
  Idempotency-Key も付ける。作り直したいときは Stripe Dashboard 側で無効化してから回すこと。

■ なぜ metadata.system を juku-payment-material にするのか（★消さないこと）
  この塾には Stripe の webhook を受ける口が 2 つある。
    api/stripe-webhook.py（Vercel・月謝）… system == "juku-payment-monthly" 以外は skip
    server/main.py     （Railway・AIコーチング）… system が "juku-payment" で始まるものを skip
  教材サブスクは**どちらの管理対象でもない**ので、両方に skip させる必要がある。
  system を "material-sub" のような別名にすると main.py 側の skip 条件を外れ、
  **教材サブスクの決済が AI コーチングの購入として students テーブルを書き換える**。
  だからタグは juku-payment で始める。判定の正典は payment/material-subscriptions.json。

■ metadata だけに頼らない（二重の保険）
  Payment Link の metadata が checkout.session.completed にどう載るかは Stripe 側の仕様に依存する。
  そこで体験授業リンク（TAIKEN_TRIAL_PLINK_ID）と同じく **Payment Link の id でも弾く**。
  このスクリプトが出す plink_... を Railway の env MATERIAL_SUB_PLINK_IDS にカンマ区切りで入れること
  （入れ方は最後に印字する）。
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CATALOG = ROOT / "payment" / "material-subscriptions.json"
API = "https://api.stripe.com/v1/"
STRIPE_VERSION = "2024-06-20"
PUBLIC_BASE = os.environ.get("PUBLIC_BASE_URL", "https://www.trillion-ai-juku.com").rstrip("/")


def load_catalog():
    d = json.loads(CATALOG.read_text(encoding="utf-8"))
    tag = d.get("_system_tag", "")
    if not tag.startswith("juku-payment"):
        sys.exit(f"[NG] _system_tag が {tag!r}。juku-payment で始めること"
                 "（両方の webhook の skip 条件から外れ、students テーブルを壊す）")
    return d


def call(key, path, form=None, method="POST", idem=None):
    headers = {"Authorization": f"Bearer {key}", "Stripe-Version": STRIPE_VERSION}
    if method == "POST":
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = urllib.parse.urlencode(form or {}, doseq=True).encode()
        url = API + path
        if idem:
            headers["Idempotency-Key"] = idem
    else:
        data = None
        url = API + path + ("?" + urllib.parse.urlencode(form or {}, doseq=True) if form else "")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        sys.exit(f"[NG] Stripe API {method} {path} → HTTP {e.code}\n{body}")


def find_existing(key, path, material_id, tag):
    """metadata.material_id で既存を探す（二度作らないため）。"""
    try:
        res = call(key, f"{path}/search", {
            "query": f"metadata['material_id']:'{material_id}' AND metadata['system']:'{tag}'",
            "limit": 10,
        }, method="GET")
        for obj in res.get("data", []):
            if not obj.get("deleted") and obj.get("active", True):
                return obj
    except SystemExit:
        raise
    except Exception:
        pass
    return None


def plan(cat):
    """作るものを一覧にする（dry-run でも --apply でも同じ計画を出す）。"""
    tag = cat["_system_tag"]
    out = []
    for it in cat["items"]:
        out.append({
            "material_id": it["id"],
            "product_name": f'トリリオン 教材サブスク／{it["name"]}',
            "price_jpy": it["price"],
            "interval": cat["billing"]["interval"],
            "tag": tag,
            "description": it["summary"],
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="実際に Stripe に作る（既定は見るだけ）")
    a = ap.parse_args()
    cat = load_catalog()
    steps = plan(cat)

    print("=" * 74)
    print(f"教材サブスク / Stripe 定期課金  （{'★本番に作成します' if a.apply else 'dry-run：何も作りません'}）")
    print("=" * 74)
    for s in steps:
        print(f"  {s['material_id']:10s} {s['product_name']}")
        print(f"             ¥{s['price_jpy']:,} / {s['interval']}   metadata.system={s['tag']}")
    print("=" * 74)

    if not a.apply:
        print("\n本番に作るには、Stripe のシークレットキーを渡して --apply を付ける:")
        print("  STRIPE_SECRET_KEY=sk_live_... python3 scripts/material_sub/setup_stripe.py --apply")
        print("\n★ライブキーを使うと本物の課金リンクができます。テストするなら sk_test_ で先に回すこと。")
        return 0

    key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not key:
        sys.exit("[NG] STRIPE_SECRET_KEY が未設定。--apply は使えない")
    live = key.startswith("sk_live_")
    print(f"\nモード: {'LIVE（本番）' if live else 'TEST'}\n")

    results = []
    for s in steps:
        mid, tag = s["material_id"], s["tag"]
        meta = {"metadata[system]": tag, "metadata[material_id]": mid}

        prod = find_existing(key, "products", mid, tag)
        if prod:
            print(f"  [既存] product {prod['id']}  {s['product_name']}")
        else:
            prod = call(key, "products", {
                "name": s["product_name"], "description": s["description"], **meta,
            }, idem=f"matsub-prod-{mid}")
            print(f"  [作成] product {prod['id']}")

        price = None
        for p in call(key, "prices", {"product": prod["id"], "active": "true", "limit": 100},
                      method="GET").get("data", []):
            rec = p.get("recurring") or {}
            if (p.get("unit_amount") == s["price_jpy"] and p.get("currency") == "jpy"
                    and rec.get("interval") == s["interval"]):
                price = p
                break
        if price:
            print(f"  [既存] price   {price['id']}  ¥{s['price_jpy']:,}/{s['interval']}")
        else:
            price = call(key, "prices", {
                "product": prod["id"], "currency": "jpy",
                "unit_amount": str(s["price_jpy"]),
                "recurring[interval]": s["interval"], **meta,
            }, idem=f"matsub-price-{mid}-{s['price_jpy']}")
            print(f"  [作成] price   {price['id']}  ¥{s['price_jpy']:,}/{s['interval']}")

        link = find_existing(key, "payment_links", mid, tag)
        if link:
            print(f"  [既存] link    {link['id']}  {link.get('url')}")
        else:
            link = call(key, "payment_links", {
                "line_items[0][price]": price["id"],
                "line_items[0][quantity]": "1",
                "after_completion[type]": "redirect",
                "after_completion[redirect][url]": f"{PUBLIC_BASE}/checkout-success.html",
                # ★サブスク側にも同じタグを載せる。invoice.* / customer.subscription.* の
                #   イベントでも webhook が skip できるようにするため。
                "subscription_data[metadata][system]": tag,
                "subscription_data[metadata][material_id]": mid,
                **meta,
            }, idem=f"matsub-link-{mid}-{price['id']}")
            print(f"  [作成] link    {link['id']}  {link.get('url')}")
        results.append({"material_id": mid, "product": prod["id"], "price": price["id"],
                        "payment_link": link["id"], "url": link.get("url")})
        print()

    print("=" * 74)
    print("できた申込URL:")
    for r in results:
        print(f"  {r['material_id']:10s} {r['url']}")
    print("=" * 74)
    print("\n★次の 2 つを必ずやること:")
    print("  1) Railway の env に Payment Link の id を入れる（webhook が students を触らないようにする）")
    print(f"     MATERIAL_SUB_PLINK_IDS={','.join(r['payment_link'] for r in results)}")
    print("  2) material-subscription.html の URL を差し替えてコミットする")
    for r in results:
        print(f"     {r['material_id']}: {r['url']}")
    out = ROOT / "payment" / "material-subscriptions.stripe.json"
    out.write_text(json.dumps({"livemode": live, "results": results}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"\n  （作成結果を {out.relative_to(ROOT)} に書きました。id の控えです）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
