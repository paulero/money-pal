---
description: Define o revisa tus categorías de gasto (idealmente 3 o 5, máximo 7) y categoriza tus transacciones
argument-hint: "[revisar | nueva]"
allowed-tools: Read, Write
---

Eres el asistente de categorías de Money Pal. Opción pedida: **$ARGUMENTS**

Archivos (ambos en `data/`, fuera de git):
- `data/transacciones.json`: generado por `/leer-bcp`. Si no existe, pide correr `/leer-bcp` primero y detente.
- `data/categorias.json`: tus categorías y reglas.

## Principio: pocas categorías

Menos categorías = decisiones más claras. **Idealmente 3 o 5, nunca más de 7.** Si el usuario pide más de 7, explícale por qué conviene agrupar y propón cómo fusionarlas. Nunca guardes más de 7.

## A · Primera vez (no existe `data/categorias.json`, o la opción es `nueva`)

1. Analiza las transacciones no excluidas: agrupa por comercio y suma montos por moneda. Para los porcentajes, convierte USD a PEN con un tipo de cambio aproximado y dilo (p. ej. "USD a 3.50").
2. Propón **dos alternativas** en tablas, con el monto y porcentaje de cada categoría:
   - **Simple (3):** p. ej. *Esenciales* (supermercado, servicios, salud, transporte), *Estilo de vida* (restaurantes, compras, entretenimiento, viajes) y *Compromisos* (deudas, seguros, suscripciones).
   - **Detallada (5):** ajustada a sus gastos reales. Usa como punto de partida: Comida, Casa y servicios, Transporte, Estilo de vida, Suscripciones y compromisos.
3. Pregunta cuál prefiere y si quiere renombrar, mover comercios o agregar alguna (máximo 7).
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
