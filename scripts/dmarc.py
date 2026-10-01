"""Money Pal · Consulta la política DMARC de los remitentes de un banco.

Cualquiera puede escribir el remitente de un banco en un correo falso. DMARC es la regla que publica el
dominio del banco para que Gmail lo detecte: con "quarantine" o "reject", un aviso falso termina en spam
(Money Pal no lee el spam) o ni llega. Con "none" o sin registro, el falso puede llegar a tu bandeja.
Por eso un banco solo puede estar "verificado" con quarantine o reject.

Uso:
  .venv/bin/python scripts/dmarc.py notificaciones@banco.com.pe     # consulta uno o más remitentes/dominios
  .venv/bin/python scripts/dmarc.py --verificar                     # compara cada banco.json con el DNS actual
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
POLITICAS = ["reject", "quarantine", "none", "sin_registro"]
SEGURAS = ["reject", "quarantine"]


def txt(nombre):
    """Registros TXT de un nombre, vía DNS sobre HTTPS (funciona igual en macOS, Windows, Linux y CI)."""
    url = "https://dns.google/resolve?" + urllib.parse.urlencode({"name": nombre, "type": "TXT"})
    with urllib.request.urlopen(url, timeout=10) as r:
        d = json.load(r)
    return [a["data"].replace('" "', "").strip('"') for a in d.get("Answer", []) if a.get("type") == 16]


def etiquetas(registro):
    return {k.strip().lower(): v.strip().lower() for k, _, v in (p.partition("=") for p in registro.split(";")) if k.strip()}


def politica(dominio):
    """Política DMARC efectiva de un dominio: la suya, o la del dominio padre (sp= si existe)."""
    partes = dominio.lower().split(".")
    for i in range(len(partes) - 1):
        candidato = ".".join(partes[i:])
        registros = [r for r in txt(f"_dmarc.{candidato}") if r.lower().startswith("v=dmarc1")]
        if registros:
            e = etiquetas(registros[0])
            p = e.get("sp", e.get("p")) if i > 0 else e.get("p")
            return p if p in SEGURAS + ["none"] else "sin_registro"
    return "sin_registro"


def dominio_de(remitente):
    return remitente.rsplit("@", 1)[-1].lower()


def verificar():
    errores = []
    for ruta in sorted((RAIZ / "banks").glob("*/banco.json")):
        b = json.loads(ruta.read_text(encoding="utf-8"))
        for dominio in sorted({dominio_de(r) for r in b.get("remitentes", [])}):
            actual, guardada = politica(dominio), b.get("dmarc", {}).get(dominio)
            marca = "✅" if actual == guardada else "❌"
            print(f"{marca} {b['id']}: {dominio} → DNS {actual}, banco.json {guardada}")
            if actual != guardada:
                errores.append(f"{b['id']}: actualiza \"dmarc\": {{\"{dominio}\": \"{actual}\"}} en banco.json")
            elif b.get("estado") == "verificado" and actual not in SEGURAS:
                errores.append(f"{b['id']}: {dominio} bajó a '{actual}'; el banco ya no puede estar 'verificado'")
    for e in errores:
        print("ERROR:", e)
    return not errores


def main():
    p = argparse.ArgumentParser(description="Consulta la política DMARC de remitentes de bancos.")
    p.add_argument("remitentes", nargs="*", help="Correos o dominios")
    p.add_argument("--verificar", action="store_true", help="Compara cada banks/*/banco.json con el DNS")
    a = p.parse_args()
    if a.verificar:
        sys.exit(0 if verificar() else 1)
    if not a.remitentes:
        p.error("indica al menos un remitente o usa --verificar")
    resultado = {dominio_de(r): politica(dominio_de(r)) for r in a.remitentes}
    for dominio, pol in resultado.items():
        nota = "los avisos falsos van a spam o no llegan" if pol in SEGURAS else "un aviso falso podría llegar a tu bandeja"
        print(f"{dominio}: {pol} ({nota})")
    print(json.dumps({"dmarc": resultado}, ensure_ascii=False))


if __name__ == "__main__":
    main()
