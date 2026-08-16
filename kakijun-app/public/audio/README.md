# 音声ファイルの差し替え方法 (§8.2)

このフォルダに mp3 を置くと、アプリは **録音音声を優先** して再生します。
ファイルが無い間は SpeechSynthesis（端末の読み上げ）で代替します。
アプリ本体の変更は不要です。置いて再ビルドするだけで切り替わります。

## ファイル名の規約

| パス | 内容 | 例 |
|---|---|---|
| `char/<id>.mp3` | 文字の読み上げ | `char/hira_a.mp3` = 「あ」 |
| `words/<name>.mp3` | 絵カードの語 (`sample.audio` の値) | `words/ari.mp3` = 「あり」 |
| `guide/stroke_N.mp3` | 「いっかくめ」「つぎは にかくめ」 | `guide/stroke_1.mp3` |
| `guide/next_is_N.mp3` | 「つぎは ◯かくめだよ」(書き順違い) | `guide/next_is_2.mp3` |
| `guide/start_here.mp3` | 「ここから はじめてね」 | |
| `guide/on_line.mp3` | 「せんの うえを なぞろうね」 | |
| `guide/this_way.mp3` | 「こっちむきだよ」 | |
| `guide/to_end.mp3` | 「さいごまで なぞろうね」 | |
| `guide/together.mp3` | 「いっしょに やってみよう」 | |
| `praise/praise_01.mp3` 〜 `praise_09.mp3` | 称賛 (文言は `src/audio/voiceLines.ts`) | |
| `retry/retry_01.mp3` 〜 `retry_06.mp3` | やり直しの促し (同上) | |

- 録音は **やさしい女性/男性の声・ゆっくりめ** を推奨。
- 「ちがう」「まちがい」「だめ」という語は使わないこと (§7.4)。
