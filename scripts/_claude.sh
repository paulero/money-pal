#!/bin/bash
# Money Pal · Funciones compartidas por los scripts que corren Claude Code sin supervisión.

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"
umask 077  # tus archivos, solo para tu usuario (ver scripts/privado.py)
mkdir -p data output/logs
chmod -R go-rwx data output
# Los registros incluyen resúmenes de tus gastos: solo se guardan 90 días
find output/logs -type f -mtime +90 -delete

# Prepara el entorno de Python la primera vez
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt
fi

# Herramientas permitidas: Gmail solo lectura, leer el proyecto, escribir SOLO en data/ y output/, y los scripts.
# El texto de los correos no es confiable: si un correo trae instrucciones, Claude no puede tocar scripts/,
# .claude/ ni nada fuera del proyecto. "Edit(ruta)" cubre también Write.
HERRAMIENTAS=(
  "mcp__claude_ai_Gmail__search_threads" "mcp__claude_ai_Gmail__get_message" "mcp__claude_ai_Gmail__get_thread"
  "Read(./**)" "Edit(./data/**)" "Edit(./output/**)"
  "Bash(.venv/bin/python scripts/leer_correos.py:*)" "Bash(.venv/bin/python scripts/guardar.py:*)"
  "Bash(.venv/bin/python scripts/comparar.py:*)" "Bash(.venv/bin/python scripts/exportar.py:*)"
  "Bash(rm -rf data/tmp)"
)

# correr_claude "<prompt>" <archivo_log>
# dontAsk: todo lo que no esté en HERRAMIENTAS se rechaza, aunque tu configuración de Claude Code sea más permisiva.
correr_claude() {
  claude -p "$1" --permission-mode dontAsk --allowedTools "${HERRAMIENTAS[@]}" > "$2" 2>&1
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

# Bancos con datos guardados (uno por línea). Los bancos se agregan la primera vez que se leen.
bancos_con_datos() {
  [ -f data/transacciones.json ] && .venv/bin/python - <<'PY' || true
import json
d = json.load(open("data/transacciones.json"))
periodos = d.get("periodos") or ({"bcp": d["periodo"]} if d.get("periodo") else {})
print("\n".join(periodos))
PY
}

avisar() {
  command -v osascript >/dev/null && osascript -e "display notification \"$1\" with title \"Money Pal\"" || true
}
