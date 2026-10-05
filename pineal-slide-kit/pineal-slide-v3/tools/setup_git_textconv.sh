#!/usr/bin/env bash
# Office(xlsx/xlsm/docx/pptx) の git diff を「読める化」する設定をこのリポジトリに適用する。
#   - tools/ にある *_textconv.py を検出
#   - .gitattributes に diff 指定を追記（重複は足さない）
#   - .git/config に diff.<type>.textconv を設定（ローカル設定。コミットされないので clone 後に再実行する）
# 使い方: リポジトリのルートで  bash tools/setup_git_textconv.sh
set -e

# リポジトリルートへ
cd "$(git rev-parse --show-toplevel)"

ATTR=".gitattributes"
touch "$ATTR"

add_attr() { # $1=pattern $2=difftype
  if ! grep -qiE "^\s*$1\s+diff=$2\s*$" "$ATTR" 2>/dev/null; then
    printf '%s diff=%s\n' "$1" "$2" >> "$ATTR"
  fi
}

if [ -f tools/xlsx_textconv.py ]; then
  add_attr '*.xlsx' xlsx ; add_attr '*.xlsm' xlsx
  git config diff.xlsx.textconv 'python3 tools/xlsx_textconv.py'
  git config diff.xlsx.cachetextconv true
  echo "✓ xlsx/xlsm textconv 設定"
fi
if [ -f tools/docx_textconv.py ]; then
  add_attr '*.docx' docx
  git config diff.docx.textconv 'python3 tools/docx_textconv.py'
  git config diff.docx.cachetextconv true
  echo "✓ docx textconv 設定"
fi
if [ -f tools/pptx_textconv.py ]; then
  add_attr '*.pptx' pptx
  git config diff.pptx.textconv 'python3 tools/pptx_textconv.py'
  git config diff.pptx.cachetextconv true
  echo "✓ pptx textconv 設定"
fi

echo "完了。 git diff / git log -p で Office ファイルの差分が読めるようになりました。"
