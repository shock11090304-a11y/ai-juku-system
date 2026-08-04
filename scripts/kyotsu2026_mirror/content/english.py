# -*- coding: utf-8 -*-
"""english.py: パート結合(自動生成マージャ)"""
from _merge import merge as _m
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

META = {
    "title": "英語（リーディング）", "outname": "英語リーディング", "time": "80分", "max_points": 100,
    "notes": [
        "解答は，解答用紙の解答欄にマークしなさい。",
        "問題冊子の余白等は適宜利用してよいが，どのページも切り離してはいけません。",
        "不正行為に対しては厳正に対処します。",
    ],
}

PROB, ANS = _m(META, ['english_a', 'english_b', 'english_c'])
