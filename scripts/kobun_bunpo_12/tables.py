# -*- coding: utf-8 -*-
"""この冊子の「基本の確認」＝共有表（scripts/_kobun_tables.py）を全部まとめて刷る。

★問題編には表を絶対に置かない（接続や活用を問う設問が表を写すだけで解けるため）。
★表の実体は scripts/_kobun_tables.py にある。助動詞ドリル（scripts/kobun_jodoushi）と
  共有しているので、表を直すときは必ずそちらを直す（ここにコピーを作らない）。

並べる順は講の進み方に合わせる（用言→助動詞→助詞→敬語）。
第一講から順に受けていく生徒が、解いた直後に自分の講の表を見つけられるようにするため。
"""
from _kobun_tables import (JODOUSHI_TABLES, YOGEN_TABLES,  # noqa: F401
                           JOSHI_TABLES, KEIGO_TABLES,
                           IDENT_FLOWS as FLOWS, CONJ_HEADERS)

TABLES = YOGEN_TABLES + JODOUSHI_TABLES + JOSHI_TABLES + KEIGO_TABLES
