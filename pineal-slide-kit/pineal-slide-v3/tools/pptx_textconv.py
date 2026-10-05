#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pptx を git diff 用の「読めるテキスト」に変換する textconv スクリプト。
出力するもの:
  - スライド順（presentation.xml の並び順）
  - 各スライドの図形内テキスト（a:t を連結、段落ごと）
  - 各スライドのノート（notesSlide のテキスト）
  - 画像一覧（パス＋バイト数）
出さないもの（保存はされるが差分に出ない）:
  - レイアウト座標・図形の書式・アニメーション
  - 画像の中身（存在/サイズの変化だけ検知）
使い方: python3 pptx_textconv.py <file>   (git textconv が自動で呼ぶ)
"""
import sys, re, zipfile, html

def shape_texts(xml):
    # 段落 <a:p> ごとに <a:t> を連結
    paras = []
    for p in re.findall(r"<a:p\b.*?</a:p>", xml, re.S):
        txt = html.unescape("".join(re.findall(r"<a:t>(.*?)</a:t>", p, re.S)))
        if txt.strip() != "":
            paras.append(txt)
    return paras

def main(path):
    out = []
    try:
        z = zipfile.ZipFile(path)
    except Exception as e:
        print("(pptx_textconv: 開けません %s)" % e); return
    names = z.namelist()

    # スライド順を presentation.xml + rels から決定
    order = []
    if "ppt/presentation.xml" in names and "ppt/_rels/presentation.xml.rels" in names:
        pres = z.read("ppt/presentation.xml").decode("utf-8", "replace")
        rels = z.read("ppt/_rels/presentation.xml.rels").decode("utf-8", "replace")
        rid2tgt = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels))
        rid2tgt.update({b: a for a, b in re.findall(r'Target="([^"]+)"[^>]*Id="(rId\d+)"', rels)})
        for m in re.finditer(r"<p:sldId[^>]*r:id=\"(rId\d+)\"", pres):
            tgt = rid2tgt.get(m.group(1), "")
            f = ("ppt/" + tgt.lstrip("/")) if tgt and not tgt.startswith("ppt/") else tgt
            f = f.replace("ppt/../", "")
            order.append(f)
    if not order:
        order = sorted([n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)])

    def notes_for(slide_path):
        # slideN.xml -> rels から notesSlide を探す
        base = slide_path.split("/")[-1]
        rels = "ppt/slides/_rels/%s.rels" % base
        if rels in names:
            r = z.read(rels).decode("utf-8", "replace")
            m = re.search(r'Target="([^"]*notesSlide\d+\.xml)"', r)
            if m:
                p = m.group(1).replace("../", "ppt/")
                if p in names:
                    return shape_texts(z.read(p).decode("utf-8", "replace"))
        return []

    for i, sp in enumerate(order, 1):
        if sp not in names:
            continue
        out.append("## SLIDE %d (%s)" % (i, sp.split("/")[-1]))
        for line in shape_texts(z.read(sp).decode("utf-8", "replace")):
            out.append("  " + line)
        nt = notes_for(sp)
        if nt:
            out.append("  [NOTES]")
            for line in nt:
                out.append("    " + line)

    media = sorted([(n, z.getinfo(n).file_size) for n in names if n.startswith("ppt/media/")])
    if media:
        out.append("## MEDIA")
        for n, sz in media:
            out.append("  %s (%d bytes)" % (n, sz))

    print("\n".join(out))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(0)
    try:
        main(sys.argv[1])
    except Exception as e:
        print("(pptx_textconv error: %s)" % e)
