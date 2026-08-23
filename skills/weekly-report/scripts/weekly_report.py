#!/usr/bin/env python3
"""正規化済みCSVから週次レポート(集計CSV + Markdown)を作る。

使い方:
    python3 weekly_report.py normalized-a.csv normalized-b.csv --out-dir report/

入力: csv-normalize skill の共通スキーマCSV
    date(YYYY-MM-DD), media, campaign, impressions, clicks, cost, conversions

出力(--out-dir 配下):
    weekly_summary.csv  週(月曜開始)×媒体の集計 + CTR/CVR/CPA
    report.md           週次合計の推移、直近週の前週差分、媒体別構成比

- 週は月曜開始。週ラベルは週初日の日付(YYYY-MM-DD)
- 前週差分は「直近週のちょうど7日前の暦週」と比較する。その週のデータが無い場合は
  差分を出力せず、欠けている旨を書く(離れた週同士を前週として比較しない)
- CTR = clicks/impressions, CVR = conversions/clicks, CPA = cost/conversions
  (分母0のときは空欄にする。0で埋めない)
- 数値の解釈・示唆の文章は出力しない。判断材料になる数表までを作る

依存: Python 3.9+ 標準ライブラリのみ。
"""

import argparse
import csv
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

SCHEMA = ["date", "media", "campaign", "impressions", "clicks", "cost", "conversions"]
METRICS = ["impressions", "clicks", "cost", "conversions"]


def week_start(d: datetime) -> str:
    return (d - timedelta(days=d.weekday())).strftime("%Y-%m-%d")


def ratio(num, den, digits=4):
    return round(num / den, digits) if den else None


def fmt(v, digits=None):
    if v is None:
        return ""
    if digits is not None:
        return f"{v:,.{digits}f}"
    return f"{v:,.0f}" if isinstance(v, float) and v.is_integer() else f"{v:,}"


def pct_diff(cur, prev):
    if prev in (None, 0) or cur is None:
        return ""
    d = (cur - prev) / prev * 100
    return f"{d:+.1f}%"


def main() -> int:
    ap = argparse.ArgumentParser(description="正規化済みCSVから週次レポートを作る")
    ap.add_argument("inputs", nargs="+", help="共通スキーマの正規化済みCSV(複数可)")
    ap.add_argument("--out-dir", required=True, help="出力ディレクトリ")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # (week, media) 単位で集計
    agg = defaultdict(lambda: {m: 0 for m in METRICS})
    for path in args.inputs:
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            missing = [c for c in SCHEMA if c not in (reader.fieldnames or [])]
            if missing:
                print(f"エラー: {path} に列が足りない: {', '.join(missing)}", file=sys.stderr)
                print("  csv-normalize skill で正規化してから渡すこと", file=sys.stderr)
                return 1
            for lineno, row in enumerate(reader, start=2):
                try:
                    d = datetime.strptime(row["date"], "%Y-%m-%d")
                except ValueError:
                    print(f"エラー: {path} {lineno}行目 dateがYYYY-MM-DDでない: {row['date']!r}", file=sys.stderr)
                    return 1
                key = (week_start(d), row["media"])
                for m in METRICS:
                    agg[key][m] += float(row[m])

    if not agg:
        print("エラー: 入力に行が無い", file=sys.stderr)
        return 1

    weeks = sorted({w for w, _ in agg})
    medias = sorted({md for _, md in agg})

    # weekly_summary.csv
    with open(out_dir / "weekly_summary.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["week_start", "media", *METRICS, "ctr", "cvr", "cpa"])
        for wk in weeks:
            for md in medias:
                v = agg.get((wk, md))
                if not v:
                    continue
                w.writerow([
                    wk, md,
                    int(v["impressions"]), int(v["clicks"]), round(v["cost"], 2), int(v["conversions"]),
                    ratio(v["clicks"], v["impressions"]),
                    ratio(v["conversions"], v["clicks"]),
                    ratio(v["cost"], v["conversions"], 1),
                ])

    # 週次合計(全媒体)
    totals = {}
    for wk in weeks:
        t = {m: sum(agg[(wk, md)][m] for md in medias if (wk, md) in agg) for m in METRICS}
        totals[wk] = t

    lines = ["# 週次レポート", ""]
    lines += [f"- 集計対象: {', '.join(medias)}", f"- 期間: {weeks[0]} 週 〜 {weeks[-1]} 週(週は月曜開始)", ""]

    lines += ["## 週次合計の推移(全媒体)", "",
              "| 週 | 表示回数 | クリック | 費用 | CV | CTR | CVR | CPA |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for wk in weeks:
        t = totals[wk]
        ctr, cvr, cpa = ratio(t["clicks"], t["impressions"]), ratio(t["conversions"], t["clicks"]), ratio(t["cost"], t["conversions"], 1)
        lines.append(
            f"| {wk} | {fmt(int(t['impressions']))} | {fmt(int(t['clicks']))} | {fmt(t['cost'], 0)} "
            f"| {fmt(int(t['conversions']))} | {f'{ctr:.2%}' if ctr is not None else ''} "
            f"| {f'{cvr:.2%}' if cvr is not None else ''} | {fmt(cpa, 1)} |")
    lines.append("")

    cur_wk = weeks[-1]
    prev_wk = (datetime.strptime(cur_wk, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
    if prev_wk in totals:
        cur, prev = totals[cur_wk], totals[prev_wk]
        lines += [f"## 直近週の前週差分({cur_wk} 週 vs {prev_wk} 週)", "",
                  "| 指標 | 前週 | 直近週 | 増減率 |", "|---|---:|---:|---:|"]
        for label, m in [("表示回数", "impressions"), ("クリック", "clicks"), ("費用", "cost"), ("CV", "conversions")]:
            lines.append(f"| {label} | {fmt(prev[m], 0)} | {fmt(cur[m], 0)} | {pct_diff(cur[m], prev[m])} |")
        lines.append("")
    else:
        lines += ["## 直近週の前週差分", "",
                  f"前週({prev_wk} 週)のデータが入力に無いため、前週差分は出力していません。", ""]

    last_wk = weeks[-1]
    total_cost = sum(agg[(last_wk, md)]["cost"] for md in medias if (last_wk, md) in agg)
    lines += [f"## 直近週の媒体別構成比({last_wk} 週)", "",
              "| 媒体 | 費用 | 費用構成比 | CV | CPA |", "|---|---:|---:|---:|---:|"]
    for md in medias:
        v = agg.get((last_wk, md))
        if not v:
            continue
        share = ratio(v["cost"], total_cost)
        cpa = ratio(v["cost"], v["conversions"], 1)
        lines.append(f"| {md} | {fmt(v['cost'], 0)} | {f'{share:.1%}' if share is not None else ''} "
                     f"| {fmt(int(v['conversions']))} | {fmt(cpa, 1)} |")
    lines += ["", "※ 費用は入力CSVの通貨単位のまま。CTR=クリック/表示回数、CVR=CV/クリック、CPA=費用/CV。分母0の指標は空欄。", ""]

    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"OK: {len(weeks)}週×{len(medias)}媒体を集計 → {out_dir}/weekly_summary.csv, {out_dir}/report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
