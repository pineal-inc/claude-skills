# pineal-slide-html

pineal のブランドで **1280 × 720 の HTML スライド**を作るためのテンプレート一式。
HTML を1枚書けばブラウザで見られる。ビルドは不要で、依存は検証スクリプトだけにある。

このファイルは **AI（Claude Code など）が読んで作業するための説明書**。
人が読んでもよいが、想定している使い方は「利用者が AI に指示 → AI がこの README を読んで HTML を書き換える → ブラウザで確認」。

- 公開版。採用・営業の作例（`decks/`）と、それを検査するスクリプトは外してある。
- Office 同梱フォントは同梱していない。本文は Noto Sans JP 系のシステムフォントで描画する。

---

## 1. まず見る

| ファイル | 中身 |
|---|---|
| `index.html` | 入口。各ページへのリンク |
| `starter.html` | 6枚。テンプレートの使い方そのものをスライドで説明したもの |
| `gallery/blocks.html` | 10枚。**部品カタログ**。使える class が実物で並んでいる |
| `gallery/pages.html` | 9枚。**ページ構成の見本**。表紙・目次・中面・章扉・部品を混ぜた1枚・完全に自由に設計した1枚 |

`open starter.html` でブラウザに渡す。ローカルサーバーは要らない。

ビューアの操作: `←` `→` でページ送り、小文字の `p` でプレゼン表示、小文字の `f` で全画面切替、`Esc` で戻る、`Cmd+P` で PDF。

---

## 2. 骨組み

新しい資料は、この形の HTML を1ファイル作るところから始める。

```html
<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>資料名 ｜ pineal</title>
<link rel="stylesheet" href="../core/pineal-tokens.css">
<link rel="stylesheet" href="../core/pineal-slide.css">
<link rel="stylesheet" href="../core/pineal-blocks.css">
<link rel="stylesheet" href="../core/pineal-viewer.css">
<style>
  /* この資料だけの CSS。必ず .deck-<name> の中に閉じる */
  .deck-sample .xx-photo { ... }
</style>
</head>
<body class="deck-sample">
<div class="deck">

  <section class="slide">
    <span class="mark"></span>
    <header class="slide-head rule">
      <div class="kicker">章ラベル</div>
      <h2 class="title">ページの主題</h2>
    </header>
    <p class="lead">このページで言い切る一文。</p>
    <div class="body">
      <!-- 中身 -->
    </div>
    <footer class="slide-foot">
      <img src="../assets/brand/pineal-logo.svg" alt="pineal">
      <span class="foot-meta">1 / 12</span>
    </footer>
  </section>

</div>
<script src="../core/pineal-viewer.js"></script>
</body>
</html>
```

`<section class="slide">` が1枚。並べた順に表示される。相対パスは置き場所に合わせる（`decks/xx/index.html` なら `../../core/...`）。

### CSS の層

| 層 | ファイル | 役割 |
|---|---|---|
| トークン | `core/pineal-tokens.css` | 色・文字・余白の共通設定 |
| ページ | `core/pineal-slide.css` | キャンバス・見出し・フッター・ページ型 |
| 部品 | `core/pineal-blocks.css` | カード・表・リスト等 |
| ビューア | `core/pineal-viewer.css` / `.js` | 表示切替・ナビゲーション・印刷調整 |
| 資料固有 | 各 HTML の `<style>` | ここに書く。`body` の `deck-<name>` でスコープする |

共通 CSS は複数資料で共有する改善や不具合修正のときに更新し、全作例を確認する。
1つの資料の都合は資料固有 CSS に書く。**スコープを外して書かない**（他の資料に漏れる）。

---

## 3. 作り方は3通り。どれを選んでもよい

この3つは**同格**で、上ほど正しいわけではない。

1. **既定の構成をそのまま使う** — `gallery/pages.html` の型（表紙・目次・中面・分割・章扉・締め）を写して中身を差し替える
2. **部品を混ぜる** — `gallery/blocks.html` の部品を必要なだけ組み合わせて1枚を作る（見本: `gallery/pages.html` の B-06）
3. **そのページ専用に自由設計する** — `class="slide free"` を下敷きに、資料固有 CSS とインライン SVG でページを起こす（見本: `gallery/pages.html` の B-07）

3 でも共通の色・文字設定を出発点にし、印刷用キャンバスは 1280 × 720 に収める。構成・比率・文字サイズは内容に合わせて調整してよい。図の意味を区別する追加色なども、読みやすさと資料全体の統一感を見て判断する。
ただし**ロゴ等のブランド資産は自由設計に含めない**。位置も切り出しも元データのまま使う（次項）。

「カードに詰める」のが既定ではない。文章で足りるページは文章でよいし、
表が最短ならカードを使わず表にする。

### 本文の配色と図の使い方

v3のブランドと共通の枠組みに、v2の「強調を絞る」「図を読める大きさで置く」判断を取り入れている。v2のCSSやPPTX変換用の制約をそのまま持ち込む必要はない。

- 本文は白・ダーク・グレーが基本。同列の項目は同じ見た目にする。中央・最後の箱、製品名や「AI」「ナレッジ」、比較の変更後という理由だけで強調しない。
- 強調を足す前に、それが何の違い・状態・判断を伝えるかを確かめる。外しても読み取りが変わらない塗り・帯・枠・太字は外す。淡いピンク、グレー、黒ベタも対象で、色を薄くするだけでは解決にならない。強調を毎ページ入れる必要はない。
- 構造は見出し・配置・間隔で伝える。箱や面が必要な場合は、同じ役割の要素で揃える。赤文字＋赤枠＋淡背景を重ねない。`.accent` / `.hi` は明示された選択や判定対象など、他との違いを示す場合に使う。
- たとえば「案件A → ナレッジ → 案件B」は3箱を同じ見た目にする。進捗図で実際の現在工程を示すなら、本文に「現在」を記し、該当する `.flow-step` に `aria-current="step"` を付ける。比較の `.to` や旧 `.on` だけでは強調されない。
- 画像の色、系列の識別、状態を示す色には意味がある。必要な色は説明・凡例とともに使い、ただ色数を減らすために元画像を加工しない。
- 元資料を移すときは本文だけでなく、画像・図・画面と説明の関係も確認する。意味を担う図を、理由なく削除してカードの羅列へ置き換えない。必要素材を同梱し、元ページと新ページを並べて確認する。
- 本文領域の下半分が空くときは、図を大きくする、図と説明を左右に組む、文字の大きさや行間を調整する。短い文章を入れた箱を引き伸ばして余白を埋めない。
- 図は投影して読める大きさにする。図を全幅に置くなら本文幅の約90%、有効高の約70%を目安にし、収まらないときは左右に分ける。これは判断の目安であり、全ページの面積を機械的に埋める規則ではない。

素材の作り方はスキルの `references/visual-assets.md` にある。

### ブランド素材の扱い

`assets/brand/` の中身は **v3 テンプレ（`pineal_temp.pptx`）の素材そのもの**。
書き出し直し・色替え・比率変更・描き起こしをしない。差し替えるときは元 pptx から取り直す。

表示位置と切り出しも元データに従う。
`core/pineal-slide.css` の座標は、pptx の `xfrm`（`off` / `ext` / `rot`）と `srcRect` を
EMU から px（1px = 9525 EMU）へ機械的に換算した値であり、目分量ではない。
`srcRect` を無視すると絵の大きさと切れ方が変わるため、必ず `background-size` と
`background-position` に反映する。

- 表紙の大型ロゴ（`.cover-art`。class 名は残しているが中身はロゴ）と、章扉・締めの背景は、
  元の配置どおりキャンバスの外へはみ出す。収めようとしない。
- 章扉と締めの背景は 270 度回転で置かれている。CSS の `transform` は Chromium の PDF 出力で崩れたため、
  回転と切り出しを `assets/brand/section-bg.svg` / `end-bg.svg` に閉じ込め、CSS からは等倍の背景として貼っている。
  この2つは原本 `section-art.png` をそのまま内包した表示用ラッパーで、原本も残してある。
- 目次のワードマークは**黒**で、白地側の右下に置く。濃灰パネルの中ではない。
- 対応表（元素材のハッシュ・画素寸法・レイアウトごとの EMU / px / `srcRect` / `rot` / 対応 CSS セレクタ）は
  `assets/brand/brand-assets.json` にある。直したときはここも更新する。

---

## 4. ページ型

`class="slide"` に足す。

| class | 用途 |
|---|---|
| （なし） | 中面。タイトル＋赤罫＋リード＋本文＋フッター |
| `cover` | 表紙。`.cover-inner`（`.cover-kicker` / `.cover-title` / `.cover-to` / `.cover-date`）と `.cover-art`（右の大型ロゴ）`.cover-sign`（左下のワードマーク） |
| `agenda` | 目次。左に濃灰パネル、右に `.agenda-item`（`.no` / `.nm` / `.desc`、現在地は `.on`） |
| `section` | 章扉。上辺・右辺に白を残した濃灰背景。`.sec-en` / `.sec-title` / `.sec-lead` / `.sec-no` |
| `split` | 左に狭いテキスト、右に淡色パネル（`.split-panel`） |
| `end` | 締め。全面濃灰＋白ロゴ |
| `dark` | 濃灰の中面。自由設計の下敷きにも使える |
| `free` | クロムなしの素のキャンバス。自由設計の入口 |

中面の共通部品: `.mark`（右上のロゴマーク）、`.slide-head.rule`（灰罫＋左91pxの赤罫）、
`.kicker`、`.title`、`.lead`（`.lead.check` で行頭に赤い ✓）、`.body`（`.tight` で詰める、`.center` で縦中央）、
`.slide-foot`（`.hairline` で細い上罫）。

---

## 5. 部品

実物は `gallery/blocks.html` にある。ここは索引。

**並べる** — `.cols` ＋ `.cols-2` `.cols-3` `.cols-4` `.cols-5` `.cols-55` `.cols-73` `.cols-64` `.cols-46` `.cols-37`。
修飾は `.top`（上揃え）`.fill`（高さを揃える）`.gap-sm` `.gap-lg`。
縦積みは `.rows`（`.gap-sm` `.gap-lg`）。チップなど小物の横並びは `.chips`。

> `.cols` は grid なので、`cols-N` を付けないと1列になる。横に並べたいのに縦に積まれたらこれを疑う。

**囲う** — `.card`（`.soft` `.accent` `.flat` `.dark` `.top-red` `.pad-sm` `.pad-lg`）、
中身は `.card-label` `.card-title` `.card-sub` `.card-body`。
`.band`（`.red` `.dark`）は横長の帯、`.callout`（`.soft`）は補足の箱。

**書く** — `.h`（`.red` `.bar` `.under`）、`.label`、`.sub`、`.note`、`.footnote`（`.rule`）、
`.list`（`.dash` `.check` `.sm` `.tight`）、`.kv`（dt/dd の対）、`.msg`（`.lg` `.plain`）、`.quote`。
インラインは `.em`（赤太字）、`.marker`（黄マーカー）、`.marker-red`、`.num`（等幅数字）。

**図解** — `.flow`（`.flow-step` ＋ `.flow-arrow`、`.vertical` で縦。実際の現在工程だけ `aria-current="step"` と本文の「現在」を付ける）、
`.compare`（`.compare-side` ＋ `.compare-arrow`、変更後の `.to` は見た目の差を作らない）、
`.timeline`、`.milestone`（`.ms-head` / `.ms-row` / `.ms-track` / `.ms-bar`）、
`.org`（`.org-cell` は「左に写真・右に本文」の2カラム。縦積みにしたいなら資料固有の class を作る）、
`.stats`（`.stat` / `.stat-num` / `.stat-label`）、`.logo-wall`（`.logo-cell`）、`.case`。

**表** — `.tbl`（`.compact` `.lines`）。`<tr class="hi">` は、明示された選択・判定対象の行に使う。料金の高い行や最後の行を自動で塗らない。

**写真** — `.photo`（figure ＋ figcaption）。`.frame` で枠、`.cover-fit` で高さいっぱいに切り抜く。
`.org-photo` は既定で切り抜くので、**元の縦横比を崩したくない写真には `.fit`** を足すか、
資料固有 CSS で枠を作って `object-fit: contain` にする。

**小物** — `.chip`（`.red` `.solid` `.line`）、`.badge`（`.ghost` `.sq`）、`.spacer`、`.grow`、`.nowrap`、`.t-c`、`.hide`。

---

## 6. トークン

色・級数・余白は `core/pineal-tokens.css` の CSS 変数を基本にする。資料固有の調整や SVG への直接指定も可能で、既定値は判断の出発点として使う。

- 色: `--red` `#D21E2C` / `--red-deep` / `--red-pale` / `--ink` `#1C1A1A` / `--ink-mid` / `--ink-weak` /
  `--paper` `#FFFFFF` / `--paper-soft` `#F6F3F3` / `--line` / `--line-soft` / `--gold` / `--sand` / `--slate` / `--marker`
- 級数: `--fs-cover` 52 / `--fs-section` 44 / `--fs-title` 32 / `--fs-lead` 19 / `--fs-h` 17 /
  **`--fs-body` 15（基準本文級数）** / `--fs-sm` 13 / `--fs-xs` 11 / `--fs-label` 11
- 余白: `--s1`〜`--s8`、版面は `--pad-x` 58 / `--pad-top` 30 / `--pad-bottom` 50
- 角丸: `--r-sm` `--r-md` `--r-lg` `--r-pill`

v3 の PPTX は 7.5〜9.5pt という極小の級数で組まれているが、**それをそのまま Web に持ってきていない**。
画面と PDF で読める大きさとして本文 15px を基準にしてある。

---

## 7. 文章のルール

文章の正本はキット直下の `rules/document-tone-rules.md`。要点を以下に載せている。ユーザーの明示的な文章・構成の指定を優先する。

- `.title` は**主題を名指しする名詞句**。言い切る一文は `.lead` に書く
- 見出しに「〜ます」「〜ましょう」「〜てください」を入れない
- 箇条書きの個数を見出しで予告しない
- 文章でダッシュ（──・—・–）を使わない
- 正式社名は「株式会社ピネアル」（前株）

原資料から作り直すときは、**商務条件・固有名詞・数値・引用の文言を勝手に更新しない**。
出典が追えるように `<section data-src="...">` と HTML コメントを入れておく。

---

## 8. 検証

```bash
npm install                       # 初回のみ
npx playwright install chromium   # 初回のみ（ブラウザ本体）
npm run check                     # 既定の3ファイルを検証
node scripts/render.mjs starter.html gallery/pages.html   # 個別に指定も可
```

`npm run check` は本文の描画を検証する。

`scripts/render.mjs` は Chromium で実際に描画して、次を見る。

- スライドのキャンバス（1280 × 720）からのはみ出し
- 子要素の枠外（`枠外 <tag>.<class> 右+N` の形で出る）
- 画像の読み込み失敗（`naturalWidth === 0`）
- **文字の見切れ** — 「切り落とす箱にテキストが入っていて、実際に溢れている」かどうかで判定する。
  既製の class に限定していないので、自由設計のページも同じ基準で検査される。
  意図的に切り落としている箱には `data-clip="ok"` を付けると除外される
- `-webkit-line-clamp` の行数打ち切り、`text-overflow: ellipsis` の末尾省略
- console エラー、JS 例外（`pageerror`）、リクエスト失敗

出力は `review/shots/<name>-NN.png`（各スライドの実描画、2倍解像度）と `review/pdf/<name>.pdf`、
それに `review/report.json`。**問題が1件でもあればコマンドが非0で終了する**。
指定した HTML が無い場合、スライドが0枚の場合も失敗する。

既定の3ファイルは `scripts/render.mjs` の `DEFAULT_TARGETS` にある。
入口の `index.html` はスライドを持たないので既定には入っていない。

**画像は必ず目で見る。** 検証スクリプトが通っても、写真の切れ方や図の詰まりは数値では出ない。
全ページの強調が何の違いを示すかも確認し、理由のない差を揃える。強調の意味は個数や色の機械検査だけでは判定できない。

### PDF

ブラウザの印刷（`Cmd+P`）で 1280 × 720px = 960 × 540pt のページとして出る。
`@page` と `break-after: page` を入れてあるので、一覧表示からもプレゼン表示からも全ページ出力される。
背景（濃灰の章扉など）を出すには、印刷ダイアログで「背景のグラフィック」を有効にする。

---

## 9. 直すとき

修正は AI への指示で行う想定になっている。指示するときは次を伝えると早い。

- どのファイルの何枚目か（`data-src` かフッターのページ番号で指す）
- どう見えていて、どうなってほしいか
- 文言を変えてよいか、原資料に合わせて固定か

AI 側は、直したら必ず `npm run check` を通して `review/shots/` の画像を見る。
1つの資料だけの調整は資料固有 CSS で行える。

---

## 10. v3 / v2 との関係

**v3から継承したもの** — ブランドと視覚文法だけ。
色（theme1.xml の実値）、タイトル・罫・マークの定位置（タイトル y=33.2 / 灰罫 y=87.7 幅1164.3 / 赤罫 幅91.4 /
マーク x=1196 y=43.3 / 左余白 57.8）、表紙・目次・章扉の意匠、素材画像。
**継承していないもの** — PPTX の生成・結合手順、python-pptx のスクリプト、1枚1フォルダの運用、極小級数。

**v2から拾ったもの** — 考え方だけ。
16:9 固定キャンバス、印刷で1スライド=1ページにする作り、部品の粒度の目安。
白・ダーク・グレーを基本に強調を絞る配色、図を大きく置いて説明と組む構成、意味を担う元図版を残す移植の判断。
**CSS は1行も引き継いでいない。** v2 のテンプレートに依存しない。

このキットは `tool-pineal-slide-v2/templates/html/` に同梱され、`pineal-slide` スキルの既定になっている。リポジトリ直下で `npm run deck:new -- /保存先/slides/資料名` を実行すると、編集用HTML・共通CSS・ブランド画像・検証スクリプトを独立したフォルダへコピーできる。

