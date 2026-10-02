// Money Pal · Revisar categorías. Todo el texto que viene de tus correos se inserta como texto
// (textContent), nunca como HTML: un comercio con "<script>" en el nombre se ve tal cual.
"use strict";

// El token llega después de "#" y se guarda solo para esta pestaña: recargar funciona, cerrarla lo olvida
const TOKEN = (() => {
  const t = new URLSearchParams(location.hash.slice(1)).get("t");
  try {
    if (t) sessionStorage.setItem("token", t);
    return t || sessionStorage.getItem("token") || "";
  } catch {
    return t || "";
  }
})();
const PESTANAS = [
  ["pendiente", "Pendientes"],
  ["sin_categoria", "Sin categoría"],
  ["por_revisar", "Por revisar"],
  ["revisado", "Revisados"],
  ["todos", "Todos"],
];
const AGRUPADAS = new Set(["sin_categoria", "por_revisar"]);
const ORIGEN = { comercio: "por comercio", regla: "por regla", manual: "solo este", asignada: "asignada" };
const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const PASO = 150;

let datos = null;
let pestana = null;
let limite = PASO;
const abiertos = new Set();
const $ = (id) => document.getElementById(id);

// --- Utilidades ---

function el(tag, props = {}, ...hijos) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else if (k in n && typeof v !== "string") n[k] = v;
    else n.setAttribute(k, v === true ? "" : v);
  }
  for (const h of hijos.flat()) if (h !== null && h !== undefined) n.append(h);
  return n;
}

const formato = new Intl.NumberFormat("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const monto = (m, moneda) => (moneda === "USD" ? "US$ " : "S/ ") + formato.format(m);
const fecha = (f) => `${+f.slice(8, 10)} ${MESES[+f.slice(5, 7) - 1]} ${f.slice(0, 4)}`;
const nombreMes = (m) => `${MESES[+m.slice(5, 7) - 1]} ${m.slice(0, 4)}`;
const nombreCategoria = (id) => (datos.categorias.find((c) => c.id === id) || {}).nombre || "Sin categoría";

function totales(movs) {
  const t = {};
  for (const m of movs) t[m.moneda] = (t[m.moneda] || 0) + m.monto;
  return Object.entries(t).map(([moneda, v]) => monto(v, moneda)).join(" · ");
}

let temporizador = null;
function avisar(texto, { error = false, botones = [] } = {}) {
  const a = $("aviso");
  a.replaceChildren(el("span", { text: texto }), ...botones.map(([t, f]) => el("button", {
    type: "button", class: "chico", text: t, onclick: () => { a.hidden = true; f(); },
  })));
  a.className = error ? "error" : "";
  a.hidden = false;
  clearTimeout(temporizador);
  temporizador = setTimeout(() => (a.hidden = true), botones.length ? 9000 : 4000);
}

// --- Servidor ---

async function api(ruta, cuerpo) {
  const r = await fetch(ruta, {
    method: cuerpo ? "POST" : "GET",
    headers: { "X-Token": TOKEN, ...(cuerpo ? { "Content-Type": "application/json" } : {}) },
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  });
  const json = await r.json().catch(() => ({ error: "Respuesta inválida" }));
  if (r.status === 409) {
    avisar(json.error, { error: true });
    await cargar();
    throw new Error(json.error);
  }
  if (!r.ok) {
    avisar(json.error || `Error ${r.status}`, { error: true });
    throw new Error(json.error);
  }
  return json;
}

async function cargar() {
  datos = await api("/api/datos");
  dibujar();
}

async function accion(cuerpo) {
  const r = await api("/api/accion", { version: datos.version, ...cuerpo });
  datos = r;
  dibujar();
  return r.cambiados;
}

async function deshacer() {
  datos = await api("/api/deshacer", { version: datos.version });
  dibujar();
  avisar("Cambio deshecho");
}

// --- Acciones ---

async function cambiarCategoria(t, categoria) {
  const antes = nombreCategoria(t.categoria);
  const n = await accion({ accion: "categoria", id: t.id, categoria });
  const botones = [["Deshacer", deshacer]];
  if (n > 1) {
    botones.unshift(["Solo este movimiento", async () => {
      await deshacer();
      await accion({ accion: "categoria", id: t.id, categoria, solo_este: true });
      avisar(`${t.comercio}: solo este movimiento pasó a ${nombreCategoria(categoria)}`, { botones: [["Deshacer", deshacer]] });
    }]);
  }
  avisar(`${t.comercio}: ${antes} → ${nombreCategoria(categoria)}` +
    (n > 1 ? ` en ${n} movimientos (y los futuros)` : " (y los futuros)"), { botones });
}

async function aprobarIds(ids, texto) {
  const n = await accion({ accion: "aprobar", ids });
  avisar(`${texto || "Aprobados"}: ${n}`, { botones: [["Deshacer", deshacer]] });
}

async function contarComoGasto(t, esGasto) {
  await accion({ accion: "gasto", id: t.id, es_gasto: esGasto });
  avisar(`${t.comercio}: ${esGasto ? "cuenta como gasto" : "no cuenta como gasto"}`, { botones: [["Deshacer", deshacer]] });
}

async function guardarNota(t, input) {
  if ((t.nota || "") === input.value.trim()) return;
  await accion({ accion: "nota", id: t.id, nota: input.value });
  avisar("Nota guardada");
}

// --- Dibujo ---

function filtrados() {
  const texto = $("buscar").value.trim().toLowerCase();
  const mes = $("f-mes").value, banco = $("f-banco").value, cat = $("f-categoria").value;
  return datos.transacciones.filter((t) =>
    (pestana === "todos" || t.estado === pestana) &&
    (!mes || t.fecha.startsWith(mes)) &&
    (!banco || t.banco === banco) &&
    (!cat || (cat === "__ninguna__" ? !t.categoria : t.categoria === cat)) &&
    (!texto || t.comercio.toLowerCase().includes(texto) || (t.nota || "").toLowerCase().includes(texto)));
}

function selectorCategoria(valor, alCambiar, deshabilitado) {
  const s = el("select", { "aria-label": "Categoría", disabled: deshabilitado },
    el("option", { value: "", text: valor === null ? "Elige categoría…" : "(varias)", disabled: true }),
    datos.categorias.map((c) => el("option", { value: c.id, text: c.nombre })));
  s.value = valor || "";
  s.addEventListener("change", () => alCambiar(s.value));
  return s;
}

function botonesFila(t) {
  switch (t.estado) {
    case "pendiente":
      return [el("button", { type: "button", class: "chico principal", text: "Cuenta como gasto", onclick: () => contarComoGasto(t, true) }), " ",
        el("button", { type: "button", class: "chico", text: "No cuenta", onclick: () => contarComoGasto(t, false) })];
    case "por_revisar":
      return [el("button", { type: "button", class: "chico", text: "✓ Aprobar", title: "Aprobar", onclick: () => aprobarIds([t.id], "Aprobado") })];
    case "revisado":
      return [el("span", { class: "ok", text: "✓", title: "Revisado" })];
    case "excluida":
      return [el("button", { type: "button", class: "chico", text: "Incluir", title: "Contar como gasto", onclick: () => contarComoGasto(t, true) })];
    default:
      return [];
  }
}

function fila(t, conComercio) {
  const nota = el("input", { class: "nota", type: "text", maxLength: 200, placeholder: "Nota", value: t.nota || "", "aria-label": "Nota" });
  nota.addEventListener("change", () => guardarNota(t, nota));
  nota.addEventListener("keydown", (e) => e.key === "Enter" && nota.blur());
  return el("tr", { class: t.estado === "excluida" ? "excluida" : null },
    el("td", { class: "fecha", text: fecha(t.fecha) }),
    conComercio ? el("td", { class: "comercio", text: t.comercio }) : null,
    el("td", { class: "monto", text: monto(t.monto, t.moneda) }),
    el("td", { class: "ocultable", text: t.banco || "" }),
    el("td", {},
      selectorCategoria(t.categoria, (c) => cambiarCategoria(t, c), t.estado === "excluida" || t.estado === "pendiente"),
      t.origen ? [" ", el("span", { class: `origen ${t.origen}`, text: ORIGEN[t.origen] })] : null),
    el("td", { class: "ocultable" }, nota),
    el("td", {}, botonesFila(t)));
}

function grupos(movs) {
  const porComercio = new Map();
  for (const t of movs) {
    if (!porComercio.has(t.comercio)) porComercio.set(t.comercio, []);
    porComercio.get(t.comercio).push(t);
  }
  const soles = (ms) => ms.reduce((s, t) => s + t.monto * (t.moneda === "USD" ? 3.5 : 1), 0);
  const lista = [...porComercio.entries()].sort((a, b) => soles(b[1]) - soles(a[1]));

  return lista.slice(0, limite).map(([comercio, ms]) => {
    const cats = new Set(ms.map((t) => t.categoria));
    const valor = cats.size === 1 ? [...cats][0] : (cats.has(null) ? null : "");
    const abierto = abiertos.has(comercio);
    return el("div", { class: "grupo" },
      el("div", { class: "cabeza" },
        el("div", { class: "nombre" }, comercio, el("div", { class: "detalle",
          text: `${ms.length} movimiento${ms.length > 1 ? "s" : ""} · ${totales(ms)}` })),
        selectorCategoria(valor, (c) => cambiarCategoria(ms[0], c)),
        pestana === "por_revisar" ? el("button", { type: "button", class: "principal",
          text: `✓ Aprobar ${ms.length}`, onclick: () => aprobarIds(ms.map((t) => t.id), `${comercio} aprobado`) }) : null,
        el("button", { type: "button", text: abierto ? "Ocultar" : "Ver", "aria-expanded": String(abierto), onclick: () => {
          abierto ? abiertos.delete(comercio) : abiertos.add(comercio);
          dibujar();
        } })),
      abierto ? el("div", { class: "filas" }, el("table", {}, el("tbody", {}, ms.map((t) => fila(t, false))))) : null);
  }).concat(lista.length > limite ? [masBoton(lista.length)] : []);
}

function masBoton(total) {
  return el("button", { type: "button", class: "mas", text: `Ver más (${total - limite} más)`, onclick: () => { limite += PASO; dibujar(); } });
}

function dibujarPestanas() {
  $("pestanas").replaceChildren(...PESTANAS.map(([id, nombre]) => {
    const n = id === "todos" ? datos.transacciones.length : datos.conteos[id];
    return el("button", { type: "button", role: "tab", "aria-selected": String(id === pestana),
      onclick: () => { pestana = id; limite = PASO; dibujar(); } },
      nombre, el("span", { class: "cuenta", text: String(n) }));
  }));
}

function llenarSelect(s, opciones, primera) {
  const valor = s.value;
  s.replaceChildren(el("option", { value: "", text: primera }), ...opciones.map(([v, t]) => el("option", { value: v, text: t })));
  s.value = opciones.some(([v]) => v === valor) ? valor : "";
}

function dibujarFiltros() {
  const meses = [...new Set(datos.transacciones.map((t) => t.fecha.slice(0, 7)))].sort().reverse();
  llenarSelect($("f-mes"), meses.map((m) => [m, nombreMes(m)]), "Todos los meses");
  llenarSelect($("f-banco"), datos.bancos.map((b) => [b, b.toUpperCase()]), "Todos los bancos");
  llenarSelect($("f-categoria"), [...datos.categorias.map((c) => [c.id, c.nombre]), ["__ninguna__", "Sin categoría"]], "Todas las categorías");

  const sel = $("mes-reporte");
  if (!sel.options.length) {
    const hoy = new Date();
    const anterior = new Date(hoy.getFullYear(), hoy.getMonth() - 1, 1);
    const pordefecto = `${anterior.getFullYear()}-${String(anterior.getMonth() + 1).padStart(2, "0")}`;
    sel.replaceChildren(...meses.map((m) => el("option", { value: m, text: `Cierre de ${nombreMes(m)}` })));
    if (meses.includes(pordefecto)) sel.value = pordefecto;
  }
}

function dibujar() {
  if (!pestana) pestana = datos.conteos.pendiente ? "pendiente" : datos.conteos.sin_categoria ? "sin_categoria" : "por_revisar";
  dibujarPestanas();
  dibujarFiltros();
  $("deshacer").disabled = !datos.puede_deshacer;

  const movs = filtrados();
  const aprobables = movs.filter((t) => t.estado === "por_revisar");
  const boton = $("aprobar-visibles");
  boton.hidden = pestana !== "por_revisar" || !aprobables.length;
  boton.textContent = `✓ Aprobar los ${aprobables.length} visibles`;
  boton.dataset.confirmar = "";

  const main = $("contenido");
  if (!movs.length) {
    const vacio = { pendiente: "No hay pendientes.", sin_categoria: "Todo tiene categoría.", por_revisar: "Nada por revisar. ✓" };
    main.replaceChildren(el("p", { class: "vacio", text: vacio[pestana] || "No hay movimientos con estos filtros." }));
    return;
  }
  if (AGRUPADAS.has(pestana)) {
    main.replaceChildren(...grupos(movs));
  } else {
    main.replaceChildren(el("div", { class: "lista" }, el("table", {}, el("tbody", {}, movs.slice(0, limite).map((t) => fila(t, true))))),
      ...(movs.length > limite ? [masBoton(movs.length)] : []));
  }
}

// --- Inicio ---

$("aprobar-visibles").addEventListener("click", (e) => {
  const b = e.currentTarget;
  const ids = filtrados().filter((t) => t.estado === "por_revisar").map((t) => t.id);
  if (!b.dataset.confirmar) {  // dos pasos en vez de un diálogo: aprobar en bloque no se hace por accidente
    b.dataset.confirmar = "1";
    b.textContent = `¿Seguro? Aprobar ${ids.length}`;
    setTimeout(() => { if (b.dataset.confirmar) { b.dataset.confirmar = ""; b.textContent = `✓ Aprobar los ${ids.length} visibles`; } }, 4000);
    return;
  }
  aprobarIds(ids, "Aprobados");
});
$("deshacer").addEventListener("click", deshacer);
$("reporte").addEventListener("click", async (e) => {
  const b = e.currentTarget, mes = $("mes-reporte").value;
  b.disabled = true;
  b.textContent = "Generando…";
  try {
    const r = await api("/api/reporte", { mes });
    avisar(`Reporte de ${nombreMes(mes)} listo en output/: ${r.archivos.join(", ")}`);
  } finally {
    b.disabled = false;
    b.textContent = "Regenerar reporte";
  }
});
for (const id of ["buscar", "f-mes", "f-banco", "f-categoria"]) {
  $(id).addEventListener("input", () => { limite = PASO; dibujar(); });
}

if (!TOKEN) {
  $("contenido").replaceChildren(el("p", { class: "vacio", text: "Abre esta página con scripts/revisar.sh." }));
} else {
  history.replaceState(null, "", location.pathname);  // quita el token de la barra de direcciones
  cargar().catch(() => {});
}
