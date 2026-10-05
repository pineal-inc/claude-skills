/* 全作例のブラウザ描画・検証・PDF出力
 *
 *   npm install            # 初回のみ（playwright をこのフォルダに入れる）
 *   npx playwright install chromium   # ブラウザ本体が無ければ
 *   node scripts/render.mjs [html ...]
 *
 * 出力: review/shots/<name>-NN.png / review/pdf/<name>.pdf / review/report.json
 * 問題を1件でも見つけたら終了コード 1 で落ちる（CI や再生成ループで拾えるように）。
 *
 * HTML を見るだけならこのスクリプトも Node も要らない。ブラウザで開けばよい。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

let chromium;
try {
  ({ chromium } = await import('playwright'));
} catch {
  console.error(
    'playwright が見つかりません。このフォルダで次を実行してください。\n' +
    '  npm install\n' +
    '  npx playwright install chromium'
  );
  process.exit(2);
}

// 既定の検証対象。スライドを持つ HTML だけを並べる。
// 入口の index.html はスライドを1枚も持たないので、ここには入れない。
const DEFAULT_TARGETS = [
  'starter.html',
  'gallery/blocks.html',
  'gallery/pages.html',
];

const args = process.argv.slice(2);
const targets = args.length ? args : DEFAULT_TARGETS;

if (!targets.length) {
  console.error('検証対象がありません。HTML のパスを引数で指定してください。');
  process.exit(2);
}
// 対象ファイルが無いのは常にエラー。既定の5ファイルも黙って読み飛ばさない。
const missing = targets.filter(f => !fs.existsSync(path.join(ROOT, f)));
if (missing.length) {
  console.error('次のファイルがありません: ' + missing.join(', '));
  process.exit(2);
}

const shots = path.join(ROOT, 'review/shots');
const pdfs = path.join(ROOT, 'review/pdf');
fs.mkdirSync(shots, { recursive: true });
fs.mkdirSync(pdfs, { recursive: true });

const browser = await chromium.launch();
const report = { generated: new Date().toISOString(), files: [] };
let failed = 0;

for (const rel of targets) {
  const name = rel.replace(/\//g, '-').replace(/\.html$/, '');
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 }, deviceScaleFactor: 2 });
  const consoleErrors = [];
  const pageErrors = [];
  const failedRequests = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', e => pageErrors.push(`${e.name}: ${e.message}`));
  page.on('requestfailed', r => failedRequests.push(`${r.url()} (${r.failure()?.errorText || 'failed'})`));
  await page.goto('file://' + path.join(ROOT, rel), { waitUntil: 'networkidle' });
  // ビューア由来の装飾（キャンバス右外のページ番号・ツールバー）は検証・撮影の対象外にする
  await page.addStyleTag({ content: ':root{--zoom:1 !important}.deck > .slide::after{display:none !important}.deck-bar{display:none !important}' });
  await page.evaluate(() => document.fonts.ready);

  const checks = await page.evaluate(() => {
    const cls = el => {
      const c = (el.getAttribute && el.getAttribute('class')) || '';
      return c ? '.' + c.trim().split(/\s+/)[0] : '';
    };
    const label = el => el.tagName.toLowerCase() + cls(el);
    const out = [];

    document.querySelectorAll('.deck > .slide').forEach((s, i) => {
      const r = s.getBoundingClientRect();
      const issues = [];

      // 1) スライド自身がスクロールしていないか（= 中身がキャンバスに収まっていない）
      if (s.scrollWidth > s.clientWidth + 1) issues.push(`横はみ出し ${s.scrollWidth - s.clientWidth}px`);
      if (s.scrollHeight > s.clientHeight + 1) issues.push(`縦はみ出し ${s.scrollHeight - s.clientHeight}px`);

      const all = s.querySelectorAll('*');

      // 2) 子要素がキャンバスの外へ出ていないか
      all.forEach(el => {
        const b = el.getBoundingClientRect();
        if (b.width === 0 && b.height === 0) return;
        const cs = getComputedStyle(el);
        if (cs.position === 'fixed' || cs.visibility === 'hidden' || cs.display === 'none') return;
        const over = [];
        if (b.right > r.right + 1) over.push(`右+${Math.round(b.right - r.right)}`);
        if (b.bottom > r.bottom + 1) over.push(`下+${Math.round(b.bottom - r.bottom)}`);
        if (b.left < r.left - 1) over.push(`左-${Math.round(r.left - b.left)}`);
        if (b.top < r.top - 1) over.push(`上-${Math.round(r.top - b.top)}`);
        if (over.length) issues.push(`枠外 ${label(el)} ${over.join(' ')}`);
      });

      // 3) 画像の読み込み失敗（img と CSS background-image の両方）
      s.querySelectorAll('img').forEach(img => {
        if (!img.complete || img.naturalWidth === 0) issues.push(`画像欠落 ${img.getAttribute('src')}`);
      });

      // 4) 文字の見切れ。class 名では絞らず、
      //    「テキストを持っていて、かつ自分で切り落としている箱」をすべて見る。
      //    - 装飾だけの図形（テキストを持たない div・SVG・画像）は対象外
      //    - 意図して切っている箱は data-clip="ok" を付ければ除外できる
      all.forEach(el => {
        if (el.closest('svg')) return;                       // 図形の中は別勘定
        if (el.hasAttribute('data-clip')) return;            // 明示的に許可された切り落とし
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') return;
        const clipsY = cs.overflowY !== 'visible';
        const clipsX = cs.overflowX !== 'visible';
        if (!clipsY && !clipsX) return;                      // 切らない箱は文字が消えない
        const text = (el.textContent || '').replace(/\s+/g, '');
        if (!text) return;                                   // 文字が無ければ飾り
        const dy = el.scrollHeight - el.clientHeight;
        const dx = el.scrollWidth - el.clientWidth;
        if (clipsY && dy > 2) issues.push(`文字見切れ ${label(el)} 下 +${dy}px`);
        if (clipsX && dx > 2) issues.push(`文字見切れ ${label(el)} 右 +${dx}px`);
      });

      // 5) 省略記号での打ち切り（text-overflow: ellipsis / -webkit-line-clamp）も
      //    「文が読めていない」ので拾う。意図的なら data-clip="ok" を付ける。
      all.forEach(el => {
        if (el.hasAttribute('data-clip')) return;
        const cs = getComputedStyle(el);
        if (cs.webkitLineClamp && cs.webkitLineClamp !== 'none') {
          if (el.scrollHeight > el.clientHeight + 2) issues.push(`行数打ち切り ${label(el)}`);
        } else if (cs.textOverflow === 'ellipsis' && el.scrollWidth > el.clientWidth + 2) {
          issues.push(`末尾省略 ${label(el)}`);
        }
      });

      out.push({ n: i + 1, id: s.id || null, issues: [...new Set(issues)] });
    });
    return out;
  });

  const slides = await page.$$('.deck > .slide');
  if (slides.length === 0) {
    console.error(`${rel}: .deck > .slide が1枚もありません`);
    report.files.push({ file: rel, slides: 0, error: 'スライドが0枚', consoleErrors, pageErrors, failedRequests, slidesWithIssues: [] });
    failed++;
    await page.close();
    continue;
  }
  for (let i = 0; i < slides.length; i++) {
    await slides[i].screenshot({ path: path.join(shots, `${name}-${String(i + 1).padStart(2, '0')}.png`) });
  }

  await page.emulateMedia({ media: 'print' });
  await page.pdf({
    path: path.join(pdfs, `${name}.pdf`),
    width: '1280px', height: '720px', printBackground: true,
    margin: { top: 0, right: 0, bottom: 0, left: 0 },
  });

  const withIssues = checks.filter(c => c.issues.length);
  report.files.push({ file: rel, slides: slides.length, consoleErrors, pageErrors, failedRequests, slidesWithIssues: withIssues });

  const bad = withIssues.length + consoleErrors.length + pageErrors.length + failedRequests.length;
  if (bad) failed++;
  console.log(
    `${rel}: ${slides.length} slides, ${withIssues.length} with issues, ` +
    `${consoleErrors.length} console errors, ${pageErrors.length} page errors, ${failedRequests.length} failed requests`
  );
  for (const s of withIssues) console.log(`  #${s.n}: ${s.issues.join(' / ')}`);
  for (const e of pageErrors) console.log(`  pageerror: ${e}`);
  for (const e of failedRequests) console.log(`  requestfailed: ${e}`);
  await page.close();
}

await browser.close();
fs.writeFileSync(path.join(ROOT, 'review/report.json'), JSON.stringify(report, null, 2));
console.log('→ review/report.json');
if (failed) {
  console.error(`検証で問題が見つかりました（${failed} ファイル）。review/report.json と review/shots を確認してください。`);
  process.exit(1);
}
