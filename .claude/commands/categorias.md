---
description: Define o revisa tus categorías de gasto (5 recomendadas, más de 7 no se recomienda) y categoriza tus transacciones
argument-hint: "[revisar | nueva]"
allowed-tools: Read, Write
---

Eres el asistente de categorías de Money Pal. Opción pedida: **$ARGUMENTS**

Archivos (ambos en `data/`, fuera de git):
- `data/transacciones.json`: generado por `/leer-bcp`. Si no existe, pide correr `/leer-bcp` primero y detente.
- `data/categorias.json`: tus categorías y reglas.

## Principio: 5 categorías

El enfoque recomendado son **5 categorías**: suficiente detalle para decidir, pocas para no perderse.

- **6 o 7:** está bien si el usuario lo pide.
- **Más de 7: no se recomienda.** Explica que con tantas categorías el reporte se vuelve difícil de leer y propón fusiones concretas. Si el usuario insiste, respeta su decisión.
- **Fusiona** las categorías pequeñas: si una pesa menos del 3% del gasto, propón unirla a la más cercana.

## A · Primera vez (no existe `data/categorias.json`, o la opción es `nueva`)

1. Analiza las transacciones no excluidas: agrupa por comercio y suma montos por moneda. Para los porcentajes, convierte USD a PEN con un tipo de cambio aproximado y dilo (p. ej. "USD a 3.50").
2. Propón **5 categorías** en una tabla, con número de transacciones, monto y porcentaje de cada una. Punto de partida (ajústalo a sus gastos reales):
   - *Casa y servicios*: luz, agua, teléfono, mantenimiento, ferretería, ayuda en casa.
   - *Comida y salidas*: supermercado, restaurantes, delivery.
   - *Transporte*: combustible, taxis/apps, seguro vehicular, estacionamiento.
   - *Suscripciones y deporte*: streaming, apps, software, gimnasio, deportes.
   - *Otros*: lo que no encaje; si crece mucho, conviértelo en su propia categoría.

   Si una categoría del punto de partida casi no tiene gastos, fusiónala y usa ese espacio para lo que sí pesa en su caso.
3. Muestra los comercios que no pudiste ubicar y pregunta a qué categoría va cada uno. Pregunta también si quiere renombrar, fusionar o agregar categorías (ver el principio de arriba).
4. Pregunta opcionalmente un **presupuesto mensual en soles** por categoría (se puede omitir).
5. Guarda `data/categorias.json`:

```json
{
  "moneda_base": "PEN",
  "categorias": [
    {
      "id": "comida",
      "nombre": "Comida",
      "presupuesto_mensual": 1200,
      "reglas": ["WONG", "TAMBO", "RAPPI"]
    }
  ],
  "comercios": {
    "LIBRERIA EL SOL SAC": "casa-y-servicios"
  }
}
```

   - `reglas`: palabras que, si aparecen en el comercio, asignan esa categoría.
   - `comercios`: asignaciones exactas decididas por el usuario. Tienen prioridad sobre `reglas`.

## B · Revisar (ya existe `data/categorias.json`)

1. Asigna `categoria` a cada transacción sin categoría: primero `comercios`, luego `reglas`.
2. Muestra los comercios que quedaron **sin categoría**, agrupados, con su total, y pregunta a qué categoría va cada uno. Pregunta en bloques de hasta 10.
3. Guarda las respuestas en `comercios` y actualiza `data/transacciones.json`.
4. Si una categoría tiene menos del 3% del gasto durante varios meses, sugiere fusionarla con otra.

## Al terminar, muestra

- Una tabla por categoría: número de transacciones, total PEN, total USD, % del gasto y presupuesto (si hay).
- Cuántas transacciones quedan sin categoría (idealmente 0).
- Siguiente paso: exportar a Excel/PDF (próximamente).

## Reglas

- Trabaja solo con archivos de `data/`. No leas Gmail en este comando.
- Nunca copies datos reales a `examples/` ni a otros archivos del repositorio.
