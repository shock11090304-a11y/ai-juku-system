# -*- coding: utf-8 -*-
"""このドリルの「不良問題の定義」。build.py と check.py が共有する唯一の判定。

★片方に書き写さないこと。書き写すと、片方だけ直されて判定がずれる
  (class_recording_assign.py で同じ轍を踏まないために置き場所を1つにした前例に倣う)。

validate() は違反メッセージのリストを返す。空なら合格。
"""
import os
import re

BLANK = "(   )"
# 位置を指す書き方。正解位置はビルド時に振り直すので、解説に書くと嘘になる
POS_TOKENS = re.compile(r"[①②③④⑤]|[0-9]\s*番目|答え\s*[:：]\s*[0-9]|選択肢\s*[0-9]|正解\s*[:：]\s*[0-9]")
JP = re.compile(r"[ぁ-んァ-ヶ一-龥、。「」]")
BAD_CHARS = re.compile(r"[�]|¥\s*[()\[\]]")   # 文字化け / ¥ 記法の LaTeX 残骸
MIN_PER_KEY = 6          # (単元,レベル) ごとの最低問数 (ドリル1本=10問を組める在庫)


def _spans(text, needle):
    """text 中の needle の出現位置 [(開始, 終了), ...]。"""
    out, i = [], text.find(needle)
    while i >= 0 and needle:
        out.append((i, i + len(needle)))
        i = text.find(needle, i + 1)
    return out


def _mentions(expl, word, ans_text):
    """解説が word(誤答) に**独立して**触れているか。

    正解 ans_text の出現の中に完全に埋もれている出現は数えない
    (have known の中の know は「know に触れた」ことにならない)。
    逆に Whom は Who を含むが Who の出現には収まりきらないので、正しく「触れている」になる。
    """
    covered = _spans(expl, ans_text)
    for s, e in _spans(expl, word):
        if not any(cs <= s and e <= ce for cs, ce in covered):
            return True
    return False


def server_constants(root):
    """単元名・レベル名の正典は server/main.py。ここに写経すると片方だけ直されてずれる。"""
    src = open(os.path.join(root, "server", "main.py"), encoding="utf-8").read()
    m = re.search(r"GRAMMAR_UNITS\s*=\s*\[(.*?)\]", src, re.S)
    units = set(re.findall(r'"([^"]+)"', m.group(1))) if m else set()
    m = re.search(r"GRAMMAR_LEVELS\s*=\s*\{(.*?)\}", src, re.S)
    levels = set(re.findall(r'"([^"]+)"\s*:', m.group(1))) if m else set()
    return units, levels


def validate(rows, answers, root):
    """rows(取り込む形の dict のリスト) を answers(正典の正解文字列) と突き合わせて検査する。

    rows は「これから import される中身そのもの」。build の出力でも、コミット済み JSON を
    読み直したものでも同じ物差しで測れるようにしてある (= 手編集も同じ網にかかる)。
    """
    ng = []
    units, levels = server_constants(root)
    if not units or not levels:
        ng.append("NG: server/main.py から GRAMMAR_UNITS / GRAMMAR_LEVELS を読めない (検査が空振りする)")
    if len(rows) != len(answers):
        ng.append(f"NG: 問数が正典と違う: JSON {len(rows)} 問 / content.py {len(answers)} 問")

    for i, (r, ans_text) in enumerate(zip(rows, answers), 1):
        where = f"第{i}問 [{r.get('unit')}/{r.get('level')}]"
        stem = r.get("stem") or ""
        choices = r.get("choices")
        expl = r.get("explanation") or ""

        # --- 取込契約 (server の admin_grammar_import が黙って skip する条件を先に潰す)
        if r.get("unit") not in units:
            ng.append(f"NG: {where} 単元名が GRAMMAR_UNITS に無い → 取込時に黙って skip される: {r.get('unit')}")
        if r.get("level") not in levels:
            ng.append(f"NG: {where} レベル名が GRAMMAR_LEVELS に無い: {r.get('level')}")
        if r.get("subject") != "english":
            ng.append(f"NG: {where} subject が english でない: {r.get('subject')}")
        if len(r.get("source") or "") > 30:
            ng.append(f"NG: {where} source が30字を超える (server 側で切り詰められロールバック不能): {r.get('source')}")
        if not isinstance(choices, list) or len(choices) != 4:
            ng.append(f"NG: {where} 選択肢が4つでない: {choices}")
            continue
        if not isinstance(r.get("answer"), int) or not (0 <= r["answer"] < len(choices)):
            ng.append(f"NG: {where} answer が index として読めない/範囲外: {r.get('answer')!r}")
            continue

        # --- 正解の一意性 (正典 content.py の正解文字列との突き合わせ = 相互チェック)
        if choices[r["answer"]] != ans_text:
            ng.append(f"NG: {where} answer の指す選択肢が正典の正解と違う: "
                      f"{choices[r['answer']]!r} != {ans_text!r}")
        norm = [" ".join(str(c).split()).lower() for c in choices]
        if len(set(norm)) != len(norm):
            ng.append(f"NG: {where} 同じ選択肢が2つある (正解が2つ成立しうる): {choices}")
        for c in choices:
            if not str(c).strip() or str(c) != str(c).strip() or BLANK in str(c):
                ng.append(f"NG: {where} 選択肢の形が不正 (空/前後の空白/空所記号): {c!r}")

        # --- 表記 (紙にもアプリにもそのまま出る。混ざると素人くさい紙になる)
        #   ★実際に「Hokkaido?  B:」と連続スペースが1件紛れていた (機械スキャンで発見)。
        for fld, val in (("stem", stem), ("選択肢", " | ".join(str(c) for c in choices))):
            if "  " in val.replace(BLANK, "@"):
                ng.append(f"NG: {where} {fld} に連続スペース: {val[:60]}")
            if re.search(r"[’‘“”]", val):
                ng.append(f"NG: {where} {fld} にカーリー引用符 (直定引用符に揃える): {val[:60]}")
            if re.search(r"[Ａ-Ｚａ-ｚ０-９　]", val):
                ng.append(f"NG: {where} {fld} に全角の英数字/空白: {val[:60]}")
        if expl.strip() and not expl.rstrip().endswith("。"):
            ng.append(f"NG: {where} 解説が句点で終わっていない: …{expl[-24:]}")

        # --- 出題として自己完結しているか
        if stem.count(BLANK) != 1:
            ng.append(f"NG: {where} 空所 '{BLANK}' がちょうど1個でない: {stem}")
        if not stem.rstrip().endswith(("?", ".", "!")):
            ng.append(f"NG: {where} stem が句読点で終わっていない: {stem}")
        if JP.search(stem):
            ng.append(f"NG: {where} stem に日本語が混ざっている: {stem}")

        # --- 解説
        if not expl.strip():
            ng.append(f"NG: {where} 解説が空")
        if ans_text not in expl:
            ng.append(f"NG: {where} 解説が正解 {ans_text!r} をそのまま含まない (値参照になっていない)")
        if POS_TOKENS.search(expl):
            ng.append(f"NG: {where} 解説に位置を指す書き方がある (正解位置は振り直されるので嘘になる): {expl[:40]}")
        if len(expl) < 40:
            ng.append(f"NG: {where} 解説が短すぎる ({len(expl)}字)")
        # ★誤答への言及は「正解の語句の中に埋もれた出現」を除いて数える。
        #   素朴に `know in expl` とすると、正解 have known の一部に当たって素通りする。
        #   逆に正解を先に伏せ字へ置換すると、Who を伏せた時点で Whom/Whose まで壊れて誤検出になる
        #   (どちらも変異試験で実測した)。位置で包含関係を見るのが唯一正しい数え方。
        if not any(_mentions(expl, str(o), ans_text) for o in choices if o != ans_text):
            ng.append(f"NG: {where} 解説が誤答に一切触れていない: {stem}")
        for fld, val in (("stem", stem), ("explanation", expl)):
            if BAD_CHARS.search(val):
                ng.append(f"NG: {where} {fld} に文字化け/¥ 記法の残骸")

    # --- 正解位置の偏り (生徒は単元・レベル単位で解くので、その中で均す)
    by_key = {}
    for r in rows:
        if isinstance(r.get("answer"), int):
            by_key.setdefault((r.get("unit"), r.get("level")), []).append(r["answer"])
    for k, arr in sorted(by_key.items(), key=lambda x: str(x[0])):
        cnt = {p: arr.count(p) for p in range(4)}
        if max(cnt.values()) - min(cnt.values()) > 1:
            ng.append(f"NG: {k[0]}/{k[1]} の正解位置が偏っている: {cnt}")
        run = best = 1
        for a, b in zip(arr, arr[1:]):
            run = run + 1 if a == b else 1
            best = max(best, run)
        if best >= 3:
            ng.append(f"NG: {k[0]}/{k[1]} で同じ位置の正解が {best} 連続している")
        if len(arr) < MIN_PER_KEY:
            ng.append(f"NG: {k[0]}/{k[1]} が {len(arr)} 問しかない (最低 {MIN_PER_KEY} 問)")

    # --- 通し番号で見たときに「読める並び」になっていないか
    #   ★紙に刷ると全問の正解が一覧で並ぶ。均等でも 1,2,3,4,1,2,3,4… だと周期が丸見えで、
    #     解かずに当てられる (刷り上がりを見て気づいた実際の不良)。アプリ側は抽選なので出ない穴。
    seq = [r["answer"] for r in rows if isinstance(r.get("answer"), int)]
    for i, (a, b, c) in enumerate(zip(seq, seq[1:], seq[2:]), 1):
        if a == b == c:
            ng.append(f"NG: 第{i}問から同じ正解位置が3連続している (通し番号で見たとき)")
            break
    deltas = [(b - a) % 4 for a, b in zip(seq, seq[1:])]
    run, start = 1, 0
    for i, (x, y) in enumerate(zip(deltas, deltas[1:]), 1):
        if x == y:
            run += 1
            if run >= 4:
                ng.append(f"NG: 第{start + 1}問から正解位置が等差で {run + 1} 問続いている "
                          f"(1,2,3,4,1… のような周期は解かずに当てられる)")
                break
        else:
            run, start = 1, i

    # --- 同一ファイル内の重複 (取込時の dedup で黙って消える)
    seen = {}
    for i, r in enumerate(rows, 1):
        key = (" ".join((r.get("stem") or "").split()), r.get("unit"))
        if key in seen:
            ng.append(f"NG: 第{i}問 の stem が 第{seen[key]}問 と同文 (取込時に dedup で消える): {r.get('stem')}")
        seen[key] = i
    return ng


def duplicate_across_seed(rows, root, self_path):
    """seed-data の他のファイルと (stem, unit) が衝突していないか。

    衝突すると取込側の dedup が**黙って skip** するので、投入したつもりで0問増えない。
    """
    import glob
    import json
    ng = []
    mine = {}
    for i, r in enumerate(rows, 1):
        mine[(" ".join((r.get("stem") or "").split()), r.get("unit"))] = i
    for path in sorted(glob.glob(os.path.join(root, "seed-data", "*.json"))):
        if os.path.abspath(path) == os.path.abspath(self_path):
            continue
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        qs = data.get("questions") if isinstance(data, dict) else (data if isinstance(data, list) else [])
        if not isinstance(qs, list):
            continue
        for q in qs:
            if not isinstance(q, dict) or not q.get("stem"):
                continue
            key = (" ".join(str(q["stem"]).split()), q.get("unit"))
            if key in mine:
                ng.append(f"NG: 第{mine[key]}問 の stem が {os.path.basename(path)} と同文 "
                          f"(同一単元なので取込時に skip される): {q['stem']}")
    return ng


BUTTON_ID = "grammarTenseConjWhImportBtn"


def ceo_button_wiring(html, seed_url, expected_count):
    """CEO ダッシュボードの取込ボタンが本当に押せる形で繋がっているか。

    ★教材を作っても、塾長が押せる導線が無ければ本番には1問も入らない
      (クラウドの Claude Code から Railway へは繋げないので、投入は必ず画面側から行う)。
    ★件数のずれも見る。ボタンに書いた数字とシードの中身が食い違うと、
      「90問入れたつもりで実は違う」という報告のずれになる。
    """
    ng = []
    if f'id="{BUTTON_ID}"' not in html:
        ng.append(f"NG: ceo.html に取込ボタン {BUTTON_ID} が無い (塾長が本番へ投入できない)")
        return ng
    m = re.search(r'id="%s"[^>]*?data-seed="([^"]+)"' % BUTTON_ID, html)
    if not m:
        ng.append(f"NG: ceo.html の {BUTTON_ID} に data-seed が無い")
    elif m.group(1) != seed_url:
        ng.append(f"NG: ceo.html の data-seed が seed ファイルを指していない: {m.group(1)} != {seed_url}")
    m = re.search(r'id="%s"[^>]*?data-size="(\d+)"' % BUTTON_ID, html)
    if not m:
        ng.append(f"NG: ceo.html の {BUTTON_ID} に data-size が無い")
    elif int(m.group(1)) != expected_count:
        ng.append(f"NG: ceo.html の data-size がシードの問数と違う: {m.group(1)} != {expected_count}")
    if f"getElementById('{BUTTON_ID}')" not in html or "grammarTenseConjWhImport" not in html:
        ng.append(f"NG: ceo.html で {BUTTON_ID} に click ハンドラが繋がっていない (押しても無反応)")
    return ng


def position_report(rows):
    by_key = {}
    for r in rows:
        by_key.setdefault((r["unit"], r["level"]), {0: 0, 1: 0, 2: 0, 3: 0})[r["answer"]] += 1
    return by_key
