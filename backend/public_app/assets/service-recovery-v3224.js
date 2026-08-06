(function (window) {
  "use strict";

  const VERSION = "3.23.5";
  const CACHE_NAME = "scsi-runtime-recovery-v3.23.5";
  const MAX_ATTEMPTS = 3;
  const TIMEOUT_MS = 12000;
  const BACKOFF_MS = [600, 1400];
  const FAILURE_THRESHOLD = 3;
  const CIRCUIT_COOLDOWN_MS = 30000;
  const PROBE_INTERVAL_MS = 30000;
  const DEFAULT_STALE_TTL_MS = 6 * 60 * 60 * 1000;
  const RECOVERABLE_STATUS = new Set([408, 425, 429, 500, 502, 503, 504]);
  const nativeFetch = window.fetch.bind(window);

  const GROUPS = [
    { id: "core", prefixes: ["/health", "/public/build-info", "/public/runtime-"], ttl: 15 * 60 * 1000 },
    { id: "geospatial", prefixes: ["/public/geospatial", "/public/spatial", "/public/earth", "/public/events"], ttl: 6 * 60 * 60 * 1000 },
    { id: "country", prefixes: ["/public/country", "/public/global-country", "/public/compare", "/public/dossiers"], ttl: 6 * 60 * 60 * 1000 },
    { id: "indicators", prefixes: ["/public/global-conditions", "/public/economics", "/public/science", "/public/humanitarian", "/public/resources", "/public/thematic"], ttl: 6 * 60 * 60 * 1000 },
    { id: "research", prefixes: ["/public/research", "/public/evidence", "/public/knowledge-graph", "/public/intelligence-publishing", "/public/source-methodology"], ttl: 24 * 60 * 60 * 1000 },
    { id: "operations", prefixes: ["/public/monitoring", "/public/workspaces", "/public/workflows", "/public/federation", "/public/production-governance", "/public/platform"], ttl: 60 * 60 * 1000 },
  ];

  const groupState = Object.fromEntries(GROUPS.map(function (group) {
    return [group.id, { id: group.id, failures: 0, circuitUntil: 0, degraded: false, lastFailure: null, lastSuccess: null, lastFailedPath: null, retries: 0, cacheRecoveries: 0 }];
  }));
  groupState.other = { id: "other", failures: 0, circuitUntil: 0, degraded: false, lastFailure: null, lastSuccess: null, lastFailedPath: null, retries: 0, cacheRecoveries: 0 };
  const memoryCache = new Map();
  const recentRequests = [];

  function dispatch(type, detail) {
    window.dispatchEvent(new CustomEvent(type, { detail: { version: VERSION, ...detail } }));
  }

  function groupFor(pathname) {
    return GROUPS.find(function (group) {
      return group.prefixes.some(function (prefix) { return pathname.startsWith(prefix); });
    }) || { id: "other", ttl: DEFAULT_STALE_TTL_MS };
  }

  function requestParts(input, init) {
    try {
      const request = input instanceof Request ? input : new Request(input, init);
      const url = new URL(request.url, window.location.href);
      const headers = new Headers(init?.headers || request.headers || {});
      return { request, url, headers, method: String(init?.method || request.method || "GET").toUpperCase() };
    } catch (_) {
      return null;
    }
  }

  function eligible(parts) {
    if (!parts || parts.method !== "GET" || parts.url.origin !== window.location.origin) return false;
    if (parts.headers.has("X-SCSI-Runtime-Diagnostic") || parts.headers.has("X-SCSI-Recovery-Bypass")) return false;
    if (!(parts.url.pathname.startsWith("/public/") || parts.url.pathname === "/health" || parts.url.pathname.startsWith("/api/public/"))) return false;
    const accept = String(parts.headers.get("Accept") || "").toLowerCase();
    if (accept && !accept.includes("json") && !accept.includes("*/*")) return false;
    const format = parts.url.searchParams.get("format");
    if (format && !["json", "geojson"].includes(format.toLowerCase())) return false;
    return true;
  }

  function recordRequest(record) {
    recentRequests.unshift({ at: new Date().toISOString(), ...record });
    recentRequests.splice(40);
  }

  function wait(ms) {
    return new Promise(function (resolve) { setTimeout(resolve, ms); });
  }

  async function responseBody(response) {
    return await response.clone().text();
  }

  async function writeCache(url, response) {
    const contentType = String(response.headers.get("Content-Type") || "").toLowerCase();
    if (!response.ok || !contentType.includes("json")) return;
    const body = await responseBody(response);
    if (!body || body.length > 1_000_000) return;
    const savedAt = Date.now();
    const headers = new Headers(response.headers);
    headers.set("X-SCSI-Saved-At", String(savedAt));
    headers.set("X-SCSI-Release", VERSION);
    const cached = new Response(body, { status: response.status, statusText: response.statusText, headers });
    memoryCache.set(url, { body, headers: Array.from(headers.entries()), savedAt });
    if ("caches" in window) {
      try {
        const cache = await caches.open(CACHE_NAME);
        await cache.put(url, cached.clone());
      } catch (_) {}
    }
  }

  async function readCache(url, ttlMs) {
    let response = null;
    if ("caches" in window) {
      try { response = await (await caches.open(CACHE_NAME)).match(url); } catch (_) {}
    }
    if (!response && memoryCache.has(url)) {
      const item = memoryCache.get(url);
      response = new Response(item.body, { status: 200, headers: new Headers(item.headers) });
    }
    if (!response) return null;
    const savedAt = Number(response.headers.get("X-SCSI-Saved-At") || 0);
    const ageMs = savedAt > 0 ? Date.now() - savedAt : Infinity;
    if (!Number.isFinite(ageMs) || ageMs > ttlMs) return null;
    const body = await response.clone().text();
    const headers = new Headers(response.headers);
    headers.set("X-SCSI-Recovery", "last-known-good");
    headers.set("X-SCSI-Stale-Age-Ms", String(Math.max(0, ageMs)));
    headers.set("X-SCSI-Recovery-Version", VERSION);
    return new Response(body, { status: 200, statusText: "Recovered", headers });
  }

  function markFailure(group, pathname, reason) {
    const state = groupState[group.id] || groupState.other;
    state.failures += 1;
    state.degraded = true;
    state.lastFailure = new Date().toISOString();
    state.lastFailedPath = pathname;
    if (state.failures >= FAILURE_THRESHOLD && Date.now() >= state.circuitUntil) {
      state.circuitUntil = Date.now() + CIRCUIT_COOLDOWN_MS;
      dispatch("scsi:service-circuit-open", { group: group.id, path: pathname, reason, cooldownMs: CIRCUIT_COOLDOWN_MS });
    }
  }

  function markSuccess(group, pathname, status) {
    const state = groupState[group.id] || groupState.other;
    const recovered = state.degraded || state.failures > 0 || state.circuitUntil > 0;
    state.failures = 0;
    state.circuitUntil = 0;
    state.degraded = false;
    state.lastSuccess = new Date().toISOString();
    if (recovered) dispatch("scsi:service-recovered", { group: group.id, path: pathname, status });
  }

  async function recoveredResponse(group, url, pathname, reason) {
    const cached = await readCache(url, group.ttl || DEFAULT_STALE_TTL_MS);
    if (!cached) return null;
    const state = groupState[group.id] || groupState.other;
    state.cacheRecoveries += 1;
    dispatch("scsi:service-fallback", {
      group: group.id,
      path: pathname,
      reason,
      staleAgeMs: Number(cached.headers.get("X-SCSI-Stale-Age-Ms") || 0),
    });
    recordRequest({ path: pathname, group: group.id, outcome: "last-known-good", reason });
    return cached;
  }

  async function fetchAttempt(input, init, parts, group, attempt) {
    const controller = new AbortController();
    const originalSignal = init?.signal || (input instanceof Request ? input.signal : null);
    const relayAbort = function () { controller.abort(originalSignal?.reason || "caller-abort"); };
    if (originalSignal) {
      if (originalSignal.aborted) relayAbort();
      else originalSignal.addEventListener("abort", relayAbort, { once: true });
    }
    const timeout = setTimeout(function () { controller.abort("scsi-timeout"); }, TIMEOUT_MS);
    const requestInit = { ...(init || {}), signal: controller.signal };
    try {
      const response = await nativeFetch(input, requestInit);
      if (response.ok) {
        const recoveryMode = response.headers.get("X-SCSI-Recovery");
        await writeCache(parts.url.href, response.clone());
        if (recoveryMode) {
          const state = groupState[group.id] || groupState.other;
          state.degraded = true;
          state.cacheRecoveries += 1;
          dispatch("scsi:service-fallback", { group: group.id, path: parts.url.pathname, reason: recoveryMode, staleAgeMs: Number(response.headers.get("X-SCSI-Stale-Age-Ms") || 0) });
          recordRequest({ path: parts.url.pathname, group: group.id, outcome: recoveryMode, status: response.status, attempt });
        } else {
          markSuccess(group, parts.url.pathname, response.status);
          recordRequest({ path: parts.url.pathname, group: group.id, outcome: "network", status: response.status, attempt });
        }
        return response;
      }
      if (!RECOVERABLE_STATUS.has(response.status)) {
        recordRequest({ path: parts.url.pathname, group: group.id, outcome: "http", status: response.status, attempt });
        return response;
      }
      throw Object.assign(new Error("HTTP " + response.status), { status: response.status });
    } finally {
      clearTimeout(timeout);
      if (originalSignal) originalSignal.removeEventListener("abort", relayAbort);
    }
  }

  async function reliableFetch(input, init) {
    const parts = requestParts(input, init);
    if (!eligible(parts)) return nativeFetch(input, init);
    const group = groupFor(parts.url.pathname);
    const state = groupState[group.id] || groupState.other;

    if (state.circuitUntil > Date.now()) {
      const fallback = await recoveredResponse(group, parts.url.href, parts.url.pathname, "circuit-open");
      if (fallback) return fallback;
      throw new TypeError("Site Intelligence service group is temporarily isolated: " + group.id);
    }

    let lastError = null;
    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
      try {
        return await fetchAttempt(input, init, parts, group, attempt);
      } catch (error) {
        if (error?.name === "AbortError" && (init?.signal?.aborted || (input instanceof Request && input.signal?.aborted))) throw error;
        lastError = error;
        if (attempt < MAX_ATTEMPTS) {
          state.retries += 1;
          dispatch("scsi:service-retry", { group: group.id, path: parts.url.pathname, attempt: attempt + 1, reason: error?.message || "network-error" });
          await wait(BACKOFF_MS[attempt - 1] || BACKOFF_MS[BACKOFF_MS.length - 1]);
        }
      }
    }

    const reason = lastError?.message || "network-error";
    markFailure(group, parts.url.pathname, reason);
    const fallback = await recoveredResponse(group, parts.url.href, parts.url.pathname, reason);
    if (fallback) return fallback;
    recordRequest({ path: parts.url.pathname, group: group.id, outcome: "failed", reason });
    throw lastError || new TypeError("Site Intelligence request failed");
  }

  async function probeGroup(groupId) {
    const state = groupState[groupId];
    if (!state || !state.degraded || !state.lastFailedPath || navigator.onLine === false) return false;
    try {
      const response = await nativeFetch(state.lastFailedPath, {
        headers: { Accept: "application/json", "X-SCSI-Recovery-Bypass": VERSION },
        cache: "no-store",
        credentials: "same-origin",
      });
      if (!response.ok) return false;
      const group = GROUPS.find(function (item) { return item.id === groupId; }) || { id: groupId };
      await writeCache(new URL(state.lastFailedPath, window.location.href).href, response.clone());
      markSuccess(group, state.lastFailedPath, response.status);
      return true;
    } catch (_) {
      return false;
    }
  }

  function snapshot() {
    return {
      version: VERSION,
      cacheName: CACHE_NAME,
      online: navigator.onLine !== false,
      groups: Object.values(groupState).map(function (item) {
        return { ...item, circuitOpen: item.circuitUntil > Date.now(), cooldownRemainingMs: Math.max(0, item.circuitUntil - Date.now()) };
      }),
      recentRequests: recentRequests.slice(0, 20),
    };
  }

  function reset(groupId) {
    const targets = groupId ? [groupState[groupId]].filter(Boolean) : Object.values(groupState);
    targets.forEach(function (item) { item.failures = 0; item.circuitUntil = 0; item.degraded = false; });
    dispatch("scsi:service-circuits-reset", { group: groupId || "all" });
  }

  window.fetch = reliableFetch;
  window.SCSIServiceRecovery = { version: VERSION, snapshot, reset, probe: probeGroup, nativeFetch };
  window.addEventListener("online", function () {
    Object.values(groupState).filter(function (item) { return item.degraded; }).forEach(function (item) { probeGroup(item.id); });
  });
  setInterval(function () {
    Object.values(groupState).filter(function (item) { return item.degraded; }).forEach(function (item) { probeGroup(item.id); });
  }, PROBE_INTERVAL_MS);
  dispatch("scsi:service-recovery-ready", { groups: GROUPS.map(function (group) { return group.id; }) });
})(window);
