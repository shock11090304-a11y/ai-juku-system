#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_instagram_carousel.py の見張りが本当に効くかを、変異試験で機械的に固定する。

★検査を書いただけでは「検査した」ことにならない。ガードを 1 つ消しても
  緑のままなら、その検査は最初から無力。ここは vol データや設定をわざと壊し、
  「壊したら必ず落ちる」ことを 1 件ずつ確かめる。

★危ない入力は**最後のスライド**に仕込む。先頭に置くと「先頭しか見ていない検査」でも
  偶然通ってしまい、空振りに気づけない (CLAUDE.md の指摘)。

出力は捕まえて外に出さない。壊した検査の "✗" をそのまま印字すると、
run_all_gates.py が「exit 0 なのに違反を印字している (INCONSISTENT)」と判定する。
"""
import copy
import io
import contextlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_vol as BV                 # noqa: E402
import theme_vol as T                  # noqa: E402
import check_instagram_carousel as G   # noqa: E402


def _run(vol):
    """検査を回して、見つかった違反の一覧を返す (印字は捨てる)。"""
    bad = []
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        G.check_vol(vol, bad)
    return bad


def _last(vol):
    """最後のスライド (検査の目に入りにくい位置)。"""
    return vol["slides"][-1]


# ── 変異 ──────────────────────────────────────────────────────────────
def m_unclosed(v):
    _last(v)["blocks"][2]["value"] = "[u]閉じ忘れた見出し"


def m_unknown_tag(v):
    _last(v)["blocks"][2]["value"] = "[zz]知らないタグ[/zz]"


def m_page_number(v):
    _last(v)["n"] = 99


def m_quote_not_in_passage(v):
    _last(v)["blocks"].append(BV.B("quote", ["This sentence is not in the passage."]))


def m_stray_english(v):
    _last(v)["blocks"].append(BV.B("dashnote", "覚え方: [s]never trust a bare as[/s]"))


def m_undeclared_claim(v):
    _last(v)["blocks"].append(BV.B("source", "出典: 東京大学 2024年 英語 第1問"))


def m_declared_but_absent(v):
    v["unverified"] = list(v["unverified"]) + ["本文のどこにも書いていない主張"]


def m_script_in_fig(v):
    _last(v)["blocks"].append(BV.B("fig", '<svg><script>alert(1)</script></svg>'))


def m_onload_in_fig(v):
    _last(v)["blocks"].append(BV.B("fig", '<svg onload="x()"></svg>'))


def m_class_collision(v):
    # 部品の修飾子がレイアウト用クラスと同名になった状態を再現する
    _last(v)["blocks"].append(BV.B("dashnote", "衝突", ctr=True))
    G.BV.COMPONENTS["dashnote"] = lambda b: '<div class="dashnote mid">衝突</div>'


def m_unknown_component(v):
    _last(v)["blocks"].append(BV.B("nonexistent_component", "x"))


def m_render_drops_handle(v):
    """★データ側を書き換えても意味がない。出力もそこから作られるので同語反復になり、
    検査は「食い違い」を見たことにならない (最初これで素通しさせた)。
    本当に守りたいのは「描画側がブランド行を落とす」壊れ方なので、そちらを仕込む。"""
    orig = BV.render_slide
    BV.render_slide = lambda vol, sl: orig(vol, sl).replace(vol["handle"], "")
    return lambda: setattr(BV, "render_slide", orig)


MUTATIONS = [
    ("記法の閉じ忘れ", m_unclosed),
    ("知らない記法タグ", m_unknown_tag),
    ("ページ番号のずれ", m_page_number),
    ("本文に無い英文を引用", m_quote_not_in_passage),
    ("地の文に紛れた英文", m_stray_english),
    ("宣言していない出典の断言", m_undeclared_claim),
    ("宣言したのに本文に無い", m_declared_but_absent),
    ("図版に <script>", m_script_in_fig),
    ("図版に on* 属性", m_onload_in_fig),
    ("クラス名の衝突", m_class_collision),
    ("知らない部品", m_unknown_component),
    ("描画がブランド行を落とす", m_render_drops_handle),
]


def main():
    base = BV.load_vols()
    if not base:
        print("[NG] vols/ に vol が 1 つも無い — 変異試験の土台が無い")
        return 1

    fails = []

    # まず「壊していない状態は通る」ことを確かめる (常に落ちる検査は検査ではない)
    for v in base:
        if _run(copy.deepcopy(v)):
            fails.append(f"{v['key']}: 壊していないのに違反が出る (検査が過敏)")

    saved = dict(BV.COMPONENTS)
    for name, mut in MUTATIONS:
        ok = False
        for v in base:
            w = copy.deepcopy(v)
            undo = None
            try:
                undo = mut(w)
                ok = ok or bool(_run(w))
            except Exception:
                ok = True  # 例外で止まるのも「捕まえた」うち
            finally:
                if callable(undo):
                    undo()
                BV.COMPONENTS.clear()
                BV.COMPONENTS.update(saved)
        if not ok:
            fails.append(f"変異「{name}」を仕込んでも検査が素通しした")

    # PNG の寸法・天地の判定 (純関数なので直に叩く)
    geo = [
        ("実寸ちがい", ((100, 100), 48, 39)),
        ("天がずれる", ((G.PNG_W, G.PNG_H), 200, 39)),
        ("地が広すぎる", ((G.PNG_W, G.PNG_H), 48, 130)),
        ("地が狭すぎる", ((G.PNG_W, G.PNG_H), 48, 2)),
        ("真っ暗", ((G.PNG_W, G.PNG_H), None, 0)),
    ]
    for label, args in geo:
        if not G.judge_geometry("x.png", *args):
            fails.append(f"変異「PNG:{label}」を仕込んでも判定が素通しした")
    if G.judge_geometry("x.png", (G.PNG_W, G.PNG_H), 48, 39):
        fails.append("正しい PNG の寸法・余白なのに判定が落ちる (過敏)")

    # 書体スタックの見張り
    sans = T.SANS
    try:
        T.SANS = '"Hiragino Sans",sans-serif'
        b = []
        G.check_fonts(b)
        if not b:
            fails.append("変異「書体スタックの先頭を和文以外に」を素通しした")
    finally:
        T.SANS = sans

    total = len(MUTATIONS) + len(geo) + 1
    print(f"変異試験: {total} 種を仕込んで、全部が捕まるかを見た "
          f"(対象 {[v['key'] for v in base]})")
    if fails:
        print(f"\n[NG] 素通しした変異 {len(fails)} 件:")
        for f in fails:
            print(f"  ✗ {f}")
        return 1
    print(f"[OK] {total} 種すべてを検査が捕まえた / 素通し 0 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
