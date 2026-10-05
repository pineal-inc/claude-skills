# pineal スライド制作キット（公開版）

株式会社ピネアルのスライドを作る作業環境。HTML を内容の正本にし、PDF と編集可能な PPTX を出す。
このファイルがあるフォルダを「キット」と呼ぶ。

## 読むもの

- 作る・直す
  - スキル `pineal-slide`（実体は `tool-pineal-slide-v2/.claude/skills/pineal-slide/SKILL.md`）
- PPTX にする
  - 同スキルの `references/pptx-v3.md`
  - v3 のテンプレ・スクリプト・参照はキット直下の `pineal-slide-v3/`
- 図・画面・ロゴ・イラスト
  - 同スキルの `references/visual-assets.md`
  - 切り出し・スクショ・イラスト生成のスクリプトは同スキルの `scripts/`
  - イラストの生成には利用者の Gemini の API キー（環境変数 `GEMINI_API_KEY`）が要る
  - キーの値を表示しない。チャットに貼るよう求めない。設定済みかどうかは `[ -n "$GEMINI_API_KEY" ] && echo set` で確かめる
- 文章
  - `rules/document-tone-rules.md`（見出し・本文・命名の正本）
  - 資料を書く前と、検収の前に読む

## 作業場所

- 新しい資料は `work/<案件>/` の下に作る
  - HTML の雛形: `node <キット>/tool-pineal-slide-v2/scripts/create-html-deck.mjs <キット>/work/<案件>/slides/<資料名>`
  - PPTX は `work/<案件>/pptx/` に、スキルの `references/pptx-v3.md` の構成で作る
- `tool-pineal-slide-v2/`・`pineal-slide-v3/`・`rules/` は書き換えない

## 環境

- Python はキット直下の `.venv/bin/python3` を絶対パスで使う
  - 手順書にある `python3` もこれに読み替える
- HTML の検証
  - 資料フォルダで `npm ci`（初回のみ）、`npm run check`
  - 通っても `review/shots/` の画像を全ページ見る
- PPTX の描画確認
  - `.venv/bin/python3 <キット>/pineal-slide-v3/scripts/visual_qa.py --file <絶対パス> --outdir <絶対パス> --dpi 110`
  - 出力に「エンジン: powerpoint」と出ること
  - 描画・結合の前に、PowerPoint で開いている資料を閉じる: `osascript -e 'tell application "Microsoft PowerPoint" to close every presentation saving no'`
  - 初回は PowerPoint と macOS が許可のダイアログを出す。利用者に許可してもらう

## 守ること

- 表記（正本は `rules/document-tone-rules.md`「表記の共通ルール」）
  - 文章でダッシュ（──・—・–）を使わない。句読点・コロン・読点で代える
  - 社名は「株式会社ピネアル」。「ピネアル株式会社」は誤り
  - 箇条書きはトップを短いラベルにし、詳細・数値は1段下げる
- テンプレ（`pineal-slide-v3/assets/pineal_temp.pptx`）
  - 型 4・5・6・15 は公開版では中身を外してある。起こさない
  - 納品する PPTX は pptxlib の `merge()` を通す。最後に `sanitize()` がかかり、使っていないレイアウトと作成者名が消える
  - 1枚だけ納品するときも `sanitize()` を呼ぶ
- 内容
  - 顧客名・数値・固有名詞・引用は元資料と照合し、指示なしに変えない
  - 依頼されていない PPTX は作らない
- 進め方
  - 形式や構成が決まっていない依頼では、作り始める前にアプローチを1行で示し、確認を取る
- 手順書や `rules/` に出てくる、キットに含まれないスキル（`verify`・`japanese-tech-writing`・`pineal-validate` など）やパスは使えない
  - その確認は、ルールを読んで目視で行う
