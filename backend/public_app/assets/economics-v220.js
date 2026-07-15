(() => {
  "use strict";
  const VERSION = "2.2.0";
  const state = {
    map: null,
    base: null,
    markers: null,
    countries: new Map(),
    records: [],
    overview: null,
    facets: null,
    selectedIndicator: "",
  };
  const qs = (selector, root = document) => root.querySelector(selector);
  const qsa = (selector, root = document) => [...root.querySelectorAll(selector)];
  const esc = (value) => String(value ?? "").replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));
  const text = (value, fallback = "—") => value === null || value === undefined || value === "" ? fallback : String(value);
  const fmt = (value, unit = "") => {
    const number = Number(value);
    if (!Number.isFinite(number)) return text(value);
    const abs = Math.abs(number);
    let result;
    if (abs >= 1e12) result = `${(number / 1e12).toFixed(2)}T`;
    else if (abs >= 1e9) result = `${(number / 1e9).toFixed(2)}B`;
    else if (abs >= 1e6) result = `${(number / 1e6).toFixed(2)}M`;
    else if (abs >= 1e3) result = new Intl.NumberFormat(undefined, {maximumFractionDigits: 1}).format(number);
    else result = new Intl.NumberFormat(undefined, {maximumFractionDigits: 3}).format(number);
    return unit ? `${result} ${unit}` : result;
  };
  async function api(path) {
    const response = await fetch(path, {headers: {"Accept": "application/json"}, credentials: "same-origin"});
    if (!response.ok) throw new Error(`Request failed (${response.status})`);
    return response.json();
  }
  function setStatus(message, mode = "loading") {
    const node = qs("#economicsStatus");
    if (!node) return;
    node.dataset.state = mode;
    const label = node.querySelector("span:last-child");
    if (label) label.textContent = message;
  }
  function showEmpty(title, detail) {
    qs("#economicsRecords").innerHTML = `<div class="economics-empty"><strong>${esc(title)}</strong><span>${esc(detail)}</span></div>`;
    qs("#economicsChart").innerHTML = `<div class="economics-empty"><strong>No series selected</strong><span>Choose an indicator and geography after Core returns official records.</span></div>`;
  }
  function populateSelect(node, items, placeholder, valueKey = "id", labelKey = "label") {
    if (!node) return;
    const current = node.value;
    node.innerHTML = `<option value="">${esc(placeholder)}</option>` + items.map(item => `<option value="${esc(item[valueKey])}">${esc(item[labelKey] || item[valueKey])}${item.count !== undefined ? ` (${esc(item.count)})` : ""}</option>`).join("");
    if ([...node.options].some(option => option.value === current)) node.value = current;
  }
  function fillCountries(catalog) {
    state.countries.clear();
    const countries = catalog?.countries || [];
    countries.forEach(country => state.countries.set(country.code, country));
    const options = countries.map(country => ({code: country.code, name: `${country.name} · ${country.code}`}));
    ["#economicsCountry", "#economicsCompareA", "#economicsCompareB"].forEach(selector => populateSelect(qs(selector), options, selector === "#economicsCountry" ? "All geographies" : "Choose geography", "code", "name"));
    if (qs("#economicsCompareA") && !qs("#economicsCompareA").value) qs("#economicsCompareA").value = "KEN";
    if (qs("#economicsCompareB") && !qs("#economicsCompareB").value) qs("#economicsCompareB").value = "GHA";
  }
  function fillFacets(facets) {
    populateSelect(qs("#economicsFamily"), facets?.families || [], "All domains");
    populateSelect(qs("#economicsSource"), facets?.sources || [], "All official sources");
    populateSelect(qs("#economicsFrequency"), facets?.frequencies || [], "All frequencies");
    const indicators = (facets?.indicators || []).map(item => ({code: item.code, name: `${item.name}${item.code !== item.name ? ` · ${item.code}` : ""}`}));
    populateSelect(qs("#economicsIndicator"), indicators, "All indicators", "code", "name");
    populateSelect(qs("#economicsCompareIndicator"), indicators, "Choose indicator", "code", "name");
    if (!state.selectedIndicator && indicators.length) state.selectedIndicator = indicators[0].code;
    if (state.selectedIndicator) {
      if ([...qs("#economicsIndicator").options].some(o => o.value === state.selectedIndicator)) qs("#economicsIndicator").value = state.selectedIndicator;
      if ([...qs("#economicsCompareIndicator").options].some(o => o.value === state.selectedIndicator)) qs("#economicsCompareIndicator").value = state.selectedIndicator;
    }
  }
  function renderOverview(overview) {
    state.overview = overview;
    const counts = overview?.counts || {};
    qs("#economicsRecordCount").textContent = text(counts.records_available, "0");
    qs("#economicsSourceCount").textContent = text(counts.sources_visible, "0");
    qs("#economicsGeographyCount").textContent = text(counts.geographies_visible, "0");
    qs("#economicsIndicatorCount").textContent = text(counts.indicators_visible, "0");
    const integration = overview?.integration || {};
    setStatus(integration.message || "Economics workspace ready", integration.state === "connected" ? "ready" : integration.state === "degraded" ? "error" : "fallback");
    qs("#economicsPolicy").textContent = overview?.market_data_policy?.statement || "Official release frequency and source dates remain visible.";
    const families = (overview?.families || []).filter(item => item.count > 0);
    qs("#economicsFamilySummary").innerHTML = families.length ? families.map(item => `<article><span>${esc(item.label)}</span><strong>${esc(item.count)}</strong><small>visible records</small></article>`).join("") : `<article><span>Core state</span><strong>${esc(integration.state || "unconfigured")}</strong><small>No values are fabricated locally.</small></article>`;
  }
  function paramsFromControls() {
    const params = new URLSearchParams();
    const fields = {
      family: qs("#economicsFamily")?.value,
      source_id: qs("#economicsSource")?.value,
      geography_code: qs("#economicsCountry")?.value,
      indicator_code: qs("#economicsIndicator")?.value,
      frequency: qs("#economicsFrequency")?.value,
      query: qs("#economicsSearch")?.value.trim(),
    };
    Object.entries(fields).forEach(([key, value]) => { if (value) params.set(key, value); });
    params.set("limit", "180");
    return params;
  }
  function syncUrl() {
    const url = new URL(location.href);
    url.searchParams.set("view", "economics");
    const params = paramsFromControls();
    ["family", "source_id", "geography_code", "indicator_code", "frequency", "query"].forEach(key => url.searchParams.delete(key));
    params.forEach((value, key) => { if (key !== "limit") url.searchParams.set(key, value); });
    history.replaceState(null, "", url);
  }
  function applyUrl() {
    const params = new URLSearchParams(location.search);
    const mapping = {family:"#economicsFamily",source_id:"#economicsSource",geography_code:"#economicsCountry",indicator_code:"#economicsIndicator",frequency:"#economicsFrequency",query:"#economicsSearch"};
    Object.entries(mapping).forEach(([key, selector]) => {
      const value = params.get(key); const node = qs(selector);
      if (!value || !node) return;
      if (node.tagName === "SELECT" && ![...node.options].some(option => option.value === value)) return;
      node.value = value;
    });
  }
  function latestPeriod(records) {
    return records.map(item => item.period || item.period_start).filter(Boolean).sort().pop() || "—";
  }
  function renderRecords(records) {
    state.records = records;
    qs("#economicsReturnedCount").textContent = String(records.length);
    qs("#economicsLatestPeriod").textContent = latestPeriod(records);
    if (!records.length) {
      showEmpty("No matching official records", "Adjust the filters or ingest economic connector data through Platform Core.");
      renderMap([]); return;
    }
    qs("#economicsRecords").innerHTML = records.slice(0, 80).map(item => {
      const value = item.value_number !== null && item.value_number !== undefined ? fmt(item.value_number, item.unit) : text(item.value_text);
      return `<article class="economics-record" data-economic-record="${esc(item.id)}">
        <div class="economics-record-head"><span>${esc(item.family_label)}</span><span class="economics-data-state">${esc(item.data_status)}</span></div>
        <h3>${esc(item.indicator_name || item.indicator_code || item.subject || "Official statistic")}</h3>
        <strong>${esc(value)}</strong>
        <p>${esc(item.geography_name || item.geography_code || "Geography unavailable")} · ${esc(item.period || item.period_start || "Period unavailable")}</p>
        <div class="economics-record-meta"><span>${esc(item.source_id || "Official source")}</span><span>${esc(item.frequency || "Frequency unavailable")}</span><span>${esc(item.unit || "Unit unavailable")}</span></div>
        ${item.source_url ? `<a href="${esc(item.source_url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a>` : ""}
      </article>`;
    }).join("");
    renderMap(records);
    const indicator = qs("#economicsIndicator")?.value || records.find(item => item.indicator_code)?.indicator_code || "";
    const geography = qs("#economicsCountry")?.value || records.find(item => item.geography_code)?.geography_code || "";
    if (indicator) loadSeries(indicator, geography).catch(() => renderSeries([])); else renderSeries([]);
  }
  function ensureMap() {
    if (state.map || !window.L || !qs("#economicsMap")) return;
    state.map = L.map("economicsMap", {worldCopyJump: true, zoomControl: true}).setView([20, 8], 2);
    state.base = L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {attribution: "© OpenStreetMap contributors © CARTO", maxZoom: 19}).addTo(state.map);
    state.markers = L.layerGroup().addTo(state.map);
  }
  function renderMap(records) {
    ensureMap();
    if (!state.map || !state.markers) return;
    state.markers.clearLayers();
    const latest = new Map();
    records.forEach(item => {
      const code = item.geography_code;
      if (!code || !state.countries.has(code)) return;
      const previous = latest.get(code);
      const date = item.period_start || item.period || "";
      if (!previous || date > (previous.period_start || previous.period || "")) latest.set(code, item);
    });
    const bounds = [];
    latest.forEach((item, code) => {
      const country = state.countries.get(code);
      const lat = Number(country.latitude), lng = Number(country.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;
      const value = item.value_number !== null && item.value_number !== undefined ? fmt(item.value_number, item.unit) : text(item.value_text);
      const marker = L.circleMarker([lat, lng], {radius: 7, weight: 1.5, color: "#f6f8fb", fillColor: "#8b1e3f", fillOpacity: .86});
      marker.bindPopup(`<strong>${esc(country.name)}</strong><br>${esc(item.indicator_name || item.indicator_code)}<br><b>${esc(value)}</b><br>${esc(item.period || item.period_start || "") } · ${esc(item.data_status)}<br><small>${esc(item.source_id)}</small>`);
      marker.addTo(state.markers); bounds.push([lat, lng]);
    });
    if (bounds.length > 1) state.map.fitBounds(bounds, {padding: [28, 28], maxZoom: 5});
    else if (bounds.length === 1) state.map.setView(bounds[0], 4);
    else state.map.setView([20, 8], 2);
    setTimeout(() => state.map.invalidateSize(), 60);
  }
  async function loadSeries(indicator, geography = "") {
    const params = new URLSearchParams({indicator_code: indicator, limit: "160"});
    if (geography) params.set("geography_code", geography);
    const payload = await api(`/public/economics-sustainability/series?${params}`);
    renderSeries(payload.points || [], payload.latest || null);
  }
  function renderSeries(points, latest = null) {
    const box = qs("#economicsChart");
    const numeric = points.filter(point => Number.isFinite(Number(point.value_number)));
    if (!numeric.length) {
      box.innerHTML = `<div class="economics-empty"><strong>No numeric series available</strong><span>The selected official record may be textual, missing, or not yet ingested.</span></div>`;
      qs("#economicsSeriesTitle").textContent = latest?.indicator_name || "Indicator history";
      return;
    }
    const values = numeric.map(point => Number(point.value_number));
    const min = Math.min(...values), max = Math.max(...values), spread = max - min || 1;
    const width = 760, height = 250, pad = 34;
    const coordinates = numeric.map((point, index) => {
      const x = pad + (index / Math.max(numeric.length - 1, 1)) * (width - pad * 2);
      const y = height - pad - ((Number(point.value_number) - min) / spread) * (height - pad * 2);
      return {x, y, point};
    });
    const polyline = coordinates.map(item => `${item.x.toFixed(1)},${item.y.toFixed(1)}`).join(" ");
    const labelEvery = Math.max(1, Math.ceil(coordinates.length / 6));
    box.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Official indicator time series">
      <line x1="${pad}" y1="${height-pad}" x2="${width-pad}" y2="${height-pad}" class="economics-axis" />
      <line x1="${pad}" y1="${pad}" x2="${pad}" y2="${height-pad}" class="economics-axis" />
      <polyline points="${polyline}" class="economics-line" />
      ${coordinates.map((item, index) => `<circle cx="${item.x}" cy="${item.y}" r="4" class="economics-point"><title>${esc(item.point.period || item.point.period_start)}: ${esc(fmt(item.point.value_number, item.point.unit))}</title></circle>${index % labelEvery === 0 || index === coordinates.length - 1 ? `<text x="${item.x}" y="${height-8}" text-anchor="middle">${esc(String(item.point.period || "").slice(0, 10))}</text>` : ""}`).join("")}
      <text x="${pad+4}" y="${pad+10}">${esc(fmt(max, latest?.unit || numeric[0]?.unit || ""))}</text>
      <text x="${pad+4}" y="${height-pad-7}">${esc(fmt(min, latest?.unit || numeric[0]?.unit || ""))}</text>
    </svg>`;
    qs("#economicsSeriesTitle").textContent = latest?.indicator_name || qs("#economicsIndicator")?.selectedOptions?.[0]?.textContent || "Indicator history";
  }
  async function loadRecords({sync = true} = {}) {
    setStatus("Loading official economics and sustainability records", "loading");
    if (sync) syncUrl();
    const payload = await api(`/public/economics-sustainability/records?${paramsFromControls()}`);
    renderRecords(payload.records || []);
    const stateName = payload.integration?.state;
    setStatus(payload.integration?.message || `${payload.records?.length || 0} records loaded`, stateName === "connected" ? "ready" : stateName === "degraded" ? "error" : "fallback");
  }
  async function loadComparison() {
    const indicator = qs("#economicsCompareIndicator")?.value;
    const a = qs("#economicsCompareA")?.value;
    const b = qs("#economicsCompareB")?.value;
    if (!indicator || !a || !b) {
      qs("#economicsCompareResult").innerHTML = `<div class="economics-empty"><strong>Choose an indicator and two geographies</strong><span>Comparison keeps source, unit, and reporting period visible.</span></div>`; return;
    }
    if (a === b) {
      qs("#economicsCompareResult").innerHTML = `<div class="economics-empty"><strong>Choose two different geographies</strong><span>A geography cannot be compared with itself.</span></div>`; return;
    }
    qs("#economicsCompareResult").innerHTML = `<div class="economics-empty"><strong>Loading comparison</strong><span>Aligning official records without silent normalization.</span></div>`;
    const params = new URLSearchParams({indicator_code: indicator, geography_a: a, geography_b: b, limit: "120"});
    const payload = await api(`/public/economics-sustainability/compare?${params}`);
    const latest = payload.latest || {};
    qs("#economicsCompareResult").innerHTML = [a, b].map(code => {
      const item = latest[code];
      const country = state.countries.get(code);
      if (!item) return `<article><span>${esc(country?.name || code)}</span><strong>No record</strong><small>Core returned no matching observation.</small></article>`;
      const value = item.value_number !== null && item.value_number !== undefined ? fmt(item.value_number, item.unit) : text(item.value_text);
      return `<article><span>${esc(country?.name || item.geography_name || code)}</span><strong>${esc(value)}</strong><small>${esc(item.period || item.period_start || "Period unavailable")} · ${esc(item.source_id || "Official source")} · ${esc(item.data_status)}</small></article>`;
    }).join("") + `<p>${esc(payload.interpretation || "")}</p>`;
  }
  function downloadCsv() {
    if (!state.records.length) return;
    const columns = ["indicator_code","indicator_name","geography_code","geography_name","period","value_number","value_text","unit","frequency","data_status","source_id","source_url"];
    const csv = [columns.join(","), ...state.records.map(row => columns.map(column => `"${String(row[column] ?? "").replaceAll('"','""')}"`).join(","))].join("\n");
    const blob = new Blob([csv], {type: "text/csv;charset=utf-8"});
    const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "site-intelligence-economics-v2.2.0.csv"; document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }
  async function open() {
    const panel = qs("#economicsStudio"); if (!panel) return;
    panel.hidden = false; panel.setAttribute("aria-busy", "true"); document.body.classList.add("economics-route");
    try {
      const [overview, facets, countries] = await Promise.all([
        api("/public/economics-sustainability"),
        api("/public/economics-sustainability/facets"),
        api("/public/countries"),
      ]);
      renderOverview(overview); state.facets = facets; fillCountries(countries); fillFacets(facets); applyUrl(); await loadRecords({sync: false});
    } catch (error) {
      setStatus("Economics records are temporarily unavailable", "error");
      showEmpty("Economics workspace unavailable", error.message || "The public data bridge did not respond.");
    } finally {
      panel.setAttribute("aria-busy", "false"); setTimeout(() => state.map?.invalidateSize(), 100); window.dispatchEvent(new Event("resize"));
    }
  }
  function close() {
    const panel = qs("#economicsStudio"); if (panel) panel.hidden = true;
    document.body.classList.remove("economics-route");
  }
  function bind() {
    qs("#economicsApply")?.addEventListener("click", () => loadRecords());
    qs("#economicsReset")?.addEventListener("click", () => {
      ["#economicsFamily","#economicsSource","#economicsCountry","#economicsIndicator","#economicsFrequency"].forEach(selector => { if (qs(selector)) qs(selector).value = ""; });
      if (qs("#economicsSearch")) qs("#economicsSearch").value = ""; loadRecords();
    });
    qs("#economicsSearch")?.addEventListener("keydown", event => { if (event.key === "Enter") loadRecords(); });
    qs("#economicsIndicator")?.addEventListener("change", event => { state.selectedIndicator = event.target.value; });
    qs("#economicsCompareApply")?.addEventListener("click", loadComparison);
    qs("#economicsShare")?.addEventListener("click", async () => { syncUrl(); try { await navigator.clipboard.writeText(location.href); } catch {} });
    qs("#economicsExport")?.addEventListener("click", downloadCsv);
    qs("#economicsWorkbench")?.addEventListener("click", () => window.open("https://sustainablecatalyst.com/workbench/", "_blank", "noopener"));
    qs("#economicsDecisionStudio")?.addEventListener("click", () => window.open("https://sustainablecatalyst.com/decision-studio/", "_blank", "noopener"));
  }
  document.addEventListener("DOMContentLoaded", bind);
  window.SCEconomicsV220 = {open, close, status: () => ({version: VERSION, map: state.map, records: state.records.length})};
})();
