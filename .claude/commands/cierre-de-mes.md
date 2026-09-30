---
description: Rutina de fin de mes — lee los gastos nuevos, categoriza, compara con los últimos 3/6/12/18 meses y genera el reporte
argument-hint: "[AAAA-MM] [automatico]"
allowed-tools: mcp__claude_ai_Gmail__search_threads, mcp__claude_ai_Gmail__get_message, mcp__claude_ai_Gmail__get_thread, Read, Write, Edit, Bash(.venv/bin/python scripts/leer_correos.py:*), Bash(.venv/bin/python scripts/guardar.py:*), Bash(rm -rf data/tmp), Bash(.venv/bin/python scripts/comparar.py:*), Bash(.venv/bin/python scripts/exportar.py:*), Bash(python3 -m venv .venv), Bash(.venv/bin/pip install -q -r requirements.txt)
---

Eres la rutina de cierre de mes de Money Pal. Argumentos: **$ARGUMENTS**

- **Mes a cerrar:** el `AAAA-MM` indicado; si no hay, el mes calendario anterior a hoy.
- **Modo automático:** si los argumentos incluyen `automatico`, nadie está mirando: **no hagas preguntas**. Deja lo dudoso como pendiente y repórtalo al final.

## Pasos

1. **Lee los gastos nuevos** siguiendo `.claude/commands/leer-correos.md` (modo `nuevos`, todos tus bancos), hasta el último día del mes a cerrar. `guardar.py` amplía el periodo; en modo automático usa `--automatico` (transferencias y retiros quedan pendientes).
2. **Categoriza** siguiendo `.claude/commands/categorias.md` (opción B · revisar). En modo automático, lo que no encaje en `comercios` ni `reglas` queda con `categoria: null` (no lo mandes a Otros sin preguntar).
3. **Compara:** `.venv/bin/python scripts/comparar.py --mes AAAA-MM`. La salida ya incluye qué comercios explican cada ⚠️ y las notas de las transferencias; no escribas scripts propios para esto.
4. **Genera el reporte:** `.venv/bin/python scripts/exportar.py --cierre AAAA-MM` (crea `.venv` antes si no existe).
5. **Escribe el resumen** en `output/cierre_AAAA-MM.md` y muéstralo:
   - Gasto total del mes y su diferencia con el promedio de 3 meses.
   - Las categorías con ⚠️ y **qué comercios explican la subida** (los 3 más grandes de cada una).
   - Una o dos observaciones útiles (p. ej. un gasto recurrente nuevo o una categoría que bajó mucho). Sin juicios ni consejos de inversión.
   - **Pendientes:** transferencias/retiros por confirmar y comercios sin categoría. Indica que se resuelven con `/categorias revisar`.
   - Rutas del Excel y el PDF.

## Reglas

- Gmail solo en lectura. Todo queda en `data/` y `output/` (fuera de git).
- Si falta historia para una ventana (6, 12 o 18 meses), dilo en una línea; no inventes promedios.
