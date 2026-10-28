"""
Dibuja AFND y AFD como SVG directamente desde el código fuente (sin Graphviz).

Distribución: los estados se ordenan por capas (camino más largo desde el
estado inicial, ignorando los arcos de retorno). Las capas se acomodan en
filas que van de izquierda a derecha y luego de derecha a izquierda, de modo
que los autómatas largos (como el del código de envío) no queden gigantes.
Las filas solo se cortan en capas de un único estado, para no partir las
ramas de una unión.
"""
import math
from collections import deque
from xml.sax.saxutils import escape

R = 17          # radio del estado
GAPX = 100      # separación horizontal entre capas
GAPY = 76       # separación vertical dentro de una capa
MX = 86         # margen lateral (deja espacio a la flecha de inicio)
TOP = 70        # espacio superior para bucles


def _layers(n, edges, start):
    adj = [[] for _ in range(n)]
    for u, v, _ in edges:
        if u != v:
            adj[u].append(v)
    estado, back = [0] * n, set()

    def dfs(u):
        estado[u] = 1
        for v in adj[u]:
            if estado[v] == 0:
                dfs(v)
            elif estado[v] == 1:
                back.add((u, v))
        estado[u] = 2

    dfs(start)
    dag = {(u, v) for u in range(n) for v in adj[u] if (u, v) not in back}
    indeg = [0] * n
    for u, v in dag:
        indeg[v] += 1
    capa = [0] * n
    queue = deque(i for i in range(n) if indeg[i] == 0)
    while queue:
        u = queue.popleft()
        for v in sorted(x for (a, x) in dag if a == u):
            capa[v] = max(capa[v], capa[u] + 1)
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    return capa, back


def _cortar_filas(por_capa, per_row):
    filas, i, n = [], 0, len(por_capa)
    while i < n:
        if n - i <= per_row:
            filas.append(por_capa[i:])
            break
        lim = i + per_row - 1
        corte = None
        for k in range(lim, i + 1, -1):
            if len(por_capa[k]) == 1:
                corte = k
                break
        if corte is None:
            k = lim + 1
            while k < n and len(por_capa[k]) != 1:
                k += 1
            corte = min(k, n - 1)
        filas.append(por_capa[i:corte + 1])
        i = corte + 1
    return filas


def _posiciones(n, edges, start, per_row):
    capa, back = _layers(n, edges, start)
    n_capas = max(capa) + 1
    preds = {i: [] for i in range(n)}
    for u, v, _ in edges:
        if u != v and (u, v) not in back:
            preds[v].append(u)

    orden_y, por_capa = {}, []
    for c in range(n_capas):
        nodos = [i for i in range(n) if capa[i] == c]
        nodos.sort(key=lambda i: (sum(orden_y[p] for p in preds[i]) / len(preds[i])
                                  if preds[i] else 0, i))
        for k, i in enumerate(nodos):
            orden_y[i] = k
        por_capa.append(nodos)

    pos, top = {}, TOP
    x_inicio, direccion = 0.0, 1
    for fila in _cortar_filas(por_capa, per_row):
        mayor = max(len(c) for c in fila)
        centro = top + (mayor - 1) * GAPY / 2 + 24
        for j, nodos in enumerate(fila):
            x = x_inicio + direccion * j * GAPX
            for k, i in enumerate(nodos):
                pos[i] = (x, centro + (k - (len(nodos) - 1) / 2) * GAPY)
        x_inicio += direccion * (len(fila) - 1) * GAPX
        direccion = -direccion
        top += (mayor - 1) * GAPY + 118
    desplazo = MX - min(x for x, _ in pos.values())
    pos = {i: (x + desplazo, y) for i, (x, y) in pos.items()}
    return pos, back


def _dist_seg(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy or 1
    t = max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / l2))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy)), t


def svg_automata(n, edges, start, accept, uid, titulo, per_row=8):
    pos, back = _posiciones(n, edges, start, per_row)
    pares = {}
    for u, v, lab in edges:
        pares.setdefault((u, v), [])
        if lab not in pares[(u, v)]:
            pares[(u, v)].append(lab)

    caja = [10 ** 9, 10 ** 9, -10 ** 9, -10 ** 9]

    def ocupa(x, y, ancho=0, alto=0):
        caja[0] = min(caja[0], x - ancho)
        caja[1] = min(caja[1], y - alto)
        caja[2] = max(caja[2], x + ancho)
        caja[3] = max(caja[3], y + alto)

    marker = f"flecha-{uid}"
    defs = (f'<defs><marker id="{marker}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            f'markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" class="punta"/></marker></defs>')
    aristas, etiquetas, nodos = [], [], []

    for (u, v), labs in pares.items():
        texto = ", ".join(labs)
        es_eps = labs == ["ε"]
        cls = "elabel eps" if es_eps else "elabel"
        ancho_txt = 3.4 * len(texto) + 6
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        if u == v:
            aristas.append(f'<path class="edge" data-u="{u}" data-v="{v}" marker-end="url(#{marker})" '
                           f'd="M{x1 - 9:.1f} {y1 - 15:.1f} C{x1 - 34:.1f} {y1 - 58:.1f} {x1 + 34:.1f} {y1 - 58:.1f} '
                           f'{x1 + 9:.1f} {y1 - 15:.1f}"/>')
            etiquetas.append(f'<text class="{cls}" data-u="{u}" data-v="{v}" x="{x1:.1f}" y="{y1 - 52:.1f}">{escape(texto)}</text>')
            ocupa(x1, y1 - 56, max(34, ancho_txt), 12)
            continue
        dx, dy = x2 - x1, y2 - y1
        largo = math.hypot(dx, dy) or 1
        nx, ny = dy / largo, -dx / largo          # normal "a la izquierda"
        hay_inverso = (v, u) in pares
        es_back = (u, v) in back
        offset, signo = 0.0, 1
        if hay_inverso:
            offset = 22
        else:
            for w, p in pos.items():
                if w in (u, v):
                    continue
                d, t = _dist_seg(p, (x1, y1), (x2, y2))
                if d < R + 8 and 0.02 < t < 0.98:
                    offset = max(34, 0.24 * largo)
                    break
            if offset:
                signo = 1 if ny < 0 else -1       # preferir hacia arriba
                if es_back:
                    signo = -signo
        if offset == 0:
            c = ((x1 + x2) / 2, (y1 + y2) / 2)
        else:
            c = ((x1 + x2) / 2 + 2 * offset * nx * signo, (y1 + y2) / 2 + 2 * offset * ny * signo)

        def recorte(px, py, qx, qy, r):
            d = math.hypot(qx - px, qy - py) or 1
            return px + (qx - px) / d * r, py + (qy - py) / d * r

        sx, sy = recorte(x1, y1, c[0], c[1], R)
        ex, ey = recorte(x2, y2, c[0], c[1], R + 2)
        aristas.append(f'<path class="edge" data-u="{u}" data-v="{v}" marker-end="url(#{marker})" '
                       f'd="M{sx:.1f} {sy:.1f} Q{c[0]:.1f} {c[1]:.1f} {ex:.1f} {ey:.1f}"/>')
        mx = 0.25 * x1 + 0.5 * c[0] + 0.25 * x2
        my = 0.25 * y1 + 0.5 * c[1] + 0.25 * y2
        if offset:
            lx, ly = mx + nx * signo * 11, my + ny * signo * 11 + 4
        else:
            lx, ly = mx, my - 9
        etiquetas.append(f'<text class="{cls}" data-u="{u}" data-v="{v}" x="{lx:.1f}" y="{ly:.1f}">{escape(texto)}</text>')
        ocupa(lx, ly - 4, ancho_txt, 10)
        ocupa(mx, my, 4, 4)

    # flecha de entrada
    sx, sy = pos[start]
    aristas.append(f'<path class="edge" marker-end="url(#{marker})" d="M{sx - 62:.1f} {sy:.1f} L{sx - R - 2:.1f} {sy:.1f}"/>')
    etiquetas.append(f'<text class="elabel inicio" x="{sx - 58:.1f}" y="{sy - 9:.1f}">inicio</text>')
    ocupa(sx - 62, sy, 6, 14)

    for i in range(n):
        x, y = pos[i]
        clases = "nodo" + (" inicial" if i == start else "") + (" final" if i in accept else "")
        nodos.append(f'<g class="{clases}" data-q="{i}"><circle cx="{x:.1f}" cy="{y:.1f}" r="{R}"/>')
        if i in accept:
            nodos.append(f'<circle class="aro" cx="{x:.1f}" cy="{y:.1f}" r="{R - 5}"/>')
        nodos.append(f'<text x="{x:.1f}" y="{y + 4:.1f}">q{i}</text></g>')
        ocupa(x, y, R + 3, R + 3)

    pad = 14
    x0, y0 = caja[0] - pad, caja[1] - pad
    w, h = caja[2] - caja[0] + 2 * pad, caja[3] - caja[1] + 2 * pad
    cab = (f'<svg xmlns="http://www.w3.org/2000/svg" class="autosvg" viewBox="{x0:.0f} {y0:.0f} {w:.0f} {h:.0f}" '
           f'width="{w:.0f}" height="{h:.0f}" role="img" aria-label="{escape(titulo)}">')
    return cab + defs + "".join(aristas) + "".join(nodos) + "".join(etiquetas) + "</svg>"
