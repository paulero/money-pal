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

Un solo comando programa dos rutinas con `launchd`:

```bash
scripts/instalar-rutinas.sh
```

| Rutina | Cuándo | Qué hace |
|---|---|---|
| Lectura semanal | Lunes 9:00 | `/leer-bcp nuevos` — guarda los correos nuevos del BCP. |
| Cierre de mes | Día 1, 10:00 | `/cierre-de-mes` — compara el mes con tus promedios y genera el reporte. |

**¿Por qué semanal?** Money Pal guarda cada transacción en `data/`, así que después ya no importa si borras el correo. Pero Gmail vacía la papelera a los 30 días: si alguien borra sus notificaciones apenas llegan, una lectura solo mensual podría llegar tarde. Leyendo cada semana, nada se pierde **y nadie tiene que cambiar cómo usa su Gmail**.

- Las rutinas corren sin hacer preguntas: lo dudoso queda como pendiente para `/categorias revisar`.
- Si tu Mac está dormida a esa hora, corren al despertar. Si está apagada, se saltan: `scripts/sincronizar.sh` o `/cierre-de-mes` a mano lo recuperan.
- Probarlas ya: `scripts/sincronizar.sh` · `scripts/cierre-de-mes.sh`.
- Quitarlas: `scripts/instalar-rutinas.sh --quitar`.
- Cada ejecución deja su registro en `output/logs/`.

## Cómo leer los promedios

- Los promedios usan solo **meses completos** anteriores al mes que cierras.
- Si todavía no tienes 6, 12 o 18 meses de historia, el reporte lo dice y promedia los meses que sí hay. Para tener historia desde el primer día, importa tu historial una vez (ver [instalación](instalacion.md#paso-6--importa-tu-historial)).
- Los montos en dólares se convierten a soles con un tipo de cambio aproximado (`tipo_cambio_usd` en `data/categorias.json`, o S/ 3.50).
