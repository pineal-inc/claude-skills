// Web ページやローカルの HTML を撮る。画面の切り出し、過去資料のサムネイルに使う。
//   node shot.mjs <URL または HTML のパス> <保存先.png> [--selector CSS] [--full] [--width 1400] [--height 900] [--scale 2] [--wait 1000]
//   --selector: その要素だけを撮る。--full: ページ全体を縦に長く撮る。どちらもなければ表示範囲だけ。
// playwright は templates/html/node_modules のものを使う（templates/html で npm ci 済みであること）。
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../..');
const { chromium } = createRequire(path.join(ROOT, 'templates/html/package.json'))('playwright');

const args = process.argv.slice(2);
const opt = { width: 1400, height: 900, scale: 2, wait: 1000, selector: null, full: false };
const pos = [];
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === '--full') opt.full = true;
  else if (a === '--selector') opt.selector = args[++i];
  else if (['--width', '--height', '--scale', '--wait'].includes(a)) opt[a.slice(2)] = Number(args[++i]);
  else pos.push(a);
}
if (pos.length !== 2) {
  console.error('使い方: node shot.mjs <URL または HTML のパス> <保存先.png> [--selector CSS] [--full] [--width 1400] [--height 900] [--scale 2] [--wait 1000]');
  process.exit(1);
}
const [src, out] = pos;
const url = /^(https?|file):/.test(src) ? src : pathToFileURL(path.resolve(src)).href;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: opt.width, height: opt.height }, deviceScaleFactor: opt.scale });
await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(opt.wait);
if (opt.selector) {
  const el = await page.$(opt.selector);
  if (!el) {
    console.error(`要素が見つかりません: ${opt.selector}`);
    await browser.close();
    process.exit(1);
  }
  await el.screenshot({ path: out });
} else {
  await page.screenshot({ path: out, fullPage: opt.full });
}
console.log('保存:', out);
await browser.close();
