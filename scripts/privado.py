"""Money Pal · Solo tu usuario puede leer tus datos.

En macOS todas las cuentas normales comparten el grupo "staff" y pueden entrar a tu carpeta de inicio:
sin esto, otra cuenta de la misma computadora podría leer data/ y output/. Los scripts que crean o
escriben esos archivos llaman a proteger_carpetas() al empezar.
"""

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def proteger_carpetas():
    """Archivos nuevos solo para ti (umask 077) y data/ y output/ cerradas para otras cuentas (700/600)."""
    os.umask(0o077)
    for carpeta in (RAIZ / "data", RAIZ / "output"):
        if not carpeta.exists():
            continue
        for ruta in [carpeta, *carpeta.rglob("*")]:
            if not ruta.is_symlink():
                ruta.chmod(ruta.stat().st_mode & 0o700)
