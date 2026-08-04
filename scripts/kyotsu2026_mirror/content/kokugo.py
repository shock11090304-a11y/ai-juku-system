# -*- coding: utf-8 -*-
"""kokugo.py: パート結合(自動生成マージャ)"""
from _merge import merge as _m
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

META = {
    "title": "国　語", "outname": "国語", "time": "90分", "max_points": 200,
    "notes": [
        "解答は，解答用紙の解答欄にマークしなさい。",
        "問題は第1問から第5問まであり，全問必答です。",
        "問題冊子の余白等は適宜利用してよいが，どのページも切り離してはいけません。",
    ],
}

PROB, ANS = _m(META, ['kokugo_a', 'kokugo_b', 'kokugo_c'])
