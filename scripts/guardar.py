"""Money Pal · Agrega transacciones nuevas a data/transacciones.json.

Recibe uno o más archivos JSON (una lista de transacciones, o la salida de leer_correos.py con "trx"),
filtra por el rango leído, quita duplicados, aplica tus reglas de data/categorias.json y amplía el
periodo cubierto. Así Claude nunca tiene que reescribir el archivo completo.

Uso:
  .venv/bin/python scripts/guardar.py --banco bcp --desde 2026-05-01 --hasta 2026-05-31 data/tmp/bcp-2026-05*.json
  .venv/bin/python scripts/guardar.py --banco interbank --desde 2026-05-01 --hasta 2026-05-31 --automatico data/tmp/*.json

--automatico: las transferencias y retiros nuevos quedan con "pendiente": true para revisarlos luego.
Si no llega ninguna transacción en el rango (ni nueva ni ya guardada), imprime SIN_CORREOS y no amplía
el periodo: significa que antes de esa fecha no hay historial en Gmail.

  .venv/bin/python scripts/guardar.py --periodos    # solo muestra el periodo guardado de cada banco
"""

import argparse
import json
import os
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REVISAR = ("transferencia", "retiro")
RESPALDOS = 10  # copias anteriores que se guardan en data/respaldos/


def leer_entrada(ruta):
    d = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return d["trx"] if isinstance(d, dict) else d


def escribir_seguro(ruta, datos):
    """Guarda sin riesgo de dejar el archivo a medias: respalda la versión anterior en data/respaldos/
    (se quedan las últimas RESPALDOS), escribe a un temporal y lo reemplaza de una sola vez."""
    if ruta.exists():
        respaldos = ruta.parent / "respaldos"
        respaldos.mkdir(exist_ok=True)
        shutil.copy2(ruta, respaldos / f"{ruta.stem}_{datetime.now():%Y-%m-%d_%H%M%S}.json")
        for viejo in sorted(respaldos.glob(f"{ruta.stem}_*.json"))[:-RESPALDOS]:
            viejo.unlink()
    temporal = ruta.with_suffix(".json.tmp")
    with open(temporal, "w", encoding="utf-8") as f:
        f.write(json.dumps(datos, ensure_ascii=False, indent=2))
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporal, ruta)


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
    p.add_argument("--periodos", action="store_true", help="Solo muestra el periodo guardado de cada banco y sale")
    p.add_argument("--desde", help="AAAA-MM-DD, primer día leído (hora local del banco)")
    p.add_argument("--hasta", help="AAAA-MM-DD, último día leído (hora local del banco)")
    p.add_argument("--automatico", action="store_true")
    p.add_argument("--banco", help="Banco leído (carpeta en banks/); su periodo es el que se amplía")
    p.add_argument("--datos", default=str(RAIZ / "data"))
    a = p.parse_args()

    if not Path(a.datos).resolve().is_relative_to(RAIZ / "data"):
        raise SystemExit(f"--datos debe estar dentro de data/ (recibido: {a.datos})")
    if a.periodos:
        ruta = Path(a.datos) / "transacciones.json"
        d = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}
        print(json.dumps(d.get("periodos") or {}, ensure_ascii=False))
        return
    if not (a.desde and a.hasta and a.banco):
        p.error("--banco, --desde y --hasta son obligatorios")
    desde, hasta = date.fromisoformat(a.desde), date.fromisoformat(a.hasta)
    ruta_trx, ruta_cat = Path(a.datos) / "transacciones.json", Path(a.datos) / "categorias.json"
    datos = json.loads(ruta_trx.read_text(encoding="utf-8")) if ruta_trx.exists() else \
        {"periodo": None, "periodos": {}, "transacciones": []}
    if "periodos" not in datos:  # formato anterior (solo existió con el BCP)
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
    datos["actualizado"] = datetime.now().astimezone().isoformat(timespec="seconds")
    ruta_trx.parent.mkdir(exist_ok=True)
    escribir_seguro(ruta_trx, datos)

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
