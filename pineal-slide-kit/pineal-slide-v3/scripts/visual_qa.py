#!/usr/bin/env python3
"""pptx を PDF 化 → 画像化し、目視QA用の JPEG を出す。

  visual_qa.py --file <deck>.pptx                  # 全ページ（PowerPointで描画）
  visual_qa.py --file <deck>.pptx --pages 16-18    # 範囲指定
  visual_qa.py --file <deck>.pptx --engine libreoffice   # PowerPointが無い環境用（明示したときだけ使う）

## エンジンの違い（重要）

  powerpoint（既定） 実際の Microsoft PowerPoint に AppleScript で PDF を吐かせる。
                     Office同梱フォント（Meiryo UI / 游ゴシック / MS Gothic）が
                     正しく描画され、レイアウトも実機と一致する。
                     → 書体の確認にも使える。
  libreoffice        soffice に変換させる。PowerPoint が無くても動くが、
                     Office同梱フォントを見ないため**別フォントに置換される**。
                     レイアウト検証にのみ使うこと。書体の確認には使えない。

⚠️ python-pptx はテキストの折返しを計算しない。
   「文字を入れた」だけでは 見切れ・重なり・下端超過(7.5in) は検出できない。
   必ずこのスクリプトを通し、出力画像を実際に見ること。

⚠️ powerpoint エンジンは PowerPoint を操作する。実行中は手を触れないこと。
   対象ファイルを PowerPoint で開いたままだと失敗するので、先に閉じる。
   失敗したら libreoffice へ自動では切り替えず、エラーで止まる。
   初回や新しいフォルダでは PowerPoint がファイルアクセスの許可ダイアログを出す（-9074）。
   ダイアログは人が許可する。
"""
import argparse, glob, os, shutil, subprocess, sys, tempfile

SOFFICE = shutil.which("soffice") or "/Applications/LibreOffice.app/Contents/MacOS/soffice"
PPT_APP = "/Applications/Microsoft PowerPoint.app"


def export_powerpoint(src, outdir):
    """実際の PowerPoint に PDF を吐かせる（書体・レイアウトが実機と一致）

    PowerPoint はサンドボックスのため /tmp 等へ直接書けない（エラー -9074）。
    元ファイルと同じフォルダへ出力してから作業ディレクトリへ移す。
    """
    tmp_pdf = os.path.splitext(src)[0] + ".__qa__.pdf"
    if os.path.exists(tmp_pdf):
        os.remove(tmp_pdf)
    lock = os.path.join(os.path.dirname(src), "~$" + os.path.basename(src))
    if os.path.exists(lock):
        print("⚠️ ロックファイルあり。対象を PowerPoint で開いたままの可能性があります", file=sys.stderr)
    script = f'''
    tell application "Microsoft PowerPoint"
        -- 既定の120秒では、起動直後や枚数の多い資料の PDF 保存が終わらず -1712 になる
        with timeout of 600 seconds
            activate
            delay 2
            open POSIX file "{src}"
            delay 4
            save active presentation in POSIX file "{tmp_pdf}" as save as PDF
            delay 3
            close active presentation saving no
        end timeout
    end tell
    '''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=660)
    if r.returncode != 0:
        err = r.stderr.strip()
        print(f"ERROR: AppleScript失敗: {err}", file=sys.stderr)
        if "-9074" in err:
            print("  （サンドボックスの書き込み制限。出力先を元ファイルの隣にしても出た場合は、"
                  "PowerPointを一度手動で起動してフォルダアクセスを許可する）", file=sys.stderr)
        return None
    if not os.path.exists(tmp_pdf) or os.path.getsize(tmp_pdf) < 2000:
        print("ERROR: PDF出力に失敗（サイズ異常）", file=sys.stderr)
        return None
    pdf = os.path.join(outdir, "qa.pdf")
    shutil.move(tmp_pdf, pdf)     # 案件フォルダにPDFを残さない
    return pdf


def export_libreoffice(src, outdir):
    ascii_pptx = os.path.join(outdir, "qa.pptx")   # 非ASCII名は pdftoppm が開けない
    shutil.copy(src, ascii_pptx)
    subprocess.run([SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", outdir, ascii_pptx],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    pdf = os.path.join(outdir, "qa.pdf")
    return pdf if os.path.exists(pdf) else None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", required=True)
    ap.add_argument("--pages", default=None, help="例: 3 / 16-18")
    ap.add_argument("--dpi", type=int, default=90)
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--engine", choices=["powerpoint", "libreoffice"], default="powerpoint")
    a = ap.parse_args()

    src = os.path.abspath(a.file)
    if not os.path.exists(src):
        sys.exit(f"見つからない: {src}")

    engine = a.engine
    if engine == "powerpoint" and not os.path.exists(PPT_APP):
        sys.exit("PowerPoint が無い。書体を確認しない前提なら --engine libreoffice を明示して再実行する")

    work = a.outdir or tempfile.mkdtemp(prefix="pptxqa_")
    os.makedirs(work, exist_ok=True)
    for f in glob.glob(os.path.join(work, "qa-*.jpg")):
        os.remove(f)

    pdf = export_powerpoint(src, work) if engine == "powerpoint" else export_libreoffice(src, work)
    # PowerPoint 失敗時に libreoffice へ黙って切り替えない。
    # 切り替えると明朝に置換された画像で合否を判断してしまう（2026-09-19 に発生）。
    if pdf is None and engine == "powerpoint":
        sys.exit("PowerPoint での PDF 出力に失敗。対象を閉じる、-9074 ならフォルダアクセスを許可してから再実行する")
    if pdf is None:
        sys.exit("PDF変換に失敗。対象を PowerPoint で開いたままになっていないか確認する")

    cmd = ["pdftoppm", "-jpeg", "-r", str(a.dpi)]
    if a.pages:
        f_, l_ = a.pages.split("-") if "-" in a.pages else (a.pages, a.pages)
        cmd += ["-f", f_, "-l", l_]
    cmd += [pdf, os.path.join(work, "qa")]
    subprocess.run(cmd, check=True)

    imgs = sorted(glob.glob(os.path.join(work, "qa-*.jpg")))
    print(f"エンジン: {engine}")
    print(f"出力 {len(imgs)} 枚:")
    for i in imgs:
        print("  ", i)
    if engine == "libreoffice":
        print("\n⚠️ libreoffice は Office同梱フォントを見ない。書体の確認には使えない")
    print("\n↑ 画像を開いて、見切れ・重なり・下端超過(7.5in)を確認する")


if __name__ == "__main__":
    main()
