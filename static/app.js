(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var CAMPOS = window.CAMPOS || [];
  var PAGINA = 10;
  var estado = { data: null, filtro: "todas", q: "", pag: 1 };

  function esc(t) {
    return String(t == null ? "" : t).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function msg(texto, tipo) {
    var m = $("#mensaje");
    m.textContent = texto || "";
    m.className = "mensaje" + (tipo ? " " + tipo : "");
  }

  /* ---------- Navegación ---------- */
  var secciones = $$(".menu a[data-seccion]");
  function marcar(id) {
    secciones.forEach(function (a) { a.classList.toggle("activo", a.dataset.seccion === id); });
  }
  if ("IntersectionObserver" in window) {
    var obs = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) marcar(e.target.id); });
    }, { rootMargin: "-30% 0px -60% 0px" });
    secciones.forEach(function (a) { var s = document.getElementById(a.dataset.seccion); if (s) obs.observe(s); });
  }

  /* ---------- Autómatas: pestañas por token ---------- */
  function mostrarToken(nombre, ir) {
    $$(".pildora").forEach(function (b) {
      var on = b.dataset.token === nombre;
      b.classList.toggle("activo", on);
      b.setAttribute("aria-selected", on ? "true" : "false");
    });
    $$(".panel-token").forEach(function (p) { p.hidden = p.dataset.panel !== nombre; });
    $$("#lista-tokens button").forEach(function (b) { b.classList.toggle("activo", b.dataset.token === nombre); });
    if (ir) document.getElementById("automatas").scrollIntoView({ behavior: "smooth" });
  }
  $$(".pildora").forEach(function (b) { b.addEventListener("click", function () { mostrarToken(b.dataset.token, false); }); });
  $$("#lista-tokens button, .enlace-token").forEach(function (b) {
    b.addEventListener("click", function () { mostrarToken(b.dataset.token, true); });
  });
  $("#buscar-token").addEventListener("input", function (e) {
    var q = e.target.value.trim().toUpperCase();
    $$("#lista-tokens li").forEach(function (li) {
      li.hidden = q && li.textContent.toUpperCase().indexOf(q) < 0;
    });
  });

  /* ---------- Simulación paso a paso ---------- */
  function iniciarSim(box) {
    var lienzo = box.previousElementSibling;
    var svg = lienzo && lienzo.querySelector("svg");
    if (!svg) return;
    var cadena = $(".sim-cadena", box), cinta = $(".sim-cinta", box), ctl = $(".sim-ctl", box);
    var texto = $(".sim-texto", box), cuenta = $(".sim-cuenta", box), play = $(".sim-play", box);
    var sim = null, i = 0, timer = null;

    function limpiar() {
      $$(".activo,.visto,.usada,.ok,.fallo", svg).forEach(function (e) {
        e.classList.remove("activo", "visto", "usada", "ok", "fallo");
      });
    }
    function parar() {
      if (timer) { clearInterval(timer); timer = null; }
      play.textContent = "▶ Reproducir";
    }
    function nodo(q) { return svg.querySelector('.nodo[data-q="' + q + '"]'); }
    function pintarPaso() {
      var p = sim.pasos[i], c = sim.cadena;
      limpiar();
      for (var k = 0; k < i; k++) sim.pasos[k].activos.forEach(function (q) {
        var n = nodo(q); if (n) n.classList.add("visto");
      });
      p.activos.forEach(function (q) {
        var n = nodo(q);
        if (n) { n.classList.remove("visto"); n.classList.add("activo"); if (p.fin) n.classList.add(p.fin); }
      });
      p.aristas.forEach(function (a) {
        $$('[data-u="' + a[0] + '"][data-v="' + a[1] + '"]', svg).forEach(function (e) { e.classList.add("usada"); });
      });
      var h = "";
      for (var j = 0; j < c.length; j++) {
        var cls = j < p.consumido ? "hecho" : "";
        if (j === p.leido) cls += p.fin === "fallo" ? " mal" : " actual";
        h += '<span class="' + cls + '">' + (c[j] === " " ? "&nbsp;" : esc(c[j])) + "</span>";
      }
      cinta.innerHTML = h || "<em>(cadena vacía)</em>";
      texto.textContent = p.texto;
      texto.className = "sim-texto" + (p.fin ? " " + p.fin : "");
      cuenta.textContent = "Paso " + (i + 1) + " de " + sim.pasos.length;
      $(".sim-ini", box).disabled = $(".sim-ant", box).disabled = i === 0;
      $(".sim-sig", box).disabled = $(".sim-fin", box).disabled = i === sim.pasos.length - 1;
    }
    function ir(n) { i = Math.max(0, Math.min(sim.pasos.length - 1, n)); pintarPaso(); }
    function reproducir() {
      if (timer) { parar(); return; }
      if (i >= sim.pasos.length - 1) ir(0);
      play.textContent = "❚❚ Pausar";
      timer = setInterval(function () {
        if (i >= sim.pasos.length - 1) { parar(); return; }
        ir(i + 1);
      }, 900);
    }
    function cargar() {
      parar();
      texto.textContent = "Calculando…";
      fetch("/api/simular", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: box.dataset.token, automata: box.dataset.tipo, cadena: cadena.value })
      }).then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
        .then(function (x) {
          if (!x.ok) throw new Error(x.j.error || "No se pudo simular.");
          sim = x.j; sim.cadena = cadena.value;
          ctl.hidden = false;
          ir(0);
        }).catch(function (e) { texto.textContent = e.message; texto.className = "sim-texto fallo"; });
    }
    $(".sim-iniciar", box).addEventListener("click", cargar);
    cadena.addEventListener("keydown", function (e) { if (e.key === "Enter") cargar(); });
    $(".sim-ini", box).addEventListener("click", function () { parar(); ir(0); });
    $(".sim-ant", box).addEventListener("click", function () { parar(); ir(i - 1); });
    $(".sim-sig", box).addEventListener("click", function () { parar(); ir(i + 1); });
    $(".sim-fin", box).addEventListener("click", function () { parar(); ir(sim.pasos.length - 1); });
    play.addEventListener("click", reproducir);
  }
  $$(".simulador").forEach(iniciarSim);

  /* ---------- Entrada ---------- */
  var area = $("#codigo");
  function leerArchivo(f) {
    if (!f) return;
    if (f.size > 2 * 1024 * 1024) { msg("El archivo supera los 2 MB permitidos.", "error"); return; }
    var r = new FileReader();
    r.onload = function () {
      area.value = String(r.result);
      $("#nombre-archivo").textContent = f.name + " · " + Math.max(1, Math.round(f.size / 1024)) + " KB";
      msg("Archivo cargado. Pulsa Compilar.", "ok");
    };
    r.onerror = function () { msg("No se pudo leer el archivo.", "error"); };
    r.readAsText(f, "utf-8");
  }
  $("#archivo").addEventListener("change", function (e) { leerArchivo(e.target.files[0]); });
  var zona = $("#zona-carga");
  ["dragenter", "dragover"].forEach(function (ev) {
    zona.addEventListener(ev, function (e) { e.preventDefault(); zona.classList.add("arrastre"); });
  });
  ["dragleave", "drop"].forEach(function (ev) {
    zona.addEventListener(ev, function (e) { e.preventDefault(); zona.classList.remove("arrastre"); });
  });
  zona.addEventListener("drop", function (e) { leerArchivo(e.dataTransfer.files[0]); });

  $$("[data-ejemplo]").forEach(function (b) {
    b.addEventListener("click", function () {
      var nombre = b.dataset.ejemplo;
      msg("Cargando " + nombre + "…");
      fetch("/static/ejemplos/" + nombre).then(function (r) {
        if (!r.ok) throw new Error();
        return r.text();
      }).then(function (t) {
        area.value = t;
        $("#nombre-archivo").textContent = nombre;
        compilar();
      }).catch(function () { msg("No se pudo cargar el ejemplo.", "error"); });
    });
  });
  $("#limpiar").addEventListener("click", function () {
    area.value = "";
    $("#nombre-archivo").textContent = "Arrastra el archivo aquí o haz clic para elegirlo";
    $("#archivo").value = "";
    $("#resultados").hidden = true;
    $("#vacio").hidden = false;
    estado.data = null;
    msg("");
  });

  /* ---------- Compilar ---------- */
  function compilar() {
    var btn = $("#compilar");
    btn.disabled = true;
    msg("Compilando…");
    fetch("/api/analizar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto: area.value })
    }).then(function (r) {
      return r.json().then(function (j) { return { ok: r.ok, j: j }; });
    }).then(function (x) {
      if (!x.ok) throw new Error(x.j.error || "Error al compilar.");
      estado.data = x.j;
      estado.filtro = "todas"; estado.q = ""; estado.pag = 1;
      $("#buscar-trama").value = "";
      $$(".chip").forEach(function (c) { c.classList.toggle("activo", c.dataset.filtro === "todas"); });
      pintar();
      var r = x.j.resumen;
      msg("Listo: " + r.total + " tramas analizadas, " + r.validas + " válidas y " + r.con_error + " con error.", "ok");
      document.getElementById("resultado").scrollIntoView({ behavior: "smooth" });
    }).catch(function (e) {
      msg(e.message || "No se pudo compilar.", "error");
    }).then(function () { btn.disabled = false; });
  }
  $("#compilar").addEventListener("click", compilar);

  /* ---------- Pintar resultados ---------- */
  function pintar() {
    var d = estado.data;
    if (!d) return;
    $("#vacio").hidden = true;
    $("#resultados").hidden = false;
    var r = d.resumen;
    $("#datos").innerHTML =
      '<div class="dato"><strong>' + r.total + '</strong><span>Tramas</span></div>' +
      '<div class="dato bien"><strong>' + r.validas + '</strong><span>Válidas</span></div>' +
      '<div class="dato mal"><strong>' + r.con_error + '</strong><span>Con error</span></div>' +
      '<div class="dato"><strong>' + r.tokens_reconocidos + '</strong><span>Tokens reconocidos</span></div>';

    var pt = r.por_token || {};
    var nombres = Array.isArray(pt) ? pt.map(function (x) { return x.token; }) : Object.keys(pt);
    $("#por-token").innerHTML = nombres.map(function (n) {
      var v = Array.isArray(pt) ? pt.filter(function (x) { return x.token === n; })[0] : pt[n];
      var ok = typeof v === "number" ? v : (v.ok || v.validos || 0);
      var mal = typeof v === "number" ? 0 : (v.error != null ? v.error : (v.errores || 0));
      var tot = ok + mal || 1;
      return '<div class="pt"><b>' + esc(n) + '</b><div class="barra-pt"><i style="width:' + Math.round(ok * 100 / tot) + '%"></i></div>' +
        '<small>' + ok + ' correctos' + (mal ? ', ' + mal + ' con error' : '') + '</small></div>';
    }).join("");
    pintarLista();
  }

  function filtradas() {
    var q = estado.q.toLowerCase();
    return estado.data.tramas.filter(function (t) {
      if (estado.filtro === "validas" && !t.ok) return false;
      if (estado.filtro === "errores" && t.ok) return false;
      if (!q) return true;
      var s = t.resumen || {};
      return ((s.codigo || "") + " " + (s.comprador || "") + " " + (s.distrito || "") + " " + t.raw).toLowerCase().indexOf(q) >= 0;
    });
  }

  function campoDe(token) {
    for (var i = 0; i < CAMPOS.length; i++) if (CAMPOS[i].tokens.indexOf(token) >= 0) return i;
    return -1;
  }

  function rawColoreado(t) {
    var malos = {};
    t.tokens.forEach(function (k) { if (!k.ok) { var c = campoDe(k.token); if (c >= 0) malos[c] = true; } });
    var partes = t.raw.split("|");
    return partes.map(function (p, i) {
      var cls = malos[i] ? "cx" : (i < 9 ? "c" + i : "cx");
      return '<span class="' + cls + '">' + esc(p) + "</span>";
    }).join("<b>|</b>");
  }

  /* ---------- Árbol sintáctico ---------- */
  var GRAMATICA = [
    "LOTE      → TRAMA RESTO",
    "RESTO     → salto TRAMA RESTO | ε",
    "TRAMA     → ENVIO | COMPRADOR | DIRECCION | ENTREGA",
    "ENVIO     → CODIGO_ENVIO",
    "COMPRADOR → NOMBRE | DNI | TELEFONO | CORREO",
    "DIRECCION → VIA | INTERIOR | UBIGEO",
    "VIA       → TIPO_VIA * NOMBRE_VIA NUMERO",
    "ENTREGA   → FECHA"
  ].join("\n");

  function arbolDe(t) {
    var tk = {};
    t.tokens.forEach(function (k) { tk[k.token] = k; });
    function tok(nombre) {
      var k = tk[nombre] || { lexema: "", ok: false, error: "Falta este campo." };
      return { tipo: "tok", label: nombre, lex: k.lexema || "(falta)", ok: !!k.ok, error: k.error || "" };
    }
    function nt(label, hijos) { return { tipo: "nt", label: label, hijos: hijos }; }
    function term(sim, fondo) { return { tipo: "term", label: sim, fondo: !!fondo, ok: true }; }
    var trama = [
      nt("ENVIO", [tok("CODIGO_ENVIO")]), term("|"),
      nt("COMPRADOR", [tok("NOMBRE"), term("|", 1), tok("DNI"), term("|", 1), tok("TELEFONO"), term("|", 1), tok("CORREO")]), term("|"),
      nt("DIRECCION", [nt("VIA", [tok("TIPO_VIA"), term("*", 1), tok("NOMBRE_VIA"), tok("NUMERO")]),
        term("|", 1), tok("INTERIOR"), term("|", 1), tok("UBIGEO")]), term("|"),
      nt("ENTREGA", [tok("FECHA")])
    ];
    var sobra = t.tokens.filter(function (k) { return k.token === "SOBRANTE"; })[0];
    if (sobra) trama.push({ tipo: "tok", label: "SOBRANTE", lex: sobra.lexema, ok: false, error: sobra.error });
    return nt("LOTE", [nt("TRAMA", trama), nt("RESTO", [{ tipo: "eps", label: "ε", ok: true }])]);
  }

  var K_TOKEN = { CODIGO_ENVIO: 0, NOMBRE: 1, DNI: 2, TELEFONO: 3, CORREO: 4, TIPO_VIA: 5, NOMBRE_VIA: 5, NUMERO: 5,
                  INTERIOR: 6, UBIGEO: 7, FECHA: 8 };
  var K_GRUPO = { ENVIO: 0, COMPRADOR: 1, DIRECCION: 5, VIA: 5, ENTREGA: 8 };

  function arbolSVG(t) {
    var raiz = arbolDe(t), cursor = 24, FONDO = 4, DY = 72, nodos = [];
    function ancho(n) { return n.tipo === "tok" ? 118 : n.tipo === "eps" ? 46 : 34; }
    function colocar(n, d) {
      n.d = d; nodos.push(n);
      if (!n.hijos) { n.x = cursor + ancho(n) / 2; cursor += ancho(n); return; }
      n.hijos.forEach(function (h) { colocar(h, d + 1); });
      n.x = (n.hijos[0].x + n.hijos[n.hijos.length - 1].x) / 2;
      n.ok = n.hijos.every(function (h) { return h.ok; });
    }
    colocar(raiz, 0);
    var LIN = 14, maxLin = 1, YB = 40 + FONDO * DY;
    nodos.forEach(function (n) {
      n.y = (n.tipo === "tok" || n.fondo) ? YB : 40 + n.d * DY;
      if (n.tipo === "tok") {
        var l = []; for (var i = 0; i < n.lex.length; i += 14) l.push(n.lex.slice(i, i + 14));
        if (l.length > 4) { l = l.slice(0, 4); l[3] = l[3].slice(0, 13) + "…"; }
        n.lineas = l; maxLin = Math.max(maxLin, l.length);
      }
    });
    var W = cursor + 24, H = YB + 40 + maxLin * LIN + 16;
    var defs = '<defs><linearGradient id="ar-grad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a1707b"/>' +
      '<stop offset="1" stop-color="#5d3647"/></linearGradient>' +
      '<filter id="ar-sombra" x="-20%" y="-30%" width="140%" height="180%"><feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#5d3647" flood-opacity=".28"/></filter></defs>';
    var aristas = "", cajas = "";
    nodos.forEach(function (n) {
      if (!n.hijos) return;
      n.hijos.forEach(function (h) {
        var y1 = n.y + 15, y2 = h.y - 14, m = (y1 + y2) / 2;
        aristas += '<path class="ar-linea" d="M' + n.x.toFixed(1) + " " + y1 + " C" + n.x.toFixed(1) + " " + m + " " + h.x.toFixed(1) + " " + m + " " + h.x.toFixed(1) + " " + y2 + '"/>';
      });
    });
    nodos.forEach(function (n) {
      var x = n.x.toFixed(1), y = n.y;
      if (n.tipo === "nt") {
        var w = n.label.length * 9 + 30;
        var cls = n.label === "LOTE" || n.label === "TRAMA" ? "ar-raiz" : n.label === "RESTO" ? "ar-resto" :
          "ar-grupo k" + K_GRUPO[n.label] + (n.label === "VIA" ? " sub" : "");
        cajas += '<g class="ar-nt ' + cls + (n.ok ? "" : " mal") + '"><rect x="' + (n.x - w / 2).toFixed(1) + '" y="' + (y - 15) + '" width="' + w.toFixed(1) +
          '" height="30" rx="15"/><text x="' + x + '" y="' + (y + 4.5) + '">' + esc(n.label) + "</text></g>";
      } else if (n.tipo === "tok") {
        var k = K_TOKEN[n.label];
        var alto = n.lineas.length * LIN + 10;
        cajas += '<g class="ar-tok' + (k != null ? " k" + k : "") + (n.ok ? "" : " mal") + '"><title>' + esc(n.label + (n.error ? ": " + n.error : "")) +
          '</title><rect class="ar-caja" x="' + (n.x - 54).toFixed(1) + '" y="' + (y - 14) + '" width="108" height="28" rx="9"/>' +
          '<text class="ar-et" x="' + x + '" y="' + (y + 4) + '">' + esc(n.label) + "</text>" +
          '<rect class="ar-lexbox" x="' + (n.x - 54).toFixed(1) + '" y="' + (y + 22) + '" width="108" height="' + alto + '" rx="8"/>';
        n.lineas.forEach(function (l, i) {
          cajas += '<text class="ar-lex" x="' + x + '" y="' + (y + 22 + 15 + i * LIN) + '">' + esc(l) + "</text>";
        });
        cajas += "</g>";
      } else if (n.tipo === "term") {
        cajas += '<g class="ar-term"><circle cx="' + x + '" cy="' + y + '" r="13"/><text x="' + x + '" y="' + (y + 5) + '">' + esc(n.label) + "</text></g>";
      } else {
        cajas += '<g class="ar-eps"><circle cx="' + x + '" cy="' + y + '" r="15"/><text x="' + x + '" y="' + (y + 5) + '">ε</text></g>';
      }
    });
    return '<svg class="arbolsvg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + W + " " + H + '" width="' + W + '" height="' + H +
      '" role="img" aria-label="Árbol sintáctico de la trama ' + t.n + '">' + defs + aristas + cajas + "</svg>";
  }

  function arbolCaja(t) {
    return '<details class="arbol-caja" data-n="' + t.n + '"><summary>Ver árbol sintáctico</summary>' +
      '<button type="button" class="boton suave arbol-ajustar">Ajustar al ancho</button>' +
      '<div class="lienzo arbol"></div>' +
      '<p class="nota">Desliza horizontalmente si el árbol no cabe. Los nodos en rojo marcan dónde falló el análisis léxico.</p>' +
      '<details class="gramatica"><summary>Ver gramática</summary><pre>' + esc(GRAMATICA) + "</pre></details></details>";
  }

  function detalle(t) {
    var filas = t.tokens.map(function (k) {
      return '<tr class="' + (k.ok ? "" : "fallo") + '"><td>' + esc(k.token) + "</td><td><code>" + esc(k.lexema) + "</code></td>" +
        "<td>" + esc(k.valor == null ? "" : k.valor) + "</td><td>" +
        (k.ok ? '<span class="estado-ok">Aceptado</span>' : '<span class="estado-mal">Rechazado</span><span class="err">' + esc(k.error) + "</span>") +
        "</td></tr>";
    }).join("");
    return '<div class="detalle"><p class="raw">' + rawColoreado(t) + "</p>" +
      '<div class="tabla-simple"><table><thead><tr><th>Token</th><th>Lexema</th><th>Valor</th><th>Estado</th></tr></thead><tbody>' +
      filas + "</tbody></table></div>" + arbolCaja(t) + "</div>";
  }

  function pintarLista() {
    var lista = filtradas();
    var paginas = Math.max(1, Math.ceil(lista.length / PAGINA));
    if (estado.pag > paginas) estado.pag = paginas;
    var ini = (estado.pag - 1) * PAGINA;
    var cont = $("#lista-tramas");
    if (!lista.length) {
      cont.innerHTML = '<div class="vacio"><p>Ninguna trama coincide con el filtro.</p></div>';
    } else {
      cont.innerHTML = lista.slice(ini, ini + PAGINA).map(function (t) {
        var s = t.resumen || {};
        return '<details class="trama"><summary><span class="num">#' + t.n + '</span><span class="codigo">' + esc(s.codigo || "(sin código)") +
          '</span><span class="ell">' + esc(s.comprador || "") + '</span><span class="ell">' + esc(s.distrito || "") +
          '</span><span class="sello ' + (t.ok ? "ok" : "error") + '">' + (t.ok ? "VÁLIDA" : "ERROR") + "</span></summary>" + detalle(t) + "</details>";
      }).join("");
    }
    var p = $("#paginador");
    if (paginas <= 1) { p.innerHTML = ""; return; }
    var h = '<button type="button" data-p="' + (estado.pag - 1) + '"' + (estado.pag === 1 ? " disabled" : "") + '>‹</button>';
    for (var i = 1; i <= paginas; i++) {
      if (i === 1 || i === paginas || Math.abs(i - estado.pag) <= 1) {
        h += '<button type="button" data-p="' + i + '" class="' + (i === estado.pag ? "activo" : "") + '">' + i + "</button>";
      } else if (Math.abs(i - estado.pag) === 2) h += "<span>…</span>";
    }
    h += '<button type="button" data-p="' + (estado.pag + 1) + '"' + (estado.pag === paginas ? " disabled" : "") + '>›</button>';
    h += "<span>" + lista.length + " tramas</span>";
    p.innerHTML = h;
  }
  $("#paginador").addEventListener("click", function (e) {
    var b = e.target.closest("button[data-p]");
    if (!b || b.disabled) return;
    estado.pag = parseInt(b.dataset.p, 10);
    pintarLista();
    $("#lista-tramas").scrollIntoView({ behavior: "smooth", block: "start" });
  });
  $$(".chip").forEach(function (c) {
    c.addEventListener("click", function () {
      estado.filtro = c.dataset.filtro; estado.pag = 1;
      $$(".chip").forEach(function (o) { o.classList.toggle("activo", o === c); });
      pintarLista();
    });
  });
  $("#buscar-trama").addEventListener("input", function (e) { estado.q = e.target.value.trim(); estado.pag = 1; pintarLista(); });

  $("#lista-tramas").addEventListener("toggle", function (e) {
    var d = e.target;
    if (!d.classList || !d.classList.contains("arbol-caja") || !d.open) return;
    var cont = $(".arbol", d);
    if (cont.firstChild) return;
    var n = parseInt(d.dataset.n, 10);
    var t = estado.data.tramas.filter(function (x) { return x.n === n; })[0];
    if (t) cont.innerHTML = arbolSVG(t);
  }, true);

  $("#lista-tramas").addEventListener("click", function (e) {
    var bt = e.target.closest(".arbol-ajustar");
    if (!bt) return;
    var lienzo = $(".arbol", bt.parentNode);
    var aj = lienzo.classList.toggle("ajustado");
    bt.textContent = aj ? "Tamaño real" : "Ajustar al ancho";
  });

  /* ---------- CSV ---------- */
  $("#csv").addEventListener("click", function () {
    if (!estado.data) return;
    var cab = ["trama", "estado"].concat(CAMPOS.length ? [] : []);
    var tokens = [];
    estado.data.tramas.forEach(function (t) { t.tokens.forEach(function (k) { if (tokens.indexOf(k.token) < 0) tokens.push(k.token); }); });
    var celda = function (v) { v = String(v == null ? "" : v); return /[",\n;]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var filas = [cab.concat(tokens).map(celda).join(",")];
    estado.data.tramas.forEach(function (t) {
      var m = {};
      t.tokens.forEach(function (k) { m[k.token] = k.lexema + (k.ok ? "" : " (ERROR)"); });
      filas.push([t.n, t.ok ? "VALIDA" : "ERROR"].concat(tokens.map(function (n) { return m[n] || ""; })).map(celda).join(","));
    });
    var blob = new Blob(["﻿" + filas.join("\r\n")], { type: "text/csv;charset=utf-8" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "tokens_lexemas.csv";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
  });
})();
