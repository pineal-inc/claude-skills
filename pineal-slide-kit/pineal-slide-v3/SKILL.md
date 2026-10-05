---
name: pineal-slide-v3
description: ピネアルのテンプレートに沿った提案書パワポ（pptx）を作成・改修するスキル。設計書md→スライド単位の個別pptx→統合版マージの3段ワークフローで進め、テーマ準拠のデザイン定数・python-pptxの実装パターン・実機PowerPoint描画＋pdftoppmでの目視QAを備える。This skill should be used when creating, editing, or merging a pineal-branded proposal deck — 「提案書のパワポ作って」「スライド追加して」「統合版を作り直して」「pinealのテンプレで資料作って」等の依頼、または既存の提案書pptxの改修時。
---

# pineal 提案書パワポ 作成スキル

## 概要

ピネアルの提案書パワポを、テンプレートのトンマナを保ったまま作る・直すためのスキル。
`assets/pineal_temp.pptx` を唯一の正とし、色・座標・フォントはテーマから継承する。

## 前提の確認

作業開始時に `python-pptx` と Microsoft PowerPoint の有無を確認する。目視QAは PowerPoint で描画する（LibreOffice は書体が置換されるため、明示したときのレイアウト確認だけに使う）。

```bash
python3 -c "import pptx; print(pptx.__version__)"
ls "/Applications/Microsoft PowerPoint.app"
```

## フォルダ構成（この構成を必ず守る）

```
<案件フォルダ>/
├ 設計書/
│   └ 提案書_パワポ設計書.md          ← ①ここから始める
├ パワポ/
│   ├ 改修ログ.md                     ← 変更を1行ずつ追記
│   ├ S01_表紙/
│   │   ├ S01_表紙.pptx
│   │   └ old/S01_表紙_YYYYMMDD_HHMM.pptx
│   ├ S02_エグゼクティブサマリ/
│   │   ├ S02_エグゼクティブサマリ.pptx
│   │   ├ old/
│   │   └ photos/ logos/ images/      ← そのページの素材だけを置く
│   ├ ...
│   └ 統合版/
│       ├ <案件>_統合版.pptx           ← 作業用。常に再生成物
│       ├ old/
│       └ YYYYMMDD_ご提案書（pineal）_〇〇.pptx   ← 提出版。凍結して触らない
```

**スライド1枚 = 1フォルダにする理由**: 改修が1枚に閉じる／`old/` で履歴が追える／素材をページの近くに置ける／統合版を「いつでも捨てて作り直せるもの」として扱える。

## ワークフロー

### ① 設計書を書いて合意を取る

**pptxを1枚も作る前に**、`references/design-doc-template.md` の雛形で設計書mdを書く。
特に「**メッセージラインだけを縦に並べて音読する**」チェックを必ず行う。ここで筋が通らなければ構成が破綻している。
図を作ってから構成を直すのは高コストなため、この段階で潰す。

タイトルとメッセージラインの役割は次のように分ける。

- タイトル（プレースホルダー idx 0）: 主題を名指しする名詞句。「〜する」「〜は〇〇」で終えない
- メッセージライン（idx 1、行頭✓）: そのページの結論を文で書く

### ② スライドを1枚ずつ作る

まず `references/template-catalog.md` で**流用できる型を探す**。As-Is/To-Be・マイルストン・タイムライン・体制図・見積表は既に型がある。ゼロから組むより速く綺麗。

```bash
python3 scripts/new_slide.py \
    --out "パワポ/S03_プロジェクト理解/S03_プロジェクト理解.pptx" \
    --source-slide 10 --keep-body \
    --title "与件整理｜プロジェクト理解" --message "……"
```

ボディを自作する場合は `references/design-system.md` の定位置・色・サイズ階層に従う。
実装時の必須作法（影OFF・マージン0・座標ヘルパ）は `references/pitfalls.md` の 2〜4 を参照。

### ③ 目視QAする

```bash
python3 scripts/visual_qa.py --file "パワポ/S03_.../S03_....pptx"
```

出力されたJPEGを Read で開き、**見切れ・重なり・下端超過（7.5in）**を確認する。
python-pptx は折返しを計算しないため、**このステップを飛ばすと必ず崩れが残る**。

### ④ 統合版を作る

初回:

```bash
python3 scripts/merge_deck.py build --slides-dir パワポ --out "パワポ/統合版/〇〇_統合版.pptx"
```

**既存デッキがある場合は `build` を使わない。**

| やりたいこと | コマンド |
|---|---|
| 既存ページのテキスト修正 | `patch_text.py --deck <統合版> --replace "旧" "新"` |
| 末尾に1枚追加 | `merge_deck.py append --deck <統合版> --slide <個別pptx>` |

`build` は全ページを組み直すためプレースホルダーの継承が切れ、**タイトル/メッセージラインのフォントが飛ぶ**。
→ `references/pitfalls.md` の「1. 全ページ再結合は autofit を壊す」を必ず読む。
`build` / `append` は画像・リンクのリレーションを結合先に張り替える（2026-09-19 修正。以前は画像が消えた）。

### ②-b 中面A の標準（2026-09 確定）

テンプレに反映済みなので、`new_slide.py` で作れば**自動でこの形になる**。

- タイトル **28pt** ／ top 0.346 ／ height 0.471
- リード文 **18pt** ／ 行頭に **✓**（Wingdings の `ü`・ハンギングインデント）
- セクション見出し **14pt**（図形で作るため明示指定）

既に作ってあるデッキを追いつかせる場合のみ:

```bash
python3 scripts/apply_standard.py --file <deck> --dry-run   # 対象確認
python3 scripts/apply_standard.py --file <deck> --skip 2    # 手作業済みページを除外
```

### ④-b フォント・タイトルサイズを変える場合

**必ず `inspect` から始める。** デッキによってフォント体系が違い、
master/layout に直書きされていることがある（テーマ変更だけでは効かない）。

```bash
python3 scripts/set_font.py inspect     --file <deck>                       # 現状の内訳を見る
python3 scripts/set_font.py font        --file <deck> --to "Meiryo UI"      # 全パート置換
python3 scripts/set_font.py title-size  --file <deck> --layout 中面A --pt 28
```

`visual_qa.py` は既定で**実際の PowerPoint に描画させる**ため、フォント変更後の確認にも使える。
PowerPoint が無い環境は `--engine libreoffice`（書体は置換されるのでレイアウト検証のみ）。
→ `references/pitfalls.md` の 0 / 0-2

### ⑤ 変更を記録する

`パワポ/改修ログ.md` に1行追記する。フォーマット:

```markdown
| 日時 | ページ | 変更内容 | 理由・備考 |
|---|---|---|---|
| 2026-08-02 | S16 | 「未整備」→「自動配信が未整備」に修正 | PoC成功済みと判明。old退避済（1455）・統合版パッチ済 |
```

個別pptxと統合版の**両方**に反映したかを備考に必ず書く。片方だけ直すと次の改修で戻る。

## 実装スニペット

```python
from pptx import Presentation
from pptx.util import Inches as In, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

DARK=RGBColor(0x1C,0x1A,0x1A); GRAY=RGBColor(0x93,0x92,0x92); RED=RGBColor(0xD2,0x1E,0x2C)
BORDER=RGBColor(0xD9,0xD9,0xD9); REDTINT=RGBColor(0xF1,0xE5,0xE5); BAND=RGBColor(0xF6,0xF3,0xF3)
WHITE=RGBColor(0xFF,0xFF,0xFF)

def box(s, x, y, w, h, fill=WHITE, line=BORDER, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    sp = s.shapes.add_shape(shape, In(x), In(y), In(w), In(h))
    sp.shadow.inherit = False                      # ← 必須
    if fill is None: sp.fill.background()
    else: sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None: sp.line.fill.background()
    else: sp.line.color.rgb = line; sp.line.width = 9525
    tf = sp.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0   # ← 必須
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return sp

def put(sp, lines, align=PP_ALIGN.CENTER):
    """lines: [(text, pt, bold, color), ...]"""
    tf = sp.text_frame
    for i, (t, sz, b, c) in enumerate(lines):
        pa = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        pa.alignment = align
        r = pa.add_run(); r.text = t
        r.font.size = Pt(sz); r.font.bold = b; r.font.color.rgb = c
```

**タイトル・メッセージラインの `font.size` は絶対に触らない**（レイアウトから継承させる）。

### 固定ポイント（全ページ共通・ずらさない）

```
タイトル        28pt  ← レイアウト継承。触らない
リード文        18pt  ← レイアウト継承。触らない
セクション見出し  14pt  ← 図形で作るので明示指定する
脚注             8pt
```

箱のタイトル・本文はコンテンツ密度に応じて可変（`references/design-system.md`）。
**ページごとに固定ポイントを変えないこと。** 揃っていないと資料全体の質が下がる。

## スクリプト

| スクリプト | 用途 |
|---|---|
| `new_slide.py` | テンプレから1枚取り出してスライドフォルダ＋pptxを起こす |
| `merge_deck.py build` | 個別pptxを結合して統合版を作る（初回のみ） |
| `merge_deck.py append` | 統合版の末尾に1枚追加（autofitを壊さない） |
| `patch_text.py` | 統合版のテキストを直接置換（件数検証つき・`--dry-run`可） |
| `set_font.py inspect` | **フォント/タイトルサイズの現状を部位別に調べる** |
| `set_font.py font` | フォントを全パート一括置換 |
| `set_font.py title-size` | レイアウトのタイトルサイズを変更 |
| `apply_standard.py` | **既存デッキの中面Aページに標準（タイトル位置・リード文の✓）を追いつかせる** |
| `visual_qa.py` | PDF経由で画像化して目視QA（既定=実機PowerPoint描画） |

いずれも `old/` に自動退避する。

## 参照ファイル

| ファイル | 中身 |
|---|---|
| `references/design-system.md` | テーマ色の実値・定位置・フォントサイズ階層・レイアウト12種 |
| `references/template-catalog.md` | テンプレ16枚の型カタログと流用手順 |
| `references/pitfalls.md` | **既知の地雷9件。作業前に一読する** |
| `references/design-doc-template.md` | 設計書mdの雛形と書き方の原則 |
| `assets/pineal_temp.pptx` | テンプレ本体（唯一の正） |

## 最後に

`visual_qa.py` の出力で「エンジン: powerpoint」を確認する。PowerPoint が失敗するとエラーで止まる（LibreOffice へ自動では切り替えない）。納品前は実際にPowerPointで開いて確認する。

```bash
open "パワポ/統合版/〇〇_統合版.pptx"
```
