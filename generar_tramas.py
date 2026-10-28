"""
Genera los archivos de ejemplo de static/ejemplos/:
  tramas_100.txt          100 tramas válidas, organizadas en 4 lotes de 25
  tramas_con_errores.txt  tramas cortas con un error léxico declarado en cada una

Uso:  python generar_tramas.py
Las líneas que empiezan con // son comentarios y el analizador las ignora.
"""
import os
import random
import unicodedata

from lexer import UBIGEOS

random.seed(2026)
SALIDA = os.path.join(os.path.dirname(__file__), "static", "ejemplos")

NOMBRES = ["MARIA FERNANDA", "JOSE LUIS", "CARLA PAOLA", "DIEGO ALONSO", "ANA LUCIA", "LUIS MIGUEL",
           "ROSA ELENA", "JORGE ANTONIO", "KAREN YULIANA", "PEDRO PABLO", "SOFIA ALEJANDRA",
           "CESAR AUGUSTO", "LUCIA MERCEDES", "RICARDO ANDRES", "VALERIA NICOLE", "MARCO ANTONIO",
           "DANIELA ISABEL", "FRANCO ALEXANDER", "MILAGROS DEL PILAR", "RENZO GABRIEL", "NATALIA BEATRIZ",
           "HECTOR RAUL", "CAMILA ANDREA", "SERGIO IVAN", "BRENDA XIMENA", "ALONSO MATEO",
           "PAMELA LISSETH", "EDGAR MANUEL", "ELIANA ROCIO", "OMAR JESUS"]
APELLIDOS = ["TORRES QUISPE", "RAMIREZ CASTRO", "FLORES HUAMAN", "GARCIA ROJAS", "VASQUEZ LOPEZ",
             "MENDOZA PAREDES", "CHAVEZ SALAZAR", "RODRIGUEZ DIAZ", "CONDORI MAMANI", "SANCHEZ VEGA",
             "REYES CARRASCO", "PEREZ ALVAREZ", "HUAMANI CCAHUANA", "MORALES CASTILLO", "GUTIERREZ NUÑEZ",
             "CASTAÑEDA RIOS", "ORTEGA CAMPOS", "ESPINOZA PEÑA", "ROMERO SILVA", "AGUILAR ZEGARRA"]
DOMINIOS = ["gmail.com", "hotmail.com", "outlook.com", "yahoo.es", "usil.pe", "icloud.com"]

VIAS = {
    "AV": ["MARISCAL_RAMON_CASTILLA", "ALFREDO_BENAVIDES", "LA_MARINA", "AREQUIPA", "JAVIER_PRADO",
           "PETIT_THOUARS", "UNIVERSITARIA", "ANGAMOS", "JOSE_LARCO", "BRASIL", "LA_MOLINA",
           "PRIMAVERA", "HIPOLITO_UNANUE", "CAMINOS_DEL_INCA", "TOMAS_MARSANO"],
    "JR": ["DE_LA_UNION", "CAÑETE", "AYACUCHO", "HUALLAGA", "CARABAYA", "LAS_PALMERAS",
           "CUSCO", "PUNO", "MONTE_CARMELO", "SAN_MARTIN"],
    "PSJ": ["LAS_ORQUIDEAS", "LOS_CLAVELES", "SANTA_ROSA", "EL_SOL", "LAS_GAVIOTAS", "LOS_JAZMINES"],
    "CAL": ["LOS_CEDROS", "LAS_BEGONIAS", "LOS_ALAMOS", "SCHELL", "LOS_PINOS", "DOS_DE_MAYO",
            "LAS_CAMELIAS", "BELLAVISTA", "LOS_NARANJOS"],
}
DISTRITOS = ["150101", "150103", "150104", "150105", "150108", "150110", "150113", "150114", "150115",
             "150116", "150117", "150120", "150121", "150122", "150130", "150131", "150132", "150133",
             "150134", "150135", "150136", "150140", "150141", "150142", "150143"]
SEDES = ["LIM"] * 6 + ["SUR", "NOR", "ORI"]


def ascii_min(texto):
    s = unicodedata.normalize("NFD", texto.lower().replace("ñ", "n"))
    return "".join(c for c in s if c.isalnum())


def trama(i, valida=True):
    nombre = random.choice(NOMBRES)
    apellido = random.choice(APELLIDOS)
    primero = ascii_min(nombre.split()[0])
    ap1 = ascii_min(apellido.split()[0])
    usuario = random.choice([f"{primero}.{ap1}", f"{primero[0]}.{ap1}", f"{primero}{ap1}",
                             f"{primero[0]}{ap1}{random.randint(1, 99)}", f"{primero}_{ap1}"])
    tipo = random.choice(["AV", "AV", "AV", "JR", "JR", "PSJ", "CAL", "CAL"])
    numero = str(random.randint(1, 9999)) + (random.choice("ABCD") if random.random() < 0.2 else "")
    interior = str(random.choice([random.randint(1, 20), random.randint(101, 1204)])) + \
        (random.choice("ABC") if random.random() < 0.3 else "")
    dia = random.randint(1, 30)
    mes = random.choice([10, 11])
    if mes == 10:
        dia = random.randint(27, 31)
    codigo = "OLVA_2026_%s_%s_%06d" % (random.choice(SEDES), random.choice(["EX", "ST"]), 4500 + i)
    campos = [
        codigo,
        "N" + nombre + " " + apellido,
        "D" + str(random.randint(1, 7)) + "".join(random.choice("0123456789") for _ in range(7)),
        "T9" + "".join(random.choice("0123456789") for _ in range(8)),
        "C" + usuario + "@" + random.choice(DOMINIOS),
        "V" + tipo + "*" + random.choice(VIAS[tipo]) + "#" + numero,
        "I" + interior,
        "U" + random.choice(DISTRITOS),
        "F%02d/%02d/2026" % (dia, mes),
    ]
    return campos


def escribir_100():
    lineas = [
        "// TRAMAS DE EJEMPLO: Compilador de Lenguaje Logístico de Olva Courier",
        "// 100 tramas válidas organizadas en 4 lotes de 25.",
        "// Formato: CODIGO|Nombre|Dni|Telefono|Correo|Via*Nombre#Numero|Interior|Ubigeo|Fecha",
        "// Las líneas que empiezan con // son comentarios y se ignoran al compilar.",
        "",
    ]
    lotes = ["Lote 1: despacho de la mañana", "Lote 2: despacho del mediodía",
             "Lote 3: despacho de la tarde", "Lote 4: despacho nocturno"]
    n = 0
    for b, titulo in enumerate(lotes):
        lineas.append(f"// ===== {titulo} (tramas {b * 25 + 1:03d} a {b * 25 + 25:03d}) =====")
        for _ in range(25):
            lineas.append("|".join(trama(n)))
            n += 1
        lineas.append("")
    ruta = os.path.join(SALIDA, "tramas_100.txt")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas).rstrip() + "\n")
    return ruta


def escribir_errores():
    def base(i):
        return trama(i)

    casos = [
        ("válida de referencia", lambda c: c),
        ("DNI con 7 dígitos", lambda c: c[:2] + ["D" + c[2][1:8]] + c[3:]),
        ("teléfono que no empieza con 9", lambda c: c[:3] + ["T8" + c[3][2:]] + c[4:]),
        ("correo sin arroba", lambda c: c[:4] + [c[4].replace("@", "#")] + c[5:]),
        ("código sin tipo de servicio", lambda c: [c[0].replace("_EX_", "_").replace("_ST_", "_")] + c[1:]),
        ("fecha con una barra menos", lambda c: c[:8] + [c[8].replace("/", "", 1)]),
        ("tipo de vía inexistente", lambda c: c[:5] + [c[5].replace("VAV", "VXX").replace("VJR", "VXX").replace("VPSJ", "VXX").replace("VCAL", "VXX")] + c[6:]),
        ("nombre de vía con minúsculas", lambda c: c[:5] + [c[5].split("*")[0] + "*" + c[5].split("*")[1].lower()] + c[6:]),
        ("ubigeo fuera de Lima", lambda c: c[:7] + ["U090101"] + c[8:]),
        ("falta el campo de interior (los campos siguientes se corren)", lambda c: c[:6] + c[7:]),
        ("campo de vía sin numeral", lambda c: c[:5] + [c[5].split("#")[0]] + c[6:]),
        ("válida de cierre", lambda c: c),
    ]
    lineas = [
        "// TRAMAS CON ERRORES LÉXICOS: sirven para mostrar que el compilador rechaza lo que no pertenece al lenguaje.",
        "// Cada comentario indica el error que trae la trama de la línea siguiente.",
        "",
    ]
    for i, (motivo, f) in enumerate(casos):
        lineas.append(f"// Trama {i + 1}: {motivo}")
        lineas.append("|".join(f(base(900 + i))))
    ruta = os.path.join(SALIDA, "tramas_con_errores.txt")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    return ruta


if __name__ == "__main__":
    os.makedirs(SALIDA, exist_ok=True)
    print(escribir_100())
    print(escribir_errores())
