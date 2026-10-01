"""Money Pal · Patrones de los bancos (banco.json) con límite de tiempo.

Los patrones vienen de banco.json, que cualquiera puede proponer en un Pull Request. Un patrón mal escrito,
p. ej. (a+)+, puede tardar minutos en un texto de 200 caracteres ("backtracking catastrófico") y congelar la
lectura. Tres defensas:
  1. buscar(): cada búsqueda tiene 1 segundo (macOS y Linux) y el texto se recorta a LARGO_MAX.
  2. repeticiones_anidadas(): probar_bancos.py rechaza patrones con repeticiones dentro de repeticiones.
  3. es_lento(): probar_bancos.py prueba cada patrón con textos hechos para provocar ese problema.
"""

import re
import signal
import threading
import time

LIMITE_SEG = 1.0
LARGO_MAX = 5000  # una vista previa de Gmail tiene ~200 caracteres

try:
    from re import _parser as sre_parse  # Python 3.11+
except ImportError:  # pragma: no cover
    import sre_parse


class PatronLento(Exception):
    pass


def _alarma(*_):
    raise PatronLento()


def buscar(compilado, texto, limite=LIMITE_SEG):
    """compilado.search(texto) con límite de tiempo. Lanza PatronLento si se pasa."""
    texto = texto[:LARGO_MAX]
    # signal solo funciona en el hilo principal y no existe en Windows: ahí queda el recorte y la revisión en CI
    if not hasattr(signal, "setitimer") or threading.current_thread() is not threading.main_thread():
        return compilado.search(texto)
    anterior = signal.signal(signal.SIGALRM, _alarma)
    signal.setitimer(signal.ITIMER_REAL, limite)
    try:
        return compilado.search(texto)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, anterior)


REPETICIONES = {sre_parse.MAX_REPEAT, sre_parse.MIN_REPEAT, getattr(sre_parse, "POSSESSIVE_REPEAT", None)} - {None}


def _tiene_repeticion(sub, solo_ilimitada=False):
    for op, arg in sub:
        if op in REPETICIONES and arg[1] > 1 and (not solo_ilimitada or arg[1] == sre_parse.MAXREPEAT):
            return True
        hijos = []
        if op in REPETICIONES:
            hijos = [arg[2]]
        elif op == sre_parse.SUBPATTERN:
            hijos = [arg[-1]]
        elif op == sre_parse.BRANCH:
            hijos = arg[1]
        elif op in (sre_parse.ASSERT, sre_parse.ASSERT_NOT):
            hijos = [arg[1]]
        if any(_tiene_repeticion(h, solo_ilimitada) for h in hijos):
            return True
    return False


def repeticiones_anidadas(patron):
    """True si el patrón repite algo que ya se repite, p. ej. (a+)+ o (\\d+,?)*: la causa típica del problema."""
    def recorrer(sub):
        for op, arg in sub:
            if op in REPETICIONES:
                # (a{1,3}){2} es inofensivo: el problema aparece si alguna de las dos repeticiones no tiene tope
                if arg[1] > 1 and _tiene_repeticion(arg[2], solo_ilimitada=arg[1] != sre_parse.MAXREPEAT):
                    return True
                if recorrer(arg[2]):
                    return True
            elif op == sre_parse.SUBPATTERN and recorrer(arg[-1]):
                return True
            elif op == sre_parse.BRANCH and any(recorrer(h) for h in arg[1]):
                return True
            elif op in (sre_parse.ASSERT, sre_parse.ASSERT_NOT) and recorrer(arg[1]):
                return True
        return False
    return recorrer(sre_parse.parse(patron))


def textos_dificiles(ejemplo=""):
    """Textos que suelen provocar backtracking catastrófico, incluido un ejemplo real del banco alargado."""
    base = ["a" * 3000 + "!", " " * 3000 + "!", "1" * 3000 + "x", "1," * 1500 + "x", "S/ " * 1000, "." * 3000]
    if ejemplo:
        base.append((ejemplo * (LARGO_MAX // max(len(ejemplo), 1) + 1))[:LARGO_MAX])
        base.append(ejemplo[: len(ejemplo) // 2] * 20)
    return base


def es_lento(compilado, ejemplos=(), limite=LIMITE_SEG):
    """Primer texto difícil con el que el patrón se pasa del límite, o None."""
    for ejemplo in list(ejemplos) or [""]:
        for texto in textos_dificiles(ejemplo):
            inicio = time.monotonic()
            try:
                buscar(compilado, texto, limite)
            except PatronLento:
                return texto[:40] + "…"
            if time.monotonic() - inicio > limite:  # sin señales (Windows): se mide igual
                return texto[:40] + "…"
    return None
