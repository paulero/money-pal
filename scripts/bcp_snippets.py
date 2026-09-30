"""Money Pal · Extrae transacciones BCP de resultados de búsqueda de Gmail guardados en archivo.

Uso: .venv/bin/python scripts/bcp_snippets.py <archivo.json> [...]
Imprime JSON: {"trx": [...], "need_body": [[id, threadId, tipo, fecha]], "skipped": {asunto: n}}
"""
import json, re, sys, datetime as dt
L = dt.timezone(dt.timedelta(hours=-5))
def load(p):
    t = open(p).read()
    d = json.loads(t)
    if isinstance(d, list):  # tool-result wrapper
        d = json.loads(d[0]["text"])
    return d
out, skipped, need_body, unknown = [], {}, [], []
for p in sys.argv[1:]:
    d = load(p)
    for th in d.get("threads", []):
        for m in th["messages"]:
            subj, snip = m.get("subject",""), m.get("snippet","")
            f = dt.datetime.fromisoformat(m["date"].replace("Z","+00:00")).astimezone(L)
            base = dict(id=m["id"], fecha=f.isoformat(timespec="minutes"))
            if "Realizaste un consumo" in subj:
                r = re.search(r"consumo de (S/|\$) ([\d,]+\.\d{2}) con tu Tarjeta de (Crédito|Débito) BCP en (.+?)\. Por tu seguridad", snip)
                if not r:
                    need_body.append((m["id"], th["id"], "consumo", snip[:80])); continue
                cur = "PEN" if r[1]=="S/" else "USD"
                out.append({**base, "tipo":"consumo", "medio":"credito" if r[3]=="Crédito" else "debito", "tarjeta":None,
                            "moneda":cur, "monto":float(r[2].replace(",","")), "comercio":r[4].strip().upper().rstrip("."), "categoria":None})
            elif "Realizaste un retiro" in subj:
                r = re.search(r"retiro de (S/|\$) ([\d,]+\.\d{2})", snip)
                out.append({**base, "tipo":"retiro", "medio":"debito", "tarjeta":None, "moneda":"PEN" if r[1]=="S/" else "USD",
                            "monto":float(r[2].replace(",","")), "comercio":"RETIRO CAJERO", "categoria":None})
            elif "PAGO DE SERVICIO" in subj.upper():
                need_body.append((m["id"], th["id"], "pago_servicio", f.date().isoformat()))
            elif "Transferencia a Terceros" in subj or "Transferencia Interbancaria" in subj or "Otros Bancos" in subj:
                need_body.append((m["id"], th["id"], "transferencia", f.date().isoformat()))
            else:
                k = re.sub(r" - Servicio de Notificaciones BCP| - BANCA MOVIL BCP","",subj)
                skipped[k] = skipped.get(k,0)+1
print(json.dumps({"trx": out, "need_body": need_body, "skipped": skipped}, ensure_ascii=False))
