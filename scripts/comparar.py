"""Money Pal · Cierre de mes: compara un mes contra el promedio de los últimos 3, 6, 12 y 18 meses.

Uso:
  .venv/bin/python scripts/comparar.py                 # último mes completo
  .venv/bin/python scripts/comparar.py --mes 2026-09
  .venv/bin/python scripts/comparar.py --ejemplo

Imprime una tabla en Markdown. `exportar.py --cierre AAAA-MM` usa este módulo para
agregar la hoja "Cierre de mes" al Excel y una página al PDF.
"""

import argparse
import calendar
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VENTANAS = (3, 6, 12, 18)
SIN_CATEGORIA = "Sin categoría"
# Una categoría se marca si el mes supera su promedio de 3 meses en más de este % y este monto
ALERTA_PCT, ALERTA_MONTO = 0.20, 100


def mes_anterior(clave, n=1):
    a, m = map(int, clave.split("-"))
    m -= n
    while m < 1:
        a, m = a - 1, m + 12
    return f"{a}-{m:02d}"


def meses_cubiertos(periodo):
    """Meses completos dentro del periodo leído (un mes a medias no entra a los promedios)."""
    desde, hasta = date.fromisoformat(periodo["desde"]), date.fromisoformat(periodo["hasta"])
    meses, a, m = set(), desde.year, desde.month
    while (a, m) <= (hasta.year, hasta.month):
        completo = date(a, m, 1) >= desde and date(a, m, calendar.monthrange(a, m)[1]) <= hasta
        if completo:
            meses.add(f"{a}-{m:02d}")
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    return meses


def ultimo_mes_completo(periodo):
    cubiertos = meses_cubiertos(periodo)
    return max(cubiertos) if cubiertos else None


def comparar(trx, cats, periodo, mes, tc):
    """Devuelve filas por categoría con el gasto del mes y los promedios de cada ventana."""
    nombres = {c["id"]: c["nombre"] for c in cats.get("categorias", [])}
    gasto = defaultdict(float)  # (categoria, mes) -> soles aprox.
    for t in trx:
        if t.get("excluida"):
            continue
        cid = t.get("categoria") if t.get("categoria") in nombres else None
        gasto[(cid, t["fecha"][:7])] += t["monto"] * (tc if t["moneda"] == "USD" else 1)

    cubiertos = meses_cubiertos(periodo)
    ventanas = {}
    for n in VENTANAS:
        previos = [mes_anterior(mes, i) for i in range(1, n + 1)]
        ventanas[n] = [m for m in previos if m in cubiertos]

    ids = list(nombres) + ([None] if any(k[0] is None for k in gasto) else [])
    filas = []
    for cid in ids + ["__total__"]:
        sel = ids if cid == "__total__" else [cid]
        fila = {"id": cid, "nombre": "Total" if cid == "__total__" else nombres.get(cid, SIN_CATEGORIA),
                "mes": sum(gasto[(c, mes)] for c in sel), "promedios": {}}
        for n, previos in ventanas.items():
            fila["promedios"][n] = (sum(gasto[(c, m)] for c in sel for m in previos) / len(previos)) if previos else None
        base = fila["promedios"][3]
        fila["alerta"] = bool(cid != "__total__" and base is not None
                              and fila["mes"] - base > max(ALERTA_MONTO, base * ALERTA_PCT))
        filas.append(fila)
    return filas, {n: len(v) for n, v in ventanas.items()}


def variacion(actual, base):
    if base is None:
        return None
    if base == 0:
        return None if actual == 0 else float("inf")
    return actual / base - 1


def texto_variacion(v):
    if v is None:
        return "—"
    if v == float("inf"):
        return "nuevo"
    return f"{v:+.0%}"


def nota_historia(disponibles):
    """Una sola frase sobre las ventanas que aún no tienen todos sus meses."""
    cortas = [n for n in VENTANAS if disponibles[n] < n]
    if not cortas:
        return ""
    grupos = defaultdict(list)
    for n in cortas:
        grupos[disponibles[n]].append(f"{n}")
    partes = [f"los de {'/'.join(v)} meses usan {k} mes(es)" for k, v in grupos.items()]
    return "Aún falta historia: " + "; ".join(partes) + "."


def markdown(filas, disponibles, mes):
    enc = ["Categoría", f"{mes}"] + [f"Prom. {n}m" + ("" if disponibles[n] == n else f" ({disponibles[n]})")
                                      for n in VENTANAS] + ["vs 3m"]
    lineas = ["| " + " | ".join(enc) + " |", "|" + "---|" * len(enc)]
    for f in filas:
        prom = [f"S/ {f['promedios'][n]:,.0f}" if f["promedios"][n] is not None else "—" for n in VENTANAS]
        nombre = f"**{f['nombre']}**" if f["id"] == "__total__" else f["nombre"] + (" ⚠️" if f["alerta"] else "")
        lineas.append("| " + " | ".join([nombre, f"S/ {f['mes']:,.0f}", *prom,
                                          texto_variacion(variacion(f["mes"], f["promedios"][3]))]) + " |")
    return "\n".join(lineas + ["", nota_historia(disponibles)])


def cargar(ejemplo=False):
    base = RAIZ / "examples" if ejemplo else RAIZ / "data"
    sufijo = ".ejemplo.json" if ejemplo else ".json"
    datos = json.loads((base / f"transacciones{sufijo}").read_text(encoding="utf-8"))
    ruta_cat = base / f"categorias{sufijo}"
    cats = json.loads(ruta_cat.read_text(encoding="utf-8")) if ruta_cat.exists() else {"categorias": []}
    return datos, cats


def main():
    p = argparse.ArgumentParser(description="Compara un mes con los promedios de 3, 6, 12 y 18 meses.")
    p.add_argument("--mes", help="AAAA-MM (por defecto, el último mes completo)")
    p.add_argument("--tc", type=float, help="Tipo de cambio USD→PEN")
    p.add_argument("--ejemplo", action="store_true", help="Usa los datos ficticios de examples/")
    a = p.parse_args()

    datos, cats = cargar(a.ejemplo)
    mes = a.mes or ultimo_mes_completo(datos["periodo"])
    if not mes:
        raise SystemExit("Aún no hay un mes completo de datos. Corre /leer-bcp con un periodo más largo.")
    tc = a.tc or cats.get("tipo_cambio_usd") or 3.50
    filas, disponibles = comparar(datos["transacciones"], cats, datos["periodo"], mes, tc)
    print(f"Cierre de {mes} (USD a S/ {tc:.2f}, aprox.)\n")
    print(markdown(filas, disponibles, mes))


if __name__ == "__main__":
    main()
