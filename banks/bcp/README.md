# BCP · Banco de Crédito del Perú

Reglas para convertir los correos de notificación del BCP en transacciones. El comando [`/leer-bcp`](../../.claude/commands/leer-bcp.md) las aplica.

## Búsqueda en Gmail

```
from:notificaciones@notificacionesbcp.com.pe
```

Filtrar por **remitente**, no por asunto: así se capturan tarjeta de crédito, débito, pagos y transferencias.

## Tipos de correo

| Asunto (contiene) | Tipo | ¿Se cuenta como gasto? |
|---|---|---|
| `Realizaste un consumo con tu Tarjeta de Crédito BCP` | `consumo` · medio `credito` | ✅ Sí |
| `Realizaste un consumo con tu Tarjeta de Débito BCP` | `consumo` · medio `debito` | ✅ Sí (incluye pagos Plin/BIM hechos con la tarjeta) |
| `CONSTANCIA DE PAGO DE SERVICIO` | `pago_servicio` | ✅ Sí (luz, teléfono, seguros…) |
| `Constancia de Transferencia a Terceros` | `transferencia` | ❓ Se pregunta al usuario (puede ser alquiler, cuotas, pagos a personas… o no ser gasto) |
| `Constancia de Transferencia Entre mis Cuentas` | — | ❌ No, es mover tu propio dinero |
| Estados de cuenta (`estadodecuenta@…`), comprobantes (`comprobante-electronico@…`), publicidad (`bcpcomunica@…`) | — | ❌ No |

## Dónde está cada dato

### Consumo (crédito o débito)

El **snippet** (vista previa) ya trae casi todo, sin abrir el correo:

> Hola ___, Realizaste un consumo de **S/ 35.90** con tu **Tarjeta de Crédito** BCP en **LIBRERIA EL SOL SAC**. Por tu seguridad…

- Moneda y monto: `S/` → `PEN`, `$` → `USD`.
- Medio: `Tarjeta de Crédito` / `Tarjeta de Débito`.
- Comercio: el texto entre `BCP en ` y `. Por tu seguridad`.
- Fecha y hora: la fecha del correo convertida a hora de Lima (UTC−5).

El cuerpo completo agrega `Número de Tarjeta` (`************1234`), `Fecha y hora` y `Número de operación`. Solo se abre si el snippet está incompleto.

### Pago de servicio

El snippet **no** trae el monto; hay que abrir el correo. Campos: `Empresa`, `Fecha y hora`, `Monto total` (`S/ 98.50`), `Cuenta de origen` (p. ej. `Tarjeta de crédito **** 1234`), `Número de operación`.

### Transferencia a terceros

Snippet: `Realizaste una transferencia de S/ 350.00 desde tu Clasica`. El destinatario (`Enviado a`) y el `Número de operación` están en el cuerpo.

## Cuidados

- **Duplicados:** un pago de servicio con tarjeta podría llegar también como consumo. Si hay dos registros con el mismo monto, misma empresa y menos de 10 minutos de diferencia, se guarda uno.
- **Nombres de comercio:** el snippet y el cuerpo pueden diferir (`SAC` vs `S.A.C.`). Se usa el del snippet en mayúsculas, sin puntos finales.
- **Privacidad:** de la tarjeta solo se guardan los **últimos 4 dígitos**. No se guarda el nombre del titular.
