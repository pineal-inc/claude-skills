---
name: csv-normalize
description: >
  Normalize messy CSV exports (ad platforms, analytics tools) into a common schema
  (date, media, campaign, impressions, clicks, cost, conversions).
  Use when the user has CSV files with inconsistent column names, date formats,
  or number formats (¥, commas) and wants them unified before aggregation.
license: MIT
---

# csv-normalize: 形式のばらばらなCSVを共通スキーマに揃える

広告媒体の管理画面からダウンロードしたCSVは、媒体ごとに列名・日付形式・数値の書式(¥や桁区切りカンマ)が違う。このskillは、それらを共通スキーマ(`date, media, campaign, impressions, clicks, cost, conversions`)のCSVに正規化する。後段の集計(weekly-report skill)への入力を作る工程にあたる。

## 考え方

- **列の対応づけは人(またはClaude)が決め、変換はスクリプトが決定的に行う。** AIに毎回CSVを読ませて変換させると、行の欠落や数値の書き換えに気づけない。マッピング定義(JSON)だけを確認対象にし、変換処理は同じ入力なら必ず同じ出力になるスクリプトに任せる
- 解釈できない行があれば**出力を書かずにエラーで止まる**。黙って行を落とさない

## 手順

1. 入力CSVの**ヘッダー行と先頭数行だけ**を読み、列の意味を把握する
2. マッピング定義JSONを書く(書式は `scripts/normalize_csv.py` の docstring 参照)。共通スキーマに対応する列が入力に無い場合(例: 媒体名の列が無い)は `constants` で固定値を与える
3. 実行する:

   ```bash
   python3 scripts/normalize_csv.py input.csv --map mapping.json --out normalized.csv
   ```

4. エラーが出たら、マッピングの列名・`date_formats`・`encoding`(Shift_JIS系は `cp932`)を見直す。**スクリプト側を直すのではなくマッピング側を直す**のが原則
5. 出力の行数が入力と一致することを確認する

## 共通スキーマ

| 列 | 型 | 内容 |
|---|---|---|
| date | YYYY-MM-DD | 日付 |
| media | 文字列 | 媒体名 |
| campaign | 文字列 | キャンペーン名 |
| impressions | 整数 | 表示回数 |
| clicks | 整数 | クリック数 |
| cost | 数値 | 費用(通貨記号・カンマは除去済み) |
| conversions | 整数 | コンバージョン数 |

## サンプルで試す

`samples/` に架空の媒体2社分のCSVとマッピング定義を同梱している(データはすべて架空)。

```bash
python3 scripts/normalize_csv.py samples/media-a.csv --map samples/media-a-map.json --out /tmp/norm-a.csv
python3 scripts/normalize_csv.py samples/media-b.csv --map samples/media-b-map.json --out /tmp/norm-b.csv
```

自社のCSVに使うときは、samples のマッピング定義をコピーして列名を差し替えるだけでよい。

## 動作要件

- Python 3.9+(標準ライブラリのみ。追加インストール不要)
