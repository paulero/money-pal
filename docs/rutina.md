# Rutina de fin de mes

Cada mes, Money Pal puede cerrar el mes solo: lee tus gastos nuevos, los categoriza, los compara con tus promedios de los **últimos 3, 6, 12 y 18 meses** y deja el reporte en `output/`.

## Manual (recomendado al empezar)

Dentro de Claude Code, en la carpeta `money-pal`:

```
/cierre-de-mes            # cierra el mes anterior
/cierre-de-mes 2026-09    # cierra un mes específico
```

Te preguntará lo que no sepa (transferencias, comercios nuevos) y al final verás:

- Gasto total del mes vs. tu promedio de 3 meses.
- Categorías en ⚠️ (más de 20% y S/ 100 sobre su promedio de 3 meses) y qué comercios lo explican.
- `output/money-pal_cierre_AAAA-MM.xlsx` y `.pdf`, con la hoja/sección **Cierre de mes** al inicio.

Sin Claude, solo el comparativo:

```bash
.venv/bin/python scripts/comparar.py --mes 2026-09
.venv/bin/python scripts/exportar.py --cierre 2026-09
```

## Automática (macOS)

El script [`scripts/cierre-de-mes.sh`](../scripts/cierre-de-mes.sh) corre la rutina **sin hacer preguntas**: lo dudoso queda como pendiente para que lo revises con `/categorias revisar`. Para programarlo el día 1 de cada mes a las 9:00 con `launchd`:

```bash
cd money-pal
RUTA="$(pwd)"
cat > ~/Library/LaunchAgents/com.moneypal.cierre.plist <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.moneypal.cierre</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$RUTA/scripts/cierre-de-mes.sh</string></array>
  <key>StartCalendarInterval</key>
  <dict><key>Day</key><integer>1</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardErrorPath</key><string>$RUTA/output/logs/launchd.err</string>
</dict>
</plist>
PLIST
mkdir -p output/logs
launchctl load ~/Library/LaunchAgents/com.moneypal.cierre.plist
```

- Si tu Mac está dormida a esa hora, la rutina corre al despertar. Si está apagada, se salta ese mes: córrela a mano.
- Para probarla ya: `launchctl start com.moneypal.cierre` (o `scripts/cierre-de-mes.sh`).
- Para desactivarla: `launchctl unload ~/Library/LaunchAgents/com.moneypal.cierre.plist`.
- El registro de cada ejecución queda en `output/logs/`.

## Cómo leer los promedios

- Los promedios usan solo **meses completos** anteriores al mes que cierras.
- Si todavía no tienes 6, 12 o 18 meses de historia, el reporte lo dice y promedia los meses que sí hay. Para tener historia desde el inicio, corre `/leer-bcp 18 meses` una vez (si tus correos siguen en Gmail).
- Los montos en dólares se convierten a soles con un tipo de cambio aproximado (`tipo_cambio_usd` en `data/categorias.json`, o S/ 3.50).
