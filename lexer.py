"""
Analizador léxico de la trama logística de Olva Courier.

La trama que emite el terminal de clasificación es una línea con 9 campos
separados por barra vertical:

    OLVA_2026_LIM_EX_004512|NMARIA FERNANDA TORRES|D72845196|T987654321|
    Cmf.torres@gmail.com|VAV*MARISCAL_RAMON_CASTILLA#1850|I302B|U150140|F27/10/2026

El campo de vía contiene tres lexemas (tipo, nombre y número), de modo que
cada trama produce 11 tokens. Cada lexema se valida con el AFD construido a
partir de la expresión regular de su token (ver automata.py).
"""
from automata import analizar_er

TOKENS = [
    dict(nombre="CODIGO_ENVIO", er=r"OLVA_[0-9]{4}_[A-Z]{3}_(EX|ST)_[0-9]{6}",
         desc="Código del envío: prefijo OLVA, año, sede, tipo de servicio (EX express o ST estándar) y correlativo.",
         ejemplo="OLVA_2026_LIM_EX_004512"),
    dict(nombre="NOMBRE", er=r"N[A-ZÑ]+( [A-ZÑ]+)*",
         desc="Nombre completo del comprador. Empieza con N y admite varias palabras separadas por espacio.",
         ejemplo="NMARIA FERNANDA TORRES"),
    dict(nombre="DNI", er=r"D[0-9]{8}",
         desc="Documento de identidad: letra D y 8 dígitos.",
         ejemplo="D72845196"),
    dict(nombre="TELEFONO", er=r"T9[0-9]{8}",
         desc="Celular peruano: letra T, un 9 inicial y 8 dígitos más.",
         ejemplo="T987654321"),
    dict(nombre="CORREO", er=r"C[a-z0-9._]+@[a-z0-9]+(\.[a-z]+)+",
         desc="Correo electrónico: letra C, usuario, arroba y dominio con uno o más puntos.",
         ejemplo="Cmf.torres@gmail.com"),
    dict(nombre="TIPO_VIA", er=r"V(AV|JR|PSJ|CAL)",
         desc="Tipo de vía: avenida, jirón, pasaje o calle, precedido por la letra V.",
         ejemplo="VAV"),
    dict(nombre="NOMBRE_VIA", er=r"[A-ZÑ]+(_[A-ZÑ]+)*",
         desc="Nombre de la vía en mayúsculas; las palabras se unen con guion bajo.",
         ejemplo="MARISCAL_RAMON_CASTILLA"),
    dict(nombre="NUMERO", er=r"#[0-9]+[A-Z]?",
         desc="Número de puerta: numeral, dígitos y una letra opcional.",
         ejemplo="#1850"),
    dict(nombre="INTERIOR", er=r"I[0-9]+[A-Z]?",
         desc="Interior o departamento: letra I, dígitos y una letra opcional.",
         ejemplo="I302B"),
    dict(nombre="UBIGEO", er=r"U1501[0-9]{2}",
         desc="Ubigeo del distrito de Lima: letra U y el código 1501 seguido de 2 dígitos.",
         ejemplo="U150140"),
    dict(nombre="FECHA", er=r"F[0-9]{2}/[0-9]{2}/[0-9]{4}",
         desc="Fecha de entrega con formato dd/mm/aaaa, precedida por la letra F.",
         ejemplo="F27/10/2026"),
]

# Orden de los 9 campos de la trama y a qué token(es) corresponde cada uno
CAMPOS = [
    ("CODIGO", "Código de envío", ["CODIGO_ENVIO"]),
    ("NOMBRE", "Comprador", ["NOMBRE"]),
    ("DNI", "Documento", ["DNI"]),
    ("TELEFONO", "Celular", ["TELEFONO"]),
    ("CORREO", "Correo", ["CORREO"]),
    ("VIA", "Dirección: vía", ["TIPO_VIA", "NOMBRE_VIA", "NUMERO"]),
    ("INTERIOR", "Dirección: interior", ["INTERIOR"]),
    ("UBIGEO", "Distrito", ["UBIGEO"]),
    ("FECHA", "Entrega", ["FECHA"]),
]

UBIGEOS = {
    "150101": "Lima", "150102": "Ancón", "150103": "Ate", "150104": "Barranco",
    "150105": "Breña", "150106": "Carabayllo", "150107": "Chaclacayo",
    "150108": "Chorrillos", "150109": "Cieneguilla", "150110": "Comas",
    "150111": "El Agustino", "150112": "Independencia", "150113": "Jesús María",
    "150114": "La Molina", "150115": "La Victoria", "150116": "Lince",
    "150117": "Los Olivos", "150118": "Lurigancho", "150119": "Lurín",
    "150120": "Magdalena del Mar", "150121": "Pueblo Libre", "150122": "Miraflores",
    "150123": "Pachacámac", "150124": "Pucusana", "150125": "Puente Piedra",
    "150126": "Punta Hermosa", "150127": "Punta Negra", "150128": "Rímac",
    "150129": "San Bartolo", "150130": "San Borja", "150131": "San Isidro",
    "150132": "San Juan de Lurigancho", "150133": "San Juan de Miraflores",
    "150134": "San Luis", "150135": "San Martín de Porres", "150136": "San Miguel",
    "150137": "Santa Anita", "150138": "Santa María del Mar", "150139": "Santa Rosa",
    "150140": "Santiago de Surco", "150141": "Surquillo", "150142": "Villa El Salvador",
    "150143": "Villa María del Triunfo",
}

VIAS = {"AV": "Av.", "JR": "Jr.", "PSJ": "Psje.", "CAL": "Calle"}
SERVICIOS = {"EX": "express", "ST": "estándar"}

# ----------------------------------------------------------------------
# Autómatas (se calculan una sola vez al iniciar)
# ----------------------------------------------------------------------
AUTOMATAS = {}
for _t in TOKENS:
    _t["automata"] = analizar_er(_t["er"])
    AUTOMATAS[_t["nombre"]] = _t["automata"]


def _titulo(texto):
    return " ".join(p.capitalize() for p in texto.replace("_", " ").split())


def _valor(token, lexema):
    if token == "CODIGO_ENVIO":
        _, anio, sede, serv, corr = lexema.split("_")
        return f"Envío {corr}, sede {sede}, servicio {SERVICIOS.get(serv, serv)}, año {anio}"
    if token == "NOMBRE":
        return _titulo(lexema[1:])
    if token in ("DNI", "TELEFONO", "INTERIOR"):
        return lexema[1:]
    if token == "CORREO":
        return lexema[1:]
    if token == "TIPO_VIA":
        return VIAS.get(lexema[1:], lexema[1:])
    if token == "NOMBRE_VIA":
        return _titulo(lexema)
    if token == "NUMERO":
        return lexema[1:]
    if token == "UBIGEO":
        cod = lexema[1:]
        return f"{cod}, {UBIGEOS.get(cod, 'distrito no registrado')}"
    if token == "FECHA":
        return lexema[1:]
    return lexema


_AMIGABLE = {
    "0…9": "un dígito",
    "A…Z": "una letra mayúscula",
    "A…Z, Ñ": "una letra mayúscula",
    "a…z": "una letra minúscula",
    "a…z, 0…9": "una letra minúscula o un dígito",
}


def _describir(labels):
    nombres = []
    for l in labels:
        nombres.append(_AMIGABLE.get(l, f"«{l}»"))
    # sin repetidos, conservando el orden
    vistos = []
    for n in nombres:
        if n not in vistos:
            vistos.append(n)
    return " o ".join(vistos) if vistos else "fin de la cadena"


def validar(token, lexema):
    """Corre el AFD del token. Devuelve (ok, mensaje_de_error)."""
    dfa = AUTOMATAS[token]["dfa"]
    ok, pos, esperado = dfa.run(lexema)
    if ok:
        return True, ""
    if pos < len(lexema):
        return False, (f"Posición {pos + 1}: se leyó «{lexema[pos]}» y se esperaba "
                       f"{_describir(esperado)}.")
    return False, (f"La cadena terminó en la posición {len(lexema)} y se esperaba "
                   f"{_describir(esperado)}.")


def _fila(token, lexema):
    ok, err = validar(token, lexema)
    return {"token": token, "lexema": lexema,
            "valor": _valor(token, lexema) if ok else "",
            "ok": ok, "error": err}


def _faltante(token, motivo):
    return {"token": token, "lexema": "", "valor": "", "ok": False, "error": motivo}


def analizar_trama(linea):
    campos = linea.split("|")
    filas = []
    for idx, (clave, _, tokens) in enumerate(CAMPOS):
        if idx >= len(campos):
            for t in tokens:
                filas.append(_faltante(t, f"Falta el campo {idx + 1} de {len(CAMPOS)} de la trama."))
            continue
        campo = campos[idx]
        if clave != "VIA":
            filas.append(_fila(tokens[0], campo))
            continue
        i, j = campo.find("*"), campo.find("#")
        if i < 0 or j < 0 or j < i:
            msg = "El campo de vía debe tener la forma V<tipo>*<nombre>#<número>."
            for t in tokens:
                filas.append(_faltante(t, msg))
            continue
        filas.append(_fila("TIPO_VIA", campo[:i]))
        filas.append(_fila("NOMBRE_VIA", campo[i + 1:j]))
        filas.append(_fila("NUMERO", campo[j:]))
    if len(campos) > len(CAMPOS):
        extra = "|".join(campos[len(CAMPOS):])
        filas.append({"token": "SOBRANTE", "lexema": extra, "valor": "", "ok": False,
                      "error": f"La trama tiene {len(campos) - len(CAMPOS)} campo(s) de más."})
    return filas


def _resumen(filas):
    def val(tok):
        for f in filas:
            if f["token"] == tok and f["ok"]:
                return f["valor"]
        return ""
    codigo = next((f["lexema"] for f in filas if f["token"] == "CODIGO_ENVIO" and f["ok"]), "")
    ubigeo = val("UBIGEO")
    return {"codigo": codigo,
            "comprador": val("NOMBRE"),
            "distrito": ubigeo.split(", ", 1)[1] if ", " in ubigeo else ""}


def analizar_texto(texto, max_lineas=5000):
    """Analiza un archivo completo. Las líneas vacías y las que empiezan con // se ignoran."""
    tramas, por_token = [], {t["nombre"]: {"ok": 0, "error": 0} for t in TOKENS}
    for n_linea, linea in enumerate(texto.splitlines(), start=1):
        limpia = linea.strip()
        if not limpia or limpia.startswith("//"):
            continue
        if len(tramas) >= max_lineas:
            break
        filas = analizar_trama(limpia)
        for f in filas:
            if f["token"] in por_token:
                por_token[f["token"]]["ok" if f["ok"] else "error"] += 1
        tramas.append({
            "n": len(tramas) + 1,
            "linea": n_linea,
            "raw": limpia,
            "ok": all(f["ok"] for f in filas),
            "tokens": filas,
            "resumen": _resumen(filas),
        })
    validas = sum(1 for t in tramas if t["ok"])
    return {
        "tramas": tramas,
        "resumen": {
            "total": len(tramas),
            "validas": validas,
            "con_error": len(tramas) - validas,
            "tokens_reconocidos": sum(1 for t in tramas for f in t["tokens"] if f["ok"]),
            "por_token": por_token,
        },
    }
