"""
Motor de autómatas del Compilador de Lenguaje Logístico.

Flujo por cada token:
    expresión regular  ->  AFND (Thompson, con transiciones épsilon)
                       ->  AFD  (construcción de subconjuntos)
                       ->  tabla de transiciones, lista de transiciones y quíntupla

Todo se calcula desde el texto de la expresión regular, de modo que el
dibujo, la tabla y el reconocedor usado por el analizador léxico salen
de la misma fuente y no pueden contradecirse.

Sintaxis de ER soportada: literales, [clases], ( ), |, *, +, ?, {n}, {n,m}
y escape con barra invertida.
"""
import bisect
from collections import deque

EPS = "ε"
DOTS = "…"


# ----------------------------------------------------------------------
# Etiquetas legibles
# ----------------------------------------------------------------------
def _ch(code):
    c = chr(code)
    return "espacio" if c == " " else c


def ranges_text(ranges):
    parts = []
    for lo, hi in ranges:
        parts.append(_ch(lo) if lo == hi else f"{_ch(lo)}{DOTS}{_ch(hi)}")
    return ", ".join(parts)


def merge_ranges(ranges):
    out = []
    for lo, hi in sorted(ranges):
        if out and lo <= out[-1][1] + 1:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


class Cls:
    """Átomo de la ER: un literal o una clase de caracteres."""

    def __init__(self, ranges, source):
        self.ranges = merge_ranges(ranges)
        self.source = source
        self.label = ranges_text(self.ranges)

    def covers(self, lo, hi):
        return any(a <= lo and hi <= b for a, b in self.ranges)


# ----------------------------------------------------------------------
# Parser de expresiones regulares -> AST
# ----------------------------------------------------------------------
class _Parser:
    def __init__(self, text):
        self.s = text
        self.i = 0

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else None

    def parse(self):
        node = self.alt()
        if self.i != len(self.s):
            raise ValueError(f"ER inválida cerca de la posición {self.i}: {self.s!r}")
        return node

    def alt(self):
        branches = [self.seq()]
        while self.peek() == "|":
            self.i += 1
            branches.append(self.seq())
        return branches[0] if len(branches) == 1 else ("alt", branches)

    def seq(self):
        items = []
        while self.peek() not in (None, "|", ")"):
            items.append(self.rep())
        return items[0] if len(items) == 1 else ("seq", items)

    def rep(self):
        node = self.atom()
        while True:
            c = self.peek()
            if c == "*":
                self.i += 1
                node = ("rep", node, 0, None)
            elif c == "+":
                self.i += 1
                node = ("rep", node, 1, None)
            elif c == "?":
                self.i += 1
                node = ("rep", node, 0, 1)
            elif c == "{":
                j = self.s.index("}", self.i)
                body = self.s[self.i + 1:j]
                self.i = j + 1
                if "," in body:
                    a, b = body.split(",")
                    node = ("rep", node, int(a), int(b) if b else None)
                else:
                    node = ("rep", node, int(body), int(body))
            else:
                return node

    def atom(self):
        c = self.peek()
        if c == "(":
            self.i += 1
            node = self.alt()
            if self.peek() != ")":
                raise ValueError("Falta ')' en la ER")
            self.i += 1
            return node
        if c == "[":
            return self.char_class()
        if c == "\\":
            self.i += 2
            ch = self.s[self.i - 1]
            return ("cls", Cls([(ord(ch), ord(ch))], ch))
        self.i += 1
        return ("cls", Cls([(ord(c), ord(c))], c))

    def _class_char(self):
        c = self.peek()
        if c == "\\":
            self.i += 2
            return self.s[self.i - 1]
        self.i += 1
        return c

    def char_class(self):
        start = self.i
        self.i += 1  # [
        ranges = []
        while self.peek() != "]":
            a = self._class_char()
            if self.peek() == "-" and self.s[self.i + 1] != "]":
                self.i += 1
                b = self._class_char()
                ranges.append((ord(a), ord(b)))
            else:
                ranges.append((ord(a), ord(a)))
        self.i += 1  # ]
        return ("cls", Cls(ranges, self.s[start:self.i]))


def parse_er(text):
    return _Parser(text).parse()


def _collect_atoms(node, out):
    kind = node[0]
    if kind == "cls":
        out.append(node[1])
    elif kind in ("seq", "alt"):
        for sub in node[1]:
            _collect_atoms(sub, out)
    elif kind == "rep":
        _collect_atoms(node[1], out)
    return out


# ----------------------------------------------------------------------
# AFND (Thompson; la concatenación une estados, los épsilon solo aparecen
# en unión, cierre y opcionales)
# ----------------------------------------------------------------------
class _Builder:
    def __init__(self):
        self.n = 0
        self.edges = []
        self.alias = {}

    def new(self):
        self.n += 1
        return self.n - 1

    def find(self, x):
        while x in self.alias:
            x = self.alias[x]
        return x

    def build(self, node):
        kind = node[0]
        if kind == "cls":
            s, e = self.new(), self.new()
            self.edges.append((s, node[1], e))
            return s, e
        if kind == "seq":
            s, e = self.build(node[1][0])
            for sub in node[1][1:]:
                s2, e2 = self.build(sub)
                self.alias[s2] = e
                e = e2
            return s, e
        if kind == "alt":
            s, e = self.new(), self.new()
            for sub in node[1]:
                bs, be = self.build(sub)
                self.edges.append((s, None, bs))
                self.edges.append((be, None, e))
            return s, e
        if kind == "rep":
            _, child, mn, mx = node
            return self._rep(child, mn, mx)
        raise ValueError(kind)

    def _star(self, child):
        s, e = self.new(), self.new()
        bs, be = self.build(child)
        self.edges += [(s, None, bs), (s, None, e), (be, None, bs), (be, None, e)]
        return s, e

    def _plus(self, child):
        s, e = self.new(), self.new()
        bs, be = self.build(child)
        self.edges += [(s, None, bs), (be, None, bs), (be, None, e)]
        return s, e

    def _opt(self, child):
        s, e = self.new(), self.new()
        bs, be = self.build(child)
        self.edges += [(s, None, bs), (be, None, e), (s, None, e)]
        return s, e

    def _rep(self, child, mn, mx):
        if (mn, mx) == (0, None):
            return self._star(child)
        if (mn, mx) == (1, None):
            return self._plus(child)
        if (mn, mx) == (0, 1):
            return self._opt(child)
        pieces = []
        if mx is None:
            pieces += [child] * (mn - 1)
            pieces.append(("rep", child, 1, None))
        else:
            pieces += [child] * mn
            pieces += [("rep", child, 0, 1)] * (mx - mn)
        return self.build(("seq", pieces) if len(pieces) > 1 else pieces[0])


def build_nfa(ast):
    b = _Builder()
    start, end = b.build(ast)
    edges = [(b.find(u), c, b.find(v)) for u, c, v in b.edges]
    start, end = b.find(start), b.find(end)
    # Renumerar por orden de descubrimiento desde el estado inicial
    adj = {}
    for u, c, v in edges:
        adj.setdefault(u, []).append((c, v))
    order, seen, queue = [], {start}, deque([start])
    while queue:
        u = queue.popleft()
        order.append(u)
        for _, v in adj.get(u, []):
            if v not in seen:
                seen.add(v)
                queue.append(v)
    ren = {old: i for i, old in enumerate(order)}
    nedges = [(ren[u], c, ren[v]) for u, c, v in edges if u in ren and v in ren]
    return {"n": len(order), "edges": nedges, "start": ren[start], "accept": ren[end]}


# ----------------------------------------------------------------------
# AFD (construcción de subconjuntos sobre intervalos elementales)
# ----------------------------------------------------------------------
class DFA:
    def __init__(self, nfa, atoms):
        self.atoms = atoms
        points = set()
        for a in atoms:
            for lo, hi in a.ranges:
                points.add(lo)
                points.add(hi + 1)
        pts = sorted(points)
        intervals = []
        for i in range(len(pts) - 1):
            lo, hi = pts[i], pts[i + 1] - 1
            if any(a.covers(lo, hi) for a in atoms):
                intervals.append((lo, hi))
        self.intervals = intervals
        self._starts = [iv[0] for iv in intervals]

        eps, moves = {}, {}
        for u, c, v in nfa["edges"]:
            if c is None:
                eps.setdefault(u, []).append(v)
            else:
                moves.setdefault(u, []).append((c, v))

        def closure(states):
            stack, out = list(states), set(states)
            while stack:
                x = stack.pop()
                for y in eps.get(x, []):
                    if y not in out:
                        out.add(y)
                        stack.append(y)
            return frozenset(out)

        start = closure({nfa["start"]})
        ids = {start: 0}
        order = [start]
        delta = [dict()]
        queue = deque([start])
        while queue:
            S = queue.popleft()
            for k, (lo, hi) in enumerate(intervals):
                T = {v for u in S for c, v in moves.get(u, []) if c.covers(lo, hi)}
                if not T:
                    continue
                T = closure(T)
                if T not in ids:
                    ids[T] = len(order)
                    order.append(T)
                    delta.append(dict())
                    queue.append(T)
                delta[ids[S]][k] = ids[T]
        self.delta = delta
        self.accept = {i for i, S in enumerate(order) if nfa["accept"] in S}
        self.n = len(order)
        self.start = 0

    # -- reconocedor -----------------------------------------------------
    def interval_of(self, code):
        i = bisect.bisect_right(self._starts, code) - 1
        if i >= 0 and code <= self.intervals[i][1]:
            return i
        return None

    def step(self, state, ch):
        k = self.interval_of(ord(ch))
        return None if k is None else self.delta[state].get(k)

    def expected(self, state):
        labels = []
        for _, dst, label in self.edge_groups(state):
            if label not in labels:
                labels.append(label)
        return labels

    def run(self, text):
        """Devuelve (ok, posición_del_fallo, etiquetas_esperadas)."""
        st = self.start
        for i, ch in enumerate(text):
            nxt = self.step(st, ch)
            if nxt is None:
                return False, i, self.expected(st)
            st = nxt
        if st in self.accept:
            return True, len(text), []
        return False, len(text), self.expected(st)

    # -- etiquetas -------------------------------------------------------
    def _label_for(self, ranges):
        ranges = merge_ranges(ranges)
        for a in self.atoms:
            if a.ranges == ranges:
                return a.label
        return ranges_text(ranges)

    def edge_groups(self, only_state=None):
        """Agrupa por (origen, destino) las transiciones con la misma meta."""
        out = []
        for s in range(self.n):
            if only_state is not None and s != only_state:
                continue
            by_dst = {}
            for k, dst in self.delta[s].items():
                by_dst.setdefault(dst, []).append(self.intervals[k])
            for dst in sorted(by_dst):
                out.append((s, dst, self._label_for(by_dst[dst])))
        return out

    def symbol_classes(self):
        """Columnas de la tabla: intervalos con idéntico comportamiento."""
        cols = {}
        for k in range(len(self.intervals)):
            key = tuple(self.delta[s].get(k) for s in range(self.n))
            cols.setdefault(key, []).append(self.intervals[k])
        result = []
        for key, ivs in cols.items():
            ranges = merge_ranges(ivs)
            label = None
            for a in self.atoms:
                if a.ranges == ranges:
                    label = a.label
                    break
            if label is None:
                containers = [a for a in self.atoms
                              if all(a.covers(lo, hi) for lo, hi in ranges)]
                if containers:
                    best = min(containers, key=lambda a: sum(h - l + 1 for l, h in a.ranges))
                    label = f"otras de {best.label}"
                else:
                    label = ranges_text(ranges)
            result.append((label, key, ranges))
        result.sort(key=lambda t: t[2][0][0])
        return result


# ----------------------------------------------------------------------
# Paquete completo para un token
# ----------------------------------------------------------------------
def analizar_er(er_text):
    ast = parse_er(er_text)
    atoms = _collect_atoms(ast, [])
    nfa = build_nfa(ast)
    dfa = DFA(nfa, atoms)

    # Alfabeto Σ (átomos distintos en orden de aparición)
    sigma, seen = [], set()
    for a in atoms:
        if a.label not in seen:
            seen.add(a.label)
            sigma.append(a.label)

    # AFND: aristas con etiqueta de texto
    nfa_edges = []
    for u, c, v in nfa["edges"]:
        nfa_edges.append((u, v, EPS if c is None else c.label))

    # AFD: tabla y transiciones
    classes = dfa.symbol_classes()
    tabla = {
        "columnas": [c[0] for c in classes],
        "filas": [
            {"estado": f"q{s}",
             "inicial": s == dfa.start,
             "final": s in dfa.accept,
             "celdas": [("q%d" % c[1][s]) if c[1][s] is not None else "" for c in classes]}
            for s in range(dfa.n)
        ],
    }
    transiciones = []
    for s in range(dfa.n):
        for label, key, _ in classes:
            if key[s] is not None:
                transiciones.append(f"δ(q{s}, {label}) = q{key[s]}")

    return {
        "er": er_text,
        "dfa": dfa,
        "nfa": nfa,
        "sigma": sigma,
        "afnd": {
            "n": nfa["n"],
            "edges": nfa_edges,
            "start": nfa["start"],
            "accept": [nfa["accept"]],
            "n_epsilon": sum(1 for e in nfa_edges if e[2] == EPS),
        },
        "afd": {
            "n": dfa.n,
            "edges": dfa.edge_groups(),
            "start": dfa.start,
            "accept": sorted(dfa.accept),
        },
        "tabla": tabla,
        "transiciones": transiciones,
        "quintupla": {
            "Q": [f"q{i}" for i in range(dfa.n)],
            "sigma": sigma,
            "q0": "q0",
            "F": [f"q{i}" for i in sorted(dfa.accept)],
        },
    }


# ----------------------------------------------------------------------
# Simulación paso a paso (para la animación de la web)
#   Cada paso: activos (estados resaltados), aristas (flechas usadas),
#   leido (índice del símbolo que se acaba de leer, -1 si ninguno),
#   consumido (cuántos símbolos ya se procesaron), texto y fin ("ok"/"fallo").
# ----------------------------------------------------------------------
def _conj(estados):
    return "{" + ", ".join(f"q{i}" for i in sorted(estados)) + "}"


def simular_afd(res, cadena):
    dfa = res["dfa"]
    st = dfa.start
    pasos = [{"activos": [st], "aristas": [], "leido": -1, "consumido": 0,
              "texto": f"Se parte del estado inicial q{st}."}]
    for i, ch in enumerate(cadena):
        nxt = dfa.step(st, ch)
        if nxt is None:
            esp = ", ".join(dfa.expected(st)) or "nada más (la cadena debía terminar)"
            pasos.append({"activos": [st], "aristas": [], "leido": i, "consumido": i, "fin": "fallo",
                          "texto": f"Se lee «{ch}» en q{st}: no hay transición. Se esperaba: {esp}. Cadena rechazada."})
            return {"aceptada": False, "pasos": pasos}
        pasos.append({"activos": [nxt], "aristas": [[st, nxt]], "leido": i, "consumido": i + 1,
                      "texto": f"Se lee «{ch}»: δ(q{st}, {ch}) = q{nxt}."})
        st = nxt
    ok = st in dfa.accept
    texto = (f"Fin de la cadena en q{st}, que es de aceptación. Cadena aceptada." if ok else
             f"Fin de la cadena en q{st}, que no es de aceptación. Cadena rechazada.")
    pasos.append({"activos": [st], "aristas": [], "leido": -1, "consumido": len(cadena),
                  "fin": "ok" if ok else "fallo", "texto": texto})
    return {"aceptada": ok, "pasos": pasos}


def simular_afnd(res, cadena):
    nfa = res["nfa"]
    eps, mov = {}, []
    for u, c, v in nfa["edges"]:
        if c is None:
            eps.setdefault(u, []).append(v)
        else:
            mov.append((u, c, v))

    def cierre(base):
        out, usadas, pila = set(base), [], list(base)
        while pila:
            x = pila.pop()
            for y in eps.get(x, []):
                if y not in out:
                    out.add(y)
                    usadas.append([x, y])
                    pila.append(y)
        return out, usadas

    S, usadas = cierre({nfa["start"]})
    pasos = [{"activos": sorted(S), "aristas": usadas, "leido": -1, "consumido": 0,
              "texto": f"Inicio: ε-cerradura de q{nfa['start']} = {_conj(S)}."}]
    for i, ch in enumerate(cadena):
        code = ord(ch)
        M, usadas = set(), []
        for u, c, v in mov:
            if u in S and c.covers(code, code):
                M.add(v)
                if [u, v] not in usadas:
                    usadas.append([u, v])
        if not M:
            pasos.append({"activos": sorted(S), "aristas": [], "leido": i, "consumido": i, "fin": "fallo",
                          "texto": f"Se lee «{ch}» desde {_conj(S)}: ningún estado tiene transición. Cadena rechazada."})
            return {"aceptada": False, "pasos": pasos}
        pasos.append({"activos": sorted(M), "aristas": usadas, "leido": i, "consumido": i + 1,
                      "texto": f"Se lee «{ch}»: desde {_conj(S)} se llega a {_conj(M)}."})
        C, usadas = cierre(M)
        if C != M:
            pasos.append({"activos": sorted(C), "aristas": usadas, "leido": i, "consumido": i + 1,
                          "texto": f"Se siguen las transiciones ε: ε-cerradura = {_conj(C)}."})
        S = C
    ok = nfa["accept"] in S
    texto = (f"Fin de la cadena: q{nfa['accept']} está en {_conj(S)}. Cadena aceptada." if ok else
             f"Fin de la cadena: q{nfa['accept']} no está en {_conj(S)}. Cadena rechazada.")
    pasos.append({"activos": sorted(S), "aristas": [], "leido": -1, "consumido": len(cadena),
                  "fin": "ok" if ok else "fallo", "texto": texto})
    return {"aceptada": ok, "pasos": pasos}
