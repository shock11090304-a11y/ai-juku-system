#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧒 CEO 画面の「中学の単元」が、単元ドリル・入試道場の単元とずれていないかを照合するゲート (run_all_gates.py が拾う)。

    python3 scripts/check_ceo_chugaku_drill_links.py

■ なぜ要るか (2026-09-29)
  中学の単元名は 4 か所に書かれている。1 か所だけ直すと、画面は正常に見えたまま導線だけが黙って切れる。
    - server/main.py の _GRAMMAR_SUBJECT_UNIT_ORDER (単元ドリルの在庫の並び・正典)
    - ceo.html の _CHU_DRILL_UNITS / _CHU_DRILL_LABEL (「やるべきこと」: 高校入試演習の弱点 → 📨 中学ドリルを配信。
      ラベルは道場の topic の前置き「中学数学 …」を見分けるのにも使う)
    - ceo.html の HW_DRILL_TOPICS (🏫 クラス宿題のドリル単元 → 生徒の「📝 ドリルで解く」)
    - dojo-drill.html の CHU_UNIT_PRESETS (宿題の単元を開く入試道場のカード。findPresetForWeakness は
      w_subject='chugaku' のとき中学のカードだけを候補にして topic の完全一致で探し、同じ topic が 2 枚あると開かない。
      filter は道場が記録する弱点の単元名)
  ずれたときの症状:
    - _CHU_DRILL_UNITS に無い単元 → その弱点は「対象外」と出て 📨 が出ない (2026-09-29 まで全単元がこれだった)
    - _CHU_DRILL_UNITS にだけある単元 → 📨 を押すと在庫 0 で 400
    - _CHU_DRILL_LABEL が無い・違う → ボタンが「chugaku_math 正負の数」のような内部名になる / 宿題経由の「中学数学 正負の数」を見分けられない
    - 道場の filter が server の単元と違う → 道場で立った弱点がどのドリルにも対応しない (📨 が出ない)
    - 単元名にかっこ・コロン → ceo.html はそこで切って照合するので 📨 が出ない
    - HW_DRILL_TOPICS の t が道場の topic と違う・道場に同じ topic が 2 枚 → 生徒の「📝 ドリルで解く」が単元を開かず
      「この宿題の単元に対応するドリルが見つかりませんでした」
    - HW_DRILL_TOPICS の s が 'chugaku' でない → 道場が大学のカードと照合する (確率・比較・時制 は同名がある)

■ 見るもの
  1. _CHU_DRILL_UNITS の各科目 == server の _GRAMMAR_SUBJECT_UNIT_ORDER の同じ科目 (集合・重複なし・教科をまたぐ同名なし・
     かっこ/コロン/前後の空白なし)。server に単元順がある中学の科目 (chugaku*) は、すべて _CHU_DRILL_UNITS にもある
  2. _CHU_DRILL_LABEL の科目 == _CHU_DRILL_UNITS の科目で、ラベルは道場の topic の前置き (「中学」＋道場の教科名)
  3. 道場の中学英語・数学・理科のカード (DOJO_SUBJ): topic は「中学<教科> <filter>」、filter は server の単元か、道場だけの単元 (DOJO_ONLY)。
     server の単元はすべて道場にカードがある。中学のカードに同じ topic が 2 枚ない
  4. HW_DRILL_TOPICS の中学の行 (s='chugaku' か t が「中学」で始まる) は s='chugaku' で、t が道場のカードの topic に実在する。
     HW_SUBJS (英語・数学) の道場のカードは、すべて HW_DRILL_TOPICS にある (クラス宿題で選べる)
  ★読めない書き方は「読み漏れ」として落とす。正規表現で読めたものだけ照合すると、読めなかった行が素通りして緑になる
    (2026-09-29 の review で実測)。JS はコメント・文字列・テンプレート (入れ子の ${…} も追う)・正規表現リテラルの中身を空白にしてから
    読む (js_mask)。落とすもの: 宣言が 1 つでない (コメントの中の写しは数えない)・オブジェクト以外の要素 (変数・スプレッド)・
    バッククォートの文字列・HW_DRILL_TOPICS の行のキーが t / s 以外 (大学の行も)・宣言の後からの書き換え
    (JS: 再代入・プロパティ/要素への代入・push 等・push.apply・delete・Object.assign・別名からの書き換え。別名は `var x = NAME` と
    要素の別名 `var u = NAME.k` / `NAME[k]` (`|| []` `?? {}` の既定値つきも) で、宣言のある { … } の中だけを探す、
    server: 再代入・global・別名・del・update / append 等・`NAME[k]` / `.get()` / `.get() or []` / `.items()` の別名からの書き換え
    (内包表記の変数はその式の中だけ)・`NAME[k][:] = …`。値として読む `NAME[k][:]` は写しなので通す)。
    ★見ていないもの: 要素のプロパティをコールバックで書き換えるもの (JS の forEach(x => x.s = …) 等)・別名の別名・
    分割代入/三項演算子/for-of の別名・eval・テンプレートの ${…} の中 (外側のテンプレートごと空白)・server の `NAME[k] if … else []` の
    別名・書き換える関数に NAME[k] を渡すもの・外側 (モジュール直下・外側の関数) で作った別名を内側の関数/lambda で書き換えるもの。
    ★逆に落ちるもの (メッセージで分かる): 宣言を Object.freeze({…}) で包むもの (中身を読めない)・引用符つきのキー・
    IIFE 直下の `var units = NAME…` (同じ IIFE の別の units.push まで拾う)。別の文の Object.freeze(NAME); は書き換えではないので通る。

★読むだけ。どのファイルも書き換えない。外部通信なし。
"""
import ast
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SERVER = os.path.join(ROOT, "server", "main.py")
CEO = os.path.join(ROOT, "ceo.html")
DOJO = os.path.join(ROOT, "dojo-drill.html")

# 単元ドリルの中学の科目 → 入試道場のカードの教科名 (subj)。次の教科 (chugaku_kokugo …) を足したらここにも足す
DOJO_SUBJ = {"chugaku": "英語", "chugaku_math": "数学", "chugaku_rika": "理科"}
# 道場にしか無い単元 (単元ドリルのプールには無い。「やるべきこと」では「対象外」の注記に出る)
DOJO_ONLY = {"英語": {"過去形", "未来形", "不定詞の用法", "長文読解"}, "数学": set(), "理科": set()}
# クラス宿題 (HW_DRILL_TOPICS) で単元を選べるようにしてある教科 = 道場のカードを 1 枚ずつ宿題の単元にも出す
#   (理科は 2026-09-29 時点で宿題の単元に出していない。出すならここに足し、HW_DRILL_TOPICS に s: 'chugaku' で並べる)
HW_SUBJS = ("英語", "数学")
SERVER_NAMES = ("_GRAMMAR_SUBJECT_UNIT_ORDER", "_GRAMMAR_CANON_SUBJECTS")
# server の dict / list / set を書き換えるメソッド (読むだけのメソッド .get / .index / .issuperset … は通す)
MUTATORS = {"append", "extend", "insert", "remove", "pop", "popitem", "clear", "update", "add", "discard",
            "setdefault", "sort", "reverse", "difference_update", "intersection_update",
            "symmetric_difference_update", "__setitem__", "__delitem__", "__iadd__"}
ALIAS_VIA = {"get", "setdefault", "values", "items"}   # 戻り値が中身そのもの (写しではない) になる呼び出し
BAD_NAME = re.compile(r"[（(：:]|^\s|\s$")
JS_MUT = r"(?:push|pop|shift|unshift|splice|sort|reverse|fill|copyWithin)"

STR = r"'((?:[^'\\\n]|\\.)*)'|\"((?:[^\"\\\n]|\\.)*)\""
VAL = rf"(?:{STR}|-?\d+(?:\.\d+)?|true|false)"
_RE_PREV = set("(,=:[!&|?{};+-*%<>~^")
_RE_KW = re.compile(r"(?:^|[^\w$])(?:return|typeof|instanceof|case|do|else|in|of|new|delete|void|throw|yield|await)\s*$")


def js_mask(code):
    """コメント・文字列・テンプレート・正規表現リテラルの中身を空白にする (改行と文字の位置は保つ)。
    テンプレートの ${ … } の中の入れ子のテンプレート・文字列・正規表現も追う (外側のテンプレートは丸ごと空白)。"""
    out, n, i, last = list(code), len(code), 0, ""
    stack, tpl_from = [], None      # stack = 開いている ${ ごとの { の深さ / tpl_from = 一番外のテンプレートの始まり

    def blank(a, b):
        for k in range(max(a, 0), min(b, n)):
            if out[k] != "\n":
                out[k] = " "

    def tpl_text(j):                # テンプレートの地の文を ` か ${ まで読む → (次の位置, ${ を開いたか)
        while j < n:
            if code[j] == "\\":
                j += 2
            elif code[j] == "`":
                return j + 1, False
            elif code.startswith("${", j):
                return j + 2, True
            else:
                j += 1
        return n, False

    while i < n:
        c = code[i]
        if c == "`" or (c == "}" and stack and stack[-1] == 0):
            if c == "}":
                stack.pop()
            elif not stack:
                tpl_from = i
            j, opened = tpl_text(i + 1)
            if opened:
                stack.append(0)
                last = "{"
            else:
                last = "`"
                if not stack and tpl_from is not None:
                    blank(tpl_from + 1, j - 1)
                    tpl_from = None
            i = j
            continue
        if stack and c == "{":
            stack[-1] += 1
        elif stack and c == "}":
            stack[-1] -= 1
        if c in "'\"":
            j = i + 1
            while j < n and code[j] != c:
                if code[j] == "\\":
                    j += 2
                    continue
                if code[j] == "\n":
                    break
                j += 1
            blank(i + 1, j)
            i, last = j + 1, c
            continue
        if code.startswith("//", i):
            j = code.find("\n", i)
            j = n if j < 0 else j
            blank(i, j)
            i = j
            continue
        if code.startswith("/*", i):
            j = code.find("*/", i + 2)
            j = n if j < 0 else j + 2
            blank(i, j)
            i = j
            continue
        if c == "/" and (last == "" or last in _RE_PREV or _RE_KW.search(code[max(0, i - 12):i])):
            j, cls = i + 1, False
            while j < n and code[j] != "\n":
                if code[j] == "\\":
                    j += 2
                    continue
                if code[j] == "[":
                    cls = True
                elif code[j] == "]":
                    cls = False
                elif code[j] == "/" and not cls:
                    break
                j += 1
            blank(i + 1, j)
            i, last = j + 1, "/"
            continue
        if not c.isspace():
            last = c
        i += 1
    if tpl_from is not None:
        blank(tpl_from + 1, n)
    return "".join(out)


def strip_js_comments(src):
    """リテラルの中身から // と /* */ を消す (文字列の中は壊さない。正規表現リテラルの無い配列・オブジェクト専用)。"""
    out, i, n, quote = [], 0, len(src), None
    while i < n:
        c = src[i]
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(src[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in "'\"`":
            quote = c
            out.append(c)
            i += 1
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def strings(s):
    return [a if a or not b else b for a, b in re.findall(STR, s)]


def leftover(s, *patterns):
    for p in patterns:
        s = re.sub(p, "", s, flags=re.S)
    return re.sub(r"[\s,]", "", s)


def script_blocks(html):
    return re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)


def literal_at(code, i):
    """code[i] の { / [ に対応する閉じかっこまでの中身 (文字列とコメントの中のかっこは数えない)。"""
    if i >= len(code) or code[i] not in "{[":
        return None
    depth, quote, j, n = 0, None, i, len(code)
    while j < n:
        c = code[j]
        if quote:
            if c == "\\":
                j += 2
                continue
            if c == quote:
                quote = None
        elif c in "'\"`":
            quote = c
        elif code.startswith("//", j):
            k = code.find("\n", j)
            j = n if k < 0 else k
            continue
        elif code.startswith("/*", j):
            k = code.find("*/", j + 2)
            j = n if k < 0 else k + 2
            continue
        elif c in "{[(":
            depth += 1
        elif c in "}])":
            depth -= 1
            if depth == 0:
                return code[i + 1:j]
        j += 1
    return None


def _line(code, pos):
    return code[code.rfind("\n", 0, pos) + 1:code.find("\n", pos) if code.find("\n", pos) >= 0 else len(code)].strip()


def js_literal(html, name, what, bad):
    """ファイル内でただ 1 つの生きた宣言 `var|let|const NAME = {…}|[…]` の中身 (コメントは除去済み)。
    宣言の後からの書き換え (再代入・代入・push 等・delete・Object.assign・別名から) も見る。"""
    nm = re.escape(name)
    decl = re.compile(rf"\b(?:var|let|const)\s+{nm}\s*=\s*")
    blocks = [(b, js_mask(b)) for b in script_blocks(html)]
    found = [(b, m) for b, mk in blocks for m in decl.finditer(mk)]
    if len(found) != 1:
        bad.append(f"{what} の宣言が {len(found)} 個ある (ちょうど 1 個にすること。コメントの中の写しは数えない)")
        if not found:
            return None
    code, m = found[0]
    body = literal_at(code, m.end())
    if body is None:
        bad.append(f"{what} の中身を読めない (= の直後が {{ か [ でない・かっこが閉じていない)")
        return None
    acc = r"(?:\s*(?:\.\s*[\w$]+|\[[^\]\n]*\]))"
    assign = r"(?:=(?![=>])|[-+*/%]=|\|\|=|&&=|\?\?=)"

    def pats(x):
        return [
            rf"(?<![\w.$]){x}{acc}+\s*{assign}",                                   # NAME.x = / NAME[k] =
            rf"(?<![\w.$]){x}{acc}*\s*\.\s*{JS_MUT}\s*(?:\(|\.\s*(?:apply|call)\s*\()",
            rf"\.\s*{JS_MUT}\s*\.\s*(?:apply|call)\s*\(\s*{x}\b",                   # Array.prototype.push.apply(NAME, …)
            rf"\bdelete\s+{x}\b",
            rf"\bObject\s*\.\s*(?:assign|defineProperty|defineProperties|setPrototypeOf)\s*\(\s*{x}\b",
        ]
    for blk, mk in blocks:
        hits = [re.finditer(p, mk) for p in pats(nm)]
        # 再代入 (宣言そのものは除く)
        hits.append(m2 for m2 in re.finditer(rf"(?<![\w.$]){nm}\s*{assign}", mk)
                    if not re.search(r"\b(?:var|let|const)\s+$", mk[max(0, m2.start() - 24):m2.start()]))
        # `var x = NAME;` / `var u = NAME.k;` / `NAME[k]` の別名 → 別名からの書き換え
        for am in re.finditer(rf"(?:\b(?:var|let|const)\s+|(?<![\w.$]))([\w$]+)\s*=\s*{nm}{acc}*\s*"
                              rf"(?:(?:\|\||\?\?)\s*(?:\[\s*\]|\{{\s*\}})\s*)?(?=[;,)\]}}\n]|$)", mk):
            if am.group(1) != name:
                # 別名は宣言のある { … } の中 (宣言より後) だけで探す。同じ名前の別の変数 (units.push 等) を拾わない
                depth, hi = 0, len(mk)
                for k in range(am.end(), len(mk)):
                    if mk[k] == "{":
                        depth += 1
                    elif mk[k] == "}":
                        if depth == 0:
                            hi = k
                            break
                        depth -= 1
                hits.extend(re.compile(p).finditer(mk, am.start(), hi) for p in pats(re.escape(am.group(1))))
        for it in hits:
            for h in it:
                bad.append(f"{what} を宣言の後から書き換えている: {_line(blk, h.start())[:90]} (このゲートが読めない)")
    return strip_js_comments(body)


def js_objects(body, what, bad):
    """配列の中身 → [{key: value}]。{ } 以外の要素や、key: 値 で読めない中身があれば読み漏れとして落とす。"""
    objs = re.findall(r"\{[^{}]*\}", body)
    rest = leftover(body, r"\{[^{}]*\}")
    if rest:
        bad.append(f"{what} に読めない要素がある (オブジェクト以外): {rest[:80]}")
    out = []
    for o in objs:
        junk = leftover(o[1:-1], rf"\w+\s*:\s*{VAL}")
        if junk:
            bad.append(f"{what} に読めない書き方の行がある: {o[:80]}")
            continue
        d = {}
        for m in re.finditer(rf"(\w+)\s*:\s*({VAL})", o):
            sv = strings(m.group(2))
            d[m.group(1)] = sv[0] if sv else m.group(2)
        out.append(d)
    return out


def server_constants(bad):
    tree = ast.parse(open(SERVER, encoding="utf-8").read())
    got, writes, defs = {}, [], set()

    def root(e, names=SERVER_NAMES, copy_ok=True):
        """式の根の名前 (NAME[k] / NAME.x / NAME.get(k) / NAME.items() … をたどる)。names に無ければ None。
        copy_ok: 値として読むとき (別名の元・メソッドを呼ぶ相手) は NAME[k][:] を写しとみなして None。
        代入先 (NAME[k][:] = … は中身を書き換える) は copy_ok=False で最後までたどる。"""
        while True:
            if copy_ok and isinstance(e, ast.Subscript) and isinstance(e.slice, ast.Slice):
                return None
            if isinstance(e, (ast.Subscript, ast.Attribute, ast.Starred)):
                e = e.value
            elif isinstance(e, ast.Call) and isinstance(e.func, ast.Attribute) and e.func.attr in ALIAS_VIA:
                e = e.func.value
            elif isinstance(e, ast.BoolOp):   # x = NAME.get(k) or [] も別名
                rs = [r for r in (root(v, names, copy_ok) for v in e.values) if r]
                return rs[0] if rs else None
            else:
                break
        return e.id if isinstance(e, ast.Name) and e.id in names else None

    def names_in(t):
        if isinstance(t, ast.Name):
            return [t.id]
        if isinstance(t, (ast.Tuple, ast.List)):
            return [x for e in t.elts for x in names_in(e)]
        return []

    for node in tree.body:   # 正典の定義 = モジュール直下の 1 回だけの代入
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            for t in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                if isinstance(t, ast.Name) and t.id in SERVER_NAMES:
                    defs.add(id(node))
                    if t.id in got:
                        writes.append(f"{t.id} を 2 回代入している (line {node.lineno})")
                    try:
                        got[t.id] = ast.literal_eval(node.value)
                    except ValueError:
                        writes.append(f"{t.id} がリテラルでない (line {node.lineno}・frozenset(...) や dict(...) も不可)")
                        got[t.id] = None

    def check_writes(nodes, names, label):
        for node in nodes:
            tgts = []
            if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                tgts = node.targets if isinstance(node, ast.Assign) else [node.target]
            elif isinstance(node, ast.Delete):
                tgts = node.targets
            for t in tgts:
                if isinstance(t, ast.Name):
                    # 名前そのものへの代入: 正典は定義以外すべて / 別名は += (list の中身が変わる) だけ
                    if t.id in names and ((names is SERVER_NAMES and id(node) not in defs) or isinstance(node, ast.AugAssign)):
                        writes.append(f"{label(t.id)} を後から書き換えている (line {node.lineno})")
                    continue
                r = root(t, names, copy_ok=False)
                if r:
                    writes.append(f"{label(r)} を後から書き換えている (line {node.lineno})")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in MUTATORS:
                r = root(node.func.value, names)
                if r:
                    writes.append(f"{label(r)}.{node.func.attr}(...) で後から書き換えている (line {node.lineno})")

    all_nodes = list(ast.walk(tree))
    check_writes(all_nodes, SERVER_NAMES, lambda r: r)
    for node in all_nodes:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(getattr(node, "value", None), ast.Name) \
                and node.value.id in SERVER_NAMES:
            writes.append(f"{node.value.id} に別名を付けている (line {node.lineno}・別名からの書き換えを追えない)")
        if isinstance(node, ast.Global):
            for g in node.names:
                if g in SERVER_NAMES:
                    writes.append(f"関数の中で global {g} している (line {node.lineno})")

    # 別名 (x = NAME[k] / NAME.get(k) / for k, v in NAME.items()) からの書き換え。関数ごとのスコープで見る
    def scope_nodes(sc):
        stack = list(ast.iter_child_nodes(sc))
        while stack:
            n = stack.pop()
            yield n
            if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                stack.extend(ast.iter_child_nodes(n))

    comps = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)   # 内包表記の変数はその式の中だけの名前
    scopes = [tree] + [n for n in all_nodes if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda) + comps)]
    for sc in scopes:
        nodes = list(scope_nodes(sc))
        aliases = {}
        for node in nodes:
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None \
                    and not isinstance(node.value, ast.Name) and root(node.value):
                for t in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                    for a in names_in(t):
                        aliases[a] = root(node.value)
            elif (isinstance(node, (ast.For, ast.AsyncFor)) or (isinstance(sc, comps) and node in sc.generators)) \
                    and root(node.iter):
                for a in names_in(node.target):
                    aliases[a] = root(node.iter)
        if aliases:
            check_writes(nodes, set(aliases), lambda a: f"{aliases[a]} の別名 {a}")
    for w in writes:
        bad.append(f"server/main.py: {w} — 単元の正典は 1 つのリテラルで書くこと (このゲートが読めない)")
    return got


def main():
    bad = []
    srv = server_constants(bad)
    order = srv.get("_GRAMMAR_SUBJECT_UNIT_ORDER") or {}
    canon = srv.get("_GRAMMAR_CANON_SUBJECTS") or set()
    if not order or not canon:
        print("❌ server/main.py から _GRAMMAR_SUBJECT_UNIT_ORDER / _GRAMMAR_CANON_SUBJECTS を読めない")
        for b in bad:
            print("   ❌ " + b)
        return 1
    ceo = open(CEO, encoding="utf-8").read()
    dojo = open(DOJO, encoding="utf-8").read()

    # --- 1. ceo.html: _CHU_DRILL_UNITS ---
    ceo_units = {}
    body = js_literal(ceo, "_CHU_DRILL_UNITS", "ceo.html の _CHU_DRILL_UNITS", bad)
    if body is not None:
        for k, v in re.findall(r"(\w+)\s*:\s*\[(.*?)\]", body, re.S):
            ceo_units[k] = strings(v)
            if leftover(v, STR):
                bad.append(f"_CHU_DRILL_UNITS[{k}] に文字列以外の要素がある: {leftover(v, STR)[:60]}")
        rest = leftover(body, r"\w+\s*:\s*\[.*?\]")
        if rest:
            bad.append(f"_CHU_DRILL_UNITS に読めない要素がある: {rest[:60]}")
    print("  ceo.html _CHU_DRILL_UNITS: " + ", ".join(f"{k} {len(v)}単元" for k, v in ceo_units.items()))
    if not ceo_units:
        bad.append("_CHU_DRILL_UNITS に科目が 1 つも読めない")
    for subj, units in ceo_units.items():
        if subj not in canon or not subj.startswith("chugaku"):
            bad.append(f"_CHU_DRILL_UNITS の科目 {subj!r} が server の中学の科目 (_GRAMMAR_CANON_SUBJECTS の chugaku*) に無い")
            continue
        if len(units) != len(set(units)):
            bad.append(f"_CHU_DRILL_UNITS[{subj}] に重複がある: {units}")
        for u in units:
            if BAD_NAME.search(u):
                bad.append(f"_CHU_DRILL_UNITS[{subj}] の単元名「{u}」にかっこ・コロン・前後の空白がある (ceo.html はそこで切って照合する)")
        want = order.get(subj)
        if want is None:
            bad.append(f"server の _GRAMMAR_SUBJECT_UNIT_ORDER に {subj} が無い (単元名の正典が無い)")
        elif set(units) != set(want):
            bad.append(f"_CHU_DRILL_UNITS[{subj}] が server の単元とずれている: "
                       f"ceo にだけある={sorted(set(units) - set(want))} / server にだけある={sorted(set(want) - set(units))}")
    for subj in sorted(k for k in order if k.startswith("chugaku")):
        if subj not in ceo_units:
            bad.append(f"server に中学の科目 {subj} の単元があるのに ceo.html の _CHU_DRILL_UNITS に無い "
                       f"(その教科の弱点が「やるべきこと」で「対象外」になる)")
    seen = {}
    for subj, units in ceo_units.items():
        for u in units:
            if u in seen and seen[u] != subj:
                bad.append(f"単元名「{u}」が {seen[u]} と {subj} の両方にある (弱点の単元名から教科を決められない)")
            seen[u] = subj

    # --- 2. ceo.html: _CHU_DRILL_LABEL ---
    labels = {}
    lbody = js_literal(ceo, "_CHU_DRILL_LABEL", "ceo.html の _CHU_DRILL_LABEL", bad)
    if lbody is not None:
        for m in re.finditer(rf"(\w+)\s*:\s*({STR})", lbody):
            labels[m.group(1)] = strings(m.group(2))[0]
        rest = leftover(lbody, rf"\w+\s*:\s*(?:{STR})")
        if rest:
            bad.append(f"_CHU_DRILL_LABEL に読めない要素がある: {rest[:60]}")
    if set(labels) != set(ceo_units):
        bad.append(f"_CHU_DRILL_LABEL の科目 {sorted(labels)} が _CHU_DRILL_UNITS の科目 {sorted(ceo_units)} と違う "
                   f"(ボタンが「chugaku_math …」のような内部名になる)")
    for subj in ceo_units:
        if subj not in DOJO_SUBJ:
            bad.append(f"このゲートの DOJO_SUBJ に {subj} が無い (入試道場のどの教科のカードかを足すこと)")
        elif labels.get(subj) != "中学" + DOJO_SUBJ[subj]:
            bad.append(f"_CHU_DRILL_LABEL[{subj}] が {labels.get(subj)!r} (道場の topic の前置き「中学{DOJO_SUBJ[subj]}」と違う → "
                       f"宿題経由の「中学{DOJO_SUBJ[subj]} …」の弱点を見分けられない)")

    # --- 3. dojo-drill.html: CHU_UNIT_PRESETS ---
    presets = []
    pbody = js_literal(dojo, "CHU_UNIT_PRESETS", "dojo-drill.html の CHU_UNIT_PRESETS", bad)
    if pbody is not None:
        presets = js_objects(pbody, "CHU_UNIT_PRESETS", bad)
    by_subj = {}
    for p in presets:
        by_subj.setdefault(p.get("subj", "?"), []).append(p)
    print(f"  dojo-drill.html CHU_UNIT_PRESETS: {len(presets)} 枚 (" + ", ".join(f"{s} {len(v)}" for s, v in by_subj.items()) + ")")
    if not presets:
        bad.append("CHU_UNIT_PRESETS のカードが 1 枚も読めない")
    topics = [p.get("topic") for p in presets]
    for t in sorted({t for t in topics if topics.count(t) > 1}, key=str):
        bad.append(f"道場の中学のカードに topic「{t}」が {topics.count(t)} 枚ある (findPresetForWeakness が選べず宿題が開かない)")
    dojo_topics = set(topics)
    for drill_subj, dsubj in DOJO_SUBJ.items():
        units = set(order.get(drill_subj) or [])
        for u in sorted(units):
            if BAD_NAME.search(u):
                bad.append(f"server の {drill_subj} の単元名「{u}」にかっこ・コロン・前後の空白がある (ceo.html はそこで切って照合する)")
        cards = by_subj.get(dsubj, [])
        filters = {p.get("filter") for p in cards}
        for p in cards:
            f, t = p.get("filter"), p.get("topic")
            if t != f"中学{dsubj} {f}":
                bad.append(f"道場の中学{dsubj}のカード {p.get('name')!r}: topic {t!r} が「中学{dsubj} {f}」でない")
            if f not in units and f not in DOJO_ONLY.get(dsubj, set()):
                bad.append(f"道場の中学{dsubj}のカード filter {f!r} が server の {drill_subj} の単元にも DOJO_ONLY にも無い "
                           f"(道場で立った弱点がどのドリルにも対応しない)")
        for u in sorted(units - filters):
            bad.append(f"server の {drill_subj} の単元「{u}」に道場のカードが無い (宿題で出せない・道場の弱点とつながらない)")

    # --- 4. ceo.html: HW_DRILL_TOPICS ---
    hw = []
    hbody = js_literal(ceo, "HW_DRILL_TOPICS", "ceo.html の HW_DRILL_TOPICS", bad)
    if hbody is not None:
        hw = js_objects(hbody, "HW_DRILL_TOPICS", bad)
    for r in hw:
        if set(r) != {"t", "s"}:
            bad.append(f"HW_DRILL_TOPICS の行のキーが t / s でない: {r}")
    chu_hw = [r for r in hw if r.get("s") == "chugaku" or str(r.get("t", "")).startswith("中学")]
    print(f"  ceo.html HW_DRILL_TOPICS: {len(hw)} 行 (うち中学 {len(chu_hw)} 行)")
    if not hw:
        bad.append("HW_DRILL_TOPICS の行が 1 つも読めない")
    for r in chu_hw:
        t, s = r.get("t"), r.get("s")
        if s != "chugaku":
            bad.append(f"HW_DRILL_TOPICS「{t}」の s が {s!r} (中学は 'chugaku' 固定。道場が大学のカードと照合してしまう)")
        if t not in dojo_topics:
            bad.append(f"HW_DRILL_TOPICS「{t}」が道場の CHU_UNIT_PRESETS の topic に無い (「📝 ドリルで解く」が単元を開かない)")
    hw_topics = {r.get("t") for r in hw}
    for dsubj in HW_SUBJS:
        for p in by_subj.get(dsubj, []):
            if p.get("topic") not in hw_topics:
                bad.append(f"道場の中学{dsubj}のカード「{p.get('topic')}」が HW_DRILL_TOPICS に無い (クラス宿題で選べない)")

    if bad:
        print(f"\n❌ 中学の単元のずれ {len(bad)} 件")
        for b in bad:
            print("   ❌ " + b)
        return 1
    print("\n✅ 中学の単元は server・ceo.html (弱点ドリル / クラス宿題)・入試道場で一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
