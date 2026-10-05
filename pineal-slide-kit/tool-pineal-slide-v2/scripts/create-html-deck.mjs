#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const kit = path.join(repo, 'templates/html');
const args = process.argv.slice(2);
if (args.length !== 1 || args[0].startsWith('--')) {
  console.error('Usage: node scripts/create-html-deck.mjs /path/to/project/slides/deck-name');
  process.exit(args[0] === '--help' ? 0 : 2);
}
const dest = path.resolve(args[0]);
if (fs.existsSync(dest)) {
  console.error(`作成先は既に存在します。上書きしません: ${dest}`);
  process.exit(2);
}
for (const name of ['starter.html', 'core', 'assets/brand', 'scripts/render.mjs', 'package-lock.json']) {
  if (!fs.existsSync(path.join(kit, name))) throw new Error(`テンプレートがありません: ${name}`);
}
fs.mkdirSync(path.dirname(dest), { recursive: true });
// Exclusive mkdir also protects a destination created after the check above.
fs.mkdirSync(dest);
for (const name of ['core', 'assets/brand']) {
  fs.cpSync(path.join(kit, name), path.join(dest, name), { recursive: true, force: false, errorOnExist: true });
}
fs.copyFileSync(path.join(kit, 'starter.html'), path.join(dest, 'index.html'), fs.constants.COPYFILE_EXCL);
fs.mkdirSync(path.join(dest, 'scripts'));
fs.copyFileSync(path.join(kit, 'scripts/render.mjs'), path.join(dest, 'scripts/render.mjs'));
const sourcePackage = JSON.parse(fs.readFileSync(path.join(kit, 'package.json'), 'utf8'));
const packageJson = {
  name: 'pineal-html-deck', version: '1.0.0', private: true, type: 'module',
  scripts: { check: 'node scripts/render.mjs index.html' },
  devDependencies: sourcePackage.devDependencies,
};
const lock = JSON.parse(fs.readFileSync(path.join(kit, 'package-lock.json'), 'utf8'));
lock.name = packageJson.name;
lock.packages[''].name = packageJson.name;
fs.writeFileSync(path.join(dest, 'package.json'), JSON.stringify(packageJson, null, 2) + '\n');
fs.writeFileSync(path.join(dest, 'package-lock.json'), JSON.stringify(lock, null, 2) + '\n');
fs.writeFileSync(path.join(dest, '.gitignore'), 'node_modules/\nreview/\n.DS_Store\n');
fs.writeFileSync(path.join(dest, 'README.md'), `# HTMLスライド\n\nindex.htmlを編集し、ブラウザで開きます。最初は6枚のスターターです。内容に合わせて差し替え、追加、削除してください。\n資料固有CSSはdeckクラスでスコープし、画像はassets/へ置きます。ロゴはassets/brand/とcore/の定義を使います。\n\n初回: npm ci と npx playwright install chromium\n検証・PDF出力: npm run check\n\nreview/shots/の各ページを目で確認してください。元資料がある場合は文章と図版をともに照合します。\nこのフォルダは元リポジトリなしで表示・編集・検証できます。\n`);
console.log(`作成しました: ${path.join(dest, 'index.html')}\n作成先で npm ci → npm run check を実行してください。`);
