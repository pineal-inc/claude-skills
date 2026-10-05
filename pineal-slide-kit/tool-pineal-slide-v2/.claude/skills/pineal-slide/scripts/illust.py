#!/usr/bin/env python3
"""資料に貼るイラストを、テンプレのイラストと同じ線画の画風で Gemini に描かせる。

  python3 illust.py --out assets/ill/ill-xxx.jpg [--aspect 16:9] [--ref 参照画像]... "Scene: ..."

- 環境変数 GEMINI_API_KEY が要る。Google AI Studio で発行した自分のキーを使い、1枚ごとに利用料がかかる
- 場面は英語で書く。人数・位置関係・手元の物・画面に映るもの・構図を具体的に書く
- 画風の指定（線画・白背景・顔なし・赤は小物1点・文字なし）はこのスクリプトが付ける
- 参照画像はテンプレの ill-before.jpg が既定。--ref を渡すと既定に足す
- 同じ資料の2枚目以降は、できたイラストを --ref に渡すと線や人物の描き方がそろう
- 保存先が .jpg なら JPEG にする
"""
import argparse, base64, io, json, os, pathlib, subprocess, sys, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[4]
DEFAULT_REF = ROOT / 'templates/html/assets/product/ill-before.jpg'
MODEL = 'gemini-3-pro-image-preview'
STYLE = ("Draw a new illustration in exactly the same style as the reference image: clean black line art on a pure white background, "
         "uniform medium stroke weight, no shading, no gradients, no gray fills, faceless round heads, business suits, simple flat perspective. "
         "Use a single small accent of red (#D21E2C) only on one tiny object. No text, no letters, no numbers, no logos anywhere in the image. ")


def part(path):
    mime = 'image/png' if path.suffix.lower() == '.png' else 'image/jpeg'
    return {'inlineData': {'mimeType': mime, 'data': base64.b64encode(path.read_bytes()).decode()}}


def save(data, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() not in ('.jpg', '.jpeg'):
        out.write_bytes(data)
        return
    try:
        from PIL import Image
        Image.open(io.BytesIO(data)).convert('RGB').save(out, quality=90, optimize=True)
    except ImportError:
        tmp = out.with_suffix('.tmp.png')
        tmp.write_bytes(data)
        subprocess.run(['sips', '-s', 'format', 'jpeg', str(tmp), '--out', str(out)], check=True, capture_output=True)
        tmp.unlink()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('scene', help='場面の説明（英語）')
    ap.add_argument('--out', required=True, type=pathlib.Path)
    ap.add_argument('--aspect', default='16:9', choices=['1:1', '3:4', '4:3', '9:16', '16:9', '21:9'])
    ap.add_argument('--size', default='2K', choices=['1K', '2K', '4K'])
    ap.add_argument('--ref', action='append', default=[], type=pathlib.Path, help='参照画像を足す（複数可）')
    ap.add_argument('--model', default=MODEL)
    a = ap.parse_args()

    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        sys.exit('GEMINI_API_KEY が設定されていません')
    refs = [DEFAULT_REF] + a.ref
    for r in refs:
        if not r.exists():
            sys.exit(f'参照画像がありません: {r}')

    body = {'contents': [{'parts': [part(r) for r in refs] + [{'text': STYLE + a.scene}]}],
            'generationConfig': {'responseModalities': ['IMAGE'], 'imageConfig': {'aspectRatio': a.aspect, 'imageSize': a.size}}}
    req = urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{a.model}:generateContent',
                                 data=json.dumps(body).encode(), headers={'x-goog-api-key': key, 'Content-Type': 'application/json'})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=300))
    except urllib.error.HTTPError as e:
        sys.exit(f'API エラー {e.code}: {e.read()[:500].decode(errors="ignore")}')
    for p in (r.get('candidates') or [{}])[0].get('content', {}).get('parts', []):
        if 'inlineData' in p:
            save(base64.b64decode(p['inlineData']['data']), a.out)
            print('保存:', a.out)
            return
    sys.exit('画像が返りませんでした: ' + json.dumps(r, ensure_ascii=False)[:500])


if __name__ == '__main__':
    main()
