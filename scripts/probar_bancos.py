"""Money Pal · Verifica que cada banco en banks/ esté bien definido y que su parser dé lo esperado.

Para cada banks/<banco>/:
  1. banco.json tiene los campos obligatorios y patrones válidos.
  2. Si existe pruebas/, procesa pruebas/busqueda-*.json (correos ficticios) y compara con pruebas/esperado.json.

No necesita cuentas en ningún banco ni acceso a Gmail: sirve para revisar contribuciones.

Uso:
  .venv/bin/python scripts/probar_bancos.py            # todos los bancos
  .venv/bin/python scripts/probar_bancos.py bcp        # uno
  .venv/bin/python scripts/probar_bancos.py bcp --actualizar   # regenera esperado.json (revísalo antes de subirlo)
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from leer_correos import RAIZ, cargar_banco, procesar  # noqa: E402

OBLIGATORIOS = ["id", "nombre", "pais", "estado", "zona_horaria", "remitentes", "monedas", "tipos"]
ESTADOS = ["verificado", "muestras", "buscado"]
TIPOS = ["consumo", "pago_servicio", "transferencia", "retiro"]


def validar(banco_id):
    ruta = RAIZ / "banks" / banco_id / "banco.json"
    b = json.loads(ruta.read_text(encoding="utf-8"))
    errores = [f"falta el campo '{c}'" for c in OBLIGATORIOS if c not in b]
    if b.get("id") != banco_id:
        errores.append(f"'id' debe ser '{banco_id}' (el nombre de la carpeta)")
    if b.get("estado") not in ESTADOS:
        errores.append(f"'estado' debe ser uno de {ESTADOS}")
    if not re.fullmatch(r"[+-]\d{2}:\d{2}", b.get("zona_horaria", "")):
        errores.append("'zona_horaria' debe tener la forma -05:00")
    for i, t in enumerate(b.get("tipos", [])):
        donde = f"tipos[{i}] ({t.get('tipo', '?')})"
        if t.get("tipo") not in TIPOS:
            errores.append(f"{donde}: 'tipo' debe ser uno de {TIPOS}")
        if not t.get("asunto_contiene"):
            errores.append(f"{donde}: falta 'asunto_contiene'")
        if t.get("fuente") == "snippet":
            try:
                grupos = set(re.compile(t.get("patron", "")).groupindex)
            except re.error as e:
                errores.append(f"{donde}: patrón inválido: {e}")
                continue
            fijos = set(t.get("fijos", {}))
            for g in ("moneda", "monto", "comercio", "medio"):
                if g not in grupos and g not in fijos:
                    errores.append(f"{donde}: el patrón necesita el grupo (?P<{g}>...) o un valor en 'fijos'")
        elif t.get("fuente") == "cuerpo":
            if not t.get("campos"):
                errores.append(f"{donde}: una fuente 'cuerpo' necesita 'campos' (qué etiqueta del correo tiene cada dato)")
        else:
            errores.append(f"{donde}: 'fuente' debe ser 'snippet' o 'cuerpo'")
    return errores


def probar(banco_id, actualizar=False):
    carpeta = RAIZ / "banks" / banco_id / "pruebas"
    muestras = sorted(carpeta.glob("busqueda-*.json"))
    if not muestras:
        return None, ["sin pruebas (agrega pruebas/busqueda-1.json con correos ficticios)"]
    obtenido = procesar(cargar_banco(banco_id), muestras)
    esperado_ruta = carpeta / "esperado.json"
    if actualizar or not esperado_ruta.exists():
        esperado_ruta.write_text(json.dumps(obtenido, ensure_ascii=False, indent=1), encoding="utf-8")
        return True, [f"esperado.json {'regenerado' if actualizar else 'creado'}: revísalo a mano"]
    esperado = json.loads(esperado_ruta.read_text(encoding="utf-8"))
    diferencias = [f"'{k}' no coincide con esperado.json" for k in esperado if esperado[k] != obtenido.get(k)]
    return not diferencias, diferencias


def main():
    p = argparse.ArgumentParser(description="Verifica las definiciones de bancos y sus pruebas.")
    p.add_argument("bancos", nargs="*")
    p.add_argument("--actualizar", action="store_true", help="Regenera esperado.json con la salida actual")
    a = p.parse_args()

    bancos = a.bancos or sorted(x.parent.name for x in (RAIZ / "banks").glob("*/banco.json"))
    fallas = 0
    for banco_id in bancos:
        errores = validar(banco_id)
        ok, notas = probar(banco_id, a.actualizar) if not errores else (False, [])
        estado = "✅" if not errores and ok else ("⚠️ " if not errores and ok is None else "❌")
        print(f"{estado} {banco_id}")
        for linea in errores + notas:
            print(f"   - {linea}")
        fallas += bool(errores) or ok is False
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
