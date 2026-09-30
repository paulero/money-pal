---
description: Exporta tus gastos categorizados a Excel y/o PDF en la carpeta output/
argument-hint: "[excel | pdf | ambos] [periodo, p. ej. septiembre | desde 2026-07]"
allowed-tools: Read, Bash(python3 -m venv .venv), Bash(.venv/bin/pip install -q -r requirements.txt), Bash(.venv/bin/python scripts/exportar.py:*), Bash(open output/:*)
---

Eres el exportador de Money Pal. Pedido: **$ARGUMENTS** (si está vacío: Excel y PDF de todo el periodo).

## Pasos

1. **Revisa los datos.** Si no existe `data/transacciones.json`, pide correr `/leer-correos` y detente. Si hay transacciones sin `categoria`, sugiere correr `/categorias revisar` primero (pero puedes continuar si el usuario quiere).
2. **Prepara el entorno** (solo la primera vez): si no existe `.venv/`, corre `python3 -m venv .venv` y `.venv/bin/pip install -q -r requirements.txt`.
3. **Exporta** con `scripts/exportar.py`, traduciendo el pedido a opciones:
   - Formato: `--formato excel | pdf | ambos`.
   - Periodo: `--desde AAAA-MM[-DD]` y `--hasta AAAA-MM[-DD]` (p. ej. "septiembre" → `--desde 2026-09 --hasta 2026-09`).
   - Tipo de cambio: `--tc 3.45` si el usuario lo indica; si no, usa `tipo_cambio_usd` de `data/categorias.json` o 3.50.
4. **Abre** los archivos generados con `open output/<archivo>` (macOS).

## Qué contiene

- **Excel:** *Resumen* (categoría, transacciones, PEN, USD, total aprox., %, presupuesto y diferencia), *Por mes* (categoría × mes), una hoja por mes con el detalle y *Recurrentes* (comercios presentes en 2 o más meses).
- **PDF:** una página con indicadores, gráfico por categoría, tabla resumen, gasto por mes y top 10 comercios.

## Al terminar, muestra

- La ruta de cada archivo generado.
- Un resumen de 3 líneas: gasto total aprox., la categoría más grande y cualquier categoría que pase su presupuesto.
- Recuerda que `output/` no se sube a GitHub.
