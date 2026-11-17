#!/usr/bin/env python3
"""Gemini に平文の書き直しを依頼する。stdin に下書き、--brief に要点や口調の指示。
gemini CLI (v0.1.4) はライセンスエラーで動かないため REST API を直接叩く。"""
import argparse, json, os, sys, urllib.request
import subprocess

SYSTEM = """あなたは下書きの書き手本人です。下書きの内容と順序を保ったまま、人間が普段書く自然な日本語のビジネス文に書き直してください。
制約: ダッシュ記号（――、—、–）を使わない。絵文字なし。箇条書きは使わず文章で。
「非常に」「極めて」「大幅に」「伴走」「寄り添う」「ソリューション」は使わない。
出力は本文のみ。前置きや説明を付けない。"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", default="", help="追加指示（宛先、長さ、口調など）")
    ap.add_argument("--model", default=os.environ.get("GEMINI_REWRITE_MODEL", "gemini-4-argon"))
    a = ap.parse_args()
    draft = sys.stdin.read()
    key = os.environ.get("GEMINI_API_KEY") or subprocess.run(["security", "find-generic-password", "-a", os.environ.get("USER", ""), "-s", os.environ.get("GEMINI_KEYCHAIN_SERVICE", "GEMINI_API_KEY"), "-w"], capture_output=True, text=True).stdout.strip() or sys.exit("GEMINI_API_KEY が環境変数にも Keychain にもない")
    prompt = SYSTEM + ("\n\n追加指示: " + a.brief if a.brief else "") + "\n\n---下書き---\n" + draft
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{a.model}:generateContent?key={key}"
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    r = urllib.request.urlopen(urllib.request.Request(url, body, {"Content-Type": "application/json"}), timeout=120)
    print(json.load(r)["candidates"][0]["content"]["parts"][0]["text"].strip())

if __name__ == "__main__":
    main()
