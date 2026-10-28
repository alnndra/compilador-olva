"""
Compilador de Lenguaje Logístico para Olva Courier (avance 2: etapas 1 y 2).

Ejecutar en local:   python app.py     y abrir http://127.0.0.1:5000
En producción:       gunicorn app:app
"""
import os

from flask import Flask, jsonify, render_template, request

from automata import simular_afd, simular_afnd
from draw import svg_automata
from lexer import AUTOMATAS, CAMPOS, TOKENS, analizar_texto

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024   # 2 MB por solicitud

EJEMPLO = (
    "// Escribe aquí tus tramas, una por línea. Las líneas con // son comentarios.\n"
    "OLVA_2026_LIM_EX_004512|NMARIA FERNANDA TORRES|D72845196|T987654321|Cmf.torres@gmail.com|"
    "VAV*MARISCAL_RAMON_CASTILLA#1850|I302B|U150140|F27/10/2026\n"
    "OLVA_2026_LIM_ST_004513|NJOSE LUIS RAMIREZ CASTRO|D45120936|T912345678|Cj.ramirez@hotmail.com|"
    "VJR*DE_LA_UNION#456|I12|U150101|F28/10/2026\n"
    "// La siguiente trama trae un DNI con 7 dígitos a propósito:\n"
    "OLVA_2026_LIM_EX_004514|NCARLA PAOLA FLORES HUAMAN|D7284519|T987123456|Ccarla.flores@usil.pe|"
    "VCAL*LOS_CEDROS#78A|I5|U150131|F29/10/2026\n"
)
TRAMA_MODELO = EJEMPLO.splitlines()[1]


def _vista_tokens():
    vista = []
    for t in TOKENS:
        a = t["automata"]
        vista.append({
            "nombre": t["nombre"],
            "er": t["er"],
            "desc": t["desc"],
            "ejemplo": t["ejemplo"],
            "sigma": a["sigma"],
            "afnd_n": a["afnd"]["n"],
            "afnd_eps": a["afnd"]["n_epsilon"],
            "afd_n": a["afd"]["n"],
            "svg_afnd": svg_automata(a["afnd"]["n"], a["afnd"]["edges"], a["afnd"]["start"],
                                     a["afnd"]["accept"], t["nombre"] + "-n",
                                     f"AFND del token {t['nombre']}"),
            "svg_afd": svg_automata(a["afd"]["n"], a["afd"]["edges"], a["afd"]["start"],
                                    a["afd"]["accept"], t["nombre"] + "-d",
                                    f"AFD del token {t['nombre']}"),
            "tabla": a["tabla"],
            "transiciones": a["transiciones"],
            "quintupla": a["quintupla"],
        })
    return vista


TOKENS_VISTA = _vista_tokens()
CAMPOS_VISTA = [{"clave": c, "titulo": t, "tokens": toks, "ejemplo": seg}
                for (c, t, toks), seg in zip(CAMPOS, TRAMA_MODELO.split("|"))]


@app.route("/")
def index():
    return render_template("index.html", tokens=TOKENS_VISTA, campos=CAMPOS_VISTA,
                           ejemplo=EJEMPLO, trama_modelo=TRAMA_MODELO.split("|"))


@app.post("/api/analizar")
def analizar():
    datos = request.get_json(silent=True) or {}
    texto = datos.get("texto", "")
    if not isinstance(texto, str) or not texto.strip():
        return jsonify(error="No hay tramas para compilar. Carga un archivo o escribe el código."), 400
    return jsonify(analizar_texto(texto))


@app.post("/api/simular")
def simular():
    datos = request.get_json(silent=True) or {}
    token, cadena, tipo = datos.get("token"), datos.get("cadena", ""), datos.get("automata")
    if token not in AUTOMATAS or tipo not in ("afd", "afnd"):
        return jsonify(error="Token o autómata no válido."), 400
    if not isinstance(cadena, str) or len(cadena) > 200:
        return jsonify(error="La cadena debe tener como máximo 200 símbolos."), 400
    res = AUTOMATAS[token]
    return jsonify((simular_afd if tipo == "afd" else simular_afnd)(res, cadena))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
