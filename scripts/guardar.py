"""Money Pal · Agrega transacciones nuevas a data/transacciones.json.

Recibe uno o más archivos JSON (una lista de transacciones, o la salida de leer_correos.py con "trx"),
filtra por el rango leído, quita duplicados, aplica tus reglas de data/categorias.json y amplía el
periodo cubierto. Así Claude nunca tiene que reescribir el archivo completo.

Uso:
  .venv/bin/python scripts/guardar.py --desde 2026-05-01 --hasta 2026-05-31 data/tmp/2026-05*.json
  .venv/bin/python scripts/guardar.py --desde 2026-05-01 --hasta 2026-05-31 --automatico data/tmp/*.json

--automatico: las transferencias y retiros nuevos quedan con "pendiente": true para revisarlos luego.
Si no llega ninguna transacción en el rango (ni nueva ni ya guardada), imprime SIN_CORREOS y no amplía
el periodo: significa que antes de esa fecha no hay historial en Gmail.
"""

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LIMA = timezone(timedelta(hours=-5))
REVISAR = ("transferencia", "retiro")


def leer_entrada(ruta):
    d = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return d["trx"] if isinstance(d, dict) else d


def categorizar(t, cats):
    """Primero asignaciones exactas por comercio, luego reglas por palabra."""
    if t["comercio"] in cats.get("comercios", {}):
        return cats["comercios"][t["comercio"]]
    for c in cats.get("categorias", []):
        if any(r in t["comercio"] for r in c.get("reglas", [])):
            return c["id"]
    return None


def ampliar_periodo(periodo, desde, hasta):
    """Solo amplía si el rango nuevo toca o se superpone al actual (el periodo debe ser continuo)."""
    if not periodo:
        return {"desde": desde.isoformat(), "hasta": hasta.isoformat()}, True
    p_desde, p_hasta = date.fromisoformat(periodo["desde"]), date.fromisoformat(periodo["hasta"])
    if desde > p_hasta + timedelta(days=1) or hasta < p_desde - timedelta(days=1):
        return periodo, False
    return {"desde": min(desde, p_desde).isoformat(), "hasta": max(hasta, p_hasta).isoformat()}, True


def periodo_comun(periodos):
    """Rango cubierto por TODOS los bancos: los promedios solo usan meses con datos completos de cada uno."""
    rangos = [p for p in periodos.values() if p]
    if not rangos:
        return None
    desde, hasta = max(p["desde"] for p in rangos), min(p["hasta"] for p in rangos)
    return {"desde": desde, "hasta": hasta} if desde <= hasta else None


def main():
    p = argparse.ArgumentParser(description="Agrega transacciones nuevas a data/transacciones.json.")
    p.add_argument("archivos", nargs="*")
    p.add_argument("--desde", required=True, help="AAAA-MM-DD, primer día leído (hora de Lima)")
    p.add_argument("--hasta", required=True, help="AAAA-MM-DD, último día leído (hora de Lima)")
    p.add_argument("--automatico", action="store_true")
    p.add_argument("--banco", default="bcp", help="Banco leído (carpeta en banks/); su periodo es el que se amplía")
    p.add_argument("--datos", default=str(RAIZ / "data"))
    a = p.parse_args()

    desde, hasta = date.fromisoformat(a.desde), date.fromisoformat(a.hasta)
    ruta_trx, ruta_cat = Path(a.datos) / "transacciones.json", Path(a.datos) / "categorias.json"
    datos = json.loads(ruta_trx.read_text(encoding="utf-8")) if ruta_trx.exists() else \
        {"periodo": None, "periodos": {}, "transacciones": []}
    if "periodos" not in datos:  # formato anterior: un solo banco
        datos["periodos"] = {datos.pop("banco", "bcp"): datos["periodo"]} if datos.get("periodo") else {}
    cats = json.loads(ruta_cat.read_text(encoding="utf-8")) if ruta_cat.exists() else {}

    existentes = {t["id"] for t in datos["transacciones"]}
    nuevas, fuera, en_rango = [], 0, 0
    for archivo in a.archivos:
        for t in leer_entrada(archivo):
            if not desde <= datetime.fromisoformat(t["fecha"]).date() <= hasta:
                fuera += 1
                continue
            en_rango += 1
            if t["id"] in existentes:
                continue
            t.setdefault("banco", a.banco)
            t.setdefault("categoria", None)
            if not t.get("excluida") and not t["categoria"]:
                t["categoria"] = categorizar(t, cats)
            if a.automatico and t["tipo"] in REVISAR and not t.get("excluida"):
                t["pendiente"] = True
            existentes.add(t["id"])
            nuevas.append(t)

    if not en_rango:
        print(f"SIN_CORREOS: no hay transacciones de {a.banco} entre {desde} y {hasta}; el periodo no se amplía.")
        return

    periodo, continuo = ampliar_periodo(datos["periodos"].get(a.banco), desde, hasta)
    datos["periodos"][a.banco] = periodo
    datos["periodo"] = periodo_comun(datos["periodos"])
    datos["transacciones"] = sorted(datos["transacciones"] + nuevas, key=lambda t: t["fecha"])
    datos["actualizado"] = datetime.now(LIMA).isoformat(timespec="seconds")
    ruta_trx.parent.mkdir(exist_ok=True)
    ruta_trx.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    por_tipo = {}
    for t in nuevas:
        por_tipo[t["tipo"]] = por_tipo.get(t["tipo"], 0) + 1
    sin_cat = sum(1 for t in nuevas if not t.get("excluida") and not t["categoria"])
    pendientes = sum(1 for t in nuevas if t.get("pendiente"))
    print(f"GUARDADO: {len(nuevas)} nuevas {por_tipo} · {sin_cat} sin categoría · {pendientes} pendientes · "
          f"{fuera} fuera de rango · {a.banco}: {periodo['desde']} a {periodo['hasta']}")
    if not continuo:
        print("AVISO: el rango no es continuo con el periodo guardado; el periodo no se amplió.")


if __name__ == "__main__":
    main()
