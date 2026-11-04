/** Same-origin ChatRequest/ChatResponse transport. No browser persistence. */
export class ChatFailure extends Error {
  constructor(code, retryable = false, requestId = null) {
    super(code);
    this.code = code;
    this.retryable = retryable;
    this.requestId = requestId;
  }
}

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const STATUSES = new Set(["answered", "clarification_required", "insufficient_evidence", "temporarily_unavailable"]);

function validReply(result) {
  const text = value => typeof value === "string" && value.trim().length > 0;
  if (!(result && result.schema_version === "0.1" && STATUSES.has(result.status)
    && UUID.test(result.session_id) && UUID.test(result.request_id)
    && text(result.answer) && text(result.store_id) && ["demo", "real"].includes(result.data_mode)
    && ["claims", "citations", "products", "warnings"].every(key => Array.isArray(result[key])))) return false;
  const ids = new Set();
  for (const citation of result.citations) {
    if (!citation || ![citation.citation_id, citation.source_id, citation.source_version].every(text)
      || citation.store_id !== result.store_id || ids.has(citation.citation_id)) return false;
    ids.add(citation.citation_id);
    if (citation.kind === "document") {
      if (!text(citation.excerpt) || !text(citation.chunk_id) || !citation.location) return false;
      const location = citation.location;
      if (!((Number.isInteger(location.page) && location.page > 0)
        || text(location.section) || (Number.isInteger(location.paragraph) && location.paragraph > 0)
        || text(location.table))) return false;
    } else if (citation.kind === "commercial") {
      if (![citation.snapshot_id, citation.variant_id].every(text) || !["price", "stock"].includes(citation.field)
        || !Number.isFinite(Date.parse(citation.source_updated_at)) || !Number.isFinite(Date.parse(citation.expires_at))) return false;
    } else return false;
  }
  return (result.status !== "answered" || result.claims.length > 0)
    && result.claims.every(claim => claim && text(claim.text) && Array.isArray(claim.citation_ids)
      && claim.citation_ids.length > 0 && claim.citation_ids.every(id => ids.has(id)))
    && result.products.every(product => product && text(product.product_id) && text(product.variant_id))
    && result.warnings.every(text);
}

export function createChatClient(fetcher = globalThis.fetch.bind(globalThis), { timeoutMs = 240000 } = {}) {
  let sessionId = null;
  let active = null;
  let epoch = 0;
  return {
    cancel() {
      epoch += 1;
      active?.abort();
      active = null;
    },
    reset() {
      this.cancel();
      sessionId = null;
    },
    async send(text) {
      const message = text.trim();
      if (!message || [...message].length > 4000) throw new ChatFailure("invalid_input");
      if (active) throw new ChatFailure("busy");
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), timeoutMs);
      active = controller;
      const turn = epoch;
      const body = { schema_version: "0.1", message };
      if (sessionId) body.session_id = sessionId;
      try {
        const response = await fetcher("/v1/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
          cache: "no-store",
          signal: controller.signal,
        });
        let result;
        try {
          result = await response.json();
        } catch {
          throw new ChatFailure("invalid_response", true);
        }
        if (turn !== epoch) throw new ChatFailure("cancelled");
        if (!response.ok) {
          throw new ChatFailure(result?.code || "internal_error", result?.retryable === true, result?.request_id);
        }
        if (!validReply(result)) throw new ChatFailure("invalid_response", true);
        sessionId = result.session_id;
        return result;
      } catch (error) {
        if (turn !== epoch) throw new ChatFailure("cancelled");
        if (controller.signal.aborted) throw new ChatFailure("timeout", true);
        if (error instanceof ChatFailure) throw error;
        throw new ChatFailure("network_error", true);
      } finally {
        clearTimeout(timeout);
        if (active === controller) active = null;
      }
    },
  };
}
