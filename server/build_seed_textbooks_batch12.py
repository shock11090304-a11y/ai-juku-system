#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🆓 batch12: 数学Ⅲ 後半5単元 ⭐ 数学Ⅲ 10/10 完成
収録: 積分の応用 / 面積・体積 / 媒介変数表示 / 曲線の長さ / 回転体の体積
"""
import json, os
OUTPUT = os.path.join(os.path.dirname(__file__), "seed_textbooks_batch12.json")

INT_APP = {
    "title": "積分の応用 — 区分求積法・偶関数奇関数・部分分数",
    "subtitle": "面積・体積を超えた積分の応用",
    "subject": "数学Ⅲ", "topic": "積分の応用", "level": "高校標準",
    "sections": [
        {"type": "intro", "heading": "はじめに — 積分の応用は計算技法と幾何学の交差点",
         "body": "積分は単に「面積を求める道具」ではなく、区分求積法・偶関数奇関数の対称性活用・部分分数分解など、計算技法を駆使して複雑な式を扱える。\n\n比喩を一つ。積分の応用は「数学のマルチツール」。1 つの基本概念 (=積分) から、面積・体積・長さ・密度・期待値などあらゆる量を計算できる。"},
        {"type": "theory", "heading": "基本事項 — 積分の応用テクニック",
         "body": "■ 区分求積法\n離散的な和の極限として定積分を表現:\n\\[ \\lim_{n \\to \\infty} \\dfrac{1}{n} \\sum_{k=1}^{n} f\\left(\\dfrac{k}{n}\\right) = \\int_0^1 f(x) \\, dx \\]\n\n用途: \\( \\sum_{k=1}^n \\) の極限を求める問題で、定積分に変換して解く。\n\n■ 偶関数・奇関数の積分\n- 偶関数 \\( f(-x) = f(x) \\): \\( \\int_{-a}^{a} f(x) dx = 2\\int_0^a f(x) dx \\)\n- 奇関数 \\( f(-x) = -f(x) \\): \\( \\int_{-a}^{a} f(x) dx = 0 \\)\n\n例: \\( \\int_{-1}^{1} x^3 dx = 0 \\) (\\( x^3 \\) は奇関数)\n例: \\( \\int_{-1}^{1} x^2 dx = 2 \\int_0^1 x^2 dx = 2/3 \\) (\\( x^2 \\) は偶関数)\n\n■ 部分分数分解\n\\( \\dfrac{P(x)}{(x-a)(x-b)} = \\dfrac{A}{x-a} + \\dfrac{B}{x-b} \\) と分解。\n\n例: \\( \\int \\dfrac{1}{x^2-1} dx = \\int \\dfrac{1}{(x-1)(x+1)} dx \\)\n\\( \\dfrac{1}{(x-1)(x+1)} = \\dfrac{1}{2}\\left(\\dfrac{1}{x-1} - \\dfrac{1}{x+1}\\right) \\)\n積分: \\( \\dfrac{1}{2} \\log\\left|\\dfrac{x-1}{x+1}\\right| + C \\)\n\n■ \\( \\sin^n x, \\cos^n x \\) の積分\n- \\( n \\) が偶数: 半角公式で次数を下げる\n- \\( n \\) が奇数: 1 つだけ取り出して \\( \\sin^2 = 1 - \\cos^2 \\) で変換\n\n例: \\( \\int \\sin^2 x dx = \\int \\dfrac{1-\\cos 2x}{2} dx = \\dfrac{x}{2} - \\dfrac{\\sin 2x}{4} + C \\)\n\n■ 三角関数の置換\n- \\( \\sqrt{a^2 - x^2} \\): \\( x = a \\sin\\theta \\)\n- \\( \\sqrt{a^2 + x^2} \\): \\( x = a \\tan\\theta \\)\n- \\( \\sqrt{x^2 - a^2} \\): \\( x = a \\sec\\theta \\)",
         "table": [["技法", "用途"], ["区分求積法", "和の極限を積分に"], ["偶/奇関数", "対称区間で簡略化"], ["部分分数", "分母が積で分解可能"], ["半角公式", "\\(\\sin^n x\\) の偶数次"]]},
        {"type": "tip", "title": "ポイント: 区分求積法の標準形",
         "body": "和の形 \\( \\dfrac{1}{n}\\sum_{k=1}^{n} f(k/n) \\) を見たら、定積分 \\( \\int_0^1 f(x) dx \\) に変換。\n\n手順:\n1. 和の形を \\( \\dfrac{1}{n}\\sum f(k/n) \\) の形に整える\n2. \\( k/n \\to x \\)、\\( 1/n \\to dx \\)、和の範囲 \\( k = 1 \\to n \\) を \\( x = 0 \\to 1 \\) に\n3. 積分計算\n\n例: \\( \\lim_{n \\to \\infty} \\dfrac{1}{n}\\sum_{k=1}^n \\dfrac{1}{1+(k/n)^2} = \\int_0^1 \\dfrac{1}{1+x^2} dx = \\dfrac{\\pi}{4} \\)"},
        {"type": "warn", "title": "注意: 積分の応用で頻発するミス",
         "body": "❌ ミス1: 偶関数・奇関数の対称性を活用しない (時間ロス)。\n❌ ミス2: 部分分数分解の係数 \\( A, B \\) を誤る。代入で求める。\n❌ ミス3: 三角関数の置換で \\( dx \\) の変換を忘れる。"},
        {"type": "example", "number": 1,
         "question": "\\( \\int_{-1}^{1} (x^3 + x^2 + x + 1) dx \\) を求めよ。",
         "thought": "発想: 奇関数 \\( x^3, x \\) は積分 0、偶関数 \\( x^2, 1 \\) のみ計算。",
         "answer": "\\( \\dfrac{8}{3} \\)",
         "explanation": "\\( x^3, x \\) は奇関数 → 区間 \\([-1,1]\\) で積分は 0。\n\\( x^2, 1 \\) は偶関数 → 2 倍。\n\n\\( \\int_{-1}^1 x^3 dx + \\int_{-1}^1 x dx + \\int_{-1}^1 x^2 dx + \\int_{-1}^1 1 dx \\)\n\\( = 0 + 0 + 2\\int_0^1 x^2 dx + 2 \\int_0^1 1 dx \\)\n\\( = 2 \\cdot \\dfrac{1}{3} + 2 \\cdot 1 = \\dfrac{2}{3} + 2 = \\dfrac{8}{3} \\)"},
        {"type": "example", "number": 2,
         "question": "\\( \\lim_{n \\to \\infty} \\dfrac{1}{n}\\sum_{k=1}^n \\dfrac{k}{n} \\) を求めよ。",
         "thought": "発想: 区分求積法。\\( f(x) = x \\) として \\( \\int_0^1 x dx \\)。",
         "answer": "\\( \\dfrac{1}{2} \\)",
         "explanation": "\\( \\dfrac{1}{n}\\sum_{k=1}^n \\dfrac{k}{n} \\to \\int_0^1 x dx = \\dfrac{1}{2} \\)\n\n直接計算: \\( \\dfrac{1}{n} \\cdot \\dfrac{n(n+1)}{2n} = \\dfrac{n+1}{2n} \\to \\dfrac{1}{2} \\) も可能だが、区分求積法の方が一般的な解法。"},
        {"type": "practice", "number": 1,
         "question": "\\( \\int \\dfrac{2}{x^2 - 4} dx \\) を求めよ。"},
        {"type": "answer", "number": 1,
         "answer": "\\( \\dfrac{1}{2}\\log\\left|\\dfrac{x-2}{x+2}\\right| + C \\)",
         "explanation": "部分分数: \\( \\dfrac{2}{(x-2)(x+2)} = \\dfrac{A}{x-2} + \\dfrac{B}{x+2} \\)\n両辺に \\( (x-2)(x+2) \\) を掛けて \\( 2 = A(x+2) + B(x-2) \\)。\n\\( x = 2 \\): \\( 2 = 4A \\Rightarrow A = 1/2 \\)\n\\( x = -2 \\): \\( 2 = -4B \\Rightarrow B = -1/2 \\)\n\n\\( \\int \\dfrac{2}{x^2-4} dx = \\dfrac{1}{2}\\int \\dfrac{1}{x-2} dx - \\dfrac{1}{2}\\int \\dfrac{1}{x+2} dx = \\dfrac{1}{2}(\\log|x-2| - \\log|x+2|) + C = \\dfrac{1}{2}\\log\\left|\\dfrac{x-2}{x+2}\\right| + C \\)"},
        {"type": "summary", "heading": "まとめ — 積分の応用",
         "points": [
            "区分求積法: 和の極限 → 積分",
            "偶関数 → 対称区間で2 倍、奇関数 → 0",
            "部分分数分解で複雑な分数を分解",
            "三角関数の置換で根号を消す",
            "他単元との繋がり: 確率密度、級数、微分方程式 (大学)"
         ]}
    ]
}

AREA_VOLUME = {
    "title": "面積・体積 — 積分による幾何量の計算",
    "subtitle": "曲線で囲まれた面積・回転体の体積",
    "subject": "数学Ⅲ", "topic": "面積・体積", "level": "高校標準",
    "sections": [
        {"type": "intro", "heading": "はじめに — 面積と体積は積分の最直接的応用",
         "body": "曲線で囲まれた領域の面積、立体の体積、これらは古代から重要な問題。微積分が発明されたのも、ニュートンとライプニッツがこれらの問題を統一的に解く方法を求めた結果。"},
        {"type": "theory", "heading": "基本事項 — 面積と体積の公式",
         "body": "■ 平面内の面積\n曲線 \\( y = f(x) \\) と \\( x \\) 軸、直線 \\( x = a, x = b \\) で囲まれた面積:\n\\[ S = \\int_a^b |f(x)| dx \\]\n\n2 曲線 \\( y = f(x), y = g(x) \\) で囲まれた面積 (\\( f \\ge g \\)):\n\\[ S = \\int_a^b (f(x) - g(x)) dx \\]\n\n■ \\( y \\) について積分\n\\( x = g(y) \\) と \\( y \\) 軸の間の面積:\n\\[ S = \\int_c^d |g(y)| dy \\]\n\n■ 立体の体積 (断面積を積分)\n断面積が \\( S(x) \\) の立体の \\( x = a \\) から \\( x = b \\) までの体積:\n\\[ V = \\int_a^b S(x) dx \\]\n\n■ \\( x \\) 軸の周りの回転体\n\\( y = f(x) \\) を \\( x \\) 軸の周りに回転させた立体の体積:\n\\[ V = \\pi \\int_a^b [f(x)]^2 dx \\]\n\n■ \\( y \\) 軸の周りの回転体\n\\( x = g(y) \\) を \\( y \\) 軸の周りに回転:\n\\[ V = \\pi \\int_c^d [g(y)]^2 dy \\]\n\n■ パップス・ギュルダンの定理 (発展)\n面積 \\( A \\) の図形を、図形外の軸の周りに回転させたときの体積 = \\( 2\\pi \\bar{r} A \\) (\\( \\bar{r} \\) は重心と軸の距離)。\n\n■ 円柱状殻の方法 (シェル積分)\n\\( y = f(x) \\) を \\( y \\) 軸の周りに回転させた体積:\n\\[ V = 2\\pi \\int_a^b x f(x) dx \\]",
         "table": [["対象", "公式"], ["面積 \\(\\int|f|dx\\)", "曲線と軸"], ["2 曲線間", "\\(\\int(f-g)dx\\)"], ["\\(x\\) 軸回転", "\\(\\pi\\int f^2 dx\\)"], ["\\(y\\) 軸回転", "\\(\\pi\\int g^2 dy\\) or \\(2\\pi\\int xf dx\\)"]]},
        {"type": "tip", "title": "ポイント: 回転軸を確認",
         "body": "回転体の体積を求めるとき、まず「どの軸の周りに回転するか」を確認:\n\n- \\( x \\) 軸周り: \\( V = \\pi \\int [f(x)]^2 dx \\) (\\( f(x) \\) を半径として)\n- \\( y \\) 軸周り: 関数を \\( x = g(y) \\) の形に直して \\( V = \\pi \\int [g(y)]^2 dy \\)、または シェル積分 \\( V = 2\\pi \\int x f(x) dx \\)\n\n選択基準: \\( y \\) 軸周りで \\( f(x) \\) を \\( g(y) \\) に変換しにくい場合はシェル積分。"},
        {"type": "warn", "title": "注意: 面積・体積で頻発するミス",
         "body": "❌ ミス1: 面積を負の値で答える。絶対値または \"上 − 下\" で常に非負に。\n❌ ミス2: 回転体で \\( \\pi \\) を忘れる。\n❌ ミス3: \\( y \\) 軸回転で関数を変換せず \\( x \\) のまま積分。\n❌ ミス4: 交点を間違えて積分範囲を誤る。"},
        {"type": "example", "number": 1,
         "question": "曲線 \\( y = x^2 \\) と直線 \\( y = 4 \\) で囲まれた図形の面積を求めよ。",
         "thought": "発想: 交点 \\( x^2 = 4 \\Rightarrow x = \\pm 2 \\)。区間 \\([-2, 2]\\) で \\( y = 4 \\) が上、\\( y = x^2 \\) が下。",
         "answer": "\\( \\dfrac{32}{3} \\)",
         "explanation": "面積 = \\( \\int_{-2}^{2} (4 - x^2) dx \\) (上 − 下)\n\n偶関数なので 2 倍:\n\\( = 2 \\int_0^2 (4 - x^2) dx = 2 [4x - x^3/3]_0^2 = 2(8 - 8/3) = 2 \\cdot 16/3 = 32/3 \\)"},
        {"type": "example", "number": 2,
         "question": "\\( y = \\sqrt{x} \\) (\\( 0 \\le x \\le 4 \\)) を \\( x \\) 軸周りに回転させてできる立体の体積を求めよ。",
         "thought": "発想: \\( V = \\pi \\int [f(x)]^2 dx = \\pi \\int_0^4 x dx \\)。",
         "answer": "\\( 8\\pi \\)",
         "explanation": "\\[ V = \\pi \\int_0^4 (\\sqrt{x})^2 dx = \\pi \\int_0^4 x dx = \\pi [x^2/2]_0^4 = \\pi \\cdot 8 = 8\\pi \\]"},
        {"type": "practice", "number": 1,
         "question": "曲線 \\( y = \\sin x \\) (\\( 0 \\le x \\le \\pi \\)) と \\( x \\) 軸で囲まれた図形を \\( x \\) 軸周りに回転させた体積を求めよ。"},
        {"type": "answer", "number": 1,
         "answer": "\\( \\dfrac{\\pi^2}{2} \\)",
         "explanation": "\\( V = \\pi \\int_0^\\pi \\sin^2 x dx \\)\n\n半角公式: \\( \\sin^2 x = (1 - \\cos 2x)/2 \\)\n\n\\( V = \\pi \\int_0^\\pi \\dfrac{1 - \\cos 2x}{2} dx = \\dfrac{\\pi}{2} [x - \\sin 2x / 2]_0^\\pi = \\dfrac{\\pi}{2}(\\pi - 0) = \\dfrac{\\pi^2}{2} \\)"},
        {"type": "summary", "heading": "まとめ — 面積・体積",
         "points": [
            "面積 = \\(\\int |f| dx\\) または \\(\\int (上-下) dx\\)",
            "回転体は軸を確認: \\(x\\) 軸周り \\(\\pi\\int f^2 dx\\)、\\(y\\) 軸周り \\(\\pi\\int g^2 dy\\)",
            "断面積が分かる立体は \\(\\int S(x) dx\\)",
            "シェル積分は \\(y\\) 軸周りで関数変換が困難な場合に有効",
            "他単元との繋がり: 微分積分学の基本定理、媒介変数 (本書)"
         ]}
    ]
}

PARAMETRIC = {
    "title": "媒介変数表示 — \\( x = f(t), y = g(t) \\) で曲線を描く",
    "subtitle": "サイクロイド・楕円・リサージュ図形",
    "subject": "数学Ⅲ", "topic": "媒介変数表示", "level": "高校標準",
    "sections": [
        {"type": "intro", "heading": "はじめに — 媒介変数は曲線の自然な表現",
         "body": "円を \\( y = f(x) \\) の形で書こうとすると \\( y = \\pm\\sqrt{1-x^2} \\) と2 つの式が必要。媒介変数なら \\( x = \\cos t, y = \\sin t \\) (\\( 0 \\le t \\le 2\\pi \\)) と1 組で表現できる。\n\n比喩を一つ。媒介変数は「動画」、\\( y = f(x) \\) は「写真」。動画では時間 \\( t \\) と共に位置 \\( (x, y) \\) が動く。"},
        {"type": "theory", "heading": "基本事項 — 媒介変数表示と計算",
         "body": "■ 媒介変数の例\n- 円: \\( x = r\\cos t, y = r\\sin t \\) (\\( 0 \\le t \\le 2\\pi \\))\n- 楕円: \\( x = a\\cos t, y = b\\sin t \\)\n- サイクロイド: \\( x = a(t - \\sin t), y = a(1 - \\cos t) \\) (車輪が転がるとき固定点が描く軌跡)\n- リサージュ: \\( x = \\sin(at), y = \\sin(bt + \\phi) \\)\n\n■ 媒介変数表示の微分\n\\[ \\dfrac{dy}{dx} = \\dfrac{dy/dt}{dx/dt} = \\dfrac{g'(t)}{f'(t)} \\]\n\n例: \\( x = t^2, y = t^3 \\) → \\( dy/dx = 3t^2 / 2t = 3t/2 \\)\n\n■ 媒介変数表示の面積\n\\( x = f(t), y = g(t) \\) (\\( t = \\alpha \\to \\beta \\)) の曲線と \\( x \\) 軸で囲まれた面積:\n\\[ S = \\int_\\alpha^\\beta |g(t)| f'(t) dt \\]\n\n例: 円の面積\n\\( x = r\\cos t, y = r\\sin t \\) (\\( t = 0 \\to \\pi \\) で上半円)\n\\( S = 2 \\int_0^\\pi r\\sin t \\cdot r(-\\sin t) dt = -2r^2 \\int_0^\\pi \\sin^2 t dt = -r^2[t - \\sin t \\cos t]_0^\\pi = -r^2 \\pi \\)\nが負になるのは積分方向の問題。絶対値を取ると \\( \\pi r^2 \\)。\n\n■ 第2 次導関数\n\\[ \\dfrac{d^2 y}{dx^2} = \\dfrac{d}{dx}\\left(\\dfrac{dy}{dx}\\right) = \\dfrac{1}{dx/dt}\\dfrac{d}{dt}\\left(\\dfrac{dy}{dx}\\right) \\]",
         "table": [["曲線", "媒介変数"], ["円", "\\(\\cos t, \\sin t\\)"], ["楕円", "\\(a\\cos t, b\\sin t\\)"], ["サイクロイド", "\\(a(t-\\sin t), a(1-\\cos t)\\)"]]},
        {"type": "tip", "title": "ポイント: 媒介変数 → \\( y = f(x) \\) の変換",
         "body": "媒介変数表示から \\( y \\) を \\( x \\) の式で書きたいとき:\n1. \\( t \\) を \\( x \\) で表す (\\( x = f(t) \\) を逆解き)\n2. \\( y = g(t) \\) に代入\n\n例: \\( x = 2t + 1, y = t^2 \\)\n\\( t = (x-1)/2 \\) → \\( y = ((x-1)/2)^2 = (x-1)^2/4 \\)\n\nただし、複雑な媒介変数では逆解きが困難。その場合は媒介変数のまま計算する方が良い。"},
        {"type": "warn", "title": "注意: 媒介変数で頻発するミス",
         "body": "❌ ミス1: \\( dy/dx \\) を \\( dy/dt \\) と勘違い。\n\\( dy/dx = (dy/dt) / (dx/dt) \\)。\n\n❌ ミス2: 媒介変数の範囲を確認しない。\n例: 円は \\( 0 \\le t \\le 2\\pi \\) で1 周。範囲を間違えると別の曲線。"},
        {"type": "example", "number": 1,
         "question": "\\( x = t^2, y = t^3 \\) のとき \\( dy/dx \\) を求めよ。",
         "thought": "発想: \\( dy/dx = (dy/dt)/(dx/dt) \\)。",
         "answer": "\\( \\dfrac{dy}{dx} = \\dfrac{3t}{2} \\)",
         "explanation": "\\( dx/dt = 2t \\), \\( dy/dt = 3t^2 \\)\n\\( dy/dx = 3t^2 / 2t = 3t/2 \\) (\\( t \\ne 0 \\))"},
        {"type": "example", "number": 2,
         "question": "サイクロイド \\( x = t - \\sin t, y = 1 - \\cos t \\) (\\( 0 \\le t \\le 2\\pi \\)) と \\( x \\) 軸で囲まれた面積を求めよ。",
         "thought": "発想: \\( S = \\int y \\cdot dx/dt \\, dt \\) を計算。",
         "answer": "\\( 3\\pi \\)",
         "explanation": "\\( dx/dt = 1 - \\cos t \\)\n\n\\[ S = \\int_0^{2\\pi} y \\cdot \\dfrac{dx}{dt} dt = \\int_0^{2\\pi} (1-\\cos t)(1-\\cos t) dt = \\int_0^{2\\pi} (1-\\cos t)^2 dt \\]\n\n展開: \\( (1-\\cos t)^2 = 1 - 2\\cos t + \\cos^2 t = 1 - 2\\cos t + (1+\\cos 2t)/2 = 3/2 - 2\\cos t + \\cos 2t / 2 \\)\n\n積分:\n\\( \\int_0^{2\\pi} (3/2) dt = 3\\pi \\)\n\\( \\int_0^{2\\pi} -2\\cos t dt = 0 \\)\n\\( \\int_0^{2\\pi} \\cos 2t / 2 dt = 0 \\)\n\nよって \\( S = 3\\pi \\)。"},
        {"type": "practice", "number": 1,
         "question": "\\( x = \\cos t, y = \\sin t \\) で \\( dy/dx \\) を求めよ。"},
        {"type": "answer", "number": 1,
         "answer": "\\( \\dfrac{dy}{dx} = -\\cot t = -\\dfrac{\\cos t}{\\sin t} \\)",
         "explanation": "\\( dx/dt = -\\sin t \\), \\( dy/dt = \\cos t \\)\n\\( dy/dx = \\cos t / (-\\sin t) = -\\cot t \\)\n\nこれは円 \\( x^2 + y^2 = 1 \\) の任意の点 \\( (\\cos t, \\sin t) \\) における接線の傾き。"},
        {"type": "summary", "heading": "まとめ — 媒介変数表示",
         "points": [
            "媒介変数は曲線を時間的に表現 (動画的)",
            "微分は \\(dy/dx = (dy/dt)/(dx/dt)\\)",
            "面積は \\(\\int g(t) f'(t) dt\\) (符号注意)",
            "代表曲線: 円・楕円・サイクロイド・リサージュ",
            "他単元との繋がり: 曲線の長さ (本書)、極座標"
         ]}
    ]
}

CURVE_LENGTH = {
    "title": "曲線の長さ — 微小要素を積分",
    "subtitle": "\\( y = f(x) \\)・媒介変数・極座標表示の弧長",
    "subject": "数学Ⅲ", "topic": "曲線の長さ", "level": "高校標準",
    "sections": [
        {"type": "intro", "heading": "はじめに — 曲線の長さ = 微小直線の和の極限",
         "body": "曲線の長さは「微小な直線部分 \\( ds \\) の和」として計算できる。これが弧長公式の本質。\n\n比喩を一つ。曲線の長さは「道路の総距離」。曲がっている道でも、無限に細かく直線に近似すれば、その合計が距離。"},
        {"type": "theory", "heading": "基本事項 — 弧長公式",
         "body": "■ \\( y = f(x) \\) の弧長 (\\( a \\le x \\le b \\))\n\\[ L = \\int_a^b \\sqrt{1 + (f'(x))^2} dx \\]\n\n導出: 微小要素 \\( ds = \\sqrt{(dx)^2 + (dy)^2} = \\sqrt{1 + (dy/dx)^2} dx \\)\n\n■ 媒介変数 \\( x = f(t), y = g(t) \\) の弧長 (\\( \\alpha \\le t \\le \\beta \\))\n\\[ L = \\int_\\alpha^\\beta \\sqrt{(f'(t))^2 + (g'(t))^2} dt \\]\n\n■ 極座標 \\( r = f(\\theta) \\) の弧長 (\\( \\alpha \\le \\theta \\le \\beta \\))\n\\[ L = \\int_\\alpha^\\beta \\sqrt{r^2 + (dr/d\\theta)^2} d\\theta \\]\n\n■ 微小要素の覚え方\n\\[ ds^2 = dx^2 + dy^2 \\] (ピタゴラスの定理)\n\nこれをパラメタで書き直すと:\n- 直交座標: \\( ds = \\sqrt{1 + (dy/dx)^2} dx \\)\n- 媒介変数: \\( ds = \\sqrt{(dx/dt)^2 + (dy/dt)^2} dt \\)\n- 極座標: \\( ds = \\sqrt{r^2 + (dr/d\\theta)^2} d\\theta \\)\n\n■ 円周の長さ\n半径 \\( r \\) の円: \\( x = r\\cos t, y = r\\sin t \\) (\\( 0 \\le t \\le 2\\pi \\))\n\\( dx/dt = -r\\sin t, dy/dt = r\\cos t \\)\n\\( L = \\int_0^{2\\pi} \\sqrt{r^2 \\sin^2 t + r^2 \\cos^2 t} dt = \\int_0^{2\\pi} r \\, dt = 2\\pi r \\) ✓",
         "table": [["表現", "弧長公式"], ["\\(y=f(x)\\)", "\\(\\int\\sqrt{1+f'^2}dx\\)"], ["媒介変数", "\\(\\int\\sqrt{f'^2+g'^2}dt\\)"], ["極座標", "\\(\\int\\sqrt{r^2+(dr/d\\theta)^2}d\\theta\\)"]]},
        {"type": "tip", "title": "ポイント: 弧長計算は積分が複雑になりがち",
         "body": "弧長公式の被積分関数は \\( \\sqrt{...} \\) を含むため、積分が複雑になりがち。受験では「特殊な形」しか出題されない:\n\n1. \\( 1 + f'^2 \\) が完全平方の形\n2. 円・楕円のような幾何学的に有名な曲線\n3. 部分積分や置換でうまく解ける形\n\n練習で典型問題に慣れる。"},
        {"type": "warn", "title": "注意: 曲線の長さで頻発するミス",
         "body": "❌ ミス1: 公式の \\(\\sqrt{1 + f'^2}\\) の \"1\" を忘れる。\n❌ ミス2: 媒介変数で \\(dt\\) を忘れる。\n❌ ミス3: 極座標公式の \\(r^2\\) を \\((r')^2\\) と書く。"},
        {"type": "example", "number": 1,
         "question": "曲線 \\( y = x^{3/2} \\) の \\( x = 0 \\) から \\( x = 4 \\) までの長さを求めよ。",
         "thought": "発想: 弧長公式 \\( L = \\int \\sqrt{1 + (y')^2} dx \\)。\\( y' = (3/2)x^{1/2} \\)。",
         "answer": "\\( L = \\dfrac{8}{27}(10\\sqrt{10} - 1) \\)",
         "explanation": "\\( y' = (3/2) x^{1/2} \\), \\( (y')^2 = (9/4) x \\)\n\\( 1 + (y')^2 = 1 + (9/4)x = (4 + 9x)/4 \\)\n\\( \\sqrt{1 + (y')^2} = \\sqrt{4 + 9x}/2 \\)\n\n\\( L = \\int_0^4 \\dfrac{\\sqrt{4 + 9x}}{2} dx \\)\n\n\\( u = 4 + 9x \\), \\( du = 9 dx \\), \\( dx = du/9 \\)\n\\( x = 0 \\to u = 4, x = 4 \\to u = 40 \\)\n\\( L = \\int_4^{40} \\dfrac{\\sqrt{u}}{2} \\cdot \\dfrac{du}{9} = \\dfrac{1}{18} \\int_4^{40} u^{1/2} du = \\dfrac{1}{18} \\cdot \\dfrac{2}{3} [u^{3/2}]_4^{40} = \\dfrac{1}{27}(40^{3/2} - 8) \\)\n\\( 40^{3/2} = 40\\sqrt{40} = 80\\sqrt{10} \\), \\( 8 = 8 \\)\n\\( L = (80\\sqrt{10} - 8)/27 = 8(10\\sqrt{10} - 1)/27 \\)"},
        {"type": "example", "number": 2,
         "question": "サイクロイド \\( x = 1 - \\cos t, y = t - \\sin t \\) (\\( 0 \\le t \\le 2\\pi \\)) の長さを求めよ。",
         "thought": "発想: 媒介変数の弧長公式。\\( dx/dt, dy/dt \\) を計算。",
         "answer": "8",
         "explanation": "\\( dx/dt = \\sin t \\), \\( dy/dt = 1 - \\cos t \\)\n\\( (dx/dt)^2 + (dy/dt)^2 = \\sin^2 t + (1 - \\cos t)^2 = \\sin^2 t + 1 - 2\\cos t + \\cos^2 t = 2 - 2\\cos t = 2(1 - \\cos t) \\)\n\n半角公式: \\( 1 - \\cos t = 2\\sin^2(t/2) \\)\n\\( (dx/dt)^2 + (dy/dt)^2 = 4\\sin^2(t/2) \\)\n\\( \\sqrt{...} = 2|\\sin(t/2)| = 2\\sin(t/2) \\) (\\( 0 \\le t \\le 2\\pi \\) なので \\( \\sin(t/2) \\ge 0 \\))\n\n\\( L = \\int_0^{2\\pi} 2\\sin(t/2) dt = 2[-2\\cos(t/2)]_0^{2\\pi} = -4[\\cos\\pi - \\cos 0] = -4(-1 - 1) = 8 \\)"},
        {"type": "practice", "number": 1,
         "question": "半径 1 の円の周の長さを弧長公式で求めよ。"},
        {"type": "answer", "number": 1,
         "answer": "\\( 2\\pi \\)",
         "explanation": "媒介変数: \\( x = \\cos t, y = \\sin t \\) (\\( 0 \\le t \\le 2\\pi \\))\n\\( dx/dt = -\\sin t, dy/dt = \\cos t \\)\n\\( (dx/dt)^2 + (dy/dt)^2 = \\sin^2 t + \\cos^2 t = 1 \\)\n\\( L = \\int_0^{2\\pi} 1 dt = 2\\pi \\) ✓"},
        {"type": "summary", "heading": "まとめ — 曲線の長さ",
         "points": [
            "弧長は微小要素 \\(ds\\) の積分",
            "\\(y = f(x)\\): \\(\\int\\sqrt{1+f'^2}dx\\)",
            "媒介変数: \\(\\int\\sqrt{(dx/dt)^2+(dy/dt)^2}dt\\)",
            "極座標: \\(\\int\\sqrt{r^2+(dr/d\\theta)^2}d\\theta\\)",
            "他単元との繋がり: 媒介変数 (本書)、回転体 (本書)"
         ]}
    ]
}

VOL_ROTATION = {
    "title": "回転体の体積 — \\( \\pi \\int f^2 dx \\) の応用",
    "subtitle": "\\( x \\) 軸・\\( y \\) 軸・任意軸周りの回転体",
    "subject": "数学Ⅲ", "topic": "回転体の体積", "level": "高校標準",
    "sections": [
        {"type": "intro", "heading": "はじめに — 回転体の体積は数III積分の頂点",
         "body": "曲線を回転させて立体を作る。これが回転体。日常的にも、ガラスのコップ・ペットボトル・球など、回転対称な物体は自然界に多い。"},
        {"type": "theory", "heading": "基本事項 — 回転体の公式",
         "body": "■ \\( x \\) 軸周りの回転\n\\( y = f(x) \\) (\\( a \\le x \\le b \\)) を \\( x \\) 軸周りに回転:\n\\[ V = \\pi \\int_a^b [f(x)]^2 dx \\]\n\n■ \\( y \\) 軸周りの回転\n\\( x = g(y) \\) (\\( c \\le y \\le d \\)) を \\( y \\) 軸周りに回転:\n\\[ V = \\pi \\int_c^d [g(y)]^2 dy \\]\n\n■ シェル法 (バウムクーヘン積分)\n\\( y = f(x) \\) (\\( a \\le x \\le b \\)) を \\( y \\) 軸周りに回転 (\\( a \\ge 0 \\) 前提):\n\\[ V = 2\\pi \\int_a^b x f(x) dx \\]\n\n■ 2 曲線間の回転体 (中空構造)\n\\( y = f(x), y = g(x) \\) (\\( f \\ge g \\ge 0 \\)) で囲まれた領域を \\( x \\) 軸周り回転:\n\\[ V = \\pi \\int_a^b ([f(x)]^2 - [g(x)]^2) dx \\]\n\n■ 任意の軸周り (発展)\n軸が \\( y = mx + c \\) など斜めの場合は、座標変換または線分の距離公式で対応。\n\n■ 球の体積 (公式の導出)\n半円 \\( y = \\sqrt{r^2 - x^2} \\) (\\( -r \\le x \\le r \\)) を \\( x \\) 軸周り回転:\n\\[ V = \\pi \\int_{-r}^{r} (r^2 - x^2) dx = \\pi[r^2 x - x^3/3]_{-r}^{r} = \\pi(2r^3 - 2r^3/3) = \\dfrac{4\\pi r^3}{3} \\] ✓",
         "table": [["回転軸", "公式"], ["\\(x\\) 軸 (\\(y=f(x)\\))", "\\(\\pi\\int f^2 dx\\)"], ["\\(y\\) 軸 (\\(x=g(y)\\))", "\\(\\pi\\int g^2 dy\\)"], ["シェル法 (\\(y\\) 軸)", "\\(2\\pi\\int xf dx\\)"], ["中空", "\\(\\pi\\int (f^2-g^2) dx\\)"]]},
        {"type": "tip", "title": "ポイント: 中空構造の見抜き方",
         "body": "回転対象の領域が \"内側に空洞\" を持つ場合、外径 \\( f \\) と内径 \\( g \\) で:\n\\[ V = \\pi \\int (外^2 - 内^2) dx \\]\n\n例: \\( y = x \\) と \\( y = x^2 \\) (\\( 0 \\le x \\le 1 \\)) で囲まれた領域を \\( x \\) 軸周り回転。\n\\( x \\) は外側 (\\( x \\ge x^2 \\) なので)、\\( x^2 \\) は内側。\n\\( V = \\pi \\int_0^1 (x^2 - x^4) dx = \\pi[x^3/3 - x^5/5]_0^1 = \\pi(1/3 - 1/5) = 2\\pi/15 \\)"},
        {"type": "warn", "title": "注意: 回転体の体積で頻発するミス",
         "body": "❌ ミス1: \\( \\pi \\) を忘れる。\n❌ ミス2: 中空の場合に \\( (外 - 内)^2 \\) と書く。正しくは \\( 外^2 - 内^2 \\)。\n❌ ミス3: \\( y \\) 軸回転で関数を \\( x = g(y) \\) に変換せず \\( x \\) のまま積分。\n❌ ミス4: シェル法で \\( 2\\pi \\) を忘れる (シェル法は2 πx)。"},
        {"type": "example", "number": 1,
         "question": "\\( y = x^2 \\) (\\( 0 \\le x \\le 1 \\)) を \\( x \\) 軸周りに回転させた立体の体積を求めよ。",
         "thought": "発想: \\( V = \\pi \\int [f(x)]^2 dx = \\pi \\int x^4 dx \\)。",
         "answer": "\\( \\dfrac{\\pi}{5} \\)",
         "explanation": "\\[ V = \\pi \\int_0^1 (x^2)^2 dx = \\pi \\int_0^1 x^4 dx = \\pi [x^5/5]_0^1 = \\dfrac{\\pi}{5} \\]"},
        {"type": "example", "number": 2,
         "question": "\\( y = \\sqrt{x} \\), \\( y = x \\) で囲まれた領域を \\( x \\) 軸周りに回転させた体積を求めよ。",
         "thought": "発想: 交点 \\( \\sqrt{x} = x \\Rightarrow x = 0, 1 \\)。区間 \\([0,1]\\) で \\( \\sqrt{x} \\ge x \\) (外径 √x、内径 x)。中空の体積。",
         "answer": "\\( \\dfrac{\\pi}{6} \\)",
         "explanation": "区間 \\( 0 \\le x \\le 1 \\) で \\( \\sqrt{x} \\ge x \\) (確認: \\( x = 0.25 \\) で \\( \\sqrt{0.25} = 0.5 \\), \\( x = 0.25 \\), \\( 0.5 > 0.25 \\))。\n\n\\[ V = \\pi \\int_0^1 ((\\sqrt{x})^2 - x^2) dx = \\pi \\int_0^1 (x - x^2) dx = \\pi [x^2/2 - x^3/3]_0^1 = \\pi(1/2 - 1/3) = \\dfrac{\\pi}{6} \\]"},
        {"type": "practice", "number": 1,
         "question": "半径 \\( r \\) の円を \\( y \\) 軸周りに回転させた立体 (=球) の体積を、シェル法で求めよ。"},
        {"type": "answer", "number": 1,
         "answer": "\\( \\dfrac{4\\pi r^3}{3} \\)",
         "explanation": "上半円 \\( y = \\sqrt{r^2 - x^2} \\) (\\( 0 \\le x \\le r \\)) を \\( y \\) 軸周りに回転させると、上半球。\n\nシェル法:\n\\[ V_{上半球} = 2\\pi \\int_0^r x \\sqrt{r^2 - x^2} dx \\]\n置換: \\( u = r^2 - x^2 \\), \\( du = -2x dx \\), \\( x dx = -du/2 \\)\n\\( x = 0 \\to u = r^2, x = r \\to u = 0 \\)\n\\[ = 2\\pi \\int_{r^2}^{0} \\sqrt{u} \\cdot (-1/2) du = \\pi \\int_0^{r^2} u^{1/2} du = \\pi [2u^{3/2}/3]_0^{r^2} = \\dfrac{2\\pi r^3}{3} \\]\n\n球全体は上半球の2 倍: \\( V = \\dfrac{4\\pi r^3}{3} \\) ✓"},
        {"type": "summary", "heading": "まとめ — 回転体の体積",
         "points": [
            "\\(x\\) 軸周り: \\(V = \\pi \\int f^2 dx\\)",
            "\\(y\\) 軸周り (関数 \\(x = g(y)\\) に変換): \\(V = \\pi \\int g^2 dy\\)",
            "シェル法 (\\(y\\) 軸周り、\\(y = f(x)\\) のまま): \\(V = 2\\pi \\int x f(x) dx\\)",
            "中空構造: \\(V = \\pi \\int (外^2 - 内^2) dx\\)",
            "球の体積 \\(4\\pi r^3 / 3\\) は半円の回転で導出可能",
            "他単元との繋がり: 微積分学の応用、立体幾何"
         ]}
    ]
}


def make_textbook_entry(content_dict, length="medium", ttype="unit_lesson", tags=None):
    return {
        "subject": content_dict["subject"], "topic": content_dict["topic"], "level": content_dict["level"],
        "length": length, "type": ttype, "title": content_dict["title"],
        "tags": tags or [], "content": content_dict,
        "status": "published", "source": "claude_max_seed_batch12",
    }

textbooks = [
    make_textbook_entry(INT_APP, tags=["積分応用", "区分求積法", "偶奇関数", "部分分数"]),
    make_textbook_entry(AREA_VOLUME, tags=["面積", "体積", "回転体", "断面積"]),
    make_textbook_entry(PARAMETRIC, tags=["媒介変数", "サイクロイド", "楕円", "リサージュ"]),
    make_textbook_entry(CURVE_LENGTH, tags=["曲線の長さ", "弧長", "媒介変数", "極座標"]),
    make_textbook_entry(VOL_ROTATION, tags=["回転体", "体積", "シェル法", "中空構造"]),
]

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump({"textbooks": textbooks}, f, ensure_ascii=False, indent=2)

print(f"✅ 書き出し完了: {OUTPUT}")
print(f"   教材数: {len(textbooks)}")
for t in textbooks:
    print(f"   - {t['subject']} / {t['topic']} ({len(t['content']['sections'])} sections)")
