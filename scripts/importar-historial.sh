#!/bin/bash
# Money Pal · Importa tu historial una sola vez: lee Gmail (incluida la papelera) mes por mes, hacia atrás.
# Cada mes corre en una sesión nueva de Claude, así la lectura nunca se satura.
# Uso: scripts/importar-historial.sh [meses=18] [banco ...]
#   scripts/importar-historial.sh 18 interbank      # un banco (la primera vez, siempre indica el banco)
#   scripts/importar-historial.sh 18 bcp interbank  # varios
#   scripts/importar-historial.sh 18                # todos los bancos que ya tienen datos
set -euo pipefail
source "$(dirname "$0")/_claude.sh"

MESES="${1:-18}"
shift || true
BANCOS=("$@")
if [ ${#BANCOS[@]} -eq 0 ]; then
  while IFS= read -r b; do [ -n "$b" ] && BANCOS+=("$b"); done < <(bancos_con_datos)
fi
if [ ${#BANCOS[@]} -eq 0 ]; then
  echo "Indica tu banco. Disponibles: $(ls -d banks/*/ | xargs -n1 basename | tr '\n' ' ')"
  echo "Ejemplo: scripts/importar-historial.sh 18 bcp"
  exit 1
fi

importar_banco() {
  local BANCO="$1"
  [ -f "banks/$BANCO/banco.json" ] || { echo "No existe banks/$BANCO/banco.json (¿quieres agregarlo? /nuevo-banco $BANCO)"; return 1; }

  # Meses a leer, del más reciente al más antiguo: desde donde empieza lo guardado de este banco (o el mes actual) hacia atrás
  local LISTA
  LISTA=$(.venv/bin/python - "$MESES" "$(periodo_desde "$BANCO")" <<'PY'
import sys, datetime as dt
n, desde = int(sys.argv[1]), sys.argv[2]
hoy = dt.date.today()
limite = (hoy.year * 12 + hoy.month - 1) - (n - 1)             # mes más antiguo permitido
if desde:
    d = dt.date.fromisoformat(desde)
    inicio = d.year * 12 + d.month - 1 - (1 if d.day == 1 else 0)  # si el mes ya está completo, empieza en el anterior
else:
    inicio = hoy.year * 12 + hoy.month - 1
print(" ".join(f"{m // 12}-{m % 12 + 1:02d}" for m in range(inicio, limite - 1, -1)))
PY
  )

  if [ -z "$LISTA" ]; then
    echo "$BANCO: ya tienes los últimos $MESES meses guardados."
    return 0
  fi

  echo "Importando $BANCO: $LISTA"
  for MES in $LISTA; do
    local ANTES DESPUES
    ANTES="$(periodo_desde "$BANCO")"
    printf "  %s ... " "$MES"
    correr_claude "/leer-correos $BANCO $MES automatico" "output/logs/historial-$BANCO-$MES.log" \
      || { echo "error (ver output/logs/historial-$BANCO-$MES.log)"; return 1; }
    DESPUES="$(periodo_desde "$BANCO")"
    if [ "$ANTES" = "$DESPUES" ]; then
      echo "sin correos de $BANCO: tu historial en Gmail empieza después de $MES."
      break
    fi
    echo "listo (datos desde $DESPUES)"
  done
}

for BANCO in "${BANCOS[@]}"; do
  importar_banco "$BANCO"
done

avisar "Historial importado. Revisa pendientes con /categorias revisar"
echo "Terminado. Revisa transferencias y comercios nuevos con /categorias revisar."
