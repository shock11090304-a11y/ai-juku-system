# -*- coding: utf-8 -*-
"""正解番号の配置を決める共通ロジック。

【なぜ専用モジュールにしたか】
以前は「全小問を md5 順に並べて rank%4」で配っていた。これは**全体**では 15/15/15/15 と
きれいに揃うが、**大問の中**は制御していなかったため次のような偏りが出ていた
(塾長指摘 2026-08-02):

    数学II・B・C 第2問  ②②④④④   ← ④ が 3 連続・5 問中 3 問が同じ番号
    英語 第4問          ②①③③③   ← ③ が 3 連続
    21 大問中 10 大問で「1 大問内の同じ番号が半数以上」

生徒は大問単位で解くので、体感の偏りは大問内の分布で決まる。

【この実装】
大問ごとに 0..3 の**順列**を 1 つ選び、小問には `perm[j % 4]` の順で配る。これで

  - 隣り合う小問が同じ番号になることが**構造的に起きない** (順列は全要素が相異なるため)
    → 最大連続は必ず 1
  - 1 大問内で各番号の出現回数は ⌊n/4⌋ 〜 ⌈n/4⌉ に収まる
    → 5 問なら最多 2 回 (40%)、7 問なら最多 2 回 (29%)
  - どの順列を選ぶかは、全体の分布が最も平らになるものを貪欲に選ぶ
    → 全体の偏りも同時に抑えられる

順列の候補順・大問の処理順はすべて md5 で決めるので、実行するたびに同じ結果になる
(seed JSON が毎回変わると import の重複判定が効かなくなるため決定性は必須)。
"""
import hashlib
import itertools

PERMS = list(itertools.permutations(range(4)))


def _h(*parts):
    return hashlib.md5(":".join(str(p) for p in parts).encode()).hexdigest()


def assign(daimon_sizes, source):
    """大問ごとの正解位置を決める。

    daimon_sizes : [(key, 小問数), ...]   key は大問を一意に識別する文字列
    source       : seed の source 文字列 (決定性のための塩)
    戻り値       : ({key: [pos, ...]}, 全体の分布 [n0, n1, n2, n3])
    """
    order = sorted(range(len(daimon_sizes)),
                   key=lambda i: _h(source, daimon_sizes[i][0]))
    total = [0, 0, 0, 0]
    out = {}
    for i in order:
        key, n = daimon_sizes[i]
        best = None
        # 順列の候補も md5 順に固定してから、全体が最も平らになるものを選ぶ
        for p in sorted(PERMS, key=lambda pp: _h(source, key, pp)):
            seq = [p[j % 4] for j in range(n)]
            cand = list(total)
            for s in seq:
                cand[s] += 1
            spread = max(cand) - min(cand)
            if best is None or spread < best[0]:
                best = (spread, seq, cand)
        out[key] = best[1]
        total = best[2]
    return out, total


def report(rows_by_daimon):
    """点検用。[(ラベル, [pos,...]), ...] を受けて偏りの要約を返す。"""
    circ = '①②③④'
    lines = []
    worst_run = 0
    for label, ans in rows_by_daimon:
        run = cur = 1
        for j in range(1, len(ans)):
            cur = cur + 1 if ans[j] == ans[j - 1] else 1
            run = max(run, cur)
        worst_run = max(worst_run, run)
        top = max(set(ans), key=ans.count)
        lines.append(f'{label}: {"".join(circ[a] for a in ans)} '
                     f'(最多 {circ[top]}×{ans.count(top)}/{len(ans)}・最大連続 {run})')
    return lines, worst_run
