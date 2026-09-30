"""Money Pal · Extrae transacciones BCP de resultados de búsqueda de Gmail (search_threads) guardados en archivo.

Cuando una búsqueda de un mes es muy grande, Claude Code guarda el resultado en un archivo. Este script
lo procesa sin cargarlo en la conversación: los consumos y retiros salen directo del snippet; los pagos
de servicio y transferencias se listan en "abrir" porque necesitan el cuerpo del correo (get_message).

Uso:
  .venv/bin/python scripts/bcp_snippets.py resultado1.json [resultado2.json ...] --salida data/tmp/2026-05.json

Imprime un resumen corto; el detalle queda en --salida: {"trx": [...], "abrir": [...], "ignorados": {...}}
"""

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

LIMA = timezone(timedelta(hours=-5))
CONSUMO = re.compile(r"consumo de (S/|\$) ([\d,]+\.\d{2}) con tu Tarjeta de (Crédito|Débito) BCP en (.+?)\. Por tu seguridad")
RETIRO = re.compile(r"retiro de (S/|\$) ([\d,]+\.\d{2})")
TRANSFERENCIAS = ("Transferencia a Terceros", "Transferencia a Otros Bancos", "Transferencia Interbancaria")


def cargar(ruta):
    d = json.loads(Path(ruta).read_text(encoding="utf-8"))
    if isinstance(d, list):  # algunos clientes envuelven el resultado: [{"type": "text", "text": "..."}]
        d = json.loads(d[0]["text"])
    return d


def moneda(simbolo):
    return "PEN" if simbolo == "S/" else "USD"


def procesar(rutas):
    trx, abrir, ignorados, vistos = [], [], {}, set()
    for ruta in rutas:
        for hilo in cargar(ruta).get("threads", []):
            for m in hilo["messages"]:
                if m["id"] in vistos:
                    continue
                vistos.add(m["id"])
                asunto, snippet = m.get("subject", ""), m.get("snippet", "")
                fecha = datetime.fromisoformat(m["date"].replace("Z", "+00:00")).astimezone(LIMA)
                base = {"id": m["id"], "fecha": fecha.isoformat(timespec="minutes")}

                if "Realizaste un consumo" in asunto and (r := CONSUMO.search(snippet)):
                    trx.append({**base, "tipo": "consumo", "medio": "credito" if r[3] == "Crédito" else "debito",
                                "tarjeta": None, "moneda": moneda(r[1]), "monto": float(r[2].replace(",", "")),
                                "comercio": r[4].strip().upper().rstrip("."), "categoria": None})
                elif "Realizaste un retiro" in asunto and (r := RETIRO.search(snippet)):
                    trx.append({**base, "tipo": "retiro", "medio": "debito", "tarjeta": None, "moneda": moneda(r[1]),
                                "monto": float(r[2].replace(",", "")), "comercio": "RETIRO CAJERO", "categoria": None})
                elif "Realizaste un consumo" in asunto or "Realizaste un retiro" in asunto:
                    abrir.append({"id": m["id"], "tipo": "consumo" if "consumo" in asunto else "retiro",
                                  "fecha": base["fecha"], "motivo": "snippet incompleto"})
                elif "PAGO DE SERVICIO" in asunto.upper():
                    abrir.append({"id": m["id"], "tipo": "pago_servicio", "fecha": base["fecha"]})
                elif any(x in asunto for x in TRANSFERENCIAS):
                    abrir.append({"id": m["id"], "tipo": "transferencia", "fecha": base["fecha"]})
                else:
                    clave = re.sub(r" - (Servicio de Notificaciones BCP|BANCA MOVIL BCP)$", "", asunto)
                    ignorados[clave] = ignorados.get(clave, 0) + 1
    return trx, abrir, ignorados


def main():
    p = argparse.ArgumentParser(description="Extrae transacciones BCP de resultados de Gmail guardados.")
    p.add_argument("archivos", nargs="+")
    p.add_argument("--salida", required=True, help="Archivo JSON de salida (p. ej. data/tmp/2026-05.json)")
    a = p.parse_args()

    trx, abrir, ignorados = procesar(a.archivos)
    salida = Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps({"trx": trx, "abrir": abrir, "ignorados": ignorados}, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    fechas = sorted(t["fecha"] for t in trx)
    print(f"{len(trx)} transacciones desde snippets ({fechas[0][:10]} a {fechas[-1][:10]})" if trx
          else "0 transacciones desde snippets")
    print(f"{len(abrir)} correos por abrir con get_message:")
    for x in abrir:
        print(f"  {x['id']}  {x['tipo']:<14} {x['fecha'][:10]}")
    print("Ignorados por asunto:", json.dumps(ignorados, ensure_ascii=False))
    print(f"Detalle en {salida}")


if __name__ == "__main__":
    main()
