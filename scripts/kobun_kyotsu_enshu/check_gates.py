# -*- coding: utf-8 -*-
"""検査そのものが効いているかを確かめる変異試験（ゲートのゲート）。

   ★ファイル名を check_ で始めてあるのは、scripts/run_all_gates.py に拾わせるため。
     名前を変えると誰からも呼ばれなくなり、ここで守っている性質が静かに失われる。

   ★★「赤になったか」だけを見てはいけない。
     以前この試験は `exit != 0` だけで合否を決めていて、**狙った検査を丸ごと消しても緑**だった
     （正解位置の検査9か所・レベルの階段5か所・校訂記録5か所を全部消しても 22種すべて検出、と出た）。
     原因は、変異が狙いの検査に届く前に別の検査（解説の丸数字など）が先に赤にすること。
     いまは変異ごとに **期待する NG の文言** を持たせ、それが出たときだけ合格とする。

   ★リポジトリのファイルには一切書かない。まるごと写しを作り、その中だけを壊す。
"""
import json, os, re, sys, shutil, subprocess, tempfile, atexit

REAL = os.path.dirname(os.path.abspath(__file__))
WORK = tempfile.mkdtemp(prefix="kobun_gates_")
HERE = os.path.join(WORK, "pkg")
shutil.copytree(REAL, HERE, ignore=shutil.ignore_patterns("out", "blind", "__pycache__", ".*"))
atexit.register(lambda: shutil.rmtree(WORK, ignore_errors=True))
SETS = os.path.join(HERE, "sets")

def run(script, base=None, args=()):
    base = base or HERE
    r = subprocess.run([sys.executable, os.path.join(base, script), *args],
                       capture_output=True, text=True, cwd=base)
    return r.returncode, [l for l in r.stdout.split("\n") if l.startswith("NG")], r.stderr

def fresh_copy():
    """まっさらな写しを作る。
       ★正解位置の変異は、使い回した写しの中でやると効かないことがある
         （前の変異が残した状態・バイトコードのキャッシュ）。実際に3種のうち2種が
         「赤にならない」と出て、ゲートの穴と見分けがつかなかった。
         回ごとに新しい写しを作れば、その手の紛れが原理的に入らない。"""
    d = tempfile.mkdtemp(prefix="kobun_pos_", dir=WORK)
    pkg = os.path.join(d, "pkg")
    shutil.copytree(REAL, pkg, ignore=shutil.ignore_patterns("out", "blind", "__pycache__", ".*"))
    return pkg

def remake(base):
    """写しの src/ から sets/ を作り直す"""
    env = dict(os.environ, PYTHONPATH=os.path.join(base, "src"), PYTHONDONTWRITEBYTECODE="1")
    subprocess.run([sys.executable, os.path.join(base, "make_sets.py")],
                   capture_output=True, text=True, cwd=base, env=env, check=True)

def all_sets():
    rows = [(json.load(open(os.path.join(SETS, f), encoding="utf-8")), os.path.join(SETS, f))
            for f in os.listdir(SETS) if re.fullmatch(r"set\d+\.json", f)]
    return sorted(rows, key=lambda r: r[0]["id"])

# ---------------------------------------------------------------- audit.py の変異
def M_quote(d):
    q = d["questions"][3]
    q["exp"] = re.sub(r"「([^」]{8})", lambda m: "「" + m.group(1)[:-1] + "し", q["exp"], count=1)

def M_long(d):
    it = d["questions"][2]["items"][0]
    it["choices"][it["answer"]] = it["choices"][it["answer"]] * 2

def M_short(d):
    it = d["questions"][2]["items"][0]
    it["choices"][it["answer"]] = it["choices"][it["answer"]][:8]

def M_rank(d):
    """正解肢を、その設問でいちばん長い肢よりさらに長くする（長さ順位の偏り）"""
    # ★1問ごとの閾値（最長が2位の1.12倍）には引っかからない範囲で、
    #   全問の正解をわずかに最長にする。順位の平均だけが動く形にしないと、
    #   別の検査が先に赤にして「順位の検査が効いている」ことを実証できない。
    for q in d["questions"]:
        for it in q["items"]:
            L = [len(c) for c in it["choices"]]
            a = it["answer"]
            need = max(L) + 1 - L[a]
            # ★末尾に足すと「誤答の文末がそろう」検査が先に赤になるので、途中に足す
            if need > 0:
                c = it["choices"][a]
                it["choices"][a] = c[:4] + "また" * ((need + 1) // 2) + c[4:]

def M_note_leak(d):
    it = d["questions"][2]["items"][0]
    d["notes"].append({"word": "注の見出し", "gloss": it["choices"][it["answer"]][:40]})

def M_deny(d):
    q = d["questions"][1]
    q["exp"] = re.sub(r"([①-⑤])", r"\1は誤り。", q["exp"], count=1)

def M_untouched(d):
    q = d["questions"][1]; it = q["items"][0]
    gone = "①②③④⑤"[(it["answer"] + 2) % 5]
    q["exp"] = q["exp"].replace(gone, "")

def M_cross(d):
    a4 = d["questions"][3]["items"][0]
    src = a4["choices"][a4["answer"]][:30]
    it3 = d["questions"][2]["items"][0]
    victim = (it3["answer"] + 2) % 5
    it3["choices"][victim] = it3["choices"][victim] + src

def M_ends(d):
    it = d["questions"][3]["items"][0]
    for i in range(len(it["choices"])):
        if i != it["answer"]: it["choices"][i] = it["choices"][i][:-4] + "というのである"

def M_mark(d):
    d["questions"][2]["text"] = d["questions"][2]["text"].replace("傍線部(Ａ)", "傍線部(Ｂ)")

def M_stem_misquote(d):
    d["questions"][0]["text"] = re.sub(r"「([^」]{6})", lambda m: "「" + m.group(1)[:-1] + "ぬ",
                                       d["questions"][0]["text"], count=1)

def M_dup_choice(d):
    it = d["questions"][2]["items"][0]
    it["choices"][(it["answer"] + 1) % 5] = it["choices"][it["answer"]]

def M_latin(d):
    q = d["questions"][2]
    q["exp"] = q["exp"].replace("。", "。financial な", 1)

# --- 正解の位置の層。★answer を直接書き換えると解説の丸数字が先に赤になり、
#     位置の検査に一度も届かない（これが以前の穴）。positions.py を壊して作り直す。
def P_arith(src):   return "POS = {\n" + "".join(f"    {i}: {[((i + j) % 5) + 1 for j in range(7)]},\n" for i in range(1, 7)) + "}"
def P_column(src):  return "POS = {\n" + "".join(f"    {i}: {[1, 2, 3, 4, 5, 2, 4]},\n" for i in range(1, 7)) + "}"
def P_skew(src):    return "POS = {\n" + "".join(f"    {i}: {[1, 2, 1, 2, 1, 2, 1]},\n" for i in range(1, 7)) + "}"

# ---------------------------------------------------------------- check.py の変異
def M_points(d):        d["questions"][1]["points"] = "6点"
def M_nums(d):          d["questions"][4]["nums"] = "30"
def M_note_absent(d):
    """注の語が本文に無い。★(注n) は足さない（足すと連番の検査に先に当たる）"""
    d["notes"][-1] = {"word": "ありもせぬ語", "gloss": d["notes"][-1]["gloss"]}
def M_note_count(d):    d["notes"].append({"word": "笞", "gloss": "番号だけ増やす。"})
def M_gram_absent(d):   d["grammar"].append({"phrase": "ありもせぬ語", "point": "本文に無い語の文法説明。"})
def M_note_ref(d):
    d["questions"][2]["exp"] += f'なお、注{len(d["notes"]) + 3}も参照のこと。'
def M_translation(d):   d["translation"] = "\n\n".join(d["translation"].split("\n\n")[:-1])
def M_level(d):         d["level_no"] = 9
def M_minutes(d):       d["minutes"] = 60
def M_rule_missing(d):  d["rules_used"] = d["rules_used"][:2]
def M_confidence(d):    d["confidence"] = "短い。"

# ---------------------------------------------------------------- check_source.py の変異
def M_passage_char(d):
    s = d["passage"]; i = len(s) // 2
    while i < len(s) and s[i] in "{}/abcwxy()注0123456789\n　 ": i += 1
    d["passage"] = s[:i] + ("ぬ" if s[i] != "ぬ" else "ね") + s[i+1:]

def M_passage_cut(d):
    s = d["passage"]; i = len(s) // 2
    d["passage"] = s[:i] + s[i+20:]

def M_shiryo(d):
    for q in d["questions"]:
        if "【資料】" in q["text"]:
            q["text"] = q["text"].replace("しどけなかりければ", "しどけなかりけるに", 1); return
    raise SystemExit("M_shiryo: 【資料】を持たない回に当てている")

def S_emend_reason(_):
    p = os.path.join(HERE, "sources", "emendations.json")
    d = json.load(open(p, encoding="utf-8"))
    k = next(iter(d)); d[k][0]["理由"] = ""
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def S_emend_stale(_):
    p = os.path.join(HERE, "sources", "emendations.json")
    d = json.load(open(p, encoding="utf-8"))
    k = next(iter(d)); d[k][0]["原典"] = "原典に無い語句をここに書く"
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def S_cut_undeclared(_):
    p = os.path.join(HERE, "sources", "cuts.json")
    json.dump({}, open(p, "w", encoding="utf-8"), ensure_ascii=False)

def S_source_edited(_):
    p = os.path.join(HERE, "sources", "set1.txt")
    t = open(p, encoding="utf-8").read()
    open(p, "w", encoding="utf-8").write(t.replace("今は昔", "いにしへ", 1))

def S_set_missing(_):
    os.remove(os.path.join(SETS, "set6.json"))

#   名前 / 変異 / 回す検査 / 期待する NG の文言 / 当てる回（"shiryo" は資料を持つ回、"all" はデータ以外）
MUTS = [
    ("解説の引用が本文から崩れる",       M_quote,         "audit.py",       "本文にない形で引用している"),
    ("正解肢だけが長い",                 M_long,          "audit.py",       "正解肢だけが長い"),
    ("正解肢だけが短い",                 M_short,         "audit.py",       "正解肢だけが短い"),
    ("長さ順位が正解に偏る",             M_rank,          "audit.py",       "長さ順位の平均", "allsets"),
    ("注が正解の文言を先出し",           M_note_leak,     "audit.py",       "注が正解の文言を先出し"),
    ("解説が正解を否定する",             M_deny,          "audit.py",       "を否定する解説"),
    ("解説が触れていない肢がある",       M_untouched,     "audit.py",       "解説が触れていない肢がある"),
    ("別の設問に答えが漏れる",           M_cross,         "audit.py",       "の設問文・選択肢に出ている"),
    ("誤答の文末だけがそろう",           M_ends,          "audit.py",       "誤答の文末がそろい"),
    ("傍線の記号と設問がずれる",         M_mark,          "audit.py",       "本文の印は"),
    ("設問文の引用が本文と違う",         M_stem_misquote, "audit.py",       "設問文の引用が本文の傍線部と違う"),
    ("選択肢が重複する",                 M_dup_choice,    "audit.py",       "選択肢に重複"),
    ("日本語以外の文字が紛れる",         M_latin,         "audit.py",       "日本語で使わない文字"),
    ("配点の合計が45点でない",           M_points,        "check.py",       "配点合計が"),
    ("解答番号が連番でない",             M_nums,          "check.py",       "解答番号が23〜29の連番でない"),
    ("注が本文に無い語を指す",           M_note_absent,   "check.py",       "が本文に見当たらない"),
    ("本文の注番号が注の数と合わない",   M_note_count,    "check.py",       "(注n)が1からの連番"),
    ("文法が本文に無い語を指す",         M_gram_absent,   "check.py",       "文法:"),
    ("解説が存在しない注を指す",         M_note_ref,      "check.py",       "存在しない注"),
    ("現代語訳の段落が本文と合わない",   M_translation,   "check.py",       "段落 ≠ 現代語訳"),
    ("レベルの指定が範囲外",             M_level,         "check.py",       "level_no が"),
    ("目安時間が階段でない",             M_minutes,       "check.py",       "1分あたりの分量"),
    ("設問の参照ルールが表に無い",       M_rule_missing,  "check.py",       "が「使うルール」の表に無い"),
    ("典拠の確からしさの記録が無い",     M_confidence,    "check.py",       "確からしさの記録が短い"),
    ("本文の1字が原典と違う",            M_passage_char,  "check_source.py", "本文が校訂本文と違う"),
    ("本文の途中が落ちている",           M_passage_cut,   "check_source.py", "本文が校訂本文と違う"),
    ("資料が原典と違う",                 M_shiryo,        "check_source.py", "【資料】が原典と違う", "shiryo"),
    ("改訂の理由が書かれていない",       S_emend_reason,  "check_source.py", "理由が書かれていない", "all"),
    ("改訂の元の形が原典に無い",         S_emend_stale,   "check_source.py", "校訂本文に無い", "all"),
    ("切り出しの申告が無い",             S_cut_undeclared,"check_source.py", "申告と合わない", "all"),
    ("保存してある原典が書き換わる",     S_source_edited, "check_source.py", "本文が校訂本文と違う", "all"),
    ("回が1つ丸ごと消える",              S_set_missing,   "check.py",       "回が足りない", "all"),
]

# positions.py を壊す変異（audit.py の位置の層に、解説を壊さずに届かせる）
POS_MUTS = [
    ("正解の位置が等差になる",   P_arith,  "正解が3小問続けて等差"),
    ("設問の縦の並びが同じ",     P_column, "回をまたいで"),
    ("正解番号が偏る",           P_skew,   "正解番号の偏り"),
]

def pick_target(kind):
    rows = all_sets()
    if kind == "shiryo":
        for S, path in rows:
            if any("【資料】" in q["text"] for q in S["questions"]): return S["id"], path
        raise SystemExit("【資料】を持つ回が1つも無い")
    return rows[-1][0]["id"], rows[-1][1]

def snapshot():
    return {p: open(os.path.join(HERE, p), "rb").read()
            for p in ("sources/emendations.json", "sources/cuts.json", "sources/set1.txt",
                      "src/positions.py")}

def restore(snap, sets_backup=None):
    for p, b in snap.items(): open(os.path.join(HERE, p), "wb").write(b)
    if sets_backup:
        for f, b in sets_backup.items(): open(os.path.join(SETS, f), "wb").write(b)

def main():
    base = {}
    for s in ("audit.py", "check.py", "check_source.py"):
        code, _, err = run(s)
        base[s] = code
        if code: print(f"素の {s} が既に赤（{err.strip()[:80]}）。先にそちらを直すこと。"); return 1
    snap = snapshot()
    sets_backup = {f: open(os.path.join(SETS, f), "rb").read() for f in os.listdir(SETS)}
    holes = []
    for row in MUTS + [(n, None, "audit.py", e, "pos", f) for n, f, e in POS_MUTS]:
        name, fn, script, expect = row[0], row[1], row[2], row[3]
        kind = row[4] if len(row) > 4 else None
        base = None
        try:
            if kind == "pos":
                base = fresh_copy()
                p = os.path.join(base, "src", "positions.py")
                t = open(p, encoding="utf-8").read()
                want = row[5](t)
                open(p, "w", encoding="utf-8").write(re.sub(r"POS = \{.*?\n\}", want, t, flags=re.S))
                remake(base); sid = "全回"
                # ★変異が本当に効いたかを、走らせる前に確かめる。
                #   効いていないのに「検出できず」と出すと、ゲートの穴と区別がつかない
                #   （実際に、バイトコードの取り違えで変異が空振りしていた）。
                got = [it["answer"] + 1 for _q in
                       json.load(open(os.path.join(base, "sets", "set1.json"), encoding="utf-8"))["questions"]
                       for it in _q["items"]]
                if got != json.loads(re.search(r"1: (\[[^\]]*\])", want).group(1)):
                    print(f"★試験の不具合 {name}: 変異が効いていない（set1 の正解が {got} のまま）")
                    holes.append(f"{name}（変異が効いていない＝試験側の不具合）")
                    continue
            elif kind == "allsets":
                for f2, raw in sets_backup.items():
                    if not re.fullmatch(r"set\d+\.json", f2): continue
                    d = json.loads(raw.decode("utf-8")); fn(d)
                    json.dump(d, open(os.path.join(SETS, f2), "w", encoding="utf-8"),
                              ensure_ascii=False, indent=1)
                sid = "全回"
            elif kind == "all":
                fn(None); sid = "全体"
            else:
                sid, target = pick_target(kind)
                d = json.loads(sets_backup[os.path.basename(target)].decode("utf-8")); fn(d)
                json.dump(d, open(target, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            code, hits, err = run(script, base if kind == "pos" else None)
            got = [h for h in hits if expect in h]
            if code == 0:
                holes.append(f"{name}（赤にならない）"); mark = "★穴"
                detail = "検出できず"
            elif not got:
                holes.append(f"{name}（別の検査に当たっている）"); mark = "★穴"
                detail = f"狙い「{expect}」が出ず、代わりに: {hits[0][3:70] if hits else err.strip()[:70]}"
            else:
                mark = "OK "; detail = got[0][3:76]
            print(f'{mark} {sid:4} / {script:16} {name}: {detail}')
        finally:
            restore(snap, sets_backup)
    print()
    if holes:
        print(f"検査の穴 {len(holes)} 件:"); [print("   " + h) for h in holes]; return 1
    print(f"変異試験: {len(MUTS) + len(POS_MUTS)} 種すべて、狙った検査が拾った")
    return 0

if __name__ == "__main__":
    sys.exit(main())
