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

def M_mark_bracket(d):
    """傍線の引き始めを、かぎかっこの外へ1字ずらす。
       ★線はかぎかっこの内側に引く（第1版と本番の冊子の引き方）。外へ出ると設問側の引用符と
         見分けがつかなくなる。実際にこの形が6回中5回に入っていたが、開閉の個数を数える検査は
         どれも通っていた＝個数だけでは位置のずれは絶対に出てこない。"""
    d["passage"] = re.sub(r"([「『])\{\{([abcwxy])\}\}", r"{{\2}}\1", d["passage"], count=1)

def M_mark_shift(d):
    """傍線の範囲を1字だけ内側へずらす（設問の引用と食い違わせる）。
       開き1個・閉じ1個は保たれるので、個数を数える検査では出てこない。"""
    d["passage"] = re.sub(r"\{\{([abc])\}\}(.)", r"\2{{\1}}", d["passage"], count=1)

def M_kill_order(d):
    """解説の潰す順を入れかえる（生徒は自分の番号を探して読むので順が飛ぶと読み返しになる）"""
    q = d["questions"][2]
    parts = re.split(r"(?<=。)", q["exp"])
    head = [i for i, t in enumerate(parts) if re.match(r"^\s*[①-⑤]", t)]
    if len(head) >= 2:
        i, j = head[0], head[1]
        parts[i], parts[j] = parts[j], parts[i]
    q["exp"] = "".join(parts)

def M_note_ruby(d):
    """注の見出し語から、本文が付けている読み仮名を落とす。
       ★末尾に読み仮名がある注だけを壊すと、「語の途中に付く形」（国の政(まつりごと)したため行ふ）の
         穴を踏まない。途中に付いているものを優先して壊す。"""
    mid = [n for n in d["notes"] if re.search(r"\([ぁ-んァ-ヶー]+\).", n["word"])]
    for n in (mid or d["notes"]):
        if re.search(r"\([ぁ-んァ-ヶー]+\)", n["word"]):
            n["word"] = re.sub(r"\([ぁ-んァ-ヶー]+\)", "", n["word"]); return

def M_base(d):
    """底本の記録を消す"""
    d.pop("base", None)

def M_mark_order(d):
    """本文の傍線の記号の順を入れかえる（(ア)(イ)(ウ) が出てくる順）"""
    p = d["passage"]
    a = re.search(r"\{\{a\}\}(.*?)\{\{/a\}\}", p, re.S)
    b = re.search(r"\{\{b\}\}(.*?)\{\{/b\}\}", p, re.S)
    if not (a and b): return
    p = p[:a.start()] + "{{b}}" + a.group(1) + "{{/b}}" + p[a.end():b.start()] + "{{a}}" + b.group(1) + "{{/a}}" + p[b.end():]
    d["passage"] = p

def M_stale(d):
    """刷るデータだけを書きかえて、原稿と食い違わせる（make_sets.py の回し忘れ）"""
    d["lead"] = d["lead"].replace("次の文章", "この文章", 1)

def M_tell(d):
    """誤答だけに出る言い回しを増やす（本文を読まずに誤答を切れる状態にする）"""
    for q in d["questions"]:
        for it in q["items"]:
            for i in range(len(it["choices"])):
                if i != it["answer"]:
                    it["choices"][i] = it["choices"][i].rstrip("。") + "というものである。"

def M_tell_one(d):
    """1つの回の中だけで、誤答にだけ出る言い回しを作る（6回合算では薄まって見えない）"""
    for q in d["questions"]:
        for it in q["items"]:
            for i in range(len(it["choices"])):
                if i != it["answer"]:
                    it["choices"][i] = it["choices"][i].rstrip("。") + "てしまったのだ。"

def M_swap_kill(d):
    """解説の「② は…」「⑤ は…」の述語だけを入れ替える（丸数字はそのまま）。
       ★1文1肢に割るとき、執筆順の添字と述語の対応を取り違える事故が実際に3か所起きた。
         刷り上がりを読まないと気づけない種類の誤りなので、機械で見張る。"""
    for q in d["questions"]:
        for it in q["items"]:
            lab = it.get("label", "")
            lines = q["exp"].split("\n")
            for li, ln in enumerate(lines):
                if lab and not ln.startswith(lab): continue
                m = re.search(r"よって\s*[①-⑤\s]+。(.*)$", ln)
                if not m: continue
                parts = [t for t in re.split(r"(?<=。)", m.group(1)) if t.strip()]
                singles = [i for i, t in enumerate(parts)
                           if len(re.findall(r"[①-⑤]", re.match(r"^\s*[①-⑤\s]*", t).group(0))) == 1]
                if len(singles) < 2: continue
                i, j = singles[0], singles[1]
                hi = re.match(r"^\s*[①-⑤\s]*", parts[i]).group(0)
                hj = re.match(r"^\s*[①-⑤\s]*", parts[j]).group(0)
                parts[i], parts[j] = hi + parts[j][len(hj):], hj + parts[i][len(hi):]
                lines[li] = ln[:m.start(1)] + "".join(parts)
                q["exp"] = "\n".join(lines)
                return

def M_anaphora(d):
    """潰し文に「これも」を入れて、前の文を受ける形にする"""
    for q in d["questions"]:
        parts = re.split(r"(?<=。)", q["exp"])
        for i, t in enumerate(parts):
            m = re.match(r"^(\s*[①-⑤]\s*は)(.+)$", t)
            if m and "いずれも" not in t:
                parts[i] = m.group(1) + "これも" + m.group(2)
                q["exp"] = "".join(parts); return

def M_anaphora2(d):
    """潰し文の**末尾**で前の文を受ける（文頭に置く変異だけだと、ガードの見える位置しか試せない）"""
    for q in d["questions"]:
        parts = re.split(r"(?<=。)", q["exp"])
        for i, t in enumerate(parts):
            if re.match(r"^\s*[①-⑤]\s*は", t) and "いずれも" not in t and "よって" not in t:
                parts[i] = t.rstrip("。") + "、そのような記述も本文にない。"
                q["exp"] = "".join(parts); return

# ---------------------------------------------------------------- check.py の判定表そのものを壊す変異
#   ★体裁の検査（check_style）は刷ったPDFを渡したときしか動かない＝CI では一度も実行されない。
#     壊れても誰も気づかないまま「体裁は見ている」と言い続けることになるので、
#     check.py の中に判定表の自己テスト（selftest_style）を置き、ここではその自己テストが
#     本当に鳴るか＝検査の中身を1つ消したら赤くなるかを確かめる。
SRC_MUTS = [
    ("体裁: 記号が全角かどうかを見なくなる",
     '    for lab in ("ア", "イ", "ウ", "Ａ", "Ｂ"):\n'
     '        if f"（{lab}）" in txt:\n'
     '            v.append(f"傍線の記号が全角の（{lab}）になっている（半角かっこ＋縦中横で1マスに収める）")',
     "    pass", "「記号が全角」を崩しても拾わない"),
    ("体裁: 記号の高さを見なくなる",
     '        if h > 14:\n'
     '            v.append(f"傍線の記号 {t} が縦に{h:.1f}pt（1マス＝約11ptに収めること）")',
     "        pass", "「記号が縦に3マス」を崩しても拾わない"),
    ("体裁: 配点の漢数字を見なくなる",
     '    for word, why in (("配点四五点", "配点は漢数字"), ("得点／四五", "得点欄の満点は漢数字")):\n'
     '        if txt.count(word) != n_sets:\n'
     '            v.append(f"「{word}」が{txt.count(word)}回（{n_sets}回あるべき／{why}）")',
     "    pass", "「配点が算用数字」を崩しても拾わない"),
    ("体裁: 見出しの漢数字を見なくなる",
     '    for sid in ids:\n'
     '        if f"第四問（古文）演習問題第{sid}回" not in txt:\n'
     '            v.append(f"第{sid}回の見出しが「第四問（古文）　演習問題　第{sid}回」でない")',
     "    pass", "「見出しが算用数字」を崩しても拾わない"),
    ("体裁: 記号の数を見なくなる",
     '    if len(found) != 5 or any(c != n_sets for c in found.values()):\n'
     '        v.append(f"傍線の記号の数が合わない {dict(found)}（5種×{n_sets}回）")',
     "    pass", "「記号が1つ足りない」を崩しても拾わない"),
]

EXTRA = [
    ("版面: 注番号の列またぎを見なくなる",
     "    return bool(xs) and max(xs) - min(xs) > 6", "    return False",
     "列をまたいだ注番号を見逃す"),
    ("版面: 紙に墨が乗っているかを見なくなる",
     "    return bool(area) and dark / area >= floor", "    return True",
     "真っ白な所を「墨あり」と言う"),
    ("版面: 罫の長さに対して字が足りないのを見なくなる",
     "    need = max(1, int(length / 10.4) - 1)", "    need = 1",
     "を right と言う（lonely のはず）"),
    ("潰す順: 読む順の昇順を見なくなる",
     '    flat = [n for b in blocks for n in b]\n'
     '    if flat != sorted(flat): return f"読む順に並べると昇順でない {[x + 1 for x in flat]}"',
     "    pass", "飛び番号のかたまりを拾えていない"),
    ("設問: かぎかっこの入れ子を見なくなる",
     "        if ch == \"「\":\n"
     "            depth += 1\n"
     "            if depth >= 2: out.append(s[max(0, i - 10):i + 14])",
     "        if False:\n            pass",
     "かぎかっこの入れ子を見逃す"),
    ("版面: ほぼ白紙のページを見なくなる",
     "    return 0 < len(body) < 4",
     "    return False", "2行しか無いページを見逃す"),
    ("版面: フッターを落とさなくなる",
     '    return [l for l in txt.split("\\n")\n'
     '            if l.strip() and "TRILLION" not in l and not re.fullmatch(r"\\s*\\d+\\s*/\\s*\\d+\\s*", l)]',
     '    return [l for l in txt.split("\\n") if l.strip()]',
     "フッターとノンブルを落とせていない"),
]

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
    ("傍線がかぎかっこにかかる",         M_mark_bracket,  "check.py",       "線がかぎかっこにかかっている"),
    ("傍線の範囲が設問の引用とずれる",   M_mark_shift,    "check.py",       "設問の引用と違う"),
    ("解説が誤答を潰す順が崩れる",       M_kill_order,    "check.py",       "誤答を潰す順で"),
    ("注の見出しから読み仮名が落ちる",   M_note_ruby,     "check.py",       "が本文の形と違う"),
    ("底本の記録が消える",               M_base,          "check.py",       "底本（base）が記録されていない"),
    ("傍線の記号の順が入れかわる",       M_mark_order,    "check.py",       "出てくる順が入れかわっている"),
    ("刷るデータだけ原稿とずれる",       M_stale,         "check.py",       "make_sets.py を回し忘れ"),
    ("誤答だけに出る言い回しが増える",   M_tell,          "audit.py",       "誤答に偏っていて", "allsets"),
    ("1つの回の中だけで手がかりが出る", M_tell_one,      "audit.py",       "この回だけ解く生徒に手がかり"),
    ("解説と肢の対応が入れかわる",       M_swap_kill,     "audit.py",       "入れかわっている疑い", "allsets"),
    ("潰し文が前の文を受ける",           M_anaphora,      "check.py",       "前の文を受けている"),
    ("潰し文が文末で前の文を受ける",     M_anaphora2,     "check.py",       "前の文を受けている"),
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
    for row in (MUTS + [(n, None, "audit.py", e, "pos", f) for n, f, e in POS_MUTS]
                + [(n, None, "check.py", e, "src", (old, new)) for n, old, new, e in SRC_MUTS + EXTRA]):
        name, fn, script, expect = row[0], row[1], row[2], row[3]
        kind = row[4] if len(row) > 4 else None
        base = None
        try:
            if kind == "src":
                # 検査の中身を1つ消して、判定表の自己テストがそれを言い当てるかを見る
                base = fresh_copy()
                pth = os.path.join(base, "check.py")
                t = open(pth, encoding="utf-8").read()
                old, new = row[5]
                if old not in t:
                    print(f"★試験の不具合 {name}: 消すはずの検査が check.py に見当たらない")
                    holes.append(f"{name}（消す対象が見当たらない＝試験側の不具合）"); continue
                open(pth, "w", encoding="utf-8").write(t.replace(old, new, 1))
                sid = "判定表"
            elif kind == "pos":
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
            code, hits, err = run(script, base if kind in ("pos", "src") else None)
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
    print(f"変異試験: {len(MUTS) + len(POS_MUTS) + len(SRC_MUTS) + len(EXTRA)} 種すべて、狙った検査が拾った")
    return 0

if __name__ == "__main__":
    sys.exit(main())
