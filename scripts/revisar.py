"""Money Pal · Página para revisar, aprobar y cambiar las categorías de tus movimientos.

Abre un servidor SOLO en tu computadora (127.0.0.1, puerto al azar) y la página en tu navegador.
Tus datos no salen de tu Mac: la página no carga nada de internet y ningún otro sitio puede usarla
(token secreto, verificación de Host y Origin, política de seguridad estricta).

Uso:
  scripts/revisar.sh                # o: .venv/bin/python scripts/revisar.py
  .venv/bin/python scripts/revisar.py --no-abrir    # solo muestra la dirección

Se cierra con Ctrl+C o sola tras 30 minutos sin uso.
"""

import argparse
import hmac
import json
import re
import secrets
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from guardar import RAIZ  # noqa: E402
from privado import proteger_carpetas  # noqa: E402
from revisiones import (  # noqa: E402
    Conflicto, ErrorRevision, Revisiones, aprobar, cambiar_categoria, contar_como_gasto, editar_nota,
)

PAGINA = Path(__file__).resolve().parent / "revisar"
ARCHIVOS = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
            "/estilos.css": ("estilos.css", "text/css")}
CUERPO_MAX = 256 * 1024
INACTIVIDAD = 30 * 60
SEGURIDAD = {
    "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
                               "img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Cross-Origin-Resource-Policy": "same-origin",
}
ACCIONES = {
    "aprobar": lambda b: (aprobar, [list(map(str, b["ids"]))]),
    "categoria": lambda b: (cambiar_categoria, [str(b["id"]), str(b["categoria"])], {"solo_este": bool(b.get("solo_este"))}),
    "gasto": lambda b: (contar_como_gasto, [str(b["id"]), bool(b["es_gasto"])]),
    "nota": lambda b: (editar_nota, [str(b["id"]), str(b.get("nota") or "")]),
}


class Manejador(BaseHTTPRequestHandler):
    server_version = "MoneyPal"
    sys_version = ""

    def log_message(self, *args):  # sin registro: las rutas no tienen datos, pero no hace falta guardarlas
        pass

    def _responder(self, codigo, cuerpo, tipo="application/json"):
        if isinstance(cuerpo, (dict, list)):
            cuerpo = json.dumps(cuerpo, ensure_ascii=False)
        datos = cuerpo.encode("utf-8") if isinstance(cuerpo, str) else cuerpo
        self.send_response(codigo)
        self.send_header("Content-Type", f"{tipo}; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        for k, v in SEGURIDAD.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(datos)

    def _host_valido(self):
        puerto = self.server.server_address[1]
        return self.headers.get("Host") in (f"127.0.0.1:{puerto}", f"localhost:{puerto}")

    def _autorizado(self):
        """Token en cada llamada a /api/ y, si el navegador manda Origin, que sea esta misma página."""
        token = self.headers.get("X-Token", "")
        origen = self.headers.get("Origin")
        puerto = self.server.server_address[1]
        if origen and origen not in (f"http://127.0.0.1:{puerto}", f"http://localhost:{puerto}"):
            return False
        return hmac.compare_digest(token, self.server.token)

    def _preparar(self):
        self.server.ultimo_uso = time.monotonic()
        if not self._host_valido():
            self._responder(403, {"error": "Host no permitido"})
            return False
        return True

    def do_GET(self):
        if not self._preparar():
            return
        ruta = self.path.split("?")[0]
        if ruta in ARCHIVOS:
            nombre, tipo = ARCHIVOS[ruta]
            return self._responder(200, (PAGINA / nombre).read_bytes(), tipo)
        if ruta == "/api/datos":
            if not self._autorizado():
                return self._responder(403, {"error": "No autorizado"})
            return self._api(lambda: self.server.revisiones.cargar())
        self._responder(404, {"error": "No existe"})

    def do_POST(self):
        if not self._preparar():
            return
        if not self._autorizado():
            return self._responder(403, {"error": "No autorizado"})
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self._responder(415, {"error": "Se espera JSON"})
        largo = int(self.headers.get("Content-Length") or 0)
        if largo > CUERPO_MAX:
            return self._responder(413, {"error": "Demasiado grande"})
        try:
            cuerpo = json.loads(self.rfile.read(largo) or b"{}")
            if not isinstance(cuerpo, dict):
                raise ValueError
        except ValueError:
            return self._responder(400, {"error": "JSON inválido"})

        ruta = self.path.split("?")[0]
        r = self.server.revisiones
        if ruta == "/api/accion":
            return self._api(lambda: self._accion(r, cuerpo))
        if ruta == "/api/deshacer":
            return self._api(lambda: (r.deshacer(str(cuerpo.get("version"))), r.cargar())[1])
        if ruta == "/api/reporte":
            return self._api(lambda: regenerar_reporte(str(cuerpo.get("mes", ""))))
        self._responder(404, {"error": "No existe"})

    def _accion(self, r, cuerpo):
        if cuerpo.get("accion") not in ACCIONES:
            raise ErrorRevision("Acción desconocida")
        try:
            accion, args, *kw = ACCIONES[cuerpo["accion"]](cuerpo)
        except (KeyError, TypeError):
            raise ErrorRevision("Faltan datos para la acción")
        cambiados = r.aplicar(str(cuerpo.get("version")), accion, *args, **(kw[0] if kw else {}))
        return {**r.cargar(), "cambiados": cambiados}

    def _api(self, funcion):
        try:
            self._responder(200, funcion())
        except Conflicto as e:
            self._responder(409, {"error": str(e)})
        except ErrorRevision as e:
            self._responder(400, {"error": str(e)})


def regenerar_reporte(mes):
    if not re.fullmatch(r"20\d\d-(0[1-9]|1[0-2])", mes):
        raise ErrorRevision("Mes inválido (AAAA-MM)")
    python = RAIZ / ".venv" / "bin" / "python"
    if not python.exists():
        raise ErrorRevision("Falta el entorno de Python: corre scripts/cierre-de-mes.sh o mira docs/instalacion.md")
    p = subprocess.run([str(python), "scripts/exportar.py", "--cierre", mes], cwd=RAIZ,
                       capture_output=True, text=True, timeout=180)
    if p.returncode != 0:
        raise ErrorRevision("No se pudo generar el reporte: " + (p.stderr.strip().splitlines() or ["error"])[-1])
    archivos = [Path(l.split(":", 1)[1].strip()).name for l in p.stdout.splitlines() if l.startswith(("Excel:", "PDF:"))]
    return {"mes": mes, "archivos": archivos}


def crear_servidor(revisiones):
    """Servidor en 127.0.0.1 con un puerto libre al azar y un token nuevo."""
    revisiones.cargar()  # falla aquí, con un mensaje claro, si aún no hay datos
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), Manejador)
    servidor.token = secrets.token_urlsafe(32)
    servidor.revisiones = revisiones
    servidor.ultimo_uso = time.monotonic()
    return servidor


def main():
    p = argparse.ArgumentParser(description="Página local para revisar tus categorías.")
    p.add_argument("--no-abrir", action="store_true", help="No abre el navegador, solo muestra la dirección")
    a = p.parse_args()
    proteger_carpetas()

    servidor = crear_servidor(Revisiones())

    def vigilar():
        while time.monotonic() - servidor.ultimo_uso < INACTIVIDAD:
            time.sleep(30)
        print("\n30 minutos sin uso: cerrando.")
        servidor.shutdown()
    threading.Thread(target=vigilar, daemon=True).start()

    # El token va después de "#": el navegador nunca lo envía en las peticiones ni queda en registros
    url = f"http://127.0.0.1:{servidor.server_address[1]}/#t={servidor.token}"
    print(f"Money Pal · revisión de categorías\n{url}\nCtrl+C para cerrar.", flush=True)
    if not a.no_abrir:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrado.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    try:
        main()
    except ErrorRevision as e:
        raise SystemExit(str(e))
