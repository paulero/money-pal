#!/bin/bash
# Money Pal · Lectura semanal: guarda los correos nuevos de todos tus bancos antes de que puedan borrarse.
# Uso: scripts/sincronizar.sh
set -euo pipefail
source "$(dirname "$0")/_claude.sh"

if [ -z "$(bancos_con_datos)" ]; then
  echo "Aún no hay datos. Importa tu banco primero: scripts/importar-historial.sh 18 <banco>" >&2
  exit 1
fi
correr_claude "/leer-correos nuevos automatico" "output/logs/sincronizar-$(date +%Y-%m-%d).log"
