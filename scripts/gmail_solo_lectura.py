"""Money Pal · Gmail en solo lectura, con lista de permitidos (hook PreToolUse de Claude Code).

.claude/settings.json lo corre antes de cada herramienta de Gmail. Solo deja pasar las de LECTURA; cualquier
otra (incluidas las que el conector agregue en el futuro) se bloquea. La lista "deny" de settings.json queda
como segunda capa, pero una lista de bloqueados no cubre herramientas nuevas: esta sí.

Claude Code envía por stdin {"tool_name": "...", ...}. Salida 0 = permitido; salida 2 = bloqueado (el motivo
va por stderr y Claude lo ve).
"""

import json
import sys

PREFIJO = "mcp__claude_ai_Gmail__"
LECTURA = {"search_threads", "get_message", "get_thread"}


def permitido(herramienta):
    return not herramienta.startswith(PREFIJO) or herramienta[len(PREFIJO):] in LECTURA


def main():
    try:
        herramienta = json.load(sys.stdin).get("tool_name", "")
    except (json.JSONDecodeError, AttributeError):
        print("Money Pal: no se pudo leer la herramienta; Gmail queda bloqueado por seguridad.", file=sys.stderr)
        sys.exit(2)
    if not permitido(herramienta):
        print(f"Money Pal usa Gmail solo en lectura: '{herramienta}' no está permitido "
              f"(solo {', '.join(sorted(LECTURA))}).", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
