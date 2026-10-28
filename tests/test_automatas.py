"""
Verifica que cada AFD construido por automata.py acepta exactamente el mismo
lenguaje que re.fullmatch de Python con la misma expresión regular.
Uso:  python tests/test_automatas.py
"""
import os
import random
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lexer import TOKENS, AUTOMATAS, analizar_texto  # noqa: E402

random.seed(7)
ALFABETO = list("ABCDEFGHIJKLMNOPQRSTUVWXYZÑabcdefghijklmnopqrstuvwxyz0123456789._@#*/|_ -")


def generar_validos(token, n=60):
    """Genera cadenas válidas recorriendo el AFD al azar hasta un estado final."""
    dfa = AUTOMATAS[token]["dfa"]
    salida = []
    for _ in range(n * 20):
        st, cadena = dfa.start, []
        for _ in range(60):
            opciones = list(dfa.delta[st].items())
            if st in dfa.accept and (not opciones or random.random() < 0.25):
                break
            if not opciones:
                break
            k, dst = random.choice(opciones)
            lo, hi = dfa.intervals[k]
            cadena.append(chr(random.randint(lo, hi)))
            st = dst
        if st in dfa.accept:
            salida.append("".join(cadena))
        if len(salida) >= n:
            break
    return salida


def mutar(cadena):
    if not cadena:
        return random.choice(ALFABETO)
    cadena = list(cadena)
    op = random.choice(["sub", "del", "ins", "trunc"])
    i = random.randrange(len(cadena))
    if op == "sub":
        cadena[i] = random.choice(ALFABETO)
    elif op == "del":
        del cadena[i]
    elif op == "ins":
        cadena.insert(i, random.choice(ALFABETO))
    else:
        cadena = cadena[:i]
    return "".join(cadena)


def main():
    fallos = 0
    for t in TOKENS:
        nombre, er = t["nombre"], t["er"]
        dfa = AUTOMATAS[nombre]["dfa"]
        pyre = re.compile(er)
        # el ejemplo declarado debe ser válido
        assert pyre.fullmatch(t["ejemplo"]) and dfa.run(t["ejemplo"])[0], f"ejemplo inválido en {nombre}"
        validos = generar_validos(nombre)
        assert validos, f"No se generaron cadenas válidas para {nombre}"
        pruebas = list(validos)
        for v in validos:
            pruebas.extend(mutar(v) for _ in range(6))
        pruebas.extend(["", "X", "9999", "OLVA", "@@"])
        malos = 0
        for s in pruebas:
            esperado = pyre.fullmatch(s) is not None
            obtenido = dfa.run(s)[0]
            if esperado != obtenido:
                malos += 1
                print(f"  DIFERENCIA en {nombre}: {s!r} re={esperado} afd={obtenido}")
        fallos += malos
        print(f"{nombre:13s} estados AFND={AUTOMATAS[nombre]['afnd']['n']:2d} "
              f"AFD={AUTOMATAS[nombre]['afd']['n']:2d}  pruebas={len(pruebas):4d}  diferencias={malos}")
    print("TOTAL de diferencias:", fallos)

    # Los archivos de ejemplo
    base = os.path.join(os.path.dirname(__file__), "..", "static", "ejemplos")
    for nombre in ("tramas_100.txt", "tramas_con_errores.txt"):
        ruta = os.path.join(base, nombre)
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as f:
                r = analizar_texto(f.read())["resumen"]
            print(f"{nombre}: {r['total']} tramas, {r['validas']} válidas, {r['con_error']} con error")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
