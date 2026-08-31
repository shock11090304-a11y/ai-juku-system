#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""和文フォントの調達。

★なぜ要るか (2026-08-31 実測):
  クラウド/CI の Linux には和文フォントが IPAGothic / WenQuanYi / Unifont しか無い。
  `font-family:"Hiragino Sans",sans-serif` は **WenQuanYi Zen Hei (中国語フォント)** に
  落ちる。豆腐にはならないので気づきにくいが、字形が中国語になる
  (直・令・漢・今・戸・画 などが日本語字形と 19〜36% 違う)。受験生に配る画像で
  中国語字形が出るのは事故。和文明朝も無く、太字も合成 (weight 700 と 900 が同一)。

  塾長の Mac にはヒラギノがあるので font-family の先頭で解決する。
  Linux では Google Fonts から Noto Sans JP / Noto Serif JP を取ってきて
  @font-face で file:// 参照する。

★取得はビルド時だけ。**描画時に Chrome が外に出ることはない** (ネットワークが
  無い環境でも刷れるように、必ずローカルのファイルを参照する)。
★キャッシュはリポジトリの外 (~/.cache)。scripts/ の中に置くと
  run_all_gates.py の「検査を回したらファイルが変わった」検出に引っかかる。
"""
import os
import urllib.request

CACHE = (os.environ.get("TRILLION_FONT_CACHE")
         or os.path.join(os.path.expanduser("~"), ".cache", "trillion-ig-fonts"))

# ★UA で返る形式が変わる。実測 (2026-08-31):
#     Chrome 141 の UA → 分割 woff2 が 124 個 (unicode-range 別) — 扱いづらい
#     "Mozilla/4.0 (MSIE 6)" → EOT — Chrome で使えない (これで一度嵌った)
#     "Mozilla/5.0" (素) → 1 ウェイト 1 個の TTF ← これを使う
_UA = "Mozilla/5.0"
_CSS_API = "https://fonts.googleapis.com/css2?family="

FACES = [
    # (family, weight, Google Fonts のクエリ, 保存名)
    ("Noto Sans JP", 400, "Noto+Sans+JP:wght@400", "NotoSansJP-400"),
    ("Noto Sans JP", 700, "Noto+Sans+JP:wght@700", "NotoSansJP-700"),
    ("Noto Sans JP", 900, "Noto+Sans+JP:wght@900", "NotoSansJP-900"),
    ("Noto Serif JP", 400, "Noto+Serif+JP:wght@400", "NotoSerifJP-400"),
    ("Noto Serif JP", 700, "Noto+Serif+JP:wght@700", "NotoSerifJP-700"),
]

# ★取れたファイルの中身を必ず確かめる。拡張子や Content-Type は信用しない。
#   EOT が返っていても大きさは正しいので、大きさだけ見ていると気づけない。
_MAGIC = {b"\x00\x01\x00\x00": "truetype", b"true": "truetype",
          b"ttcf": "truetype", b"OTTO": "opentype",
          b"wOFF": "woff", b"wOF2": "woff2"}


def _fmt_of(path):
    with open(path, "rb") as f:
        return _MAGIC.get(f.read(4))


def _get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def have():
    """キャッシュ済みの顔を [(family, weight, path, format), ...] で返す。取得はしない。

    ★先頭 4 バイトだけでなく末尾も見る。途中で切れた TTF は先頭が正しいので、
      マジックとサイズだけでは壊れていることが分からない。
    """
    out = []
    for fam, w, _q, name in FACES:
        p = os.path.join(CACHE, name + ".font")
        if os.path.exists(p) and os.path.getsize(p) > 100_000 and _looks_whole(p):
            fmt = _fmt_of(p)
            if fmt:
                out.append((fam, w, p, fmt))
    return out


def _looks_whole(path):
    """末尾がゼロ埋めで終わっていないか (途中で切れたファイルの見分け)。"""
    try:
        with open(path, "rb") as f:
            f.seek(-4096, os.SEEK_END)
            return any(f.read(4096))
    except OSError:
        return False


def fetch(verbose=True):
    """未取得の顔をダウンロードする。失敗しても例外にしない (刷れなくはないため)。

    返り値は have() と同じ形。取れなかった顔は入らない。
    """
    os.makedirs(CACHE, exist_ok=True)
    for fam, w, q, name in FACES:
        p = os.path.join(CACHE, name + ".font")
        if os.path.exists(p) and os.path.getsize(p) > 100_000:
            continue
        try:
            css = _get(_CSS_API + q).decode("utf-8", "replace")
            i = css.index("url(") + 4
            url = css[i:css.index(")", i)].strip("'\"")
            data = _get(url, timeout=180)
            if len(data) < 100_000:
                raise ValueError(f"小さすぎる ({len(data)} bytes)")
            if data[:4] not in _MAGIC:
                raise ValueError(f"フォントの形式ではない (先頭 {data[:4]!r})")
            # ★一時ファイルに書いてから差し替える。最終パスへ直接書くと、
            #   途中で落ちたときに「100KB は超えているが壊れている」ファイルが
            #   キャッシュに残り、have() を通ってしまう (そして二度と取り直さない)。
            tmp = p + ".part"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, p)
            if verbose:
                print(f"  フォント取得: {fam} {w} ({len(data)//1024} KB)")
        except Exception as e:  # noqa: BLE001 — 取れなくても刷れるので落とさない
            if verbose:
                print(f"  フォント取得できず: {fam} {w} — {e}")
    return have()


def face_css(faces=None):
    """@font-face の CSS を返す。キャッシュが空なら空文字 (システムのフォントに任せる)。"""
    faces = have() if faces is None else faces
    out = []
    for fam, w, path, fmt in faces:
        url = "file://" + path.replace(" ", "%20")
        out.append(f"@font-face{{font-family:'{fam}';font-style:normal;"
                   f"font-weight:{w};src:url('{url}') format('{fmt}');}}")
    return "".join(out)


def describe():
    """何が使えるかを人間向けに 1 行で。検査とビルドの両方が印字に使う。"""
    got = have()
    if not got:
        return ("和文フォント: 同梱なし (システム任せ)。"
                f"取得するには python3 {os.path.basename(__file__)} --fetch")
    fams = sorted({f"{fam} {w}" for fam, w, _p, _f in got})
    return f"和文フォント: {len(got)}顔を同梱 ({', '.join(fams)}) ← {CACHE}"


if __name__ == "__main__":
    import sys
    if "--fetch" in sys.argv:
        fetch()
    print(describe())
