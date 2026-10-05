# 素材の作り方（図・画面・ロゴ・イラスト）

文字と箱だけのページを続けない。
構成を決めたら、各ページの内容を目で示せる素材がないかを先に探す。
次の表の上から優先して使う。

| 順 | 素材 | 向く内容 |
|---|---|---|
| 1 | 元資料の図・画面の切り出し | 顧客の現物、既存の成果物、システムの画面 |
| 2 | HTML で組む図 | 流れ、構成、比較、スケジュール、画面イメージ |
| 3 | ロゴ | 会社、製品、使うツール |
| 4 | イラスト | 人と業務の場面、役割分担、運用の姿 |

## 置き場所と出典

- 置き場所: 資料フォルダの `assets/` に種類ごとに置く
  - `assets/shots/`: 切り出し・スクショ
  - `assets/logos/`: ロゴ
  - `assets/ill/`: イラスト
- 素材の出典: `assets/sources.md` に1素材1行で残す
  - 書くこと: ファイル名、元資料名とページ、または取得元の URL
  - ロゴはライセンスも書く
- ページの出典: 元資料のページを移したスライドは、`<section>` の `data-src` に元ページを入れる
  - 例: `templates/html/decks/product/index.html` の `data-src="product p.04"`

## スクリプトの前提

スクリプトはこのスキルの `scripts/` にある。
コマンド例は、先に次を実行してある前提で書いている。

```bash
SK=~/.claude/skills/pineal-slide
```

- スキルの場所
  - `$SK` は、リポジトリの `.claude/skills/pineal-slide` を指すリンクであること
  - `shot.mjs` と `illust.py` は、リンク先からリポジトリの `templates/html/` をたどって使う
- 使うコマンド
  - `pdftoppm`: `brew install poppler`
  - `rsvg-convert`: `brew install librsvg`
  - Pillow の入った `python3`: `crop.py` と `illust.py` が使う
  - Playwright: リポジトリ直下で `npm run setup:html` を1回実行する。`shot.mjs` が使う

## 元資料の図・画面の切り出し

### PDF から

確認用の低い解像度で座標を読み、貼り付け用の高い解像度から切る。

```bash
pdftoppm -r 110 -png -f 3 -l 3 受領/資料.pdf /tmp/prev        # 確認用
python3 $SK/scripts/crop.py grid /tmp/prev-03.png /tmp/prev-03-grid.png
# grid の画像を Read で見て、切る範囲の左上と右下の座標を読む
pdftoppm -r 250 -png -f 3 -l 3 受領/資料.pdf /tmp/hi          # 貼り付け用
python3 $SK/scripts/crop.py cut /tmp/hi-03.png 497 92 1260 782 assets/shots/line.png --scale 2.27
```

- `--scale`: 貼り付け用の解像度を確認用の解像度で割った値
  - 例: 250 ÷ 110 = 2.27
- pdftoppm の出力名: 総ページ数の桁に合わせて `-3` や `-03` になる。`ls` で確かめる

### Web ページ・HTML から

```bash
node $SK/scripts/shot.mjs https://example.com/ assets/shots/top.png
node $SK/scripts/shot.mjs 過去資料/報告.html /tmp/report.png --full
node $SK/scripts/shot.mjs 画面.html assets/shots/panel.png --selector ".panel"
```

- 撮る範囲
  - 既定: 1400×900 の表示範囲を2倍の解像度で撮る
  - `--full`: ページ全体
  - `--selector`: その要素だけ
- 縦に長い画像から一部を使うとき: `crop.py grid` で座標を読んで `crop.py cut` で切る
- ログインが要る画面: スクリプトでは撮れない。ユーザーに撮ってもらい、`assets/shots/` に置いてもらう

### 過去資料のサムネイル

これまでの成果物を並べるページでは、各資料の1ページ目を撮り、縦横比をそろえる。

```bash
python3 $SK/scripts/crop.py fit /tmp/report.png assets/shots/d-final.png --ratio 1.414 --width 900
```

### 切り出した後の確認

- `crop.py sheet` で一覧画像を作り、Read でまとめて見る
  - 文字が読める大きさか
  - 端が切れていないか
  - 関係のない部分が入っていないか
- 顧客の資料・画面は、その顧客向けの資料にだけ使う
- 元画像の色、系列を見分ける色、状態を示す色は加工しない

## HTML で組む図

- 流れ・構成・比較・スケジュールは、テンプレの部品か自由設計で組む
  - 部品: `templates/html/gallery/blocks.html`
  - 組み合わせと自由設計の例: `templates/html/gallery/pages.html`
- 画面イメージは画像を作らず HTML で組む
  - 文言を直すと画面にそのまま反映される
  - PPTX にするときは、その要素を `shot.mjs --selector` で撮って貼る
- 構成図には、製品の箱にその製品のロゴを入れる

## ロゴ

### 入手先

上から順に探す。

1. 公式のブランド素材
   - プレスキット、ブランドガイドライン、製品アイコンの配布ページ
2. Wikimedia Commons
3. Simple Icons
   - 単色の記号。公式の色つきロゴがあるならそちらを使う
   - 収録されていないブランドもある

Wikimedia Commons での探し方は次のとおり。

```bash
UA="pineal-slide/1.0 (<連絡先のURLかメールアドレス>)"
curl -sfG -A "$UA" https://commons.wikimedia.org/w/api.php \
  --data-urlencode "srsearch=<会社名> logo svg" \
  -d action=query -d list=search -d srnamespace=6 -d srlimit=10 -d format=json
curl -sfG -A "$UA" https://commons.wikimedia.org/w/api.php \
  --data-urlencode "titles=File:<候補のファイル名>.svg" \
  -d action=query -d prop=imageinfo -d "iiprop=url|extmetadata" -d format=json
curl -sfL -A "$UA" -o assets/logos/<会社名>.svg "<上の結果の url>"
```

- User-Agent: Wikimedia は連絡先入りの User-Agent を求める
  - 決まり: https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy
- ライセンス: 2つ目の結果の `extmetadata` で確かめ、`assets/sources.md` に書く
  - 確かめる項目: `LicenseShortName`、`AttributionRequired`、`Restrictions`
  - 多くのロゴは商標として保護されている。ライセンスと別に、その会社・製品を指す場所でだけ使う
- 候補が複数あるとき: 全部取り、`rsvg-convert -h 200 -o /tmp/x.png x.svg` で描画して見比べる
  - 旧ロゴ、社章、別事業のロゴと取り違えない
  - 判断がつかないときは、相手の公式サイトのロゴと見比べる

Simple Icons は次の URL で取る。名前は小文字の英数字。

```bash
curl -sfL -o assets/logos/openai.svg https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/openai.svg
```

### 使い方の決まり

- 縦横比、色、余白を変えない
  - 切り抜き、影、枠などの装飾をしない
- 顧客のロゴは、その顧客向け資料の表紙や体制図など、その会社を指す場所に置く
- 製品のロゴは、その製品を使うこと、またはつなぐことを示す場所に置く
  - ロゴだけを並べて実績のように見せない
- 横長のワードマークと正方形の記号を並べるときは、高さではなく見た目の大きさをそろえる
- PPTX にするときは、`pptxlib.svg_to_png()` が `assets/logos/*.svg` を PNG にする

## イラスト

### 使う場面

- 人と業務の場面を示すとき
  - 誰が何に困っているか、役割分担、運用の姿
- 図・画面・ロゴで示せる内容には使わない
- 置き方
  - 1ページに1点
  - 説明文と左右に組む

### 前提

- Gemini の API キー
  - Google AI Studio（https://aistudio.google.com/apikey）で、課金を有効にしたプロジェクトに発行する
  - 無料枠はない。2K の画像1枚で約 0.134 ドル（2026年10月時点）
- キーの置き場所: macOS のキーチェーン
  - 登録は利用者本人が行う。登録の決まりがある環境ではそれに従う
  - 決まりがなければ `security add-generic-password -a "$USER" -s GEMINI_API_KEY -w` で登録する。値は表示される入力欄に入れる
  - `~/.zshrc` には読み出す行だけを書く。キーの値をファイルに書かない

    ```bash
    export GEMINI_API_KEY=$(security find-generic-password -s GEMINI_API_KEY -w 2>/dev/null)
    ```

  - 書いたら新しいターミナルを開き、そこで Claude Code を起動する
- Claude の扱い
  - キーの値を表示しない。チャットに貼るよう求めない
  - 設定済みかどうかは `[ -n "$GEMINI_API_KEY" ] && echo set` で確かめる

### 作り方

```bash
python3 $SK/scripts/illust.py --out assets/ill/ill-planners.jpg --aspect 16:9 \
  "Scene: a wide open-plan office seen slightly from above with six separate desks in two rows; at each desk one person works alone on a laptop showing a spreadsheet grid; each desk has its own tall stack of binders and papers; the people are not talking to each other; one coffee mug with a red stripe on the front desk. Wide composition."
```

- 画風の指定はスクリプトが付ける
  - テンプレの `templates/html/assets/product/ill-before.jpg` と同じ線画、白背景、顔なし、赤は小物1点、文字なし
- 場面は英語で、次を具体的に書く
  - 人数と位置関係
  - 手元の物、画面に映っているもの
  - 構図（wide composition、close-up など）
  - 赤にする小物1つ（例: `a coffee mug with a red stripe`）
- 数値や名前など文字が要る情報は、イラストに入れず HTML に書く
- 同じ資料の2枚目以降は、できたイラストを `--ref assets/ill/ill-planners.jpg` で渡す
  - 線の太さと人物の描き方がそろう

もう1つの例（役割分担のページ）は次のとおり。

```text
Scene: on the left, a person in a suit calmly operates a laptop at a desk; on the right, behind a low partition, another person in a suit holds a wrench with a red handle next to a small server rack and a cloud outline, maintaining it; a simple dashed line connects the server rack to the laptop.
```

### 生成後の確認

Read で1枚ずつ見る。

- 文字、数字、ロゴが入っていない
- 赤が1点だけ
- 手、指、机の形が崩れていない
- 同じ資料の他のイラストと描き方がそろっている

合わないときは、場面の書き方を変えて作り直す。
1枚ごとに利用料がかかるため、同じ文のまま何度も生成し直さない。

## 仕上げの確認

- 資料フォルダで `npm run check` を実行し、`review/shots/` を全ページ見る
  - 素材が読める大きさで置かれているか
  - 素材と説明の位置関係が取れているか
  - 文字と箱だけのページが続いていないか
- `assets/sources.md` に全素材の出典があるか
