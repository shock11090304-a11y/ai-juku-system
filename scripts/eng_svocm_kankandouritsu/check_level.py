# -*- coding: utf-8 -*-
"""この教材の語彙レベルが「関関同立」と言える範囲にあるかを機械で照合する。

    python3 check_level.py            # この教材を測る
    python3 check_level.py --compare  # 同じ塾の既存教材と並べて比べる

■ なぜ要るか
  「関関同立レベルです」と紙に書くのは**レベルの主張**であって、измерение抜きに言ってよい
  ことではない。同じリポジトリの eiken_tango_test/check_cefr.py には、
  「収録語はすべて CEFR B2〜C1 です」と表紙で断言しながら半分が未照合で、実際には B1 の語が
  混ざっていた、という前例が記録されている。**紙は刷ったら直せない。**

■ 目安は当て推量で置かない。**実物と並べて決める**
  `--compare` で、リポジトリにある実際の入試英文（doshisha / kwansei の mirror）と
  塾の既存教材を同じ物差しで測って並べる。2026-09-01 の実測:

      同志社 英語（実物）              A1+A2 59.8%  B1+B2 23.3%  C1+一覧外 16.9%
      関西学院 英語（実物）            A1+A2 61.6%  B1+B2 24.4%  C1+一覧外 13.9%
      品詞分解（高校標準〜MARCH・既存） A1+A2 76.5%  B1+B2 17.2%  C1+一覧外  6.3%
      この教材（全体）                A1+A2 77.9%  B1+B2 18.6%  C1+一覧外  3.5%

  ★つまり**この教材の語彙は実物より 1 段やさしい**。構文（59 種）は関関同立の帯だが、
    語彙だけは「高校標準〜MARCH」の既存教材と同じ位置にある。
    第1部・第2部は**判別ドリルなので語彙をやさしく保つのが正しい**（語彙で落とすと
    構文を見る訓練にならない）。上げるとしたら第3部（全訳を課す 18 文）。
"""
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "_cefr_oxford5000.tsv")

# 一覧に無いが、この教材で使ってよい語（理由を必ず書く。理由なしに足さないこと）。
# ★「一覧に無い＝難しい」ではない。派生が透明な語・具体名詞は入試で普通に出る。
ALLOW = {
    "aquarium": "具体名詞。中学レベルの綴りで意味が推測できる",
    "brake": "具体名詞。自転車・車の文脈で頻出",
    "chairperson": "chair + person の複合。会議の文脈で意味が透明",
    "cyclist": "cycle + ist の派生",
    "sprinter": "sprint + er の派生",
    "mathematician": "mathematics + ian の派生",
    "translator": "translate + or の派生",
    "learner": "learn + er の派生",
    "gardener": "garden + er の派生",
    "baker": "bake + er の派生",
    "fisherman": "fisher + man の複合",
    "technician": "technique + ian の派生",
    "manufacturer": "manufacture + er の派生（manufacture は B2）",
    "workspace": "work + space の複合",
    "timetable": "time + table の複合",
    "rethink": "re + think の派生",
    "rewrite": "re + write の派生",
    "unrestored": "un + restored の派生",
    "first-time": "first + time の複合",
    "memorize": "memory の派生。B2 相当で入試頻出",
    "judgment": "judge の名詞形（B1）",
    "hesitation": "hesitate（B2）の名詞形",
    "fluent": "B2 相当。英語学習の話題で頻出",
    "harbor": "B1 相当の具体名詞（英綴り harbour はリストにある）",
    "antique": "B2 相当。骨董の文脈で意味が限定される",
    "aloud": "B1 相当。read aloud の形で頻出",
    "english": "固有名詞",
    "pottery": "具体名詞。陶芸の文脈で意味が限定される（B2 相当）",
    "stew": "具体名詞。料理の文脈で意味が推測できる",
    "fog": "A2 相当の具体名詞（Oxford 3000/5000 に見出しが無いだけ）",
    "paperwork": "paper + work の複合",
    "phrasebook": "phrase + book の複合",
    "windless": "wind + less の派生",
    "beginner": "begin + er の派生",
    "trader": "trade + er の派生",
    # ↓ 第3部を実物の帯まで上げたときに**意図して入れた**入試レベルの語。
    #   話題から意味が絞れるもの・派生が透明なものだけを入れる。
    "archaeologist": "考古学の話題語。archaeology の派生で、発掘の文脈から意味が絞れる",
    "archivist": "archive（C1）+ ist の派生",
    "excavation": "excavate の名詞形。考古学の話題語",
    "sediment": "地学・考古学の話題語。堆積の文脈から意味が絞れる",
    "erosion": "erode の名詞形。環境の話題語で入試頻出",
    "irrigation": "irrigate の名詞形。農業の話題語",
    "vaccination": "vaccinate の名詞形。医療の話題語で入試頻出",
    "tariff": "経済の話題語。subsidy（C1）と対で出る",
    "contradict": "contra + dict。入試頻出の他動詞",
    "fabricate": "「作り上げる・でっち上げる」。裁判の文脈で意味が絞れる",
    "exhausted": "exhaust の過去分詞。B2 相当で入試頻出",
    "prolonged": "prolong の過去分詞。B2 相当",
    "migrate": "migration（C1）の動詞形",
    "unforeseeable": "un + foresee + able の派生",
    "epidemic": "医療の話題語。入試頻出",
}

# ★実測した「実物」の帯（scripts/*_eigo_mirror/content.json ＝ 実際の入試英文）。
#   --compare で再現できる。ここを目安に、この教材の位置を判断する。
REFERENCE = {
    "同志社 英語（実物）": (59.8, 23.3, 16.9),
    "関西学院 英語（実物）": (61.6, 24.4, 13.9),
    "品詞分解（高校標準〜MARCH・既存）": (76.5, 17.2, 6.3),
}

SUFFIX = [("ies", "y"), ("ied", "y"), ("ier", "y"), ("iest", "y"), ("ily", "y"),
          ("es", ""), ("s", ""), ("ed", ""), ("ed", "e"), ("ing", ""), ("ing", "e"),
          ("er", ""), ("er", "e"), ("est", ""), ("ly", ""), ("ment", ""), ("ness", ""),
          ("ers", ""), ("ors", ""), ("or", ""), ("ist", ""), ("ists", ""),
          ("ians", ""), ("ian", ""), ("ion", "e"), ("ation", "e"), ("al", ""), ("'s", "")]
# 不規則変化。語形処理だけに任せると is / was / taken が「一覧に無い語」に化ける。
IRREGULAR = {
    "is": "be", "am": "be", "are": "be", "was": "be", "were": "be", "been": "be",
    "being": "be", "has": "have", "had": "have", "does": "do", "did": "do",
    "done": "do", "said": "say", "sent": "send", "spoke": "speak", "spoken": "speak",
    "taken": "take", "took": "take", "given": "give", "gave": "give", "begun": "begin",
    "began": "begin", "risen": "rise", "rose": "rise", "hung": "hang", "rung": "ring",
    "rang": "ring", "worn": "wear", "wore": "wear", "written": "write", "wrote": "write",
    "known": "know", "knew": "know", "grown": "grow", "grew": "grow", "left": "leave",
    "lost": "lose", "made": "make", "kept": "keep", "felt": "feel", "held": "hold",
    "found": "find", "brought": "bring", "bought": "buy", "caught": "catch",
    "thought": "think", "sought": "seek", "taught": "teach", "told": "tell",
    "understood": "understand", "chose": "choose", "chosen": "choose", "drew": "draw",
    "drawn": "draw", "shown": "show", "seen": "see", "saw": "see", "went": "go",
    "gone": "go", "an": "a", "those": "that", "these": "this", "men": "man",
    "women": "woman", "children": "child", "people": "person", "feet": "foot",
    "better": "good", "best": "good", "worse": "bad", "worst": "bad", "more": "much",
    "most": "much", "less": "little", "least": "little", "fewer": "few",
}
# 米綴り → 英綴り。Oxford の一覧は英綴りなので、この教材（米綴りに統一）のままでは引けない。
AME_TO_BRE = {"color": "colour", "colors": "colours", "colored": "coloured",
              "meter": "metre", "meters": "metres", "center": "centre",
              "theater": "theatre", "harbor": "harbour", "neighbor": "neighbour",
              "behavior": "behaviour", "favorite": "favourite", "labor": "labour",
              "labeled": "labelled", "traveled": "travelled", "canceled": "cancelled",
              "organization": "organisation", "realize": "realise",
              "recognize": "recognise", "defense": "defence", "offense": "offence",
              "gray": "grey", "analyze": "analyse", "judgment": "judgement"}
BAND = ["A1", "A2", "B1", "B2", "C1"]


def load_levels():
    lev = {}
    for line in open(TSV, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        w, _, L = line.strip().partition("\t")
        lev[w] = L
    return lev


# ★分けても意味が保たれる接頭辞だけを並べる。dis は入れない
#   （dismay を dis + may と分けて A1 と判定した。discuss / dismiss / distort も同じ形）。
#   基語は 5 文字以上を要求する（短い基語だと偶然の一致が増える）。
PREFIX = ("re", "un", "non", "over", "under", "mis", "pre", "post", "inter")


def lemma_level(w, lev, depth=0):
    """語形変化・派生・複合をたどって CEFR レベルを引く。返り値 (レベル, 引けた見出し語)。

    ★1 段だけの引き方では足りない。traders は s を落として trader、さらに er を落として
      trade まで**二段**たどらないと引けず、「一覧に無い難語」に化ける（実測）。
    """
    w = w.lower().strip("'-")
    if not w or depth > 3:
        return None, None
    if w in lev:
        return lev[w], w
    if w in AME_TO_BRE and AME_TO_BRE[w] in lev:
        return lev[AME_TO_BRE[w]], AME_TO_BRE[w]
    if w in IRREGULAR and IRREGULAR[w] in lev:
        return lev[IRREGULAR[w]], IRREGULAR[w]
    # ★最初に当たったものを返してはいけない。restored は ("ed","") で restor になり、
    #   さらに ("or","") で rest（A2）まで遡って「休憩」の語になる（実測）。
    #   候補を全部集めて、**元の語にいちばん近い（見出し語が長い）もの**を採る。
    cands = []
    for a, b in SUFFIX:
        if w.endswith(a) and len(w) - len(a) >= 3:
            L, head = lemma_level(w[:-len(a)] + b, lev, depth + 1)
            if L:
                cands.append((len(head), L, head))
    if cands:
        _n, L, head = max(cands)
        return L, head
    # 子音字重ねの -ed / -ing / -er / -est（stopped / running / hotter / hottest）
    for a in ("ed", "ing", "er", "est"):
        if w.endswith(a) and len(w) > len(a) + 2 and w[-len(a) - 1] == w[-len(a) - 2]:
            L, head = lemma_level(w[:-len(a) - 1], lev, depth + 1)
            if L:
                return L, head
    # 接頭辞（rewritten / unrestored / nonstop）。意味が透明なので基語のレベルを採る。
    for p in PREFIX:
        if w.startswith(p) and len(w) - len(p) >= 5:
            L, head = lemma_level(w[len(p):], lev, depth + 1)
            if L:
                return L, f"{p}+{head}"
    # 複合語（ハイフンあり・なし）。分けた要素がすべて既知なら、いちばん高いレベルを採る。
    # paperwork / phrasebook / windless のような「意味が透明な複合」を難語と数えないため。
    if "-" in w:
        parts = [x for x in w.split("-") if x]
        got = [lemma_level(x, lev, depth + 1)[0] for x in parts]
        if all(got):
            return max(got, key=BAND.index), w
    for i in range(3, len(w) - 2):
        a, b = w[:i], w[i:]
        la = lemma_level(a, lev, depth + 1)[0]
        lb = lemma_level(b, lev, depth + 1)[0]
        if la and lb:
            return max(la, lb, key=BAND.index), f"{a}+{b}"
    return None, None


def allowed(w):
    """ALLOW に理由が書かれている語か（複数形・過去形などの語形も許す）。"""
    w = w.lower().strip("'-")
    if w in ALLOW:
        return True
    for a, b in SUFFIX:
        if w.endswith(a) and len(w) - len(a) >= 2 and (w[:-len(a)] + b) in ALLOW:
            return True
    if w in IRREGULAR and IRREGULAR[w] in ALLOW:
        return True
    return False


def profile(sentences, lev):
    types = collections.Counter()
    for s in sentences:
        for w in re.findall(r"[A-Za-z][A-Za-z'-]*", s):
            types[w.lower().strip("'-")] += 1
    dist = collections.Counter()
    off = {}
    for w, n in types.items():
        L, _ = lemma_level(w, lev)
        if L:
            dist[L] += n if False else 1
        else:
            off[w] = n
    return types, dist, off


def sentences_of_this_material():
    import content as C
    out = []
    for g in C.PART1:
        out += [(f'第1部/{it["id"]}', it["en"]) for it in g["items"]]
    out += [(f'第2部/{q["id"]}', q["en"]) for q in C.PART2]
    for g in C.PART3:
        out += [(f'第3部/{it["id"]}', it["en"]) for it in g["items"]]
    return out


def compare():
    """実際の入試英文・既存教材と同じ物差しで並べる（目安を当て推量で置かないため）。"""
    import importlib.util
    import json as _json
    lev = load_levels()

    def show(sents, label):
        types, dist, off = profile(sents, lev)
        n = len(types) or 1
        print(f"  {label:32s} {len(sents):>4}文 異なり{n:>5}語  "
              f"A1+A2 {(dist['A1'] + dist['A2']) / n * 100:5.1f}%  "
              f"B1+B2 {(dist['B1'] + dist['B2']) / n * 100:5.1f}%  "
              f"C1+一覧外 {(dist['C1'] + len(off)) / n * 100:5.1f}%")

    def harvest(o, out):
        if isinstance(o, str):
            if (len(re.findall(r"[A-Za-z]{2,}", o)) >= 8
                    and len(re.findall(r"[ぁ-んァ-ン一-龥]", o)) < len(o) * 0.1):
                out.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                harvest(v, out)
        elif isinstance(o, list):
            for v in o:
                harvest(v, out)

    print("=" * 78)
    for d, label in (("doshisha_eigo_mirror", "同志社 英語（実物）"),
                     ("kwansei_eigo_mirror", "関西学院 英語（実物）")):
        path = os.path.normpath(os.path.join(HERE, "..", d, "content.json"))
        if os.path.exists(path):
            out = []
            harvest(_json.load(open(path, encoding="utf-8")), out)
            show(out, label)
    hp = os.path.normpath(os.path.join(HERE, "..", "eng_hinshi_bunkai", "content.py"))
    if os.path.exists(hp):
        sp = importlib.util.spec_from_file_location("_hcontent", hp)
        m = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(m)
        sents = [re.sub(r"@\d+\{|\}", "", p) for P in m.PASSAGES for p in P["paras"]]
        show(sents, "品詞分解（高校標準〜MARCH・既存）")
    pairs = sentences_of_this_material()
    import content as C
    show([it["en"] for g in C.PART1 for it in g["items"]], "この教材 第1部（判別ドリル）")
    show([q["en"] for q in C.PART2], "この教材 第2部（構造4択）")
    show([it["en"] for g in C.PART3 for it in g["items"]], "この教材 第3部（英文解釈）")
    show([s for _w, s in pairs], "この教材 全体")
    print("=" * 78)


def measure_file(path):
    """原稿を書きながら測る。JSON 配列（各件に "en"）を渡す。

        python3 check_level.py --file draft.json

    ★DSL を lint.py で確かめながら書くのと同じで、語彙レベルも書きながら確かめる。
      書き上げてから測って「1 段やさしい」と分かると、全部作り直しになる（実際になった）。
    """
    import json as _json
    lev = load_levels()
    items = _json.load(open(path, encoding="utf-8"))
    if isinstance(items, dict):
        items = items.get("items", [items])
    sents = [it["en"] for it in items if it.get("en")]
    types, dist, off = profile(sents, lev)
    n = len(types) or 1
    easy = (dist["A1"] + dist["A2"]) / n * 100
    mid = (dist["B1"] + dist["B2"]) / n * 100
    hard = (dist["C1"] + len(off)) / n * 100
    print("-" * 72)
    for name, (e, m, h) in REFERENCE.items():
        print(f"  {name:32s} A1+A2 {e:5.1f}%  B1+B2 {m:5.1f}%  C1+一覧外 {h:5.1f}%")
    print(f"  {'この原稿':32s} A1+A2 {easy:5.1f}%  B1+B2 {mid:5.1f}%  C1+一覧外 {hard:5.1f}%"
          f"  （{len(sents)} 文 / 異なり {n} 語）")
    print("-" * 72)
    heavy = sorted({w for w in types if lemma_level(w, lev)[0] in (None, "C1")})
    print(f"重い語（C1 と一覧外）{len(heavy)} 語: {', '.join(heavy)}")
    lens = [len(re.findall(r"[A-Za-z][A-Za-z'-]*", s)) for s in sents]
    if lens:
        print(f"1文の語数: 最短 {min(lens)} / 中央 {sorted(lens)[len(lens) // 2]} / 最長 {max(lens)}")
    ng = []
    if easy > 68:
        ng.append(f"A1+A2 が {easy:.1f}%。実物（59.8 / 61.6%）に近づける（68% 以下）")
    if hard < 10:
        ng.append(f"C1+一覧外 が {hard:.1f}%。実物（13.9 / 16.9%）に近づける（10% 以上）")
    if hard > 22:
        ng.append(f"C1+一覧外 が {hard:.1f}%。早慶・旧帝に寄りすぎ（22% 以下）")
    for x in ng:
        print(f"[NG] {x}")
    print(f"NG {len(ng)} 件")
    return 1 if ng else 0


def main():
    if "--compare" in sys.argv:
        compare()
        return
    if "--file" in sys.argv:
        sys.exit(measure_file(sys.argv[sys.argv.index("--file") + 1]))
    lev = load_levels()
    pairs = sentences_of_this_material()
    types, dist, off = profile([s for _w, s in pairs], lev)
    tot = len(types)
    errs, warns = [], []

    print("=" * 66)
    print(f"英文 {len(pairs)} 文 / 延べ {sum(types.values())} 語 / 異なり {tot} 語")
    lens = [len(re.findall(r"[A-Za-z][A-Za-z'-]*", s)) for _w, s in pairs]
    print(f"1文の語数: 最短 {min(lens)} / 中央 {sorted(lens)[len(lens) // 2]} / 最長 {max(lens)}")
    print("-" * 66)
    cum = 0
    for L in BAND:
        cum += dist[L]
        print(f"  {L}  {dist[L]:>3} 語 ({dist[L] / tot * 100:5.1f}%)   累計 {cum / tot * 100:5.1f}%")
    unknown = {w: n for w, n in off.items() if not allowed(w)}
    known_off = len(off) - len(unknown)
    print(f"  一覧外（許可済み）  {known_off:>3} 語 ({known_off / tot * 100:5.1f}%)")
    print(f"  一覧外（未確認）    {len(unknown):>3} 語 ({len(unknown) / tot * 100:5.1f}%)")
    print("=" * 66)

    easy = (dist["A1"] + dist["A2"]) / tot * 100
    mid = (dist["B1"] + dist["B2"]) / tot * 100
    hard = (dist["C1"] + len(off)) / tot * 100
    print("--- 実物と並べる（--compare で再測できる） ---")
    for name, (e, m, h) in REFERENCE.items():
        print(f"  {name:32s} A1+A2 {e:5.1f}%  B1+B2 {m:5.1f}%  C1+一覧外 {h:5.1f}%")
    print(f"  {'この教材（全体）':32s} A1+A2 {easy:5.1f}%  B1+B2 {mid:5.1f}%  C1+一覧外 {hard:5.1f}%")
    ref_easy = min(e for e, _m, _h in REFERENCE.values())
    print(f"\n★実物より {easy - ref_easy:+.1f} ポイントやさしい"
          "（第1部・第2部は判別ドリルなので、やさしいのが正しい）")
    # 明らかに帯を外れたときだけ落とす。実物との差は上の表で判断する（内容の判断は人がする）。
    if easy > 85:
        errs.append(f"やさしい語（A1+A2）が {easy:.1f}%。共通テストの下に落ちている")
    if hard > 20:
        errs.append(f"重い語（C1+一覧外）が {hard:.1f}%。早慶・旧帝の帯に入っている")
    if mid < 10:
        errs.append(f"B1+B2 が {mid:.1f}% しかない。関関同立の読解はここが主戦場")
    if unknown:
        errs.append(f"CEFR 一覧に無く、ALLOW にも理由が書かれていない語が {len(unknown)} 語ある: "
                    + ", ".join(sorted(unknown)))

    # 1 文ごとの重さ（重い語が 3 語以上ある文は解釈問題として過負荷）
    for w, s in pairs:
        heavy = [t for t in re.findall(r"[A-Za-z][A-Za-z'-]*", s)
                 if (lemma_level(t, lev)[0] in (None, "C1"))
                 and not allowed(t)]
        # ★実物の入試英文は 1 文に重い語を 3 語前後含む。3 で警告すると正常な文を毎回鳴らす。
        #   語彙で落とす文（4 語以上）だけを見る。
        if len(heavy) >= 4:
            warns.append(f"[warn] {w}: 重い語が {len(heavy)} 語 {heavy}"
                         "（構文でなく語彙で落とす文になっていないか）")

    for x in warns:
        print(x)
    if errs:
        print(f"\n*** レベルの照合に通らなかった項目 {len(errs)} 件 ***")
        for e in errs:
            print(f"[NG] {e}")
        sys.exit(1)
    print("NG 0 件 / 明らかな帯外れは無い"
          "（★実物との差は上の表で判断すること。第3部の語彙を上げるかは内容の判断）")


if __name__ == "__main__":
    main()
