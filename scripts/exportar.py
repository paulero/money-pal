"""Money Pal · Exporta tus transacciones categorizadas a Excel y PDF.

Lee data/transacciones.json y data/categorias.json y genera en output/:
  money-pal_<desde>_<hasta>.xlsx  y  money-pal_<desde>_<hasta>.pdf

Uso:
  .venv/bin/python scripts/exportar.py                      # todo el periodo
  .venv/bin/python scripts/exportar.py --desde 2026-09      # desde un mes
  .venv/bin/python scripts/exportar.py --formato pdf --tc 3.45
  .venv/bin/python scripts/exportar.py --ejemplo            # prueba con datos ficticios
  .venv/bin/python scripts/exportar.py --cierre             # cierre del último mes completo, con comparativo

Todo se genera en tu computadora; output/ está en .gitignore.
"""

import argparse
import calendar
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from privado import proteger_carpetas

RAIZ = Path(__file__).resolve().parent.parent
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
TIPOS = {"consumo": "Consumo", "pago_servicio": "Pago de servicio", "transferencia": "Transferencia"}
MEDIOS = {"credito": "Crédito", "debito": "Débito", "cuenta": "Cuenta"}
COLORES = ["2563EB", "059669", "D97706", "7C3AED", "DB2777", "0891B2", "65A30D", "94A3B8"]
SIN_CATEGORIA = "Sin categoría"


# ---------- datos ----------

def parse_fecha(texto, fin=False):
    """Acepta AAAA-MM o AAAA-MM-DD. Con fin=True, AAAA-MM devuelve el último día del mes."""
    if len(texto) == 7:
        a, m = map(int, texto.split("-"))
        return date(a, m, calendar.monthrange(a, m)[1] if fin else 1)
    return date.fromisoformat(texto)


def cargar(ruta_trx, ruta_cat, desde, hasta):
    trx = json.loads(ruta_trx.read_text(encoding="utf-8"))["transacciones"]
    cats = json.loads(ruta_cat.read_text(encoding="utf-8")) if ruta_cat.exists() else {"categorias": []}

    filas = []
    for t in trx:
        if t.get("excluida"):
            continue
        f = datetime.fromisoformat(t["fecha"])
        if (desde and f.date() < desde) or (hasta and f.date() > hasta):
            continue
        filas.append({**t, "dt": f})
    filas.sort(key=lambda t: t["dt"])
    return filas, cats


def nombres_categorias(cats):
    return {c["id"]: c["nombre"] for c in cats.get("categorias", [])}


def mes_clave(f):
    return f"{f.year}-{f.month:02d}"


def mes_nombre(clave):
    a, m = clave.split("-")
    return f"{MESES[int(m) - 1].capitalize()} {a}"


def resumir(filas, cats, tc):
    """Totales por categoría en el orden de categorias.json (más 'Sin categoría' al final)."""
    nombres = nombres_categorias(cats)
    orden = list(nombres) + [None]
    res = {cid: {"n": 0, "PEN": 0.0, "USD": 0.0} for cid in orden}
    for t in filas:
        cid = t.get("categoria") if t.get("categoria") in nombres else None
        res[cid]["n"] += 1
        res[cid][t["moneda"]] += t["monto"]
    for r in res.values():
        r["aprox"] = r["PEN"] + r["USD"] * tc
    total = sum(r["aprox"] for r in res.values()) or 1
    salida = []
    presupuestos = {c["id"]: c.get("presupuesto_mensual") for c in cats.get("categorias", [])}
    for cid in orden:
        r = res[cid]
        if cid is None and r["n"] == 0:
            continue
        salida.append({"id": cid, "nombre": nombres.get(cid, SIN_CATEGORIA), **r,
                       "pct": r["aprox"] / total, "presupuesto": presupuestos.get(cid)})
    # De mayor a menor gasto; "Sin categoría" siempre al final
    return sorted(salida, key=lambda c: (c["id"] is None, -c["aprox"]))


def recurrentes(filas, tc):
    """Comercios que aparecen en 2 o más meses distintos."""
    por_comercio = defaultdict(lambda: {"meses": set(), "PEN": 0.0, "USD": 0.0, "cat": None})
    for t in filas:
        c = por_comercio[t["comercio"]]
        c["meses"].add(mes_clave(t["dt"]))
        c[t["moneda"]] += t["monto"]
        c["cat"] = t.get("categoria")
    out = []
    for comercio, c in por_comercio.items():
        if len(c["meses"]) >= 2:
            n = len(c["meses"])
            out.append({"comercio": comercio, "cat": c["cat"], "meses": n, "PEN": c["PEN"], "USD": c["USD"],
                        "prom": (c["PEN"] + c["USD"] * tc) / n})
    return sorted(out, key=lambda r: -r["prom"])


def nombre_banco(banco_id):
    """Nombre corto del banco desde banks/<id>/banco.json (p. ej. "BCP")."""
    ruta = RAIZ / "banks" / (banco_id or "") / "banco.json"
    if banco_id and ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))["nombre"].split(" · ")[0]
    return banco_id or "—"


def por_banco(filas, tc):
    """[(nombre, transacciones, soles aprox.)] de mayor a menor."""
    tot = defaultdict(lambda: [0, 0.0])
    for t in filas:
        tot[t.get("banco")][0] += 1
        tot[t.get("banco")][1] += t["monto"] * (tc if t["moneda"] == "USD" else 1)
    return sorted(((nombre_banco(b), n, v) for b, (n, v) in tot.items()), key=lambda x: -x[2])


def por_moneda(filas, tc):
    """[(moneda, transacciones, total en su moneda, soles aprox.)] de mayor a menor."""
    tot = defaultdict(lambda: [0, 0.0])
    for t in filas:
        tot[t["moneda"]][0] += 1
        tot[t["moneda"]][1] += t["monto"]
    return sorted(((m, n, v, v * (tc if m == "USD" else 1)) for m, (n, v) in tot.items()), key=lambda x: -x[3])


def top_comercios(filas, tc, n=10):
    tot = defaultdict(lambda: [0, 0.0])
    for t in filas:
        tot[t["comercio"]][0] += 1
        tot[t["comercio"]][1] += t["monto"] * (tc if t["moneda"] == "USD" else 1)
    return sorted(tot.items(), key=lambda kv: -kv[1][1])[:n]


# ---------- Excel ----------

def exportar_excel(filas, cats, tc, meses_periodo, ruta, cierre=None):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    nombres = nombres_categorias(cats)
    cabecera = PatternFill("solid", fgColor="1E293B")
    blanco = Font(bold=True, color="FFFFFF")
    negrita = Font(bold=True)
    soles, dolares, pct = '"S/" #,##0.00', '"$" #,##0.00', "0%"

    def tabla(ws, fila, columnas):
        for i, titulo in enumerate(columnas, 1):
            celda = ws.cell(fila, i, titulo)
            celda.fill, celda.font = cabecera, blanco
            celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    def fila_datos(ws, valores):
        """Agrega una fila de datos. Un texto que empieza con "=" (p. ej. un comercio sacado de un correo)
        queda como texto: nunca se convierte en fórmula de Excel."""
        ws.append(valores)
        for celda in ws[ws.max_row]:
            if isinstance(celda.value, str) and celda.value.startswith("="):
                celda.data_type, celda.quotePrefix = "s", True

    def anchos(ws, valores):
        for i, w in enumerate(valores, 1):
            ws.column_dimensions[get_column_letter(i)].width = w

    wb = Workbook()

    # Resumen
    ws = wb.active
    ws.title = "Resumen"
    desde, hasta = filas[0]["dt"].date(), filas[-1]["dt"].date()
    ws["A1"] = "Money Pal · Resumen de gastos"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Periodo: {desde:%d/%m/%Y} al {hasta:%d/%m/%Y} · {len(filas)} transacciones · USD a S/ {tc:.2f} (aprox.)"
    cols = ["Categoría", "Transacciones", "Total PEN", "Total USD", "Total aprox. PEN", "% del gasto",
            "Presupuesto mensual", f"Presupuesto del periodo ({meses_periodo:g} {'mes' if meses_periodo == 1 else 'meses'})", "Diferencia"]
    tabla(ws, 4, cols)
    r = 5
    for c in resumir(filas, cats, tc):
        fila_datos(ws, [c["nombre"], c["n"], round(c["PEN"], 2), round(c["USD"], 2), round(c["aprox"], 2), c["pct"]])
        if c["presupuesto"]:
            ws.cell(r, 7, c["presupuesto"])
            ws.cell(r, 8, f"=G{r}*{meses_periodo}")
            ws.cell(r, 9, f"=H{r}-E{r}")
        r += 1
    ws.append(["Total", f"=SUM(B5:B{r - 1})", f"=SUM(C5:C{r - 1})", f"=SUM(D5:D{r - 1})",
               f"=SUM(E5:E{r - 1})", f"=SUM(F5:F{r - 1})"])
    for celda in ws[r]:
        celda.font = negrita
    for fila in ws.iter_rows(min_row=5, max_row=r):
        fila[2].number_format = fila[4].number_format = fila[6].number_format = soles
        fila[7].number_format = fila[8].number_format = soles
        fila[3].number_format, fila[5].number_format = dolares, pct
    anchos(ws, [28, 14, 14, 12, 16, 11, 16, 18, 14])
    ws.freeze_panes = "A5"
    bancos = por_banco(filas, tc)
    if len(bancos) > 1:
        fila_b = ws.max_row + 2
        tabla(ws, fila_b, ["Banco", "Transacciones", "Total aprox. PEN"])
        for i, (nombre, n, v) in enumerate(bancos, fila_b + 1):
            ws.cell(i, 1, nombre)
            ws.cell(i, 2, n)
            ws.cell(i, 3, round(v, 2)).number_format = soles
    monedas = por_moneda(filas, tc)
    if len(monedas) > 1:
        fila_m = ws.max_row + 2
        tabla(ws, fila_m, ["Moneda", "Transacciones", "Total", "Total aprox. PEN"])
        for i, (m, n, v, aprox) in enumerate(monedas, fila_m + 1):
            ws.cell(i, 1, m)
            ws.cell(i, 2, n)
            ws.cell(i, 3, round(v, 2)).number_format = dolares if m == "USD" else soles
            ws.cell(i, 4, round(aprox, 2)).number_format = soles

    # Por mes (categoría × mes, en soles aprox.)
    meses = sorted({mes_clave(t["dt"]) for t in filas})
    ws = wb.create_sheet("Por mes")
    ws["A1"] = "Gasto por categoría y mes (aprox. PEN)"
    ws["A1"].font = Font(bold=True, size=12)
    tabla(ws, 3, ["Categoría"] + [mes_nombre(m) for m in meses] + ["Promedio"])
    ids = list(nombres) + [None]
    matriz = defaultdict(float)
    for t in filas:
        cid = t.get("categoria") if t.get("categoria") in nombres else None
        matriz[(cid, mes_clave(t["dt"]))] += t["monto"] * (tc if t["moneda"] == "USD" else 1)
    fila = 4
    for cid in ids:
        if cid is None and not any(matriz[(None, m)] for m in meses):
            continue
        ws.cell(fila, 1, nombres.get(cid, SIN_CATEGORIA))
        for j, m in enumerate(meses, 2):
            ws.cell(fila, j, round(matriz[(cid, m)], 2)).number_format = soles
        ultima = get_column_letter(len(meses) + 1)
        ws.cell(fila, len(meses) + 2, f"=AVERAGE(B{fila}:{ultima}{fila})").number_format = soles
        fila += 1
    ws.cell(fila, 1, "Total").font = negrita
    for j in range(2, len(meses) + 3):
        letra = get_column_letter(j)
        celda = ws.cell(fila, j, f"=SUM({letra}4:{letra}{fila - 1})")
        celda.number_format, celda.font = soles, negrita
    anchos(ws, [28] + [16] * (len(meses) + 1))

    # Una hoja por mes con el detalle
    for m in reversed(meses):
        ws = wb.create_sheet(mes_nombre(m))
        tabla(ws, 1, ["Fecha", "Hora", "Comercio", "Categoría", "Tipo", "Banco", "Medio", "Moneda", "Monto"])
        for t in (t for t in filas if mes_clave(t["dt"]) == m):
            fila_datos(ws, [t["dt"].date(), t["dt"].strftime("%H:%M"), t["comercio"],
                       nombres.get(t.get("categoria"), SIN_CATEGORIA), TIPOS.get(t["tipo"], t["tipo"]),
                       nombre_banco(t.get("banco")), MEDIOS.get(t["medio"], t["medio"]), t["moneda"], t["monto"]])
            ws.cell(ws.max_row, 1).number_format = "DD/MM/YYYY"
            ws.cell(ws.max_row, 9).number_format = soles if t["moneda"] == "PEN" else dolares
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        anchos(ws, [12, 8, 34, 24, 17, 12, 10, 9, 12])

    # Recurrentes
    ws = wb.create_sheet("Recurrentes")
    tabla(ws, 1, ["Comercio", "Categoría", "Meses activos", "Total PEN", "Total USD", "Promedio mensual aprox. PEN"])
    rec = recurrentes(filas, tc)
    for x in rec:
        fila_datos(ws, [x["comercio"], nombres.get(x["cat"], SIN_CATEGORIA), x["meses"], round(x["PEN"], 2), round(x["USD"], 2), round(x["prom"], 2)])
        ws.cell(ws.max_row, 4).number_format = ws.cell(ws.max_row, 6).number_format = soles
        ws.cell(ws.max_row, 5).number_format = dolares
    if not rec:
        ws["A2"] = "Se necesitan al menos 2 meses de datos para detectar gastos recurrentes."
    anchos(ws, [34, 24, 14, 14, 12, 26])

    if cierre:
        from comparar import VENTANAS, nota_historia, texto_revision, variacion
        mes, comp, disponibles, revision = cierre
        ws = wb.create_sheet("Cierre de mes", 0)
        wb.active = 0
        ws["A1"] = f"Cierre de {mes_nombre(mes).lower()} · comparado con meses anteriores (aprox. PEN)"
        ws["A1"].font = Font(bold=True, size=14)
        ws["A2"] = nota_historia(disponibles) or "Todos los promedios usan meses completos."
        ws["A3"] = texto_revision(revision)
        tabla(ws, 4, ["Categoría", mes_nombre(mes)] + [f"Promedio {n} meses" for n in VENTANAS]
              + [f"vs {n}m" for n in VENTANAS] + ["Alerta"])
        alerta = PatternFill("solid", fgColor="FEE2E2")
        for i, f in enumerate(comp, 5):
            proms = [f["promedios"][n] for n in VENTANAS]
            vars_ = [variacion(f["mes"], b) for b in proms]
            fila_datos(ws, [f["nombre"], round(f["mes"], 2)] + [round(b, 2) if b is not None else None for b in proms]
                      + [v if v not in (None, float("inf")) else None for v in vars_]
                      + ["Sobre su promedio de 3 meses" if f["alerta"] else None])
            for j in range(2, 7):
                ws.cell(i, j).number_format = soles
            for j in range(7, 11):
                ws.cell(i, j).number_format = "+0%;-0%;0%"
            if f["id"] == "__total__":
                for celda in ws[i]:
                    celda.font = negrita
            if f["alerta"]:
                for celda in ws[i]:
                    celda.fill = alerta
        anchos(ws, [28, 16, 14, 14, 14, 14, 9, 9, 9, 9, 28])
        ws.freeze_panes = "B5"

    wb.save(ruta)


# ---------- PDF ----------

def exportar_pdf(filas, cats, tc, meses_periodo, ruta, cierre=None):
    from reportlab.graphics.shapes import Drawing, Rect, String
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle("t", parent=estilos["Title"], alignment=0, fontSize=20, spaceAfter=2)
    sub = ParagraphStyle("s", parent=estilos["Normal"], textColor=colors.HexColor("#64748B"), fontSize=9)
    h2 = ParagraphStyle("h", parent=estilos["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=6)
    oscuro, gris = colors.HexColor("#1E293B"), colors.HexColor("#E2E8F0")

    def estilo_tabla(extra=()):
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), oscuro), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"), ("LINEBELOW", (0, 1), (-1, -1), 0.4, gris),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), *extra])

    s = lambda v: f"S/ {v:,.2f}"
    d = lambda v: f"$ {v:,.2f}" if v else "—"
    resumen = resumir(filas, cats, tc)
    total_pen = sum(t["monto"] for t in filas if t["moneda"] == "PEN")
    total_usd = sum(t["monto"] for t in filas if t["moneda"] == "USD")
    desde, hasta = filas[0]["dt"].date(), filas[-1]["dt"].date()

    doc = SimpleDocTemplate(str(ruta), pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm, title="Money Pal · Reporte de gastos")
    ancho = A4[0] - 32 * mm
    h = [Paragraph("Money Pal · Reporte de gastos", titulo),
         Paragraph(f"{desde:%d/%m/%Y} al {hasta:%d/%m/%Y} · {len(filas)} transacciones · "
                   f"USD convertido a S/ {tc:.2f} (aprox.)", sub), Spacer(1, 8)]

    if cierre:
        from comparar import VENTANAS, nota_historia, texto_revision, texto_variacion, variacion
        mes, comp, disponibles, revision = cierre
        h[0] = Paragraph(f"Money Pal · Cierre de {mes_nombre(mes).lower()}", titulo)
        h.append(Paragraph("Comparado con tus meses anteriores (aprox. PEN)", h2))
        filas_c = [["Categoría", "Este mes"] + [f"Prom. {n}m" for n in VENTANAS] + ["vs 3m"]]
        extra = []
        for i, f in enumerate(comp, 1):
            proms = [s(f["promedios"][n]) if f["promedios"][n] is not None else "—" for n in VENTANAS]
            filas_c.append([f["nombre"], s(f["mes"]), *proms, texto_variacion(variacion(f["mes"], f["promedios"][3]))])
            if f["alerta"]:
                extra.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FEE2E2")))
        extra += [("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"), ("LINEABOVE", (0, -1), (-1, -1), 0.8, oscuro)]
        t = Table(filas_c, colWidths=[ancho * w for w in (.26, .13, .13, .13, .13, .13, .09)])
        t.setStyle(estilo_tabla(extra))
        h.append(t)
        leyenda = "En rojo: categorías que superan su promedio de 3 meses en más de 20% y S/ 100."
        h += [Spacer(1, 4), Paragraph(" ".join(filter(None, [leyenda, nota_historia(disponibles)])), sub)]
        if texto_revision(revision):
            h += [Spacer(1, 2), Paragraph(texto_revision(revision), sub)]
        h.append(Spacer(1, 6))

    # Indicadores
    kpis = [("Gasto total aprox.", s(total_pen + total_usd * tc)), ("En soles", s(total_pen)),
            ("En dólares", d(total_usd)), ("Promedio mensual aprox.", s((total_pen + total_usd * tc) / meses_periodo))]
    t = Table([[Paragraph(f'<font size=8 color="#64748B">{k}</font><br/><font size=13><b>{v}</b></font>',
                          estilos["Normal"]) for k, v in kpis]], colWidths=[ancho / 4] * 4)
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, gris), ("INNERGRID", (0, 0), (-1, -1), 0.5, gris),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    h += [t, Paragraph("Gasto por categoría", h2)]

    # Barras
    alto_fila, etiqueta = 16, 120
    dib = Drawing(ancho, alto_fila * len(resumen))
    maximo = max(c["aprox"] for c in resumen) or 1
    for i, c in enumerate(resumen):
        y = alto_fila * (len(resumen) - i - 1) + 3
        color = colors.HexColor("#" + (COLORES[i % 7] if c["id"] else COLORES[7]))
        dib.add(String(0, y + 2, c["nombre"], fontName="Helvetica", fontSize=8.5))
        largo = (ancho - etiqueta - 90) * c["aprox"] / maximo
        dib.add(Rect(etiqueta, y, max(largo, 1), 10, fillColor=color, strokeColor=None))
        dib.add(String(etiqueta + largo + 4, y + 2, f"{s(c['aprox'])} · {c['pct']:.0%}",
                           fontName="Helvetica", fontSize=8, fillColor=colors.HexColor("#475569")))
    h.append(dib)
    h.append(Spacer(1, 8))

    filas_tabla = [["Categoría", "Trx", "PEN", "USD", "Aprox. PEN", "%", "Presupuesto"]]
    for c in resumen:
        ppto = s(c["presupuesto"] * meses_periodo) if c["presupuesto"] else "—"
        filas_tabla.append([c["nombre"], c["n"], s(c["PEN"]), d(c["USD"]), s(c["aprox"]), f"{c['pct']:.0%}", ppto])
    filas_tabla.append(["Total", len(filas), s(total_pen), d(total_usd), s(total_pen + total_usd * tc), "100%", ""])
    t = Table(filas_tabla, colWidths=[ancho * w for w in (.27, .07, .14, .11, .15, .08, .18)])
    t.setStyle(estilo_tabla([("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                             ("LINEABOVE", (0, -1), (-1, -1), 0.8, oscuro)]))
    h.append(t)

    # Por mes
    meses = sorted({mes_clave(t["dt"]) for t in filas})
    if len(meses) > 1:
        por_mes = defaultdict(float)
        for x in filas:
            por_mes[mes_clave(x["dt"])] += x["monto"] * (tc if x["moneda"] == "USD" else 1)
        h.append(Paragraph("Gasto por mes (aprox. PEN)", h2))
        t = Table([["Mes", "Total"]] + [[mes_nombre(m), s(por_mes[m])] for m in meses],
                  colWidths=[ancho * .5, ancho * .5])
        t.setStyle(estilo_tabla())
        h.append(t)

    bancos = por_banco(filas, tc)
    if len(bancos) > 1:
        h.append(Paragraph("Gasto por banco (aprox. PEN)", h2))
        t = Table([["Banco", "Trx", "Total"]] + [[b, n, s(v)] for b, n, v in bancos],
                  colWidths=[ancho * .6, ancho * .12, ancho * .28])
        t.setStyle(estilo_tabla())
        h.append(t)

    monedas = por_moneda(filas, tc)
    if len(monedas) > 1:
        h.append(Paragraph("Gasto por moneda", h2))
        t = Table([["Moneda", "Trx", "Total", "Aprox. PEN"]] +
                  [[m, n, d(v) if m == "USD" else s(v), s(aprox)] for m, n, v, aprox in monedas],
                  colWidths=[ancho * .4, ancho * .12, ancho * .24, ancho * .24])
        t.setStyle(estilo_tabla())
        h.append(t)

    # Top comercios
    h.append(Paragraph("Top 10 comercios (aprox. PEN)", h2))
    t = Table([["Comercio", "Trx", "Total"]] + [[c, n, s(v)] for c, (n, v) in top_comercios(filas, tc)],
              colWidths=[ancho * .6, ancho * .12, ancho * .28])
    t.setStyle(estilo_tabla())
    h.append(t)

    def pie(canvas, _doc):
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#94A3B8"))
        canvas.drawString(16 * mm, 8 * mm, "Generado localmente con Money Pal · github.com/paulero/money-pal · "
                                           "Herramienta de organización personal, no es asesoría financiera.")
        canvas.drawRightString(A4[0] - 16 * mm, 8 * mm, f"Página {_doc.page}")

    doc.build(h, onFirstPage=pie, onLaterPages=pie)


# ---------- main ----------

def main():
    p = argparse.ArgumentParser(description="Exporta tus gastos a Excel y PDF.")
    p.add_argument("--desde", help="AAAA-MM o AAAA-MM-DD")
    p.add_argument("--hasta", help="AAAA-MM o AAAA-MM-DD")
    p.add_argument("--formato", choices=["excel", "pdf", "ambos"], default="ambos")
    p.add_argument("--tc", type=float, help="Tipo de cambio USD→PEN (por defecto, el de categorias.json o 3.50)")
    p.add_argument("--datos", default=str(RAIZ / "data"))
    p.add_argument("--ejemplo", action="store_true", help="Usa los datos ficticios de examples/")
    p.add_argument("--salida", default=str(RAIZ / "output"))
    p.add_argument("--cierre", nargs="?", const="auto", metavar="AAAA-MM",
                   help="Reporte de cierre de mes con comparativo 3/6/12/18 meses (por defecto, el último mes completo)")
    a = p.parse_args()
    proteger_carpetas()

    desde = parse_fecha(a.desde) if a.desde else None
    hasta = parse_fecha(a.hasta, fin=True) if a.hasta else None
    if a.ejemplo:
        rutas = RAIZ / "examples" / "transacciones.ejemplo.json", RAIZ / "examples" / "categorias.ejemplo.json"
    else:
        rutas = Path(a.datos) / "transacciones.json", Path(a.datos) / "categorias.json"
    if not rutas[0].exists():
        raise SystemExit(f"No encontré {rutas[0]}. Corre /leer-correos primero (o usa --ejemplo).")
    mes_cierre = None
    if a.cierre:
        from comparar import ultimo_mes_completo
        datos = json.loads(rutas[0].read_text(encoding="utf-8"))
        mes_cierre = ultimo_mes_completo(datos["periodo"]) if a.cierre == "auto" else a.cierre
        if not mes_cierre:
            raise SystemExit("Aún no hay un mes completo de datos para el cierre.")
        desde, hasta = desde or parse_fecha(mes_cierre), hasta or parse_fecha(mes_cierre, fin=True)
    filas, cats = cargar(*rutas, desde, hasta)
    if not filas:
        raise SystemExit("No hay transacciones en ese periodo. Revisa --desde / --hasta o corre /leer-correos para traer más meses.")
    tc = a.tc or cats.get("tipo_cambio_usd") or 3.50
    # Meses del periodo según días, redondeado a medio mes (29/08–29/09 = 1 mes), para promedios y presupuestos
    inicio, fin = desde or filas[0]["dt"].date(), hasta or filas[-1]["dt"].date()
    meses_periodo = max(round(((fin - inicio).days + 1) / 30.44 * 2) / 2, 0.5)

    cierre = None
    if mes_cierre:
        from comparar import avance_revision, comparar
        cierre = (mes_cierre, *comparar(datos["transacciones"], cats, datos["periodo"], mes_cierre, tc),
                  avance_revision(datos["transacciones"], mes_cierre, tc))

    salida = Path(a.salida)
    salida.mkdir(exist_ok=True)
    nombre = f"cierre_{mes_cierre}" if mes_cierre else f"{filas[0]['dt']:%Y-%m-%d}_{filas[-1]['dt']:%Y-%m-%d}"
    base = salida / f"money-pal{'_ejemplo' if a.ejemplo else ''}_{nombre}"
    if a.formato in ("excel", "ambos"):
        exportar_excel(filas, cats, tc, meses_periodo, base.with_suffix(".xlsx"), cierre)
        print(f"Excel: {base.with_suffix('.xlsx')}")
    if a.formato in ("pdf", "ambos"):
        exportar_pdf(filas, cats, tc, meses_periodo, base.with_suffix(".pdf"), cierre)
        print(f"PDF:   {base.with_suffix('.pdf')}")


if __name__ == "__main__":
    main()
