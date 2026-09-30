#!/bin/bash
# Money Pal · Ejecuta la rutina de cierre de mes sin supervisión (para launchd o cron).
# Uso: scripts/cierre-de-mes.sh [AAAA-MM]
set -euo pipefail

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$(dirname "$0")/.."

mkdir -p output/logs
LOG="output/logs/cierre-$(date +%Y-%m-%d).log"

claude -p "/cierre-de-mes ${1:-} automatico" \
  --allowedTools "mcp__claude_ai_Gmail__search_threads" "mcp__claude_ai_Gmail__get_message" \
                 "mcp__claude_ai_Gmail__get_thread" "Read" "Write" \
                 "Bash(.venv/bin/python scripts/bcp_snippets.py:*)" "Bash(.venv/bin/python scripts/comparar.py:*)" \
                 "Bash(.venv/bin/python scripts/exportar.py:*)" "Bash(python3 -m venv .venv)" \
                 "Bash(.venv/bin/pip install -q -r requirements.txt)" \
  > "$LOG" 2>&1

# Aviso en macOS cuando termina (opcional)
command -v osascript >/dev/null && osascript -e 'display notification "Tu reporte de cierre de mes está en output/" with title "Money Pal"' || true
