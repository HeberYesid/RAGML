import { createChatClient, ChatFailure } from "./chat-client.mjs";

const $ = id => document.getElementById(id);
const client = createChatClient();
const form = $("chat-form");
const input = $("message");
let catalog = null;
let busy = false;
let view = 0;
let turnNumber = 0;

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function draftChanged() {
  $("char-count").textContent = `${[...input.value].length} / 4000`;
  input.setCustomValidity("");
  input.removeAttribute("aria-invalid");
  $("input-error").hidden = true;
}

function setBusy(value) {
  busy = value;
  input.readOnly = value;
  $("send").disabled = value;
  $("pending").hidden = !value;
  $("transcript").setAttribute("aria-busy", String(value));
  document.querySelectorAll(".starter, .category").forEach(button => { button.disabled = value; });
}

function choosePrompt(text) {
  if (busy) return;
  input.value = text;
  draftChanged();
  input.focus();
  input.scrollIntoView({ block: "nearest" });
}

function renderCatalog(data) {
  catalog = data;
  const profile = data.profile;
  $("store-name").textContent = profile.display_name;
  document.title = `Asistente | ${profile.display_name}`;
  $("data-mode").textContent = profile.data_mode === "demo" ? "Datos ficticios" : "Datos reales";
  $("data-notice").textContent = profile.data_mode === "demo"
    ? "Tienda de demostración. El catálogo y sus datos son ficticios; no se realizan compras."
    : "Catálogo de la tienda configurada. Comprueba las fuentes y la vigencia de los datos comerciales.";
  $("product-count").textContent = `${data.products.length} productos`;
  $("categories").replaceChildren();
  for (const category of profile.categories) {
    const count = data.products.filter(product => product.category_id === category.category_id).length;
    const button = node("button", undefined, "category");
    button.type = "button";
    const icon = node("span", "◇", "category-icon");
    icon.setAttribute("aria-hidden", "true");
    button.append(icon, node("span", category.name, "category-name"), node("span", String(count), "category-count"));
    button.addEventListener("click", () => choosePrompt(`¿Qué información tienes sobre ${category.name.toLocaleLowerCase("es")}?`));
    button.disabled = busy;
    $("categories").append(button);
  }
  $("catalog-message").hidden = true;
}

async function checkConnection() {
  $("check-connection").disabled = true;
  try {
    const response = await fetch("/ready", { cache: "no-store", signal: AbortSignal.timeout(10000) });
    $("connection-status").textContent = response.ok ? "Asistente local disponible" : "Asistente requiere preparación";
  } catch {
    $("connection-status").textContent = "API sin conexión";
  } finally {
    $("check-connection").disabled = false;
  }
}

function renderTurn(role, text) {
  $("welcome").hidden = true;
  $("transcript").hidden = false;
  const turn = node("article", undefined, `turn ${role}`);
  turn.append(node("h2", role === "user" ? "Tú" : "Asistente", "turn-label"), node("p", text, "turn-text"));
  $("transcript").append(turn);
  return turn;
}

function sourceLocation(location) {
  return [location.page && `Página ${location.page}`, location.section && `Sección: ${location.section}`,
    location.paragraph && `Párrafo ${location.paragraph}`, location.table && `Tabla: ${location.table}`].filter(Boolean).join(" · ");
}

function renderSources(turn, result, prefix) {
  if (!result.citations.length) return;
  const sources = node("details", undefined, "sources");
  sources.append(node("summary", `Consultar fuentes (${result.citations.length})`));
  const targets = new Map();
  result.citations.forEach((citation, index) => {
    const source = node("div", undefined, "source");
    source.id = `${prefix}-source-${index}`;
    source.tabIndex = -1;
    targets.set(citation.citation_id, source.id);
    source.append(node("p", `[${index + 1}] ${citation.source_id}`), node("p", `Versión: ${citation.source_version}`));
    if (citation.kind === "document") {
      source.append(node("p", sourceLocation(citation.location)), node("blockquote", citation.excerpt));
    } else {
      source.append(node("p", `${citation.field === "price" ? "Precio" : "Existencias"} · Variante: ${citation.variant_id}`));
      const expires = new Date(citation.expires_at);
      source.append(node("p", `Actualización: ${new Date(citation.source_updated_at).toLocaleString("es-CO")}`));
      source.append(node("p", `Vigencia hasta: ${expires.toLocaleString("es-CO")}`));
      const simulated = result.data_mode === "demo" && result.versions?.commercial_clock === "simulated";
      const evaluatedAt = simulated ? new Date(result.versions.commercial_evaluated_at) : new Date();
      if (expires <= evaluatedAt) source.append(node("p", "Dato vencido: requiere una nueva consulta.", "response-warning"));
      if (simulated) source.append(node("p", `Vigencia comprobada en el reloj simulado: ${evaluatedAt.toLocaleString("es-CO")}.`, "muted"));
    }
    sources.append(source);
  });
  for (const claim of result.claims) {
    const group = node("div", undefined, "claim-links");
    group.append(node("span", claim.text));
    claim.citation_ids.forEach(id => {
      const target = targets.get(id);
      if (!target) return;
      const index = result.citations.findIndex(citation => citation.citation_id === id);
      const link = node("a", `[${index + 1}]`);
      link.href = `#${target}`;
      link.setAttribute("aria-label", `Ver fuente ${index + 1} de la afirmación: ${claim.text}`);
      link.addEventListener("click", () => { sources.open = true; $(target).focus(); });
      group.append(link);
    });
    turn.append(group);
  }
  turn.append(sources);
}

function renderProducts(turn, references) {
  if (!references.length) return;
  const list = node("div", undefined, "product-list");
  for (const reference of references) {
    const card = node("section", undefined, "product-card");
    const product = catalog?.products.find(item => item.product_id === reference.product_id);
    const variant = catalog?.variants.find(item => item.variant_id === reference.variant_id && item.product_id === reference.product_id);
    card.append(node("h3", product?.name || reference.product_id));
    card.append(node("p", variant?.name || reference.variant_id));
    if (product && variant) {
      const category = catalog.profile.categories.find(item => item.category_id === product.category_id);
      const values = new Map([...product.attributes, ...variant.attributes].map(item => [item.key, item]));
      const attributes = node("dl");
      for (const attribute of values.values()) {
        const label = category?.attribute_definitions.find(item => item.key === attribute.key)?.label || attribute.key;
        const value = attribute.value === null ? "Sin información" : typeof attribute.value === "boolean" ? (attribute.value ? "Sí" : "No") : String(attribute.value);
        attributes.append(node("dt", label), node("dd", `${value}${attribute.unit && attribute.value !== null ? ` ${attribute.unit}` : ""}`));
      }
      card.append(attributes);
    }
    card.append(node("p", "Ficha del catálogo. Precio y existencias requieren una consulta comercial vigente.", "muted"));
    list.append(card);
  }
  turn.append(list);
}

const responseLabels = {
  answered: "Respuesta con fuentes", clarification_required: "Hace falta una aclaración",
  insufficient_evidence: "Información insuficiente", temporarily_unavailable: "Servicio temporalmente no disponible",
};
const errorMessages = {
  rag_not_ready: "El asistente está en preparación. La interfaz está conectada, pero el servicio RAG todavía no está integrado.",
  provider_unavailable: "El modelo local no está disponible. Comprueba que esté iniciado antes de reintentar.",
  invalid_input: "Escribe una consulta de entre 1 y 4000 caracteres.",
  invalid_response: "El servicio devolvió una respuesta que no se puede mostrar. Tu consulta se conserva.",
  network_error: "No se pudo conectar con el servicio local. Tu consulta se conserva; puedes reintentar.",
  timeout: "La consulta superó el tiempo de espera. Tu texto se conserva. Puedes reintentar cuando el servicio esté disponible.",
  internal_error: "El servicio no pudo completar la consulta. Tu texto se conserva.",
  session_not_found: "La conversación venció o dejó de estar disponible. Reenvía tu consulta para iniciar una nueva.",
};

async function submit(event) {
  event.preventDefault();
  if (busy) return;
  const text = input.value.trim();
  if (!text || [...text].length > 4000) {
    input.setCustomValidity(errorMessages.invalid_input);
    input.reportValidity();
    return;
  }
  const revision = view;
  $("error-banner").hidden = true;
  setBusy(true);
  const userTurn = renderTurn("user", text);
  try {
    const result = await client.send(text);
    if (revision !== view) return;
    if (catalog && result.versions?.catalog_profile && result.versions.catalog_profile !== catalog.profile.revision) {
      const refreshed = await fetch("/v1/web/catalog", { cache: "no-store", signal: AbortSignal.timeout(10000) });
      if (!refreshed.ok) throw new ChatFailure("invalid_response", true);
      const latest = await refreshed.json();
      if (latest.profile.revision !== result.versions.catalog_profile) throw new ChatFailure("invalid_response", true);
      if (revision !== view) return;
      renderCatalog(latest);
    }
    if (catalog && (result.store_id !== catalog.profile.store_id || result.data_mode !== catalog.profile.data_mode)) {
      client.reset();
      throw new ChatFailure("invalid_response");
    }
    const turn = renderTurn("assistant", result.answer);
    turn.append(node("span", responseLabels[result.status], "response-state"));
    if (result.data_mode === "demo") turn.append(node("p", "Respuesta sobre datos ficticios.", "technical"));
    result.warnings.forEach(warning => turn.append(node("p", warning, "response-warning")));
    renderProducts(turn, result.products);
    renderSources(turn, result, `turn-${++turnNumber}`);
    const technical = node("details", undefined, "technical");
    technical.append(node("summary", "Detalles de la consulta"), node("p", `Solicitud: ${result.request_id}`));
    Object.entries(result.versions || {}).forEach(([key, value]) => technical.append(node("p", `${key}: ${value}`)));
    turn.append(technical);
    input.value = "";
    draftChanged();
    turn.scrollIntoView({ block: "nearest" });
  } catch (error) {
    if (revision !== view) return;
    userTurn.remove();
    if (!$("transcript").children.length) { $("transcript").hidden = true; $("welcome").hidden = false; }
    if (error.code !== "cancelled") {
      $("error-text").textContent = errorMessages[error.code] || errorMessages.internal_error;
      $("retry").hidden = error.retryable !== true;
      $("error-banner").hidden = false;
    }
  } finally {
    if (revision === view) { setBusy(false); input.focus(); }
  }
}

form.addEventListener("submit", submit);
input.addEventListener("input", draftChanged);
input.addEventListener("invalid", () => {
  $("input-error").textContent = errorMessages.invalid_input;
  $("input-error").hidden = false;
  input.setAttribute("aria-invalid", "true");
});
input.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) {
    if (event.isComposing || event.keyCode === 229) return;
    event.preventDefault();
    if (!busy) form.requestSubmit();
  }
});
$("retry").addEventListener("click", () => form.requestSubmit());
$("check-connection").addEventListener("click", checkConnection);
$("cancel").addEventListener("click", () => { client.cancel(); });
$("new-session").addEventListener("click", () => {
  view += 1;
  client.reset();
  setBusy(false);
  $("transcript").replaceChildren();
  $("transcript").hidden = true;
  $("welcome").hidden = false;
  $("error-banner").hidden = true;
  input.value = "";
  draftChanged();
  input.focus();
  $("announcer").textContent = "Nueva conversación iniciada.";
});
document.querySelectorAll("[data-prompt]").forEach(button => button.addEventListener("click", () => choosePrompt(button.dataset.prompt)));

checkConnection();
fetch("/v1/web/catalog", { cache: "no-store", signal: AbortSignal.timeout(10000) })
  .then(response => { if (!response.ok) throw new Error("unavailable"); return response.json(); })
  .then(async data => {
    renderCatalog(data);
    try {
      const response = await fetch("/v1/web/runtime", { cache: "no-store", signal: AbortSignal.timeout(10000) });
      if (!response.ok) return;
      const runtime = await response.json();
      if (runtime.store_id !== data.profile.store_id || runtime.catalog_profile !== data.profile.revision) return;
      if (runtime.commercial_clock === "simulated") $("data-notice").textContent += ` Precios y existencias se reproducen con reloj simulado: ${new Date(runtime.evaluated_at).toLocaleString("es-CO")}.`;
      $("privacy-note").textContent = `El historial visible permanece en esta pestaña. El servidor local conserva los requisitos durante ${Math.round(runtime.session_ttl_seconds / 60)} minutos de inactividad, en memoria y sin guardarlos en disco. Revisa las fuentes.`;
    } catch { /* The catalog remains usable if the runtime notice is unavailable. */ }
  })
  .catch(() => { $("catalog-message").textContent = "No se pudo cargar el catálogo. Puedes intentar una consulta al asistente."; });
