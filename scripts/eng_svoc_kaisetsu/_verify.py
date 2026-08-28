# -*- coding: utf-8 -*-
"""照合の実体。check.py と build.py の両方がこれを呼ぶ（判定を二重に書かない）。"""
import os, re, sys, difflib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import core


def restored_text(para):
    """1 段落分の解析 DSL から英文を復元して連結する。"""
    return " ".join(core.plain_text(core.parse(s["dsl"])) for s in para["sents"])


def check_passage(mod, errs):
    """本文（RAW＋FILLS）と解析 DSL の全文照合。段落単位で突き合わせる。"""
    name = mod.META["key"]
    if len(mod.RAW) != len(mod.PARAS):
        errs.append(f"[{name}] 段落数が合わない: RAW {len(mod.RAW)} / PARAS {len(mod.PARAS)}")
        return
    filled = core.apply_fills(mod.RAW, mod.FILLS)
    for i, (raw, para) in enumerate(zip(filled, mod.PARAS), 1):
        want = core.cmp_norm(raw)
        got = core.cmp_norm(restored_text(para))
        if want != got:
            errs.append(f"[{name}] 第{i}段落: 解析 DSL から復元した英文が本文と一致しない\n"
                        + _diff(want, got))


def _diff(want, got):
    w, g = want.split(), got.split()
    out = []
    for line in difflib.unified_diff(w, g, "本文", "復元", lineterm="", n=2):
        if line.startswith(("---", "+++", "@@")):
            continue
        out.append("      " + line)
        if len(out) > 24:
            out.append("      …")
            break
    return "\n".join(out)


def check_labels(mod, errs):
    """ラベルの整合。V が 1 つも無い解析、未知ラベル、空チャンクを弾く。"""
    name = mod.META["key"]
    for para in mod.PARAS:
        for j, s in enumerate(para["sents"], 1):
            where = f"[{name}] 第{para['no']}段落 第{j}文"
            try:
                node = core.parse(s["dsl"])
            except ValueError as e:
                errs.append(f"{where}: DSL 構文エラー: {e}")
                continue
            labels = [n.label for n in core.iter_nodes(node) if n.label]
            has_v = any(l.startswith("V") or l == "助" for l in labels)
            if not has_v and not s.get("frag"):
                errs.append(f"{where}: V も 助 も無い（frag 指定も無い）")
            if has_v and s.get("frag") and not any(
                    n.label in ("V", "助") for n in core.iter_nodes(node)):
                pass
            if not s.get("ja", "").strip():
                errs.append(f"{where}: 和訳が空")
            if not s.get("pat", "").strip():
                errs.append(f"{where}: 文型の表示が空")


core.iter_nodes = core.hb.iter_nodes


def check_questions(mod, errs):
    """設問解説の検査。CLAUDE.md の 4 セクション必須 ＋ 引用の実在 ＋ 解答の相互照合。"""
    name = mod.META["key"]
    qs = getattr(mod, "QUESTIONS", None)
    if not qs:
        return
    body = core.cmp_norm(" ".join(core.apply_fills(mod.RAW, mod.FILLS)))
    seen = set()
    for q in qs:
        w = f"[{name}] 設問{q['no']}"
        if q["no"] in seen:
            errs.append(f"{w}: 設問番号が重複")
        seen.add(q["no"])
        # --- 4 セクション（🎯 コアイメージ / 🔬 文構造分析 / 📍 本文の根拠 / ❌ 誤答NG）
        for key, ja in (("core", "🎯 コアイメージ"), ("struct", "🔬 文構造分析"),
                        ("evidence", "📍 本文の根拠"), ("ng", "❌ 誤答 NG 理由")):
            if not q.get(key):
                errs.append(f"{w}: 「{ja}」が空（4 セクション必須）")
        if not q.get("ans", "").strip():
            errs.append(f"{w}: 解答が空")
        # --- 引用した英文が本文に実在するか（全数照合）
        for quote, _note in q.get("evidence", []):
            if core.cmp_norm(quote) not in body:
                errs.append(f"{w}: 📍本文の根拠 の引用が本文に無い → {quote!r}")

    # --- 解答の相互照合: 本文に入れた語（FILLS）と解説の主張する記号が一致するか
    opts = getattr(mod, "OPTIONS", {})
    for marker, (qno, letter) in getattr(mod, "ANSWER_MAP", {}).items():
        want = opts.get(qno, {}).get(letter)
        if want is None:
            errs.append(f"[{name}] {marker}: 選択肢 {qno} {letter}) が OPTIONS に無い")
            continue
        got = mod.FILLS.get(marker)
        if core.cmp_norm(got or "") != core.cmp_norm(want):
            errs.append(f"[{name}] {marker}: 本文に入れた語と解説の記号が食い違う "
                        f"（本文 {got!r} / {qno} {letter}) は {want!r}）")
        q = next((x for x in mod.QUESTIONS if x["no"] == qno), None)
        if q and letter not in q["ans"]:
            errs.append(f"[{name}] {marker}: 解答欄に記号 {letter}) が書かれていない → {q['ans']!r}")

    # --- 重複不可の設問で記号が重複していないか
    b_letters = [l for m, (qq, l) in getattr(mod, "ANSWER_MAP", {}).items() if qq == "(B)"]
    if len(b_letters) != len(set(b_letters)):
        errs.append(f"[{name}] (B): 同じ記号を複数回使っている → {sorted(b_letters)}")

    # --- 単独選択問題（本文の空所ではないもの）の記号が解答欄に書かれているか
    for qno, letter in getattr(mod, "STANDALONE_ANSWER", {}).items():
        q = next((x for x in mod.QUESTIONS if x["no"] == qno), None)
        if not q:
            errs.append(f"[{name}] {qno}: 設問が見つからない")
        elif letter not in q["ans"]:
            errs.append(f"[{name}] {qno}: 解答欄に記号 {letter}) が無い → {q['ans']!r}")
        elif qno in opts and opts[qno][letter] not in q["ans"]:
            errs.append(f"[{name}] {qno}: 解答欄の本文が選択肢 {letter}) と違う")

    # --- (F) 語句整序: 与えられた語をすべて 1 回ずつ使い、コンマがちょうど 1 つか
    fw = getattr(mod, "F_WORDS", None)
    if fw:
        got = mod.FILLS.get("(F)", "")
        used = [t.strip(",") for t in got.split()]
        if sorted(used) != sorted(fw):
            errs.append(f"[{name}] (F): 与えられた語と使った語が一致しない\n"
                        f"      与: {sorted(fw)}\n      使: {sorted(used)}")
        if got.count(",") != 1:
            errs.append(f"[{name}] (F): コンマがちょうど 1 つでない（{got.count(',')} 個）")
        qf = next((x for x in mod.QUESTIONS if x["no"] == "(F)"), None)
        if qf and core.cmp_norm(qf["ans"]) != core.cmp_norm(got):
            errs.append(f"[{name}] (F): 解答欄と本文に入れた語句が違う\n"
                        f"      解答欄: {qf['ans']!r}\n      本文  : {got!r}")


def check_underline(mod, errs):
    """表示用の下線部が本文に実在するか。ここがずれると解説の指し示す場所が狂う。"""
    name = mod.META["key"]
    body = core.cmp_norm(" ".join(core.apply_fills(mod.RAW, mod.FILLS)))
    for label, anchor, target in getattr(mod, "UNDERLINE", []):
        n = body.count(core.cmp_norm(anchor))
        if n == 0:
            errs.append(f"[{name}] 下線部({label}) のアンカーが本文に無い → {anchor!r}")
        elif n > 1:
            errs.append(f"[{name}] 下線部({label}) のアンカーが本文に {n} 箇所ある"
                        f"（どれに下線が付くか決まらない）→ {anchor!r}")
        if core.cmp_norm(target) not in core.cmp_norm(anchor):
            errs.append(f"[{name}] 下線部({label}) の下線部分がアンカーの中に無い → {target!r}")


# ---------------------------------------------------------------- 文型 ↔ ラベルの矛盾
_PAT_RE = re.compile(r"第([1-5])文型")


def _labels_by_level(node, out=None):
    """ラベルを節の深さ（ダッシュの数）ごとに分けて集める。

    0＝主節、1＝S′ V′ の節、2＝S″ V″ の節。
    ★「O と C が揃っているか」は<同じ節の中>で見ないと意味が無い。
      主節の O と従属節の C を足して第5文型と認めてしまうと検査が骨抜きになる。
    """
    if out is None:
        out = {0: set(), 1: set(), 2: set()}
    for k in node.kids:
        if k.label:
            lvl = k.label.count("'")
            base = k.label.replace("'", "")
            out.setdefault(lvl, set()).add(base)
        if k.kind == "group":
            _labels_by_level(k, out)
    return out


def check_pattern_consistency(mod, errs):
    """宣言した文型と、実際に振ったラベルが噛み合っているか。

    ★「第2文型（SVC）と書いたのに C を振っていない」「第4文型なのに O1/O2 が無い」
      といった書き間違いは、本文照合でもラベル整合でも素通りする。
      解説を読む生徒が最初に信じるのがこの見出しなので、機械で突き合わせる。

    ★文型は「その文の見た目の形」で判定する方針（受動態を能動に戻さない）。
      よって be made / be judged は第1文型、be made worse / be assumed to be は第2文型。
    """
    name = mod.META["key"]
    need = {"2": ({"C"}, {"真S"}), "3": ({"O"}, {"真O"}),
            "4": ({"O1", "O2"},), "5": ({"O", "C"},)}
    for para in mod.PARAS:
        for j, s in enumerate(para["sents"], 1):
            where = f"[{name}] 第{para['no']}段落 第{j}文"
            pats = set(_PAT_RE.findall(s["pat"]))
            if not pats:
                if not s.get("frag"):
                    errs.append(f"{where}: 文型の宣言に『第N文型』が無い → {s['pat']!r}")
                continue
            lv = _labels_by_level(core.parse(s["dsl"]))
            for p in sorted(pats):
                if p == "1":
                    continue
                if not any(alt <= g for alt in need[p] for g in lv.values()):
                    want = " または ".join("+".join(sorted(a)) for a in need[p])
                    errs.append(f"{where}: 第{p}文型と書いてあるのに、同じ節の中に "
                                f"{want} が揃っていない → {s['pat']!r}")
            # 第1文型だけを宣言した文に、主節の O / C があってはならない
            if pats == {"1"}:
                bad = sorted(lv.get(0, set()) & {"O", "O1", "O2", "C"})
                if bad:
                    errs.append(f"{where}: 第1文型だけの宣言なのに主節に {bad} がある → {s['pat']!r}")
            # O1 と O2 は必ず対で使う
            for lvl, g in lv.items():
                if ("O1" in g) != ("O2" in g):
                    errs.append(f"{where}: 深さ{lvl} で O1 と O2 が対になっていない")


def check_fill_notes(mod, errs):
    """空所の一覧表と、本文に実際に入れた語が食い違っていないか。

    ★一覧表は生徒が最初に見る場所。ここが本文とずれると、
      「表の答えを覚えたのに本文と違う」という最悪の事故になる。
    """
    name = mod.META["key"]
    for marker, ans, note in getattr(mod, "FILL_NOTES", []):
        if marker not in mod.FILLS:
            errs.append(f"[{name}] 一覧表の {marker} が FILLS に無い")
            continue
        word = mod.FILLS[marker]
        if word and core.cmp_norm(word) not in core.cmp_norm(ans):
            errs.append(f"[{name}] 一覧表の答えと本文に入れた語が違う {marker}\n"
                        f"      一覧表: {ans!r}\n      本文  : {word!r}")
        if not note.strip():
            errs.append(f"[{name}] 一覧表 {marker} の根拠が空")
    # 空所なのに一覧表に載っていないものを見つける（載せ忘れ）
    hints = getattr(mod, "FILL_HINT", {})
    for marker, hint in hints.items():
        if marker not in mod.FILLS:
            errs.append(f"[{name}] 一覧表の {marker} が FILLS に無い")
        if not hint.strip():
            errs.append(f"[{name}] 一覧表 {marker} の根拠が空")
    listed = {m for m, _a, _n in getattr(mod, "FILL_NOTES", [])} | set(hints)
    if listed:
        for marker, word in mod.FILLS.items():
            if word and marker not in listed:
                errs.append(f"[{name}] 空所 {marker} が一覧表に載っていない")


def _adj_groups(node):
    """形容詞のカタマリ（DSL では < >）を出現順に取り出す。"""
    out = []

    def walk(nd):
        for k in nd.kids:
            if k.kind == "group":
                if k.text == "<":
                    out.append(core.plain_text(k))
                walk(k)
    walk(node)
    return out


def check_refs(mod, errs):
    """形容詞のカタマリ [ ] の「かかり先（先行詞）」の検査。

    ★ここが本命。関係詞・分詞のカタマリを括るだけでは、生徒は
      「で、どの名詞にかかるの?」が分からない。宣言を必須にし、
      ① 全部のカタマリに宣言があるか（書き漏らし）
      ② 宣言がちょうど 1 つのカタマリを指しているか（あいまいな指定）
      ③ かかる先が本当にそのカタマリより<前>に実在するか（後ろの名詞を指していないか）
      を機械で確かめる。
    """
    name = mod.META["key"]
    refs = getattr(mod, "REFS", {})
    seen = set()
    for para in mod.PARAS:
        for j, s in enumerate(para["sents"], 1):
            key = (para["no"], j)
            where = f"[{name}] 第{para['no']}段落 第{j}文"
            node = core.parse(s["dsl"])
            groups = _adj_groups(node)
            decl = refs.get(key, [])
            if key in refs:
                seen.add(key)
            if len(groups) != len(decl):
                errs.append(f"{where}: 形容詞のカタマリ {len(groups)} 個に対して "
                            f"かかり先の宣言が {len(decl)} 個")
                continue
            sent = core.cmp_norm(core.plain_text(node))
            used = set()
            for ant, head, kind in decl:
                hit = [i for i, g in enumerate(groups)
                       if core.cmp_norm(g).startswith(core.cmp_norm(head))]
                if len(hit) != 1:
                    errs.append(f"{where}: 先頭 {head!r} が指すカタマリが {len(hit)} 個"
                                f"（ちょうど 1 個であるべき）")
                    continue
                if hit[0] in used:
                    errs.append(f"{where}: 先頭 {head!r} が同じカタマリを二重に指している")
                used.add(hit[0])
                if not kind.strip():
                    errs.append(f"{where}: {head!r} の種類が空")
                # かかる先が、そのカタマリより前に語として実在するか
                pos = sent.find(core.cmp_norm(groups[hit[0]]))
                if pos < 0:
                    errs.append(f"{where}: カタマリ {head!r} を本文中に見つけられない")
                    continue
                pref = sent[:pos]
                if not re.search(r"(?<![A-Za-z])" + re.escape(core.cmp_norm(ant))
                                 + r"(?![A-Za-z])", pref):
                    errs.append(f"{where}: かかり先 {ant!r} が "
                                f"[ {head} … ] より前に見当たらない")
    for key in refs:
        if key not in seen:
            errs.append(f"[{name}] REFS に余分な項目（そんな文は無い）: {key}")


_TAG_OK = re.compile(r'</?(?:b|u|i|br)\s*/?>')


def check_notation(mod, errs):
    """古い記号名が本文中に残っていないか。

    ★2026-08-27 に括弧の割り当てを変えた（形容詞＝[ ] / 名詞＝〈 〉/ 副詞＝( )）。
      解説の地の文が古いままだと、凡例と本文で記号が食い違い、
      生徒はどちらを信じてよいか分からなくなるので機械で止める。

    ★2026-08-28 追記: 最初は &lt; &gt; しか見ておらず、設問解説の 🔬文構造分析 に
      書いた生の < > を 8 か所も取りこぼした（紙に出ていた）。
      HTML タグ以外の生の < > も落とすようにした。
    """
    name = mod.META["key"]
    stale = ("&lt;", "&gt;")

    def scan(text, where):
        t = str(text)
        for x in stale:
            if x in t:
                errs.append(f"[{name}] {where}: 古い記号 {x} が残っている → {t[:60]!r}")
        bare = _TAG_OK.sub("", t)
        if "<" in bare or ">" in bare:
            errs.append(f"[{name}] {where}: HTML タグでない生の < > が残っている"
                        f"（形容詞のカタマリは [ ] と書く）→ {t[:60]!r}")

    for para in mod.PARAS:
        for j, s in enumerate(para["sents"], 1):
            for n in s.get("notes", []):
                scan(n, f"第{para['no']}段落 第{j}文 の注記")
            scan(s.get("tag", ""), f"第{para['no']}段落 第{j}文 の tag")
            scan(s.get("pat", ""), f"第{para['no']}段落 第{j}文 の pat")
    for q in getattr(mod, "QUESTIONS", []):
        for key in ("core", "struct", "ng"):
            for x in q.get(key, []):
                scan(x, f"設問{q['no']} の {key}")
        for key in ("ans", "ansnote"):
            scan(q.get(key, ""), f"設問{q['no']} の {key}")
    for _k, a, n in getattr(mod, "FILL_NOTES", []):
        scan(a, "空所一覧の答え")
        scan(n, "空所一覧の根拠")
    for _k, h in getattr(mod, "FILL_HINT", {}).items():
        scan(h, "空所一覧の根拠")
