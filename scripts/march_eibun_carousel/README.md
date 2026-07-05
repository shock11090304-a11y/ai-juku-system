# MARCH英文カルーセル (Instagram / @trillion_ai)

「MARCHの英文はこう読む」シリーズの画像ジェネレータ。
`東大・京大の英文はこう読む vol.01`(京大2023・as の識別)と同じデザインを踏襲する。

## vol.02 = 「この but、訳せる?」(nothing to do but ~)
実際の入試長文(**Linda Sue Park『A Long Walk to Water』(2010)** を出典とする難関私大の
長文空所補充問題)から、空所 `There was nothing to do [　] wait.` の答え **but** を題材にした6枚組。
「but=しかし」ではなく「but=〜を除いて(except)」→ `nothing to do but V`=「Vするしかない」という
MARCH・共通テスト・英検頻出の識別ポイントを解説する。

## 生成
```bash
python3 build.py          # out/march_01.png ... march_06.png (2160x2700, 4:5)
```
- HTML を組み、ヘッドレス Chromium(`--force-device-scale-factor=2`)で 1080x1350 → 2x PNG に描画。
- フォント: 見出し・和文 = Noto Sans CJK JP / 英文引用 = Liberation Serif(Times系)。
  ローカルに無ければ `apt-get install -y fonts-noto-cjk poppler-utils` を先に実行。

## 構成(6枚)
1. フック: “There was nothing to do but wait.” → 「この but、訳せる?」
2. 設問: この but をどう訳す?(A 珍訳「しかし、待った」/ B 正解「ただ待つしかなかった」)
3. 解答: 正解 **B**。but を「しかし」と読むと珍訳に。
4. 公式: `nothing to do but V`=「Vするしかない」/ この but = except(〜を除いて)。+ 英文出典。
5. but の仲間: have no choice but to do / anything but / all but。
6. 全訳・まとめ + 保存/フォロー CTA + 次回予告(as)。

## 出典表記について
- 英文出典(`A Long Walk to Water`, 2010)は問題冊子に明記されており、そのまま表記。
- **大学名・年度は問題冊子に印字が無く未確定**のため、確認でき次第 `build.py` の `SOURCE` に
  「〇〇大学 20XX年」を追記する(現状は「難関私大」表記)。
- 別の英文・文法ポイントに差し替える場合は、`build.py` の `SLIDES[1..6]`・`SOURCE` を編集して再生成。

## 投稿キャプション例
> 【MARCHの英文はこう読む vol.02】
> "There was nothing to do but wait."
> ―― この "but"、正しく訳せますか?
> 「しかし」と読むと沈みます。カギは "nothing to do but V"。
> 👉 答えはA?B? コメントで教えてください!
> 保存して復習 / フォローで次の1文 → @trillion_ai
> (英文出典: Linda Sue Park, A Long Walk to Water, 2010)
> #大学受験 #英文法 #MARCH #英語構文 #共通テスト #英検 #but
