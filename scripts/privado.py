"""Money Pal · Solo tu usuario puede leer tus datos.

En macOS todas las cuentas normales comparten el grupo "staff" y pueden entrar a tu carpeta de inicio:
sin esto, otra cuenta de la misma computadora podría leer data/ y output/. Los scripts que crean o
escriben esos archivos llaman a proteger_carpetas() al empezar, que además:
  - activa el filtro de .githooks/pre-commit (bloquea commits con datos personales), y
  - avisa si el proyecto está en una carpeta que se sube a la nube (iCloud, Dropbox, OneDrive, Google Drive).
"""

import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
# Lo más específico primero: Dropbox y compañía también viven dentro de Library/CloudStorage
NUBE = {"Dropbox": "Dropbox", "OneDrive": "OneDrive", "Google Drive": "Google Drive", "GoogleDrive": "Google Drive",
        "Library/Mobile Documents": "iCloud Drive", "Library/CloudStorage": "un servicio en la nube"}
_avisado = False


def proteger_carpetas():
    """Archivos nuevos solo para ti (umask 077) y data/ y output/ cerradas para otras cuentas (700/600)."""
    os.umask(0o077)
    for carpeta in (RAIZ / "data", RAIZ / "output"):
        if not carpeta.exists():
            continue
        for ruta in [carpeta, *carpeta.rglob("*")]:
            if not ruta.is_symlink():
                ruta.chmod(ruta.stat().st_mode & 0o700)
    activar_filtro_commits()
    avisar_si_esta_en_la_nube()


def activar_filtro_commits():
    """Configura este repositorio para usar .githooks/ (solo si es un clon de git y aún no lo está)."""
    if not (RAIZ / ".git").exists() or not (RAIZ / ".githooks" / "pre-commit").exists():
        return
    try:
        actual = subprocess.run(["git", "-C", str(RAIZ), "config", "--local", "core.hooksPath"],
                                capture_output=True, text=True, timeout=5).stdout.strip()
        if actual != ".githooks":
            subprocess.run(["git", "-C", str(RAIZ), "config", "--local", "core.hooksPath", ".githooks"],
                           capture_output=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        pass  # sin git no hay commits que filtrar


def en_la_nube(raiz=RAIZ, casa=Path.home()):
    """Nombre del servicio si la carpeta se sincroniza con la nube, o None."""
    texto = str(raiz)
    for marca, servicio in NUBE.items():
        if marca in texto:
            return servicio
    # macOS puede subir el Escritorio y Documentos a iCloud sin cambiar la ruta
    for carpeta, clave in (("Desktop", "FXICloudDriveDesktop"), ("Documents", "FXICloudDriveDocuments")):
        if raiz.is_relative_to(casa / carpeta) and sys.platform == "darwin":
            try:
                activo = subprocess.run(["defaults", "read", "com.apple.finder", clave],
                                        capture_output=True, text=True, timeout=5).stdout.strip()
            except (OSError, subprocess.SubprocessError):
                activo = ""
            if activo == "1":
                return "iCloud Drive (Escritorio y Documentos)"
    return None


def avisar_si_esta_en_la_nube():
    global _avisado
    servicio = None if _avisado else en_la_nube()
    _avisado = True
    if servicio:
        print(f"⚠️  Money Pal está en una carpeta que se sube a {servicio}: tus gastos se copian a ese servicio. "
              f"Mueve la carpeta money-pal fuera (p. ej. a tu carpeta de inicio). Ver SECURITY.md.", file=sys.stderr)
