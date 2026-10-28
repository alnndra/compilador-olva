# Compilador de Lenguaje Logístico para Olva Courier

Avance 2, etapas 1 y 2: análisis léxico (tokens y lexemas) y autómatas por token
(ER, AFND, AFD, tabla de transiciones, transiciones y quíntupla).

## Ejecutar en local
    pip install -r requirements.txt
    python app.py
Abrir http://127.0.0.1:5000

## Publicar gratis en Render
1. Subir esta carpeta a un repositorio de GitHub.
2. En render.com elegir New, Blueprint y seleccionar el repositorio. Render lee render.yaml y crea el servicio.
   Si prefieres hacerlo a mano: New, Web Service, Build Command `pip install -r requirements.txt`, Start Command `gunicorn app:app`, plan Free.
3. Render entrega una URL pública. En el plan gratis el servicio se duerme tras unos minutos sin uso y la primera visita tarda unos 50 segundos.

GitHub Pages no sirve para este proyecto porque Flask necesita un servidor.

## Archivos
- render.yaml: configuración de despliegue en Render
- app.py: servidor Flask y rutas
- lexer.py: tokens, expresiones regulares y analizador
- automata.py: ER a AFND (Thompson), AFD (subconjuntos), tabla y quíntupla
- draw.py: dibujo SVG de los autómatas
- generar_tramas.py: regenera los TXT de ejemplo
- static/ejemplos/tramas_100.txt y tramas_con_errores.txt
- tests/test_automatas.py: compara cada AFD contra la librería re
