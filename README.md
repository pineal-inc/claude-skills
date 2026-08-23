# claude-skills

株式会社ピネアルが業務で使っている [Claude Code](https://claude.com/claude-code) 用skillの公開リポジトリです。

## 収録skill

| skill | 内容 |
|---|---|
| [csv-normalize](skills/csv-normalize/) | 広告媒体などの形式がばらばらなCSVを共通スキーマに正規化する。列マッピングをJSONで定義し、変換はスクリプトが決定的に実行。架空データのサンプルCSV同梱 |
| [weekly-report](skills/weekly-report/) | 正規化済みCSVから週次集計・前週差分・媒体別構成比・CTR/CVR/CPAを計算し、集計CSVとMarkdownレポートを出力する |
| [xlsx-live](skills/xlsx-live/) | 実Excelをxlwingsで操作してxlsxを作成・編集する。更新がExcelの画面上でリアルタイムに見える。納品前の品質ゲートと数式再計算スクリプトを同梱 |

csv-normalize → weekly-report → xlsx-live の順につなぐと、媒体別CSVの正規化から週次レポートのExcel仕上げまでが一続きになります。

## インストール

skillのフォルダを `~/.claude/skills/` にコピーするだけです。

```bash
git clone https://github.com/pineal-inc/claude-skills.git
cp -r claude-skills/skills/csv-normalize ~/.claude/skills/
cp -r claude-skills/skills/weekly-report ~/.claude/skills/
cp -r claude-skills/skills/xlsx-live ~/.claude/skills/
```

以後、Claude Codeが「エクセル作成」「このxlsxを更新して」といった依頼を受けたときに自動で参照します。動作要件は各skillのSKILL.mdを参照してください(xlsx-liveはmacOS + Microsoft Excelが前提です)。

## 背景

各skillの設計背景は、コーポレートサイトのコラムで解説しています。

- csv-normalize / weekly-report: [AIデータ分析の活用事例とツール](https://pineal.co.jp/column/ai-data-analysis-guide)
- xlsx-live: [Excel・スプレッドシートをAIで効率化する方法](https://pineal.co.jp/column/excel-ai-guide)

## License

[MIT](LICENSE)
