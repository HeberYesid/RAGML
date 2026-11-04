import test from "node:test";
import assert from "node:assert/strict";
import { createChatClient } from "../../src/ragml/web_assets/chat-client.mjs";

const session = "3da23ae5-6273-4cf1-8241-2f1546533df5";
const reply = {
  schema_version: "0.1", session_id: session,
  request_id: "da731f7b-1d5a-42b4-859a-5739a2b49b57",
  store_id: "test-store", data_mode: "demo", status: "clarification_required",
  answer: "¿Qué tamaño necesitas?", claims: [], citations: [], products: [], warnings: [], versions: {},
};

test("sends same-origin JSON and reuses only the server-issued session", async () => {
  const requests = [];
  const client = createChatClient(async (url, options) => {
    requests.push({ url, ...options });
    return new Response(JSON.stringify(reply));
  });
  assert.deepEqual(await client.send("  Una lámpara  "), reply);
  await client.send("Pequeña");
  assert.equal(requests[0].url, "/v1/chat");
  assert.equal(requests[0].method, "POST");
  assert.equal(requests[0].headers["Content-Type"], "application/json");
  assert.deepEqual(JSON.parse(requests[0].body), { schema_version: "0.1", message: "Una lámpara" });
  assert.equal(JSON.parse(requests[1].body).session_id, session);
});

test("reports unavailable service and connection failure without losing the session", async () => {
  let count = 0;
  const bodies = [];
  const client = createChatClient(async (url, options) => {
    bodies.push(JSON.parse(options.body));
    count += 1;
    if (count === 2) return new Response(JSON.stringify({ code: "rag_not_ready", retryable: true }), { status: 503 });
    if (count === 3) throw new TypeError("private transport detail");
    return new Response(JSON.stringify(reply));
  });
  await client.send("Primera");
  await assert.rejects(client.send("Segunda"), error => error.code === "rag_not_ready" && error.retryable);
  await assert.rejects(client.send("Tercera"), error => error.code === "network_error" && !error.message.includes("private"));
  await client.send("Reintento");
  assert.equal(bodies[3].session_id, session);
});

test("new conversation cancels an in-flight turn and never adopts its late session", async () => {
  let finish;
  let count = 0;
  const bodies = [];
  const client = createChatClient(async (url, options) => {
    bodies.push(JSON.parse(options.body));
    count += 1;
    if (count === 1) return new Promise(resolve => { finish = resolve; });
    return new Response(JSON.stringify(reply));
  });
  const pending = client.send("Consulta anterior");
  await assert.rejects(client.send("Doble envío"), error => error.code === "busy");
  client.reset();
  finish(new Response(JSON.stringify(reply)));
  await assert.rejects(pending, error => error.code === "cancelled");
  await client.send("Nueva consulta");
  assert.equal(bodies.length, 2);
  assert.equal(bodies[1].session_id, undefined);
});

test("rejects empty or overlong input and malformed replies without adopting a session", async () => {
  let calls = 0;
  const client = createChatClient(async () => {
    calls += 1;
    return new Response(JSON.stringify({ ...reply, status: "invented" }));
  });
  await assert.rejects(client.send("  "), error => error.code === "invalid_input");
  await assert.rejects(client.send("x".repeat(4001)), error => error.code === "invalid_input");
  assert.equal(calls, 0);
  await assert.rejects(client.send("Hola"), error => error.code === "invalid_response");
});

test("bounds waiting time and releases the client for retry", async () => {
  let calls = 0;
  const client = createChatClient(async (url, options) => {
    if (++calls > 1) return new Response(JSON.stringify(reply));
    return new Promise((resolve, reject) => options.signal.addEventListener("abort", () => reject(options.signal.reason)));
  }, { timeoutMs: 20 });
  const deadline = new Promise((resolve, reject) => setTimeout(() => reject(new Error("No timeout was applied")), 200));
  await Promise.race([deadline, assert.rejects(client.send("Consulta lenta"), error => error.code === "timeout" && error.retryable)]);
  assert.deepEqual(await client.send("Reintento"), reply);
});

test("does not accept broken evidence links or fields that the interface cannot render", async () => {
  const malformed = [
    { ...reply, status: "answered", claims: [] },
    { ...reply, claims: [{ text: "Unbacked", citation_ids: ["missing"] }] },
    { ...reply, citations: [{ kind: "document", citation_id: "c1", location: null }] },
    { ...reply, products: [{}] },
    { ...reply, warnings: [null] },
  ];
  for (const payload of malformed) {
    const client = createChatClient(async () => new Response(JSON.stringify(payload)));
    await assert.rejects(client.send("Consulta"), error => error.code === "invalid_response");
  }
});

test("new conversation removes the previous server session using same-origin credentials", async () => {
  const requests = [];
  const client = createChatClient(async (url, options) => {
    requests.push({ url, ...options });
    if (options.method === "DELETE") return new Response(null, { status: 204 });
    return new Response(JSON.stringify(reply));
  });
  await client.send("Primera");
  await client.reset();
  await client.send("Nueva");
  assert.equal(requests[1].method, "DELETE");
  assert.equal(requests[1].url, `/v1/chat/sessions/${session}`);
  assert.equal(requests[1].credentials, "same-origin");
  assert.equal(JSON.parse(requests[2].body).session_id, undefined);
});

test("expired sessions release the old identity before a retry", async () => {
  const requests = [];
  const client = createChatClient(async (url, options) => {
    requests.push(JSON.parse(options.body));
    if (requests.length === 2) return new Response(JSON.stringify({ code: "session_not_found" }), { status: 404 });
    return new Response(JSON.stringify(reply));
  });
  await client.send("Primera");
  await assert.rejects(client.send("Seguimiento"), error => error.code === "session_not_found" && error.retryable);
  await client.send("Nueva consulta");
  assert.equal(requests[2].session_id, undefined);
});
