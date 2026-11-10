# settings.json 修正案(説明)

**参考用の完成形は同じディレクトリの `settings.json`**(permissions / env / hooks のみ)。`~/.claude/settings.json` は上書きせず、既存の設定にマージする(配列は既存の項目と重複させず結合し、`env` `hooks` はキー単位で足す)。UI 等の個人設定はここに含めない。
以下の各節は、完成版の各ブロックの意図と出典。

`~/.claude/settings.json` は**手動で**反映する(セキュリティに関わるため、Claude は `~/.claude` を直接編集しない)。
このファイルは提案のみ。反映後は `/permissions` と `/hooks` で確認する。

## 1. permissions

評価順は deny → ask → allow（最初に一致したものが有効）。
出典: https://code.claude.com/docs/en/permissions

```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf *)",
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(git push --force *)",
      "Bash(git push -f *)",
      "Bash(git reset --hard *)",
      "Read(.env)",
      "Read(.env.*)",
      "Read(~/.ssh/**)",
      "Read(**/*.pem)"
    ],
    "ask": [
      "Bash(gh pr merge *)"
    ]
  }
}
```

- deny の基本は `rm -rf` / `curl` / `wget` / `.env` 系の読み取り。加えて force push / hard reset / 秘密鍵の読み取りを拒否する。
- `ask` はマージだけを人間の確認に回す（「エージェントの承認は人間の承認にならない」）。dev/* ブランチからの push と PR 作成は確認なしで行ってよい運用。
- main/master への push は hook（`guard-git-commit.py`）が拒否する。
- 注意: `Bash(curl *)` の deny は `gh` や WebFetch 経路を塞がない。

## 2. env

```json
{
  "env": {
    "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "1"
  }
}
```

公式の既定ではサブエージェントは3階層まで入れ子にできる。global/CLAUDE.md の「サブエージェントは他を呼べない」を設定で担保する。
（現状も各 agent の `tools` に Agent が無いため実質成立している。二重の担保。）
出典: https://code.claude.com/docs/en/sub-agents

## 3. hooks

`hooks/guard-git-commit.py` を PreToolUse (Bash) に登録する。main/master 上のコミットと、prefix(`feat|fix|refactor|docs|chore:`)違反のメッセージを exit 2 で拒否する。
hook の deny は permission mode では回避できない。
注意: `command` 内の `$HOME/claude-config` は例。`$HOME` が展開されるかは未確認。環境に合わせてパスを書き換え、不安なら絶対パスにする。
出典: https://code.claude.com/docs/en/hooks-guide#hooks-and-permission-modes

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -I $HOME/claude-config/hooks/guard-git-commit.py"
          }
        ]
      }
    ]
  }
}
```

テスト済みのケース: prefix 正常(`-m` / heredoc)、prefix 違反(`-m` / heredoc)、非commitコマンド、`git -C` 経由、main ブランチ上（未コミットの空リポジトリ含む）。
限界: コマンド文字列の正規表現による判定。変数展開や複雑なシェル構文は解析できず、その場合は許可する。

## 4. 未対応（要検証）

- **tester の Bash 制限**: tools の allowlist だけでは Bash 経由の書き込みを防げない。subagent の frontmatter `hooks` で PreToolUse を付ける方式を想定しているが、未検証。
- **Stop hook**（変更ありでテスト未実行なら続行させる）: 任意。連続8回ブロックで打ち切られる。
- **sandbox**: WSL2 / Linux 等で利用可(対応環境は公式ドキュメントを確認)。Bash のみが対象で、File ツールや hook は対象外。
  出典: https://code.claude.com/docs/en/sandboxing
