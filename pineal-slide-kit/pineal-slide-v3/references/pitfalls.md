# 既知の地雷

実際に踏んだものだけを載せている。**すべて再現性がある。**

---

## 0. 🔴 フォントはテーマだけ変えても効かない

**症状**: `theme1.xml` の majorFont / minorFont を差し替えたのに**見た目が1文字も変わらない**。

**原因**: デッキによっては**スライドマスターとレイアウトにフォント名が直書き**されている。
下位（master/layout）の直書きが上位（theme）の継承に勝つため、テーマ変更は無視される。

実例（ある案件のデッキ）:

```
theme   游ゴシック / 游ゴシック Light   ← 変えても効かない
layout  Noto Sans JP           224箇所  ← 実際に効いているのはこちら
layout  Noto Sans JP Light     188箇所
master  Noto Sans JP            14箇所
master  Noto Sans JP SemiBold    2箇所
```

**対策**: `scripts/set_font.py inspect` で**部位別の内訳**を先に見る。
`master`/`layout` に直書きがあれば `set_font.py font` で全パートを置換する。

```bash
python3 scripts/set_font.py inspect --file deck.pptx      # まず現状を見る
python3 scripts/set_font.py font --file deck.pptx --to "Meiryo UI"
```

> ⚠️ **デッキごとにフォント体系が違う。** `pineal_temp.pptx` は游ゴシックだが、
> 案件デッキは Noto Sans JP で組まれていることがある。必ず `inspect` から始める。

**script指定を巻き込まないこと**: `script="Thai"` `script="Arab"` 等の各言語マッピングまで
置換すると多言語フォント設定を壊す。`set_font.py` は `script="Jpan"` のみを対象にしている。
Wingdings・Symbol・Cambria Math も置換対象外（図と数式が壊れるため）。

---

## 0-2. 目視QAは PowerPoint エンジンを使う（LibreOffice では書体が見えない）

`Meiryo` / `MS Gothic` / `游ゴシック` は **Microsoft Office 同梱**。

```
/Applications/Microsoft PowerPoint.app/Contents/Resources/DFonts/
  meiryo.ttc  meiryob.ttc  msgothic.ttc  YuGoth*.ttc
```

このフォルダは fontconfig の探索対象外なので、**LibreOffice は代替フォントで描く**
（実際に Meiryo UI → 筑紫丸ゴシックに置換された）。

→ `visual_qa.py` は既定で**実際の PowerPoint に AppleScript で PDF を吐かせる**。
書体もレイアウトも実機と一致するので、フォント変更後の確認にも使える。

```bash
python3 scripts/visual_qa.py --file <deck>                      # PowerPoint（既定）
python3 scripts/visual_qa.py --file <deck> --engine libreoffice # PowerPointが無い環境
```

**PowerPointエンジンの注意**

- 実行中は PowerPoint が前面に出る。**終わるまで触らない**
- 対象を PowerPoint で開いたままだと失敗する。先に閉じる
- PowerPoint はサンドボックスのため **`/tmp` 等へ直接書けない**（エラー `-9074`）。
  スクリプトは元ファイルの隣に一時PDFを出してから作業ディレクトリへ移す。
  案件フォルダにPDFは残さない

---

## 1. 🔴 全ページ再結合は autofit を壊す（最悪の事故）

**症状**: 個別pptxを全部集めて統合版を作り直したら、**全ページのメッセージラインの文字が巨大化**して図に重なった。

**原因**: タイトル・メッセージラインは**プレースホルダー**で、フォントサイズをレイアウトから継承している（`font.size` は `None`）。
別レイアウトから作った新スライドに shape XML をコピーすると**継承元が切れ**、既定サイズにフォールバックする。

**対策**

| やりたいこと | 正しい方法 |
|---|---|
| 既存ページのテキスト修正 | **統合版に直接パッチ**（`scripts/patch_text.py`）。再結合しない |
| 末尾にページ追加 | **既存最終スライドの `slide_layout` を継承**して `add_slide` → shape をコピー（`scripts/merge_deck.py --append`） |
| 全ページ作り直し | 原則やらない。どうしても必要なら**1ページずつ目視QA** |

**検知方法**: 修正後は必ず `scripts/visual_qa.py` で**変更していないページも1枚**レンダリングして比較する。

---

## 2. 影が勝手に付く

`add_shape` した図形はテーマの影を継承する。pinealのトンマナは影なし。

```python
sp.shadow.inherit = False   # 図形を作ったら必ず即座に
```

---

## 3. テキストが箱の中で上下左右にズレる

textframe の既定マージンが効いている。

```python
tf = sp.text_frame
tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
tf.word_wrap = True
tf.vertical_anchor = MSO_ANCHOR.MIDDLE   # 箱の場合
```

---

## 3-2. 🔴 プレースホルダーの位置を一部だけ設定すると幅が0になる

**症状**: `title.top` と `title.height` だけを設定したら、**タイトルが左端で縦1列に潰れた**。

**原因**: プレースホルダーは位置・サイズをレイアウトから継承しており、`<a:xfrm>` を持たない。
python-pptx で1つでも値を設定すると `<a:xfrm>` が新規作成され、**指定しなかった側の継承が切れて 0 になる**。

```
設定前: xfrm なし（レイアウト継承 L=0.602 W=12.128）
top/height だけ設定 → <a:off x="0" y="316382"/><a:ext cx="0" cy="430682"/>
                        ↑ L=0        ↑ W=0 で幅が消える
```

**対策**: プレースホルダーの位置を触るときは **4値すべてを設定する**。

```python
sh.left   = Inches(0.602)
sh.top    = Inches(0.346)
sh.width  = Inches(12.128)
sh.height = Inches(0.471)
```

既に崩れたものを直す場合は、正常なページの値をコピー元にする。

---

## 4. 座標の単位を混ぜる

相対単位（列幅の倍数など）とインチを混在させると図が潰れる。**実際に潰した。**

対策: ヘルパを最初に定義し、以降は必ずそれを通す。

```python
MW = TW / 5                    # 1ヶ月分の幅
def MX(u): return TX + MW * u  # 月単位 → インチ
def MWD(u): return MW * u
```

---

## 5. `pdftoppm` が非ASCIIファイル名を開けない

日本語ファイル名のPDFで `I/O Error: Couldn't open file` になる。
→ **ASCII名にコピーしてから**変換する（`scripts/visual_qa.py` は自動でこれを行う）。

---

## 6. zsh のグロブ不一致でコマンドチェーンが止まる

```bash
rm -f a.pptx a.pdf a-*.jpg && cp ...   # a-*.jpg が無いと no matches found で以降が実行されない
```

→ 存在しないグロブを `rm` に混ぜない。個別に消すか `setopt null_glob` 相当を避ける書き方にする。

---

## 7. 目視QAを飛ばすと必ず崩れが残る

python-pptx はテキストの折返しを計算しない。**「文字を入れた」だけでは以下は絶対に検出できない。**

- 箱の中で2行に折れて見切れる
- 隣の図形と重なる
- 下端が 7.5in を超えて切れる

**書いたら必ずレンダリングして画像を見る。** 過去に見つけた例:
ベンダー6社の箱が下段バンドに侵入／注釈が説明ボックスに重なる／表が7.5inを超過／不要な矢印が中央テキストを横断。

---

## 8. レンダリングはエンジンによって精度が違う

| エンジン | 書体 | レイアウト | 用途 |
|---|---|---|---|
| **powerpoint**（既定） | 実機と一致 | 実機と一致 | すべての確認に使える |
| libreoffice | **別フォントに置換される** | 近似 | PowerPointが無い環境の代替 |

libreoffice で見た目を判断すると誤る。書体を変えたときは必ず powerpoint エンジンで確認する。

---

## 9. 提出済みファイルは絶対に上書きしない

提出版は別名で凍結し、以降の改修は作業用の統合版だけに入れる。

```
統合版/LeadMetrix提案書_統合版.pptx          ← 作業用。改修はこちら
統合版/20260727_ご提案書（pineal）_〇〇.pptx  ← 提出版。凍結
```

---

## 10. スキル配下に退避や成果物を作らない

`set_font.py` が `assets/old/` に退避を作り、**スキル本体と配布zipが 25MB → 49MB に膨らんだ**。

テンプレ（`assets/pineal_temp.pptx`）を編集するときの退避は**スキル外の一時領域**に置く。
`set_font.py` は対象パスがスキル配下かを判定して自動でそうする（`--no-backup` でも抑止可）。

同梱テンプレを変更したら、**戻す必要がない状態か確認してから実行する**。
一時領域の退避は再起動で消えるため、残したい場合は明示的に別の場所へ移す。

---

## 11. スクリプトの修正履歴（実装済み・経緯の記録）

- `new_slide.py`: 削除したスライドの rel を落とさず孤児パーツが残り、再保存で `Duplicate name: ppt/slides/slide1.xml` が出て壊れる → `p.part.drop_rel()` を追加
- `merge_deck.py`: build/append が「結合先の最終スライドのレイアウト」を全ページに使っていた。1枚目が表紙だと全ページに表紙の背景図が乗り、プレースホルダー継承も切れる → 元スライドと同名のレイアウトを結合先から探す `match_layout()` を追加
- `merge_deck.py`: 図形 XML だけを複製し、画像の `r:embed` を張り替えていなかった。結合後に画像が消える → `_remap()` で画像を blob から取り込み直し、スライド背景も複製（2026-09-19）
- `visual_qa.py`: PowerPoint が失敗すると LibreOffice に黙って切り替え、明朝に置換された画像で合否を判断していた → エラーで止めるよう変更。LibreOffice は `--engine libreoffice` の明示時だけ（2026-09-19）
- 表紙レイアウト（表紙A）に固定テキスト「2000.00.00」が残っている。スライド側から消せないので白箔で覆い、その上に日付を置く
