---
name: weekly-report
description: >
  Aggregate normalized marketing CSVs into a weekly report: per-week totals,
  week-over-week diff, media share, CTR/CVR/CPA. Outputs a summary CSV and a
  Markdown report. Use when the user wants recurring weekly reporting from
  ad/analytics data that has been normalized to the common schema (csv-normalize skill).
license: MIT
---

# weekly-report: 正規化済みデータから週次レポートを組み立てる

csv-normalize skill が出力した共通スキーマのCSV(複数媒体分)を読み、週(月曜開始)単位の集計・前週差分・媒体別構成比・CTR/CVR/CPAをまとめた `weekly_summary.csv` と `report.md` を出力する。

## 考え方

- **集計はスクリプトが決定的に行い、解釈の下書きはClaudeが、判断は人が行う。** スクリプトの出力は数表まで。「CPAが上がったのは何故か」「予算をどう動かすか」の文章はこの出力を見て書き、施策判断は人が下す
- 分母が0の指標(CV0件のCPA等)は**0や捏造値で埋めず空欄にする**
- 毎週同じスクリプトを同じ引数で回すだけの状態にしておくと、レポート作成が「作業」から「確認」に変わる

## 手順

1. 入力を用意する。媒体ごとのCSVを csv-normalize skill で共通スキーマ(`date, media, campaign, impressions, clicks, cost, conversions`)に正規化しておく
2. 実行する:

   ```bash
   python3 scripts/weekly_report.py normalized-a.csv normalized-b.csv --out-dir report/
   ```

3. `report/report.md` の数表を確認し、必要なら解釈の下書き(気づいた変化・確認したい点)を追記する。**数値そのものは書き換えない**
4. Excel形式の報告書に仕上げる場合は **xlsx-live skill** に引き継ぐ。`report/weekly_summary.csv` を読み込んで表・グラフ入りのxlsxを組み、開いたまま仕上がりを確認する

## 出力

| ファイル | 内容 |
|---|---|
| weekly_summary.csv | 週×媒体の集計(表示回数・クリック・費用・CV・CTR・CVR・CPA) |
| report.md | 週次合計の推移、直近週の前週差分(増減率)、直近週の媒体別費用構成比 |

## サンプルで試す

csv-normalize skill 同梱の架空データをそのまま入力にできる。

```bash
python3 ../csv-normalize/scripts/normalize_csv.py ../csv-normalize/samples/media-a.csv \
  --map ../csv-normalize/samples/media-a-map.json --out /tmp/norm-a.csv
python3 ../csv-normalize/scripts/normalize_csv.py ../csv-normalize/samples/media-b.csv \
  --map ../csv-normalize/samples/media-b-map.json --out /tmp/norm-b.csv
python3 scripts/weekly_report.py /tmp/norm-a.csv /tmp/norm-b.csv --out-dir /tmp/report
```

## 動作要件

- Python 3.9+(標準ライブラリのみ。追加インストール不要)
