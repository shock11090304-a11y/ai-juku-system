#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_instagram_carousel.py の見張りが本当に効くかを、変異試験で機械的に固定する。

★検査を書いただけでは「検査した」ことにならない。ガードを 1 つ消しても緑のままなら、
  その検査は最初から無力。ここは vol データや描画をわざと壊し、
  「壊したら**意図したガードが**鳴る」ことを 1 件ずつ確かめる。

★以前ここで 2 つ空振りを作った。同じ穴を掘らないこと:
  ① 「違反が 1 件でも出れば合格」にすると、**別のガードが鳴っただけ**で通る。
     実際に 18 種のうち 9 種が巻き添えで捕まっており、本命のガードを消しても緑だった。
     → 変異ごとに「鳴るべきガードの文言」(expect) を宣言し、それが出たかで判定する。
  ② `except Exception: ok = True` は、無関係な例外まで「捕まえた」に数える。
     → 例外は文字列にして違反リストに混ぜ、expect と照合する。例外そのものは合格にしない。
  ③ 複数の vol で OR を取ると、1 冊が免疫でも「全部捕まえた」と出る。
     → vol ごとに AND を取る。
  ④ 危ない入力は**最後のスライド**に仕込む。先頭に置くと「先頭しか見ていない検査」でも
     偶然通ってしまう (CLAUDE.md の指摘)。

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
    """検査を回して、見つかった**違反の一覧**を返す (印字は捨てる)。

    ★例外は違反に混ぜない。混ぜると「たまたま落ちた」だけで合格になり、
      見張りを消しても緑のままになる (実際にそうなっていた)。
      見張りは「違反として報告する」ところまでやって初めて仕事をしている。
    """
    bad = []
    try:
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            G.check_vol(vol, bad)
            G.check_caption(vol, bad)
    except Exception:  # noqa: BLE001  例外は「捕まえた」に数えない
        pass
    return bad


def _last(vol):
    """最後のスライド (検査の目に入りにくい位置)。"""
    return vol["slides"][-1]


# ── データを壊す変異 ──────────────────────────────────────────────────
def m_unclosed(v):
    _last(v)["blocks"][2]["value"] = "[u]閉じ忘れた見出し"


def m_unknown_tag(v):
    _last(v)["blocks"][2]["value"] = "[zz]知らないタグ[/zz]"


def m_page_number(v):
    _last(v)["n"] = 99


def m_quote_not_in_passage(v):
    _last(v)["blocks"].append(BV.B("quote", ["This sentence is not in the passage."]))


def m_quote_reordered(v):
    """本文の離れた場所から切り出した行を並べ替えて、本文に無い主張を作る。"""
    _last(v)["blocks"].append(
        BV.B("quote", ["Louis Armstrong purportedly saw", "consciousness"]))


def m_stray_english(v):
    _last(v)["blocks"].append(BV.B("dashnote", "覚え方: [s]never trust a bare as[/s]"))


def m_stray_english_hyphen(v):
    """区切りをハイフンにしただけで素通りしていた形。"""
    _last(v)["blocks"].append(BV.B("dashnote", "合言葉: [s]never-trust-a-bare-as[/s]"))


def m_stray_english_zenkaku(v):
    _last(v)["blocks"].append(BV.B("lead", "Trust　the　rule,　not　the　meaning"))


def m_undeclared_claim(v):
    _last(v)["blocks"].append(BV.B("source", "出典: 東京大学 2024年 英語 第1問"))


def m_claim_abbrev(v):
    """「出典」「大学」を避けた略称の断言。以前はこれで素通りした。"""
    _last(v)["blocks"].append(BV.B("chip", "京大 2023年 英語 第2問 より"))


def m_claim_akahon(v):
    _last(v)["blocks"].append(BV.B("source", "赤本 京大英語 第2問 (2023実施)"))


def m_claim_in_fig(v):
    """図版の中に書いた断言。以前は fig が全文検査から丸ごと外れていた。"""
    _last(v)["blocks"].append(
        BV.B("fig", '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
                    '<text x="1" y="9">出典: 東京大学 2024年 英語 第1問</text></svg>'))


def m_declared_but_absent(v):
    v["unverified"] = list(v["unverified"]) + ["本文のどこにも書いていない主張です"]


def m_disclaimer_not_negative(v):
    """裏の取れない断言を disclaimers に書いて unverified を迂回する形。"""
    v["disclaimers"] = list(v.get("disclaimers") or []) + ["京都大学 2023年 英語 第2問"]


def m_disclaimer_too_short(v):
    v["disclaimers"] = list(v.get("disclaimers") or []) + ["ではない"]


def m_unverified_too_short(v):
    """短い generic な語 1 つで全部の出典行を黙らせる形。"""
    v["unverified"] = ["京都大学"]


def m_script_in_fig(v):
    _last(v)["blocks"].append(BV.B("fig", '<svg><script>alert(1)</script></svg>'))


def m_onload_in_fig(v):
    _last(v)["blocks"].append(BV.B("fig", '<svg onload="x()"></svg>'))


def m_unknown_component(v):
    _last(v)["blocks"].append(BV.B("nonexistent_component", "x"))


# ── 投稿文を壊す変異 ──────────────────────────────────────────────────
def m_caption_missing(v):
    v.pop("caption", None)


def m_caption_too_long(v):
    v["caption"]["full"] = v["caption"]["full"] + "あ" * 2200


def m_caption_too_many_tags(v):
    v["caption"]["hashtags"] = [f"#t{i}" for i in range(31)]


def m_caption_dup_tags(v):
    v["caption"]["hashtags"] = list(v["caption"]["hashtags"]) + [v["caption"]["hashtags"][0]]


def m_caption_bad_tag(v):
    v["caption"]["hashtags"] = list(v["caption"]["hashtags"]) + ["大学受験 と 英語"]


def m_caption_markup_left(v):
    v["caption"]["short"] = "[a]消し忘れた記法[/a]\n" + v["caption"]["short"]


def m_caption_fake_english(v):
    v["caption"]["short"] += "\nRemember: never trust a bare as."


def m_caption_undeclared_claim(v):
    v["caption"]["short"] += "\n出典: 東京大学 2024年 英語 第1問"


# ── 描画側を壊す変異 ──────────────────────────────────────────────────
def _patch_render(fn):
    orig = BV.render_slide
    BV.render_slide = fn(orig)
    return lambda: setattr(BV, "render_slide", orig)


def m_render_drops_handle(v):
    """★データ側を書き換えても意味がない。出力もそこから作られるので同語反復になる。
    守りたいのは「描画側がブランド行を落とす」壊れ方なので、そちらを仕込む。"""
    return _patch_render(lambda o: lambda vol, sl: o(vol, sl).replace(vol["handle"], ""))


def m_render_drops_site(v):
    return _patch_render(lambda o: lambda vol, sl: o(vol, sl).replace(vol["site"], ""))


def m_render_drops_label(v):
    return _patch_render(lambda o: lambda vol, sl: o(vol, sl).replace(vol["label"], ""))


def m_render_dot_missing(v):
    """ドットを 1 つ落とす (総数がスライド数と合わなくなる)。"""
    return _patch_render(lambda o: lambda vol, sl: o(vol, sl)
                         .replace('<span class="dot"></span>', "", 1))


def m_render_dot_offbyone(v):
    """点灯するドットを 1 つずらす (描画側の off-by-one)。"""
    return _patch_render(lambda o: lambda vol, sl: o(vol, sl)
                         .replace('class="dot on"', 'class="dot"', 1)
                         .replace('class="dot"', 'class="dot on"', 1))


def m_render_pgnum_swapped(v):
    """ページ番号を n/total ではなく total/n で書く。"""
    def wrap(o):
        def f(vol, sl):
            h = o(vol, sl)
            n, tot = sl["n"], len(vol["slides"])
            return h.replace(f'class="pgnum">{n}/{tot}<',
                             f'class="pgnum">{tot}/{n}<')
        return f
    return _patch_render(wrap)


def _collide(cls):
    def mut(v):
        _last(v)["blocks"].append(BV.B("dashnote", "衝突", ctr=True))
        saved = BV.COMPONENTS["dashnote"]
        BV.COMPONENTS["dashnote"] = lambda b: f'<div class="dashnote {cls}">衝突</div>'
        return lambda: BV.COMPONENTS.__setitem__("dashnote", saved)
    return mut


# (名前, 変異, 鳴るべきガードの文言)
MUTATIONS = [
    ("記法の閉じ忘れ", m_unclosed, "閉じ忘れ"),
    ("知らない記法タグ", m_unknown_tag, "未知のタグ"),
    ("ページ番号のずれ", m_page_number, "ページ番号が ["),
    ("本文に無い英文を引用", m_quote_not_in_passage, "本文にその並びで存在しない英文"),
    ("引用の行を並べ替えて捏造", m_quote_reordered, "本文にその並びで存在しない英文"),
    ("地の文に紛れた英文", m_stray_english, "本文にも例文にも無い英文"),
    ("ハイフンで繋いだ英文", m_stray_english_hyphen, "本文にも例文にも無い英文"),
    ("全角空白で繋いだ英文", m_stray_english_zenkaku, "本文にも例文にも無い英文"),
    ("宣言していない出典の断言", m_undeclared_claim, "未検証の主張が unverified に宣言されていない"),
    ("略称での出典の断言", m_claim_abbrev, "未検証の主張が unverified に宣言されていない"),
    ("赤本表記での出典の断言", m_claim_akahon, "未検証の主張が unverified に宣言されていない"),
    ("図版の中に書いた出典の断言", m_claim_in_fig, "未検証の主張が unverified に宣言されていない"),
    ("宣言したのに本文に無い", m_declared_but_absent, "本文にも投稿文にも無い"),
    ("打ち消しでない disclaimer", m_disclaimer_not_negative, "打ち消しになっていない"),
    ("disclaimer が短すぎる", m_disclaimer_too_short, "短すぎる"),
    ("短い語で宣言を済ませる", m_unverified_too_short, "短すぎる"),
    ("図版に <script>", m_script_in_fig, "<script> は禁止"),
    ("図版に on* 属性", m_onload_in_fig, "on* 属性は禁止"),
    ("知らない部品", m_unknown_component, "未知の部品"),
    ("描画がブランド行を落とす", m_render_drops_handle, "handle ("),
    ("描画が URL を落とす", m_render_drops_site, "site ("),
    ("描画が vol バッジを落とす", m_render_drops_label, "label ("),
    ("描画がドットを 1 つ落とす", m_render_dot_missing, "ドットが "),
    ("描画の点灯ドットが 1 つずれる", m_render_dot_offbyone, "点灯位置が"),
    ("描画のページ番号が入れ替わる", m_render_pgnum_swapped, "ページ番号の表示が"),
    # ★文言まで指定する。CSS 由来の見張りは 2 枝あり、片方を消しても
    #   もう片方が鳴るので、「どちらでもいい」にすると枝を消せてしまう。
    ("クラス名の衝突 (.mid)", _collide("mid"), "中身の並びが壊れる"),
    ("クラス名の衝突 (.opts)", _collide("opts"), "中身の並びが壊れる"),
    ("クラス名の衝突 (.answer)", _collide("answer"), "中身の並びが壊れる"),
    ("クラス名の衝突 (指定の混ざり)", _collide("gloss"), "意図しない指定の混ざり"),
    ("投稿文が無い", m_caption_missing, "caption が無い"),
    ("投稿文が上限を超える", m_caption_too_long, "上限 2200 字を超えている"),
    ("ハッシュタグが 31 個", m_caption_too_many_tags, "上限は 30"),
    ("ハッシュタグの重複", m_caption_dup_tags, "重複している"),
    ("ハッシュタグの形が不正", m_caption_bad_tag, "形が不正"),
    ("投稿文に記法の消し忘れ", m_caption_markup_left, "記法 [a] が残っている"),
    ("投稿文に本文に無い英文", m_caption_fake_english, "本文にも例文にも無い英文"),
    ("投稿文に宣言なしの出典", m_caption_undeclared_claim, "未検証の主張が unverified に"),
]


# ── 刷り上がりの判定 (画像はメモリ上で作る。ファイルは書かない) ──────
def _fake_pages(n=6):
    """版面と同じ大きさの、互いに異なる「刷り上がり」を作る。"""
    from PIL import Image, ImageDraw
    out = []
    for i in range(n):
        im = Image.new("RGB", (G.PNG_W, G.PNG_H), (12, 10, 24))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 100, G.PNG_W, 160], fill=(240, 240, 240))          # ヘッダ
        d.rectangle([200 + i * 90, 1000, 900 + i * 90, 1600], fill=(240, 200, 80))  # 本文
        d.rectangle([0, G.PNG_H - 120, G.PNG_W, G.PNG_H - 80], fill=(200, 200, 210))  # フッタ
        out.append((f"fake_{i + 1:02d}.png", im))
    return out


def _fake_sheet(items):
    from PIL import Image
    tw = 430
    th = int(tw * T.H / T.W)
    cols = 3
    rows = -(-len(items) // cols)
    sh = Image.new("RGB", (tw * cols + 10 * (cols + 1), th * rows + 10 * (rows + 1)),
                   (24, 22, 40))
    for i, (_nm, im) in enumerate(items):
        sh.paste(im.convert("RGB").resize((tw, th), Image.LANCZOS),
                 ((i % cols) * (tw + 10) + 10, (i // cols) * (th + 10) + 10))
    return sh


def content_cases():
    """(名前, items, sheet, 鳴るべき文言) を返す。Pillow が無ければ ImportError。"""
    from PIL import Image, ImageDraw  # noqa: F401
    base = _fake_pages()
    sheet = _fake_sheet(base)

    blank = [(n, im.copy()) for n, im in base]
    d = ImageDraw.Draw(blank[-1][1])
    d.rectangle([0, int(G.PNG_H * 0.20), G.PNG_W, int(G.PNG_H * 0.80)], fill=(12, 10, 24))
    yield ("本文の帯が空", blank, _fake_sheet(blank), "本文の帯に何も無い")

    dup = [(n, base[0][1]) for n, _ in base]
    yield ("全部が同じ画像", dup, _fake_sheet(dup), "中身が同一")

    yield ("一覧 JPG が無い", base, None, "一覧 JPG が無い")

    stale = [(n, im) for n, im in base]
    yield ("一覧 JPG が古い (刷り直し漏れ)", stale,
           _fake_sheet(list(reversed(stale))), "一覧 JPG の")

    yield ("正しい組 (過敏でないこと)", base, sheet, None)


GEOMETRY_CASES = [
    ("実寸ちがい", ((100, 100), 48, 39), True),
    ("天がずれる", (None, 200, 39), True),
    ("地が広すぎる", (None, 48, 130), True),
    ("地が狭すぎる", (None, 48, 2), True),
    ("真っ暗", (None, None, 0), True),
    ("正しい版面 (過敏でないこと)", (None, 48, 39), False),
]


def main():
    base = BV.load_vols()
    if not base:
        print("[NG] vols/ に vol が 1 つも無い — 変異試験の土台が無い")
        return 1

    fails = []

    # 壊していない状態は通ること (常に落ちる検査は検査ではない)
    for v in base:
        got = _run(copy.deepcopy(v))
        if got:
            fails.append(f"{v['key']}: 壊していないのに違反が出る (検査が過敏): {got[:2]}")

    saved = dict(BV.COMPONENTS)
    for name, mut, expect in MUTATIONS:
        for v in base:                      # ★vol ごとに AND
            w = copy.deepcopy(v)
            undo = None
            try:
                undo = mut(w)
                got = _run(w)
            finally:
                if callable(undo):
                    undo()
                BV.COMPONENTS.clear()
                BV.COMPONENTS.update(saved)
            if not any(expect in g for g in got):
                fails.append(
                    f"変異「{name}」({v['key']}): 鳴るべき見張り {expect!r} が鳴らなかった "
                    f"(出たのは {got[:2] or 'なし'})")

    # 刷り上がりの中身。★Pillow が無いと画像を作れないので回せない。
    #   落ちるのではなく「回していない」と声に出す (黙って減らすと全部通ったように見える)。
    n_content = 0
    try:
        cases = list(content_cases())
    except ImportError:
        cases = []
        print("  ★Pillow が無いので、刷り上がりの判定 (本文帯・取り違え・一覧との照合) は"
              "1 件も回していない。python3 -m pip install Pillow")
    for name, items, sheet, expect in cases:
        n_content += 1
        got = G.judge_content("fake", items, sheet)
        if expect is None:
            if got:
                fails.append(f"刷り上がり「{name}」: 正しいのに落ちる: {got[:2]}")
        elif not any(expect in g for g in got):
            fails.append(f"刷り上がり「{name}」: {expect!r} が鳴らなかった "
                         f"(出たのは {got[:2] or 'なし'})")

    # 寸法と天地 (純関数なので直に叩く)
    for label, (size, top, gap), should in GEOMETRY_CASES:
        size = size or (G.PNG_W, G.PNG_H)
        got = G.judge_geometry("x.png", size, top, gap)
        if should and not got:
            fails.append(f"版面「{label}」: 判定が素通しした")
        if not should and got:
            fails.append(f"版面「{label}」: 正しいのに落ちる: {got}")

    # 書体スタックの見張り (★和文の族名を入れない。'Hiragino' は和文なので変異にならない)
    sans = T.SANS
    try:
        T.SANS = 'system-ui,-apple-system,sans-serif'
        b = []
        G.check_fonts(b)
        if not any("先頭が" in x for x in b):
            fails.append("変異「書体スタックの先頭を和文以外に」: 先頭の見張りが鳴らなかった")
        T.SANS = '"Noto Sans JP",sans-serif'
        b = []
        G.check_fonts(b)
        if not any("フォールバック" in x for x in b):
            fails.append("変異「和文のフォールバックを削る」: 見張りが鳴らなかった")
    finally:
        T.SANS = sans

    total = len(MUTATIONS) * len(base) + n_content + len(GEOMETRY_CASES) + 2
    print(f"変異試験: {total} 件 (データ {len(MUTATIONS)}種×{len(base)}冊 / "
          f"刷り上がり {n_content} / 版面 {len(GEOMETRY_CASES)} / 書体 2) を仕込み、"
          f"**鳴るべき見張りが鳴ったか**まで見た")
    if fails:
        print(f"\n[NG] 期待どおりに鳴らなかったもの {len(fails)} 件:")
        for f in fails:
            print(f"  ✗ {f}")
        return 1
    print(f"[OK] {total} 件すべてで意図した見張りが鳴った / 取りこぼし 0 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
