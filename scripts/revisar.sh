#!/bin/bash
# Money Pal · Abre la página para revisar, aprobar y cambiar tus categorías (solo en tu computadora).
# Uso: scripts/revisar.sh
set -euo pipefail
cd "$(dirname "$0")/.."
umask 077
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
exec "$PY" scripts/revisar.py "$@"
