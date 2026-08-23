# claude-skills

株式会社ピネアルが業務で使っている [Claude Code](https://claude.com/claude-code) 用skillの公開リポジトリです。

## 収録skill

| skill | 内容 |
|---|---|
| [xlsx-live](skills/xlsx-live/) | 実Excelをxlwingsで操作してxlsxを作成・編集する。更新がExcelの画面上でリアルタイムに見える。納品前の品質ゲートと数式再計算スクリプトを同梱 |

## インストール

skillのフォルダを `~/.claude/skills/` にコピーするだけです。

```bash
git clone https://github.com/pineal-inc/claude-skills.git
cp -r claude-skills/skills/xlsx-live ~/.claude/skills/
```

以後、Claude Codeが「エクセル作成」「このxlsxを更新して」といった依頼を受けたときに自動で参照します。動作要件は各skillのSKILL.mdを参照してください(xlsx-liveはmacOS + Microsoft Excelが前提です)。

## 背景

各skillの設計背景は、コーポレートサイトのコラムで解説しています。

- xlsx-live: [Excel・スプレッドシートをAIで効率化する方法](https://pineal.co.jp/column/excel-ai-guide)

## License

[MIT](LICENSE)
