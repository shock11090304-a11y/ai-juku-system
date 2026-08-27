#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
刷り上がり（PDF）からの逆照合 — 相互チェックの第 1 層

★これは「ソースを検査する check.py」とは<独立した経路>。
  同じ正典（RAW / PARAS / QUESTIONS）から作った PDF を**もう一度読み直して**、
  本文・全解析文・全設問の解答・全引用が紙の上に実在するかを確かめる。
  ビルドの取りこぼし（CSS で隠れた・改ページで消えた・そもそも出力されていない）は
  ソース検査では絶対に見えないので、この層が要る。

  python3 scripts/eng_svoc_kaisetsu/check_pdf.py [PDFのパス]

CI では回せない（PDF はリポジトリに無い生成物）。
PDF が無ければ「刷った PDF が無い」と言って落ちる＝ build を回し忘れている合図。
run_all_gates.py は --no-pdf のときだけこのゲートを外し、外したことを一覧に出す。
"""
import os, re, sys
import pymupdf                      # ← run_all_gates.needs_pdf がこれを見て --no-pdf 対象と判定する

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import core, _verify

DEFAULT_PDF = os.path.join(HERE, "_out", "英文構造解析_慶應経済2018-1_東大2018-5.pdf")
# ソースの括弧と、紙に刷るときの読み替え後の括弧（core.DISP_BR）の両方を落とす
BRACKETS = set("()[]<>") | {b for pair in core.DISP_BR.values() for b in pair}
LABELS = set(core.ALLOWED_LABELS)

# 日本語フォントに無い字が豆腐で出ていないか（CLAUDE.md 2026-08-02）
TOFU = re.compile(r"[�□]")


def squash(s):
    """空白と引用符を全部落とす。改行位置・ハイフン折り返しの影響を受けなくする。"""
    return re.sub(r'[\s "“”]+', "", str(s))


def pdf_stream(doc):
    """PDF の全文から『ラベルと括弧だけの行』を除いた文字列を作る。

    分解図は 1 語 1 セルなので、抽出すると語とラベルが交互に行として出てくる。
    ラベル行を落とせば英文だけが残り、原文と直接つき合わせられる。

    ★ページ内のブロックは<b>縦位置で並べ直す</b>。get_text() の既定は
      PDF の内容ストリーム順で、Chrome は帯や見出しを後ろに吐くことがある。
      並べ直さないと、ページをまたいだ段落の途中に見出しが割り込んで偽の不一致が出る。
    ★下端の柱（ページ番号）は本文ではないので落とす。落とさないと、
      ページをまたいだ段落の切れ目にページ番号が挟まる。
    """
    keep = []
    for page in doc:
        foot = page.rect.height - 30
        blocks = [b for b in page.get_text("blocks") if b[1] < foot]
        blocks.sort(key=lambda b: (round(b[1], 1), round(b[0], 1)))
        for b in blocks:
            for line in b[4].split("\n"):
                s = line.replace(" ", "").strip()
                if not s or s in LABELS or (len(s) == 1 and s in BRACKETS):
                    continue
                keep.append(s)
    return squash("\n".join(keep))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF
    print("=" * 68)
    print("刷り上がり（PDF）からの逆照合")
    print(f"対象: {path}")
    print("=" * 68)
    if not os.path.exists(path):
        print(f"✗ 刷った PDF が無い: {path}")
        print("  先に `python3 scripts/eng_svoc_kaisetsu/build.py` を回すこと。")
        return 1

    doc = pymupdf.open(path)
    stream = pdf_stream(doc)
    raw_all = "".join(p.get_text() for p in doc)
    print(f"  {doc.page_count} ページ / 抽出 {len(stream):,} 文字\n")

    import content_keio2018 as K, content_todai2018 as T
    errs = []

    if TOFU.search(raw_all):
        errs.append("豆腐（□ / U+FFFD）が紙に出ている＝フォントに無い字を使っている")

    for mod in (K, T):
        name = mod.META["key"]
        n_ok = 0
        # 紙には下線部の印「(A)」「(9)」等が刷り足してある。
        # モジュールが宣言したラベルだけを取り除いてから照合する（それ以外は 1 文字も許さない）。
        # ★下線部が「正しい語の直後」に 1 回だけ刷られているかを数える。
        #   ラベル単独（"(A)" 等）を数えると設問番号まで拾ってしまうので、
        #   「下線を引く語 ＋ その印」という並びで照合する。
        #   下線がビルドで落ちても本文照合は通ってしまうので、この層が要る。
        pstream = stream
        for lb, _a, target in getattr(mod, "UNDERLINE", []):
            pat = squash(target) + squash(f"({lb})")
            n_mark = stream.count(pat)
            if n_mark != 1:
                errs.append(f"[{name}] 下線部({lb}) が「{target[:40]}」の直後に "
                            f"{n_mark} 個（1 個であるべき）")
            pstream = pstream.replace(pat, squash(target))
        # ① 本文が紙に載っているか（段落単位）
        for i, para in enumerate(core.apply_fills(mod.RAW, mod.FILLS), 1):
            if squash(para) not in pstream:
                errs.append(f"[{name}] 本文 第{i}段落が紙に無い（または崩れている）")
            else:
                n_ok += 1
        # ② 全解析文が紙に載っているか
        n_s = 0
        for p in mod.PARAS:
            for j, s in enumerate(p["sents"], 1):
                eng = core.plain_text(core.parse(s["dsl"]))
                if squash(eng) not in stream:
                    errs.append(f"[{name}] 解析 {p['no']}-{j} の英文が紙に無い → {eng[:56]!r}")
                else:
                    n_s += 1
                if squash(s["ja"]) not in squash(raw_all):
                    errs.append(f"[{name}] 解析 {p['no']}-{j} の和訳が紙に無い")
        # ③ 設問の解答・引用・4 セクションが紙に載っているか
        n_q = 0
        for q in getattr(mod, "QUESTIONS", []):
            if squash(q["ans"]) not in squash(raw_all):
                errs.append(f"[{name}] 設問{q['no']} の解答が紙に無い → {q['ans'][:44]!r}")
            else:
                n_q += 1
            for quote, _ in q["evidence"]:
                if squash(quote) not in stream:
                    errs.append(f"[{name}] 設問{q['no']} の引用が紙に無い → {quote[:44]!r}")
            for head in ("コアイメージ", "文構造分析", "本文の根拠"):
                if squash(head) not in squash(raw_all):
                    errs.append(f"[{name}] 設問{q['no']} のセクション「{head}」が紙に無い")
        print(f"[{name}] 本文 {n_ok}/{len(mod.RAW)} 段落 ／ 解析 {n_s} 文 ／ 解答 {n_q} 問 — 紙で確認")

    print()
    if errs:
        for e in errs:
            print(f"  ✗ VIOLATION: {e}")
        print("=" * 68)
        print(f"✗ {len(errs)} 件。刷り上がりと正典が食い違っている。")
        return 1
    print("=" * 68)
    print("✓ ALL PASS — 正典と刷り上がりが全数一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
