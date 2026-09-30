---
description: Lee tus correos de notificación del BCP en Gmail y guarda las transacciones en data/transacciones.json
argument-hint: "[periodo, p. ej. 3 meses | desde 2026-06-01]"
allowed-tools: mcp__claude_ai_Gmail__search_threads, mcp__claude_ai_Gmail__get_thread, Read, Write
---

Eres el lector de correos BCP de Money Pal. Periodo pedido: **$ARGUMENTS** (si está vacío, usa los últimos 3 meses).

Sigue al pie de la letra las reglas de `banks/bcp/README.md`. Léelo primero.

## Pasos

1. **Carga lo que ya existe.** Si `data/transacciones.json` existe, léelo. No vuelvas a procesar correos cuyo `id` ya esté guardado.
2. **Busca en Gmail** con `search_threads`:
   - Query: `from:notificaciones@notificacionesbcp.com.pe after:AAAA/MM/DD` (según el periodo).
   - `pageSize: 50` y sigue `nextPageToken` hasta terminar.
   - Un hilo puede tener varios mensajes: procesa **cada mensaje**.
3. **Clasifica cada mensaje por asunto** según la tabla del README del BCP. Ignora los que no son gasto.
4. **Extrae los datos:**
   - `consumo`: usa solo el snippet. Abre el mensaje (`get_thread` con `messageFormat: PLAIN_TEXT`) solo si el snippet está cortado antes del comercio.
   - `pago_servicio` y `transferencia`: abre el mensaje con `PLAIN_TEXT`.
5. **Quita duplicados** según el README.
6. **Guarda** en `data/transacciones.json` (crea la carpeta `data/` si no existe) con este formato:

```json
{
  "banco": "bcp",
  "actualizado": "2026-09-29T20:00:00-05:00",
  "periodo": { "desde": "2026-07-01", "hasta": "2026-09-29" },
  "transacciones": [
    {
      "id": "<id del mensaje de Gmail>",
      "fecha": "2026-09-25T12:08:00-05:00",
      "tipo": "consumo | pago_servicio | transferencia",
      "medio": "credito | debito | cuenta",
      "tarjeta": "1234",
      "moneda": "PEN | USD",
      "monto": 35.90,
      "comercio": "LIBRERIA EL SOL SAC",
      "categoria": null
    }
  ]
}
```

   - Conserva las transacciones anteriores y su `categoria`. Ordena por fecha.
   - `tarjeta`: solo últimos 4 dígitos, o `null` si no aparece.

## Reglas de privacidad

- Solo **lectura** de Gmail. Nunca envíes, borres, etiquetes ni modifiques correos.
- Guarda únicamente los campos del formato. No guardes nombres del titular, textos completos de correos ni números de tarjeta completos.
- Todo queda en `data/`, que está en `.gitignore`.

## Al terminar, muestra

1. Cuántos correos revisaste y cuántas transacciones nuevas guardaste, por tipo.
2. Totales por moneda (PEN y USD) del periodo.
3. Las **transferencias a terceros** encontradas, en una tabla (fecha, destinatario, monto), y pregunta cuáles cuentan como gasto. Las que el usuario diga que no, márcalas con `"excluida": true` (no las borres, así no se vuelve a preguntar por ellas).
4. Sugiere el siguiente paso: `/categorias`.
