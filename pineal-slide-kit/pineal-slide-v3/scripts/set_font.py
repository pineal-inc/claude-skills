#!/usr/bin/env python3
"""pptx のフォント / タイトルサイズを一括変更する。

⚠️ テーマ（theme1.xml）だけ変えても効かないことが多い。
   pinealのデッキはスライドマスター・レイアウトにフォント名が直書きされている場合があり、
   下位の直書きが上位のテーマ継承に勝つ。このスクリプトは全パートを対象にする。

まず現状を調べる:
  set_font.py inspect --file deck.pptx

フォントを差し替える（全パート・直書きも含めて）:
  set_font.py font --file deck.pptx --to "Meiryo UI"
  set_font.py font --file deck.pptx --to "Meiryo UI" --keep Arial        # Arialは残す（既定）
  set_font.py font --file deck.pptx --to "Meiryo UI" --only "Noto Sans JP,Noto Sans JP Light"

レイアウトのタイトルサイズを変える:
  set_font.py title-size --file deck.pptx --layout 中面A --pt 28

いずれも old/ に自動退避する。実行後は必ず PowerPoint で開いて確認する
（LibreOffice は Office 同梱フォントを見ないため、レンダリングが実機と一致しない）。
"""
import argparse, collections, os, re, shutil, sys, tempfile, zipfile
from datetime import datetime

TAG_RE = re.compile(r'<a:(latin|ea|cs)\b([^>]*?)/>')
PLACEHOLDERS = ("+mj-lt", "+mn-lt", "+mj-ea", "+mn-ea", "+mj-cs", "+mn-cs")
# 記号・絵文字系は本文フォントに置換すると図が壊れるため常に保護する
NEVER = {"Wingdings", "Wingdings 2", "Wingdings 3", "Symbol", "Webdings",
         "Cambria Math", "Segoe UI Symbol", "Segoe UI Emoji"}


def part_of(name):
    if "slideMaster" in name: return "master"
    if "slideLayout" in name: return "layout"
    if "/slides/" in name:    return "slide"
    if "/theme/" in name:     return "theme"
    return "other"


SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def backup(path, tag, enabled=True):
    """退避を作る。ただしスキル配下（assets/ のテンプレ等）には作らない。

    スキル内に退避を溜めると、skill本体と配布zipが肥大する（実際に49MBまで膨らんだ）。
    テンプレを編集する場合は退避を一時領域に置き、パスだけ表示する。
    """
    if not enabled:
        print("退避: スキップ（--no-backup）")
        return
    src = os.path.abspath(path)
    base, ext = os.path.splitext(os.path.basename(src))
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if src.startswith(SKILL_ROOT + os.sep):
        d = tempfile.mkdtemp(prefix="pineal_pptx_bk_")
        dst = os.path.join(d, f"{base}_{stamp}_{tag}{ext}")
        shutil.copy(src, dst)
        print(f"退避（スキル外の一時領域）: {dst}")
        print("  ※ 残す必要があれば任意の場所へ移すこと。再起動で消える")
        return
    d = os.path.join(os.path.dirname(src), "old")
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, f"{base}_{stamp}_{tag}{ext}")
    n = 2
    while os.path.exists(dst):
        dst = os.path.join(d, f"{base}_{stamp}_{tag}_{n}{ext}")
        n += 1
    shutil.copy(src, dst)
    print(f"退避: {dst}")


def rewrite(path, fn):
    """各 .xml に fn(name, text) -> (text, count) を適用して書き戻す"""
    zin = zipfile.ZipFile(path)
    tmp = path + ".tmp"
    zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
    total = {}
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename.endswith(".xml"):
            t = data.decode("utf-8")
            n, c = fn(item.filename, t)
            if c:
                total[item.filename] = c
                data = n.encode("utf-8")
        zout.writestr(item, data)
    zout.close(); zin.close()
    shutil.move(tmp, path)
    return total


def cmd_inspect(a):
    z = zipfile.ZipFile(a.file)
    cnt = collections.Counter()
    for n in z.namelist():
        if not n.endswith(".xml"):
            continue
        t = z.read(n).decode("utf-8", "ignore")
        for m in TAG_RE.finditer(t):
            tf = re.search(r'typeface="([^"]*)"', m.group(2))
            if tf:
                cnt[(part_of(n), tf.group(1))] += 1
        for m in re.finditer(r'script="Jpan" typeface="([^"]*)"', t):
            cnt[(part_of(n) + "/Jpan", m.group(1))] += 1
    print("=== typeface の内訳（部位別）===")
    for (p, f), v in sorted(cnt.items()):
        mark = "  ← テーマ継承" if f in PLACEHOLDERS else ""
        print(f"  {p:14s} {f!r:26s} {v:4d}{mark}")
    hard = {f for (p, f) in cnt if p in ("master", "layout") and f not in PLACEHOLDERS}
    if hard:
        print(f"\n⚠️ master/layout に直書きされたフォント: {sorted(hard)}")
        print("   → テーマ変更だけでは効かない。font サブコマンドで置換する")

    print("\n=== レイアウトのタイトルサイズ ===")
    from pptx import Presentation
    p = Presentation(a.file)
    for l in p.slide_masters[0].slide_layouts:
        lt = z.read(l.part.partname.lstrip("/")).decode("utf-8", "ignore")
        m = re.search(r'<p:sp>(?:(?!</p:sp>).)*?type="(ctrTitle|title)"(?:(?!</p:sp>).)*?</p:sp>', lt, re.S)
        szs = sorted({int(x) / 100 for x in re.findall(r'sz="(\d+)"', m.group(0))}) if m else []
        print(f"  {l.name:16s} {os.path.basename(str(l.part.partname)):22s} title sz={szs}")


def cmd_font(a):
    only = [s.strip() for s in a.only.split(",")] if a.only else None
    keep = {s.strip() for s in a.keep.split(",")} if a.keep else set()

    def fn(name, xml):
        n = [0]

        def rep(m):
            kind, attrs = m.group(1), m.group(2)
            tf = re.search(r'typeface="([^"]*)"', attrs)
            if not tf:
                return m.group(0)
            face = tf.group(1)
            if face in PLACEHOLDERS or face in keep or face in NEVER or face == a.to:
                return m.group(0)
            if only is not None and face not in only:
                return m.group(0)
            n[0] += 1
            # panose / pitchFamily / charset は元フォント固有なので落とす
            return f'<a:{kind} typeface="{a.to}"/>'

        out = TAG_RE.sub(rep, xml)

        def rep2(m):
            # Jpan（日本語）以外のスクリプト指定は触らない。
            # 全スクリプトを置換すると Angsana New / DaunPenh 等の各言語用マッピングを壊す。
            face = m.group(2)
            if face in keep or face in NEVER or face == a.to:
                return m.group(0)
            if only is not None and face not in only:
                return m.group(0)
            n[0] += 1
            return f'{m.group(1)}"{a.to}"'

        out = re.sub(r'(script="Jpan" typeface=)"([^"]*)"', rep2, out)
        return out, n[0]

    backup(a.file, "beforefont", not a.no_backup)
    total = rewrite(a.file, fn)
    for k in sorted(total):
        print(f"  {k}: {total[k]}箇所")
    print(f"\n合計 {sum(total.values())}箇所 → {a.to!r}")
    print("⚠️ PowerPoint で開いて確認する（LibreOfficeのレンダリングは一致しない）")


def cmd_title_size(a):
    from pptx import Presentation
    p = Presentation(a.file)
    target = None
    for l in p.slide_masters[0].slide_layouts:
        if l.name == a.layout:
            target = str(l.part.partname).lstrip("/")
            break
    if not target:
        names = [l.name for l in p.slide_masters[0].slide_layouts]
        sys.exit(f"レイアウト {a.layout!r} が無い。候補: {names}")

    sz = int(round(a.pt * 100))

    def fn(name, xml):
        if name != target:
            return xml, 0
        m = re.search(r'<p:sp>(?:(?!</p:sp>).)*?type="(ctrTitle|title)"(?:(?!</p:sp>).)*?</p:sp>', xml, re.S)
        if not m:
            return xml, 0
        blk = m.group(0)
        new, c = re.subn(r'sz="\d+"', f'sz="{sz}"', blk)
        return xml.replace(blk, new), c

    backup(a.file, "beforesize", not a.no_backup)
    total = rewrite(a.file, fn)
    if not total:
        sys.exit("タイトルのsz指定が見つからなかった（レイアウトにsz未定義の可能性）")
    print(f"{target}: タイトル sz を {a.pt}pt に変更（{sum(total.values())}箇所）")
    print("※ タイトル枠の高さは既定 0.34in。28pt以上にすると下のメッセージラインと詰まることがある")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("inspect", help="現状のフォント/サイズを調べる")
    i.add_argument("--file", required=True)

    f = sub.add_parser("font", help="フォントを一括置換")
    f.add_argument("--file", required=True)
    f.add_argument("--to", required=True)
    f.add_argument("--only", default=None, help="この名前だけを置換（カンマ区切り）")
    f.add_argument("--keep", default="Arial", help="置換しないフォント（カンマ区切り・既定 Arial）")
    f.add_argument("--no-backup", action="store_true", help="退避を作らない")

    t = sub.add_parser("title-size", help="レイアウトのタイトルサイズを変更")
    t.add_argument("--file", required=True)
    t.add_argument("--layout", required=True, help="例: 中面A")
    t.add_argument("--pt", type=float, required=True)
    t.add_argument("--no-backup", action="store_true", help="退避を作らない")

    a = ap.parse_args()
    {"inspect": cmd_inspect, "font": cmd_font, "title-size": cmd_title_size}[a.cmd](a)


if __name__ == "__main__":
    main()
