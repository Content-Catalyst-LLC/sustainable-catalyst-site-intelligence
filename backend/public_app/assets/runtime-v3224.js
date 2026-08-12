(function (window, document) {
  "use strict";

  const VERSION = "4.35.21";
  const EVENT_LIMIT = 30;
  const ENDPOINTS = [
    ["Service", "/health"],
    ["Build", "/public/build-info"],
    ["Deployment Receipt", "/public/deployment-receipt"],
    ["Release Gate", "/public/release-gate?plugin_version=4.35.21&expected_release_id=site-intelligence-v4.35.21"],
    ["Runtime", "/public/runtime-health"],
    ["Recovery", "/public/runtime-recovery"],
    ["Geospatial", "/public/geospatial/diagnostics"],
    ["Spatial", "/public/spatial"],
  ];
  const state = {
    startedAt: new Date().toISOString(),
    online: navigator.onLine !== false,
    serviceWorker: "checking",
    contract: null,
    recoveryContract: null,
    endpoints: [],
    events: [],
    errors: [],
    running: false,
  };

  function emit(type, detail) {
    window.dispatchEvent(new CustomEvent(type, { detail: { version: VERSION, ...detail } }));
  }

  function text(value) {
    return String(value == null ? "" : value);
  }

  function escapeHtml(value) {
    return text(value).replace(/[&<>"']/g, function (character) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[character];
    });
  }

  function recordEvent(type, detail) {
    state.events.unshift({ type, detail: detail || {}, at: new Date().toISOString() });
    state.events = state.events.slice(0, EVENT_LIMIT);
    updateUi();
  }

  function recordError(type, message, source) {
    state.errors.unshift({ type, message: text(message).slice(0, 400), source: text(source).slice(0, 240), at: new Date().toISOString() });
    state.errors = state.errors.slice(0, EVENT_LIMIT);
    updateUi();
  }

  async function fetchJson(path, timeoutMs) {
    const controller = new AbortController();
    const timeout = setTimeout(function () { controller.abort(); }, timeoutMs || 7000);
    const started = performance.now();
    try {
      const response = await fetch(path, {
        headers: { Accept: "application/json", "X-SCSI-Runtime-Diagnostic": VERSION },
        cache: "no-store",
        credentials: "same-origin",
        signal: controller.signal,
      });
      const elapsedMs = Math.round(performance.now() - started);
      let payload = null;
      try { payload = await response.json(); } catch (_) {}
      return { ok: response.ok, status: response.status, elapsedMs, payload, path };
    } catch (error) {
      return {
        ok: false,
        status: 0,
        elapsedMs: Math.round(performance.now() - started),
        error: error && error.name === "AbortError" ? "timeout" : text(error && error.message ? error.message : error),
        path,
      };
    } finally {
      clearTimeout(timeout);
    }
  }

  function mapSnapshot() {
    if (window.SCSIMapReliability && typeof window.SCSIMapReliability.snapshot === "function") {
      return window.SCSIMapReliability.snapshot();
    }
    const containers = Array.from(document.querySelectorAll(".scsi-map-managed, .scsi-static-map, [id$='Map']"));
    return {
      version: window.SCSIMapReliability?.version || "unknown",
      libraryMode: window.L?.__scsiFirstParty ? "first-party-interactive" : window.L?.__scsiFallback ? "geographic-fallback" : window.L ? "leaflet" : "unavailable",
      mapCount: containers.length,
      modes: containers.reduce(function (counts, container) {
        const mode = container.dataset.scsiMapMode || (container.classList.contains("scsi-static-map") ? "first-party-interactive" : "declared");
        counts[mode] = (counts[mode] || 0) + 1;
        return counts;
      }, {}),
    };
  }

  function visibleMapContainers() {
    return Array.from(document.querySelectorAll(".scsi-map-managed, .scsi-static-map, [id$='Map']")).filter(function (element) {
      const style = window.getComputedStyle(element);
      return style.display !== "none" && style.visibility !== "hidden" && element.getClientRects().length > 0;
    }).map(function (element) {
      return {
        id: element.id || "unnamed-map",
        mode: element.dataset.scsiMapMode || (element.classList.contains("scsi-static-map") ? "first-party-interactive" : "leaflet-or-pending"),
        degraded: element.dataset.scsiMapStatus === "degraded" || element.classList.contains("scsi-map-tile-degraded") || element.classList.contains("scsi-map-grid-overlay"),
      };
    });
  }


  function serviceSnapshot() {
    if (window.SCSIServiceRecovery && typeof window.SCSIServiceRecovery.snapshot === "function") {
      return window.SCSIServiceRecovery.snapshot();
    }
    return { version: "unavailable", groups: [], recentRequests: [] };
  }

  async function serviceWorkerState() {
    if (!("serviceWorker" in navigator)) return "unsupported";
    try {
      const registration = await navigator.serviceWorker.getRegistration("/app/");
      if (!registration) return "not-registered";
      if (registration.active) return "active";
      if (registration.waiting) return "waiting";
      if (registration.installing) return "installing";
      return "registered";
    } catch (_) {
      return "unavailable";
    }
  }

  function overallStatus() {
    const failed = state.endpoints.filter(function (item) { return !item.ok; }).length;
    const maps = mapSnapshot();
    const visibleSurfaces = (maps.surfaces || visibleMapContainers()).filter(function (surface) { return surface.visible !== false; });
    const degradedMaps = visibleSurfaces.some(function (surface) { return surface.degraded || surface.status === "degraded"; });
    const degradedServices = (serviceSnapshot().groups || []).some(function (group) { return group.degraded || group.circuitOpen; });
    if (!state.online || failed >= 3) return "offline";
    if (failed || state.errors.length || degradedMaps || degradedServices || state.contract?.status === "degraded") return "degraded";
    return state.running ? "checking" : "healthy";
  }

  function statusLabel(status) {
    return { healthy: "Healthy", degraded: "Degraded", offline: "Offline", checking: "Checking" }[status] || "Review";
  }

  function ensureUi() {
    if (document.getElementById("scsiRuntimeToggle")) return;
    const toggle = document.createElement("button");
    toggle.id = "scsiRuntimeToggle";
    toggle.className = "scsi-runtime-toggle";
    toggle.type = "button";
    toggle.setAttribute("aria-haspopup", "dialog");
    toggle.setAttribute("aria-controls", "scsiRuntimePanel");
    toggle.innerHTML = '<span class="scsi-runtime-dot" aria-hidden="true"></span><span data-runtime-toggle-label>Site health</span>';

    const panel = document.createElement("section");
    panel.id = "scsiRuntimePanel";
    panel.className = "scsi-runtime-panel";
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-modal", "false");
    panel.setAttribute("aria-labelledby", "scsiRuntimeTitle");
    panel.hidden = true;
    panel.innerHTML = [
      '<header class="scsi-runtime-header">',
      '<div><p>Runtime diagnostics · v' + VERSION + '</p><h2 id="scsiRuntimeTitle">Site Intelligence health</h2></div>',
      '<button type="button" class="scsi-runtime-close" aria-label="Close runtime diagnostics">×</button>',
      '</header>',
      '<div class="scsi-runtime-summary" data-runtime-summary></div>',
      '<div class="scsi-runtime-actions"><button type="button" data-runtime-rerun>Run checks</button><button type="button" data-runtime-recover>Retry failed services</button><button type="button" data-runtime-copy>Copy report</button></div>',
      '<div class="scsi-runtime-body" data-runtime-body></div>',
    ].join("");
    document.body.appendChild(toggle);
    document.body.appendChild(panel);

    toggle.addEventListener("click", function () {
      panel.hidden = !panel.hidden;
      toggle.setAttribute("aria-expanded", panel.hidden ? "false" : "true");
      if (!panel.hidden) panel.querySelector(".scsi-runtime-close")?.focus();
    });
    panel.querySelector(".scsi-runtime-close").addEventListener("click", function () {
      panel.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
      toggle.focus();
    });
    panel.querySelector("[data-runtime-rerun]").addEventListener("click", runChecks);
    panel.querySelector("[data-runtime-recover]").addEventListener("click", function () {
      window.SCSIServiceRecovery?.reset?.();
      (serviceSnapshot().groups || []).filter(function (group) { return group.degraded; }).forEach(function (group) { window.SCSIServiceRecovery?.probe?.(group.id); });
      runChecks();
    });
    panel.querySelector("[data-runtime-copy]").addEventListener("click", copyReport);
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && !panel.hidden) {
        panel.hidden = true;
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });
  }

  function reportObject() {
    return {
      version: VERSION,
      generatedAt: new Date().toISOString(),
      page: window.location.href,
      online: state.online,
      serviceWorker: state.serviceWorker,
      overallStatus: overallStatus(),
      contract: state.contract,
      recoveryContract: state.recoveryContract,
      serviceRecovery: serviceSnapshot(),
      endpoints: state.endpoints,
      maps: mapSnapshot(),
      visibleMaps: visibleMapContainers(),
      recentEvents: state.events.slice(0, 12),
      recentErrors: state.errors.slice(0, 12),
      userAgent: navigator.userAgent,
    };
  }

  async function copyReport() {
    const payload = JSON.stringify(reportObject(), null, 2);
    const button = document.querySelector("[data-runtime-copy]");
    try {
      await navigator.clipboard.writeText(payload);
      if (button) button.textContent = "Copied";
    } catch (_) {
      const area = document.createElement("textarea");
      area.value = payload;
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      area.remove();
      if (button) button.textContent = "Copied";
    }
    setTimeout(function () { if (button) button.textContent = "Copy report"; }, 1600);
  }

  function endpointRows() {
    if (!state.endpoints.length) return '<p class="scsi-runtime-muted">No endpoint checks have run yet.</p>';
    return '<div class="scsi-runtime-list">' + state.endpoints.map(function (item) {
      const detail = item.ok ? item.status + " · " + item.elapsedMs + " ms" : (item.error || ("HTTP " + item.status));
      return '<div class="scsi-runtime-row"><span class="scsi-runtime-state is-' + (item.ok ? "pass" : "fail") + '">' + (item.ok ? "Pass" : "Fail") + '</span><strong>' + escapeHtml(item.label) + '</strong><small>' + escapeHtml(detail) + '</small></div>';
    }).join("") + '</div>';
  }

  function mapRows() {
    const snapshot = mapSnapshot();
    const visible = visibleMapContainers();
    const surfaces = snapshot.surfaces || visible;
    const rows = surfaces.length ? '<div class="scsi-runtime-list">' + surfaces.map(function (surface) {
      const detail = [surface.mode || "pending", surface.visible === false ? "hidden" : "visible", surface.recoveryScheduled ? "recovery scheduled" : ""].filter(Boolean).join(" · ");
      return '<div class="scsi-runtime-row"><span class="scsi-runtime-state is-' + (surface.degraded ? "fail" : "pass") + '">' + (surface.degraded ? "Degraded" : "Ready") + '</span><strong>' + escapeHtml(surface.id || "unnamed-map") + '</strong><small>' + escapeHtml(detail) + '</small></div>';
    }).join("") + '</div>' : '<p class="scsi-runtime-muted">No initialized maps detected.</p>';
    return '<div class="scsi-runtime-metric-grid">' +
      '<div><strong>' + escapeHtml(snapshot.libraryMode) + '</strong><span>Map library</span></div>' +
      '<div><strong>' + escapeHtml(snapshot.mapCount) + '</strong><span>Initialized maps</span></div>' +
      '<div><strong>' + escapeHtml(snapshot.degradedCount || 0) + '</strong><span>Degraded maps</span></div>' +
      '<div><strong>' + escapeHtml(state.serviceWorker) + '</strong><span>Offline worker</span></div>' +
      '</div>' + rows;
  }

  function serviceRows() {
    const snapshot = serviceSnapshot();
    const groups = snapshot.groups || [];
    if (!groups.length) return '<p class="scsi-runtime-muted">The service-recovery runtime is unavailable.</p>';
    return '<div class="scsi-runtime-list">' + groups.map(function (group) {
      const degraded = group.degraded || group.circuitOpen;
      const detail = [group.circuitOpen ? "circuit open" : "circuit closed", group.retries + " retries", group.cacheRecoveries + " cached recoveries"].join(" · ");
      return '<div class="scsi-runtime-row"><span class="scsi-runtime-state is-' + (degraded ? "review" : "pass") + '">' + (degraded ? "Recovering" : "Ready") + '</span><strong>' + escapeHtml(group.id) + '</strong><small>' + escapeHtml(detail) + '</small></div>';
    }).join("") + '</div>';
  }

  function eventRows() {
    const items = state.events.slice(0, 8);
    const errors = state.errors.slice(0, 5);
    if (!items.length && !errors.length) return '<p class="scsi-runtime-muted">No runtime faults have been recorded in this page session.</p>';
    return '<div class="scsi-runtime-list">' + errors.map(function (item) {
      return '<div class="scsi-runtime-row"><span class="scsi-runtime-state is-fail">Error</span><strong>' + escapeHtml(item.type) + '</strong><small>' + escapeHtml(item.message) + '</small></div>';
    }).join("") + items.map(function (item) {
      return '<div class="scsi-runtime-row"><span class="scsi-runtime-state is-review">Event</span><strong>' + escapeHtml(item.type) + '</strong><small>' + escapeHtml(item.detail.reason || item.detail.mode || item.at) + '</small></div>';
    }).join("") + '</div>';
  }

  function updateUi() {
    ensureUi();
    const status = overallStatus();
    const toggle = document.getElementById("scsiRuntimeToggle");
    const panel = document.getElementById("scsiRuntimePanel");
    if (!toggle || !panel) return;
    toggle.dataset.status = status;
    panel.dataset.status = status;
    const label = toggle.querySelector("[data-runtime-toggle-label]");
    if (label) label.textContent = "Site health: " + statusLabel(status);
    const summary = panel.querySelector("[data-runtime-summary]");
    if (summary) summary.innerHTML = '<strong>' + statusLabel(status) + '</strong><span>' + (state.running ? "Checks are running." : "Local runtime and critical public endpoints.") + '</span>';
    const body = panel.querySelector("[data-runtime-body]");
    if (body) body.innerHTML = '<section><h3>Application contract</h3>' + endpointRows() + '</section><section><h3>Service recovery</h3>' + serviceRows() + '</section><section><h3>Map-by-map health</h3>' + mapRows() + '</section><section><h3>Session faults</h3>' + eventRows() + '</section><p class="scsi-runtime-footnote">Diagnostics are local and public-safe. Hidden map workspaces do not lower health, and the first-party interactive map runtime is a healthy production mode. Cached recovery responses remain explicitly marked.</p>';
  }

  async function runChecks() {
    if (state.running) return;
    state.running = true;
    updateUi();
    const results = await Promise.all(ENDPOINTS.map(async function (entry) {
      const result = await fetchJson(entry[1], 7000);
      return { label: entry[0], ...result };
    }));
    state.endpoints = results;
    const runtime = results.find(function (item) { return item.path === "/public/runtime-health"; });
    const recovery = results.find(function (item) { return item.path === "/public/runtime-recovery"; });
    state.contract = runtime && runtime.ok ? runtime.payload : null;
    state.recoveryContract = recovery && recovery.ok ? recovery.payload : null;
    state.serviceWorker = await serviceWorkerState();
    state.running = false;
    updateUi();
    emit("scsi:runtime-health", reportObject());
  }

  ["scsi:map-library-ready", "scsi:map-first-party-ready", "scsi:map-initialized", "scsi:map-degraded", "scsi:map-fallback", "scsi:map-recovered", "scsi:map-retry", "scsi:imagery-degraded", "scsi:service-recovery-ready", "scsi:service-retry", "scsi:service-fallback", "scsi:service-circuit-open", "scsi:service-recovered"].forEach(function (name) {
    window.addEventListener(name, function (event) { recordEvent(name, event.detail || {}); });
  });
  window.addEventListener("error", function (event) {
    recordError("window-error", event.message || "Unknown script error", event.filename || "");
  });
  window.addEventListener("unhandledrejection", function (event) {
    const reason = event.reason && event.reason.message ? event.reason.message : event.reason;
    recordError("unhandled-rejection", reason || "Unhandled promise rejection", "");
  });
  window.addEventListener("online", function () { state.online = true; recordEvent("browser-online", {}); runChecks(); });
  window.addEventListener("offline", function () { state.online = false; recordEvent("browser-offline", {}); });
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.addEventListener("message", function (event) {
      if (event.data && /^SC_SI_/.test(event.data.type || "")) recordEvent(event.data.type, event.data);
    });
  }

  window.SCSIRuntimeHealth = {
    version: VERSION,
    run: runChecks,
    report: reportObject,
    state: state,
  };

  document.addEventListener("DOMContentLoaded", function () {
    ensureUi();
    updateUi();
    setTimeout(runChecks, 250);
  });
})(window, document);
