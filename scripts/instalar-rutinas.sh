#!/bin/bash
# Money Pal · Programa las rutinas en macOS (launchd):
#   - Lectura semanal: lunes 9:00, guarda los correos nuevos antes de que puedan borrarse.
#   - Cierre de mes: día 1 a las 10:00, compara el mes con tus promedios y genera el reporte.
# Uso: scripts/instalar-rutinas.sh            (instalar)
#      scripts/instalar-rutinas.sh --quitar   (desinstalar)
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
AGENTES="$HOME/Library/LaunchAgents"

plist() {  # plist <etiqueta> <script> <intervalo en XML>
  cat <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$1</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$RAIZ/scripts/$2</string></array>
  <key>StartCalendarInterval</key>
  $3
  <key>StandardErrorPath</key><string>$RAIZ/output/logs/launchd-$2.err</string>
</dict>
</plist>
PLIST
}

for ETIQUETA in com.moneypal.sincronizar com.moneypal.cierre; do
  launchctl unload "$AGENTES/$ETIQUETA.plist" 2>/dev/null || true
  rm -f "$AGENTES/$ETIQUETA.plist"
done
if [ "${1:-}" = "--quitar" ]; then
  echo "Rutinas de Money Pal desinstaladas."
  exit 0
fi

mkdir -p "$AGENTES" "$RAIZ/output/logs"
plist com.moneypal.sincronizar sincronizar.sh \
  "<dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>" \
  > "$AGENTES/com.moneypal.sincronizar.plist"
plist com.moneypal.cierre cierre-de-mes.sh \
  "<dict><key>Day</key><integer>1</integer><key>Hour</key><integer>10</integer><key>Minute</key><integer>0</integer></dict>" \
  > "$AGENTES/com.moneypal.cierre.plist"
for ETIQUETA in com.moneypal.sincronizar com.moneypal.cierre; do
  plutil -lint -s "$AGENTES/$ETIQUETA.plist"
  launchctl load "$AGENTES/$ETIQUETA.plist"
done
echo "Listo: lectura semanal (lunes 9:00) y cierre de mes (día 1, 10:00)."
echo "Registros en output/logs/. Para quitarlas: scripts/instalar-rutinas.sh --quitar"
