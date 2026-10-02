"""Money Pal · Revisar, aprobar y cambiar las categorías de tus movimientos.

Es la lógica detrás de la página de revisión (scripts/revisar.py): cada acción valida lo que recibe y
guarda con escribir_seguro (respaldo en data/respaldos/ y reemplazo atómico). No usa Gmail ni internet.

Estado de cada movimiento (calculado, no se guarda):
  pendiente      transferencia o retiro leído en modo automático: falta decir si cuenta como gasto
  sin_categoria  cuenta como gasto pero no tiene categoría
  por_revisar    tiene categoría pero aún no la aprobaste
  revisado       aprobado ("revisado": true)
  excluida       no cuenta como gasto

De dónde viene la categoría (también calculado): "comercio" (data/categorias.json → comercios),
"regla" (palabra en las reglas de una categoría), "manual" (cambiada solo para ese movimiento,
"categoria_manual": true) o "asignada" (puesta antes a mano o por Claude, sin regla que la respalde).

Cambiar la categoría de un movimiento también la cambia para su comercio: se guarda en comercios y
se aplica a los demás movimientos de ese comercio (menos los manuales y los excluidos). Con
solo_este=True cambia únicamente ese movimiento.

Uso:
  .venv/bin/python scripts/revisiones.py      # cuántos movimientos hay en cada estado
"""

import copy
import hashlib
import json
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from guardar import RAIZ, categorizar, escribir_seguro  # noqa: E402
from privado import proteger_carpetas  # noqa: E402

ESTADOS = ["pendiente", "sin_categoria", "por_revisar", "revisado", "excluida"]
NOTA_MAX = 200
DESHACER_MAX = 50


class ErrorRevision(ValueError):
    """La acción no es válida (movimiento o categoría que no existe, nota muy larga, etc.)."""


class Conflicto(ErrorRevision):
    """Los archivos cambiaron desde que se cargaron (p. ej. corrió la lectura semanal): hay que recargar."""


def estado(t):
    if t.get("excluida"):
        return "excluida"
    if t.get("pendiente"):
        return "pendiente"
    if not t.get("categoria"):
        return "sin_categoria"
    return "revisado" if t.get("revisado") else "por_revisar"


def origen(t, cats):
    if not t.get("categoria"):
        return None
    if t.get("categoria_manual"):
        return "manual"
    if t["comercio"] in cats.get("comercios", {}) and cats["comercios"][t["comercio"]] == t["categoria"]:
        return "comercio"
    return "regla" if categorizar(t, cats) == t["categoria"] else "asignada"


def _buscar(datos, id_):
    for t in datos["transacciones"]:
        if t["id"] == id_:
            return t
    raise ErrorRevision(f"No existe el movimiento {id_}")


def _validar_categoria(cats, categoria):
    ids = [c["id"] for c in cats.get("categorias", [])]
    if categoria not in ids:
        raise ErrorRevision(f"Categoría desconocida: {categoria}. Opciones: {', '.join(ids)}")


# --- Acciones sobre los datos en memoria. Devuelven cuántos movimientos cambiaron. ---

def aprobar(datos, ids):
    """Marca como revisados. Los pendientes y los sin categoría se resuelven primero."""
    movs = [_buscar(datos, i) for i in ids]
    for t in movs:
        if estado(t) in ("pendiente", "sin_categoria"):
            raise ErrorRevision(f"{t['comercio']} ({t['fecha'][:10]}): elige primero "
                                + ("si cuenta como gasto" if t.get("pendiente") else "una categoría"))
    cambiados = 0
    for t in movs:
        if not t.get("excluida") and not t.get("revisado"):
            t["revisado"] = True
            cambiados += 1
    return cambiados


def cambiar_categoria(datos, cats, id_, categoria, solo_este=False):
    """Cambia la categoría del movimiento (queda aprobado) y, salvo solo_este, la de su comercio."""
    _validar_categoria(cats, categoria)
    t = _buscar(datos, id_)
    if t.get("excluida"):
        raise ErrorRevision(f"{t['comercio']} ({t['fecha'][:10]}) no cuenta como gasto: inclúyelo primero")
    t["categoria"] = categoria
    t["revisado"] = True
    if solo_este:
        t["categoria_manual"] = True
        return 1
    t.pop("categoria_manual", None)
    cats.setdefault("comercios", {})[t["comercio"]] = categoria
    cambiados = 1
    for otro in datos["transacciones"]:
        if otro is t or otro["comercio"] != t["comercio"] or otro.get("excluida") or otro.get("categoria_manual"):
            continue
        if otro.get("categoria") != categoria:
            otro["categoria"] = categoria
            cambiados += 1
    return cambiados


def contar_como_gasto(datos, id_, es_gasto):
    """Resuelve un pendiente (o cambia de idea): incluye o excluye el movimiento del gasto."""
    t = _buscar(datos, id_)
    if not t.get("pendiente") and bool(t.get("excluida")) != es_gasto:
        return 0  # ya estaba así
    t.pop("pendiente", None)
    t.pop("revisado", None)  # si cuenta, vuelve a revisión con su categoría (o queda sin categoría)
    if es_gasto:
        t.pop("excluida", None)
    else:
        t["excluida"] = True
    return 1


def editar_nota(datos, id_, nota):
    t = _buscar(datos, id_)
    nota = " ".join((nota or "").split())
    if len(nota) > NOTA_MAX:
        raise ErrorRevision(f"La nota puede tener hasta {NOTA_MAX} caracteres")
    if nota:
        t["nota"] = nota
    else:
        t.pop("nota", None)
    return 1


def vista(datos, cats):
    """Lo que muestra la página: categorías, movimientos con estado y origen, y conteos."""
    movs = []
    for t in sorted(datos["transacciones"], key=lambda t: t["fecha"], reverse=True):
        movs.append({**t, "estado": estado(t), "origen": origen(t, cats)})
    conteos = {e: 0 for e in ESTADOS}
    for m in movs:
        conteos[m["estado"]] += 1
    return {
        "categorias": [{"id": c["id"], "nombre": c["nombre"]} for c in cats.get("categorias", [])],
        "bancos": sorted({t.get("banco", "") for t in datos["transacciones"]}),
        "transacciones": movs,
        "conteos": conteos,
    }


# --- Archivos: carga, versión, guardado y deshacer ---

class Revisiones:
    """Carga data/transacciones.json y data/categorias.json y aplica acciones de forma segura.

    Cada acción recibe la versión que vio la página: si los archivos cambiaron desde entonces, lanza
    Conflicto y no guarda nada. Las acciones se aplican de a una (con candado).
    """

    def __init__(self, carpeta=RAIZ / "data"):
        self.ruta_trx = Path(carpeta) / "transacciones.json"
        self.ruta_cat = Path(carpeta) / "categorias.json"
        self._candado = threading.Lock()
        self._deshacer = []  # (datos, cats, version después del cambio)

    def _leer(self):
        if not self.ruta_trx.exists() or not self.ruta_cat.exists():
            raise ErrorRevision("Faltan data/transacciones.json o data/categorias.json: corre /leer-correos y /categorias")
        b_trx, b_cat = self.ruta_trx.read_bytes(), self.ruta_cat.read_bytes()
        version = hashlib.sha256(b_trx + b"\0" + b_cat).hexdigest()[:16]
        return json.loads(b_trx), json.loads(b_cat), version

    def cargar(self):
        datos, cats, version = self._leer()
        return {**vista(datos, cats), "version": version, "puede_deshacer": self._puede_deshacer(version)}

    def _puede_deshacer(self, version):
        return bool(self._deshacer) and self._deshacer[-1][2] == version

    def aplicar(self, version, accion, *args, **kwargs):
        """Aplica accion(datos, cats, ...) o accion(datos, ...) si la versión coincide, y guarda."""
        with self._candado:
            datos, cats, actual = self._leer()
            if version != actual:
                raise Conflicto("Tus datos cambiaron mientras revisabas: recarga la página")
            antes = (copy.deepcopy(datos), copy.deepcopy(cats))
            usa_cats = accion is cambiar_categoria
            cambiados = accion(datos, cats, *args, **kwargs) if usa_cats else accion(datos, *args, **kwargs)
            proteger_carpetas()
            escribir_seguro(self.ruta_trx, datos)
            if usa_cats:
                escribir_seguro(self.ruta_cat, cats)
            nueva = self._leer()[2]
            self._deshacer = (self._deshacer + [(*antes, nueva)])[-DESHACER_MAX:]
            return cambiados

    def deshacer(self, version):
        """Vuelve al estado anterior al último cambio, si nadie más tocó los archivos desde entonces."""
        with self._candado:
            actual = self._leer()[2]
            if version != actual:
                raise Conflicto("Tus datos cambiaron mientras revisabas: recarga la página")
            if not self._puede_deshacer(actual):
                raise ErrorRevision("No hay nada que deshacer")
            datos, cats, _ = self._deshacer.pop()
            proteger_carpetas()
            escribir_seguro(self.ruta_trx, datos)
            escribir_seguro(self.ruta_cat, cats)
            # Lo que quede en la pila apunta a la versión restaurada, que es la de antes del cambio deshecho
            if self._deshacer:
                d, c, _ = self._deshacer[-1]
                self._deshacer[-1] = (d, c, self._leer()[2])
            return 1


def main():
    v = Revisiones().cargar()
    nombres = {"pendiente": "Pendientes (¿cuentan como gasto?)", "sin_categoria": "Sin categoría",
               "por_revisar": "Por revisar", "revisado": "Revisados", "excluida": "No cuentan como gasto"}
    for e in ESTADOS:
        print(f"{nombres[e]}: {v['conteos'][e]}")


if __name__ == "__main__":
    main()
