# -*- coding: utf-8 -*-
"""生成 PDF のグリフ監査（豆腐・制御文字・絵文字）＋ 全ページ PNG 化。"""
import os, unicodedata, fitz

DESK = os.path.expanduser("~/Desktop")
OUT = ("/private/tmp/claude-501/-Users-adachishouhei-ai-juku-system/"
       "b8595e4e-c14f-4f81-a2dd-feb46082ddf2/scratchpad/qa")
SAFE_SO = "★▲●◆■□◇→←↑↓〜①②③④⑤⑥"
FILES = [("Q", "英語_品詞分解トレーニング_問題編.pdf"),
         ("A", "英語_品詞分解トレーニング_解答解説編.pdf")]


def main():
    os.makedirs(OUT, exist_ok=True)
    ng = 0
    for tag, name in FILES:
        path = os.path.join(DESK, name)
        d = fitz.open(path)
        txt, thin = "", []
        for i, pg in enumerate(d):
            t = pg.get_text()
            txt += t
            if len(t.strip()) < 150:
                thin.append((i + 1, len(t.strip())))
        hits = {}
        for ch in txt:
            if ch in "\n\r\t":
                continue
            bad = (ord(ch) < 0x20 or ord(ch) in (0xFFFD, 0x25A0)
                   or (unicodedata.category(ch) == "So" and ch not in SAFE_SO))
            if bad:
                hits[ch] = hits.get(ch, 0) + 1
        print(f"=== {name} : {d.page_count}p ===")
        print("  NG glyph      :", {f"U+{ord(k):04X}": v for k, v in hits.items()} or "なし")
        print("  中身の薄いページ:", thin or "なし")
        print("  ダッシュ付ラベル:",
              {k: txt.count(k) for k in ("S'", "S''", "V'", "V''", "M'", "C'")})
        ng += len(hits)
        for i in range(d.page_count):
            d[i].get_pixmap(dpi=110).save(f"{OUT}/{tag}{i + 1:02d}.png")
        d.close()
    print("NG total:", ng, "| images ->", OUT)


if __name__ == "__main__":
    main()
