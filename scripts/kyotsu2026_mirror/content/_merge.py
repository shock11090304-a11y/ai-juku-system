# -*- coding: utf-8 -*-
"""パートモジュール(SECTIONS/ANS_SECTIONS)を結合してPROB/ANSを作る共通ヘルパ"""
import importlib.util, os

HERE = os.path.dirname(os.path.abspath(__file__))


def load_part(name):
    p = os.path.join(HERE, name + ".py")
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def merge(meta, part_names):
    parts = [load_part(n) for n in part_names]
    sections = sorted((s for p in parts for s in p.SECTIONS), key=lambda s: s["no"])
    ans = sorted((s for p in parts for s in getattr(p, "ANS_SECTIONS", [])),
                 key=lambda s: s["section"])
    return ({"meta": meta, "sections": sections}, {"sections": ans})
