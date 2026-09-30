"""Money Pal · Verifica que las pruebas de un banco no contengan datos de correos reales.

Compara banks/<banco>/pruebas/*.json con los resultados de búsqueda reales que usaste para definir el
banco. Marca como sensible todo lo que varía entre correos (montos, comercios, números, códigos), el
nombre del saludo, las direcciones de destinatario y los ids de Gmail. El texto fijo de la plantilla
del banco ("Realizaste un consumo de…") sí puede repetirse.

Uso:
  .venv/bin/python scripts/revisar_privacidad.py --banco interbank --reales data/tmp/busqueda-*.json
Sale con código 1 si encuentra algo.
"""

import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from leer_correos import cargar_banco  # noqa: E402

SALUDO = re.compile(r"\b(?:Hola|Estimad[oa])\s+([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]+)?)",
                    re.IGNORECASE)
MONTO = re.compile(r"\d[\d,]*\.\d{2}")
CODIGO = re.compile(r"(?<![\d.,])\d{4,}(?![\d.,])")


def cargar(ruta):
    d = json.loads(Path(ruta).read_text(encoding="utf-8"))
    if isinstance(d, list) and d and isinstance(d[0], dict) and "text" in d[0]:
        d = json.loads(d[0]["text"])
    return d


def mensajes(d):
    for hilo in d.get("threads", []) if isinstance(d, dict) else []:
        yield from hilo.get("messages", [])


def es_redondo(monto):
    valor = float(monto.replace(",", ""))
    return valor == int(valor) and int(valor) % 10 == 0


def sensibles(rutas_reales, banco):
    """Valores que identifican a una persona: comercios/destinatarios, montos no redondos, códigos,
    el nombre del saludo, destinatarios del correo e ids de Gmail."""
    textos, palabras = set(), set()
    for ruta in rutas_reales:
        for m in mensajes(cargar(ruta)):
            snippet = m.get("snippet", "")
            palabras |= {m["id"].lower(), m.get("threadId", "").lower()}
            palabras |= {x.lower() for x in m.get("toRecipients", []) + m.get("ccRecipients", [])}
            for nombre in SALUDO.findall(snippet):
                palabras |= {w.lower() for w in nombre.split() if len(w) > 2}
            palabras |= {x for x in MONTO.findall(snippet) if not es_redondo(x)}
            palabras |= {x for x in CODIGO.findall(snippet) if not 2000 <= int(x) <= 2099}
            for t in banco["tipos"]:
                r = t.get("_re") and t["_re"].search(snippet)
                if r and r.groupdict().get("comercio"):
                    textos.add(r["comercio"].strip().lower())
    return textos, {p for p in palabras if p}


def main():
    p = argparse.ArgumentParser(description="Busca datos reales en las pruebas de un banco.")
    p.add_argument("--banco", required=True)
    p.add_argument("--reales", nargs="+", required=True, help="Resultados de búsqueda reales (no se suben)")
    a = p.parse_args()

    textos, palabras = sensibles(a.reales, cargar_banco(a.banco))
    hallazgos = []
    for ruta in sorted((RAIZ / "banks" / a.banco / "pruebas").glob("*.json")):
        texto = ruta.read_text(encoding="utf-8")
        for campo in ("toRecipients", "ccRecipients", "bccRecipients", "viewUrl", "historyId"):
            if f'"{campo}"' in texto:
                hallazgos.append(f"{ruta.name}: quita el campo '{campo}'")
        bajo = texto.lower()
        tokens = set(re.findall(r"[\w@.\-]+", bajo))
        for t in sorted(palabras & tokens):
            hallazgos.append(f"{ruta.name}: contiene '{t}', que aparece en tus correos reales")
        for t in sorted(x for x in textos if x in bajo):
            hallazgos.append(f"{ruta.name}: contiene el comercio o destinatario real '{t}'")
    if hallazgos:
        print("❌ Las pruebas contienen datos que parecen reales. Cámbialos por valores inventados:")
        for h in hallazgos:
            print("   -", h)
        sys.exit(1)
    print(f"✅ Ningún dato de tus {len(a.reales)} archivo(s) reales aparece en banks/{a.banco}/pruebas/ "
          f"({len(textos) + len(palabras)} valores revisados).")


if __name__ == "__main__":
    main()
