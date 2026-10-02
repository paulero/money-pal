"""Money Pal · Pruebas de scripts/revisiones.py y del servidor de scripts/revisar.py con los datos ficticios de examples/.

Trabaja en una carpeta temporal: nunca toca data/.

Uso:
  .venv/bin/python scripts/probar_revisiones.py
"""

import http.client
import json
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from revisiones import (  # noqa: E402
    Conflicto, ErrorRevision, Revisiones, aprobar, cambiar_categoria, contar_como_gasto, editar_nota,
)

from comparar import avance_revision, texto_revision  # noqa: E402
from revisar import crear_servidor  # noqa: E402

EJEMPLOS = Path(__file__).resolve().parent.parent / "examples"


class PruebasRevisiones(unittest.TestCase):
    def setUp(self):
        self.carpeta = Path(tempfile.mkdtemp())
        shutil.copy(EJEMPLOS / "transacciones.ejemplo.json", self.carpeta / "transacciones.json")
        shutil.copy(EJEMPLOS / "categorias.ejemplo.json", self.carpeta / "categorias.json")
        self.r = Revisiones(self.carpeta)

    def tearDown(self):
        shutil.rmtree(self.carpeta)

    def leer(self, nombre):
        return json.loads((self.carpeta / nombre).read_text(encoding="utf-8"))

    def mov(self, id_):
        return next(t for t in self.leer("transacciones.json")["transacciones"] if t["id"] == id_)

    def primero(self, v, **filtro):
        return next(t for t in v["transacciones"] if all(t.get(k) == x for k, x in filtro.items()))

    def test_vista_estados_y_origen(self):
        v = self.r.cargar()
        self.assertEqual(sum(v["conteos"].values()), len(v["transacciones"]))
        self.assertGreater(v["conteos"]["excluida"], 0)
        self.assertEqual(self.primero(v, comercio="BIM-JUAN PEREZ")["origen"], "comercio")
        self.assertEqual(self.primero(v, comercio="WONG SAN ISIDRO")["origen"], "regla")
        fechas = [t["fecha"] for t in v["transacciones"]]
        self.assertEqual(fechas, sorted(fechas, reverse=True))

    def test_aprobar(self):
        v = self.r.cargar()
        t = self.primero(v, estado="por_revisar")
        self.assertEqual(self.r.aplicar(v["version"], aprobar, [t["id"]]), 1)
        self.assertTrue(self.mov(t["id"])["revisado"])
        self.assertEqual(self.r.cargar()["conteos"]["revisado"], 1)

    def test_cambiar_categoria_aplica_al_comercio(self):
        v = self.r.cargar()
        wong = [t for t in v["transacciones"] if t["comercio"] == "WONG SAN ISIDRO"]
        self.assertGreater(len(wong), 1)
        n = self.r.aplicar(v["version"], cambiar_categoria, wong[0]["id"], "otros")
        self.assertEqual(n, len(wong))
        self.assertEqual(self.leer("categorias.json")["comercios"]["WONG SAN ISIDRO"], "otros")
        for t in wong:
            self.assertEqual(self.mov(t["id"])["categoria"], "otros")
        self.assertTrue(self.mov(wong[0]["id"])["revisado"])
        self.assertNotIn("revisado", self.mov(wong[1]["id"]))
        self.assertEqual(self.primero(self.r.cargar(), id=wong[1]["id"])["origen"], "comercio")

    def test_solo_este_y_manual_se_respeta(self):
        v = self.r.cargar()
        wong = [t["id"] for t in v["transacciones"] if t["comercio"] == "WONG SAN ISIDRO"]
        self.r.aplicar(v["version"], cambiar_categoria, wong[0], "transporte", solo_este=True)
        self.assertTrue(self.mov(wong[0])["categoria_manual"])
        self.assertNotIn("WONG SAN ISIDRO", self.leer("categorias.json")["comercios"])
        self.assertEqual(self.mov(wong[1])["categoria"], "comida-y-salidas")
        # Cambiar el comercio después no pisa el movimiento manual
        self.r.aplicar(self.r.cargar()["version"], cambiar_categoria, wong[1], "otros")
        self.assertEqual(self.mov(wong[0])["categoria"], "transporte")
        self.assertEqual(self.primero(self.r.cargar(), id=wong[0])["origen"], "manual")

    def test_pendientes(self):
        v = self.r.cargar()
        t = self.primero(v, estado="por_revisar")
        datos = self.leer("transacciones.json")
        next(x for x in datos["transacciones"] if x["id"] == t["id"])["pendiente"] = True
        (self.carpeta / "transacciones.json").write_text(json.dumps(datos), encoding="utf-8")
        v = self.r.cargar()
        self.assertEqual(self.primero(v, id=t["id"])["estado"], "pendiente")
        with self.assertRaises(ErrorRevision):
            self.r.aplicar(v["version"], aprobar, [t["id"]])
        self.r.aplicar(v["version"], contar_como_gasto, t["id"], False)
        self.assertEqual(self.primero(self.r.cargar(), id=t["id"])["estado"], "excluida")
        self.r.aplicar(self.r.cargar()["version"], contar_como_gasto, t["id"], True)
        self.assertEqual(self.primero(self.r.cargar(), id=t["id"])["estado"], "por_revisar")

    def test_validaciones(self):
        v = self.r.cargar()
        t = self.primero(v, estado="por_revisar")
        excluida = self.primero(v, estado="excluida")
        with self.assertRaises(ErrorRevision):
            self.r.aplicar(v["version"], cambiar_categoria, t["id"], "no-existe")
        with self.assertRaises(ErrorRevision):
            self.r.aplicar(v["version"], aprobar, ["no-existe"])
        with self.assertRaises(ErrorRevision):
            self.r.aplicar(v["version"], cambiar_categoria, excluida["id"], "otros")
        with self.assertRaises(ErrorRevision):
            self.r.aplicar(v["version"], editar_nota, t["id"], "x" * 201)
        self.assertEqual(self.r.cargar()["version"], v["version"])  # nada se guardó

    def test_nota(self):
        v = self.r.cargar()
        t = self.primero(v, estado="por_revisar")
        self.r.aplicar(v["version"], editar_nota, t["id"], "  cena   de  cumpleaños ")
        self.assertEqual(self.mov(t["id"])["nota"], "cena de cumpleaños")
        self.r.aplicar(self.r.cargar()["version"], editar_nota, t["id"], "")
        self.assertNotIn("nota", self.mov(t["id"]))

    def test_conflicto_si_los_archivos_cambian(self):
        v = self.r.cargar()
        t = self.primero(v, estado="por_revisar")
        datos = self.leer("transacciones.json")
        datos["actualizado"] = "otra lectura"
        (self.carpeta / "transacciones.json").write_text(json.dumps(datos), encoding="utf-8")
        with self.assertRaises(Conflicto):
            self.r.aplicar(v["version"], aprobar, [t["id"]])

    def test_deshacer(self):
        original_trx = self.leer("transacciones.json")
        original_cat = self.leer("categorias.json")
        v = self.r.cargar()
        self.assertFalse(v["puede_deshacer"])
        wong = self.primero(v, comercio="WONG SAN ISIDRO")
        t = self.primero(v, estado="por_revisar", comercio="CABIFY")
        self.r.aplicar(v["version"], aprobar, [t["id"]])
        self.r.aplicar(self.r.cargar()["version"], cambiar_categoria, wong["id"], "otros")
        v = self.r.cargar()
        self.assertTrue(v["puede_deshacer"])
        self.r.deshacer(v["version"])
        self.assertNotIn("WONG SAN ISIDRO", self.leer("categorias.json")["comercios"])
        self.assertTrue(self.mov(t["id"])["revisado"])
        v = self.r.cargar()
        self.assertTrue(v["puede_deshacer"])
        self.r.deshacer(v["version"])
        self.assertEqual(self.leer("transacciones.json"), original_trx)
        self.assertEqual(self.leer("categorias.json"), original_cat)
        v = self.r.cargar()
        self.assertFalse(v["puede_deshacer"])
        with self.assertRaises(ErrorRevision):
            self.r.deshacer(v["version"])

    def test_avance_revision(self):
        v = self.r.cargar()
        sep = [t for t in v["transacciones"] if t["fecha"].startswith("2026-09") and t["estado"] == "por_revisar"]
        self.assertEqual(avance_revision(self.leer("transacciones.json")["transacciones"], "2026-09", 3.5)["pct"], 0)
        self.r.aplicar(v["version"], aprobar, [t["id"] for t in sep])
        r = avance_revision(self.leer("transacciones.json")["transacciones"], "2026-09", 3.5)
        self.assertAlmostEqual(r["pct"], 1)
        self.assertEqual(texto_revision(r), "Revisado: 100% del gasto del mes.")
        self.assertEqual(texto_revision(avance_revision([], "2026-09", 3.5)), "")

    def test_respaldo(self):
        v = self.r.cargar()
        self.r.aplicar(v["version"], aprobar, [self.primero(v, estado="por_revisar")["id"]])
        self.assertTrue(list((self.carpeta / "respaldos").glob("transacciones_*.json")))


class PruebasServidor(unittest.TestCase):
    """La página solo responde a sí misma: Host, token y Origin correctos, y cabeceras de seguridad."""

    def setUp(self):
        self.carpeta = Path(tempfile.mkdtemp())
        shutil.copy(EJEMPLOS / "transacciones.ejemplo.json", self.carpeta / "transacciones.json")
        shutil.copy(EJEMPLOS / "categorias.ejemplo.json", self.carpeta / "categorias.json")
        self.s = crear_servidor(Revisiones(self.carpeta))
        self.puerto = self.s.server_address[1]
        threading.Thread(target=self.s.serve_forever, daemon=True).start()

    def tearDown(self):
        self.s.shutdown()
        self.s.server_close()
        shutil.rmtree(self.carpeta)

    def pedir(self, metodo, ruta, cuerpo=None, token=True, host=None, origen=None, tipo="application/json"):
        c = http.client.HTTPConnection("127.0.0.1", self.puerto, timeout=10)
        h = {"Host": host or f"127.0.0.1:{self.puerto}"}
        if token:
            h["X-Token"] = self.s.token if token is True else token
        if origen:
            h["Origin"] = origen
        datos = None
        if cuerpo is not None:
            datos = json.dumps(cuerpo).encode()
            h["Content-Type"] = tipo
        c.request(metodo, ruta, body=datos, headers=h)
        r = c.getresponse()
        texto = r.read()
        c.close()
        return r.status, dict(r.getheaders()), texto

    def test_solo_escucha_en_127(self):
        self.assertEqual(self.s.server_address[0], "127.0.0.1")

    def test_pagina_y_cabeceras(self):
        estado, h, texto = self.pedir("GET", "/", token=False)
        self.assertEqual(estado, 200)
        self.assertIn(b"app.js", texto)
        self.assertIn("default-src 'none'", h["Content-Security-Policy"])
        self.assertIn("frame-ancestors 'none'", h["Content-Security-Policy"])
        self.assertEqual(h["Cache-Control"], "no-store")
        self.assertEqual(self.pedir("GET", "/../data/transacciones.json", token=False)[0], 404)

    def test_datos_piden_token(self):
        self.assertEqual(self.pedir("GET", "/api/datos", token=False)[0], 403)
        self.assertEqual(self.pedir("GET", "/api/datos", token="otro")[0], 403)
        estado, _, texto = self.pedir("GET", "/api/datos")
        self.assertEqual(estado, 200)
        self.assertIn("transacciones", json.loads(texto))

    def test_host_y_origen_ajenos(self):
        # DNS rebinding: un sitio que apunte su dominio a 127.0.0.1 llega con su propio Host
        self.assertEqual(self.pedir("GET", "/", token=False, host="malo.example:80")[0], 403)
        self.assertEqual(self.pedir("GET", "/api/datos", host=f"malo.example:{self.puerto}")[0], 403)
        estado = self.pedir("POST", "/api/accion", {"accion": "aprobar", "ids": []}, origen="https://malo.example")[0]
        self.assertEqual(estado, 403)

    def test_post_solo_json(self):
        v = json.loads(self.pedir("GET", "/api/datos")[2])
        estado = self.pedir("POST", "/api/accion", {"version": v["version"], "accion": "aprobar", "ids": []},
                            tipo="text/plain")[0]
        self.assertEqual(estado, 415)

    def test_accion_conflicto_y_errores(self):
        v = json.loads(self.pedir("GET", "/api/datos")[2])
        t = next(x for x in v["transacciones"] if x["estado"] == "por_revisar")
        origen = f"http://127.0.0.1:{self.puerto}"
        estado, _, texto = self.pedir("POST", "/api/accion",
                                      {"version": v["version"], "accion": "aprobar", "ids": [t["id"]]}, origen=origen)
        self.assertEqual(estado, 200)
        self.assertEqual(json.loads(texto)["cambiados"], 1)
        # La versión vieja ya no sirve
        self.assertEqual(self.pedir("POST", "/api/accion",
                                    {"version": v["version"], "accion": "aprobar", "ids": [t["id"]]})[0], 409)
        nueva = json.loads(texto)["version"]
        self.assertEqual(self.pedir("POST", "/api/accion", {"version": nueva, "accion": "borrar"})[0], 400)
        self.assertEqual(self.pedir("POST", "/api/accion", {"version": nueva, "accion": "categoria"})[0], 400)
        self.assertEqual(self.pedir("POST", "/api/reporte", {"mes": "../../etc"})[0], 400)
        estado, _, texto = self.pedir("POST", "/api/deshacer", {"version": nueva})
        self.assertEqual(estado, 200)
        self.assertNotIn("revisado", next(x for x in json.loads(texto)["transacciones"] if x["id"] == t["id"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
