#!/usr/bin/env bash
# PostToolUse hook: when a Python source file in this project is edited,
# remind Claude to keep README.md in sync. Emits additionalContext only
# for .py files (README edits and everything else are ignored).
set -euo pipefail

file_path="$(jq -r '.tool_input.file_path // empty')"

case "$file_path" in
  *README.md) exit 0 ;;
  *.py) ;;
  *) exit 0 ;;
esac

cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"NOTE: A Python source file in this project was just modified. If this change affects anything documented in README.md (features, tools, setup, usage, configuration, or project structure), update README.md in the same session so it stays accurate."}}
JSON
