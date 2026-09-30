"""Money Pal · Extrae transacciones de resultados de búsqueda de Gmail usando las reglas de un banco.

Cada banco describe sus correos en banks/<banco>/banco.json (remitentes, asuntos, patrones). Este script
no sabe nada de ningún banco en particular: agregar un banco es escribir su banco.json, no código.

Cuando una búsqueda es muy grande, Claude Code la guarda en un archivo; este script la procesa sin
cargarla en la conversación. Los tipos con "fuente": "snippet" salen directo de la vista previa; los de
"fuente": "cuerpo" se listan en "abrir" para leerlos con get_message.

Uso:
  .venv/bin/python scripts/leer_correos.py --banco bcp resultado1.json [...] --salida data/tmp/2026-05.json

Imprime un resumen corto; el detalle queda en --salida:
  {"trx": [...], "abrir": [...], "ignorados": {...}, "avisos": [...], "desconocidos": {...}}
"""

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from privado import proteger_carpetas

RAIZ = Path(__file__).resolve().parent.parent


def cargar_banco(banco_id):
    ruta = RAIZ / "banks" / banco_id / "banco.json"
    if not ruta.exists():
        disponibles = sorted(p.parent.name for p in (RAIZ / "banks").glob("*/banco.json"))
        raise SystemExit(f"No existe {ruta}. Bancos disponibles: {', '.join(disponibles)}")
    banco = json.loads(ruta.read_text(encoding="utf-8"))
    for t in banco["tipos"]:
        if t.get("patron"):
            t["_re"] = re.compile(t["patron"])
    h, m = banco.get("zona_horaria", "+00:00")[1:].split(":")
    signo = -1 if banco.get("zona_horaria", "+").startswith("-") else 1
    banco["_tz"] = timezone(signo * timedelta(hours=int(h), minutes=int(m)))
    return banco


def cargar_resultado(ruta):
    d = json.loads(Path(ruta).read_text(encoding="utf-8"))
    if isinstance(d, list):  # algunos clientes envuelven el resultado: [{"type": "text", "text": "..."}]
        d = json.loads(d[0]["text"])
    return d


def contiene(asunto, textos):
    a = asunto.lower()
    return any(x.lower() in a for x in textos)


def limpiar_asunto(asunto, banco):
    for sufijo in banco.get("limpiar_asunto", []):
        if asunto.endswith(sufijo):
            return asunto[: -len(sufijo)]
    return asunto


def extraer(regla, r, banco, base):
    """Arma una transacción desde los grupos con nombre del patrón y los valores fijos de la regla."""
    g, fijos = r.groupdict(), regla.get("fijos", {})
    return {
        **base,
        "banco": banco["id"],
        "tipo": regla["tipo"],
        "medio": fijos.get("medio") or banco.get("medios", {}).get(g.get("medio"), g.get("medio")),
        "tarjeta": g.get("tarjeta"),
        "moneda": banco["monedas"][g["moneda"]],
        "monto": float(g["monto"].replace(",", "")),
        "comercio": (fijos.get("comercio") or g["comercio"]).strip().upper().rstrip("."),
        "categoria": None,
    }


def procesar(banco, rutas):
    trx, abrir, ignorados, avisos, desconocidos, vistos = [], [], {}, [], {}, set()
    remitentes = [r.lower() for r in banco["remitentes"]]
    for ruta in rutas:
        for hilo in cargar_resultado(ruta).get("threads", []):
            for m in hilo["messages"]:
                if m["id"] in vistos or m.get("sender", "").lower() not in remitentes:
                    continue
                vistos.add(m["id"])
                asunto, snippet = m.get("subject", ""), m.get("snippet", "")
                fecha = datetime.fromisoformat(m["date"].replace("Z", "+00:00")).astimezone(banco["_tz"])
                base = {"id": m["id"], "fecha": fecha.isoformat(timespec="minutes")}

                regla = next((t for t in banco["tipos"] if contiene(asunto, t["asunto_contiene"])), None)
                if regla and regla["fuente"] == "snippet" and (r := regla["_re"].search(snippet)):
                    trx.append(extraer(regla, r, banco, base))
                elif regla:
                    motivo = "snippet incompleto" if regla["fuente"] == "snippet" else "datos en el cuerpo"
                    abrir.append({"id": m["id"], "tipo": regla["tipo"], "fecha": base["fecha"], "motivo": motivo})
                else:
                    clave = limpiar_asunto(asunto, banco)
                    ignorados[clave] = ignorados.get(clave, 0) + 1
                    conocido = next((i for i in banco.get("ignorar", []) if contiene(asunto, [i["asunto_contiene"]])), None)
                    if conocido is None:
                        desconocidos[clave] = desconocidos.get(clave, 0) + 1
                    elif conocido.get("avisar"):
                        avisos.append(f"{base['fecha'][:10]} · {clave}: {conocido['motivo']}")
    return {"trx": trx, "abrir": abrir, "ignorados": ignorados, "avisos": avisos, "desconocidos": desconocidos}


def main():
    p = argparse.ArgumentParser(description="Extrae transacciones de resultados de Gmail con las reglas de un banco.")
    p.add_argument("archivos", nargs="+")
    p.add_argument("--banco", required=True, help="Carpeta del banco en banks/ (p. ej. bcp)")
    p.add_argument("--salida", required=True, help="Archivo JSON de salida (p. ej. data/tmp/2026-05.json)")
    a = p.parse_args()
    proteger_carpetas()

    # Solo dentro de data/tmp/: el texto de los correos no es confiable y nunca debe terminar en un script
    salida = Path(a.salida).resolve()
    if not salida.is_relative_to(RAIZ / "data" / "tmp"):
        raise SystemExit(f"--salida debe estar dentro de data/tmp/ (recibido: {a.salida})")
    res = procesar(cargar_banco(a.banco), a.archivos)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    fechas = sorted(t["fecha"] for t in res["trx"])
    print(f"{len(res['trx'])} transacciones desde snippets" + (f" ({fechas[0][:10]} a {fechas[-1][:10]})" if fechas else ""))
    print(f"{len(res['abrir'])} correos por abrir con get_message:")
    for x in res["abrir"]:
        print(f"  {x['id']}  {x['tipo']:<14} {x['fecha'][:10]}  ({x['motivo']})")
    print("Ignorados por asunto:", json.dumps(res["ignorados"], ensure_ascii=False))
    for aviso in res["avisos"]:
        print("AVISO:", aviso)
    if res["desconocidos"]:
        print("ASUNTOS NUEVOS (revisar si alguno es un gasto):", json.dumps(res["desconocidos"], ensure_ascii=False))
    print(f"Detalle en {salida}")


if __name__ == "__main__":
    main()
