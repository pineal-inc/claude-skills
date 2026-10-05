# PPTX 出力（v3 テンプレ方式）

HTML 版を内容の正本にしたまま、編集可能な PPTX を作る手順。
ピネアルのテンプレ `pineal-slide-v3/assets/pineal_temp.pptx` の型スライドを1枚ずつ起こし、
ボディを `../pptx/pptxlib.py` の部品で組む。

## 前提

- 内容
  - HTML 版が承認済みであること。タイトル・リード・本文は HTML 版から転記し、PPTX 側で文言を変えない
  - 依頼されていない PPTX は作らない
- 環境
  - `python-pptx`、`Pillow`、`rsvg-convert`、Microsoft PowerPoint
  - pineal-slide-v3 リポジトリ（キット直下の `pineal-slide-v3/`。tool-pineal-slide-v2 と同じ階層にあれば自動で見つかる）
  - `pdftoppm`・`pdffonts`（poppler）。`visual_qa.py` が使う
- 読むもの
  - v3 `SKILL.md`: フォルダ構成、中面A の標準、改修ログの書き方
  - v3 `references/template-catalog.md`: 型の番号
  - v3 `references/design-system.md`: 定位置、色、サイズ階層
  - v3 `references/pitfalls.md`: 影、マージン、autofit、フォント

## 社内情報の扱い

- テンプレには役員写真、顧客ロゴ、連絡先が入った型がある
  - 4 Board Member、5 Media、6 Client、15 お問い合わせ
- パートナー・顧客向けの資料ではこれらを起こさない
- 納品前に、統合版にこれらの文言が残っていないことを確認する
- 公開版のテンプレでは、4・5・6・15 の中身と「ピネアルについて」レイアウトのメンバー紹介を外してある（レイアウト名は「白紙」）
- マスターのレイアウトにも社内情報がある
  - 「ピネアルについて」レイアウトはメンバーの写真・氏名・経歴を持つ
  - スライドで使わなくてもファイルの中に残り、「新しいスライド」から出せてしまう
  - `merge()` は最後に `sanitize()` を呼び、使っていないレイアウト、作成者名、テンプレのサムネイルを除く（2026-09-29〜）

## 案件フォルダ

```
案件/workspace/
  slides/<資料名>/            # HTML 版（正本）。assets/ を PPTX でも共用する
  pptx/
    設計書/提案書_パワポ設計書.md
    slides.py                 # 1ページ1関数。build_S01() ... と _共通ヘルパ
    パワポ/S01_表紙/S01_表紙.pptx ...   # v3 と同じ「1枚=1フォルダ」
    パワポ/統合版/full.pptx
    パワポ/改修ログ.md
    _qa/                      # visual_qa の出力
```

`slides.py` の先頭:

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / '.claude/skills/pineal-slide/pptx'))
from pptxlib import *
import pptxlib
HERE = pathlib.Path(__file__).parent
pptxlib.configure(assets=HERE.parent / 'slides/<資料名>/assets', out=HERE / 'パワポ')
```

`configure()` は HTML 版の `icons/*.svg` と `logos/*.svg` を高さ256px の PNG に書き出す（既存は触らない）。

## 部品（pptxlib.py）

| 区分 | 関数 | 要点 |
|---|---|---|
| 起こす | `new_slide(key, TPL_*, title, lead)` | 型を複製し、タイトルとメッセージラインを差し替える。既存は `old/` へ退避 |
| 箱・線 | `box` `put` `text` `hline` `vline` `arrow` `tri` | 影OFF・マージン0。`box` は図形を返すので、後から背面へ移せる |
| 見出し | `section` | 14pt 太字＋罫線（左端だけ赤）。戻り値は次の y |
| 箇条書き | `bullets` `marked_list` | `marked_list` はロゴ・アイコンを行頭に置き、下端の y を返す |
| 表 | `table` `mark_table` | 行高は `row_h` で固定。`fills` で行やセルに色を付ける。`mark_table` はセル左に記号を置き、記号の実寸幅だけ段落を字下げする |
| 画像 | `pic` `logo` `icon` `mark` `mark_w` `logo_label` | 縦横比は常に保つ。幅と高さの両方を渡すと内接させる |
| 注記 | `footnote` `caption` | 8pt・8.5pt のグレー |
| 見積り | `est_lines` | Meiryo UI の実測係数で行数を見積もる。係数を下げると折り返しが重なる |
| 結合 | `merge(files, out)` | 画像リレーションを張り替えて結合し、最後に `sanitize()` をかける |
| 掃除 | `sanitize(path)` | 使っていないレイアウト、作成者名、テンプレのサムネイル、app.xml のスライド名一覧を除く。1枚だけ渡すときも呼ぶ |

定数: `L` `R` `W` `BODY_TOP`（リード1行のとき2.05、2行なら2.40）`FOOT_Y`、色 `DARK` `RED` `BORDER` `REDTINT` `BAND`、型番号 `TPL_COVER` `TPL_SECTION` `TPL_BASE` `TPL_ASIS` `TPL_END` ほか。

## 手順

1. 設計書を書く
   - v3 `references/design-doc-template.md` の雛形を使う
   - ストーリーラインは「S番号 タイトル｜リード」を HTML 版から写す
   - タイトルは名詞句、結論はメッセージライン（キット直下の `rules/document-tone-rules.md` R1）
   - スライド別に「流用する型」と「ボディの構成」を1行ずつ書く
2. パイロット8枚
   - 型と部品の組み合わせが出そろう8枚を選ぶ（表紙、章扉、表、As-Is/To-Be、画面つき、構成図など）
   - 描画して依頼者に見せ、承認を取ってから残りに進む
3. 残りを作る
   - 共通ヘルパ（タイムテーブル、比較、ゴールなど）は `slides.py` 内に `_名前` で置き、ページ間で揃える
   - 箱の高さを文字量に合わせるときは、先にリストを置いて下端の y を得てから箱を描き、`spTree.insert` で背面へ移す
4. 結合
   - `merge()` か v3 `merge_deck.py build`。どちらも画像を張り替える
   - `merge_deck.py build` は掃除をしないので、後で `sanitize(out)` を呼ぶ
   - 結合前に PowerPoint で開いている資料を閉じる
     - `osascript -e 'tell application "Microsoft PowerPoint" to close every presentation saving no'`
5. 描画して全ページを見る
   - `python3 $V3/scripts/visual_qa.py --file <絶対パス>/full.pptx --outdir <絶対パス>/_qa/full --dpi 110`
   - 出力の「エンジン: powerpoint」を確認する。PowerPoint が失敗するとエラーで止まる
   - 初回は PowerPoint がフォルダアクセスの許可ダイアログを出す（-9074）。ダイアログは利用者に許可してもらう
   - `pdffonts _qa/full/qa.pdf` で MeiryoUI が埋め込まれ、明朝が無いことを確かめる
   - ページ画像を1枚ずつ Read する。ロゴと本文の重なり、折り返しの重なり、箱と文字量のずれ、下端超過を見る
6. 検査
   - 社内情報の型（4・5・6・15）の文言が残っていない
   - 残っているレイアウトが使った型の分だけで、文書プロパティの作成者が「株式会社ピネアル」になっている
   - ダッシュ、行頭の全角中黒、「ピネアル株式会社」が無い
   - `python3 -c "from pptx import Presentation; Presentation('<file>')"` で読み戻せる
7. 納品
   - 直下に `トピック-YYYYMMDD.pptx` で置く。旧版は `archive/` へ移す（同名の上書きに注意）
   - 直下の PDF は HTML 版から出したものを残す
   - `パワポ/改修ログ.md` に方式、成果物、部品の修正、依頼者の判断を日付つきで書く

## 過去に出た崩れ

| 症状 | 原因と対処 |
|---|---|
| ワードマーク型のロゴが本文に重なる | 記号幅を固定値で見ていた。`mark_w` で実寸幅を使う |
| 2行のリードが本文に食い込む | ボディ上端を 2.40 に下げる |
| 表の行の色が付かない | `mark_table` に `fills` を渡し忘れ |
| 箱が文字より高い・低い | 箱を先に描いていた。リストの下端から高さを決める |
| 折り返し行が重なる | `est_lines` の係数を下げすぎた。かな0.86、漢字・約物0.95、半角0.52 が下限 |
| 結合後に画像が消える | 旧 `merge_deck.py build` の不具合。2026-09-19 に修正済み |
| 描画が明朝になる | `visual_qa` が LibreOffice に切り替わっていた。2026-09-19 からエラーで止まる |
| 語の途中で改行する（「画面イ／メージ」） | PowerPoint は日本語をどの字の間でも折り返す。文節の切れ目に `\n` を入れ、`a:br` に置き換える |
| 納品ファイルにメンバー紹介が入っている | 使っていないレイアウトがマスターに残っていた。`sanitize()` で除く（2026-09-29） |
