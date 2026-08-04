# -*- coding: utf-8 -*-
"""
中学生 夏休み特訓プリント［5科総合］ 機械ゲート。

  python3 check.py     → ALL PASS なら exit 0、FAIL があれば exit 1

構造が DAY 単位なので _workbook_check.run_generic はそのまま使えない。
共通ゲート（_workbook_gates.Gate）だけを借りて、この教材の形に合わせて呼ぶ。

  T1  10日ぶんそろっているか／各日 5科×4問／1日100点
  T2  範囲ラベルが設計どおりか（DAY1-4=中1範囲 / 5-8=中2範囲 / 9-10=中3 1学期の範囲）
  T2b ★DAY1-4（中1範囲）に中2以降の語が混ざっていないか（生物＋物理の2本立て）
      （現行課程＝平成29年告示では 光合成・蒸散・気孔・葉緑体・細胞・道管・師管 は
        中2「生物の体のつくりと働き」。旧課程の区分で作ると中1生が未習で解けない）
  T3  mc の ans がレンジ内／選択肢の重複／全問に exp
  T4  calc の単位一致・work あり／desc の limit・keys あり
  T5  ★その日の theme・科目 lead が、その日の答えを言っていないか
      （見出しが答えを漏らす事故＝[[chem-camp-workbook-and-print-gates]] と同型）
  T6  ★全1000点ぶんの答えが、問題編に印字される他のテキストに出ていないか
  T6b ★記述（desc）は T6 の走査から外れるので、採点キーの言い回しが他の日の設問文・
      選択肢に印字されていないかを別に見る（記述の答えが他の日の正解肢に丸ごと出ていた事故）
  T7  正解肢が最長のテル／正解位置の偏り／解説の①②③④参照ズレ／記述の文末・字数・採点キー
  T8  設問文の重複（10日ぶんを横断。同じ問題を2回出していないか）
  T8b ★同じ本文（古文・長文）の使い回し。形式を変えて2回出すと T8 は素通しになる
  T9  英語の order（整序）：tokens を並べ替えると ans になるか（機械照合）
"""
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from _workbook_gates import Gate       # noqa: E402
import content as C                     # noqa: E402

SUBJECTS = ["英語", "数学", "国語", "理科", "社会"]
EXPECT_RANGE = {1: "中1範囲", 2: "中1範囲", 3: "中1範囲", 4: "中1範囲",
                5: "中2範囲", 6: "中2範囲", 7: "中2範囲", 8: "中2範囲",
                9: "中3 1学期の範囲", 10: "中3 1学期の範囲"}
TAG = re.compile(r"<[^>]+>")


def flat(DAYS):
    for D in DAYS:
        for sec in D["sections"]:
            for i, q in enumerate(sec["qs"], start=1):
                yield f'DAY{D["day"]}{sec["subj"]}{i}', D, sec, q


def printed_text(DAYS, META):
    """問題編に印字される全テキスト（ans/exp/work/keys は入らない）。"""
    buf = [str(META.get(k, "")) for k in ("title", "subtitle", "intro", "level")]
    for D in DAYS:
        buf += [D["theme"], D["range"], D.get("range_note", "")]
        for sec in D["sections"]:
            buf += [sec["subj"], sec.get("lead", "")]
            for q in sec["qs"]:
                buf.append(q["q"])
                buf += list(q.get("choices", []))
                buf += list(q.get("tokens", []))
    return " ".join(TAG.sub(" ", x) for x in buf)


def _norm_en(s):
    """英文の比較用正規化（大小・記号・連続空白を吸収）。"""
    return re.sub(r"[\s]+", " ", re.sub(r"[.,?!;:'\"]", " ", str(s))).strip().lower()


def main():
    print("=== 中学生 夏休み特訓プリント［5科総合］ check ===")
    g = Gate()
    DAYS = C.DAYS
    ALL = list(flat(DAYS))

    # ------------------------------------------------------------ T1/T2 構造
    if len(DAYS) != 10:
        g._fail(f"[構成] DAY が {len(DAYS)} 日ぶんしかない（10日必要）")
    for D in DAYS:
        subs = [s["subj"] for s in D["sections"]]
        if subs != SUBJECTS:
            g._fail(f'[構成] DAY{D["day"]} の科目が {subs}（{SUBJECTS} の順で5科必要）')
        for sec in D["sections"]:
            if len(sec["qs"]) != 4:
                g._fail(f'[構成] DAY{D["day"]} {sec["subj"]} が {len(sec["qs"])}問（4問必要）')
        tot = sum(q.get("pt", 5) for s in D["sections"] for q in s["qs"])
        if tot != 100:
            g._fail(f'[配点] DAY{D["day"]} の合計が {tot}点（100点必要）')
        if D["range"] != EXPECT_RANGE.get(D["day"]):
            g._fail(f'[範囲] DAY{D["day"]} の range が「{D["range"]}」'
                    f'（設計は「{EXPECT_RANGE.get(D["day"])}」）')
    g._ok(f"[構成] {len(DAYS)}日×5科×4問＝{len(ALL)}問／各日100点／範囲ラベル OK")

    # ------------------------------------------------------------ T2b 学年範囲の禁止語
    # ★現行課程（平成29年告示・令和3年度全面実施）では、光合成・蒸散・気孔・葉緑体・細胞・
    #   道管・師管は中2「生物の体のつくりと働き」の内容。中1は「いろいろな生物とその共通点」
    #   （花のつくり・植物の分類）まで。旧課程（中1「植物の生活と種類」）の記憶で作ると、
    #   DAY1-4 を配られた中1生がまるごと解けない設問になる。
    # ★同じ事故は物理でも起きる。旧課程では中1「力と圧力」だった圧力・大気圧は、現行課程では
    #   中2「気象とその変化」（第2分野(4)）の内容で、中1「身近な物理現象」の力の働きには
    #   入っていない（水圧・浮力は中3「運動とエネルギー」）。生物の語だけ見ていると素通しになり、
    #   実際に DAY4 理科2 が圧力の計算（1200Pa）で中1生に未習の5点を配っていた。
    #   「Pa」は英語の Paul / Park などに当たらないよう、前後が英字でないときだけ拾う。
    NG_CHU1 = ["光合成", "蒸散", "気孔", "葉緑体", "細胞", "道管", "師管"]
    NG_CHU1_BUTSURI = [("圧力", "圧力"), ("Pa", r"(?<![A-Za-z])Pa(?![A-Za-z])"),
                       ("パスカル", "パスカル"), ("大気圧", "大気圧"),
                       ("水圧", "水圧"), ("浮力", "浮力")]
    ng, ngb = [], []
    for where, D, sec, q in ALL:
        if D["day"] > 4:
            continue
        txt = " ".join([str(q.get("q", "")), str(q.get("ans", "")),
                        str(q.get("unit", "")), str(q.get("work", "")),
                        " ".join(str(x) for x in q.get("choices", [])),
                        " ".join(str(k) for k in q.get("keys", []))])
        hit = [w for w in NG_CHU1 if w in txt]
        if hit:
            ng.append(f'{where}（{"・".join(hit)}）')
        hitb = [w for w, pat in NG_CHU1_BUTSURI if re.search(pat, txt)]
        if hitb:
            ngb.append(f'{where}（{"・".join(hitb)}）')
    if ng:
        g._fail("[学年範囲] DAY1-4（中1範囲）の設問・模範解答・採点キーに中2内容の語がある"
                "（現行課程では中2「生物の体のつくりと働き」）: " + "／".join(ng))
    else:
        g._ok("[学年範囲] DAY1-4 に中2生物の語（光合成・蒸散・気孔ほか）なし OK")
    if ngb:
        g._fail("[学年範囲] DAY1-4（中1範囲）に圧力の語がある"
                "（現行課程では圧力・大気圧は中2「気象とその変化」／水圧・浮力は中3）: "
                + "／".join(ngb))
    else:
        g._ok("[学年範囲] DAY1-4 に中2/中3物理の語（圧力・大気圧・水圧・浮力ほか）なし OK")

    # ------------------------------------------------------------ T3/T4 設問
    mcs, descs = [], []
    for where, D, sec, q in ALL:
        if not str(q.get("exp", "")).strip():
            g._fail(f"[解説] {where} の解説が空")
        t = q["type"]
        if t == "mc":
            ch = q["choices"]
            if len(ch) < 3:
                g._fail(f"[選択肢] {where} 選択肢が{len(ch)}個")
            if len(set(ch)) != len(ch):
                g._fail(f"[選択肢] {where} 同じ選択肢が2つある")
            if not isinstance(q["ans"], int) or not (0 <= q["ans"] < len(ch)):
                g._fail(f'[選択肢] {where} ans={q["ans"]} がレンジ外（★ans は 0 始まり）')
            else:
                mcs.append({"where": where, "choices": ch, "ans": q["ans"],
                            "exp": q.get("exp", "")})
        elif t == "calc":
            if not str(q.get("work", "")).strip():
                g._fail(f"[途中式] {where} calc なのに work が無い")
            m = re.match(r"^[約]?([0-9０-９.．/／:：〜~,、\-−+±]+)\s*(.*)$", str(q["ans"]).strip())
            u = m.group(2).strip() if m else ""
            want = str(q.get("unit", "")).strip()
            if want and u and u != want:
                g._fail(f'[単位] {where} 解答欄「{want}」と模範解答「{q["ans"]}」が食い違う')
        elif t == "desc":
            if not q.get("limit"):
                g._fail(f"[記述] {where} に limit が無い")
            if not q.get("keys"):
                g._fail(f"[記述] {where} に keys が無い")
            descs.append({"where": where, "q": q["q"], "ans": q["ans"],
                          "limit": q.get("limit", 40), "keys": q.get("keys", [])})
        elif t == "order":
            if not q.get("tokens"):
                g._fail(f"[整序] {where} に tokens が無い")
    g._ok(f"[設問] 4択{len(mcs)}問／記述{len(descs)}問 形式チェック OK")

    # ------------------------------------------------------------ T9 整序の機械照合
    bad = []
    for where, D, sec, q in ALL:
        if q["type"] != "order" or not q.get("tokens"):
            continue
        want = _norm_en(q["ans"]).split()
        got = sorted(_norm_en(" ".join(q["tokens"])).split())
        if sorted(want) != got:
            bad.append(f'{where}（tokens={q["tokens"]} / ans=「{q["ans"]}」）')
    if bad:
        g._fail("[整序] tokens を並べ替えても模範解答にならない: " + "／".join(bad))
    else:
        g._ok("[整序] tokens と模範解答の語がすべて一致 OK")

    # ------------------------------------------------------ T9b 語群が答えの順に並んでいないか
    # ★上の T9 は sorted() で**語の集合**しか見ないので、tokens が正解と同じ順に並んでいても
    #   ALL PASS する。book.py の _ansbody は tokens をリスト順にそのまま印字するため、
    #   その状態だと生徒は語群を左から読み写すだけで正解が書ける（初版で12問中6問がこれだった）。
    #   並べ替えの問題として成立しなくなるので、並び順まで拘束する。
    def _aw(s):
        return re.sub(r"[.,?!;:]", " ", str(s)).lower().split()

    def _pairs(seq):
        return {(seq[i], seq[i + 1]) for i in range(len(seq) - 1)}

    order_bad = []
    for where, D, sec, q in ALL:
        if q["type"] != "order" or not q.get("tokens"):
            continue
        tl = [t.lower() for t in q["tokens"]]
        al = _aw(q["ans"])
        if tl == al:
            order_bad.append(f"{where}（語群が正解と完全に同順）")
            continue
        lead = 0
        while lead < min(len(tl), len(al)) and tl[lead] == al[lead]:
            lead += 1
        if lead >= 2:
            order_bad.append(f"{where}（先頭{lead}語が正解と同順）")
            continue
        ap = _pairs(al)
        if ap and len(_pairs(tl) & ap) * 2 > len(ap):
            order_bad.append(f"{where}（正解で隣り合う語の組が語群にも半数超そのまま残っている）")
    if order_bad:
        g._fail("[整序の並び] 語群を左から読むだけで答えが書ける: " + "／".join(order_bad))
    else:
        g._ok("[整序の並び] 語群はすべて正解と別の順に並んでいる OK")

    # ------------------------------------------------------------ T5 見出しの漏洩
    lead_leak = []
    for where, D, sec, q in ALL:
        ans = str(q["ans"])
        if q["type"] == "mc":
            ans = str(q["choices"][q["ans"]])
        core = re.sub(r"^約|（.*?）|\(.*?\)", "", ans).strip()
        if len(core) < 3:
            continue
        for label, txt in (("theme", D["theme"]), ("lead", sec.get("lead", ""))):
            if core and core in str(txt):
                lead_leak.append(f'{where}「{core}」← {label}「{txt}」')
    if lead_leak:
        g._fail("[見出し漏洩] その日のテーマ／科目の指示文が答えを言っている: "
                + "／".join(lead_leak))
    else:
        g._ok("[見出し漏洩] theme・lead が答えを言っていない OK")

    # ------------------------------------------------------------ T6 解答漏洩
    ptxt = printed_text(DAYS, C.META)
    qa, own = [], []
    for where, D, sec, q in ALL:
        # 記述は文章なので一致するはずがない（走査対象にすると意味がない）
        if q["type"] == "desc":
            continue
        a = str(q["choices"][q["ans"]]) if q["type"] == "mc" else str(q["ans"])
        qa.append({"q": q["q"], "ans": a})
        # ★その設問自身が印字するもの（選択肢・整序トークン）は走査対象から外す。
        #   4択の正解はその設問の選択肢に必ず印字されているので、外さないと全問誤検出になる。
        own.append(list(q.get("choices", [])) + list(q.get("tokens", [])))
    g.answer_leak(qa, ptxt, allow=getattr(C, "LEAK_ALLOW", {}), min_len=3, own_blocks=own)

    # ------------------------------------------------- T6b 記述（desc）の採点キーの漏洩
    # ★上の T6 は `if q["type"] == "desc": continue` で記述をまるごと外している。
    #   記述の模範解答は文章なので完全一致では捕まらない、というのがその理由だが、
    #   そのせいで「記述の答えが他の日の選択肢に丸ごと書いてある」事故を構造的に見逃す。
    #   （DAY4国語4「あはれなり」の模範解答が、DAY8国語2の正解肢
    #     「しみじみとした趣が感じられる」としてそのまま印字されていた。ゲートはALL PASSだった。）
    #   完全一致は無理でも、採点キーの内容語が**他の日**の設問文・選択肢に印字されていないかは
    #   走査できる。同じ日の中は、本文を読ませる設問（「3に示した文章から…」）が正常なので見ない。
    #   走査するのは採点キーの**ひらがな／カタカナの言い回し**だけにする。漢字の名詞
    #   （二酸化炭素・平方根・日本語…）は単元名そのものなので他の日の設問文に出て当たり前で、
    #   拾うと毎回FAILする無意味なゲートになる。答えを漏らすのは「しみじみと」のような
    #   言い回しのほう。さらに、2日以上に出ている語は定型表現なので候補から外す
    #   （「なっている」のような語尾で誤検出しない）。
    per_day = {D["day"]: printed_text([D], {}) for D in DAYS}
    dleak = []
    for where, D, sec, q in ALL:
        if q["type"] != "desc":
            continue
        hit = []
        for k in q.get("keys", []):
            core = re.sub(r"(ことにふれている|にふれている|と書けている|を書いている)$", "", str(k))
            for w in re.findall(r"[ぁ-ん]{5,}|[ァ-ヶ]{3,}", core):
                where_days = [d for d, t in per_day.items() if d != D["day"] and w in t]
                if len(where_days) == 1:
                    hit.append(f'{w}→DAY{where_days[0]}')
        if hit:
            dleak.append(f'{where}（{"・".join(sorted(set(hit)))}）')
    if dleak:
        g._fail("[解答漏洩] 記述の採点キーの語が、他の日の設問文・選択肢に印字されている"
                "（ページをめくれば書ける）: " + "／".join(dleak))
    else:
        g._ok(f"[解答漏洩] 記述{len(descs)}問 採点キーの語が他の日に印字されていない OK")

    # ------------------------------------------------------------ T7 共通ゲート
    g.longest_tell(mcs)
    g.choice_position(mcs)
    g.exp_choice_refs(mcs)
    g.desc_ending(descs)
    g.char_limit(descs)
    g.keys_consistency(descs)
    g.glyphs([C.META, C.POINTS, DAYS])

    # ------------------------------------------------------------ T8 重複
    dup = [k for k, v in Counter(q["q"] for _, _, _, q in ALL).items() if v > 1]
    if dup:
        g._fail(f"[重複] 同じ設問文が2回以上出ている（{len(dup)}件）: " + "／".join(dup[:6]))
    else:
        g._ok(f"[重複] {len(ALL)}問 設問文の重複なし OK")

    # ------------------------------------------------------------ T8b 本文の使い回し
    # ★T8 は設問文の**完全一致**しか見ないので、同じ古文・同じ長文を「一方は記述・他方は4択」
    #   のように形式を変えて2回出すと素通しになる（DAY4国語4とDAY8国語1・2で、枕草子
    #   「秋は夕暮れ」の同じ本文から同じ語の意味を2回問うていた）。
    #   本文は30字も続けば同一素材なので、30字の連続一致で検出する。
    #   ★走査するのは設問文全体ではなく、引用された本文の部分だけ。
    #     「（　）内の語を並べかえて、日本語の意味に合う英文を完成させなさい」のような**指示文**は
    #     日をまたいで同じ言い回しになるのが正常で、設問文まるごとを見ると指示文だけでFAILする。
    NGRAM = 30
    seen, body_dup = {}, []
    for where, D, sec, q in ALL:
        # ★空欄の「（　）」の中の全角スペースは区切りではない。先につぶさないと、
        #   指示文の途中で切れて「）内の語を並べかえて…」が本文あつかいになる。
        raw = re.sub(r"（[　\s]+）", "（）", str(q["q"]))
        # 全角スペースより後ろに置いた本文＋「…」でくくって引用した本文
        parts = re.split(r"[　]+", raw)[1:] + re.findall(r"「([^」]{20,})」", raw)
        grams = []
        for p in parts:
            s = re.sub(r"[\s　]+", "", p)
            grams += [s[i:i + NGRAM] for i in range(len(s) - NGRAM + 1)]
        for gm in grams:
            if gm in seen and seen[gm] != where:
                body_dup.append(f'{seen[gm]} と {where}（「{gm[:24]}…」）')
                break
        for gm in grams:
            seen.setdefault(gm, where)
    if body_dup:
        g._fail(f"[重複] 同じ本文（30字以上）を2か所で使い回している（{len(body_dup)}件）: "
                + "／".join(body_dup[:6]))
    else:
        g._ok(f"[重複] {len(ALL)}問 本文（30字連続）の使い回しなし OK")

    g.report()


if __name__ == "__main__":
    main()
