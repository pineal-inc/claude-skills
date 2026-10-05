"""pineal-slide の PPTX 出力用の部品（pineal-slide-v3 テンプレ方式）。

HTML 版を内容の正本とし、pineal-slide-v3 の assets/pineal_temp.pptx の型スライドを
new_slide.py で1枚ずつ起こしてボディを足す。手順は ../references/pptx-v3.md。

案件側では最初に configure() を呼ぶ。

    import sys; sys.path.insert(0, '<このフォルダ>')
    from pptxlib import *
    import pptxlib
    pptxlib.configure(assets='<HTML版の assets/>', out='<案件>/workspace/pptx/パワポ')

色・サイズ・作法は pineal-slide-v3/references/design-system.md と pitfalls.md に従う。
"""
import io, os, math, copy, shutil, datetime, subprocess, pathlib
from pptx import Presentation
from pptx.util import Inches as In, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree
from PIL import Image

# v3 の場所: 環境変数 → tool-pineal-slide-v2 と同じ階層（キット直下の pineal-slide-v3）
_SIBLING = pathlib.Path(__file__).resolve().parents[5] / 'pineal-slide-v3'
V3 = pathlib.Path(os.environ.get('PINEAL_SLIDE_V3')
                  or _SIBLING)
SRC_ASSETS = None   # HTML 版の assets/。logos/png/*.png と icons/png/*.png を置く
ASSETS = None       # 塗り替えたアイコンの置き場（既定: out の隣の _assets/）
OUT = None          # スライド1枚=1フォルダを作る親（v3 の「パワポ/」）


def configure(assets, out, work=None):
    """assets: HTML 版の assets/。out: スライドフォルダの親。work: 生成素材の置き場。"""
    global SRC_ASSETS, ASSETS, OUT
    SRC_ASSETS = pathlib.Path(assets)
    OUT = pathlib.Path(out)
    ASSETS = pathlib.Path(work) if work else OUT.parent / '_assets'
    svg_to_png()


def svg_to_png(height=256):
    """HTML 版の icons/*.svg と logos/*.svg を、高さ height px の PNG にして */png/ に置く。
    既にある PNG は作り直さない。縦横比は rsvg-convert が保つ（-h だけを渡す）。"""
    for kind in ('icons', 'logos'):
        d = SRC_ASSETS / kind
        if not d.is_dir():
            continue
        (d / 'png').mkdir(exist_ok=True)
        for f in d.glob('*.svg'):
            dst = d / 'png' / f'{f.stem}.png'
            if not dst.exists():
                subprocess.run(['rsvg-convert', '-h', str(height), '-o', str(dst), str(f)], check=True)


# テンプレ assets/pineal_temp.pptx の型番号（1始まり。v3 references/template-catalog.md）
# 4 Board Member / 5 Media / 6 Client / 15 お問い合わせ は社内情報入り。社外向けに使わない
TPL_COVER, TPL_AGENDA, TPL_BLANK = 1, 2, 3
TPL_SECTION, TPL_BASE, TPL_BASE_B, TPL_ASIS = 7, 8, 9, 10
TPL_MILESTONE, TPL_TIMELINE, TPL_TEAM, TPL_ESTIMATE, TPL_END = 11, 12, 13, 14, 16

DARK = RGBColor(0x1C, 0x1A, 0x1A); GRAY = RGBColor(0x93, 0x92, 0x92); RED = RGBColor(0xD2, 0x1E, 0x2C)
BORDER = RGBColor(0xD9, 0xD9, 0xD9); REDTINT = RGBColor(0xF1, 0xE5, 0xE5); BAND = RGBColor(0xF6, 0xF3, 0xF3)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = 'Meiryo UI'
L, R = 0.60, 12.73          # 有効幅の左右端（インチ）
W = R - L
BODY_TOP = 2.05             # メッセージライン1行のときのボディ上端。2行なら 2.40
FOOT_Y = 6.72


# ---------- 素材 ----------

def _tint_icons():
    """黒の線アイコンを赤・濃灰・白に塗り替えて ASSETS に置く（縦横比はそのまま）。"""
    for name, rgb in (('red', (0xD2, 0x1E, 0x2C)), ('dark', (0x1C, 0x1A, 0x1A)), ('white', (255, 255, 255))):
        d = ASSETS / f'icons-{name}'; d.mkdir(parents=True, exist_ok=True)
        for f in (SRC_ASSETS / 'icons/png').glob('*.png'):
            dst = d / f.name
            if dst.exists():
                continue
            im = Image.open(f).convert('RGBA')
            a = im.split()[3]
            out = Image.new('RGBA', im.size, rgb + (0,)); out.putalpha(a)
            out.save(dst)


def icon(name, color='red'):
    _tint_icons()
    return ASSETS / f'icons-{color}' / f'{name}.png'


def logo(name):
    """SVG 原本は logos/png/ の書き出しを、PNG 原本（python.png 等）は logos/ のものをそのまま返す。"""
    f = SRC_ASSETS / 'logos/png' / f'{name}.png'
    return f if f.exists() else SRC_ASSETS / 'logos' / f'{name}.png'


def asset(rel):
    return SRC_ASSETS / rel


# ---------- スライドの起こし方 ----------

def new_slide(key, source, title=None, lead=None, keep_body=False):
    """テンプレの型 #source を new_slide.py で起こす。key 例: 'S03_Day1〜Day5の骨子'。
    title は名詞句、lead（メッセージライン）は結論の文。font.size は継承のまま触らない。"""
    d = OUT / key; d.mkdir(parents=True, exist_ok=True)
    path = d / f'{key}.pptx'
    if path.exists():  # 作り直す前に old/ へ退避
        (d / 'old').mkdir(exist_ok=True)
        shutil.copy(path, d / 'old' / f"{key}_{datetime.datetime.now():%Y%m%d_%H%M%S}.pptx")
    cmd = ['python3', str(V3 / 'scripts/new_slide.py'), '--out', str(path), '--source-slide', str(source)]
    if keep_body:
        cmd.append('--keep-body')
    subprocess.run(cmd, check=True, capture_output=True)
    p = Presentation(path)
    s = p.slides[0]
    for sh in s.shapes:
        if not sh.is_placeholder:
            continue
        idx = sh.placeholder_format.idx
        if idx == 0 and title is not None:
            set_text_keep_style(sh, title)
        elif idx == 1 and lead is not None:
            set_text_keep_style(sh, lead)
    return p, s, path


def set_text_keep_style(sh, text):
    """プレースホルダーの書式（継承）を保ったまま文言だけ差し替える。font.size は触らない。"""
    tf = sh.text_frame
    lines = text.split('\n')
    p0 = tf.paragraphs[0]
    runs = p0.runs
    if runs:
        runs[0].text = lines[0]
        for r in runs[1:]:
            r._r.getparent().remove(r._r)
    else:
        p0.add_run().text = lines[0]
    for extra in tf.paragraphs[1:]:
        extra._p.getparent().remove(extra._p)
    for ln in lines[1:]:
        np_ = etree.SubElement(tf._txBody, qn('a:p'))
        if p0._p.pPr is not None:
            np_.append(etree.fromstring(etree.tostring(p0._p.pPr)))
        r = etree.SubElement(np_, qn('a:r'))
        if runs and runs[0]._r.rPr is not None:
            r.append(etree.fromstring(etree.tostring(runs[0]._r.rPr)))
        t = etree.SubElement(r, qn('a:t')); t.text = ln


def ph(s, idx):
    for sh in s.shapes:
        if sh.is_placeholder and sh.placeholder_format.idx == idx:
            return sh


# ---------- 部品 ----------

def _font(run, size, bold=False, color=DARK):
    f = run.font
    f.size = Pt(size); f.bold = bold; f.color.rgb = color; f.name = FONT
    rPr = run._r.get_or_add_rPr()
    rPr.set('lang', 'ja-JP'); rPr.set('altLang', 'en-US')  # 無いと禁則が効かず、行頭に「、」が来る
    for tag in ('a:ea', 'a:cs'):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set('typeface', FONT)


def box(s, x, y, w, h, fill=WHITE, line=BORDER, shape=MSO_SHAPE.ROUNDED_RECTANGLE, lw=9525, radius=None):
    sp = s.shapes.add_shape(shape, In(x), In(y), In(w), In(h))
    sp.shadow.inherit = False
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line; sp.line.width = lw
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        sp.adjustments[0] = radius
    tf = sp.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return sp


def put(sp, lines, align=PP_ALIGN.CENTER, anchor=None, spacing=None, margin=None):
    """lines: [(text, pt, bold, color), ...]。text が list のときは run を連結する [(t,pt,b,c),...]"""
    tf = sp.text_frame
    if anchor is not None:
        tf.vertical_anchor = anchor
    if margin is not None:
        tf.margin_left, tf.margin_top, tf.margin_right, tf.margin_bottom = [In(v) for v in margin]
    first = True
    for item in lines:
        pa = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        pa.alignment = align
        if spacing:
            pa.space_after = Pt(spacing)
        runs = item if isinstance(item, list) else [item]
        for (t, sz, b, c) in runs:
            r = pa.add_run(); r.text = t; _font(r, sz, b, c)
    return sp


def text(s, x, y, w, h, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=None):
    tb = s.shapes.add_textbox(In(x), In(y), In(w), In(h))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    if isinstance(lines, str):
        lines = [(lines, 10, False, DARK)]
    put(tb, lines, align=align, spacing=spacing)
    return tb


def bullets(s, x, y, w, h, items, size=10, gap=4, marker='•', color=DARK, sub_size=None):
    """items: str or (str, level)。level 1 はグレーで1段下げる。"""
    tb = s.shapes.add_textbox(In(x), In(y), In(w), In(h))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    first = True
    for it in items:
        t, lv = (it, 0) if isinstance(it, str) else it
        pa = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        pa.space_after = Pt(gap)
        pPr = pa._p.get_or_add_pPr()
        ind = 0.16
        pPr.set('marL', str(int(In(ind * (lv + 1))))); pPr.set('indent', str(int(-In(ind))))
        clr = etree.SubElement(pPr, qn('a:buClr')); sc = etree.SubElement(clr, qn('a:srgbClr'))
        sc.set('val', '939292' if lv else 'D21E2C')
        bu = etree.SubElement(pPr, qn('a:buFont')); bu.set('typeface', FONT)
        bc = etree.SubElement(pPr, qn('a:buChar')); bc.set('char', marker)
        r = pa.add_run(); r.text = t
        _font(r, (sub_size or size - 0.5) if lv else size, False, GRAY if lv else color)
    return tb


def section(s, x, y, w, label, icon_name=None):
    """セクション見出し 14pt bold ＋ 下の罫線（灰、左端だけ赤）。"""
    tx = x
    if icon_name:
        pic(s, icon(icon_name), x, y + 0.04, h=0.24)
        tx = x + 0.32
    text(s, tx, y, w - (tx - x), 0.32, [(label, 14, True, DARK)], anchor=MSO_ANCHOR.MIDDLE)
    hline(s, x, y + 0.40, w, BORDER, 9525)
    hline(s, x, y + 0.40, 0.5, RED, 19050)
    return y + 0.55


def hline(s, x, y, w, color=BORDER, width=9525):
    ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, In(x), In(y), In(x + w), In(y))
    ln.line.color.rgb = color; ln.line.width = width
    return ln


def vline(s, x, y, h, color=BORDER, width=9525):
    ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, In(x), In(y), In(x), In(y + h))
    ln.line.color.rgb = color; ln.line.width = width
    return ln


def arrow(s, x, y, w=0.40, h=0.32, color=RED):
    """As-Is/To-Be 型と同じ右矢印。"""
    sp = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, In(x), In(y), In(w), In(h))
    sp.shadow.inherit = False
    sp.fill.solid(); sp.fill.fore_color.rgb = color; sp.line.fill.background()
    return sp


def tri(s, x, y, w=0.18, h=0.26, color=RED):
    """小さな右向き三角。"""
    sp = s.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, In(x), In(y), In(h), In(w))
    sp.rotation = 90
    sp.shadow.inherit = False
    sp.fill.solid(); sp.fill.fore_color.rgb = color; sp.line.fill.background()
    return sp


def pic(s, path, x, y, w=None, h=None, border=None):
    """縦横比を保って貼る。w か h の片方だけを渡す。両方渡したら内接させて中央寄せ。"""
    iw, ih = Image.open(path).size
    r = iw / ih
    if w is not None and h is not None:
        if w / h > r:
            nw = h * r; x += (w - nw) / 2; w = nw
        else:
            nh = w / r; y += (h - nh) / 2; h = nh
    elif w is not None:
        h = w / r
    else:
        w = h * r
    p = s.shapes.add_picture(str(path), In(x), In(y), In(w), In(h))
    if border is not None:
        p.line.color.rgb = border; p.line.width = 9525
    return p


def logo_label(s, x, y, name, label, size=10, bold=True, h=0.22, color=DARK, w=4.0):
    """ロゴ＋ラベルを1行で置く。戻り値は右端の x。"""
    p = pic(s, logo(name) if not str(name).endswith('.png') else name, x, y + 0.01, h=h)
    tx = x + p.width / 914400 + 0.08
    text(s, tx, y - 0.02, w, h + 0.06, [(label, size, bold, color)], anchor=MSO_ANCHOR.MIDDLE)
    return tx


def footnote(s, t, y=FOOT_Y):
    text(s, L, y, 12.10, 0.28, [(t, 8, False, GRAY)], anchor=MSO_ANCHOR.MIDDLE)


def caption(s, x, y, w, t, align=PP_ALIGN.CENTER):
    text(s, x, y, w, 0.25, [(t, 8.5, False, GRAY)], align=align)


# ---------- 表 ----------

def table(s, x, y, col_w, rows, header=True, size=9.5, row_h=None, head_size=9.5,
          first_col_bold=True, fills=None, pad=0.08):
    """rows[0] がヘッダー。セルは str または [(text,pt,bold,color),...] の行リスト。
    行高は row_h（list か数値）で固定。テキストが収まらないと PowerPoint が行を伸ばすので目視QAで確認する。"""
    nr, nc = len(rows), len(col_w)
    rh = row_h if isinstance(row_h, list) else [row_h or 0.3] * nr
    gs = s.shapes.add_table(nr, nc, In(x), In(y), In(sum(col_w)), In(sum(rh)))
    tbl = gs.table
    tblPr = tbl._tbl.tblPr
    tblPr.set('firstRow', '0'); tblPr.set('bandRow', '0')
    sid = tblPr.find(qn('a:tableStyleId'))
    if sid is None:
        sid = etree.SubElement(tblPr, qn('a:tableStyleId'))
    sid.text = '{2D5ABB26-0587-4C30-8999-92F81FD0307C}'  # No Style, No Grid
    for j, cw in enumerate(col_w):
        tbl.columns[j].width = In(cw)
    for i in range(nr):
        tbl.rows[i].height = In(rh[i])
        for j in range(nc):
            c = tbl.cell(i, j)
            c.margin_left = c.margin_right = In(pad)
            c.margin_top = c.margin_bottom = In(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            is_head = header and i == 0
            fill = DARK if is_head else (fills[i][j] if fills and fills[i] and fills[i][j] else WHITE)
            c.fill.solid(); c.fill.fore_color.rgb = fill
            _cell_border(c, bottom=('D9D9D9' if not is_head else None))
            val = rows[i][j]
            tf = c.text_frame; tf.word_wrap = True
            if isinstance(val, str):
                val = [(val, head_size if is_head else size, is_head or (j == 0 and first_col_bold),
                        WHITE if is_head else DARK)]
            first = True
            for item in val:
                pa = tf.paragraphs[0] if first else tf.add_paragraph()
                first = False
                runs = item if isinstance(item, list) else [item]
                for (t, sz, b, col) in runs:
                    r = pa.add_run(); r.text = t; _font(r, sz, b, col)
    return gs


def _cell_border(cell, bottom='D9D9D9', others=None):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ('a:lnL', 'a:lnR', 'a:lnT', 'a:lnB'):
        old = tcPr.find(qn(tag))
        if old is not None:
            tcPr.remove(old)
    for tag, col in (('a:lnL', None), ('a:lnR', None), ('a:lnT', None), ('a:lnB', bottom)):
        ln = etree.SubElement(tcPr, qn(tag))
        if col:
            ln.set('w', '9525')
            sf = etree.SubElement(ln, qn('a:solidFill')); c = etree.SubElement(sf, qn('a:srgbClr')); c.set('val', col)
        else:
            ln.set('w', '0'); etree.SubElement(ln, qn('a:noFill'))
    # lnX は solidFill より前に置く必要がある
    fill = tcPr.find(qn('a:solidFill'))
    if fill is not None:
        tcPr.remove(fill); tcPr.append(fill)


def cell_rect(x, y, col_w, row_h, i, j):
    """表のセル (i,j) の左上座標。行高が固定のときだけ正しい。"""
    rh = row_h if isinstance(row_h, list) else [row_h] * (i + 1)
    return x + sum(col_w[:j]), y + sum(rh[:i])


def save(p, path):
    p.save(path)
    Presentation(path)  # 読み戻し検証
    return path


# ---------- 記号つきリスト・記号つき表 ----------

def est_lines(t, size, w):
    """1行に入る量から行数を見積もる。Meiryo UI の実測に合わせ、かな0.86字、漢字・約物0.95字、半角0.52字分で数える。"""
    units = sum(0.86 if 0x3040 <= ord(ch) <= 0x30FF else 0.95 if ord(ch) > 0x2000 else 0.52 for ch in t)
    per = max(1.0, w * 72 / size)
    return max(1, math.ceil(units / per))


def mark_w(name, h):
    """記号を高さ h で置いたときの幅（縦横比を保つ）。"""
    p = logo(name[5:]) if name.startswith('logo:') else icon(name[5:] if name.startswith('icon:') else name)
    iw, ih = Image.open(p).size
    return h * iw / ih


def mark(s, name, x, y, h):
    """'logo:xxx' はロゴ、'icon:xxx'（または名前だけ）は赤アイコン。"""
    if name.startswith('logo:'):
        return pic(s, logo(name[5:]), x, y, h=h)
    return pic(s, icon(name[5:] if name.startswith('icon:') else name), x, y, h=h)


def marked_list(s, x, y, w, items, size=10.5, gap=0.10, mh=0.22, color=DARK):
    """items: (mark or None, text[, bold])。mark が None なら赤の点。戻り値は下端の y。"""
    lh = size / 72 * 1.45
    for it in items:
        mk, t = it[0], it[1]
        b = it[2] if len(it) > 2 else False
        n = est_lines(t, size, w - 0.36)
        h = n * lh
        if mk:
            mark(s, mk, x, y + (lh - mh) / 2, mh)
        else:
            text(s, x + 0.05, y, 0.2, lh, [('•', size, True, RED)])
        text(s, x + 0.36, y, w - 0.36, h, [(t, size, b, color)])
        y += h + gap
    return y


def mark_table(s, x, y, col_w, rows, marks=None, mh=0.20, **kw):
    """table() の各セル左にロゴ・アイコンを重ねる。marks: {(i, j): ['logo:dify', 'wrench', ...]}。
    記号の幅だけセル内の段落を左インデントするので、折り返しても記号と重ならない。
    記号はセルの上下中央に置く。行高は row_h で固定しておくこと。"""
    marks = marks or {}
    gs = table(s, x, y, col_w, rows, **kw)
    rh = kw.get('row_h')
    pad = kw.get('pad', 0.08)
    for (i, j), mks in marks.items():
        indent = sum(mark_w(m, mh) + 0.07 for m in mks) + 0.03
        for pa in gs.table.cell(i, j).text_frame.paragraphs:
            pa._p.get_or_add_pPr().set('marL', str(int(In(indent))))
        cx, cy = cell_rect(x, y, col_w, rh, i, j)
        hh = rh[i] if isinstance(rh, list) else rh
        mx = cx + pad
        for mk in mks:
            mark(s, mk, mx, cy + hh / 2 - mh / 2, mh)
            mx += mark_w(mk, mh) + 0.07
    return gs

# ---------- 結合 ----------

_R_ATTRS = (qn('r:embed'), qn('r:link'), qn('r:id'))


def merge(files, out):
    """個別 pptx を files の順に結合する。図形 XML の r:embed / r:link / r:id を新しいスライドの
    リレーションに張り替える（v3 merge_deck.py build も 2026-09-19 に同じ修正済み）。
    結合後は必ず visual_qa.py（エンジン: powerpoint）で全ページを見る。"""
    base = Presentation(files[0])
    for f in files[1:]:
        src = Presentation(f)
        for sl in src.slides:
            lay = next((l for l in base.slide_layouts if l.name == sl.slide_layout.name),
                       base.slide_layouts[4])
            new = base.slides.add_slide(lay)
            for sh in list(new.shapes):
                sh._element.getparent().remove(sh._element)
            rmap = {}
            for sh in sl.shapes:
                el = copy.deepcopy(sh._element)
                for node in el.iter():
                    for at in _R_ATTRS:
                        rid = node.get(at)
                        if not rid:
                            continue
                        if rid not in rmap:
                            rel = sl.part.rels[rid]
                            if rel.is_external:
                                rmap[rid] = new.part.relate_to(rel.target_ref, rel.reltype, is_external=True)
                            elif rel.reltype.endswith('/image'):
                                # 別パッケージの画像パーツは名前が衝突するので、blob から取り込み直す
                                _, rmap[rid] = new.part.get_or_add_image_part(io.BytesIO(rel.target_part.blob))
                            elif rel.target_part in base.slide_layouts[0].part.package.iter_parts():
                                rmap[rid] = new.part.relate_to(rel.target_part, rel.reltype)
                            else:
                                raise ValueError(f'未対応のリレーション: {rel.reltype}')
                        node.set(at, rmap[rid])
                new.shapes._spTree.append(el)
            # 背景（p:bg）も複製
            bg = sl._element.cSld.find(qn('p:bg'))
            if bg is not None:
                new._element.cSld.insert(0, copy.deepcopy(bg))
    base.save(out)
    sanitize(out)
    n = len(Presentation(out).slides)
    print(f'生成: {out}（{n}ページ）')
    return out


def sanitize(path):
    """納品するファイルから、スライドで使っていないレイアウトと文書プロパティの個人名を除く。

    テンプレのマスターには「ピネアルについて」（メンバーの写真・氏名・経歴）などのレイアウトがあり、
    スライドで使わなくてもファイルの中に残る。merge() の最後に必ず呼ぶ。1枚だけ渡すときも呼ぶ。
    """
    import re, zipfile
    pr = Presentation(str(path))
    used = {id(sl.slide_layout) for sl in pr.slides}
    for m in pr.slide_masters:
        for lay in list(m.slide_layouts):
            if id(lay) not in used:
                m.slide_layouts.remove(lay)
    cp = pr.core_properties
    cp.author = cp.last_modified_by = '株式会社ピネアル'
    rels = pr.part.package._rels
    for rid, rel in list(rels.items()):
        if rel.reltype.endswith('/thumbnail'):
            rels.pop(rid)
    pr.save(str(path))
    # app.xml のスライド名一覧はテンプレ時代のまま残るので外す（任意要素で、PowerPoint が保存時に作り直す）
    tmp = pathlib.Path(str(path) + '.tmp')
    with zipfile.ZipFile(path) as zi, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            b = zi.read(it.filename)
            if it.filename == 'docProps/app.xml':
                b = re.sub(rb'<HeadingPairs>.*?</HeadingPairs>|<TitlesOfParts>.*?</TitlesOfParts>', b'', b, flags=re.S)
            zo.writestr(it, b)
    shutil.move(str(tmp), str(path))
    return path
