# MARCH英文カルーセル (Instagram / @trillion_ai)

「MARCHの英文はこう読む」シリーズの画像ジェネレータ。
`東大・京大の英文はこう読む vol.01`(京大2023・as の識別)と同じデザインを踏襲し、
**vol.02 = クジラ構文 `no more A than B`** を題材にした6枚組を生成する。

## 生成
```bash
python3 build.py          # out/march_01.png ... march_06.png (2160x2700, 4:5)
```
- HTML を組み、ヘッドレス Chromium(`--force-device-scale-factor=2`)で 1080x1350 → 2x PNG に描画。
- フォント: 見出し・和文 = Noto Sans CJK JP / 英文引用 = Liberation Serif(Times系)。
  ローカルに無い場合は `apt-get install -y fonts-noto-cjk` を先に実行。

## 構成(6枚)
1. フック: 英文引用 “A whale is no more a fish than a horse is.” → 「訳せる？」
2. 設問: この `no more…than` はどう訳す?(A 珍訳 / B 正解 の二択)
3. 解答: 正解は **B**(両者否定)。A で読むと珍訳に。
4. 公式: `no more A than B` = 「B でないのと同様に A でない」/ `no less` との対比。
5. 注意点: “比較の more” と誤読するな(no が付いたら比べていない)。
6. 全訳・まとめ + 保存/フォロー CTA + 次回予告。

## 出典表記について
vol.01 は実在の「京都大学 2023 第2問」を引用しているが、本 vol.02 は特定の MARCH 過去問を
断定できないため、出典は捏造せず **「テーマ: クジラ構文・難関大頻出」** と正直に表記している。
実在の特定過去問(例: 明治/立教等の下線部和訳)が手元にあれば、`build.py` の英文・和訳・
`SOURCE` を差し替えるだけで同デザインのまま再生成できる。

## 投稿キャプション例
> 【MARCHの英文はこう読む vol.02】
> "A whale is no more a fish than a horse is."
> ―― この一文、正しく訳せますか?
> 事故ポイントは "no more A than B"(クジラ構文)ただ1つ。
> 👉 答えはA?B? コメントで教えてください!
> 保存して復習 / フォローで次の1文 → @trillion_ai
> #大学受験 #英文法 #MARCH #英語構文 #クジラ構文 #共通テスト #英検
