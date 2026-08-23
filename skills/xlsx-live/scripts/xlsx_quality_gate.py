#!/usr/bin/env python3
"""Quality gate for generated XLSX/XLSM workbooks."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from copy import copy
from pathlib import Path
from xml.etree import ElementTree as ET

from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.views import Selection


ERROR_STRINGS = ("#VALUE!", "#DIV/0!", "#REF!", "#NAME?", "#NULL!", "#NUM!", "#N/A")


def add_issue(issues, severity, code, message, location=None, detail=None):
    item = {"severity": severity, "code": code, "message": message}
    if location:
        item["location"] = location
    if detail is not None:
        item["detail"] = detail
    issues.append(item)


def display_units(value):
    total = 0.0
    for ch in str(value):
        if ch == "\t":
            total += 4
        elif unicodedata.east_asian_width(ch) in {"F", "W"}:
            total += 2
        elif unicodedata.east_asian_width(ch) == "A":
            total += 1.5
        else:
            total += 1
    return total


def required_lines(value, width):
    if value is None:
        return 1
    text = str(value)
    if text.startswith("="):
        return 1
    usable_width = max(1.0, float(width or 8.43) - 1.0)
    lines = 0
    for line in text.splitlines() or [""]:
        lines += max(1, int(math.ceil(display_units(line) / usable_width)))
    return lines


def column_width(ws, col_idx):
    letter = get_column_letter(col_idx)
    width = ws.column_dimensions[letter].width
    if width:
        return width
    return ws.sheet_format.defaultColWidth or 8.43


def target_height(lines, font_size):
    size = float(font_size or 10)
    line_height = max(12.0, size * 1.35)
    return min(409, max(15, line_height * lines + 6))


def check_zip_and_xml(path, issues):
    try:
        with zipfile.ZipFile(path) as zf:
            bad = zf.testzip()
            if bad:
                add_issue(issues, "error", "zip-corrupt", "ZIP integrity test failed.", bad)
            for name in zf.namelist():
                if name.endswith(".xml"):
                    try:
                        ET.fromstring(zf.read(name))
                    except ET.ParseError as exc:
                        add_issue(issues, "error", "xml-parse", "XML part does not parse.", name, str(exc))
                if name.startswith("xl/tables/"):
                    add_issue(issues, "error", "excel-table-part", "Native Excel Table part found; prefer styled ranges plus worksheet auto_filter.", name)
                if name.startswith("xl/worksheets/") and name.endswith(".xml"):
                    raw = zf.read(name)
                    if b"<tableParts" in raw:
                        add_issue(issues, "error", "worksheet-tableparts", "Worksheet references tableParts; this has caused Excel repair warnings.", name)
    except zipfile.BadZipFile as exc:
        add_issue(issues, "error", "bad-zip", "File is not a valid XLSX ZIP package.", str(path), str(exc))


def freeze_selection_ok(ws):
    if not ws.freeze_panes:
        return True
    target = ws.freeze_panes if isinstance(ws.freeze_panes, str) else ws.freeze_panes.coordinate
    selections = ws.sheet_view.selection or []
    for selection in selections:
        if selection.activeCell == target or selection.sqref == target:
            return True
    return False


def fix_freeze_selection(ws):
    if not ws.freeze_panes:
        return
    target = ws.freeze_panes if isinstance(ws.freeze_panes, str) else ws.freeze_panes.coordinate
    selections = ws.sheet_view.selection or []
    if selections:
        selections[0].activeCell = target
        selections[0].sqref = target
    else:
        ws.sheet_view.selection = [Selection(activeCell=target, sqref=target)]


def check_workbook(path, issues, fix=False, allow_tables=False):
    keep_vba = path.suffix.lower() == ".xlsm"
    try:
        wb = load_workbook(path, keep_vba=keep_vba)
    except Exception as exc:
        add_issue(issues, "error", "openpyxl-load", "Workbook cannot be loaded by openpyxl.", str(path), str(exc))
        return None

    for ws in wb.worksheets:
        if ws.sheet_state != "visible":
            add_issue(issues, "warning", "hidden-sheet", "Worksheet is not visible.", ws.title, ws.sheet_state)

        if ws.tables and not allow_tables:
            add_issue(issues, "error", "openpyxl-table", "openpyxl Table object found; use styled ranges unless native Tables are required.", ws.title, list(ws.tables.keys()))

        if ws.auto_filter and ws.auto_filter.ref and ws.tables and not allow_tables:
            add_issue(issues, "error", "table-and-autofilter", "Worksheet has both native Tables and worksheet auto_filter.", ws.title, ws.auto_filter.ref)

        for key, dim in ws.column_dimensions.items():
            if dim.hidden:
                add_issue(issues, "error", "hidden-column", "Hidden column found.", f"{ws.title}!{key}")
            if dim.collapsed:
                add_issue(issues, "warning", "collapsed-column", "Collapsed column group found.", f"{ws.title}!{key}")

        for idx, dim in ws.row_dimensions.items():
            if dim.hidden:
                add_issue(issues, "error", "hidden-row", "Hidden row found.", f"{ws.title}!{idx}")
            if dim.collapsed:
                add_issue(issues, "warning", "collapsed-row", "Collapsed row group found.", f"{ws.title}!{idx}")

        if ws.merged_cells.ranges:
            add_issue(issues, "warning", "merged-cells", "Merged cells found; avoid them in data tables.", ws.title, [str(r) for r in list(ws.merged_cells.ranges)[:20]])

        if not freeze_selection_ok(ws):
            add_issue(issues, "error", "freeze-selection", "Freeze panes selection is stale and may trigger repair or odd initial focus.", ws.title, str(ws.freeze_panes))
            if fix:
                fix_freeze_selection(ws)

        for row in ws.iter_rows():
            row_idx = row[0].row
            needed_height = 15
            needs_height_check = False
            for cell in row:
                if isinstance(cell, MergedCell) or cell.value is None:
                    continue
                if isinstance(cell.value, str) and any(err in cell.value for err in ERROR_STRINGS):
                    add_issue(issues, "error", "excel-error-string", "Cell contains an Excel error string.", f"{ws.title}!{cell.coordinate}", cell.value)
                if not isinstance(cell.value, str) or cell.value.startswith("="):
                    continue
                width = column_width(ws, cell.column)
                lines = required_lines(cell.value, width)
                explicit_line_breaks = "\n" in cell.value or "\r" in cell.value
                should_wrap = bool(cell.alignment.wrap_text or explicit_line_breaks)
                right_value = ws.cell(row=cell.row, column=cell.column + 1).value if cell.column < ws.max_column else None
                overflow_blocked = right_value not in (None, "")
                if lines > 1 and not cell.alignment.wrap_text and (explicit_line_breaks or overflow_blocked):
                    add_issue(issues, "warning", "wrap-disabled", "Long text may need wrap_text.", f"{ws.title}!{cell.coordinate}")
                    if fix and explicit_line_breaks:
                        alignment = copy(cell.alignment)
                        alignment.wrap_text = True
                        alignment.vertical = "top"
                        cell.alignment = alignment
                        should_wrap = True
                if lines > 1 and should_wrap:
                    needs_height_check = True
                    needed_height = max(needed_height, target_height(lines, cell.font.sz))

            if needs_height_check:
                current = ws.row_dimensions[row_idx].height or ws.sheet_format.defaultRowHeight or 15
                needed = needed_height
                if needed >= current + 16:
                    add_issue(issues, "error", "row-height", "Row height may clip wrapped text.", f"{ws.title}!{row_idx}", {"current": current, "needed": needed})
                    if fix:
                        ws.row_dimensions[row_idx].height = needed

    return wb


def render_pdf(path, issues):
    candidates = [
        shutil.which("soffice"),
        "/opt/homebrew/bin/soffice",
        "/usr/local/bin/soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ]
    soffice = next((candidate for candidate in candidates if candidate and Path(candidate).exists()), None)
    if not soffice:
        add_issue(issues, "warning", "render-pdf-skipped", "LibreOffice soffice was not found; visual PDF render skipped.")
        return
    outdir = path.parent / f"{path.stem}-render"
    outdir.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as profile:
        cmd = [
            soffice,
            "--headless",
            "--norestore",
            f"-env:UserInstallation=file://{profile}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(outdir),
            str(path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    expected = outdir / f"{path.stem}.pdf"
    if result.returncode != 0 or not expected.exists():
        add_issue(issues, "error", "render-pdf", "LibreOffice PDF render failed.", str(path), (result.stderr or result.stdout).strip())
    else:
        add_issue(issues, "info", "render-pdf", "LibreOffice PDF render succeeded; inspect the rendered PDF visually.", str(expected))


def print_text_report(path, issues):
    print(f"XLSX quality gate: {path}")
    counts = {}
    for issue in issues:
        counts[issue["severity"]] = counts.get(issue["severity"], 0) + 1
    print("summary:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "no issues")
    for issue in issues[:120]:
        loc = f" [{issue['location']}]" if "location" in issue else ""
        detail = f" {issue['detail']}" if "detail" in issue else ""
        print(f"- {issue['severity'].upper()} {issue['code']}{loc}: {issue['message']}{detail}")
    if len(issues) > 120:
        print(f"... {len(issues) - 120} more issues omitted")


def main():
    parser = argparse.ArgumentParser(description="Validate and optionally repair generated XLSX/XLSM files.")
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--allow-tables", action="store_true", help="Do not fail on native Excel Tables/tableParts.")
    parser.add_argument("--fix", action="store_true", help="Fix wrap_text, row heights, and frozen-pane selection.")
    parser.add_argument("--out", type=Path, help="Output path for --fix. If omitted, the input file is overwritten.")
    parser.add_argument("--render-pdf", action="store_true", help="Render with LibreOffice to catch repair/render failures.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    args = parser.parse_args()

    path = args.workbook.expanduser().resolve()
    issues = []
    if not path.exists():
        add_issue(issues, "error", "missing-file", "Workbook file does not exist.", str(path))
    else:
        check_zip_and_xml(path, issues)
        wb = check_workbook(path, issues, fix=args.fix, allow_tables=args.allow_tables)
        if args.fix and wb is not None:
            out = (args.out or path).expanduser().resolve()
            wb.save(out)
            path = out
            issues = [issue for issue in issues if issue["code"] not in {"wrap-disabled", "row-height", "freeze-selection"}]
            check_zip_and_xml(path, issues)
            wb = check_workbook(path, issues, fix=False, allow_tables=args.allow_tables)
        if wb is not None:
            wb.close()
        if args.render_pdf:
            render_pdf(path, issues)

    result = {"workbook": str(path), "issues": issues}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text_report(path, issues)
    has_errors = any(issue["severity"] == "error" for issue in issues)
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
