#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英検準1級 二次面接カードの4コマイラストを gpt-image-1 で1枚(4コマ合成)生成→PNG保存。
実行: railway run -s ai-juku-api python3 scripts/eiken_nijikai_gp1/gen_figure.py <card_key> <out.png>
  OPENAI_API_KEY を env から読む。1枚 約$0.04〜0.08(サイズ/品質による)。
  文字は画像に描かせない(DALL-E系は英文綴りが崩れる)→吹き出し/時間句はアプリ側のテキストで併記。
"""
import os, sys, json, base64, urllib.request, urllib.error

# 4コマの各beatを1枚の漫画にまとめる英語プロンプト(人物を毎コマ同一文言で固定・文字禁止)
STYLE = ("A single four-panel educational comic strip arranged in a 2x2 grid with clear thin panel borders. "
         "Simple clean black-and-white line art, Japanese textbook / educational manga style, flat, minimal shading. "
         "IMPORTANT: absolutely no text, no words, no letters, no numbers, no writing on signs, screens, or speech bubbles anywhere in the image. "
         "Keep the SAME characters consistent across all four panels. ")

# slug → (topic_en, prompt)。topic_en は cards_ja.json と突合するキー。
CARDS = {
    "edtech": ("Technology in Schools", STYLE + (
        "Characters: a middle-aged male school principal in a dark suit; several teachers; a group of junior-high students including ONE specific boy with short black hair and a school uniform (same boy in panels 2,3,4). "
        "Panel 1 (top-left): in a school staff room, the principal stands before the seated teachers and holds up a tablet device; the teachers smile and nod. "
        "Panel 2 (top-right): a few weeks later, in a bright classroom, students sit at desks using tablets; the boy looks at a lesson video on his tablet, smiling and concentrating; a teacher stands nearby looking pleased. "
        "Panel 3 (bottom-left): later, in the same classroom, the same boy secretly plays a video game on his tablet under his desk instead of studying; a nearby teacher notices and frowns with a worried expression. "
        "Panel 4 (bottom-right): finally, a teacher checks a control monitor at the front; the students, including the boy, now study seriously and focused on their tablets again."
    )),
    "telework": ("Telework and Flexible Working", STYLE + (
        "Characters: a male manager in business-casual clothes; several office workers; ONE specific male worker with glasses and short hair (the same worker in panels 2,3,4); a little girl (his daughter) in panel 2. "
        "Panel 1 (top-left): in a small modern office, the manager stands in front of seated office workers and gestures welcomingly as if making an announcement; the workers look pleasantly surprised and happy. "
        "Panel 2 (top-right): a few weeks later, the male worker with glasses sits happily at a desk in his home, typing on a laptop; his little daughter plays on the floor beside him; a round wall clock shows midday. "
        "Panel 3 (bottom-left): later, the same worker with glasses sits alone at his home desk, slumped forward with a gloomy, lonely expression; the room around him is quiet and empty. "
        "Panel 4 (bottom-right): finally, the same worker smiles brightly at his open laptop, whose screen shows several colleagues in an online video meeting waving at him; he looks relieved and cheerful."
    )),
    "aging": ("Community Support for the Elderly", STYLE + (
        "Characters: an elderly woman with grey hair (in panels 1,3,4); a young female volunteer with a ponytail (in panels 1,2,4); several other volunteers in panel 2. "
        "Panel 1 (top-left): outside an apartment building on an outdoor staircase, the elderly woman struggles to carry two heavy grocery bags up the stairs; the young woman with a ponytail nearby watches her with a worried expression. "
        "Panel 2 (top-right): a few weeks later, in a community center, a group of volunteers sit around a table holding a meeting; one volunteer holds up a tablet device; a blank whiteboard is on the wall behind them. "
        "Panel 3 (bottom-left): the elderly woman sits alone at her home table, staring at the tablet with a confused and troubled expression, surrounded by several floating question-mark symbols; she looks lonely. "
        "Panel 4 (bottom-right): the young volunteer visits the woman's home, sits close beside her and patiently points at the tablet screen to teach her how to use it; two teacups are on the table; the elderly woman is finally smiling."
    )),
    "plastic": ("Reducing Plastic Waste", STYLE + (
        "Characters: a male supermarket manager wearing an apron (in all panels); several shoppers; an elderly female customer (in panels 3,4). "
        "Panel 1 (top-left): in a supermarket back office, the manager watches a television news report; the TV screen shows plastic waste floating in the ocean; the manager frowns with concern. "
        "Panel 2 (top-right): a few weeks later, at the supermarket entrance, the manager holds up a large blank sign and offers colorful reusable shopping bags; many smiling shoppers hold their own bags. "
        "Panel 3 (bottom-left): at the checkout counter, an elderly female customer looks troubled because she forgot her bag and has to buy another reusable bag; a small side inset shows unused bags piling up at her home. "
        "Panel 4 (bottom-right): a few months later, the manager has set up a free bag-lending box near the entrance; the same elderly woman happily borrows a bag from the box while the manager watches with a satisfied smile."
    )),
}

def main():
    card = sys.argv[1] if len(sys.argv) > 1 else "edtech"
    out = sys.argv[2] if len(sys.argv) > 2 else f"/tmp/eiken_{card}.png"
    entry = CARDS.get(card)
    if not entry:
        sys.exit(f"unknown card '{card}'. available: {list(CARDS)}")
    _topic_en, prompt = entry
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("❌ OPENAI_API_KEY が env に無い。railway run -s ai-juku-api で実行して。")
    body = json.dumps({
        "model": "gpt-image-1", "prompt": prompt,
        "size": "1536x1024", "quality": "medium", "n": 1,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations", data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print("HTTP ERROR", e.code); print(e.read().decode("utf-8", "replace")); sys.exit(1)
    item = (data.get("data") or [{}])[0]
    b64 = item.get("b64_json")
    if not b64:
        sys.exit("❌ b64_json が返らなかった: " + json.dumps(data)[:300])
    raw = base64.b64decode(b64)
    with open(out, "wb") as f:
        f.write(raw)
    print(f"✅ 生成成功 → {out} ({len(raw)//1024} KB) card={card} size=1536x1024 quality=medium")

if __name__ == "__main__":
    main()
