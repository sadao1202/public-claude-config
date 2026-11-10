#!/usr/bin/env python3
"""PreToolUse hook: git commit / push のガード。

- main/master 上でのコミットを拒否する
- コミットメッセージが prefix(feat|fix|refactor|docs|chore): で始まらなければ拒否する
- main/master への push(現在ブランチが main/master、または宛先に main/master 指定)を拒否する

stdin に PreToolUse の JSON を受け取り、拒否時は exit 2 + stderr で理由を返す。
判定はコマンド文字列の正規表現。ヒアドキュメント本文と引用符内は、git コマンドの
検出・宛先判定から除外する(本文中の "git push" による誤ブロックを避ける)。
解析できないコマンドは許可する。
"""
import json
import re
import subprocess
import sys

PREFIX = re.compile(r'(?:^|\n|-m\s*["\'])\s*(?:feat|fix|refactor|docs|chore): ')
COMMIT = re.compile(r'(?:^|\s)git(?:\s+-C\s+\S+)?\s+commit\b')
PUSH = re.compile(r'(?:^|\s)git(?:\s+-C\s+\S+)?\s+push\b')
PUSH_TO_MAIN = re.compile(r'\s(?:\S+:)?(?:refs/heads/)?(?:main|master)(?:\s|$)')
HEREDOC = re.compile(r'<<-?\s*([\'"]?)(\w+)\1[^\n]*\n.*?\n\s*\2\b', re.S)
QUOTED = re.compile(r'"(?:\\.|[^"\\])*"|\'[^\']*\'')
SEGMENT = re.compile(r'&&|\|\||[;|\n]')


def skeleton(cmd):
    """ヒアドキュメント本文と引用符内を空にした、構文だけのコマンド文字列。"""
    cmd = HEREDOC.sub(lambda m: "<<" + m.group(2), cmd)
    return QUOTED.sub('""', cmd)


def current_branch(cwd):
    try:
        return subprocess.run(
            ["git", "-C", cwd, "symbolic-ref", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
    except Exception:
        return ""


def main():
    data = json.load(sys.stdin)
    cmd = data.get("tool_input", {}).get("command", "")
    skel = skeleton(cmd)
    segments = SEGMENT.split(skel)
    commits = [s for s in segments if COMMIT.search(s)]
    pushes = [s for s in segments if PUSH.search(s)]
    if not (commits or pushes):
        return 0

    branch = current_branch(data.get("cwd", "."))
    on_main = branch in ("main", "master")

    if pushes and (on_main or any(PUSH_TO_MAIN.search(s) for s in pushes)):
        print("main/master への push は禁止です。dev/<作業概要> ブランチから push して PR を作成してください。", file=sys.stderr)
        return 2

    if commits:
        if on_main:
            print(f"{branch} 上では直接コミットできません。dev/<作業概要> ブランチを切ってください。", file=sys.stderr)
            return 2
        has_message = re.search(r'\s-m\s*["\']|<<', cmd) is not None
        if has_message and not PREFIX.search(cmd):
            print("コミットメッセージは feat|fix|refactor|docs|chore: のいずれかで始めてください(日本語)。", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
