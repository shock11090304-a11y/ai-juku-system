# -*- coding: utf-8 -*-
"""講師用メモ（本文の典拠と校訂の記録）を、データから組み立てて出す。

   ★手で書かない。手で書くと、原稿を直したときにメモだけ古いまま残る。
"""
import json, os, sys, glob, textwrap, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = "TRILLION AI 学習塾"

def wrap(s, w=52, indent="　"):
    out = []
    for para in s.split("\n"):
        if not para.strip(): out.append(""); continue
        out += [indent + l for l in textwrap.wrap(para, width=w)]
    return "\n".join(out)

def main(dest=None):
    em = json.load(open(os.path.join(HERE, "sources", "emendations.json"), encoding="utf-8")) \
         if os.path.exists(os.path.join(HERE, "sources", "emendations.json")) else {}
    cuts = json.load(open(os.path.join(HERE, "sources", "cuts.json"), encoding="utf-8")) \
           if os.path.exists(os.path.join(HERE, "sources", "cuts.json")) else {}
    sets = sorted([json.load(open(f, encoding="utf-8")) for f in
                   glob.glob(os.path.join(HERE, "sets", "set*.json"))], key=lambda x: x["id"])
    L = {1: "基礎", 2: "標準", 3: "本番"}
    b = [f"共通テスト形式 国語 第4問（古文）演習問題集 基礎から本番まで　講師用メモ",
         f"―― 本文の典拠と校訂の記録　――",
         f"作成 {datetime.date.today():%Y-%m-%d}　{BRAND}", "",
         "本文はすべて実在の古典から、電子テキストの校訂本文どおりに引いている。",
         "記憶から書いた箇所は一つもない。以下は取得元と、原典から改めた箇所の記録である。", "",
         "＊照合のしかた（全6本に共通）",
         "　① 配布 zip に入っている本文と、同じページに表示される校訂本文とを機械で突き合わせ、",
         "　　 一字一句一致することを確かめた。",
         "　② 同じページに併載された翻刻（底本の仮名書き）と語句を照合した。",
         "　③ 刷る側のデータと①の本文とを、毎回 check_source.py が機械で突き合わせる。",
         "　　 改めた箇所は sources/emendations.json に理由つきで登録しないと通らない。",
         "　④ 読み仮名は校訂本文が付けているものだけを残し、こちらでは足していない。",
         "　★「梅沢本」は第1回（古本説話集）と第4・5回（無名抄）で別の本である。",
         "　　どちらも梅沢彦太郎の旧蔵だが、古本説話集は孤本、無名抄は東京国立博物館所蔵の写本。", ""]
    for S in sets:
        key = f'set{S["id"]}'
        b.append("■ 第{}回（{}レベル）　{}".format(S["id"], L[S["level_no"]], S["work"]))
        b.append("　（{}・{}）".format(S["genre"], S["era"]))
        if S.get("base"): b.append("　底本: " + S["base"] + "（やたナビTEXT の作品ページに明記されているもの）")
        b.append("　取得元: " + S.get("source_url", ""))
        if S.get("source_note"): b.append("　関連: " + S["source_note"])
        b.append("")
        b.append(wrap(S.get("confidence", "")))
        c = cuts.get(key)
        if c:
            for side in ("前", "後"):
                if c.get(side):
                    b.append("")
                    b.append(f"　・本文の{side}で落とした箇所：「{c[side]}」")
                    b.append(wrap("理由：" + c.get(f"{side}の理由", ""), indent="　　"))
        rows = em.get(key, [])
        if rows:
            b.append("")
            b.append(f"　・原典から改めた箇所（{len(rows)}か所）")
            for i, r in enumerate(rows, 1):
                b.append(f"　　({i})「{r['原典']}」→「{r['改めた形']}」")
                b.append(wrap(r.get("理由", ""), indent="　　　"))
        # 資料（別本文）
        for q in S["questions"]:
            if "【資料】" not in q["text"]: continue
            sk = f"shiryo_{key}"
            b.append("")
            b.append(f"　・問{q['no']}の【資料】は別の本文から引いた。典拠は sources/{sk}.txt に保存してある。")
            for i, r in enumerate(em.get(sk, []), 1):
                b.append(f"　　({i})「{r['原典']}」→「{r['改めた形']}」　{r.get('理由','')}")
        b.append("")
    b += ["", "■ 作り直すとき",
          "　1. src/setN.py を直す（原稿。解説の選択肢参照は [[ア0]] 形式で書く）",
          "　2. PYTHONPATH=src python3 make_sets.py   … sets/setN.json を作り直す",
          "　3. python3 check_source.py / check.py / audit.py … 3つとも通ること",
          "　4. python3 check_gates.py                … 検査そのものが効いているかを確かめる（変異試験）",
          "　5. python3 build.py                      … out/ に PDF を出す",
          "　6. python3 check.py <問題編.pdf> <解答解説編.pdf> … 刷り上がりとデータの逆照合",
          "",
          "　★正解の位置は src/positions.py が正典。設問を差し替えても、この表は動かさないこと。",
          "　★sources/*.txt は原典の保存物。編集すれば check_source.py が無意味になる。", ""]
    out = "\n".join(b)
    path = dest or os.path.join(HERE, "out", "講師用メモ_本文の典拠と校訂の記録.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(out)
    print(f"{os.path.basename(path)}: {len(out)}字")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
