# pineal スライド制作キット

株式会社ピネアルのスライドを、Claude Code への指示で作るための一式です。
HTML で作ってブラウザで確認し、PDF を出し、必要なときは編集できる PowerPoint（PPTX）にします。

## 動作環境

- Mac
- Microsoft PowerPoint for Mac
  - PPTX の描画確認に使います
- Claude Code
  - ご自身のアカウントでログインしておいてください
- Homebrew（https://brew.sh）
- Python 3.9 以上
  - macOS の `python3` で足ります
- Gemini の API キー（イラストを作るときだけ）
  - Google AI Studio（https://aistudio.google.com/apikey）で、課金を有効にしたプロジェクトに発行します
  - 無料枠はなく、2K の画像1枚で約 0.134 ドルかかります（2026年10月時点）
  - キーは macOS のキーチェーンに登録します。次を実行し、表示される入力欄にキーを入れてください

    ```bash
    security add-generic-password -a "$USER" -s GEMINI_API_KEY -w
    ```

  - `~/.zshrc` には読み出す行だけを書きます。キーの値はファイルに書かないでください

    ```bash
    export GEMINI_API_KEY=$(security find-generic-password -s GEMINI_API_KEY -w 2>/dev/null)
    ```

  - 書いた後は新しいターミナルを開き、そこで Claude Code を起動します
  - キーは Claude Code のチャットに貼らないでください

## セットアップ

1. 置き場所
   - `git clone https://github.com/pineal-inc/claude-skills.git ~/claude-skills` で取得します。キットは `~/claude-skills/pineal-slide-kit/` です
   - 更新は `git pull` で取り込みます。`work/` の中身と `.venv/` は git の対象外なので、更新で消えません
   - セットアップの後に動かすと、スキルへのリンクが切れます。動かしたときは手順3をもう一度実行してください
2. 必要なソフト

   ```bash
   brew install node poppler librsvg
   brew install --cask font-noto-sans-jp
   ```

3. セットアップ

   ```bash
   cd ~/claude-skills/pineal-slide-kit
   bash setup.sh
   ```

   - 最後に「セットアップが終わりました」と出れば完了です
   - `NG` が出たら、表示どおりに入れてからもう一度実行します

setup.sh がすること

- Python の仮想環境 `.venv/` を作り、python-pptx などを入れる
- HTML の検証に使う Playwright と Chromium を入れる
- Claude Code のスキル `pineal-slide` を `~/.claude/skills/pineal-slide` にリンクする
  - 同じ名前のものが既にあれば、何もせず止まります
- テンプレと部品が読めること、HTML が描画できることを確かめる

## 使い方

1. 起動
   - `cd ~/claude-skills/pineal-slide-kit/work` に移ってから `claude` を起動します
   - キット直下の `CLAUDE.md`（作業ルール）が読み込まれるよう、必ず `work/` の中で起動します
2. 指示の例
   - 「/pineal-slide で、◯◯社向けの提案資料を作って。元資料は work/◯◯/受領/ にある」
   - 「元資料の図や画面の切り出し、ロゴ、イラストを使って」
   - 「この資料の PDF を出して」
   - 「この HTML 資料を、編集できる PPTX にして」
3. 初回の許可
   - PPTX の描画確認で、macOS と PowerPoint が「ターミナルからの操作」や「フォルダへのアクセス」の許可を求めます。許可してください

## 作業の流れ

| 段階 | 成果物 | 確かめること |
|---|---|---|
| 構成 | 各ページのタイトルと結論の一覧 | 結論を並べて読み、話がつながるか |
| 素材 | `slides/<資料名>/assets/` | 切り出し・ロゴ・イラストが読める大きさか、出典が `assets/sources.md` にあるか |
| HTML | `slides/<資料名>/index.html` | ブラウザでの見た目（Claude が全ページの画像を撮って確認する） |
| PDF | `review/pdf/index.pdf` | HTML の検証と同時に出る |
| PPTX | `<資料名>-YYYYMMDD.pptx` | PowerPoint で描画した全ページの画像 |

- HTML が内容の正本です。文言を直すときは HTML を直し、PPTX を作り直します
- PPTX は、設計書、パイロット8枚の確認、残りのページ、結合の順に作ります
- PPTX はテンプレ `pineal-slide-v3/assets/pineal_temp.pptx` の型から1枚ずつ起こすので、PowerPoint でそのまま編集できます

## フォルダ

| 場所 | 中身 |
|---|---|
| `work/` | 作業場所。案件ごとにフォルダを作る |
| `tool-pineal-slide-v2/` | スキル `pineal-slide`、HTML のテンプレート、PPTX の部品（`pptxlib.py`） |
| `pineal-slide-v3/` | PPTX のテンプレと、結合・描画確認のスクリプト |
| `rules/` | 文章のルール |
| `.venv/` | Python の仮想環境（setup.sh が作る） |

## 困ったとき

| 症状 | 対処 |
|---|---|
| PowerPoint がエラー -9074 を返し続ける | 開いている資料をすべて閉じ、PowerPoint を終了して起動し直す |
| 描画確認が -1712（タイムアウト）で止まる | 許可のダイアログが出ていないかを確かめ、出ていなければ PowerPoint を先に起動しておいてから再実行する |
| 描画確認の出力に「エンジン: powerpoint」が出ない | PowerPoint が /Applications にあるか、許可のダイアログを閉じてしまっていないかを確かめる |
| `/pineal-slide` が出てこない | `ls -l ~/.claude/skills/pineal-slide` でリンク先を確かめ、ずれていれば `bash setup.sh` |
| HTML の文字が想定と違う字形になる | Noto Sans JP が入っているかを確かめる |

## ライセンス

- スクリプト、HTML、CSS、文書
  - リポジトリ直下の `LICENSE`（MIT）に従います
- ピネアルのロゴ、ブランド素材、PPTX テンプレート
  - MIT の対象外です。株式会社ピネアルの資料、またはピネアルと共同で作る資料にだけ使ってください
  - 対象は `tool-pineal-slide-v2/templates/html/assets/brand/` と `pineal-slide-v3/assets/pineal_temp.pptx` です
