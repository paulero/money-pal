# BCP · Banco de Crédito del Perú

Reglas para convertir los correos de notificación del BCP en transacciones. El comando [`/leer-bcp`](../../.claude/commands/leer-bcp.md) las aplica.

## Búsqueda en Gmail

```
from:notificaciones@notificacionesbcp.com.pe
```

Filtrar por **remitente**, no por asunto: así se capturan tarjeta de crédito, débito, pagos y transferencias.

**Incluir la papelera** (`includeTrash: true`): muchas personas borran estas notificaciones después de leerlas. Gmail vacía la papelera cada 30 días, así que lo que esté ahí se pierde pronto.

Gmail filtra `after:` / `before:` por día, no por hora de Lima: después de extraer, filtra de nuevo por la fecha en hora de Lima.

## Tipos de correo

| Asunto (contiene) | Tipo | ¿Se cuenta como gasto? |
|---|---|---|
| `Realizaste un consumo con tu Tarjeta de Crédito BCP` | `consumo` · medio `credito` | ✅ Sí |
| `Realizaste un consumo con tu Tarjeta de Débito BCP` | `consumo` · medio `debito` | ✅ Sí (incluye pagos Plin/BIM hechos con la tarjeta) |
| `CONSTANCIA DE PAGO DE SERVICIO` | `pago_servicio` | ✅ Sí (luz, teléfono, seguros…) |
| `Constancia de Transferencia a Terceros` | `transferencia` | ❓ Se pregunta al usuario (puede ser alquiler, cuotas, pagos a personas… o no ser gasto) |
| `Constancia de Transferencia a Otros Bancos` | `transferencia` | ❓ Igual que la anterior. **Si `Enviado a` es el mismo titular, se excluye** (es su propia cuenta en otro banco). El monto a registrar es `Total cobrado` (incluye comisión) |
| `Realizaste un retiro en un cajero` | `retiro` | ❓ Efectivo: se pregunta si cuenta como gasto (el destino del efectivo no se conoce) |
| `Constancia de Transferencia Entre mis Cuentas` | — | ❌ No, es mover tu propio dinero |
| `Constancia de Pago de Tarjeta de Crédito Propia` | — | ❌ No: pagar tu tarjeta no es un gasto nuevo; los consumos ya se contaron uno por uno |
| `Constancia de Pago de Tarjeta de Crédito de Otros Bancos` | — | ❌ No se cuenta, pero **avisa**: los consumos de esa tarjeta no pasan por el BCP. Para verlos hay que agregar ese banco (`banks/<banco>/`) |
| Afiliaciones, actualización de datos, OTP, bienvenida a billetera digital | — | ❌ No |
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

El snippet **no** trae el monto; hay que abrir el correo. Campos: `Empresa`, `Fecha y hora`, `Monto total` (`S/ 98.50` o en dólares, `$ 45.00`), `Cuenta de origen` (p. ej. `Tarjeta de crédito **** 1234`), `Número de operación`.

### Transferencia a terceros

Snippet: `Realizaste una transferencia de S/ 350.00 desde tu Clasica`. El destinatario (`Enviado a`), el `Mensaje` (guárdalo en `nota`, ayuda a categorizar: p. ej. "Mantenimiento") y el `Número de operación` están en el cuerpo.

Transferencias a casas de cambio (p. ej. Kambista) suelen ser **cambio de moneda, no gasto**, y las que van a fondos mutuos o cuentas de inversión (nombres con "FONDO", mensaje "Inversión") son **ahorro, no gasto**: propón excluirlas con esa `nota`.

### Retiro en cajero

Snippet: `Realizaste un retiro de S/ 80.00 con tu Tarjeta de Débito BCP en un Cajero BCP`.

## Cuidados

- **Abrir correos en la papelera:** usa `get_message` (por id de mensaje). `get_thread` falla con "permission" en hilos que están en la papelera.
- **Resultados grandes:** una búsqueda de un mes (~50 hilos) suele superar el límite y Claude Code la guarda en un archivo. No la leas entera: procésala con `scripts/bcp_snippets.py <archivo>`.

- **Duplicados:** un pago de servicio con tarjeta podría llegar también como consumo. Si hay dos registros con el mismo monto, misma empresa y menos de 10 minutos de diferencia, se guarda uno.
- **Nombres de comercio:** el snippet y el cuerpo pueden diferir (`SAC` vs `S.A.C.`). Se usa el del snippet en mayúsculas, sin puntos finales.
- **Privacidad:** de la tarjeta solo se guardan los **últimos 4 dígitos**. No se guarda el nombre del titular.
