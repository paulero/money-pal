#!/bin/bash
# Money Pal · Rutina de cierre de mes sin supervisión (para launchd o cron).
# Uso: scripts/cierre-de-mes.sh [AAAA-MM]
set -euo pipefail
source "$(dirname "$0")/_claude.sh"

correr_claude "/cierre-de-mes ${1:-} automatico" "output/logs/cierre-$(date +%Y-%m-%d).log"
avisar "Tu reporte de cierre de mes está en output/"
