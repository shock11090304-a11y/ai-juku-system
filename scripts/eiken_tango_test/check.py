# -*- coding: utf-8 -*-
"""英検準1級 単語テストの機械ゲート。

「AIに探させる前に、Python で判定できるものは全部ここで潰す」層。
build.py が呼び、1つでも FAIL があれば HTML を書き出さない。

  python3 check.py    # 単体実行（build.py と同じ結果を表示）
"""
import re, sys, os, hashlib
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

POS_OK = {"動", "名", "形", "副", "熟"}

# 中学〜英検2級で扱う句動詞。準1級の単語テストに混ぜると難度が崩れる
# （2026-07-23 の準1級 対策問題集で実際に指摘された易化。put off / carry out / keep up with）
TOO_EASY_IDIOM = {
    "put off", "carry out", "keep up with", "look for", "look after", "give up",
    "take care of", "find out", "turn on", "turn off", "get up", "put on",
    "look forward to", "come true", "get along with", "make up one's mind",
    "bring about", "call off", "run out of", "take part in", "depend on",
}

# 用例に見出し語がそのままの形では出ない語（不規則変化・語順変化）。理由つきで明示的に許可する
USAGE_IRREGULAR = {
    "wear off": "wore off（過去形）",
    "fall through": "fell through（過去形）",
    "wind up doing": "wind up paying（doing に実際の動詞が入る）",
}

# G4（2正解の疑い）の例外。核を共有していても意味は正反対で、むしろ良い誤答になるもの。
# ★必ず理由を書く。理由を書けないものは例外にしない。
ALLOW_CORE_SHARE = {
    ("phase out", "〜を段階的に導入する"): "phase in との対比。段階的という語は共有するが方向が逆",
    ("ramp up", "〜を段階的にやめる"): "phase out との対比。方向が逆",
}


# G20（同語源の対が回をまたぐ）の例外。★必ず理由を書く。理由を書けないものは例外にしない。
#
# 判断の分かれ目は「先の回の解説を見たら当たるか」ではなく「**語彙知識ゼロでも**当たるか」。
#   ・熟語が丸ごと再利用される（account for → account for the bulk of）＝英語を1語も
#     知らなくても同じ熟語だと分かる → 例外にせず差し替えた。
#   ・deter の意味欄に「抑止する」と書いたために deterrent「抑止力」が渡るのは、
#     こちらが付随的に書いてしまっただけ → 言い換えて消した。同じ理由で
#     assert の「主張する」、consist of の「構成」、advocate の「支持者」も消した。
#   ・infer / inference は infer が inference に丸ごと入っており、答えの「推論」も
#     第12回の解説に出る → 例外にせず inference を connotation に差し替えた。
#
# ★残した下の2組には**反対意見がある**。レビューで「testi- / alleg- という綴りの近さに
#   気づけば足り、語形の対応を見抜く語彙力は要らない」と指摘された。もっともな指摘で、
#   本筋の対処は**同じ回に置く**こと（G20 のメッセージ自身がそう勧めている）。
#   いまは回のテーマ（第8回=心情・態度の語／第12回=主張・判断の動詞）が崩れるのを避けて
#   据え置いているが、**次に回を組み替えるときに同居させる**。
ALLOW_SAME_ROOT_TODO = "testimony/testify と allegation/allege は同じ回に移すのが本筋（未実施）"
ALLOW_SAME_ROOT = {
    ("testimony", "testify"): "名詞形と動詞形。意味が同じなので意味欄からは消せない。"
                              "当てるには語形の対応を見抜く必要があり、それは語彙力そのもの",
    ("allegation", "allege"): "同上（名詞形と動詞形）",
}


# 物理的な具体物・日常動作を指す語。正解の語義（抽象・改まった語）には現れないので、
# ここに当たる肢は構造的に必ず誤答になる → 1問に何本まで置いてよいかを G17 が見張る。
CONCRETE = re.compile(
    "洗剤|真珠|打楽器|記念碑|月曜|弦楽器|胞子|粉末|水を|水中|洗い流|着古|長旅|柵|ピン|ボルト|"
    "まくら|縁石|雑草|アイロン|印刷|口座|前払|遺言|身分証明|貝|地震|蒸留|染色|溶接|湾曲|山積み|"
    "切り倒|包み込|鉛筆|貫通|沈下|上昇気流|隆起|丘|乳化|銃|独身|茎")


RANK_NAMES = ("最小", "2番目に小さい", "3番目に小さい", "最大")


def rank_scores(items, key):
    """選択肢を key で数値化し、「正解が k 番目に小さい」戦略の期待得点を4つ返す。
    同じ値の肢が n 本あるときは勘で1本選ぶので 1/n 点。"""
    out = [0.0, 0.0, 0.0, 0.0]
    for it in items:
        v = [key(c) for c in it["choices"]]
        srt = sorted(v)
        a = v[it["answer"]]
        for k in range(4):
            if a == srt[k]:
                out[k] += 1.0 / v.count(srt[k])
    return out


def rank_limits(items, key, z):
    """しきい値を**実データの同点構造から**、しかも**順位ごとに**計算して4つ返す。

    ★30%などと決め打ちしてはいけない。問数が少ない部分集合（熟語だけ80問）では
      1問=1.25pt 動くので、ゆらぎを欠陥と誤認して延々に直し続けることになる。
      逆に400問では30%でも緩すぎる。

    正解位置を一様乱数にしたときの1問あたりの寄与を X とすると
      E[X] = 1/4、E[X^2] = 1/(4c)（c＝その順位に並ぶ同値の肢の本数）
    なので分散は 1/(4c) - 1/16。

    ★★4順位の分散を**平均してはいけない**。同点の多い順位は分散が小さく、無い順位は大きい。
      平均すると同点の多い順位が緩くなって**見逃し**、無い順位が厳しくなって**誤検出**する。
      実測で実効 z が 2.2〜3.2 にばらついていた。漢字数は同点が構造的に多く、
      緩くなるのは rank0（＝「漢字が最少」）——まさに40.2%の事故が起きた順位だった。

    z は順列検定で較正した値を使う（4順位×3範囲×2キー＝24回の検定になるので、
    z=2.6 だとゲート全体の偽陽性が11.7%あった。z=2.9 で約5%）。"""
    var = [0.0, 0.0, 0.0, 0.0]
    for it in items:
        v = [key(c) for c in it["choices"]]
        srt = sorted(v)
        for k in range(4):
            c = v.count(srt[k])
            var[k] += 1.0 / (4.0 * c) - 1.0 / 16.0
    n = len(items)
    if not n:
        return [100.0] * 4
    return [25.0 + z * 100.0 * (x ** 0.5) / n for x in var]


def rank_gate(g, tag, what, tests, key):
    """4順位すべて × 全問/熟語のみ/単語のみ で「読まずに当たる」戦略を測る。

    ★片側だけ見てはいけない（最短を潰したら2番目が立ち、それを潰したら中間が立った＝3回踏んだ）。
    ★全体で薄まるので部分集合でも見る（熟語だけ「漢字が最少」が40.2%、全問では31%に見えた）。"""
    for scope, want in (("全問", None), ("熟語のみ", True), ("単語のみ", False)):
        items = [it for t in tests for it in t["items"]
                 if want is None or (it["pos"] == "熟") == want]
        if len(items) < 40:
            # ★黙って飛ばさない。飛ばしたことに気づかないと「検査した」と誤解する
            g.note(tag, "%s は %d問しか無いので %s の検査を飛ばした（統計にならない）"
                   % (scope, len(items), what))
            continue
        obs = rank_scores(items, key)
        # z は順列検定で較正。4順位×3範囲×2キー＝24回の検定なので z=2.6 だと
        # ゲート全体の偽陽性が11.7%あった。z=2.9 でおおむね5%。
        lim_bad = rank_limits(items, key, 2.9)
        lim_note = rank_limits(items, key, 2.0)
        for k, pct in enumerate((100.0 * x / len(items) for x in obs)):
            name = "%sが%s" % (what, RANK_NAMES[k])
            if pct > lim_bad[k]:
                g.bad(tag, "「%s肢」を選ぶ戦略が %s で %.1f%%（ランダム25%% / 上限%.1f%%）＝読まずに当たる"
                      % (name, scope, pct, lim_bad[k]))
            elif pct > lim_note[k]:
                g.note(tag, "「%s肢」を選ぶ %s %.1f%%（上限%.1f%%）" % (name, scope, pct, lim_bad[k]))


def cores(s):
    """日本語の語義から『意味の核』を抜く。漢字2字以上の連続とカタカナ2字以上。
    「〜を」「する」「な」等の機能部分は核にならないので比較から自然に落ちる。
    ★接尾の 的/化/性/さ/み は落として比較する（「深刻化」と「深刻」を同一視するため）。
      逆に部分文字列での照合はしない（「暫定的」と「決定的」が“定的”で衝突する誤検出が出た）。"""
    s = re.sub(r"[（(][^）)]*[）)]", "", s)          # 補足の括弧は落とす
    raw = set(re.findall(r"[一-鿿]{2,}", s)) | set(re.findall(r"[ァ-ヶー]{2,}", s))
    out = set()
    for c in raw:
        out.add(c)
        t = re.sub(r"[的化性さみ]+$", "", c)
        if len(t) >= 2:
            out.add(t)
    return out


def jlen(s):
    return len(re.sub(r"[（()）〜、。・/／]", "", s))


def _bone(s):
    """日本語から**漢字とカタカナだけ**を残した骨格を作る。

    ★語尾だけ落とす「語幹化」では足りない。実測で、`allegation` の意味欄を
      「申し立て」→「申立て」と書き換える（意味は同じ）だけでゲートが緑になった。
      語中の送り仮名（引き受ける→引受）も表記ゆれも吸収するには、かなを全部落とすしかない。
      「証言／証言する」「申し立て／申立て」「抑止／抑止力」「主張する／自己主張の強い」を
      すべて同じ土俵に載せる。"""
    return "".join(re.findall(r"[一-鿿ァ-ヶ]+", re.sub(r"[（(][^）)]*[）)]", "", s)))


class Gate:
    def __init__(self):
        self.fail = []
        self.warn = []

    def bad(self, gid, msg):
        self.fail.append("[%s] %s" % (gid, msg))

    def note(self, gid, msg):
        self.warn.append("[%s] %s" % (gid, msg))


def run(tests, verbose=False):
    g = Gate()
    all_words, all_gloss = [], {}

    # ---------- G1 構造 ----------
    for t in tests:
        tag = "第%d回" % t["no"]
        if len(t["items"]) != 20:
            g.bad("G1", "%s の問題数が %d（20であるべき）" % (tag, len(t["items"])))
        for it in t["items"]:
            loc = "%s-%d %s" % (tag, it["n"], it["word"])
            if len(it["choices"]) != 4:
                g.bad("G1", "%s の選択肢が %d 個" % (loc, len(it["choices"])))
            if len(set(it["choices"])) != len(it["choices"]):
                g.bad("G1", "%s の選択肢に重複" % loc)
            if not (0 <= it["answer"] < 4):
                g.bad("G1", "%s の answer が範囲外" % loc)
            elif it["choices"][it["answer"]] != it["gloss_brief"]:
                g.bad("G1", "%s: choices[answer] が印字用語義と不一致" % loc)
            # 印字用語義は「先頭の1義／カッコ記号を外す／中黒を や に開く」で作られる。
            # build.brief() を直に呼ばず“結果が満たすべき形”で照合する（片方だけ直す事故を防ぐ）。
            norm = re.sub(r"[（）()]", "", it["gloss"]).replace("・", "や")
            if not it["gloss_brief"] or not norm.startswith(it["gloss_brief"]):
                g.bad("G1", "%s: 印字用語義 '%s' が語義 '%s' から作られていない"
                      % (loc, it["gloss_brief"], it["gloss"]))
            if it["pos"] not in POS_OK:
                g.bad("G1", "%s の品詞 '%s' が不正" % (loc, it["pos"]))
            if not it["usage_en"] or not it["usage_ja"]:
                g.bad("G1", "%s の用例が空" % loc)
            all_words.append(it["word"].lower())
            all_gloss.setdefault(it["gloss"], []).append(loc)

    # ---------- G2 見出し語・語義の重複 ----------
    for w, c in Counter(all_words).items():
        if c > 1:
            g.bad("G2", "見出し語 '%s' が %d 回出ている" % (w, c))
    for gl, locs in all_gloss.items():
        if len(locs) > 1:
            g.bad("G2", "同じ語義が複数語の正解になっている: '%s' → %s" % (gl, " / ".join(locs)))

    # ---------- G3 正解位置 ----------
    for t in tests:
        tag = "第%d回" % t["no"]
        seq = [it["answer"] for it in t["items"]]
        dist = Counter(seq)
        if sorted(dist.values()) != [5, 5, 5, 5]:
            g.bad("G3", "%s の正解位置分布が %s（各5であるべき）" % (tag, dict(sorted(dist.items()))))
        # 完全周期（0,1,2,3,0,1,2,3...）＝英単語を読まずに全問正解できる
        if all((seq[i] + 1) % 4 == seq[i + 1] for i in range(len(seq) - 1)):
            g.bad("G3", "%s の正解列が完全周期" % tag)
        inc = sum(1 for i in range(len(seq) - 1) if (seq[i] + 1) % 4 == seq[i + 1])
        if inc > len(seq) * 0.5:
            g.bad("G3", "%s の +1 遷移が %d/%d（半数超＝位置で読める）" % (tag, inc, len(seq) - 1))
        run_len, mx = 1, 1
        for i in range(1, len(seq)):
            run_len = run_len + 1 if seq[i] == seq[i - 1] else 1
            mx = max(mx, run_len)
        if mx >= 4:
            g.note("G3", "%s で同じ位置が %d 連続" % (tag, mx))

    # ---------- G4 選択肢どうしが同義（＝2正解） ----------
    for t in tests:
        for it in t["items"]:
            loc = "第%d回-%d %s" % (t["no"], it["n"], it["word"])
            ck = cores(it["gloss"])
            for j, c in enumerate(it["choices"]):
                if j == it["answer"]:
                    continue
                if c == it["gloss_brief"]:
                    g.bad("G4", "%s: 誤答が正解と同一" % loc)
                dup = ck & cores(c)
                if dup and (it["word"], c) not in ALLOW_CORE_SHARE:
                    g.bad("G4", "%s: 正解『%s』と誤答『%s』が意味の核 %s を共有（2正解の疑い）"
                          % (loc, it["gloss"], c, "・".join(sorted(dup))))

    # ---------- G5 長さで解けてしまわないか ----------
    # ★「単独最長／単独最短の件数」だけでは足りない。同点を含めた戦略の期待得点で測る。
    #   実際に「最短を選ぶ（同点は勘）」が 68.9/200＝34.5% を取った（第6回だけなら51.5%）。
    #   単独最短は21%で基準内だったのに、同点を拾う分で10点も上振れしていた。
    # ★★さらに「最短と最長だけ見る」のも足りなかった。両端を平らにしたら**真ん中**が立つ。
    #   実測: 最短10.2%・最長8.1%で両方合格なのに「中間の長さを選ぶ」が44.4%取れた原稿があった。
    #   → 4順位すべてを測る。1つでも30%を超えたら不合格。
    longest = shortest = 0
    for t in tests:
        for it in t["items"]:
            ls = [jlen(c) for c in it["choices"]]
            a = ls[it["answer"]]
            if a == max(ls) and ls.count(max(ls)) == 1:
                longest += 1
            if a == min(ls) and ls.count(min(ls)) == 1:
                shortest += 1
    rank_gate(g, "G5", "長さ", tests, jlen)

    # ---------- G6 冊子内の解答漏洩（同一回で正解語義が他問の誤答と一致） ----------
    for t in tests:
        seen = {}
        for it in t["items"]:
            if it["gloss_brief"] in seen:
                g.bad("G6", "第%d回: 問%d(%s) と 問%d(%s) の印字語義が同一『%s』（正解が2つに見える）"
                      % (t["no"], seen[it["gloss_brief"]][0], seen[it["gloss_brief"]][1],
                         it["n"], it["word"], it["gloss_brief"]))
            seen[it["gloss_brief"]] = (it["n"], it["word"])
        gl2loc = {it["gloss_brief"]: it["n"] for it in t["items"]}
        for it in t["items"]:
            for j, c in enumerate(it["choices"]):
                if j == it["answer"]:
                    continue
                if c in gl2loc and gl2loc[c] != it["n"]:
                    g.bad("G6", "第%d回: 問%d の誤答『%s』が問%d の正解と完全一致"
                          % (t["no"], it["n"], c, gl2loc[c]))
    # 同一回内で正解どうしの意味が近すぎる（どちらの問題でも通る誤答を作りやすい）
    for t in tests:
        its = t["items"]
        for i in range(len(its)):
            for j in range(i + 1, len(its)):
                dup = cores(its[i]["gloss"]) & cores(its[j]["gloss"])
                if dup:
                    g.note("G6", "第%d回: 問%d(%s) と 問%d(%s) の正解語義が核 %s を共有"
                           % (t["no"], its[i]["n"], its[i]["word"], its[j]["n"], its[j]["word"],
                              "・".join(sorted(dup))))

    # ---------- G11 誤答肢が同じ紙の別問の正解と“実質同義” ----------
    # G6 は完全一致しか見ない。核の共有まで見ると、消去法で2問が連動して解ける型を拾える。
    for t in tests:
        ans_cores = [(it["n"], it["word"], cores(it["gloss_brief"])) for it in t["items"]]
        ans_gloss = {it["n"]: it["gloss_brief"] for it in t["items"]}
        for it in t["items"]:
            for j, c in enumerate(it["choices"]):
                if j == it["answer"]:
                    continue
                cc = cores(c)
                for n2, w2, k2 in ans_cores:
                    if n2 == it["n"]:
                        continue
                    # ★送り仮名違いは cores() では捕まらない。同じ紙に「割り当て」（誤答）と
                    #   「割当」（別問の正解）が並び、quota を知っている生徒は誤答を機械的に
                    #   消せた。かなを落とした骨格で比べると同一と分かる。
                    #   ★骨格1文字だと「思いがけない」と「思いやりのある」が同一になる。2文字以上に限る。
                    if len(_bone(c)) >= 2 and _bone(c) == _bone(ans_gloss[n2]):
                        g.bad("G11", "第%d回: 問%d(%s) の誤答『%s』が 問%d(%s) の正解『%s』と"
                              "同じ（送り仮名違い）＝消去法で連動して解ける"
                              % (t["no"], it["n"], it["word"], c, n2, w2, ans_gloss[n2]))
                    elif cc & k2:
                        g.note("G11", "第%d回: 問%d(%s) の誤答『%s』が 問%d(%s) の正解と核 %s を共有"
                               % (t["no"], it["n"], it["word"], c, n2, w2, "・".join(sorted(cc & k2))))

    # ---------- G12 表記の目印が正解と相関していないか ----------
    # ★盲ソルバーが実際に見つけた本物の欠陥: 丸カッコ付きの肢は正解にしか無く、39問すべてで
    #   「カッコを探すだけ」で当たった（19.5%が確定で取れる）。長さ・位置とは別の“書式の tell”。
    #   意味を一切読まずに当たる軸なので、記号ごとに正解との相関を数える。
    for mark, label in (("／", "スラッシュ"), ("（", "丸カッコ"), ("・", "中黒"),
                        ("〜", "チルダ"), ("…", "三点リーダ")):
        only_ans = marked_q = 0
        for t in tests:
            for it in t["items"]:
                hit = [j for j, c in enumerate(it["choices"]) if mark in c]
                if not hit:
                    continue
                marked_q += 1
                if hit == [it["answer"]]:
                    only_ans += 1
        if marked_q >= 8 and only_ans > marked_q * 0.6:
            g.bad("G12", "%s が正解肢だけに付く設問 %d/%d（%.0f%%）＝記号を探すだけで当たる"
                  % (label, only_ans, marked_q, 100.0 * only_ans / marked_q))
        elif marked_q >= 8 and only_ans > marked_q * 0.45:
            g.note("G12", "%s が正解肢だけに付く設問 %d/%d（%.0f%%）"
                   % (label, only_ans, marked_q, 100.0 * only_ans / marked_q))

    # ---------- G13 解答解説編のメモ／用例が「後の回の見出し語」を先出ししていないか ----------
    # 解説編は各回の実施後に生徒へ配る運用なので、第1回のメモに第8回の見出し語の意味が
    # 書いてあると、その回は必ず正解される。盲ソルバーは1問しか見ないので構造的に検出できない。
    later = {}
    for t in tests:
        for it in t["items"]:
            later.setdefault(it["word"].lower(), t["no"])
    for t in tests:
        for it in t["items"]:
            text = "%s %s" % (it["note"], it["usage_en"])
            for w, first_no in later.items():
                if first_no <= t["no"] or len(w) < 5:
                    continue
                if re.search(r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(w), text.lower()):
                    g.bad("G13", "第%d回 '%s' のメモ/用例が第%d回の見出し語 '%s' を先出ししている"
                          % (t["no"], it["word"], first_no, w))

    # ---------- G19 メモが「後の回の正解語義」を日本語で書いていないか ----------
    # ★G13（英単語の先出し）だけでは足りない。**英単語を出さずに日本語の語義だけ書いても漏れる**。
    #   実例: 第16回 considerable のメモ「「思いやりのある」意味の似た形の語と混同注意」が、
    #   第18回 considerate の正解「思いやりのある」をそのまま書いていた。
    #   綴りの近い語を注意するとき、相手の**語義を書かない**（「綴りの近い別語」とだけ書く）。
    #   ★下限はメモと用例訳で分ける。メモは「この語はこういう意味だ」という**断定**なので
    #     3字から見る。用例訳は普通の文で、「重大な」「厳格な」のような日常の修飾語が
    #     偶然一致するだけの誤検出が出る（実測: 下限3字にすると4件が誤検出）ので4字から。
    #     ★下限4字のままだと『支持者』(3字) を書いた advocate のメモを見逃していた。
    later_gloss = [(t["no"], it["word"], it["gloss_brief"])
                   for t in tests for it in t["items"]]
    for t in tests:
        for it in t["items"]:
            for no, w, b in later_gloss:
                if no <= t["no"] or w == it["word"]:
                    continue
                where = None
                if len(b) >= 3 and b in it["note"]:
                    where = "メモ"
                elif len(b) >= 4 and b in it["usage_ja"]:
                    where = "用例訳"
                # ★意味欄をここで全数照合すると誤検出になる。別々の英単語が同じ和訳を持つのは
                #   普通で（dwindle と diminish の「減少する」、prudent と sensible の
                #   「分別のある」）、それは漏洩ではない。意味欄は G20 が**同語源ペアに限って**見る。
                if where:
                    g.bad("G19", "第%d回 '%s' の%sが第%d回 '%s' の正解語義『%s』を書いている"
                          % (t["no"], it["word"], where, no, w, b))

    # ---------- G20 同語源・部分文字列の見出し語が回をまたいでいないか ----------
    # ★これが G19 の取りこぼしの本体だった。解答解説編は意味欄も刷るので、
    #   第8回 testimony の意味「証言」を配った時点で、第12回 testify の正解「証言する」は
    #   語形を見るだけで決まる。用例訳を言い換えても意味欄が残るので直らない。
    #   ★とくに **後の見出し語が前の見出し語をそのまま含む**（account for →
    #   account for the bulk of）のは、語彙知識ゼロで当たるので致命的。
    #   対策は「同語源の対は同じ回に置く」。回をまたいだ時点で落とす。
    #   ★「語幹が同じ」だけでは広すぎる。comply / compile / compensate のような無関係語まで
    #     拾って30件の誤検出になった。**語幹が共通かつ日本語の意味の核も重なる**組だけを落とす。
    #     considerable(かなり多い)/considerate(思いやりのある) のような、意味の違う
    #     「紛らわしい対」は落とさない（意味が違えば先の回を見ても後の回は決まらない）。
    def _pref(a, b):
        n = 0
        for x, y in zip(a, b):
            if x != y:
                break
            n += 1
        return n

    items_all = [(t["no"], it) for t in tests for it in t["items"]]
    for i, (no_a, ia) in enumerate(items_all):
        for no_b, ib in items_all[i + 1:]:
            if no_a == no_b:
                continue
            wa, wb = ia["word"].lower(), ib["word"].lower()
            # (1) 片方の見出し語が他方に文字列として含まれる＝語彙知識ゼロで当たる。
            #     ★語末境界だけ見ていたので infer⊂inference / assert⊂assertive を取り逃していた。
            # ★判定は「**日本語を文字列照合するだけで当たるか**」に一本化する。
            #   語形から derive できる分（deter→deterrent を「思いとどまらせるもの＝抑止力」と
            #   推す）は、このテストが測りたい語彙力そのものなので落とさない。
            #   落とすのは「先の回の解説に書いてある日本語が、後の回の答えにそのまま出る」場合。
            #   ★見出し語の包含（infer⊂inference）と語幹4字共通（constitute/consist of）の
            #     両方を対象にする。語末境界だけ見ていて包含を取り逃していた。
            short, long_ = (wa, wb) if len(wa) <= len(wb) else (wb, wa)
            # ★**複数語の熟語が丸ごと再利用される**のは無条件で不可。
            #   account for → account for the bulk of は、英語を1語も知らなくても
            #   「同じ熟語だ」と分かる。単語の派生（deter→deterrent）とは質が違う。
            if " " in short and short in long_:
                g.bad("G20", "熟語が別の回の熟語に丸ごと入っている: 第%d回 '%s' と 第%d回 '%s'"
                      "（英語を知らなくても同じ熟語だと分かる。片方を差し替える）"
                      % (no_a, ia["word"], no_b, ib["word"]))
                continue
            # 単語の派生（deter/deterrent、assert/assertive）は、語形の対応を見抜く力＝語彙力。
            # 落とすのは「先の回の解説に書いてある日本語が、後の回の答えにそのまま出る」場合だけ。
            related = (len(short) >= 5 and short in long_) or _pref(wa, wb) >= 4
            if not related:
                continue
            early, late = (ia, ib) if no_a < no_b else (ib, ia)
            pair = (early["word"], late["word"])
            if pair in ALLOW_SAME_ROOT:
                continue
            bone = _bone(late["gloss_brief"])
            page = _bone("%s ／ %s ／ %s" % (early["gloss"], early["usage_ja"], early["note"]))
            # 骨格そのものと、その連続部分（「自己主張強」→「主張」も拾う）で照合する。
            # ★骨格が1文字以下になる語義（「思いやりのある」→思、「〜から成る」→成、
            #   「おさまる」→空）は keys が空になり、**意味欄に答えを丸ごと書いても鳴らなかった**。
            #   そういう語義は、かなも含めた語義そのもので照合する（助詞と〜は落とす）。
            keys = {bone[i:j] for i in range(len(bone)) for j in range(i + 2, len(bone) + 1)}
            whole = re.sub(r"^[〜～]+", "", late["gloss_brief"])   # 〜だけ落とし助詞は残す
            raw_page = "%s ／ %s ／ %s" % (early["gloss"], early["usage_ja"], early["note"])
            hit = any(k in page for k in keys) or (len(whole) >= 3 and whole in raw_page)
            if hit:
                g.bad("G20", "同語源で、後の回の答えが先の回の解説ページに書いてある: "
                      "第%d回 '%s' の解説に『%s』→ 第%d回 '%s' の正解（同じ回に置くこと）"
                      % (min(no_a, no_b), early["word"], late["gloss_brief"],
                         max(no_a, no_b), late["word"]))

    # ★「印字語義と用例訳が別の語義になっている」型（induce の gloss を並べ替えたら用例
    #   "induce sleep（眠気を誘う）" が取り残された）は、ここでは検査しない。
    #   cores() は漢字2字以上しか核にしないため「〜を罰する／違反者を罰する」のような
    #   完全に対応した組を「核が無い」と誤検出し、実装すると73件中ほぼ全部が誤報になった。
    #   ＝本物の警告が埋もれてゲート全体が信用されなくなる。この型は辞書照合レビュー層で拾う。
    #   ★語義の順序を入れ替えたら usage_en / usage_ja を必ず読み直すこと。

    # ---------- G18 文字種（漢字の量）で解けてしまわないか ----------
    # ★長さを平らにしたら、今度は**字面**が目印になった。
    #   熟語の語義は自然と和語（ひらがな主体）になるのに、誤答だけ漢語で書いていたため
    #   「漢字が最少の肢を選ぶ」だけで熟語40問中40.2%取れた（単語は27%で無害）。
    #   ★全体で薄まって見えるので、**熟語だけの部分集合でも測る**こと。
    #   ★片側だけ潰すと反対側が立つ（G5 の長さで2回踏んだ）。最少を潰したら
    #     「2番目に少ない」が33%になった。**漢字の量も4順位すべて**測る。
    #   ★しきい値は決め打ちしない。rank_limit() が実データの同点構造から計算する
    #     （30%固定にしていたら、熟語80問ではゆらぎを欠陥と誤認して直し続けることになる）。
    kanji = re.compile(r"[一-鿿]")
    rank_gate(g, "G18", "漢字", tests, lambda c: len(kanji.findall(c)))

    # ★「意味欄が、同語源でない後の回の答えを書いている」型は**ゲートにしない**（判断を明記する）。
    #   G19 はメモと用例訳だけ、G20 は意味欄を見るが同語源ペアだけ。この交差は無検査で、
    #   実際に3件そこから落ちた（下記）。だが機械化を試した結果、入れない方がよいと判断した:
    #     ・素朴に全数照合 → **82件**。大半は「別々の英単語が同じ和訳を持つ」だけの正常なもの
    #       （advocate と endorse の「〜を支持する」、dwindle と diminish の「減少する」）。
    #     ・「全400語中2箇所だけの希少な言い回し」に絞っても **25件**残り、やはり大半が
    #       近義語ペア。先の回で「減少する＝dwindle」と知っても diminish の答えは決まらない
    #       （むしろ「それは dwindle の意味だから違う」と誤誘導する）。
    #   ★本物の警告が埋もれてゲート全体が信用されなくなる方が害が大きい（G16 で同じ轍を踏んだ）。
    #   落ちた3件は個別に直した:
    #     ・第9回 implication の意味欄「言外の意味」→ 第15回 connotation の正解（一字一句同じ）
    #       → implication の第2義を「波及効果」に変更
    #     ・第3回 disparity のメモ「⇔ parity（同等）」→ 第10回 on a par with の正解「〜と同等で」
    #       → メモを「dis-（打ち消し）＋ par（等しい）から」に変更
    #     ・第8回 allegation の誤答「割り当て」→ 同じ紙の quota の正解「割当」（送り仮名違い）
    #       → 誤答を差し替え、あわせて G11 が送り仮名を吸収して比べるようにした
    #   ★**回や語を足したら、この交差だけは人が見ること**。機械では precision が出ない。

    # ---------- G17 具体物ダミーは1問に1本まで ----------
    # ★正解の語義は抽象・改まった語なので、物理的な具体物を指す肢は必ず誤答になる。
    #   実測 35本すべて誤答。1問に2〜3本入ると「具体物を消す」だけで実質2択・0択になり、
    #   water down と testimony は誤答3本とも具体物で**答えが確定**していた。
    #   綴り混同を狙うダミー（deterrent/detergent, peril/pearl 等）は教材として価値があるので
    #   全廃せず、1問1本に制限する。
    for t in tests:
        for it in t["items"]:
            hit = [c for c in it["choices"] if CONCRETE.search(c)]
            if it["choices"][it["answer"]] in hit:
                g.bad("G17", "第%d回-%d %s: 正解肢が具体物マーカーを含む（設計上ありえない）"
                      % (t["no"], it["n"], it["word"]))
            if len(hit) >= 2:
                g.bad("G17", "第%d回-%d %s: 具体物ダミーが%d本（1本まで）: %s"
                      % (t["no"], it["n"], it["word"], len(hit), " / ".join(hit)))

    # ---------- G14 同一回で同じ誤答肢が2回以上 ----------
    for t in tests:
        seen = {}
        for it in t["items"]:
            for j, c in enumerate(it["choices"]):
                if j == it["answer"]:
                    continue
                if c in seen:
                    g.note("G14", "第%d回: 誤答『%s』が 問%d と 問%d に重複"
                           % (t["no"], c, seen[c], it["n"]))
                seen[c] = it["n"]

    # ---------- G15 回をまたいで印字語義が完全一致（解説編で同じ訳が2語に付く） ----------
    seen_g = {}
    for t in tests:
        for it in t["items"]:
            k = it["gloss_brief"]
            if k in seen_g:
                g.bad("G15", "印字語義『%s』が %s と %s の両方の正解になっている"
                      % (k, seen_g[k], "%s(第%d回)" % (it["word"], t["no"])))
            seen_g[k] = "%s(第%d回)" % (it["word"], t["no"])

    # ---------- G7 熟語パートの構成と難度 ----------
    for t in tests:
        idi = [it for it in t["items"] if it["pos"] == "熟"]
        if len(idi) != 4:
            g.bad("G7", "第%d回 の熟語が %d 個（4であるべき）" % (t["no"], len(idi)))
        for it in idi:
            if it["word"].lower() in TOO_EASY_IDIOM:
                g.bad("G7", "第%d回 '%s' は2級以下の難度" % (t["no"], it["word"]))
            if " " not in it["word"]:
                g.bad("G7", "第%d回 '%s' は熟語なのに1語" % (t["no"], it["word"]))
        for it in t["items"]:
            if it["pos"] != "熟" and " " in it["word"]:
                g.bad("G7", "第%d回 '%s' は複数語なのに品詞が '%s'" % (t["no"], it["word"], it["pos"]))

    # ---------- G8 用例に見出し語が実在する ----------
    for t in tests:
        for it in t["items"]:
            if it["word"] in USAGE_IRREGULAR:
                continue
            ue = it["usage_en"].lower()
            for part in it["word"].lower().split():
                if part in ("one's", "a", "the", "doing", "sb", "sth"):
                    continue
                stem = part[:max(4, len(part) - 3)]
                if stem not in ue:
                    g.bad("G8", "第%d回 '%s' の用例に語幹 '%s' が無い: %s"
                          % (t["no"], it["word"], stem, it["usage_en"]))

    # ---------- G9 品詞の分布（各回が単語16＋熟語4） ----------
    for t in tests:
        c = Counter(it["pos"] for it in t["items"])
        if sum(v for k, v in c.items() if k != "熟") != 16:
            g.bad("G9", "第%d回 の単語が %d 個（16であるべき）: %s"
                  % (t["no"], sum(v for k, v in c.items() if k != "熟"), dict(c)))

    # ---------- G10 選択肢の長さがそろっているか（極端なばらつきは tell） ----------
    for t in tests:
        for it in t["items"]:
            ls = [jlen(c) for c in it["choices"]]
            if max(ls) - min(ls) >= 12:
                g.note("G10", "第%d回-%d %s: 選択肢の長さ差が %d字 %s"
                       % (t["no"], it["n"], it["word"], max(ls) - min(ls), ls))

    n = sum(len(t["items"]) for t in tests)
    if verbose:
        print("=" * 74)
        print("[check] 全%d回 / %d問 / 見出し語 %d 語" % (len(tests), n, len(set(all_words))))
        for t in tests:
            print("  第%2d回 正解位置 %s" % (t["no"],
                  dict(sorted(Counter(it["answer"] + 1 for it in t["items"]).items()))))
        print("  正解肢が単独最長 %d/%d (%.0f%%) ・ 単独最短 %d/%d (%.0f%%)"
              % (longest, n, 100.0 * longest / n, shortest, n, 100.0 * shortest / n))
        for w in g.warn:
            print("  WARN", w)
        for f in g.fail:
            print("  FAIL", f)
        print("[check] %s  (FAIL %d / WARN %d)"
              % ("PASS" if not g.fail else "★NG★", len(g.fail), len(g.warn)))
        print("=" * 74)
    return not g.fail


if __name__ == "__main__":
    from content import TESTS
    import build
    sys.exit(0 if run(build.assign(TESTS), verbose=True) else 1)
