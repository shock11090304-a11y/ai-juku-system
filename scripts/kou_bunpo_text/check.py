# -*- coding: utf-8 -*-
"""
高校英文法テキストの機械ゲート。

  python3 check.py            # 刷るもの全部（vol1, vol2 …）を検査する
  python3 check.py vol1       # 巻を絞る

★引数なしの既定は「刷るもの全部」。何を見たかを必ず印字する
  （[[material-gates-single-entry]] の教訓：引数で対象が変わるゲートを
    引数なしで回すと「見本」を検査して緑になる）。

検査する項目
  1. データ健全性  … ja / exp が空でない、ans が範囲内、選択肢に重複が無い
  2. 文字種       … 想定外の文字体系（キリル文字・ハングル等）の混入
  3. 空所         … stem か lines のどちらかに ___ がある（不適当選択型を除く）
  4. 復習テスト    … review の tag がすべて演習に実在し、重複していない
  5. 正解位置     … 大問ごと・巻全体で位置が偏っていないか
  6. 長さの tell   … 正解の選択肢が「いつも最長」になっていないか
  7. 組版         … PDF に OVERFLOW バッジが無い、目次のページ番号が実物と一致
  8. ページ構成    … 各講のページ数が偶数、講扉が偶数ノンブル（＝左ページ）、
                     ポイント【1】の直後が ● 見出し
  9. 見本の型      … 不適当選択型（5択）が各講の大問1 ⑵ にちょうど1問、instr が対応、
                     復習テストは4択だけ
"""
import os, re, sys, glob, importlib, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build  # noqa: E402

VIOLATIONS = []
PDF_MISSING = []
CHECKED = []


def bad(msg):
    VIOLATIONS.append(msg)


# 想定外の文字体系（生成時の取り違え・混入を機械で捕まえる）
FOREIGN = re.compile(
    r"[Ѐ-ӿ"      # キリル
    r"؀-ۿ"       # アラビア
    r"฀-๿"       # タイ
    r"가-힯"       # ハングル
    r"Ͱ-Ͽ]")     # ギリシャ


def walk_strings(obj, path=""):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, "%s.%s" % (path, k))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from walk_strings(v, "%s[%d]" % (path, i))


def check_items(vol, kozas):
    ansdist = collections.Counter()
    longest_is_answer = 0
    total = 0
    for k in kozas:
        seen_tags = set()
        gpos = collections.defaultdict(list)
        for g, n, it in build.all_items(k):
            where = "%s 第%d講 %s(%d)" % (vol, k["no"],
                                         "大問%s" % g.get("no", "-"), n)
            total += 1
            ch = it.get("choices") or []
            if len(ch) < 2:
                bad("%s: 選択肢が足りない" % where)
                continue
            if not isinstance(it.get("ans"), int) or not (0 <= it["ans"] < len(ch)):
                bad("%s: ans が範囲外 (%r)" % (where, it.get("ans")))
                continue
            if len(set(c.strip().lower() for c in ch)) != len(ch):
                bad("%s: 選択肢に重複がある %r" % (where, ch))
            for field in ("ja", "exp"):
                if not (it.get(field) or "").strip():
                    bad("%s: %s が空" % (where, field))
            body = " ".join([it.get("stem", "")] + list(it.get("lines", [])))
            if "___" not in body:
                bad("%s: 空所（___）が無い" % where)
            if it.get("tag"):
                if it["tag"] in seen_tags:
                    bad("%s: tag が重複 %r" % (where, it["tag"]))
                seen_tags.add(it["tag"])
            ansdist[it["ans"]] += 1
            gpos[id(g)].append(it["ans"])
            if len(ch[it["ans"]]) == max(len(c) for c in ch) and \
               sum(1 for c in ch if len(c) == len(ch[it["ans"]])) == 1:
                longest_is_answer += 1

        # 復習テストの tag がすべて実在するか（build 側でも落ちるが先に出す）
        for tag in k.get("review", []):
            if tag not in seen_tags:
                bad("%s 第%d講: 復習テストの tag %r が演習に無い" % (vol, k["no"], tag))
        if len(set(k.get("review", []))) != len(k.get("review", [])):
            bad("%s 第%d講: 復習テストの tag が重複" % (vol, k["no"]))

        # 大問内で正解位置が全部同じ＝生徒に見抜かれる
        for gid, poss in gpos.items():
            if len(poss) >= 3 and len(set(poss)) == 1:
                bad("%s 第%d講: 同じ大問で正解位置が全問 %d 番に固まっている"
                    % (vol, k["no"], poss[0] + 1))

    # 全体の正解位置の偏り（4択のみで判定）
    four = sum(ansdist[i] for i in range(4))
    if four:
        for i in range(4):
            r = ansdist[i] / four
            if r > 0.40 or r < 0.12:
                bad("%s: 正解位置 %d 番の比率が %.0f%%（12〜40%% に収めること）"
                    % (vol, i + 1, r * 100))
    if total and longest_is_answer / total > 0.45:
        bad("%s: 正解が「最も長い選択肢」の問題が %d/%d（45%% 未満にすること）"
            % (vol, longest_is_answer, total))
    CHECKED.append("%s: 設問 %d 問 / 正解位置 %s"
                   % (vol, total, dict(sorted(ansdist.items()))))


def check_quotes(vol, kozas):
    """名言・ことわざの使い回しを止める（同じ格言が2度出ると教材として締まらない）。"""
    seen = {}
    for k in kozas:
        n = 0
        for pg in k["pages"]:
            for b in pg:
                if b["t"] != "quote":
                    continue
                n += 1
                key = b["en"].strip().lower()
                if key in seen:
                    bad("%s 第%d講: 名言が第%d講と重複 → %s" % (vol, k["no"], seen[key], b["en"]))
                seen[key] = k["no"]
                for f in ("en", "by", "ja", "byja", "note"):
                    if not (b.get(f) or "").strip():
                        bad("%s 第%d講: 名言の %s が空" % (vol, k["no"], f))
        if n < 3:
            bad("%s 第%d講: 名言が %d 個しかない（各ポイントに1つ）" % (vol, k["no"], n))
    CHECKED.append("%s: 名言 %d 個を照合" % (vol, len(seen)))


def check_strings(vol, kozas):
    for k in kozas:
        for path, s in walk_strings(k, "第%d講" % k["no"]):
            m = FOREIGN.search(s)
            if m:
                bad("%s %s: 想定外の文字 %r を含む → %s"
                    % (vol, path, m.group(0), s[:40]))


def check_pdf(vol, mod, pdf):
    import fitz
    doc = fitz.open(pdf)
    over = []
    for p in doc:
        t = p.get_text()
        if "OVERFLOW" in t:
            over.append([l for l in t.split("\n") if "OVERFLOW" in l][0])
    for o in over:
        bad("%s: ページからはみ出している → %s" % (vol, o))

    # 目次のページ番号と実物の一致（表紙1枚＋目次1枚のあと本文）
    st = build.page_starts(mod.KOZAS)
    for k in mod.KOZAS:
        idx = st[k["no"]]              # PDF 0起点 index：表紙が index 0、ノンブル N が index N
        if idx >= doc.page_count:
            bad("%s 第%d講: 目次の p%d が実物に無い" % (vol, k["no"], st[k["no"]]))
            continue
        head = doc[idx].get_text().strip().replace("\n", "")[:80]
        if not head.startswith("第%s講" % build.zenkaku_no(k["no"])) or k["title"] not in head:
            bad("%s 第%d講: 目次 p%d の内容が講扉ではない → %r"
                % (vol, k["no"], st[k["no"]], head[:40]))
        if st[k["no"]] % 2:
            bad("%s 第%d講: 講扉が奇数ノンブル p%d（見開き左に来ない）"
                % (vol, k["no"], st[k["no"]]))
    CHECKED.append("%s: 問題編 %d ページ・目次 %d 講を照合" % (vol, doc.page_count, len(mod.KOZAS)))
    doc.close()



def _norm(s):
    """PDF 抽出テキストとデータの照合用：空白（全角含む）を全部落とす。"""
    return re.sub(r"\s+", "", s)


def check_freshness(vol, mod, outdir):
    """content / build.py を直したのにビルドし忘れた古い PDF に緑を出さない。"""
    import hashlib, json
    mp = os.path.join(outdir, "manifest.json")
    if not os.path.exists(mp):
        bad("%s: manifest.json が無い（古い形式のビルド）→ build.py を回し直すこと" % vol)
        return
    man = json.load(open(mp))
    cur = {"content": hashlib.sha256(open(mod.__file__, "rb").read()).hexdigest(),
           "build": hashlib.sha256(open(os.path.join(HERE, "build.py"), "rb").read()).hexdigest()}
    for key in ("content", "build"):
        if man.get(key) != cur[key]:
            bad("%s: %s がビルド後に変更されている（PDF が古い）→ 再ビルド必須" % (vol, key))


def check_mondai_content(vol, mod, pdf):
    """問題編 PDF に全設問の本文が実在するか（鮮度の実測）。"""
    import fitz
    doc = fitz.open(pdf)
    full = _norm("".join(pg.get_text() for pg in doc))
    doc.close()
    total = 0
    for k in mod.KOZAS:
        for g, n, it in build.all_items(k):
            total += 1
            probe = it.get("stem") or (it.get("lines") or [""])[0]
            probe = re.sub(r"\[/?[a-z]\]", "", probe.replace("___", "（　　）"))
            if _norm(probe)[:30] not in full:
                bad("%s 問題編 第%d講: 本文が PDF に無い（古い PDF？）→ %s"
                    % (vol, k["no"], probe[:36]))
    CHECKED.append("%s: 問題編 %d 問の本文を照合" % (vol, total))


def check_kaitou(vol, mod, pdf):
    """解答解説編：見出し・全問の【答】と選択肢・復習解答列・参照ページ・白紙を照合。"""
    import fitz
    doc = fitz.open(pdf)
    full = _norm("".join(pg.get_text() for pg in doc))
    st = build.page_starts(mod.KOZAS)
    n_ans = 0
    for k in mod.KOZAS:
        if _norm("第%s講　%s" % (build.zenkaku_no(k["no"]), k["title"])) not in full:
            bad("%s 解答編: 第%d講の見出しが無い" % (vol, k["no"]))
        for g, n, it in build.all_items(k):
            n_ans += 1
            exp = _norm("%s　【答】%s　%s" % (build.paren(n), build.ans_label(it),
                                             it["choices"][it["ans"]]))
            if exp not in full:
                bad("%s 解答編 第%d講: 【答】が問題編の選択肢と一致しない → %s"
                    % (vol, k["no"], exp[:44]))
        rg = build.build_review_group(k)
        seq = _norm("　".join("%s %s" % (build.paren(i + 1), build.ans_label(it))
                              for i, it in enumerate(rg["items"])))
        if seq not in full:
            bad("%s 解答編 第%d講: 復習テストの解答列が一致しない → %s" % (vol, k["no"], seq))
        if _norm("■復習テスト（問題編 p%d）" % (st[k["no"]] + len(k["pages"]) - 2)) not in full:
            bad("%s 解答編 第%d講: 復習テストの参照ページ番号がずれている" % (vol, k["no"]))
        for pi, pg in enumerate(k["pages"]):
            if any(b["t"] == "enshu" for b in pg):
                if _norm("■入試問題演習（問題編 p%d）" % (st[k["no"]] + pi)) not in full:
                    bad("%s 解答編 第%d講: 演習の参照ページ p%d が無い"
                        % (vol, k["no"], st[k["no"]] + pi))
    for i, pg in enumerate(doc):
        if i and len(_norm(pg.get_text())) < 8:
            bad("%s 解答編: p%d がほぼ白紙（泣き別れの疑い）" % (vol, i))
    doc.close()
    CHECKED.append("%s: 解答編 %d 問の【答】と選択肢・参照ページを照合" % (vol, n_ans))


# 見本（市販の講義式テキスト）の第1講から起こした「1講の型」。
# ★これは体裁・構成の型であって、本文・例文・設問・解説はすべて自作。
FUTEKITOU_INSTR = "⑴，⑶〜⑺は空欄に入る最も適切なものを選びなさい。⑵は不適当なものを選びなさい。"
FUTEKITOU_PAGE = 6          # 見開き左＝ノンブル8。まとめの「■入試問題演習」のページ
FUTEKITOU_POS = 1           # その大問1の ⑵（0起点）


def check_futekitou(vol, kozas):
    """見本と同じ「不適当選択型（5択）」が各講に1問だけ、同じ位置にあるか。

    ★見本は 大問1（7問）の ⑵ だけを5択の不適当選択型にし、instr でそこを名指しする。
      この型が崩れると「4択だけの単元別ドリル」に戻り、見本と別物になる。
    ★5択は復習テストに入れない（見本の復習テストは4択だけ。解答が数字とＡ〜Ｅで混ざる）。
    """
    for k in kozas:
        where = "%s 第%d講" % (vol, k["no"])
        five = [(g, n, it) for g, n, it in build.all_items(k) if len(it["choices"]) == 5]
        if len(five) != 1:
            bad("%s: 不適当選択型（5択）が %d 問（見本は各講ちょうど1問）" % (where, len(five)))
            continue
        pg = k["pages"][FUTEKITOU_PAGE] if len(k["pages"]) > FUTEKITOU_PAGE else []
        es = [b for b in pg if b["t"] == "enshu"]
        if not es:
            bad("%s: p%d に「■入試問題演習」が無い" % (where, FUTEKITOU_PAGE))
            continue
        g0 = es[0]["groups"][0]
        if g0.get("instr") != FUTEKITOU_INSTR:
            bad("%s: 大問1の instr が見本と違う → %r" % (where, g0.get("instr")))
        if len(g0["items"]) <= FUTEKITOU_POS or \
                len(g0["items"][FUTEKITOU_POS]["choices"]) != 5:
            bad("%s: 大問1の ⑵ が5択になっていない（instr が名指しする位置とずれる）" % where)
        elif g0["items"][FUTEKITOU_POS] is not five[0][2]:
            bad("%s: 5択が大問1の ⑵ 以外の位置にある" % where)
        it5 = five[0][2]
        if it5.get("cols") != 5:
            bad("%s: 不適当選択型に cols:5 が無い（見本と同じ3列組にならない）" % where)
        if it5.get("tag"):
            bad("%s: 不適当選択型に復習テストの tag が付いている"
                "（復習テストは4択だけで組む）" % where)
        longest = max(it5["choices"], key=len)
        if it5["choices"][it5["ans"]] == longest and \
                sum(1 for c in it5["choices"] if len(c) == len(longest)) == 1:
            bad("%s: 不適当選択型の答えが5つの中で最長（長さで当てられる）" % where)
    for k in kozas:
        for it in build.build_review_group(k)["items"]:
            if len(it["choices"]) != 5:
                continue
            bad("%s 第%d講: 復習テストに5択が入っている" % (vol, k["no"]))
    CHECKED.append("%s: 不適当選択型（5択）を %d 講ぶん照合" % (vol, len(kozas)))


def check_structure(vol, kozas):
    for k in kozas:
        if len(k["pages"]) % 2:
            bad("%s 第%d講: ページ数が奇数 (%d)" % (vol, k["no"], len(k["pages"])))
        if len(k["index"]) < 2:
            bad("%s 第%d講: ポイントが %d 個しかない" % (vol, k["no"], len(k["index"])))
        # 見本はポイント【1】の直後に必ず ● 見出しが来る（いきなり枠から始めない）
        ts = [b["t"] for b in k["pages"][0]]
        if "ph" in ts and ts[ts.index("ph") + 1] != "h":
            bad("%s 第%d講: ポイント【1】の直後が ● 見出しでない (%s)"
                % (vol, k["no"], ts[ts.index("ph") + 1]))
        last2 = [b["t"] for pg in k["pages"][-2:] for b in pg]
        if last2 != ["review", "note"]:
            bad("%s 第%d講: 末尾が「復習テスト → NOTE」になっていない (%r)"
                % (vol, k["no"], last2))


def main():
    vols = sys.argv[1:] or sorted(
        os.path.basename(p)[8:-3] for p in glob.glob(os.path.join(HERE, "content_*.py")))
    print("検査対象:", ", ".join(vols))
    for vol in vols:
        mod = importlib.import_module("content_" + vol)
        build.balance_answers(mod.KOZAS)   # ビルドと同じ並べ替えを適用してから見る
        check_structure(vol, mod.KOZAS)
        check_futekitou(vol, mod.KOZAS)
        check_strings(vol, mod.KOZAS)
        check_quotes(vol, mod.KOZAS)
        check_items(vol, mod.KOZAS)
        if any(len(k["pages"]) % 2 for k in mod.KOZAS):
            continue   # ページ数が奇数（構造違反は出力済み）。page_starts が assert 死する前に紙面照合を飛ばす
        pdfs = sorted(glob.glob(os.path.join(HERE, "_build", "%s_*" % mod.META["slug"],
                                             "%s_mondai.pdf" % mod.META["slug"])))
        if pdfs:
            outdir = os.path.dirname(pdfs[-1])
            check_freshness(vol, mod, outdir)
            check_pdf(vol, mod, pdfs[-1])
            check_mondai_content(vol, mod, pdfs[-1])
            kp = os.path.join(outdir, "%s_kaitou.pdf" % mod.META["slug"])
            if os.path.exists(kp):
                check_kaitou(vol, mod, kp)
            else:
                PDF_MISSING.append("%s: 解答解説編 PDF が無い（刷る2冊の片方が無検査になる）" % vol)
        else:
            PDF_MISSING.append("%s: ビルド済み PDF が無い（先に build.py を実行すること）" % vol)

    for c in CHECKED:
        print("  ", c)
    if VIOLATIONS:
        print("\nVIOLATION %d 件" % len(VIOLATIONS))
        for v in VIOLATIONS:
            print("  -", v)
        if PDF_MISSING:
            # ★ここで「PDF が無い」と書くと run_all_gates が CI で本物の違反ごと
            #   「PDF待ち」扱いにして隠すので、分類に掛からない言い方にする。
            print("※ PDF未生成のため紙面検査は未実施（build.py を回すこと）")
        sys.exit(1)
    if PDF_MISSING:
        # データは緑で紙だけ無い場合に限り、runner の分類語で報告する
        # （CI=--no-pdf では「ここでは検査していない」扱い、手元では build 忘れとして落ちる）。
        for v in PDF_MISSING:
            print("  -", v)
        sys.exit(1)
    print("\nALL PASS")


if __name__ == "__main__":
    main()
