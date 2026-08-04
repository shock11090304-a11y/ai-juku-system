# -*- coding: utf-8 -*-
"""
盲ソルバー3人の解答と「鍵」を **Python が決定的に照合** する。

  python3 _reconcile.py rika_kagaku/content_no01.py out/blind_kagaku__A.json out/…__B.json out/…__C.json
  python3 _reconcile.py natsu_tokkun/content.py out/…__{A,B,C}.json --days

設計（[[question-bank-rigorous-verification-harness]]）:
  **LLMは解く／審査する・Pythonが照合して判定する。** LLMに一致判定をさせると非決定でミスが漏れる。

出力の読み方:
  KEY-MISMATCH … 3人**全員**が鍵と違う答えに合意した ＝ 本物の鍵誤りの最強シグナル。まず疑う。
  SPLIT        … 3人の答えが割れた ＝ 設問が曖昧か、第2正解がある可能性。
  MINORITY     … 1人だけ違う ＝ たいていソルバー側のミス。ただし理由は確認する。

★盲ソルバーは「鍵が正しいか」は測るが、「他に正解が無いか／解説が正しいか／範囲内か」は
  測らない別の軸。そちらは敵対レビューと機械ゲートで見ること。
"""
import argparse
import json
import re
import sys
import unicodedata

from _make_blind import load

CIRCLED = "①②③④⑤⑥⑦⑧"


_MK_SQRT = re.compile(r"\[\[sqrt:([^\]]+)\]\]")
_MK_FRAC = re.compile(r"\[\[frac:([^|\]]+)\|([^\]]+)\]\]")


def norm(s):
    """★日本語の解答は「見た目の差」で簡単に不一致になる。実際に盲検証で出た偽の
    KEY-MISMATCH は全部これだった:
      「約25.4人」vs「25.4人」／「8月10日 午前3時」vs「8月10日午前3時」／「20.0cm」vs「20cm」
    概数の「約」・空白・末尾の句点・末尾の 0 は落としてから比べる。
    （落としてよいのは表記の差だけ。数値そのものは 20.0→20 のように値が変わらない形だけ）"""
    # ★組分数・根号の目印は「紙に出る形」に直してから比べる。
    #   鍵が [[frac:3|8]] のままだと、盲ソルバーの「3/8」と当然一致しない。
    s = _MK_SQRT.sub(r"√\1", str(s))
    s = _MK_FRAC.sub(r"\1/\2", s)
    s = unicodedata.normalize("NFKC", s).strip()
    s = re.sub(r"^約", "", s)
    s = re.sub(r"[\s　]+", "", s)            # 日本語は空白の有無で意味が変わらない
    s = re.sub(r"[。．]$", "", s)
    # 数学の解答で必ず出る表記差：全角マイナス／ハイフン類、読点とカンマ、囲み記号
    s = s.translate(str.maketrans({"−": "-", "－": "-", "–": "-", "—": "-",
                                   "、": ",", "，": ",", "・": ",",
                                   "（": "", "）": "", "(": "", ")": "",
                                   "〔": "", "〕": "", "［": "", "］": ""}))
    # 「20.0cm」→「20cm」：小数末尾の 0 を落とす（値は同じ）
    s = re.sub(r"(\d+)\.0+(?=\D|$)", r"\1", s)
    s = re.sub(r"(\d+\.\d*?)0+(?=\D|$)", r"\1", s)
    s = _split_markers(s)
    return s.lower()


def _split_markers(s):
    """空欄が2つ以上ある設問の「ア」「イ」「1」「2」は**欄の名前**であって解答ではない。
    鍵が「ア表す イ現す」でソルバーが「表す, 現す」だと、中身が同じでも不一致になる。

    ★誤爆に注意: 「アンモニア」「オアシス農業」の先頭のカナは欄の名前ではない。
      そこで「その記号が2つ以上あり、どれも直後に中身を持つ」ときだけ区切りとみなす。
      数字は「8月10日午前3時」を壊さないよう、1,2,3… が昇順にそろっているときだけ。
    """
    kana = r"[アイウエオ](?=[^\sアイウエオ])"
    if len(re.findall(kana, s)) >= 2:
        s = re.sub(kana, ",", s)
    m = re.findall(r"[1-4](?=[^\d])", s)
    if len(m) >= 2 and m == [str(i + 1) for i in range(len(m))]:
        s = re.sub(r"[1-4](?=[^\d])", ",", s)
    return s.strip(",")


def _had_markers(s):
    """norm() を通す前に欄の名前（ア/イ・1/2）が付いていたか。付いていたら順序は解答の一部。"""
    return bool(re.search(r"[アイウエオ][^\sアイウエオ]", str(s))) or \
        bool(re.match(r"^[（(]?[1-4][）)]?[^\d]", str(s)))


def strip_var(s):
    """「y=-6」→「-6」。設問が変数を指定しているので、頭に付けても付けなくても同じ解答。"""
    return re.sub(r"^[a-zA-Z]\s*=\s*", "", s)


def as_multiset(s):
    """「x=3,x=-5」と「x=-5,x=3」を同じとみなすための多重集合。"""
    return tuple(sorted(p for p in re.split(r"[,]", s) if p))


def norm_en(s):
    return re.sub(r"\s+", " ", re.sub(r"[.,?!;:'\"]", " ", str(s))).strip().lower()


def key_of(C, days=False):
    """id -> (type, 正解の正規形の集合)。mc は 1 始まりの番号で持つ。"""
    K = {}
    if days:
        for D in C.DAYS:
            for sec in D["sections"]:
                for i, q in enumerate(sec["qs"], start=1):
                    _put(K, f'D{D["day"]}-{sec["subj"]}-{i}', q)
    else:
        n = 1
        for g in C.PART1:
            for it in g["items"]:
                K[f"P1-{n}"] = ("short", _short_forms(it["ans"]))
                n += 1
        for b in C.PART2:
            for i, q in enumerate(b["qs"], start=1):
                _put(K, f'{b["no"]}-{i}', q)
    return K


def _norm_seq(seq):
    """記号の並び（match の解答）を、順序を保ったまま比べられる形にする。"""
    return ",".join(unicodedata.normalize("NFKC", str(x)).strip() for x in seq).lower()


def _short_forms(ans):
    """「電気抵抗（抵抗）」→ {電気抵抗, 抵抗, 電気抵抗(抵抗)} のように許容形を展開。"""
    a = str(ans)
    forms = {norm(a)}
    forms.add(norm(re.sub(r"[（(].*?[）)]", "", a)))
    forms |= {norm(x) for x in re.findall(r"[（(](.+?)[）)]", a)}
    return {f for f in forms if f}


def _put(K, qid, q):
    t = q["type"]
    if t == "desc":
        return
    if t == "mc":
        K[qid] = ("mc", {str(q["ans"] + 1)})          # ★0始まり → 1始まりに直して持つ
    elif t == "order":
        K[qid] = ("order", {norm_en(q["ans"])})
    elif t == "match":
        # ★match は ア/イ/ウ/エ **そのものが解答**。norm() は「2つ以上並んだ ア/イ は欄の名前」
        #   とみなして区切りに潰すので、そのまま通すと鍵が最後の1欄に崩壊し、
        #   24通りの順列のうち6通りが「完全一致」になっていた（地理No.02の match 4問が実質未検証）。
        K[qid] = ("match", {_norm_seq(q["ans"])})
    else:
        K[qid] = (t, _short_forms(q["ans"]))


def parse_ans(t, raw):
    s = str(raw).strip()
    if t == "mc":
        for i, c in enumerate(CIRCLED):
            s = s.replace(c, str(i + 1))
        m = re.search(r"[0-9０-９]+", unicodedata.normalize("NFKC", s))
        return m.group(0) if m else norm(s)
    if t == "order":
        return norm_en(s)
    if t == "match":
        return _norm_seq([x for x in re.split(r"[,、／/\s]+", s) if x])
    return norm(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content")
    ap.add_argument("solutions", nargs="+")
    ap.add_argument("--days", action="store_true")
    a = ap.parse_args()

    C = load(a.content)
    K = key_of(C, a.days)

    sols = []
    for p in a.solutions:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        arr = d if isinstance(d, list) else d.get("answers") or d.get("items") or []
        sols.append({str(x["id"]): x.get("answer", "") for x in arr})

    names = [chr(ord("A") + i) for i in range(len(sols))]
    mismatch, split, minority, missing, fmt = [], [], [], [], []

    def equiv(t, g, want):
        """厳密一致 → 変数の頭（y=）を外して一致 → 並び順だけの差、の順に見る。
        ★整序と match は順序そのものが解答なので、多重集合の比較を使わない。"""
        if g in want:
            return "exact"
        if t in ("calc", "short") and any(strip_var(g) == strip_var(w) for w in want):
            return "var"
        # ★多重集合の比較を使ってよいのは「2つの解の順序」だけ。
        #   「ア my／イ mine」のような**名前つきの欄**は入れ替わったら本物の誤りなので、
        #   欄の名前を含む解答（norm で , に潰される前に ア/イ や 1/2 があった）には使わない。
        if (t in ("calc", "short") and not _had_markers(g)
                and any(as_multiset(g) == as_multiset(w) for w in want)):
            return "order"
        return None

    for qid, (t, want) in K.items():
        got = []
        for s in sols:
            if qid not in s:
                got.append(None)
            else:
                got.append(parse_ans(t, s[qid]))
        if any(g is None for g in got):
            missing.append(f"{qid}（{'/'.join(n for n, g in zip(names, got) if g is None)} が未回答）")
            got = [g for g in got if g is not None]
            if not got:
                continue
        kinds = [equiv(t, g, want) for g in got]
        if all(k == "exact" for k in kinds):
            continue
        detail = "／".join(f"{n}={g}" for n, g in zip(names, got))
        w = "|".join(sorted(want))
        if all(k is not None for k in kinds):
            # 中身は正しく、書き方だけが違う（y= を付けた／2つの解の順序が逆 など）。
            # 鍵の誤りではないので分けて出す。ここを KEY-MISMATCH に混ぜると本物が埋もれる。
            fmt.append(f"{qid} 鍵=「{w}」（{detail}）＝" +
                       ("変数の頭の有無" if "var" in kinds else "並び順の違い"))
            continue
        ok = [k == "exact" for k in kinds]
        if not any(ok):
            if len(set(got)) == 1:
                mismatch.append(f"{qid} 鍵=「{w}」だが3人全員が「{got[0]}」 ← 鍵誤りを最優先で疑う")
            else:
                mismatch.append(f"{qid} 鍵=「{w}」に誰も一致しない（{detail}）")
        elif sum(ok) == 1:
            split.append(f"{qid} 鍵=「{w}」 一致1人のみ（{detail}）")
        else:
            minority.append(f"{qid} 鍵=「{w}」（{detail}）")

    n = len(K)
    print(f"=== 盲検証の照合結果（照合対象 {n} 問／ソルバー {len(sols)}人）===")
    for label, arr in (("KEY-MISMATCH（鍵誤りの疑い・最優先）", mismatch),
                       ("SPLIT（曖昧／第2正解の疑い）", split),
                       ("MINORITY（1人だけ不一致）", minority),
                       ("MISSING（未回答）", missing),
                       ("FORMAT（中身は正しく書き方だけ違う＝鍵の誤りではない）", fmt)):
        print(f"\n--- {label}: {len(arr)}件 ---")
        for x in arr:
            print("  ", x)
    bad = len(mismatch) + len(split)
    print(f"\n全員一致で鍵どおり: "
          f"{n - len(mismatch) - len(split) - len(minority) - len(fmt)}/{n}"
          f"（＋書き方だけの差 {len(fmt)}問）")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
