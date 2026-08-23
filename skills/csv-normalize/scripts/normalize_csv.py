#!/usr/bin/env python3
"""広告媒体などのCSVを共通スキーマに正規化する。

使い方:
    python3 normalize_csv.py input.csv --map mapping.json --out normalized.csv

mapping.json の書式:
    {
      "encoding": "utf-8-sig",            // 省略時 utf-8-sig。Shift_JIS系は "cp932"
      "columns": {                        // 入力列名 → 共通スキーマ列名
        "日付": "date",
        "キャンペーン名": "campaign",
        "表示回数": "impressions",
        "クリック数": "clicks",
        "費用": "cost",
        "CV数": "conversions"
      },
      "constants": {"media": "サンプル媒体A"},  // 全行に固定値で入れる列
      "date_formats": ["%Y/%m/%d", "%Y-%m-%d"]  // date列の解釈候補(先勝ち)
    }

共通スキーマ(出力列・この順):
    date, media, campaign, impressions, clicks, cost, conversions

- date は YYYY-MM-DD に統一する
- 数値列は「¥」「,」「%」「円」と空白を除去してから整数/実数として検証する
- 解釈できない行は行番号つきでstderrに列挙し、終了コード1で終わる(出力は書かない)

依存: Python 3.9+ 標準ライブラリのみ。
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SCHEMA = ["date", "media", "campaign", "impressions", "clicks", "cost", "conversions"]
NUMERIC = {"impressions", "clicks", "cost", "conversions"}
DEFAULT_DATE_FORMATS = ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%m/%d/%Y"]
NUM_STRIP = re.compile(r"[¥￥,%円\s]")


def clean_number(raw: str):
    s = NUM_STRIP.sub("", raw)
    if s == "":
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    return int(f) if f.is_integer() else f


def parse_date(raw: str, formats):
    s = raw.strip()
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="CSVを共通スキーマに正規化する")
    ap.add_argument("input", help="入力CSV")
    ap.add_argument("--map", required=True, dest="mapping", help="列マッピング定義(JSON)")
    ap.add_argument("--out", required=True, help="出力CSV(UTF-8)")
    args = ap.parse_args()

    mapping = json.loads(Path(args.mapping).read_text(encoding="utf-8"))
    columns = mapping.get("columns", {})
    constants = mapping.get("constants", {})
    encoding = mapping.get("encoding", "utf-8-sig")
    date_formats = mapping.get("date_formats", DEFAULT_DATE_FORMATS)

    covered = set(columns.values()) | set(constants.keys())
    missing = [c for c in SCHEMA if c not in covered]
    if missing:
        print(f"エラー: マッピングに共通スキーマ列が足りない: {', '.join(missing)}", file=sys.stderr)
        return 1

    with open(args.input, encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        unknown = [src for src in columns if src not in header]
        if unknown:
            print(f"エラー: 入力CSVに列が見つからない: {', '.join(unknown)}", file=sys.stderr)
            print(f"  入力の列: {', '.join(header)}", file=sys.stderr)
            return 1

        rows, errors = [], []
        for lineno, row in enumerate(reader, start=2):
            out = dict(constants)
            for src, dst in columns.items():
                out[dst] = (row.get(src) or "").strip()
            date = parse_date(out["date"], date_formats)
            if date is None:
                errors.append(f"  {lineno}行目: dateを解釈できない: {out['date']!r}")
                continue
            out["date"] = date
            ok = True
            for col in NUMERIC:
                val = clean_number(str(out[col]))
                if val is None:
                    errors.append(f"  {lineno}行目: {col}が数値でない: {out[col]!r}")
                    ok = False
                else:
                    out[col] = val
            if ok:
                rows.append(out)

    if errors:
        print(f"エラー: {len(errors)}件の行を解釈できなかった(出力は書いていない)", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
        return 1

    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA)
        writer.writeheader()
        writer.writerows(rows)
    print(f"OK: {len(rows)}行を正規化 → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
