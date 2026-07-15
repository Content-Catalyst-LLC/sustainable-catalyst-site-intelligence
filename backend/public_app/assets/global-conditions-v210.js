(() => {
  "use strict";
  const VERSION = "2.1.0";
  const API = window.location.origin;
  const state = { map: null, featureLayer: null, loaded: false, active: false };
  const $ = (selector) => document.querySelector(selector);
  const escapeHtml = (value) => String(value ?? "")
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");

  async function getJson(path, options = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), options.timeout || 15000);
    try {
      const response = await fetch(`${API}${path}`, {
        headers: { Accept: "application/json" }, signal: controller.signal,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } finally { clearTimeout(timer); }
  }

  function panelMarkup() {
    return `<section id="globalConditionsObservatory" class="global-conditions-v210" hidden aria-labelledby="globalConditionsTitle">
      <header class="gc-hero">
        <p class="gc-kicker">GLOBAL CONDITIONS AND LIVE MAP OBSERVATORY</p>
        <h2 id="globalConditionsTitle">One map for public conditions across Sustainable Catalyst</h2>
        <p>Explore Core-powered geographic features, source-aware observations, existing Site Intelligence events, and Earth-observation layers without exposing provider credentials to the browser.</p>
        <div class="gc-status-grid" aria-label="Global conditions status">
          <article><span>Integration</span><strong id="gcIntegrationState">Checking…</strong></article>
          <article><span>Mapped records</span><strong id="gcFeatureCount">—</strong></article>
          <article><span>Registered layers</span><strong id="gcLayerCount">—</strong></article>
          <article><span>Current signals</span><strong id="gcSignalCount">—</strong></article>
        </div>
      </header>
      <div class="gc-toolbar" aria-label="Global conditions map controls">
        <label>Domain<select id="gcDomain"><option value="">All domains</option><option value="weather">Weather</option><option value="earth_observation">Earth observation</option><option value="hazards">Hazards</option><option value="sustainability">Sustainability</option><option value="economics">Economics</option><option value="humanitarian">Humanitarian</option></select></label>
        <label>Observed after<input id="gcObservedAfter" type="date"></label>
        <button id="gcApply" type="button">Refresh map</button>
        <button id="gcFit" type="button" class="secondary">Fit records</button>
        <button id="gcShare" type="button" class="secondary">Copy view</button>
      </div>
      <div class="gc-layout">
        <section class="gc-map-panel" aria-label="Global conditions map">
          <div id="globalConditionsMap" class="gc-map"></div>
          <p class="gc-map-note" id="gcMapStatus">Preparing public map layers…</p>
        </section>
        <aside class="gc-side-panel">
          <section><p class="gc-label">SIGNAL STREAM</p><h3>Latest observations</h3><div id="gcSignals" class="gc-list"><p>Loading signals…</p></div></section>
          <section><p class="gc-label">LAYER REGISTRY</p><h3>Available map layers</h3><div id="gcLayers" class="gc-list"><p>Loading layers…</p></div></section>
        </aside>
      </div>
      <section class="gc-methodology">
        <p class="gc-label">PUBLIC EVIDENCE BOUNDARY</p>
        <h3>Freshness and provenance stay visible</h3>
        <p>Site Intelligence uses free and official public sources. A mapped feature may be observed, modeled, estimated, delayed, or derived. Confirm important findings against the cited source and current local information.</p>
      </section>
    </section>`;
  }

  function mount() {
    const main = $("#main");
    if (!main || $("#globalConditionsObservatory")) return;
    main.insertAdjacentHTML("beforeend", panelMarkup());
    const nav = $("#primaryNavigation");
    if (nav && !nav.querySelector('[data-route="global"]')) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "nav-item";
      button.dataset.route = "global";
      button.innerHTML = '<span class="nav-label">Global</span><span class="nav-description">Conditions and live map</span>';
      const overview = nav.querySelector('[data-route="overview"]');
      if (overview?.nextSibling) nav.insertBefore(button, overview.nextSibling); else nav.appendChild(button);
    }
    $("#gcApply")?.addEventListener("click", loadAll);
    $("#gcFit")?.addEventListener("click", fitFeatures);
    $("#gcShare")?.addEventListener("click", shareView);
    $("#gcDomain")?.addEventListener("change", syncUrl);
    $("#gcObservedAfter")?.addEventListener("change", syncUrl);
  }

  function initMap() {
    if (state.map || !window.L || !$("#globalConditionsMap")) return;
    state.map = L.map("globalConditionsMap", { worldCopyJump: true, zoomControl: true }).setView([12, 20], 2);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors", maxZoom: 19,
    }).addTo(state.map);
    state.featureLayer = L.geoJSON([], {
      pointToLayer: (feature, latlng) => L.circleMarker(latlng, {
        radius: 6, weight: 1.5, color: "#ffffff", fillColor: markerColor(feature), fillOpacity: 0.9,
      }),
      style: (feature) => ({ color: markerColor(feature), weight: 2, fillOpacity: 0.22 }),
      onEachFeature: (feature, layer) => {
        const p = feature.properties || {};
        layer.bindPopup(`<strong>${escapeHtml(p.title || p.name || p.metric || "Public record")}</strong><br>${escapeHtml(p.domain || p.category || p.record_type || "Public data")}<br>${escapeHtml(p.source_name || p.source_id || "Source identified in record")}<br>${escapeHtml(p.observed_at || p.published_at || "Date unavailable")}`);
      },
    }).addTo(state.map);
  }

  function markerColor(feature) {
    const domain = String(feature?.properties?.domain || feature?.properties?.category || "").toLowerCase();
    if (domain.includes("weather")) return "#43d6ff";
    if (domain.includes("earth") || domain.includes("climate")) return "#7ed957";
    if (domain.includes("hazard") || domain.includes("earthquake") || domain.includes("fire")) return "#ff3434";
    if (domain.includes("economic")) return "#ffd166";
    if (domain.includes("humanitarian")) return "#c792ea";
    return "#b31b34";
  }

  function queryString() {
    const params = new URLSearchParams();
    const domain = $("#gcDomain")?.value || "";
    const observed = $("#gcObservedAfter")?.value || "";
    if (domain) params.set("domain", domain);
    if (observed) params.set("observed_after", `${observed}T00:00:00Z`);
    params.set("limit", "400");
    return params.toString();
  }

  async function localFallbackFeatures() {
    try {
      const payload = await getJson("/public/events?days=14&limit=300", { timeout: 20000 });
      if (payload?.type === "FeatureCollection") return payload;
      if (Array.isArray(payload?.features)) return { type: "FeatureCollection", features: payload.features };
    } catch (_) {}
    try {
      const payload = await getJson("/public/geospatial/events", { timeout: 16000 });
      return { type: "FeatureCollection", features: payload?.features || [] };
    } catch (_) { return { type: "FeatureCollection", features: [] }; }
  }

  async function loadFeatures() {
    let payload;
    try { payload = await getJson(`/public/global-conditions/features?${queryString()}`, { timeout: 22000 }); }
    catch (_) { payload = { state: "degraded", features: [] }; }
    if (!payload.features?.length) {
      const fallback = await localFallbackFeatures();
      payload = { ...fallback, state: payload.state === "connected" ? "connected" : "local-fallback" };
    }
    state.featureLayer?.clearLayers();
    state.featureLayer?.addData(payload);
    const count = payload.features?.length || 0;
    $("#gcFeatureCount").textContent = String(count);
    $("#gcMapStatus").textContent = count
      ? `${count} mapped public records · ${String(payload.state || "available").replaceAll("-", " ")}.`
      : "No mapped records matched the current filters. Existing source and imagery workspaces remain available.";
    if (count) fitFeatures();
  }

  function fitFeatures() {
    const bounds = state.featureLayer?.getBounds?.();
    if (bounds?.isValid?.()) state.map.fitBounds(bounds.pad(0.12), { maxZoom: 7 });
  }

  async function loadOverview() {
    const payload = await getJson("/public/global-conditions", { timeout: 18000 });
    const stateText = payload?.integration?.state || "local-fallback";
    $("#gcIntegrationState").textContent = stateText.replaceAll("-", " ");
    $("#gcIntegrationState").title = payload?.integration?.message || "";
  }

  function renderSignals(payload) {
    const signals = payload?.signals || [];
    $("#gcSignalCount").textContent = String(signals.length);
    $("#gcSignals").innerHTML = signals.length ? signals.slice(0, 12).map((item) => `<article>
      <span>${escapeHtml(item.domain || item.source_id || "Signal")}</span>
      <strong>${escapeHtml(item.metric || "Observation")}</strong>
      <p>${escapeHtml(item.value ?? "Value unavailable")}${item.unit ? ` ${escapeHtml(item.unit)}` : ""}</p>
      <small>${escapeHtml(item.freshness_status || item.observed_at || "Freshness unavailable")}</small>
    </article>`).join("") : "<p>No Core observation signals are currently available. The map continues with Site Intelligence event records.</p>";
  }

  async function loadSignals() {
    try { renderSignals(await getJson("/public/global-conditions/signals?limit=50")); }
    catch (_) { renderSignals({ signals: [] }); }
  }

  function renderLayers(payload) {
    const layers = payload?.layers || [];
    $("#gcLayerCount").textContent = String(layers.length);
    $("#gcLayers").innerHTML = layers.length ? layers.slice(0, 12).map((item) => `<article>
      <span>${escapeHtml(item.layer_type || "layer")}</span>
      <strong>${escapeHtml(item.title || item.id || "Map layer")}</strong>
      <p>${escapeHtml(item.description || item.attribution || "Source metadata available in Core.")}</p>
      <small>${escapeHtml(item.source_id || item.freshness_status || "Source registered")}</small>
    </article>`).join("") : "<p>No Core map layers are registered yet. NASA GIBS and existing Site Intelligence layers remain available in Earth Observation.</p>";
  }

  async function loadLayers() {
    try { renderLayers(await getJson("/public/global-conditions/layers?limit=100")); }
    catch (_) { renderLayers({ layers: [] }); }
  }

  function syncUrl() {
    if (!state.active) return;
    const params = new URLSearchParams(window.location.search);
    params.set("view", "global");
    const domain = $("#gcDomain")?.value || "";
    const observed = $("#gcObservedAfter")?.value || "";
    domain ? params.set("domain", domain) : params.delete("domain");
    observed ? params.set("observed", observed) : params.delete("observed");
    history.replaceState(null, "", `?${params.toString()}`);
  }

  async function shareView() {
    syncUrl();
    try { await navigator.clipboard.writeText(location.href); }
    catch (_) {
      const area = document.createElement("textarea"); area.value = location.href;
      document.body.appendChild(area); area.select(); document.execCommand("copy"); area.remove();
    }
    $("#gcMapStatus").textContent = "Global conditions view link copied.";
  }

  async function loadAll() {
    initMap(); syncUrl();
    $("#globalConditionsObservatory")?.setAttribute("aria-busy", "true");
    await Promise.allSettled([loadOverview(), loadFeatures(), loadSignals(), loadLayers()]);
    $("#globalConditionsObservatory")?.setAttribute("aria-busy", "false");
    state.loaded = true;
    setTimeout(() => state.map?.invalidateSize?.(), 80);
  }

  function close() {
    state.active = false;
    const panel = $("#globalConditionsObservatory");
    if (panel) panel.hidden = true;
    document.body.classList.remove("global-conditions-route");
  }

  async function open() {
    mount(); state.active = true;
    const params = new URLSearchParams(location.search);
    if ($("#gcDomain")) $("#gcDomain").value = params.get("domain") || "";
    if ($("#gcObservedAfter")) $("#gcObservedAfter").value = params.get("observed") || "";
    const panel = $("#globalConditionsObservatory");
    if (panel) panel.hidden = false;
    document.body.classList.add("global-conditions-route");
    if (!state.loaded) await loadAll(); else setTimeout(() => state.map?.invalidateSize?.(), 80);
  }

  window.SCGlobalConditionsV210 = { version: VERSION, mount, open, close, refresh: loadAll, status: () => ({ ...state }) };
  document.addEventListener("DOMContentLoaded", mount);
})();
