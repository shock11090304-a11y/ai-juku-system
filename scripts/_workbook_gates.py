# -*- coding: utf-8 -*-
"""
問題集ビルダー共通の機械ゲート（教科非依存）。

  import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
  from _workbook_gates import Gate
  g = Gate()
  g.answer_leak(qa_items, printed_text)      # 解答が問題編の別の場所に印字されていないか
  g.longest_tell(mcs)                        # 正解肢が最長になっていないか
  g.desc_ending(descs)                       # 記述の文末が設問の問いに正対しているか
  g.exp_choice_refs(mcs)                     # 解説の①②③④参照と正解番号の衝突
  g.char_limit(descs)                        # 記述の模範解答が字数制限内か（機械数え直し）
  g.choice_position(mcs)                     # 正解位置の偏り
  g.glyphs(any_object)                       # PDFで黒四角/豆腐になる文字
  g.report()                                 # FAILがあれば sys.exit(1)

★このモジュールが存在する理由（2026-07-28 中学社会プリントの反省）:
  これら6種は「AIの3並列レビューでしか出ない」と思われていたが、全部Pythonで判定できる。
  1回のAIレビューより桁違いに安く何度でも回せるので、**AIに探させる前にここで潰す**。
  実際この6種は、初版で出た致命2件+要修正5件のうち4件をゼロコストで検出できた。

■ 各メソッドが受け取る形（教科ごとの dict 構造に依存しないよう、最小限の形に正規化して渡す）
  qa_items : [{"q":問題文, "ans":解答}]                     一問一答など短答
  mcs      : [{"where":"大問1問2", "choices":[...], "ans":idx, "exp":解説}]
  descs    : [{"where":"記述1", "q":設問文, "ans":模範解答, "limit":字数}]
"""
import re
import sys
import unicodedata
from collections import Counter

CIRC = "①②③④⑤⑥⑦⑧"

# ★組分数・根号の目印（build_common.mathmark が組版に変える）。
#   ゲートは**紙に出る形**で数えないといけないので、数える前に必ず外す。
#   外し忘れると「[[sqrt:8]]」が10字と数えられ、字数制限も選択肢の長さ比較も狂う。
_MARK_FRAC = re.compile(r"\[\[frac:([^|\]]+)\|([^\]]+)\]\]")
_MARK_SQRT = re.compile(r"\[\[sqrt:([^\]]+)\]\]")


def strip_math(s):
    """[[frac:a|b]] → a/b ／ [[sqrt:x]] → √x  （字数・照合はこの形で行う）"""
    s = _MARK_SQRT.sub(r"√\1", str(s))
    return _MARK_FRAC.sub(r"\1/\2", s)

# 「〜から。」で終わってよいのは理由を聞かれたときだけ
REASON_WORDS = ("理由", "なぜ", "原因", "わけ")
# PDF(Arial Unicode / Hiragino)で出るが黒四角にならない記号
SAFE_EXTRA = set("①②③④⑤⑥⑦⑧―－−℃²³　★●◆▲√≧≦")


class Gate:
    def __init__(self, verbose=True):
        self.fails = []
        self.warns = []
        self.verbose = verbose

    # ------------------------------------------------------------------ 出力
    def _fail(self, msg):
        self.fails.append(msg)

    def _warn(self, msg):
        self.warns.append(msg)

    def _ok(self, msg):
        if self.verbose:
            print("  " + msg)

    def report(self, exit_on_fail=True):
        for w in self.warns:
            print("WARN:", w)
        if self.fails:
            print(f"\n=== FAIL {len(self.fails)}件 ===")
            for f in self.fails:
                print(" ×", f)
            if exit_on_fail:
                sys.exit(1)
            return False
        print(f"\n=== ALL PASS ({len(self.warns)} warnings) ===")
        return True

    # ------------------------------------------- 1. 解答の自己漏洩（最重要）
    def answer_leak(self, qa_items, printed_text, allow=None, min_len=2, extra_texts=None,
                    own_blocks=None):
        """qa_items の解答が printed_text（＝問題編に印字される他の全テキスト）に
        出ていないか。出ていれば知識ゼロで得点できてしまう。

        ★own_blocks[i] = その設問**自身**が印字する文字列のリスト（選択肢・語群・整序トークン）。
          4択の正解は当然その設問の選択肢に印字されているので、これを除かないと
          **全ての4択が漏洩として検出される**（合成データで実際に 50/50 が誤検出された）。
          設問文だけを除く実装では足りない。

        ★printed_text には**一問一答どうしの設問文も必ず含める**こと。
          理科版で (11)沸点 が (12)の設問文に、(19)中和 が (20)の設問文に出ていたのを
          「同じ第1部の中は走査対象外」という設計ミスで見逃した。
          この関数は qa_items 自身の設問文も自動で走査対象に足す（自分の設問文だけは除外）。
        ★min_len は既定2。理科・社会の重要語は「沸点」「中和」「気孔」など2字が主力で、
          3字にすると40問中17問が素通しになる（実測）。
        ★「電気抵抗（抵抗）」のような許容解答は、括弧の外だけでなく**中の語も**走査する。
          印字されていたのは括弧内の「抵抗」のほうだった。
        allow = {語: 許容する理由} 長い語の一部として出るだけの無害な衝突を明示的に免除する。
        """
        allow = allow or {}
        own_q = [str(it.get("q", "")) for it in qa_items]
        base = strip_math(" ".join([printed_text] + own_q + list(extra_texts or [])))
        leaks, allowed = [], []
        for i, it in enumerate(qa_items, start=1):
            ans = strip_math(it["ans"])        # ★needle 側も外す（掛け忘れると数式入りの答えが無検査）
            body = re.sub(r"^約|（.*?）|\(.*?\)", "", ans).strip()
            cands = [body] + re.findall(r"[（(](.+?)[）)]", ans)
            # 自分自身が印字するもの（設問文＋その設問の選択肢など）は除外して走査する
            own = strip_math(own_q[i - 1])
            hay = base.replace(own, " ") if own else base
            for ownb in (own_blocks[i - 1] if own_blocks else []):
                if ownb:
                    hay = hay.replace(strip_math(ownb), " ")
            for c in cands:
                c = c.strip()
                if len(c) < min_len or c not in hay:
                    continue
                (allowed if c in allow else leaks).append(f'({i}) {ans} ←「{c}」')
                break
        if leaks:
            self._fail(f"[解答漏洩] {len(qa_items)}問中 {len(leaks)}問の答えが問題編の別の場所に"
                       f"印字されている: " + "／".join(leaks))
        else:
            self._ok(f"[解答漏洩] {len(qa_items)}問 漏洩なし OK（{min_len}字以上・括弧内も走査）"
                     + (f"／許容: {'／'.join(allowed)}" if allowed else ""))

    # ------------------------------------- 8. 模範解答が自分の採点キーを満たすか
    def keys_consistency(self, descs, sample_len=None):
        """★「採点のポイント(keys)がそろっていれば正解」と冊子に書いておきながら、
        模範解答がそのkeysを満たしていない、という自己矛盾を検出する。
        keysは日本語の要約なので完全な自動判定はできないが、
        「keyの中の名詞が模範解答に1つも出てこない」なら確実に不整合。"""
        import unicodedata as _u
        bad = []
        for d in descs:
            for k in d.get("keys", []):
                core = re.sub(r"(にふれている|ことにふれている|と書けている|を書いている)$", "", k)
                # keyから内容語（漢字/カタカナ2字以上）を抜き、1つも解答に無ければ不整合
                words = [w for w in re.findall(r"[一-龥ァ-ヶ]{2,}", core)
                         if w not in ("説明", "解答", "記述", "内容", "以上", "以内")]
                if words and not any(w in strip_math(d["ans"]) for w in words):
                    bad.append(f'{d.get("where","?")}「{k[:22]}…」')
        if bad:
            self._fail("[採点キー] 模範解答がそのkeyを満たしていない"
                       "（模範解答どおり書いた生徒が×になる）: " + "／".join(bad))
        else:
            self._ok(f"[採点キー] 記述{len(descs)}問 模範解答が全keyの内容語を含む OK")

    # ------------------------------------------------- 2. 正解肢が最長のテル
    def longest_tell(self, mcs, ratio=0.5, min_n=4):
        tot = len(mcs)
        # ★母数が少ないと「偏り」は統計的に意味がない（4択2問で両方最長でも偶然の範囲）。
        #   ここを見落とすと、正しい教材にFAILを出す偽陽性ゲートになる。
        if tot < min_n:
            self._ok(f"[テル] 4択{tot}問のみ＝判定に必要な{min_n}問未満のためスキップ"
                     "（4択をもっと入れるか、手で長さを確認する）")
            return
        # ★「単独で最長」に絞る。同点も最長と数えると、選択肢の字数がそろっている四択
        #   （「あああ／いいい／ううう／えええ」のような等長の語）が全問ヒットして誤検出になる。
        #   長さで当てられるのは正解肢だけが飛び抜けて長いときであって、同点は tell ではない。
        def _sole_longest(m):
            L = [len(strip_math(c)) for c in m["choices"]]
            return L[m["ans"]] == max(L) and L.count(max(L)) == 1

        hit = [m for m in mcs if _sole_longest(m)]
        if len(hit) > tot * ratio:
            self._fail(f"[テル] 4択{tot}問中 {len(hit)}問で正解肢が最長（期待値{tot/4:.1f}問）。"
                       "長さだけで当てられる: " + "／".join(m.get("where", "?") for m in hit))
        else:
            self._ok(f"[テル] 4択{tot}問中 正解肢が最長なのは{len(hit)}問（期待値{tot/4:.1f}）OK")

    # ------------------------------------------- 3. 記述の文末が問いに正対か
    def desc_ending(self, descs):
        bad = []
        for d in descs:
            asks_reason = any(k in d["q"] for k in REASON_WORDS)
            if str(d["ans"]).endswith("から。") and not asks_reason:
                bad.append(f'{d.get("where","?")}（…{d["q"][-12:]}／…{d["ans"][-6:]}）')
        if bad:
            self._fail("[記述] 理由を聞いていないのに模範解答が「〜から。」で終わっている"
                       "（公立入試は文末不一致で減点）: " + "／".join(bad))
        else:
            self._ok(f"[記述] {len(descs)}問 設問の問いと模範解答の文末が一致 OK")

    # --------------------------------------- 4. 解説の選択肢番号ズレ（並べ替え事故）
    def exp_choice_refs(self, mcs):
        n = 0
        for m in mcs:
            refs = {CIRC.index(c) for c in m.get("exp", "") if c in CIRC}
            if not refs:
                continue
            n += 1
            if m["ans"] in refs:
                self._fail(f'[解説参照] {m.get("where","?")} 解説が正解{CIRC[m["ans"]]}を誤答として'
                           "説明している（選択肢の並べ替え後に直し忘れ）")
            ghost = [r for r in refs if r >= len(m["choices"])]
            if ghost:
                self._fail(f'[解説参照] {m.get("where","?")} 存在しない選択肢を参照: '
                           + "".join(CIRC[r] for r in ghost))
        self._ok(f"[解説参照] 番号参照のある解説{n}件 正解番号との衝突なし OK")

    # ------------------------------------------------------ 5. 記述の字数
    def char_limit(self, descs, short_ratio=0.5):
        for d in descs:
            ln = len(strip_math(d["ans"]))
            if ln > d["limit"]:
                self._fail(f'[字数] {d.get("where","?")} 模範解答が字数超過: {ln}字 > 制限{d["limit"]}字'
                           f'「{d["ans"]}」')
            elif ln < d["limit"] * short_ratio:
                self._warn(f'[字数] {d.get("where","?")} 制限より大幅に短い: {ln}字/{d["limit"]}字')
        self._ok(f"[字数] 記述{len(descs)}問 機械数え直し完了")

    # ------------------------------------------------------ 6. 正解位置の偏り
    def choice_position(self, mcs, ratio=0.5, min_n=4):
        tot = len(mcs)
        if tot < min_n:   # 母数不足（longest_tell と同じ理由）
            self._ok(f"[正解位置] 4択{tot}問のみ＝判定に必要な{min_n}問未満のためスキップ")
            return
        pos = Counter(m["ans"] for m in mcs)
        dist = "／".join(f"{k+1}番:{pos.get(k,0)}" for k in range(4))
        if max(pos.values()) > tot * ratio:
            self._fail(f"[正解位置] {tot}問中 最頻{max(pos.values())}問に偏り: {dist}")
        else:
            self._ok(f"[正解位置] 4択{tot}問 分布 {dist} OK")

    # ------------------------------------------------------ 7. 文字（黒四角）
    def glyphs(self, obj):
        bad = Counter()

        def walk(o):
            if isinstance(o, str):
                yield o
            elif isinstance(o, dict):
                for v in o.values():
                    yield from walk(v)
            elif isinstance(o, (list, tuple)):
                for v in o:
                    yield from walk(v)

        for s in walk(obj):
            for ch in s:
                if ch in SAFE_EXTRA or ch in "\n\t":
                    continue
                cp = ord(ch)
                if cp < 0x20:
                    bad[f"制御文字 U+{cp:04X}"] += 1
                elif 0x1F000 <= cp <= 0x1FAFF or 0x2600 <= cp <= 0x27BF or cp in (0xFE0F, 0x20E3):
                    bad[f"絵文字 {ch}"] += 1
                elif unicodedata.category(ch) in ("Cn", "Co", "Cs"):
                    bad[f"未定義/私用領域 {ch} U+{cp:04X}"] += 1
        if bad:
            for k, v in bad.items():
                self._fail(f"[文字] PDFで黒四角/豆腐になる: {k} ×{v}")
        else:
            self._ok("[文字] 絵文字・制御文字・私用領域 なし OK")
