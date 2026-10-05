#!/bin/bash
# pineal スライド制作キットのセットアップ（Mac）
#   bash setup.sh
# キットを別の場所へ動かしたときも、もう一度実行する。
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd -P)"
cd "$KIT"
FAIL=0
ok()   { printf '  OK   %s\n' "$1"; }
ng()   { printf '  NG   %s\n' "$1"; FAIL=1; }
warn() { printf '  注意 %s\n' "$1"; }

echo "1/5 前提の確認"
if command -v node >/dev/null && [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 18 ]; then ok "Node.js $(node -v)"; else ng "Node.js 18 以上が必要です（brew install node）"; fi
if command -v python3 >/dev/null && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then ok "$(python3 -V 2>&1)"; else ng "Python 3.9 以上が必要です"; fi
for c in pdftoppm pdffonts; do
  if command -v "$c" >/dev/null; then ok "$c"; else ng "$c が必要です（brew install poppler）"; fi
done
if command -v rsvg-convert >/dev/null; then ok "rsvg-convert"; else ng "rsvg-convert が必要です（brew install librsvg）"; fi
if [ -d "/Applications/Microsoft PowerPoint.app" ]; then ok "Microsoft PowerPoint"; else ng "Microsoft PowerPoint が /Applications にありません"; fi
if command -v claude >/dev/null; then ok "Claude Code"; else warn "claude コマンドが見つかりません。Claude Code を入れてください"; fi
if [ -n "${GEMINI_API_KEY:-}" ]; then ok "GEMINI_API_KEY"; else warn "GEMINI_API_KEY が未設定です。イラストを作るときに設定してください（README の動作環境）"; fi
if ls ~/Library/Fonts /Library/Fonts 2>/dev/null | grep -qi 'NotoSansJP\|NotoSansCJKjp\|NotoSansCJK-'; then ok "Noto Sans JP"; else warn "Noto Sans JP が見つかりません。HTML はヒラギノで表示されます（brew install --cask font-noto-sans-jp）"; fi
if [ "$FAIL" != 0 ]; then
  echo "足りないものを入れてから、もう一度 bash setup.sh を実行してください。"
  exit 1
fi

echo "2/5 Python の仮想環境（.venv）"
[ -x .venv/bin/python3 ] || python3 -m venv .venv
.venv/bin/python3 -m pip install -q --disable-pip-version-check -r requirements.txt
ok "$(.venv/bin/python3 -c 'import pptx; print("python-pptx", pptx.__version__)')"

echo "3/5 HTML の検証環境（Playwright と Chromium）"
npm --prefix tool-pineal-slide-v2/templates/html ci --no-audit --no-fund --loglevel=error
npm --prefix tool-pineal-slide-v2/templates/html exec -- playwright install chromium
ok "Playwright"

echo "4/5 Claude Code のスキル（~/.claude/skills/pineal-slide）"
SK="$KIT/tool-pineal-slide-v2/.claude/skills/pineal-slide"
LINK="$HOME/.claude/skills/pineal-slide"
mkdir -p "$HOME/.claude/skills"
if [ -L "$LINK" ]; then
  case "$(readlink "$LINK")" in
    */tool-pineal-slide-v2/.claude/skills/pineal-slide) ln -sfn "$SK" "$LINK" ;;
    *) echo "  $LINK は別の場所へのリンクです（$(readlink "$LINK")）。退避してから再実行してください。"; exit 1 ;;
  esac
elif [ -e "$LINK" ]; then
  echo "  $LINK が既にあります（リンクではありません）。中身を確かめて退避してから再実行してください。"
  exit 1
else
  ln -s "$SK" "$LINK"
fi
ok "$LINK → $SK"

echo "5/5 動作確認"
.venv/bin/python3 - <<'EOF'
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / '.claude/skills/pineal-slide/pptx'))
import pptxlib
from pptx import Presentation
tpl = pptxlib.V3 / 'assets/pineal_temp.pptx'
assert tpl.exists(), f'テンプレがありません: {tpl}'
assert len(Presentation(str(tpl)).slides) == 16
print('  OK   pptxlib とテンプレ', pptxlib.V3)
EOF
npm --prefix tool-pineal-slide-v2/templates/html run --silent check:starter >/dev/null
ok "HTML の描画（starter.html）"

echo
echo "セットアップが終わりました。"
echo "  cd \"$KIT/work\" && claude"
