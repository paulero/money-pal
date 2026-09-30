"""Money Pal · Resume los correos de un banco para definir su banco.json (lo usa /nuevo-banco).

Agrupa resultados de búsqueda de Gmail (search_threads) por remitente y por asunto, con cantidad,
fechas y un ejemplo de vista previa. La salida es solo para tu terminal: contiene datos reales,
no la copies al repositorio.

Uso:
  .venv/bin/python scripts/explorar_correos.py resultado*.json                   # remitentes
  .venv/bin/python scripts/explorar_correos.py resultado*.json --remitente x@y   # asuntos de un remitente
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path


def mensajes(rutas):
    vistos = set()
    for ruta in rutas:
        d = json.loads(Path(ruta).read_text(encoding="utf-8"))
        if isinstance(d, list):
            d = json.loads(d[0]["text"])
        for hilo in d.get("threads", []):
            for m in hilo["messages"]:
                if m["id"] not in vistos:
                    vistos.add(m["id"])
                    yield m


def main():
    p = argparse.ArgumentParser(description="Resume correos por remitente y asunto.")
    p.add_argument("archivos", nargs="+")
    p.add_argument("--remitente", help="Muestra los asuntos de este remitente")
    p.add_argument("--ejemplos", type=int, default=1, help="Vistas previas de ejemplo por asunto")
    a = p.parse_args()

    grupos = defaultdict(list)
    for m in mensajes(a.archivos):
        clave = m.get("subject", "") if a.remitente else m.get("sender", "")
        if a.remitente and m.get("sender", "").lower() != a.remitente.lower():
            continue
        grupos[clave].append(m)

    titulo = f"Asuntos de {a.remitente}" if a.remitente else "Remitentes"
    print(f"{titulo} ({sum(len(v) for v in grupos.values())} correos)\n")
    for clave, ms in sorted(grupos.items(), key=lambda kv: -len(kv[1])):
        fechas = sorted(m["date"][:10] for m in ms)
        print(f"{len(ms):>4}  {clave}   [{fechas[0]} a {fechas[-1]}]")
        if a.remitente:
            for m in ms[: a.ejemplos]:
                print(f"        {m['id']}: {m.get('snippet', '')[:220]}")


if __name__ == "__main__":
    main()
