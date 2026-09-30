#!/bin/bash
# Money Pal · Funciones compartidas por los scripts que corren Claude Code sin supervisión.

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"
mkdir -p output/logs

# Prepara el entorno de Python la primera vez
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt
fi

# Herramientas permitidas: Gmail solo lectura, archivos del proyecto y los scripts de Money Pal
HERRAMIENTAS=(
  "mcp__claude_ai_Gmail__search_threads" "mcp__claude_ai_Gmail__get_message" "mcp__claude_ai_Gmail__get_thread"
  "Read" "Write" "Edit"
  "Bash(.venv/bin/python scripts/leer_correos.py:*)" "Bash(.venv/bin/python scripts/guardar.py:*)"
  "Bash(.venv/bin/python scripts/comparar.py:*)" "Bash(.venv/bin/python scripts/exportar.py:*)"
  "Bash(rm -rf data/tmp)"
)

# correr_claude "<prompt>" <archivo_log>
correr_claude() {
  claude -p "$1" --allowedTools "${HERRAMIENTAS[@]}" > "$2" 2>&1
}

# Inicio del periodo guardado de un banco (AAAA-MM-DD), o vacío si aún no hay datos de ese banco
# Uso: periodo_desde <banco>
periodo_desde() {
  [ -f data/transacciones.json ] && .venv/bin/python - "$1" <<'PY' || true
import json, sys
d = json.load(open("data/transacciones.json"))
periodos = d.get("periodos") or ({"bcp": d["periodo"]} if d.get("periodo") else {})
print((periodos.get(sys.argv[1]) or {}).get("desde", ""))
PY
}

avisar() {
  command -v osascript >/dev/null && osascript -e "display notification \"$1\" with title \"Money Pal\"" || true
}
