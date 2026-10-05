#!/usr/bin/env python3
"""PDF のページ画像やスクショから、資料に貼る部分を切り出す。

  python3 crop.py grid  <元画像> <保存先.png> [--step 100]            座標の目盛りを重ねた確認用の画像を作る
  python3 crop.py cut   <元画像> <x0> <y0> <x1> <y1> <保存先> [--scale 倍率]
                        座標は左上と右下。--scale は確認用より高い解像度の画像から切るときの倍率（既定 1.0）
                        例: 確認用 110dpi で座標を読み、250dpi の画像から切るなら 250/110
  python3 crop.py fit   <元画像> <保存先> [--ratio 1.414] [--width 900]  上端を基準に縦横比をそろえて縮小する（資料のサムネイル）
  python3 crop.py sheet <保存先.png> <画像>...                         一覧画像を作り、まとめて確認する
"""
import argparse, pathlib
from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None


def grid(a):
    im = Image.open(a.src).convert('RGB')
    d = ImageDraw.Draw(im)
    w, h = im.size
    for x in range(0, w, a.step):
        d.line([(x, 0), (x, h)], fill=(255, 0, 0), width=1)
        d.text((x + 2, 2), str(x), fill=(255, 0, 0))
    for y in range(0, h, a.step):
        d.line([(0, y), (w, y)], fill=(0, 0, 255), width=1)
        d.text((2, y + 2), str(y), fill=(0, 0, 255))
    im.save(a.out)
    print('保存:', a.out, im.size)


def cut(a):
    im = Image.open(a.src).convert('RGB')
    box = tuple(round(v * a.scale) for v in (a.x0, a.y0, a.x1, a.y1))
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    c = im.crop(box)
    c.save(a.out, optimize=True)
    print('保存:', a.out, c.size)


def fit(a):
    im = Image.open(a.src).convert('RGB')
    iw, ih = im.size
    if iw / ih > a.ratio:
        nw = round(ih * a.ratio)
        x = (iw - nw) // 2
        im = im.crop((x, 0, x + nw, ih))
    else:
        im = im.crop((0, 0, iw, round(iw / a.ratio)))
    im = im.resize((a.width, round(a.width / a.ratio)), Image.LANCZOS)
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    im.save(a.out, optimize=True)
    print('保存:', a.out, im.size)


def sheet(a):
    cell_w, cell_h, pad = 600, 400, 24
    cols = min(4, len(a.images))
    rows = -(-len(a.images) // cols)
    s = Image.new('RGB', (cols * (cell_w + pad), rows * (cell_h + pad + 20)), (200, 200, 200))
    d = ImageDraw.Draw(s)
    for i, f in enumerate(a.images):
        im = Image.open(f).convert('RGB')
        size = im.size
        im.thumbnail((cell_w, cell_h))
        x, y = (i % cols) * (cell_w + pad), (i // cols) * (cell_h + pad + 20)
        d.text((x + 2, y + 2), f'{pathlib.Path(f).name} {size[0]}x{size[1]}', fill=(0, 0, 0))
        s.paste(im, (x, y + 20))
    s.save(a.out)
    print('保存:', a.out, s.size)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('grid'); p.add_argument('src'); p.add_argument('out'); p.add_argument('--step', type=int, default=100); p.set_defaults(f=grid)
    p = sub.add_parser('cut'); p.add_argument('src')
    for k in ('x0', 'y0', 'x1', 'y1'):
        p.add_argument(k, type=float)
    p.add_argument('out'); p.add_argument('--scale', type=float, default=1.0); p.set_defaults(f=cut)
    p = sub.add_parser('fit'); p.add_argument('src'); p.add_argument('out')
    p.add_argument('--ratio', type=float, default=1.414); p.add_argument('--width', type=int, default=900); p.set_defaults(f=fit)
    p = sub.add_parser('sheet'); p.add_argument('out'); p.add_argument('images', nargs='+'); p.set_defaults(f=sheet)
    a = ap.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()
