> 適用先: 旧HTML → PPTX方式の参照資料。通常の新規作成は [現HTMLキット](../../../../templates/html/README.md) を使う。現HTML方式の基準本文級数は15pxで、旧CSS・DOM契約・文字数上限は適用しない。色の強調や図の見せ方は内容に合わせて判断する。

# Pineal コンポーネントリファレンス v2

> **配色は正本による**: 既定色・赤系の閉じた列挙・使用条件は
> 配色の正本 `pineal-slide/references/style-guide.md` の「カラールール」が定義する。ここには値も条件も再掲しない。


> **v1 からの変更**: Marp `<section>` → 独立 HTML ファイル、CSS 変数 → 直値、Grid → Flex

## スライドの契約（pineal-v2.1）

> **見出し・本文の文体の正本（必読）** → `~/.claude/rules/document-tone-rules.md`

ルート要素には `data-slide-type` と `data-contract-version="pineal-v2.1"` を付ける。

| `data-slide-type` | ルート要素 |
|---|---|
| `content` | `<div class="slide" ...>` |
| `cover` | `<div class="slide-dark title-slide" ...>` |
| `section` | `<div class="slide-dark section-divider" ...>` |
| `cta` | `<div class="slide-dark cta-slide" ...>` |
| `toc` | `<div class="slide" ...>` + `.agenda` |

上は生成時に書く root の形。**契約の条件（class の併記要件、種別ごとの `p.lead` の件数、
`.lead` 自身の条件、Fail になる状態）は `pineal-validate/skill.md` の Phase 0 が定義する。
ここには再掲しない。**

### コンポーネントに使える縦の高さ

`.slide` の内側は 405 − 48（上パディング） − 32（下パディング） = **325pt**。
ここから見出し群を引いた残りがコンポーネントの可用高になる。

| 構成 | 可用高 |
|---|---|
| h1 + `.lead` + h2 + `.h2-line` | **230.8pt** |
| h1 + `.lead`（h2 なし） | **265pt** |

内訳: h1-bar 34pt / `.lead` 26pt / h2 23.2pt / `.h2-line` 11pt。
可用高を超える構成にしない。超える場合はスライドを分割する。

検査は**コンポーネント自身の bbox 高**で行う（スライド下端405pt に収まっているかではない）。
手順とフィクスチャは `tests/heading-fixtures/README.md` の「可用高の測り方」を参照。

`.lead` の行数による可用高の分岐は置かない。理由は2つある。
`.lead` は 12pt・幅624pt のため、Phase 0 の字数上限いっぱいでも HTML 上1行にしかならない
（上限値は Phase 0 が定義する。ここでは1行として 26pt を計上する）。
また `scripts/html2pptx.js` は各要素を HTML の bbox 由来の絶対座標で配置するため、
PPTX 側で `.lead` が折り返しても後続コンポーネントの座標は動かない。
契約内では `.lead` は常に26ptとして扱ってよい。

### 本文エリアの占有規律（2026-08-25 制定）

図・コンポーネント群は本文エリアを埋める。中央に小さく浮かせない。

- 図を全幅で1つ置くスライドでは、図の幅は本文幅 624pt の **90%以上**、bbox 高は可用高の **70%以上** を目安にする
- 満たせない場合の対応は**縮小や余白での辻褄合わせではなく**、次のいずれか:
  - 左右2分割にして片側を図で全面占有する（レシピ「左右2分割」参照）
  - スライドを分割して図を大きく保つ（複数の図を1枚に詰めない）
  - ノードのパディング・文字級数を上げて図自体を可用高まで育てる
- 図が可用高より低い場合の縦配置は上下中央でなく**上寄せ**とし、余りには出典・補足（`p.sub` 相当）を置くか、そのまま下余白にする
- 結論・キーメッセージを本文エリアの下部に置かない。結論は `.lead` に書く

根拠: 実務標準の調査（2026-08-25）。本文はスライド面積の約70%、図は詰めずに分割して大きく保つ、
結論は下部に置かない（投影時に視界が遮られる）、が決算説明・コンサル型資料の共通則。

## 目次

> 新規スライドで使えるのは 24種。**8番と26番は legacy 専用**で、新規では選ばない。

### 基本コンポーネント
1. [タイトルスライド](#1-タイトルスライド)
2. [2カラムグリッド（grid-2）](#2-2カラムグリッド)
3. [3カラムグリッド（grid-3）](#3-3カラムグリッド)
4. [4カラムグリッド（grid-4）](#4-4カラムグリッド)
5. [featureカード](#5-featureカード)
6. [Before / After カード](#6-before--after-カード)
7. [プロセスフロー](#7-プロセスフロー)
8. [ダッシュボード（数値強調）](#8-ダッシュボード) **legacy 専用。新規では使わない**
9. [棒グラフ（ROI比較）](#9-棒グラフ)
10. [比較テーブル](#10-比較テーブル)
11. [画像プレースホルダー付きレイアウト](#11-画像プレースホルダー付きレイアウト)

### 拡張コンポーネント
12. [セクションディバイダー](#12-セクションディバイダー)
13. [CTA / クロージングスライド](#13-cta--クロージングスライド)
14. [タグ / バッジ](#14-タグ--バッジ)
15. [番号付きカード](#15-番号付きカード)
16. [テスティモニアル（引用）](#16-テスティモニアル)
17. [ケーススタディ（人物比較）](#17-ケーススタディ)
18. [バブル比較](#18-バブル比較)
19. [タイムライン](#19-タイムライン)
20. [結果ハイライト帯](#20-結果ハイライト帯)
21. [フォトギャラリー](#21-フォトギャラリー)
22. [マルチセクションレイアウト](#22-マルチセクションレイアウト)
23. [目次 / アジェンダ](#23-目次--アジェンダ)
24. [画像オーバーレイ](#24-画像オーバーレイ)
25. [アイコングリッド](#25-アイコングリッド)
26. [ハイライトボックス](#26-ハイライトボックス) **legacy 専用。新規では使わない**

---

## 1. タイトルスライド

**用途**: 最初のスライド（ダーク背景）

```html
<div class="slide-dark title-slide" data-slide-type="cover" data-contract-version="pineal-v2.1">
  <div class="title-brand"><img src="images/pineal-logo-dark.png" alt="pineal"></div>
  <div class="h1-bar">
    <div class="h1-accent"></div>
    <h1>メインタイトル</h1>
  </div>
  <p style="font-size: 14pt; color: rgba(255,255,255,0.6); margin-top: 12pt;">サブタイトル</p>
  <p style="font-size: 10pt; color: rgba(255,255,255,0.4); margin-top: 24pt;">2026年4月・会社名</p>
</div>
```

---

## 2. 2カラムグリッド

**用途**: 2つの対等な情報を並べる（比較・特徴x2・左右レイアウト）

```html
<div class="h1-bar">
  <div class="h1-accent"></div>
  <h1>スライドの見出し</h1>
</div>
<p class="lead">このスライドの結論（分量の契約は Phase 0）</p>
<h2>サブタイトル（文脈）</h2>
  <div class="h2-line"></div>
<div class="grid-2">
  <div class="card">
    <h3>左側タイトル</h3>
    <p>説明テキスト</p>
  </div>
  <div class="card">
    <h3>右側タイトル</h3>
    <p>説明テキスト</p>
  </div>
</div>
```

---

## 3. 3カラムグリッド

**用途**: 3つの並列情報（3つの特徴・3つの事例・3つの声）

```html
<div class="h1-bar">
  <div class="h1-accent"></div>
  <h1>スライドの見出し</h1>
</div>
<p class="lead">このスライドの結論（分量の契約は Phase 0）</p>
<h2>サブタイトル</h2>
  <div class="h2-line"></div>
<div class="grid-3">
  <div class="card feature">
    <p style="font-size: 20pt; margin-bottom: 6pt;">🎯</p>
    <h3>項目1</h3>
    <p>説明テキスト</p>
  </div>
  <div class="card feature">
    <p style="font-size: 20pt; margin-bottom: 6pt;">🚀</p>
    <h3>項目2</h3>
    <p>説明テキスト</p>
  </div>
  <div class="card feature">
    <p style="font-size: 20pt; margin-bottom: 6pt;">💡</p>
    <h3>項目3</h3>
    <p>説明テキスト</p>
  </div>
</div>
```

---

## 4. 4カラムグリッド

**用途**: 4つの並列情報（機能一覧・ステータスx4）

```html
<div class="h1-bar">
  <div class="h1-accent"></div>
  <h1>スライドの見出し</h1>
</div>
<p class="lead">このスライドの結論（分量の契約は Phase 0）</p>
<div class="grid-4">
  <div class="card feature">
    <h3>項目1</h3>
    <p style="font-size: 8pt;">説明テキスト</p>
  </div>
  <div class="card feature">
    <h3>項目2</h3>
    <p style="font-size: 8pt;">説明テキスト</p>
  </div>
  <div class="card feature">
    <h3>項目3</h3>
    <p style="font-size: 8pt;">説明テキスト</p>
  </div>
  <div class="card feature">
    <h3>項目4</h3>
    <p style="font-size: 8pt;">説明テキスト</p>
  </div>
</div>
```

---

## 5. featureカード

**用途**: 並列項目のカード（上部に 1pt 罫線 + 淡背景）。色は配色の正本による

```html
<div class="card feature">
  <h3>カードタイトル</h3>
  <p>説明テキスト</p>
  <ul>
    <li>ポイント1</li>
    <li>ポイント2</li>
  </ul>
</div>
```

---

## 6. Before / After カード

**用途**: 変革前後の比較（課題→解決策、現状→理想）

```html
<div class="h1-bar">
  <div class="h1-accent"></div>
  <h1>内製化とベンダー発注のコスト比較</h1>
</div>
<p class="lead">内製化の費用はベンダー発注の約5分の1になります。</p>
<h2>導入前後の比較</h2>
  <div class="h2-line"></div>
<div class="grid-2">
  <div class="card before">
    <h3>Before</h3>
    <ul>
      <li>課題1</li>
      <li>課題2</li>
      <li>課題3</li>
    </ul>
  </div>
  <div class="card after">
    <h3>After</h3>
    <p style="font-weight: bold; margin-bottom: 6pt;">インパクトの一言</p>
    <ul>
      <li>成果1</li>
      <li>成果2</li>
      <li>成果3</li>
    </ul>
  </div>
</div>
```

---

## 7. プロセスフロー

**用途**: 手順・ステップ・時系列（矢印型のフロー）

```html
<div class="h1-bar">
  <div class="h1-accent"></div>
  <h1>導入の手順</h1>
</div>
<p class="lead">ヒアリングから運用開始までを3つの工程で進めます。</p>
<h2>導入プロセス</h2>
  <div class="h2-line"></div>
<div class="flow-container">
  <div class="flow-step">
    <h4 style="margin: 0; font-size: 9pt; font-weight: 900; color: white;">Step 1</h4>
    <p style="margin: 3pt 0 0; font-size: 8pt; color: rgba(255,255,255,0.9);">ヒアリング</p>
  </div>
  <div class="flow-step">
    <h4 style="margin: 0; font-size: 9pt; font-weight: 900; color: white;">Step 2</h4>
    <p style="margin: 3pt 0 0; font-size: 8pt; color: rgba(255,255,255,0.9);">設計・開発</p>
  </div>
  <div class="flow-step active">
    <h4 style="margin: 0; font-size: 9pt; font-weight: 900; color: white;">Step 3</h4>
    <p style="margin: 3pt 0 0; font-size: 8pt; color: rgba(255,255,255,0.9);">運用開始</p>
  </div>
</div>
```

---

## 8. ダッシュボード

> **legacy 専用。新規スライドでは使わない**。数字の見せ方の正本は
> `~/.claude/rules/document-tone-rules.md`「表記の共通ルール」であり、規則はここに再掲しない。
> 新規での見せ方は正本による。以下は既存資料を保守するときの参照用として残す。

**用途**: KPI・数値インパクト・実績の強調表示

```html
<div class="h1-bar">
  <div class="h1-accent"></div>
  <h1>工数削減の実績</h1>
</div>
<p class="lead">導入から3か月で月あたり80時間を削減しました。</p>
<h2>主要KPI</h2>
  <div class="h2-line"></div>
<div class="dashboard">
  <div class="stat-item">
    <p class="stat-num">80<small style="font-size: 14pt;">h</small></p>
    <p class="stat-desc">月間削減時間</p>
  </div>
  <div class="stat-item">
    <p class="stat-num">15<small style="font-size: 14pt;">+</small></p>
    <p class="stat-desc">生成ツール数</p>
  </div>
  <div class="stat-item">
    <p class="stat-num">3x</p>
    <p class="stat-desc">生産性向上</p>
  </div>
</div>
```

---

## 9. 棒グラフ

**用途**: コスト比較・割合の視覚化

```html
<div class="bar-chart">
  <div class="bar-row">
    <div class="bar-label">
      <p>外部ベンダー発注</p>
      <p>200万円</p>
    </div>
    <div class="bar-track">
      <div class="bar-fill costly"><p style="color: white; font-size: 8pt; font-weight: 700;">200万円</p></div>
    </div>
  </div>
  <div class="bar-row">
    <div class="bar-label">
      <p>内製化</p>
      <p>120万円</p>
    </div>
    <div class="bar-track">
      <div class="bar-fill saving"><p style="color: white; font-size: 8pt; font-weight: 700;">120万円</p></div>
    </div>
  </div>
</div>
```

---

## 10. 比較テーブル

**用途**: 機能比較・仕様・スペック

> **注意**: `<table>` / `<tr>` / `<th>` / `<td>` に background や border を直接指定すると
> html2pptx でエラーになる。div + flex で擬似テーブルを構築する。

```html
<!-- ヘッダー行 -->
<div style="display: flex; background: #1C1A1A; border-radius: 4pt 4pt 0 0;">
  <div style="flex: 1; padding: 8pt 12pt;"><p style="color: white; font-size: 9pt; font-weight: 700;">比較項目</p></div>
  <div style="flex: 1; padding: 8pt 12pt;"><p style="color: white; font-size: 9pt; font-weight: 700; text-align: center;">従来手法</p></div>
  <div style="flex: 1; padding: 8pt 12pt; background: #1C1A1A;"><p style="color: white; font-size: 9pt; font-weight: 700; text-align: center;">Pineal Slide</p></div>
</div>
<!-- データ行 -->
<div style="display: flex; border-bottom: 1pt solid #eee;">
  <div style="flex: 1; padding: 8pt 12pt;"><p style="font-size: 9pt; font-weight: 700;">作成時間</p></div>
  <div style="flex: 1; padding: 8pt 12pt;"><p style="font-size: 9pt; text-align: center;">3〜5時間</p></div>
  <div style="flex: 1; padding: 8pt 12pt;"><p style="font-size: 9pt; text-align: center; font-weight: 700;">15分</p></div>
</div>
```

---

## 11. 画像プレースホルダー付きレイアウト

**用途**: ツール画面・図・写真を入れるスライド

```html
<div class="grid-2">
  <div>
    <div class="card feature">
      <h3>説明タイトル</h3>
      <ul style="line-height: 1.8;">
        <li>ポイント1</li>
        <li>ポイント2</li>
      </ul>
    </div>
  </div>
  <div style="background: #e0e0e0; border-radius: 6pt; display: flex; align-items: center; justify-content: center; min-height: 200pt;">
    <p style="color: #888;">[ここに画像を挿入]</p>
  </div>
</div>
```

---

## 12. セクションディバイダー

**用途**: 章の区切り。ダーク背景で一呼吸置く。

完成形（style 込みの standalone）は `pineal-slide/SKILL.md` の
「セクションディバイダー」が正本。ここには構造だけを示す。

```html
<div class="slide-dark section-divider" data-slide-type="section" data-contract-version="pineal-v2.1">
  <div class="title-brand"><img src="images/pineal-logo-dark.png" alt="pineal"></div>
  <p class="section-num">02</p>
  <div class="h1-bar">
    <div class="h1-accent"></div>
    <h1>章題</h1>
  </div>
</div>
```

ロゴ（`.title-brand`）と章番号（`.section-num`）を置く。説明文は置かない。
`.lead` の可否は Phase 0 の契約表による。

---

## 13. CTA / クロージングスライド

**用途**: 最後のスライド。お問い合わせ・次のアクションを促す。

完成形（style 込みの standalone）は `pineal-slide/SKILL.md` の
「ダークスライド（表紙 / セクション扉 / CTA）」が正本。ここには構造だけを示す。

```html
<div class="slide-dark cta-slide" data-slide-type="cta" data-contract-version="pineal-v2.1">
  <div class="title-brand"><img src="images/pineal-logo-dark.png" alt="pineal"></div>
  <div class="h1-bar">
    <div class="h1-accent"></div>
    <h1>次の打ち合わせで決めること</h1>
  </div>
  <p class="cta-body">次アクション（決定事項・依頼事項）。文体は正本による</p>
  <p class="cta-contact">株式会社ピネアル</p>
</div>
```

表紙・章扉と同じ左寄せにする。中央寄せにしない。
`.cta-button`（赤ベタのボタン）は CSS に残っているが**使わない**（例外を設けない）。
理由は配色の正本 `style-guide.md` の「カラールール」による（条件はここに再掲しない）。
次アクションは `.cta-body` に書く（文体の条件は正本）。

---

## 14. タグ / バッジ

**用途**: カテゴリ分類、ステータス表示。他コンポーネントと組み合わせて使う。

```html
<div class="tags">
  <div class="tag primary"><p style="color: white; font-size: 7pt; font-weight: 700;">AI活用</p></div>
  <div class="tag outline"><p style="color: #1C1A1A; font-size: 7pt; font-weight: 700;">ノーコード</p></div>
  <div class="tag muted"><p style="color: #666; font-size: 7pt; font-weight: 700;">社内向け</p></div>
</div>
```

---

## 15. 番号付きカード

**用途**: 順序のある3〜4項目

```html
<div class="grid-3">
  <div class="numbered-card">
    <div class="number-badge">
      <p style="color: white; font-size: 12pt; font-weight: 900;">1</p>
    </div>
    <h3>要件定義力</h3>
    <p>現場の声をシステムで実現するための設計スキル</p>
  </div>
  <div class="numbered-card">
    <div class="number-badge">
      <p style="color: white; font-size: 12pt; font-weight: 900;">2</p>
    </div>
    <h3>実装力</h3>
    <p>アイデアを形にするノーコード開発スキル</p>
  </div>
  <div class="numbered-card">
    <div class="number-badge">
      <p style="color: white; font-size: 12pt; font-weight: 900;">3</p>
    </div>
    <h3>推進力</h3>
    <p>社内DXを主導するリーダーシップ</p>
  </div>
</div>
```

---

## 16. テスティモニアル

**用途**: 顧客の声、参加者の感想。

```html
<div class="testimonial">
  <p class="quote-mark">"</p>
  <p>ここに参加者の感想を1〜2文で入れる（見本の文）</p>
  <p style="font-size: 8pt; color: #939292; margin-top: 6pt;">Aさん（営業部門）</p>
</div>
```

---

## 17. ケーススタディ

**用途**: 人物別の事例比較

```html
<div class="grid-2">
  <div class="case-study">
    <div class="case-header">
      <p style="color: white; font-size: 10pt; font-weight: 700;">Aさん（営業部門）</p>
    </div>
    <div class="case-body">
      <p class="case-label">背景</p>
      <p style="font-size: 8pt;">背景を1文で書く（見本の文）</p>
      <p class="case-label">取り組み</p>
      <p style="font-size: 8pt;">取り組みを1文で書く（見本の文）</p>
    </div>
    <div class="case-result">
      <p style="color: white; font-size: 9pt; font-weight: 700;">結果を1文で書く（見本の文）</p>
    </div>
  </div>
  <!-- 2人目も同様 -->
</div>
```

---

## 18. バブル比較

**用途**: 金額・規模の大きさ比較（円のサイズで直感的に表現）

```html
<div class="bubble-compare">
  <div>
    <div class="bubble xl">
      <p style="color: white; font-size: 18pt; font-weight: 900;">300万</p>
      <p style="color: rgba(255,255,255,0.8); font-size: 7pt;">円/年</p>
    </div>
    <p style="text-align: center; font-size: 9pt; font-weight: 700; margin-top: 6pt;">新規採用</p>
  </div>
  <div>
    <div class="bubble lg">
      <p style="color: white; font-size: 16pt; font-weight: 900;">200万</p>
    </div>
    <p style="text-align: center; font-size: 9pt; font-weight: 700; margin-top: 6pt;">外注開発</p>
  </div>
  <div>
    <div class="bubble sm">
      <p style="color: white; font-size: 14pt; font-weight: 900;">120万</p>
    </div>
    <p style="text-align: center; font-size: 9pt; font-weight: 700; margin-top: 6pt;">社内育成</p>
  </div>
</div>
```

---

## 19. タイムライン

**用途**: ロードマップ、スケジュール、プロジェクトの進行

```html
<div class="timeline">
  <div class="timeline-line"></div>
  <div class="timeline-item">
    <div class="timeline-dot active"></div>
    <h4 style="font-size: 9pt; color: #1C1A1A; margin: 0 0 2pt;">Month 1</h4>
    <p style="font-size: 8pt;">AI基礎リテラシー</p>
  </div>
  <div class="timeline-item">
    <div class="timeline-dot"></div>
    <h4 style="font-size: 9pt; color: #1C1A1A; margin: 0 0 2pt;">Month 2</h4>
    <p style="font-size: 8pt;">エージェント構築</p>
  </div>
  <div class="timeline-item">
    <div class="timeline-dot"></div>
    <h4 style="font-size: 9pt; color: #939292; margin: 0 0 2pt;">Month 3</h4>
    <p style="font-size: 8pt;">自社ツール開発</p>
  </div>
</div>
```

---

## 20. 結果ハイライト帯

**用途**: 成果を目立たせる帯。カードやケーススタディの後に配置。

```html
<div class="result-strip">
  <div class="result-label">
    <p style="color: #1C1A1A; font-size: 7pt; font-weight: 900;">結果</p>
  </div>
  <p style="color: white; font-size: 10pt; font-weight: 700;">結果を1文で書く（見本の文）</p>
</div>
```

---

## 21. フォトギャラリー

**用途**: 研修風景、製品写真、実績スクリーンショット

```html
<div class="gallery">
  <div class="gallery-item">
    <p style="color: #888; font-size: 8pt;">写真1</p>
    <div class="gallery-caption">
      <p style="color: white; font-size: 7pt;">講義中の様子</p>
    </div>
  </div>
  <div class="gallery-item">
    <p style="color: #888; font-size: 8pt;">写真2</p>
    <div class="gallery-caption">
      <p style="color: white; font-size: 7pt;">グループワーク</p>
    </div>
  </div>
</div>
```

---

## 22. マルチセクションレイアウト

**用途**: 1枚に概要・特長・カリキュラムなど複数セクションを配置

```html
<div class="multi-section cols-2-1">
  <div>
    <div class="section-block">
      <div class="section-label">
        <p style="color: white; font-size: 7pt; font-weight: 700;">概要</p>
      </div>
      <p style="font-size: 8pt;">時間：◯時間x◯日間 / 形式：◯◯ / 定員：◯名</p>
    </div>
    <div class="section-block" style="margin-top: 8pt;">
      <div class="section-label primary">
        <p style="color: white; font-size: 7pt; font-weight: 700;">カリキュラム</p>
      </div>
      <p style="font-size: 8pt;"><strong>Phase 1</strong> AI基礎</p>
      <p style="font-size: 8pt;"><strong>Phase 2</strong> エージェント構築</p>
    </div>
  </div>
  <div>
    <div class="section-block">
      <div class="section-label">
        <p style="color: white; font-size: 7pt; font-weight: 700;">特長</p>
      </div>
      <p style="font-size: 8pt;">実際に組織課題を動かせる人材を育てる研修</p>
    </div>
  </div>
</div>
```

---

## 23. 目次 / アジェンダ

**用途**: プレゼンの構成を示す。現在のセクションをハイライト可能。
ルート要素は `<div class="slide" data-slide-type="toc" data-contract-version="pineal-v2.1">`。`.lead` の可否は Phase 0 の契約表による。

```html
<div class="agenda">
  <div class="agenda-item current">
    <p class="agenda-num">01</p>
    <div>
      <h3>会社紹介</h3>
      <p style="font-size: 8pt; color: #939292;">ピネアルの事業概要</p>
    </div>
  </div>
  <div class="agenda-item">
    <p class="agenda-num">02</p>
    <div>
      <h3>課題と解決策</h3>
      <p style="font-size: 8pt; color: #939292;">スライド作成の現状と改善提案</p>
    </div>
  </div>
  <div class="agenda-item">
    <p class="agenda-num">03</p>
    <div>
      <h3>デモンストレーション</h3>
      <p style="font-size: 8pt; color: #939292;">Pineal Slide の実演</p>
    </div>
  </div>
</div>
```

---

## 24. 画像オーバーレイ

**用途**: 画像の上にテキストを重ねるレイアウト

```html
<div class="grid-2">
  <div class="image-overlay">
    <div class="overlay-content">
      <h3 style="color: white;">プロジェクト名</h3>
      <p style="color: rgba(255,255,255,0.8); font-size: 8pt;">コーポレートサイト制作</p>
    </div>
  </div>
</div>
```

---

## 25. アイコングリッド

**用途**: 機能一覧、サービスメニュー、カテゴリ概要

```html
<div class="icon-grid">
  <div class="icon-grid-item">
    <p class="icon-emoji">💬</p>
    <h4 style="font-size: 9pt; color: #1C1A1A; margin: 0 0 2pt;">Chatbot活用</h4>
    <p style="font-size: 7pt; color: #939292;">AI対話の基礎から応用まで</p>
  </div>
  <div class="icon-grid-item">
    <p class="icon-emoji">⚙️</p>
    <h4 style="font-size: 9pt; color: #1C1A1A; margin: 0 0 2pt;">ワークフロー構築</h4>
    <p style="font-size: 7pt; color: #939292;">Dify・GASの実践</p>
  </div>
</div>
```

---

## 26. ハイライトボックス

> **legacy 専用。新規スライドでは使わない**。数字の見せ方の正本は
> `~/.claude/rules/document-tone-rules.md`「表記の共通ルール」であり、規則はここに再掲しない。
> 新規での見せ方は正本による。以下は既存資料を保守するときの参照用として残す。

**用途**: 1つの数値や結論を大きく強調

```html
<div class="grid-3">
  <div class="highlight-box">
    <p style="font-size: 24pt; font-weight: 900; color: #1C1A1A;">15<small style="font-size: 12pt;">分</small></p>
    <p style="font-size: 8pt; color: #939292;">平均作成時間</p>
  </div>
  <div class="highlight-box">
    <p style="font-size: 24pt; font-weight: 900; color: #1C1A1A;">26</p>
    <p style="font-size: 8pt; color: #939292;">レイアウトパターン</p>
  </div>
  <div class="highlight-box">
    <p style="font-size: 24pt; font-weight: 900; color: #1C1A1A;">0<small style="font-size: 12pt;">円</small></p>
    <p style="font-size: 8pt; color: #939292;">追加デザインコスト</p>
  </div>
</div>
```

---

## コンポーネントの組み合わせパターン

### パターン1: 実績の表 + 結果ハイライト
```html
<table><!-- 指標と実測値を並べる --></table>
<div class="result-strip">
  <div class="result-label"><p style="color: #1C1A1A; font-size: 7pt; font-weight: 900;">総括</p></div>
  <p style="color: white; font-size: 10pt; font-weight: 700;">全指標が目標を上回りました</p>
</div>
```
（`.dashboard` は legacy 専用。新規での見せ方は正本「表記の共通ルール」による）

### パターン2: ケーススタディ + タグ
ケーススタディの case-body 内にタグを配置。

### パターン3: タイムライン + 番号付きカード
タイムラインで全体像 → 各フェーズを番号付きカードで詳細化（複数スライド）。
