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


# 物理的な具体物・日常動作を指す語。正解の語義（抽象・改まった語）には現れないので、
# ここに当たる肢は構造的に必ず誤答になる → 1問に何本まで置いてよいかを G17 が見張る。
CONCRETE = re.compile(
    "洗剤|真珠|打楽器|記念碑|月曜|弦楽器|胞子|粉末|水を|水中|洗い流|着古|長旅|柵|ピン|ボルト|"
    "まくら|縁石|雑草|アイロン|印刷|口座|前払|遺言|身分証明|貝|地震|蒸留|染色|溶接|湾曲|山積み|"
    "切り倒|包み込|鉛筆|貫通|沈下|上昇気流|隆起|丘|乳化|銃|独身|茎")


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
    longest = shortest = total = 0
    exp = {"最長": 0.0, "最短": 0.0}
    per_test = {"最長": {}, "最短": {}}
    for t in tests:
        for label in exp:
            per_test[label].setdefault(t["no"], 0.0)
        for it in t["items"]:
            ls = [jlen(c) for c in it["choices"]]
            a = ls[it["answer"]]
            total += 1
            if a == max(ls) and ls.count(max(ls)) == 1:
                longest += 1
            if a == min(ls) and ls.count(min(ls)) == 1:
                shortest += 1
            for label, tgt in (("最長", max(ls)), ("最短", min(ls))):
                if a == tgt:
                    exp[label] += 1.0 / ls.count(tgt)
                    per_test[label][t["no"]] += 1.0 / ls.count(tgt)
    for label in ("最長", "最短"):
        pct = 100.0 * exp[label] / total
        if pct > 30.0:
            g.bad("G5", "「%sの肢を選ぶ」戦略の得点 %.1f/%d（%.1f%%・ランダム25%%）＝読まずに当たる"
                  % (label, exp[label], total, pct))
        elif pct > 28.0:
            g.note("G5", "「%sの肢を選ぶ」戦略 %.1f/%d（%.1f%%）" % (label, exp[label], total, pct))
        worst = max(per_test[label].items(), key=lambda kv: kv[1])
        n_items = len(tests[0]["items"])
        if worst[1] > n_items * 0.40:
            g.bad("G5", "第%d回だけで「%sを選ぶ」が %.1f/%d（%.0f%%）＝回ごとの偏り"
                  % (worst[0], label, worst[1], n_items, 100.0 * worst[1] / n_items))

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
        for it in t["items"]:
            for j, c in enumerate(it["choices"]):
                if j == it["answer"]:
                    continue
                cc = cores(c)
                for n2, w2, k2 in ans_cores:
                    if n2 == it["n"] or not (cc & k2):
                        continue
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

    # ★「印字語義と用例訳が別の語義になっている」型（induce の gloss を並べ替えたら用例
    #   "induce sleep（眠気を誘う）" が取り残された）は、ここでは検査しない。
    #   cores() は漢字2字以上しか核にしないため「〜を罰する／違反者を罰する」のような
    #   完全に対応した組を「核が無い」と誤検出し、実装すると73件中ほぼ全部が誤報になった。
    #   ＝本物の警告が埋もれてゲート全体が信用されなくなる。この型は辞書照合レビュー層で拾う。
    #   ★語義の順序を入れ替えたら usage_en / usage_ja を必ず読み直すこと。

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
