# -*- coding: utf-8 -*-
"""機械ゲート: 分解 DSL と長文本文の整合を全数検査する。1 件でも落ちたらビルドしない。"""
import re, sys, unicodedata
from core import parse, plain_text, normalize, iter_nodes, ALLOWED_LABELS
from content import PASSAGES, RULE_EXAMPLES, META, RULES, STEPS

ERR = []
WARN = []
MARK_RE = re.compile(r'@(\d+)\{([^{}]*)\}')
# 設問文が「下線部 (N)」で参照する番号と、そこに引用された英文
REF_RE = re.compile(r'下線部\s*\((\d)\)')
QUOTE_RE = re.compile(r'<span class="en">(.*?)</span>')
# 解説文などで許可する HTML タグ（これ以外の < は生タグ扱いで語が消える）
TAG_OK = re.compile(r'</?(?:b|u|i|br|span(?:\s+class="[a-z0-9 _-]+")?)\s*/?>')
ENT_OK = re.compile(r'&(?:lt|gt|amp|nbsp|quot|#\d+);')
# pat の文型宣言 → 主節に必要な最上位ラベル
PAT_NEED = {"第1文型": ("V",), "第2文型": ("V", "C"), "第3文型": ("V", "O"),
            "第4文型": ("V", "O1", "O2"), "第5文型": ("V", "O", "C")}


def err(where, msg):
    ERR.append(f"[NG] {where}: {msg}")


def strip_marks(p):
    return MARK_RE.sub(lambda m: m.group(2), p)


def markup_check(s, where):
    """生タグ・未エスケープの & を弾く。< を書き忘れると Chrome が語を黙って飲み込む。"""
    for m in re.finditer(r'<', s):
        if not TAG_OK.match(s, m.start()):
            err(where, f"未エスケープの '<'（&lt; と書くこと）: …{s[m.start():m.start()+28]}…")
    for m in re.finditer(r'&', s):
        if not ENT_OK.match(s, m.start()):
            err(where, f"未エスケープの '&': …{s[m.start():m.start()+20]}…")
    opens = re.findall(r'<(b|u|i|span)\b', s)
    closes = re.findall(r'</(b|u|i|span)>', s)
    if sorted(opens) != sorted(closes):
        err(where, f"タグの開閉が不一致: open={opens} close={closes}")


def depth_check(root, where):
    """ラベルのダッシュ本数 <= 括弧のネスト深さ を検査（S'' が depth0 に出るなどを弾く）。"""
    def walk(nd, d):
        for k in nd.kids:
            if k.kind == "chunk":
                pr = k.label.count("'")
                if pr > d:
                    err(where, f"ラベル {k.label} の深さ超過（ネスト深さ {d} / ダッシュ {pr}）: {k.text!r}")
            elif k.kind == "group":
                walk(k, d + 1)
    walk(root, 0)


def main():
    total_sent = 0
    mcq_ans_hist = [0, 0, 0, 0]
    total_mcq = 0

    # 巻頭の例文も同じゲートを通す
    for i, ex in enumerate(RULE_EXAMPLES, 1):
        try:
            parse(ex["dsl"])
        except ValueError as e:
            err(f"巻頭例文{i}", f"DSL パース失敗: {e}")

    for P in PASSAGES:
        pid = f'長文{P["no"]} "{P["title"]}"'

        # --- 本文のマーカー -------------------------------------------------
        marks = {}
        for para in P["paras"]:
            for m in MARK_RE.finditer(para):
                n = int(m.group(1))
                if n in marks:
                    err(pid, f"@{n} が重複している")
                marks[n] = normalize(m.group(2))
        want = list(range(1, len(P["sents"]) + 1))
        if sorted(marks) != want:
            err(pid, f"マーカー番号が {sorted(marks)}（期待 {want}）")

        body = normalize(strip_marks(" ".join(P["paras"])))
        for bad in "{}@[]<>":
            if bad in body:
                err(pid, f"本文に記号 {bad!r} が残っている")
        wc = len(re.findall(r"[A-Za-z][A-Za-z'’-]*", body))
        if not (140 <= wc <= 230):
            err(pid, f"語数 {wc} が想定レンジ 140-230 の外")
        P["_wc"] = wc
        P["_body"] = body

        if len(P["sents"]) != 6:
            err(pid, f"分解対象文が {len(P['sents'])} 文（6 文であること）")
        if len(P["fulltrans"]) != len(P["paras"]):
            err(pid, "全訳の段落数が本文と一致しない")

        # --- 各文の分解 -----------------------------------------------------
        for idx, s in enumerate(P["sents"], 1):
            where = f"{pid} (#{idx})"
            total_sent += 1
            try:
                root = parse(s["dsl"])
            except ValueError as e:
                err(where, f"DSL パース失敗: {e}")
                continue

            recon = plain_text(root)
            s["_en"] = recon

            # (a) 分解 → 英文の復元が、本文のマーカー内と 1 文字も違わないこと
            if idx in marks and recon != marks[idx]:
                err(where, "復元英文が本文と不一致\n"
                           f"     本文: {marks[idx]}\n"
                           f"     復元: {recon}")
            # (b) その英文が本文全体にもそのまま存在すること
            if recon not in body:
                err(where, "復元英文が本文中に見つからない")
            # (c) 末尾が文末記号
            if recon[-1:] not in ".?!":
                err(where, f"文末記号が無い: …{recon[-12:]!r}")
            # (d) ラベル深さ
            depth_check(root, where)
            # (e) 主節に述語動詞（V もしくは 助）が最低 1 つ
            top_v = [k for k in root.kids if k.kind == "chunk" and k.label in ("V", "助")]
            if not top_v:
                err(where, "主節の V（述語動詞）ラベルが 1 つも無い")
            # (f) 主節に S が無いのは命令文だけ（pat に「命令文」と明記されていること）
            top_s = [k for k in root.kids if k.kind == "chunk" and k.label in ("S", "真S")]
            top_sg = [k for k in root.kids if k.kind == "group" and k.label in ("S", "真S")]
            if not top_s and not top_sg and "命令文" not in s["pat"]:
                err(where, "主節の S が無い（命令文なら pat に明記すること）")
            # (g) 使用ラベルの棚卸し
            for k in iter_nodes(root):
                if k.kind == "chunk" and k.label not in ALLOWED_LABELS:
                    err(where, f"未許可ラベル {k.label!r}")
            # (h) 解説・和訳の実体
            if len(s.get("notes", [])) < 2:
                err(where, "notes が 2 項目未満")
            if not s.get("ja"):
                err(where, "和訳が空")
            if not re.search(r"第[1-5]文型|命令文|受動態", s["pat"]):
                err(where, f"pat に文型の記載が無い: {s['pat']!r}")
            # (i) pat の文型宣言と、実際に付いている最上位ラベルの整合
            top_lbl = {k.label for k in root.kids if k.label}
            for pat_name, need in PAT_NEED.items():
                if pat_name in s["pat"] and "受動態" not in s["pat"]:
                    miss = [x for x in need if x not in top_lbl]
                    if miss:
                        err(where, f"pat が {pat_name} なのに主節ラベル {miss} が無い"
                                   f"（実際: {sorted(top_lbl)}）")
            # (j) 解説・和訳の HTML 健全性
            for ni, n in enumerate(s["notes"]):
                markup_check(n, f"{where} notes[{ni}]")
            # (k) 和訳が全訳にもそのまま入っていること（ドリフト検出）
            if s["ja"] not in " ".join(P["fulltrans"]):
                err(where, "和訳が fulltrans に見当たらない（訳のドリフト）")

        # --- 語注が本文に実在するか（見出し語の内容語が 1 つでも本文に出れば OK） ---
        STOP = {"be", "do", "the", "one", "ones", "and", "of", "to", "in", "on", "at",
                "for", "with", "as", "so", "a", "an", "that", "it", "not"}
        body_words = set(re.findall(r"[a-z]+", body.lower()))
        def in_body(t):   # 語形変化を許すため 4 文字前方一致で双方向に照合
            return any(bw.startswith(t[:4]) or t.startswith(bw[:4]) for bw in body_words)
        for w, _m in P["vocab"]:
            toks = [t for t in re.findall(r"[a-z]+", w.lower())
                    if len(t) >= 3 and t not in STOP]
            if toks and not any(in_body(t) for t in toks):
                err(pid, f"語注 {w!r} が本文に出現しない（別の長文の語では？）")

        # --- 設問 ------------------------------------------------------------
        mcq_refs = set()
        for qi, q in enumerate(P["mcq"], 1):
            where = f"{pid} 問2-({qi})"
            total_mcq += 1
            markup_check(q["q"], where + " 設問文")
            markup_check(q["exp"], where + " 解説")
            for c in q["choices"]:
                markup_check(c, where + " 選択肢")
            # 参照した下線部番号と、設問文が引用している英文の一致（番号ずれ検出）
            refs = [int(x) for x in REF_RE.findall(q["q"])]
            mcq_refs.update(refs)
            for quote in QUOTE_RE.findall(q["q"]):
                qn = normalize(re.sub(r'<[^>]+>', '', quote))
                if not refs:
                    err(where, f"英文を引用しているのに「下線部 (N)」の指定が無い: {qn!r}")
                elif not any(qn in P["sents"][r - 1].get("_en", "") for r in refs):
                    err(where, f"引用 {qn!r} が下線部 {refs} の文に含まれない（番号ずれ）")
            if len(q["choices"]) != 4:
                err(where, f"選択肢が {len(q['choices'])} 個")
            if not (0 <= q["ans"] < len(q["choices"])):
                err(where, "ans が範囲外")
            else:
                mcq_ans_hist[q["ans"]] += 1
            if len(set(q["choices"])) != len(q["choices"]):
                err(where, "選択肢が重複している")
            if not q.get("exp"):
                err(where, "解説が空")
            # 正解肢だけが極端に長い（テル）の検出
            L = [len(re.sub(r"<[^>]+>", "", c)) for c in q["choices"]]
            if L[q["ans"]] == max(L) and L[q["ans"]] >= min(L) * 2.2:
                WARN.append(f"[warn] {where}: 正解肢が最長かつ他の 2.2 倍以上（長さテル）")

        tns = [t["n"] for t in P["trans"]]
        if len(set(tns)) != len(tns):
            err(pid, f"和訳問題の参照番号が重複: {tns}")
        for t in P["trans"]:
            if not (1 <= t["n"] <= len(P["sents"])):
                err(pid, f"和訳問題の参照番号 {t['n']} が不正")
        # ★問2 で構造を明かした文を問3 の和訳に出すと、採点ポイントを先に開示してしまう
        leak = sorted(set(tns) & mcq_refs)
        if leak:
            err(pid, f"和訳問題 {leak} が問2 でも扱われている（採点ポイントの先出し）"
                     f"／問2 参照={sorted(mcq_refs)}")

        # --- グリフ安全（絵文字・制御文字） ---------------------------------
        def scan(obj, path):
            if isinstance(obj, str):
                for ch in obj:
                    if ord(ch) < 0x20 and ch != "\n":
                        err(pid, f"{path} に制御文字 U+{ord(ch):04X}")
                    if unicodedata.category(ch) == "So" and ch not in "★▲●◆■□◇→←↑↓〜":
                        err(pid, f"{path} に記号/絵文字 {ch!r}（Arial Unicode に無い恐れ）")
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    if not str(k).startswith("_"):
                        scan(v, f"{path}.{k}")
            elif isinstance(obj, (list, tuple)):
                for i, v in enumerate(obj):
                    scan(v, f"{path}[{i}]")
        scan(P, pid)

    # --- 記号名の残留 --------------------------------------------------------
    # ★2026-08-27 に括弧の割り当てを変えた（形容詞＝[ ] / 名詞＝〈 〉/ 副詞＝( )）。
    #   凡例だけ直して解説の地の文が古いままだと、生徒は記号を 2 通り見ることになる。
    #   読み替えの正典は core.DISP_BR。ここはその「言い忘れ」を機械で止める。
    from core import DISP_BR as _DB
    _stale = ("&lt;", "&gt;", "< >", "[ ] … 名詞", "[名詞のカタマリ]")
    def stale_scan(obj, path):
        if isinstance(obj, str):
            for t in _stale:
                if t in obj:
                    err(path, f"古い記号名 {t!r} が残っている: …{obj[:44]}…")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if k != "dsl":          # DSL のソース記号は読み替えの対象外
                    stale_scan(v, f"{path}.{k}")
        elif isinstance(obj, (list, tuple)):
            for i, v in enumerate(obj):
                stale_scan(v, f"{path}[{i}]")
    for _name, _obj in (("RULES", RULES), ("STEPS", STEPS),
                        ("RULE_EXAMPLES", RULE_EXAMPLES), ("PASSAGES", PASSAGES)):
        stale_scan(_obj, _name)

    # --- 正解位置の偏り ------------------------------------------------------
    if total_mcq:
        lo, hi = min(mcq_ans_hist), max(mcq_ans_hist)
        if hi - lo > 1:
            err("設問全体", f"4 択の正解位置が偏っている: {mcq_ans_hist}")

    print("=" * 62)
    print(f"長文 {len(PASSAGES)} 本 / 分解 {total_sent} 文 / 4択 {total_mcq} 問")
    for P in PASSAGES:
        print(f"  長文{P['no']} {P['title']:<26} {P['_wc']:>4} words")
    print(f"4択の正解位置分布 (1234): {mcq_ans_hist}")
    print("=" * 62)
    for w in WARN:
        print(w)
    if ERR:
        print(f"\n*** {len(ERR)} 件の不整合 ***")
        for e in ERR:
            print(e)
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
