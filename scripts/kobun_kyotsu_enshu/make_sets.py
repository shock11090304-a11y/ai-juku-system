# -*- coding: utf-8 -*-
"""src/setN.py（執筆順のまま書いた原稿）-> sets/setN.json（刷る形）

   ここでやることは2つだけ。
   1. 正解の位置を、回ごとにあらかじめ決めた番号（pos）へ動かす。
      手で番号を振ると必ず偏る。並べ替えは stem の md5 で決めるので毎回同じ結果になる。
   2. 解説の中の選択肢参照を、並べ替え後の丸数字へ書き直す。
      ★解説には ①②③ を直接書かず、必ず [[0]]〜[[4]]（執筆順の添字）で書くこと。
        直接書くと、並べ替えたときに解説と選択肢がずれる（この事故はこのリポジトリで何度も起きている）。
"""
import os, re, sys, json, glob, hashlib, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))
import positions
SRC = os.path.join(HERE, "src")
DEST = os.path.join(HERE, "sets")
CIRC = "①②③④⑤"

def permute(n_choices, answer, pos, seed_text):
    """執筆順 -> 刷る順 の写像 order を返す。order[新] = 旧添字。
       正解は必ず pos-1 に来る。残りは seed で決まる順（毎回同じ）に並べる。"""
    if not (0 <= answer < n_choices and 1 <= pos <= n_choices):
        raise SystemExit(f"permute: 選択肢{n_choices}個に対して answer={answer} pos={pos} は範囲外")
    others = [i for i in range(n_choices) if i != answer]
    h = hashlib.md5(seed_text.encode("utf-8")).hexdigest()
    others.sort(key=lambda i: hashlib.md5((h + str(i)).encode()).hexdigest())
    order, it = [], iter(others)
    for slot in range(n_choices):
        order.append(answer if slot == pos - 1 else next(it))
    return order

def render_exp(exp, maps, where=""):
    """解説の [[接頭辞+旧添字]] を、並べ替え後の丸数字へ書き直す。
       maps = {小問の接頭辞: {旧添字: 新添字}}。小問が1つの設問は接頭辞が空文字。"""
    def sub(m):
        key, k = m.group(1) or "", int(m.group(2))
        if key not in maps: raise SystemExit(f"{where}解説の参照 [[{key}{k}]] に対応する小問がない")
        if k not in maps[key]: raise SystemExit(f"{where}[[{key}{k}]] が選択肢の範囲外")
        return CIRC[maps[key][k]]
    out = re.sub(r"\[\[([^\d\]]*)(\d)\]\]", sub, exp)
    if "[[" in out: raise SystemExit(f"{where}解説に未解決の参照が残っている")
    return out

# ★まとめて潰していると読める言い方。ここに無い言い方で書くと、並べ替えが黙って効かなくなる。
COLLECTIVE = re.compile(r"^(?:は|も|が|の|について)?[、は]?\s*"
                        r"(?:いずれも|どれも|どちらも|両方とも|ともに|そろって|同様に|同じく|二つとも|三つとも)")
# ★丸数字と語が順に対応して読める形。「・」だけを見るのは壊れ方の側から数えること。
# ★ただの読点まで「対応づけ」と見ると、ほとんどの文が動かせなくなる。
#   順序が意味を持つのは、語を並べる記号（・や）と、位置を指す言葉（前者・後者・順に…）。
# ★対応づけは「・」「や」だけでなく「、」「と」でも作れる（「甲、乙とする」「甲と乙に取る」）。
PAIRED = re.compile(r"[・や、と]|前者|後者|それぞれ|順に|前は|後は|一方は|他方は|片方は")
# ★かたまりの続きに見えて実は全体のまとめ、という文。動かすと文章の途中へ紛れ込む。
TAIL_STOP = re.compile(r"^\s*(?:以上|したがって|つまり|まとめると|要するに|よって|このように|結局|ゆえに|なお|いずれにせよ|まとめ)")

def sort_kills(exp):
    """解説の末尾に並ぶ「① は…」「②③ は…」を、丸数字の昇順に並べ替える。
       ★執筆順（[[0]]〜[[4]]）で書いたものを刷る順に並べ替えるので、
         そのままでは潰す順が回ごとにばらばらになる。実測で42小問中40小問が昇順でなく、
         生徒は自分が選んだ番号を探すのに毎回解説を全部読み返すことになっていた
         （第1版は14問すべて昇順だった）。
       ひとかたまり＝「丸数字で始まる文」＋「そのあとに続く、丸数字で始まらない文」。
       安全弁: 扱う番号に重複があるときは、つながりを壊しうるので何もしない。"""
    parts = [x for x in re.split(r"(?<=。)", exp) if x]
    head = [n for n, t in enumerate(parts) if re.match(r"^\s*[①-⑤]", t)]
    # ★丸数字を「①・③」「①と③」「①、③」と書くと、下のキー抽出が片方しか拾わない。
    #   拾えない書き方が混ざっていたら、並べ替えないで原稿のまま出す（黙って壊さない）。
    if any(re.match(r"^\s*[①-⑤]\s*[・と、]\s*[①-⑤]", parts[n]) for n in head): return exp
    if len(head) < 2: return exp
    if head[0] == 0: return exp                      # 冒頭から丸数字＝別の書き方。触らない
    blocks = [parts[a:b] for a, b in zip(head, head[1:] + [len(parts)])]
    # ★まとめの1文がかたまりにくっつくと、並べ替えで文章の途中へ紛れ込む。
    #   「以上」「なお」などの黒リスト（TAIL_STOP）は書き方が1つ増えるたびに穴が開くので、
    #   最後のかたまりに続きの文があるときは、中身を見ずに何もしない（安全な形の側から数える）。
    if len(blocks[-1]) > 1: return exp
    if any(TAIL_STOP.match(t) for b in blocks for t in b[1:]): return exp
    keys = [[CIRC.index(c) for c in re.match(r"^\s*([①-⑤\s]+)", b[0]).group(1) if c in CIRC]
            for b in blocks]
    if sum(len(k) for k in keys) != len({n for k in keys for n in k}): return exp

    def inner(b, k):
        """1文が2つ以上の肢をまとめて潰しているとき、頭の丸数字も昇順にする。
           ★「・があったら触らない」と壊れ方の側から数えてはいけない。対応づけの記号は
             「・」だけでなく「や」「と」「、」でも作れる（「①⑤ は下役への体裁や老いへの配慮」）。
             並べ替えると対応が入れかわって意味が反転する。**まとめて潰していると読める言い方**
             （「はいずれも」等）のときだけ動かす＝安全な形の側から数える。"""
        if len(k) < 2: return b
        m = re.match(r"^(\s*)([①-⑤\s]+)", b[0])
        rest = b[0][m.end():]
        # 「いずれも」と書いてあっても、述語が「・」「や」で並んでいれば順に対応して読める。
        # 実際に「③ ④ はいずれも追いつめる・怒らせる意図とする」で対応が反転した。
        if not COLLECTIVE.match(rest) or PAIRED.search(rest): return b
        return [m.group(1) + " ".join(CIRC[n] for n in sorted(k)) + " " + rest.lstrip()] + b[1:]

    blocks = [inner(b, k) for b, k in zip(blocks, keys)]
    order = sorted(range(len(blocks)), key=lambda n: min(keys[n]))
    return "".join(parts[:head[0]]) + "".join("".join(blocks[n]) for n in order)

def build_set_multi(S):
    """小問が1つの設問は [[0]]〜[[4]]、問1のように小問が複数ある設問は
       小問ごとに [[ア0]] のように接頭辞を付けて参照する（解説が1欄にまとまるため）。"""
    k = 0
    for q in S["questions"]:
        maps = {}
        for it in q["items"]:
            pos = positions.of(S["id"], k); k += 1
            seed = f'{S["id"]}/{q["no"]}/{it.get("label","")}/{it["choices"][0]}'
            order = permute(len(it["choices"]), it["answer"], pos, seed)
            it["choices"] = [it["choices"][i] for i in order]
            it["answer"] = pos - 1
            key = re.sub(r"[()（）]", "", it.get("label", "")) or ""
            if key in maps:
                raise SystemExit(f'第{S["id"]}回 問{q["no"]}: 同じ接頭辞「{key}」の小問が2つある'
                                 "（解説の参照がどちらの並びで解決されるか決まらない）")
            maps[key] = {old: new for new, old in enumerate(order)}
        if re.search(r"[①-⑤]", q["exp"]):
            raise SystemExit(f'第{S["id"]}回 問{q["no"]}: 解説に丸数字が直接書かれている'
                             "（並べ替えでずれる。[[ア0]] の形で書くこと）")
        q["exp"] = render_exp(q["exp"], maps, f'第{S["id"]}回 問{q["no"]}: ')
        # 問1のように小問が複数ある設問は、解説が (ア)(イ)(ウ) の行に分かれている。
        # 行ごとに閉じているので、行単位で並べ替える。
        q["exp"] = "\n".join(sort_kills(ln) for ln in q["exp"].split("\n"))
    return S

def load(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.SET

def selftest():
    if not __debug__:
        raise SystemExit("python3 -O では assert が消えるので、この自己テストは意味をなさない")
    """並べ替えと解説の書き直しが本当に対応しているかを、ここで毎回確かめる。
       （検査そのものが壊れていないことを、使う前に確認する）"""
    for ans in range(5):
        for pos in range(1, 6):
            o = permute(5, ans, pos, f"seed{ans}{pos}")
            assert sorted(o) == list(range(5)), o
            assert o[pos - 1] == ans, (ans, pos, o)
            m = {"": {old: new for new, old in enumerate(o)}}
            assert render_exp("[[0]][[1]][[2]][[3]][[4]]", m) == \
                   "".join(CIRC[o.index(k)] for k in range(5))
            assert render_exp("[[ア0]]", {"ア": {0: 3}}) == CIRC[3]
    # 同じ入力なら毎回同じ並びになること
    assert permute(5, 2, 4, "x") == permute(5, 2, 4, "x")
    # 種が違えば並びも変わること（全部同じなら並べ替えが効いていない）
    assert len({tuple(permute(5, 0, 1, f"s{i}")) for i in range(30)}) > 1
    # 潰す順の並べ替え
    assert sort_kills("本文。よって①。③ は誤り。② は誤り。④ は誤り。⑤ は誤り。") == \
           "本文。よって①。② は誤り。③ は誤り。④ は誤り。⑤ は誤り。"
    assert sort_kills("よって①。④⑤ は甲。② は乙。③ は丙。") == \
           "よって①。② は乙。③ は丙。④⑤ は甲。"
    # まとめて潰していると明記した文だけ、頭の丸数字も昇順にする
    assert sort_kills("よって①。⑤ ③ はいずれも甲。② は乙。") == "よって①。② は乙。③ ⑤ はいずれも甲。"
    # 「いずれも」があっても、述語が並んでいる文は動かさない
    assert sort_kills("よって①。⑤ ③ はいずれも甲・乙とする。② は丙。") == \
           "よって①。② は丙。⑤ ③ はいずれも甲・乙とする。"
    # 語を並べて順に対応させている文は触らない（「・」も「や」も）
    assert sort_kills("よって①。⑤ ③ は甲・乙とする。② は丙。") == "よって①。② は丙。⑤ ③ は甲・乙とする。"
    assert sort_kills("よって①。⑤ ③ は甲や乙を持ち出す。② は丙。") == "よって①。② は丙。⑤ ③ は甲や乙を持ち出す。"
    # まとめの1文がくっついている解説は、並べ替えると途中へ紛れ込むので触らない
    assert sort_kills("よって①。④ は甲。② は乙。以上から、根拠は本文にある。") == \
           "よって①。④ は甲。② は乙。以上から、根拠は本文にある。"
    # 番号が重なっていたら触らない（意味のつながりを壊しうるので）
    assert sort_kills("よって①。③ は甲。③④ は乙。") == "よって①。③ は甲。③④ は乙。"
    # 末尾が丸数字で始まらない文は動かさない
    # 丸数字で始まらない文は、直前のかたまりにくっついて一緒に動く
    assert sort_kills("よって①。③ は甲。これも本文にない。② は乙。") == \
           "よって①。② は乙。③ は甲。これも本文にない。"
    # まとめの1文がくっついているときは、動かすと途中へ紛れ込むので何もしない
    assert sort_kills("よって①。③ は甲。なお本文を見よ。② は乙。") == \
           "よって①。③ は甲。なお本文を見よ。② は乙。"
    # 丸数字を「①・③」「①と③」と書いた行は、キーを拾いきれないので触らない
    assert sort_kills("よって①。④・⑤ は甲。② は乙。") == "よって①。④・⑤ は甲。② は乙。"
    print("selftest: ok")

def main():
    selftest()
    os.makedirs(DEST, exist_ok=True)
    files = sorted(glob.glob(os.path.join(SRC, "set*.py")))
    if not files: raise SystemExit("src/set*.py が無い")
    for f in files:
        S = build_set_multi(load(f))
        out = os.path.join(DEST, os.path.basename(f)[:-3] + ".json")
        json.dump(S, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        ans = [CIRC[it["answer"]] for q in S["questions"] for it in q["items"]]
        print(f'{os.path.basename(out)}: 第{S["id"]}回 正解 {"".join(ans)}')

if __name__ == "__main__":
    main()
