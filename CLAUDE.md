# claude-config

使い方・構成は README.md を参照。

## 注意点
- `global/CLAUDE.md` は `~/.claude/CLAUDE.md` に symlink され、**全PJに効く**。編集は全PJの挙動に影響するため、変更前にユーザーと合意する。
- このリポジトリ直下の `CLAUDE.md`(本ファイル)は、このリポジトリ作業時のみ効く。global と混同しない。
- コミット規約・ブランチ名は `rules/git-workflow.md` に従う(ここに複製しない)。
- `~/.claude/settings.json` は管理外。編集せず、修正案は `proposals/` に置く。
- symlink の張り直しなどリポジトリ外(`~/.claude`)の操作は、ユーザーの指示なく実行しない。
- `plan/` は gitignore 対象。
