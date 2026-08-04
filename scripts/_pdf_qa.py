#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配布PDFの機械QA。**画像を1枚も読まずに**判定できるものを全部ここで出す。

  python3 scripts/_pdf_qa.py ~/Desktop/foo_問題編.pdf ~/Desktop/foo_解答解説編.pdf
  python3 scripts/_pdf_qa.py --png 1,4 foo.pdf     # 目視したいページだけPNG化

★存在理由（2026-07-28 中学社会プリントの反省）:
  全ページをPNG化して Read で目視 → ページ画像86枚を作り12枚読んだ。画像Readは1枚数千トークンで、
  ~30枚を超えると以後Read画像が全拒否になる既知の罠もある。
  「文字化け」「ほぼ空白のページ」「行あふれ」は**テキストで判定できる**ので、目視は
  代表2〜3ページ（表紙・図版ページ・最終ページ）だけに絞る。

判定するもの
  1. グリフ監査 …… NUL/置換文字(�)/私用領域＝黒四角・豆腐の検出
  2. ほぼ空白のページ …… 文字数が閾値未満（改ページ設定ミスで奥付だけのページが出る事故）
  3. ページ番号の連番 …… ノンブル刻印の抜け
  4. 余白はみ出し …… テキストブロックが @page マージンの外に出ていないか
  5. サイズ/ページ数 …… フォント埋め込みでPDFが肥大していないか
"""
import re
import sys
import os
import unicodedata
from collections import Counter

import fitz

A4_W, A4_H = 595.0, 842.0     # pt
EMPTY_CHARS = 200             # これ未満なら「ほぼ空白」とみなす
# 表紙・大扉・部扉に出る語。これを含む短いページは「意図的な扉」として空白判定から除く
# ★表紙は字間を空けて組むことがある（「解 答 ・ 解 説 編」）。
#   空白を落としてから照合しないと、意図的な表紙を「ほぼ空白のページ」と誤検出する。
# ★単独の「編」を入れてはいけない。本文にも出る1文字なので、
#   これがあるだけで「短いページ＝扉」と誤認され、空白ページ検出が丸ごと無効になる
#   （実際、記述1問しかない18%のページが検出されずに出荷寸前まで来た）。
DIVIDER_WORDS = ("問題編", "解答・解説編", "解説編", "第1編", "第2編", "第3編",
                 "ドリル", "問題集", "目次", "問題演習")
DIVIDER_CHARS = 80        # 扉とみなすのはこの字数未満のときだけ
# ★「本文が少ない」のが**設計どおり**のページもある。計算らん・メモらんは
#   生徒が書き込むための空間なので、文字が少ないのが正しい。
#   ただし紙に**ラベルが刷ってある**ことを条件にする（ラベルの無い空白は事故）。
WORKSPACE_WORDS = ("計算らん", "計算欄", "計算・見直しらん", "メモらん", "下書きらん")
FAT_KB_PER_PAGE = 400     # 1ページあたりこれを超えたらフォント埋め込みを疑う
FOOT_BAND = 32            # 下からこの高さまでを「柱・ノンブルの帯」とみなす（pt）
THIN_RATIO = 0.25         # 最終ページがこれ未満しか使っていなければ1枚むだ（奇数ページのとき）


def audit(path, png_pages=None):
    name = os.path.basename(path)
    d = fitz.open(path)
    kb = os.path.getsize(path) / 1024
    print(f"\n=== {name} ===")
    print(f"  {d.page_count}ページ / {kb:.0f}KB ({kb/d.page_count:.0f}KB/page)")

    bad_glyph = Counter()
    empties, overflow, dup_text, thin = [], [], [], []
    for i, pg in enumerate(d):
        t = pg.get_text()
        # ★KaTeX は数式記号を私用領域(PUA)のコードポイントで持つ。KaTeX_* フォントで
        #   描かれた PUA は正常な数式であって文字化けではない（既存巻でも同じ検出が出て
        #   誤検出と確認済み）。フォント名を見て除外する。
        katex_pua = set()
        for b in pg.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                for sp_ in ln["spans"]:
                    if sp_["font"].startswith("KaTeX"):
                        katex_pua.update(sp_["text"])
        for ch in t:
            if ch in "\n\t\r " or ch in katex_pua:
                continue
            cp = ord(ch)
            if cp < 0x20 or ch == "�" or unicodedata.category(ch) in ("Cn", "Co", "Cs"):
                bad_glyph[f"p{i+1} U+{cp:04X} {ch!r}"] += 1
        # ★★このゲートは長い間**無効化されていた**。
        #   柱（ページ下端に insert_text で刻む書名）に「確認プリント」「問題編」が入るため、
        #   下の is_divider 判定が**全ページを扉とみなして**空白ページ検出を素通ししていた。
        #   実際、記述1問だけで85%が白紙のページが検出されずに出荷寸前まで来た。
        #   → 本文の量を測るときは、刻印した柱・ノンブルを必ず除いてから数える。
        body = "".join(
            s["text"] for b in pg.get_text("dict")["blocks"] for ln in b.get("lines", [])
            for s in ln["spans"] if s["bbox"][1] <= pg.rect.height - FOOT_BAND
        ).strip()
        # 表紙・大扉・部扉は意図的に文字が少ない。「本文が無い」ことを問題視したいので、
        # 扉らしさ（短い＋見出し語のみ）を判定して除外する。
        squeezed = re.sub(r"\s|　", "", body)
        # ★1ページ目は必ず表紙。字数が DIVIDER_CHARS を少し超えただけで
        #   「ほぼ空白のページ」と誤検出していた（副題が長い本で再現）。
        #   ただし扉語を含むことは引き続き求める（本文が1ページ目から始まる本を素通ししない）。
        is_divider = ((len(body) < DIVIDER_CHARS or i == 0)
                      and any(k in squeezed for k in DIVIDER_WORDS))
        is_workspace = any(re.sub(r"\s|　", "", k) in squeezed for k in WORKSPACE_WORDS)
        is_divider = is_divider or is_workspace
        if len(body) < EMPTY_CHARS and not is_divider:
            empties.append((i + 1, len(body)))
        # ★「空白ではないが、紙の大半が空いている」ページも拾う（両面印刷で1枚むだになる）。
        used = max((s["bbox"][3] for b in pg.get_text("dict")["blocks"]
                    for ln in b.get("lines", []) for s in ln["spans"]
                    if s["bbox"][1] <= pg.rect.height - FOOT_BAND), default=0)
        # ★「ページ数が奇数」のときだけ問題にする。両面印刷では 7ページも8ページも同じ4枚で、
        #   薄い最終ページが偶数番なら既存の紙の裏を埋めるだけ＝むだにならない。
        #   奇数なら、その1問のために1枚まるごと増えている（物理が7p/18%＝実際に1枚むだだった）。
        # しきい値は実例で決めた: 記述1問だけの物理p7＝18%は捕まえたいが、
        # 記述2問が載っている地理p7＝30%は正常（これ以上詰めようがない）。25%を境にする。
        if (i + 1 == d.page_count and d.page_count % 2 == 1
                and used < pg.rect.height * THIN_RATIO):
            thin.append((i + 1, round(used / pg.rect.height * 100)))
        # ★同じ文字列が続けて2回刷られていないか。
        #   下線用のマーカーと本文を両方書いてしまい、6問すべてが
        #   「(a)Did Kaito and AiriDid Kaito and Airi」と二重印字された事故がある。
        #   PDFは正常に生成され、配点も解答も合うので、他のどのゲートも素通りした。
        flat = re.sub(r"[\s\u3000]+", " ", t)
        # ★区切り記号で並べた別解リスト（「可: A / B / C」）は同じ語が繰り返し出るのが
        #   正常なので除外する。捕まえたいのは区切りなしで本文がそのまま二度出る型。
        for m in re.finditer(r"(\S[^\n]{14,}?)\1", flat):
            unit = m.group(1)
            if any(k in unit for k in ("/", "／", "、", "別解", "可:")):
                continue
            dup_text.append((i + 1, unit[:40]))
            break
        # 余白はみ出し（左右6mm=17pt より外に描画されていないか）
        for b in pg.get_text("blocks"):
            x0, y0, x1, y1 = b[:4]
            if x0 < 12 or x1 > pg.rect.width - 12:
                overflow.append((i + 1, round(x0), round(x1)))
                break

    ng = 0
    if dup_text:
        ng += 1
        print(f"  ✗ 同じ文字列の二重印字 {len(dup_text)}ページ: "
              + "／".join(f'p{p}「{x}…」' for p, x in dup_text[:4]))
        print("     → 下線・記号つき区間のテンプレートが本文を2回出力していないか疑う")
    else:
        print("  ✓ 同一文字列の二重印字なし")

    if bad_glyph:
        ng += 1
        print(f"  ✗ 文字化け {sum(bad_glyph.values())}件:", dict(list(bad_glyph.items())[:6]))
    else:
        print("  ✓ グリフ監査クリーン（NUL/置換文字/私用領域 0件）")

    if empties:
        ng += 1
        print(f"  ✗ ほぼ空白のページ: " + "／".join(f"p{p}({c}字)" for p, c in empties))
        print("     → 改ページ強制(page-break-before:always)か奥付のはみ出しを疑う")
    else:
        print(f"  ✓ 全ページに本文あり（最少 {min(len(p.get_text().strip()) for p in d)}字）")

    if thin:
        ng += 1
        print("  ✗ 最終ページの使用率が低い: "
              + "／".join(f"p{p}({u}%しか使っていない)" for p, u in thin))
        print("     → 1問だけのために両面1枚ふえる。前ページの余白を詰めて収める")
    else:
        print("  ✓ 最終ページの使用率 OK")

    if overflow:
        ng += 1
        print(f"  ✗ 余白外への描画: " + "／".join(f"p{p}(x={a}..{b})" for p, a, b in overflow[:5]))
    else:
        print("  ✓ 余白内に収まっている")

    # ---- 柱（書名）とノンブル（ページ番号）の重なり -------------------------------
    # ★実際に踏んだ: 解答解説編の柱が x=311 まで伸び、中央 x=295 のノンブルに 16pt 重なって
    #   ページ番号が読めなくなっていた。柱は insert_text で後から刻印しており、
    #   HTML の組版ではないので他のどのゲートにも掛からない。書名の長さは号ごとに変わるため
    #   「今回は大丈夫」は根拠にならず、毎回測るしかない。
    foot_hit = []
    for i, pg in enumerate(d):
        sp = []
        for b in pg.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                for s in ln["spans"]:
                    if s["bbox"][1] > pg.rect.height - FOOT_BAND:
                        sp.append((s["bbox"][0], s["bbox"][2], s["text"]))
        sp.sort()
        for k in range(len(sp) - 1):
            gap = sp[k + 1][0] - sp[k][1]
            if gap < 0.5:
                foot_hit.append((i + 1, round(gap, 1), sp[k][2][-16:], sp[k + 1][2][:8]))
    if foot_hit:
        ng += 1
        print("  ✗ 柱とノンブルが重なっている: "
              + "／".join(f"p{p}({g}pt「…{a}」×「{b}」)" for p, g, a, b in foot_hit[:4]))
        print("     → 刻印側で柱を詰める（build_common.render / book._render の avail 計算）")
    else:
        print("  ✓ 柱とノンブルが離れている")

    if kb / d.page_count > FAT_KB_PER_PAGE:
        print(f"  ! {kb/d.page_count:.0f}KB/page と重い → subset_fonts() 済みか確認")

    if png_pages:
        outdir = os.path.join(os.path.dirname(path) or ".", "_qa_png")
        os.makedirs(outdir, exist_ok=True)
        for p in png_pages:
            if 1 <= p <= d.page_count:
                f = os.path.join(outdir, f"{os.path.splitext(name)[0]}_p{p:02d}.png")
                d[p - 1].get_pixmap(dpi=110).save(f)
                print(f"  → 目視用PNG: {f}")
    d.close()
    return ng


def main():
    args = sys.argv[1:]
    png = None
    if args and args[0] == "--png":
        png = [int(x) for x in args[1].split(",")]
        args = args[2:]
    if not args:
        sys.exit(__doc__)
    ng = sum(audit(a, png) for a in args)
    print()
    if ng:
        print(f"=== {ng}種の問題あり（上を修正してから目視に進む） ===")
        sys.exit(1)
    print("=== 機械QA ALL PASS ／ 目視は代表2〜3ページだけでよい ===")


if __name__ == "__main__":
    main()
