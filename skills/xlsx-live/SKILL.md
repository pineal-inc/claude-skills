---
name: xlsx-live
description: "実Excelをxlwingsで操作してxlsxを作成・編集するスキル。更新がExcelの画面上でリアルタイムに見える。納品前の品質ゲート(壊れたZIP/XML・行高不足・数式エラー等の検出)と数式再計算スクリプトを同梱。Use when creating or editing .xlsx files on macOS with Microsoft Excel installed, e.g. 'エクセル作成', 'Excel編集', 'このxlsxを更新して'."
license: MIT
---

# xlsx-live: 実Excelを操作してxlsxを作成・編集する

## このスキルの考え方

Pythonからxlsxを扱う定番はopenpyxlだが、**既存ファイルのload→saveはExcelネイティブ要素を壊すことがある**。具体的にはオートフィルタの状態、条件付き書式の一部、図形・画像、テーブル、印刷設定、他アプリ由来のメタデータが落ちる。そこでこのスキルは役割を分ける。

| 作業 | 使うもの | 理由 |
|---|---|---|
| 新規ファイルの作成 | openpyxl | 壊す対象が存在しない。数式・書式をコードで組みやすい |
| **既存ファイルの更新** | **xlwings(実Excel)** | Excel自身に保存させるのでネイティブ要素が壊れない |
| 数式の再計算 | `scripts/recalc.py` | 実Excelに計算させ、エラーをJSONで返す |
| 納品前チェック | `scripts/xlsx_quality_gate.py` | 破損・見切れ・数式エラーを機械検出 |

xlwingsは実際のExcel.appを起動して操作するため、`visible=True` にすれば**セルが埋まっていく様子がExcelの画面上でリアルタイムに見える**。人がレビューしながらAIに編集させる用途に向く。

## 動作要件

- macOS + Microsoft Excel(デスクトップ版)
- Python 3.10+、`pip install xlwings openpyxl`
- 品質ゲートのPDFレンダリング検査(任意)にはLibreOffice(`soffice`)
- **初回実行時**、macOSが端末アプリにExcelの制御を許可するか尋ねるダイアログを出す。応答するまでxlwingsが止まって見えるので、初回はExcelを可視(`visible=True`)で動かして画面を確認するとよい。許可は「システム設定 > プライバシーとセキュリティ > オートメーション」から後で変更できる

## 既存ファイルの更新(xlwings)

```python
import xlwings as xw

app = xw.App(visible=True)  # False にすれば画面を出さずに実行できる
try:
    wb = app.books.open('/absolute/path/file.xlsx')
    ws = wb.sheets['Sheet1']

    # 読み書きは2次元リストの一括転送が速い。セル単位のループは遅い
    data = ws.range('A1:J57').value
    ws.range('A2').value = [['col1', 'col2'], ['val1', 'val2']]

    # 書式
    ws.range('A1:J1').color = (217, 217, 217)
    ws.range('A2:A57').api.font_object.bold.set(True)  # macOSはappscript API

    wb.save()
finally:
    wb.close()
    app.quit()  # 必ず呼ぶ。ゾンビExcelプロセスを残さない
```

パスは必ず絶対パスで渡す。相対パスはExcel側のカレントディレクトリ基準で解決されて事故になる。

### macOS固有の回避策(appscript API)

macOSのxlwingsはWindows COMとAPIが異なり、一部の操作はAppleScriptを直接叩く必要がある。

**オートフィルタ**: `ws.api.autofilter(...)` は `KeyError: 'autofilter'` で使えない。AppleScriptで適用する。

```bash
osascript -e 'tell application "Microsoft Excel"
  tell worksheet "Sheet1" of active workbook
    autofilter range range "A1:J57"
  end tell
  save active workbook
end tell'
```

**freeze paneと選択セルの不整合**: freeze paneを設定したシートで選択セルが凍結境界と矛盾していると、開いたとき表示が飛ぶ。各シートで先頭セル(A2等)をselectしてから保存する。

```bash
osascript -e 'tell application "Microsoft Excel"
  select range "A2" of worksheet "Sheet1" of active workbook
  save active workbook
end tell'
```

## 新規ファイルの作成(openpyxl)

新規作成はopenpyxlでよい。ただし2つの原則を守る。

1. **計算はExcel数式で書く**。Pythonで計算した結果の数値をセルに書き込むと、元データが変わっても再計算されない静的な表になる。`=SUM(B2:B9)` のように数式文字列を入れる
2. **openpyxlは数式を評価しない**。保存直後のファイルは数式の計算値が空なので、`scripts/recalc.py` で実Excelに再計算させる

```bash
python scripts/recalc.py output.xlsx
```

結果はJSONで返る。`status` が `errors_found` なら `error_summary` に `#REF!` 等の位置が出るので、修正して再実行する。

## 納品前の品質ゲート

作成・更新したxlsxは、渡す前に必ず品質ゲートを通す。

```bash
python scripts/xlsx_quality_gate.py output.xlsx --render-pdf
```

検出するもの: ZIP/XML破損、openpyxlで開けない構造、非表示の行・列、freeze paneと選択セルの不整合、折り返しテキストの行高不足(East Asian widthで日本語の字幅を見積もる)、数式エラー文字列、LibreOfficeでのPDFレンダリング失敗。

行高不足などは自動修復できる。

```bash
python scripts/xlsx_quality_gate.py output.xlsx --fix --out output-fixed.xlsx
python scripts/xlsx_quality_gate.py output-fixed.xlsx --render-pdf
```

日本語の長文セルは、文字数ではなく表示幅で行高を見積もらないと切れて見える。ゲートはこの見積もりを含むが、そもそも折り返しセルには「wrap text + 上揃え + 十分な行高(実用上の上限は約409pt)」を設定して書き込むこと。

## チェックリスト

- [ ] 既存ファイルの更新をopenpyxlのload→saveでやっていないか(xlwingsを使う)
- [ ] 数式で書くべき値をPython計算の固定値で埋めていないか
- [ ] recalc.pyの結果が `success` か
- [ ] 品質ゲートを通したか
- [ ] `app.quit()` を呼び、Excelプロセスが残っていないか
