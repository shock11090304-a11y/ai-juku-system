# AI学習コーチ塾 — SNS販促素材キット

すべて製品投入可能な状態。コピペ/ドラッグ&ドロップで即使用可能です。

## 📂 ファイル一覧

| ファイル | 用途 |
|---|---|
| `ig-slide-1.png` 〜 `ig-slide-5.png` | **Instagramカルーセル投稿用**（1080×1080 / 5枚組） |
| `threads-posts.txt` | **Threads投稿文** 5バリエーション + 投稿スケジュール |
| `reels-60sec-script.txt` | **Reels 60秒動画** 台本2パターン（顔出し/アプリ画面） |
| `generate_ig_slides.py` | Instagram画像を再生成するPythonスクリプト（塾名変更時用）|

---

## 🚀 使い方(Instagram投稿)

### カルーセル画像投稿

1. Instagramアプリ → 「+」 → 投稿
2. `ig-slide-1.png` から順番に5枚全て選択
3. キャプションは `sns-launch-kit.html` または `influencer-campaign.html` からコピー
4. 位置情報: 任意（つけると地域からの流入が増える）
5. 投稿

### Reels動画

1. `reels-60sec-script.txt` の台本に従って撮影
2. CapCut/VLLOなどで編集(推奨アプリは台本末尾に記載)
3. 60秒を超えないように編集
4. Instagram → Reels作成 → アップロード

---

## 🧵 Threads投稿

1. Threadsアプリまたは `threads.net` を開く
2. `threads-posts.txt` から好きな投稿をコピー
3. スレッド開始 → ペースト → 投稿

---

## 🔄 画像の再生成

塾名や価格が変わったら:

```bash
cd marketing-assets
# generate_ig_slides.py を編集
python3 generate_ig_slides.py
```

一瞬で全5枚が再生成されます。

---

## 📅 1週間の最適スケジュール

```
【月曜】
 朝8時   Threads: 共感型投稿(①)
 夜9時   Instagram: カルーセル(5枚)+キャプション

【火曜】
 朝8時   Threads: 比較型(④)
 夜8時   Instagram Reels: 60秒動画公開

【水曜】 朝8時   Threads: 数字訴求(②)
【木曜】 朝8時   Threads: ストーリー(③)
【金曜】 朝8時   Threads: 保護者向け(⑤)
【土日】 反応が良かった投稿をブースト(広告)
```

---

## 🎯 初週の目標KPI

- Threads 各投稿 1,000インプレッション以上
- Instagram フォロワー +100名
- LP(`trillion-ai-juku.com/lp.html`) 訪問 50名
- 体験トライアル申込 3〜5名

超えたら販売加速のためにインフルエンサー起用検討。
