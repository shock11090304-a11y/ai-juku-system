# -*- coding: utf-8 -*-
"""第4問（古文）演習問題集の敵対的検査
   「解ける」かどうかではなく、「読まずに当てられないか」「答えがどこかに漏れていないか」
   「解説が正解と食い違っていないか」を見る。盲ソルバーは自分の設問しか見ないので、
   この層がないと冊子ぐるみの欠陥（先出し・引用の崩れ・位置の癖）が素通りする。
"""
import json, re, sys, os, glob, collections, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
CIRC = "①②③④⑤"
bad = []
def ng(m): bad.append(m); print("NG " + m)

def plain(s): return re.sub(r"\{\{/?[abcwxy]\}\}", "", s)
def flat(s):  return re.sub(r"[\s「」『』、。・…]", "", s)          # 照合の邪魔になる記号を落とす
def deruby(s): return re.sub(r"[（(][ぁ-んァ-ン]+[)）]", "", re.sub(r"[（(]注\d+[)）]", "", s))  # 読み仮名と注番号を外す
def noquote(s): return re.sub(r"「[^」]*」", "", s)                   # 引用（＝指し示し）を外す

NEG = re.compile(r"誤り|不可|合わない|当たらない|矛盾|言い過ぎ|すり替え|取り違え|ではない|できない|成立しない|排除|逆|外れる")

def lcs(a, b):
    """a と b の最長共通部分列（連続）の長さ。引用が崩れているかの判定に使う。"""
    best, prev = 0, [0] * (len(b) + 1)
    for x in a:
        cur = [0] * (len(b) + 1)
        for j, y in enumerate(b, 1):
            if x == y:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best: best = cur[j]
        prev = cur
    return best

def exp_for(q, it, sid):
    """問1のように小問が複数ある設問は、解説が1欄にまとまっているので該当部分だけを切り出す。
       ★切り出せないときに黙って全文へ落とすと、検査が「全文のどこかにあればよい」に退化する。"""
    e = q["exp"]
    lab = it.get("label") or ""
    if not lab: return e
    seg = re.split(r"(?=\((?:ア|イ|ウ)\))", e)
    hit = [x for x in seg if x.startswith(lab)]
    if not hit:
        ng(f"第{sid}回 問{q['no']}{lab}: 解説から{lab}の部分を切り出せない（見出しの形が違う）")
        return e
    return " ".join(hit)

def quotes(s):
    return [q for q in re.findall(r"「([^「」]+)」", s)]

def audit_set(S, longest, shortest, ranks):
    sid = S["id"]; P = S["passage"]
    body = flat(deruby(plain(P)))
    qtexts = "".join(q["text"] for q in S["questions"])
    # 本文＋資料＋注 ＝ 「本文から引いてよい」範囲
    hay = body + flat(deruby(qtexts)) + flat("".join(n["gloss"] + n["word"] for n in S["notes"]))

    # 1) 傍線記号の整合：問3・問4 が呼ぶ記号が本文の印と対応するか
    for no, mark, label in ((3, "x", "Ａ"), (4, "y", "Ｂ")):
        q = [x for x in S["questions"] if x["no"] == no][0]
        has = "{{" + mark + "}}" in P
        ref = re.findall(r"傍線部[（(]?([Ａ-ＺA-Z])[)）]?", q["text"])
        if has and (not ref or ref[0] != label):
            ng(f"第{sid}回 問{no}: 本文の印は{label}だが設問は「傍線部{ref[0] if ref else '（記載なし）'}」")
        if not has and ref:
            ng(f"第{sid}回 問{no}: 「傍線部{ref[0]}」と言うが本文に対応する印がない")
    q1 = [x for x in S["questions"] if x["no"] == 1][0]
    for k, lab in (("a", "ア"), ("b", "イ"), ("c", "ウ")):
        if ("{{" + k + "}}" in P) != (f"({lab})" in q1["text"] or f"（{lab}）" in q1["text"]):
            ng(f"第{sid}回 問1: 本文の印({lab})と設問文の対応が取れていない")
    # 問1が呼ぶ傍線部の文言が、本文の印の中身と一致するか
    for k, lab in (("a", "ア"), ("b", "イ"), ("c", "ウ")):
        m = re.search(r"\{\{" + k + r"\}\}(.*?)\{\{/" + k + r"\}\}", P, re.S)
        if not m: continue
        want = flat(deruby(re.sub(r"\(注\d+\)", "", m.group(1))))
        got = re.search(r"\(" + lab + r"\)「([^」]+)」", q1["text"])
        if not got: ng(f"第{sid}回 問1: 設問文に({lab})の引用がない")
        elif flat(got.group(1)) not in want:
            ng(f"第{sid}回 問1({lab}): 設問文の引用が本文の傍線部と違う「{got.group(1)[:24]}」")

    for q in S["questions"]:
        for it in q["items"]:
            a = it["answer"]; ans = CIRC[a]; lab = it["label"] or ""
            e = exp_for(q, it, sid)
            # 2) 解説が正解に触れているか
            key = flat(it["choices"][a])[:12]
            if ans not in e and key not in flat(e):
                ng(f"第{sid}回 問{q['no']}{lab}: 解説が正解{ans}に触れていない")
            # 3) 解説が正解を否定していないか
            for m in re.finditer(re.escape(ans), e):
                tail = re.split(r"[。\n]", e[m.end():m.end() + 40])[0]
                if NEG.search(tail):
                    ng(f"第{sid}回 問{q['no']}{lab}: 正解{ans}を否定する解説「…{e[max(0,m.start()-6):m.end()+30]}」")
            # 4) 選択肢の長さの偏り（正解だけ単独で最長／最短）
            #    ★1問ごとの倍率だけでは足りない。実際に「最大比 1.299 倍」で 1.30 の閾値に
            #      一度も届かないまま、問2〜問5 の 24/24 が最長＝正解になっていた。
            #      倍率を締めたうえで、割合を見る層（下の 15）を必ず併せて回すこと。
            L = [len(c) for c in it["choices"]]
            srt = sorted(L)
            if L[a] == max(L) and L.count(max(L)) == 1 and max(L) >= srt[-2] * 1.12:
                ng(f"第{sid}回 問{q['no']}{lab}: 正解肢だけが長い {L}（正解={a+1}）")
            if L[a] == min(L) and L.count(min(L)) == 1 and min(L) <= srt[1] * 0.85:
                ng(f"第{sid}回 問{q['no']}{lab}: 正解肢だけが短い {L}（正解={a+1}）")
            longest.append(L[a] == max(L) and L.count(max(L)) == 1)
            ranks.append(sorted(L, reverse=True).index(L[a]) + 1)
            shortest.append(L[a] == min(L) and L.count(min(L)) == 1)
            # 5) 選択肢の重複
            if len({flat(c) for c in it["choices"]}) != len(it["choices"]):
                ng(f"第{sid}回 問{q['no']}{lab}: 選択肢に重複")
            # 6) 正解肢だけ文末の形が違う（読まずに当てられる）
            ends = [c[-4:] for c in it["choices"]]
            others = [e2 for i, e2 in enumerate(ends) if i != a]
            if len(set(others)) == 1 and ends[a] not in others:
                ng(f"第{sid}回 問{q['no']}{lab}: 誤答の文末がそろい、正解だけ形が違う {ends}")

    # 7) 注・会話・資料が正解肢の文言を先出ししていないか（引用として示した部分は除く）
    notes_txt = flat("／".join(n["gloss"] for n in S["notes"]))
    for q in S["questions"]:
        t = flat(q["text"])
        for it in q["items"]:
            c = flat(noquote(it["choices"][it["answer"]]))
            for n in range(max(0, len(c) - 7)):
                g = c[n:n + 8]
                if g in notes_txt and g not in body:
                    ng(f"第{sid}回 問{q['no']}{it['label']}: 注が正解の文言を先出し「{g}」"); break
            for n in range(max(0, len(c) - 7)):
                g = c[n:n + 8]
                if g in t and g not in body:
                    ng(f"第{sid}回 問{q['no']}{it['label']}: 設問文（会話・資料）が正解の文言を先出し「{g}」"); break

    # 8) 設問をまたぐ漏洩：ある設問の正解の要点が、別の設問の選択肢にそのまま書かれていないか
    for qa in S["questions"]:
        for ia in qa["items"]:
            c = flat(noquote(ia["choices"][ia["answer"]]))
            for qb in S["questions"]:
                if qb["no"] == qa["no"]: continue
                other = flat(noquote(qb["text"] + "".join(x for ib in qb["items"] for x in ib["choices"])))
                for n in range(max(0, len(c) - 7)):
                    g = c[n:n + 8]
                    if g and g in other and g not in body:
                        ng(f"第{sid}回 問{qa['no']}{ia['label']}の正解が問{qb['no']}の設問文・選択肢に出ている「{g}」"); break
                else: continue
                break

    # 9) 引用の崩れ：本文から引いたつもりの「…」が、本文の形と違っていないか
    for q in S["questions"]:
        srcs = [("設問文", q["text"]), ("解説", q["exp"])] + \
               [(f"選択肢{CIRC[i]}", c) for it in q["items"] for i, c in enumerate(it["choices"])]
        for where, s in srcs:
            for qt in quotes(s):
                # 「…」で中を飛ばした引用は、飛ばした前後をそれぞれ別に照合する
                for part in re.split(r"[…‥・]{2,}|…|〜|～", qt):
                    f = flat(deruby(part))
                    if len(f) < 6 or f in hay: continue
                    # 活用語を辞書形にして引く（「言葉少なになる」）のは崩れではないので通す
                    if f[:-1] in hay or f[:-2] in hay: continue
                    # 本文から引いたつもりの語句は、途中が崩れても長いひとつづきが本文に残る。
                    # 現代語の言い換え（本文に無い言い回し）は、残るひとつづきが短いので区別できる。
                    n = lcs(f, hay)
                    if n >= max(4, len(f) * 0.5):
                        ng(f"第{sid}回 問{q['no']} {where}: 本文にない形で引用している「{part[:26]}」"
                           f"（本文と続けて一致するのは{n}/{len(f)}字）")

    # 10) 日本語で使う文字の外が紛れていないか
    #     ★以前はここで半角ラテンだけを見ていたため、キリル文字の混入を見逃した。
    #       「起こりうる壊れ方」を数えるのではなく、通してよい文字の側から数えること。
    vis = (plain(P) + S.get("translation", "")
           + "".join(n["word"] + n["gloss"] for n in S["notes"])
           + "".join(g["phrase"] + g["point"] for g in S["grammar"])
           + "".join(r["rule"] + r["where"] for r in S["rules_used"])
           + "".join(q["text"] + q["exp"] + "".join(c for it in q["items"] for c in it["choices"])
                     for q in S["questions"]))
    OK_CHARS = (r"\u3000-\u303F"      # 句読点・かぎかっこ・々
                r"\u3040-\u309F"      # ひらがな
                r"\u30A0-\u30FF"      # カタカナ
                r"\u4E00-\u9FFF"      # 漢字
                r"\uFF01-\uFFEF"      # 全角記号・全角英数（傍線の記号Ａ・Ｂ）
                r"\u2460-\u2473"      # 丸数字
                r"\u2026\u2192\u2014\u2015"  # … → ―（ルール名のダッシュ・生徒のノートの矢印）
                r"\s0-9()")            # 注番号・傍線記号に使う半角
    odd = sorted(set(re.findall(f"[^{OK_CHARS}]", vis)))
    if odd: ng(f"第{sid}回: 日本語で使わない文字が紛れている {odd}（{[hex(ord(c)) for c in odd]}）")

    # 11b) 解説が5つの肢すべてに触れているか（触れていない肢は、生徒が消去の根拠を得られない）
    for q in S["questions"]:
        for it in q["items"]:
            e = exp_for(q, it, sid)
            nt = [CIRC[i] for i in range(len(it["choices"])) if CIRC[i] not in e]
            if nt:
                ng(f"第{sid}回 問{q['no']}{it['label']}: 解説が触れていない肢がある {''.join(nt)}")

    # 11) 問5が会話・資料の形式か
    q5 = [x for x in S["questions"] if x["no"] == 5][0]
    if not re.search(r"【.*?会話.*?】|【資料】|【生徒のノート】|【.*?ノート.*?】", q5["text"]):
        ng(f"第{sid}回 問5: 会話文・資料の形式になっていない")

def main():
    files = sorted(glob.glob(os.path.join(HERE, "sets", "set*.json")))
    sets = sorted([json.load(open(f, encoding="utf-8")) for f in files], key=lambda x: x["id"])
    if not sets: ng("sets/set*.json が無い")
    dist = collections.Counter(); seq = []; longest = []; shortest = []; ranks = []
    for S in sets:
        audit_set(S, longest, shortest, ranks)
        for q in S["questions"]:
            for it in q["items"]:
                dist[CIRC[it["answer"]]] += 1; seq.append(it["answer"])

    # 12) 題をまたぐ選択肢・設問の重複
    allc = collections.defaultdict(list)
    for S in sets:
        for q in S["questions"]:
            for it in q["items"]:
                for i, c in enumerate(it["choices"]):
                    allc[flat(c)].append(f"第{S['id']}回 問{q['no']}{it['label']}{CIRC[i]}")
    for k, v in allc.items():
        if len(v) > 1: ng(f"選択肢の重複: {' / '.join(v)}")

    # 15) 「いちばん長い肢を選ぶ」だけで当たる割合
    # ★単独最長・単独最短だけでは足りない。「長い方から2つ」に絞れば当たる、という偏りが残る。
    #   長さ順位の平均が真ん中（3.0）から離れていないことも見る。
    if ranks:
        m = sum(ranks) / len(ranks)
        if not 2.4 <= m <= 3.6:
            ng(f"正解肢の長さ順位の平均が {m:.2f}（期待3.00）＝長さだけで絞り込める")
    for arr, word in ((longest, "最長"), (shortest, "最短")):
        if not arr: continue
        r = sum(arr) / len(arr)
        if r > 0.40:
            ng(f"正解が単独で{word}になる設問が {sum(arr)}/{len(arr)}（{r:.0%}）"
               f"＝本文を読まず長さだけで当たってしまう")

    # 13) 正解の位置が「読まなくても当たる」並びになっていないか
    if len(seq) >= 10:
        step = [(b - a) % 5 for a, b in zip(seq, seq[1:])]
        c = collections.Counter(step).most_common(1)[0]
        if c[1] > len(step) * 0.5:
            ng(f"正解位置の遷移が{c[0]}に偏っている（{c[1]}/{len(step)}）＝位置だけで当てられる")
        # 1回は7小問なので、回ごとに区切って「昇順に並んでいないか」を見る
        for S in sets:
            row = [it["answer"] for qq in S["questions"] for it in qq["items"]]
            if row == sorted(row) or row == sorted(row, reverse=True):
                ng(f"第{S['id']}回: 正解が7小問すべて単調に並んでいる {[x+1 for x in row]}")
        mx, mn = max(dist.values()), min(dist.values())
        if mx - mn >= 4: ng(f"正解番号の偏り: {dict(sorted(dist.items()))}")

    # 14) 設問の「縦の並び」に癖がないか
    #     ★分布と遷移を均しただけでは足りない。同じ設問番号（問2 なら問2）を回ごとに縦に並べたとき、
    #       同じ番号が続くと「問2はいつも⑤」と覚えられる。回どうしで並びがそっくりなのも同じ穴。
    cols = collections.defaultdict(list); rows = []
    for S in sets:
        row = []
        for q in S["questions"]:
            for it in q["items"]:
                slot = f'問{q["no"]}{it["label"]}'
                cols[slot].append(it["answer"] + 1); row.append(it["answer"] + 1)
        rows.append((S["id"], row))
    for slot, v in cols.items():
        c = collections.Counter(v).most_common(1)[0]
        if len(v) >= 4 and c[1] >= 3:
            ng(f"{slot} の正解が回をまたいで {CIRC[c[0]-1]} に{c[1]}回（縦に並べると癖が見える）")
        for i in range(len(v) - 2):
            if v[i] == v[i+1] == v[i+2]:
                ng(f"{slot} の正解が3回続けて {CIRC[v[i]-1]}")
    for (ia, ra), (ib, rb) in itertools.combinations(rows, 2):
        if ra == rb: ng(f"第{ia}回と第{ib}回で正解の並びがまったく同じ {ra}")
        if ra[:3] == rb[:3]: ng(f"第{ia}回と第{ib}回で問1(ア)(イ)(ウ)の並びが同じ {ra[:3]}")
    for sid, r in rows:
        for i in range(len(r) - 2):
            if r[i+1] - r[i] == r[i+2] - r[i+1] != 0:
                ng(f"第{sid}回: 正解が3小問続けて等差になっている {r[i:i+3]}")

    print(f"\n小問 {sum(dist.values())}個／正解の分布: {dict(sorted(dist.items()))}"
          f"／正解が単独最長: {sum(longest)}/{len(longest)}・単独最短: {sum(shortest)}/{len(shortest)}"
          f"・長さ順位の平均: {sum(ranks)/len(ranks):.2f}")
    print("設問ごとの縦の並び:", {k: "".join(CIRC[x-1] for x in v) for k, v in cols.items()})
    print("問題なし" if not bad else f"要修正 {len(bad)} 件")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
