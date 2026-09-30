---
description: Agrega un banco nuevo a Money Pal a partir de tus propios correos (sin programar) y prepara la contribución
argument-hint: "<banco, p. ej. interbank>"
allowed-tools: mcp__claude_ai_Gmail__search_threads, mcp__claude_ai_Gmail__get_message, Read, Write, Edit, Bash(.venv/bin/python scripts/explorar_correos.py:*), Bash(.venv/bin/python scripts/leer_correos.py:*), Bash(.venv/bin/python scripts/probar_bancos.py:*), Bash(.venv/bin/python scripts/revisar_privacidad.py:*), Bash(rm -rf data/tmp/nuevo-*)
---

Vas a agregar el banco **$ARGUMENTS** a Money Pal usando los correos de la persona que tiene cuenta ahí. El resultado son **reglas** (`banco.json`) y **pruebas con correos inventados**: nunca datos reales.

Usa `banks/bcp/` como modelo y `banks/README.md` como referencia del formato. Trabaja en español y explica cada paso en una línea.

## Reglas de privacidad (no negociables)

- Gmail solo en lectura.
- Los resultados reales van **solo** a `data/tmp/nuevo-<banco>/` (fuera de git) y se borran al final.
- En `banks/<banco>/` solo puede haber reglas y correos **inventados**. `revisar_privacidad.py` debe pasar antes de proponer la contribución.
- No muestres montos, comercios o nombres reales en el README del banco: usa ejemplos inventados.

## Pasos

1. **Identificador.** Usa un id corto en minúsculas sin espacios (`interbank`, `bbva`, `scotiabank`, `pichincha`). Si `banks/<id>/banco.json` ya existe con estado `verificado`, avisa y detente.

2. **Encuentra el remitente.** Busca con `search_threads` (`includeTrash: true`, `pageSize: 50`) algo como `<nombre del banco> newer_than:180d` y también `from:<nombre>`. Guarda los resultados en `data/tmp/nuevo-<id>/` (si quedaron en un archivo, cópialo con Write; si llegaron en la conversación, guárdalos tal cual) y corre:
   `.venv/bin/python scripts/explorar_correos.py data/tmp/nuevo-<id>/*.json`
   Muestra los remitentes del banco y **pregunta cuál(es) envían los avisos de movimientos** (no la publicidad).

3. **Reúne los asuntos.** Busca `from:<remitente> newer_than:180d` (hasta 4 páginas), guarda en `data/tmp/nuevo-<id>/busqueda-N.json` y corre:
   `.venv/bin/python scripts/explorar_correos.py data/tmp/nuevo-<id>/busqueda-*.json --remitente <remitente> --ejemplos 2`

4. **Clasifica cada asunto** en una tabla: `consumo`, `pago_servicio`, `transferencia`, `retiro` o *ignorar* (con motivo: publicidad, códigos, pagos de tarjeta propia, movimientos entre cuentas propias…). Si la vista previa no alcanza para decidir, abre un ejemplo con `get_message` (`PLAIN_TEXT`). Pregunta lo que no sea evidente.

5. **Escribe `banks/<id>/banco.json`** con `"estado": "muestras"`:
   - `fuente: "snippet"` cuando la vista previa trae monto y comercio; escribe el `patron` con los grupos `moneda`, `monto`, `comercio` y `medio` (o `fijos`).
   - `fuente: "cuerpo"` si no; abre 1–2 ejemplos con `get_message` y anota en `campos` qué etiqueta tiene cada dato, y en `excluir_si` cuándo no es gasto.
   - Todo asunto clasificado como *ignorar* va a `ignorar` con su `motivo`.

6. **Prueba con los correos reales** (no se guardan):
   `.venv/bin/python scripts/leer_correos.py --banco <id> data/tmp/nuevo-<id>/busqueda-*.json --salida data/tmp/nuevo-<id>/resultado.json`
   Debe quedar **sin ASUNTOS NUEVOS**, y los tipos `snippet` no deben caer en "por abrir" salvo vistas previas cortadas. Compara 5 transacciones extraídas con sus vistas previas. Ajusta y repite hasta que cuadre.

7. **Crea las pruebas con correos inventados** en `banks/<id>/pruebas/busqueda-1.json` (y `-2` si quieres probar paginación), con la forma exacta de `search_threads` (`threads` → `messages` con `id`, `date`, `subject`, `snippet`, `sender`):
   - Copia el **texto fijo** de cada asunto y vista previa, pero **inventa** todo lo variable: nombre del saludo (p. ej. "Ana"), comercios, montos, tarjetas, números de operación, fechas e ids (`prueba001`…).
   - Incluye al menos: un correo por cada tipo, una vista previa cortada, un asunto a ignorar, un asunto desconocido, un correo de otro remitente y un mensaje repetido.
   - Sin `toRecipients`, `viewUrl` ni `historyId`.

8. **Revisa la privacidad** (debe pasar):
   `.venv/bin/python scripts/revisar_privacidad.py --banco <id> --reales data/tmp/nuevo-<id>/busqueda-*.json`

9. **Genera y revisa el resultado esperado:**
   `.venv/bin/python scripts/probar_bancos.py <id> --actualizar`, muestra en una tabla lo que devolvió cada correo inventado y confirma que es correcto. Luego `.venv/bin/python scripts/probar_bancos.py` (todos los bancos) debe dar ✅.

10. **Documenta:** crea `banks/<id>/README.md` siguiendo el de `banks/bcp/` (remitente, tabla de tipos, dónde está cada dato, cuidados; ejemplos inventados) y actualiza la tabla de `banks/README.md` con el estado 🧪 muestras.

11. **Úsalo tú primero.** Explica que ya puede leer este banco con `/leer-correos <id> 3 meses` o importar su historial en la Terminal con `scripts/importar-historial.sh 18 <id>`.

12. **Contribuye (con permiso).** Muestra `git status` y un resumen de los archivos nuevos. Confirma que **solo** hay archivos en `banks/<id>/` y `banks/README.md`. Pregunta si quiere proponerlo al proyecto; si dice que sí:
    - Crea la rama `banco-<id>` y haz commit.
    - Si puede escribir en el repositorio (`gh repo view --json viewerPermission`), haz push de la rama; si no, `gh repo fork --remote` y push a su fork.
    - Abre el Pull Request con `gh pr create`: banco, tipos cubiertos, meses revisados y que `revisar_privacidad.py` y `probar_bancos.py` pasaron.

13. **Limpia:** `rm -rf data/tmp/nuevo-<id>`.
