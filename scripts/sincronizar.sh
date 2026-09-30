#!/bin/bash
# Money Pal · Lectura semanal: guarda los correos nuevos del BCP antes de que puedan borrarse.
# Uso: scripts/sincronizar.sh
set -euo pipefail
source "$(dirname "$0")/_claude.sh"

correr_claude "/leer-correos nuevos automatico" "output/logs/sincronizar-$(date +%Y-%m-%d).log"
