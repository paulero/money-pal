# Bancos

Cada banco o institución vive en su propia carpeta. **Agregar un banco es escribir datos, no código**: el parser [`scripts/leer_correos.py`](../scripts/leer_correos.py) es el mismo para todos.

```
banks/
└── <banco>/
    ├── banco.json          # reglas: remitentes, tipos de correo, patrones, qué ignorar
    ├── README.md           # las mismas reglas explicadas para personas
    └── pruebas/
        ├── busqueda-1.json # correos FICTICIOS con la forma real de los del banco
        └── esperado.json   # lo que el parser debe devolver
```

| Banco | Estado |
|---|---|
| [BCP](bcp/) | ✅ verificado |
| BBVA, Interbank, Scotiabank, Pichincha | 📋 buscado — ¿tienes cuenta? Corre `/nuevo-banco` |

Estados: `verificado` (probado con correos reales por varios meses) · `muestras` (definido con correos de una persona, falta más uso) · `buscado` (aún no existe).

## Agrega tu banco (sin programar)

Si tienes cuenta en un banco que aún no está y recibes sus avisos de movimientos en Gmail:

1. Sigue la [instalación](../docs/instalacion.md) (Claude Code + Gmail).
2. En la carpeta `money-pal`, abre Claude Code y escribe `/nuevo-banco <banco>` (p. ej. `/nuevo-banco interbank`).
3. Claude encuentra el remitente, clasifica los tipos de correo, escribe `banco.json`, lo prueba con tus correos reales **sin guardarlos**, crea pruebas con correos **inventados**, verifica con [`revisar_privacidad.py`](../scripts/revisar_privacidad.py) que no se filtre nada tuyo y, si aceptas, abre el Pull Request.

Tus correos nunca salen de tu computadora: al repositorio solo llegan las reglas y los correos inventados.

## Formato de `banco.json`

Usa [`bcp/banco.json`](bcp/banco.json) como plantilla.

| Campo | Qué es |
|---|---|
| `id` | Nombre de la carpeta (`bcp`, `interbank`…). |
| `nombre`, `pais`, `estado` | Nombre visible, país (`PE`) y estado (ver arriba). |
| `zona_horaria` | Hora local de las fechas, p. ej. `-05:00`. |
| `remitentes` | Correos desde los que el banco envía las notificaciones. |
| `limpiar_asunto` | Textos que se quitan del final del asunto al reportarlo (opcional). |
| `monedas` | Símbolo en el correo → código (`"S/": "PEN"`, `"$": "USD"`). |
| `medios` | Texto en el correo → `credito` / `debito` (opcional). |
| `tipos` | Una entrada por tipo de correo que **es** un movimiento (ver abajo). |
| `ignorar` | Asuntos conocidos que **no** son gasto, con su `motivo`. `"avisar": true` los muestra al usuario. |

Cada entrada de `tipos`:

| Campo | Qué es |
|---|---|
| `tipo` | `consumo`, `pago_servicio`, `transferencia` o `retiro`. |
| `asunto_contiene` | Textos que identifican el asunto (sin distinguir mayúsculas). |
| `fuente` | `snippet` si la vista previa trae los datos; `cuerpo` si hay que abrir el correo. |
| `patron` | Solo `snippet`: expresión regular con grupos `(?P<moneda>)`, `(?P<monto>)`, `(?P<comercio>)`, `(?P<medio>)` y opcional `(?P<tarjeta>)`. |
| `fijos` | Valores que no vienen en el correo (p. ej. `"comercio": "RETIRO CAJERO"`). |
| `campos` | Solo `cuerpo`: qué etiqueta del correo tiene cada dato (Claude los lee con `get_message`). |
| `excluir_si` | Solo `cuerpo`: condiciones en que el movimiento no es gasto (cuenta propia, casa de cambio, inversión). |

Un asunto del remitente que no esté en `tipos` ni en `ignorar` aparece como **ASUNTO NUEVO** para revisarlo: así el banco puede cambiar sus correos sin que se pierdan movimientos en silencio.

## Pruebas

Las pruebas usan **solo correos inventados** (nombres, montos, comercios y tarjetas ficticios) con la misma forma que los reales. Así cualquiera puede revisar un banco sin tener cuenta en él:

```bash
.venv/bin/python scripts/probar_bancos.py            # todos
.venv/bin/python scripts/probar_bancos.py bcp        # uno
```

`probar_bancos.py` valida `banco.json` (campos, patrones y grupos) y compara la salida del parser con `esperado.json`. Incluye en tus pruebas al menos un correo de cada tipo, una vista previa cortada, un asunto a ignorar y uno desconocido.

**Nunca subas correos reales**, ni siquiera parcialmente.
