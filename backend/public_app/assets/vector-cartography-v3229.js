(function (window, document) {
  "use strict";

  const VERSION = "4.36.1";
  const TILE_SIZE = 256;
  const MAX_LAT = 85.05112878;
  const OSM_TILES = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
  const OSM_ATTRIBUTION = "© OpenStreetMap contributors";
  const managedMaps = new Map();
  const boundaryCache = { promise: null, data: null, error: null };
  let anonymousMapCount = 0;

  function dispatch(type, detail) {
    window.dispatchEvent(new CustomEvent(type, { detail: { version: VERSION, ...detail } }));
  }

  function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
  function normalizeLng(value) { return ((Number(value) + 540) % 360) - 180; }
  function containerFor(target) { return typeof target === "string" ? document.getElementById(target) : target; }
  function containerId(container) {
    if (!container) return "unknown-map";
    if (!container.id) { anonymousMapCount += 1; container.id = `scsiMap${anonymousMapCount}`; }
    return container.id;
  }
  function escapeText(value) { return String(value ?? "").replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim(); }
  function latLng(value) {
    if (Array.isArray(value)) return { lat: Number(value[0]) || 0, lng: Number(value[1]) || 0 };
    return { lat: Number(value?.lat) || 0, lng: Number(value?.lng) || 0 };
  }
  function flattenCoordinates(value, out = []) {
    if (!Array.isArray(value)) return out;
    if (value.length >= 2 && Number.isFinite(Number(value[0])) && Number.isFinite(Number(value[1]))) {
      out.push({ lat: Number(value[1]), lng: Number(value[0]) }); return out;
    }
    value.forEach(item => flattenCoordinates(item, out)); return out;
  }
  function boundsObject(points) {
    const clean = (points || []).map(latLng).filter(item => Number.isFinite(item.lat) && Number.isFinite(item.lng));
    return { _points: clean, isValid: () => clean.length > 0, pad: () => boundsObject(clean) };
  }
  function worldPoint(value, zoom) {
    const point = latLng(value);
    const size = TILE_SIZE * Math.pow(2, zoom);
    const lat = clamp(point.lat, -MAX_LAT, MAX_LAT) * Math.PI / 180;
    return {
      x: ((normalizeLng(point.lng) + 180) / 360) * size,
      y: (1 - Math.log(Math.tan(lat) + (1 / Math.cos(lat))) / Math.PI) / 2 * size,
      size,
    };
  }
  function worldToLatLng(x, y, zoom) {
    const size = TILE_SIZE * Math.pow(2, zoom);
    const lng = x / size * 360 - 180;
    const n = Math.PI - (2 * Math.PI * y / size);
    const lat = 180 / Math.PI * Math.atan(Math.sinh(n));
    return { lat: clamp(lat, -MAX_LAT, MAX_LAT), lng: normalizeLng(lng) };
  }
  function inferAssetUrl(filename) {
    const script = document.currentScript || Array.from(document.scripts).find(item => /vector-cartography-v3229\.js/.test(item.src));
    if (script?.dataset?.worldUrl && filename.includes("world-boundaries")) return script.dataset.worldUrl;
    if (script?.src) return script.src.replace(/vector-cartography-v3229\.js(?:\?.*)?$/, filename);
    return `/app/assets/${filename}`;
  }
  function loadBoundaries() {
    if (boundaryCache.data) return Promise.resolve(boundaryCache.data);
    if (boundaryCache.promise) return boundaryCache.promise;
    const url = inferAssetUrl("world-cartography-v3229.geojson");
    boundaryCache.promise = fetch(url, { cache: "force-cache", credentials: "same-origin" })
      .then(response => { if (!response.ok) throw new Error(`World boundaries returned ${response.status}`); return response.json(); })
      .then(data => { boundaryCache.data = data; dispatch("scsi:local-basemap-ready", { featureCount: data.features?.length || 0, url }); return data; })
      .catch(error => { boundaryCache.error = String(error?.message || error); dispatch("scsi:local-basemap-error", { error: boundaryCache.error, url }); return null; });
    return boundaryCache.promise;
  }
  function registerMap(map, mode) {
    const container = map?.getContainer?.() || map?._container;
    if (!container) return map;
    const id = containerId(container);
    container.classList.add("scsi-map-managed", "scsi-vector-map");
    container.dataset.scsiMapMode = mode || "self-hosted-vector-cartography";
    container.dataset.scsiMapStatus = "ready";
    container.dataset.scsiMapProvider = "sustainable-catalyst";
    managedMaps.set(id, { map, container, initializedAt: new Date().toISOString() });
    dispatch("scsi:map-initialized", { containerId: id, mode: container.dataset.scsiMapMode });
    return map;
  }

  class SelfHostedMap {
    constructor(target, options = {}) {
      this._container = containerFor(target);
      if (!this._container) throw new Error("Map container was not found.");
      this.options = options;
      this._center = { lat: 12, lng: 20 };
      this._zoom = 2;
      this._layers = new Set();
      this._events = new Map();
      this._drag = null;
      this._destroyed = false;
      this._boundaries = null;
      this._container.innerHTML = "";
      this._container.tabIndex = this._container.tabIndex >= 0 ? this._container.tabIndex : 0;
      if (!this._container.getAttribute("aria-label")) this._container.setAttribute("aria-label", "Interactive geographic intelligence map");
      this._canvas = document.createElement("div");
      this._canvas.className = "scsi-map-engine-canvas";
      this._canvas.innerHTML = '<div class="scsi-map-ocean-shading" aria-hidden="true"></div><div class="scsi-map-tile-root" aria-hidden="true"></div><svg class="scsi-map-engine-svg" role="img" aria-label="Vector map with country boundaries, labels, raster imagery, and evidence overlays"><defs><filter id="scsiBoundaryGlow"><feGaussianBlur stdDeviation="0.35" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><g class="scsi-map-grid"></g><g class="scsi-local-basemap"></g><g class="scsi-country-labels"></g><g class="scsi-map-overlay-root"></g></svg><div class="scsi-map-html-markers"></div><div class="scsi-map-engine-label"><span>VECTOR CARTOGRAPHY</span><strong>Local boundaries and labels</strong></div><div class="scsi-map-quality" aria-live="polite">Local vector context ready</div><div class="scsi-map-scale" aria-label="Map scale"></div><div class="scsi-map-coordinate-readout" aria-live="polite"></div><div class="scsi-map-attribution">Natural Earth · OpenStreetMap and NASA when available</div><div class="scsi-map-controls" role="group" aria-label="Map controls"><button type="button" data-map-zoom-in aria-label="Zoom in">+</button><button type="button" data-map-zoom-out aria-label="Zoom out">−</button><button type="button" data-map-reset aria-label="Reset world view">⌂</button></div><div class="scsi-map-popup" hidden></div>';
      this._container.appendChild(this._canvas);
      this._tileRoot = this._canvas.querySelector(".scsi-map-tile-root");
      this._svg = this._canvas.querySelector(".scsi-map-engine-svg");
      this._basemapRoot = this._canvas.querySelector(".scsi-local-basemap");
      this._labelRoot = this._canvas.querySelector(".scsi-country-labels");
      this._grid = this._canvas.querySelector(".scsi-map-grid");
      this._layerRoot = this._canvas.querySelector(".scsi-map-overlay-root");
      this._markerRoot = this._canvas.querySelector(".scsi-map-html-markers");
      this._label = this._canvas.querySelector(".scsi-map-engine-label");
      this._quality = this._canvas.querySelector(".scsi-map-quality");
      this._scale = this._canvas.querySelector(".scsi-map-scale");
      this._readout = this._canvas.querySelector(".scsi-map-coordinate-readout");
      this._popup = this._canvas.querySelector(".scsi-map-popup");
      this._bindInteraction();
      registerMap(this, "self-hosted-vector-cartography");
      loadBoundaries().then(data => {
        if (this._destroyed) return;
        this._boundaries = data;
        this._container.dataset.scsiLocalBasemap = data ? "ready" : "grid-only";
        this._redraw();
        dispatch(data ? "scsi:map-local-basemap-ready" : "scsi:map-local-basemap-fallback", { containerId: containerId(this._container) });
      });
      this._redraw();
      dispatch("scsi:map-first-party-ready", { containerId: containerId(this._container), mode: "self-hosted-vector-cartography" });
    }
    _dimensions() {
      const rect = this._container.getBoundingClientRect?.() || {};
      return { width: Math.max(320, Math.round(rect.width || this._container.clientWidth || 1000)), height: Math.max(240, Math.round(rect.height || this._container.clientHeight || 500)) };
    }
    _normalizeCenter(center) { const point = latLng(center); return { lat: clamp(point.lat, -MAX_LAT, MAX_LAT), lng: normalizeLng(point.lng) }; }
    _bindInteraction() {
      this._canvas.querySelector("[data-map-zoom-in]")?.addEventListener("click", () => this.setZoom(this._zoom + 1));
      this._canvas.querySelector("[data-map-zoom-out]")?.addEventListener("click", () => this.setZoom(this._zoom - 1));
      this._canvas.querySelector("[data-map-reset]")?.addEventListener("click", () => this.setView([12, 20], 2));
      this._container.addEventListener("wheel", event => { event.preventDefault(); this.setZoom(this._zoom + (event.deltaY < 0 ? 1 : -1)); }, { passive: false });
      this._container.addEventListener("pointerdown", event => {
        if (event.button !== 0 || event.target.closest?.("button,a,.scsi-map-popup")) return;
        const centerWorld = worldPoint(this._center, this._zoom);
        this._drag = { x: event.clientX, y: event.clientY, centerWorld };
        this._container.classList.add("is-dragging"); this._container.setPointerCapture?.(event.pointerId);
      });
      this._container.addEventListener("pointermove", event => {
        if (!this._drag) return;
        this._center = worldToLatLng(this._drag.centerWorld.x - (event.clientX - this._drag.x), this._drag.centerWorld.y - (event.clientY - this._drag.y), this._zoom);
        this._redraw(); this._emit("move");
      });
      const finish = event => { if (!this._drag) return; this._drag = null; this._container.classList.remove("is-dragging"); this._container.releasePointerCapture?.(event.pointerId); this._emit("moveend"); };
      this._container.addEventListener("pointerup", finish); this._container.addEventListener("pointercancel", finish);
      this._container.addEventListener("keydown", event => {
        if (event.key === "+" || event.key === "=") { event.preventDefault(); this.zoomIn(); }
        else if (event.key === "-") { event.preventDefault(); this.zoomOut(); }
        else if (event.key === "ArrowLeft") { event.preventDefault(); this.panBy([-64, 0]); }
        else if (event.key === "ArrowRight") { event.preventDefault(); this.panBy([64, 0]); }
        else if (event.key === "ArrowUp") { event.preventDefault(); this.panBy([0, -64]); }
        else if (event.key === "ArrowDown") { event.preventDefault(); this.panBy([0, 64]); }
        else if (event.key === "Home") { event.preventDefault(); this.setView([12, 20], 2); }
      });
      if (window.ResizeObserver) this._resizeObserver = new ResizeObserver(() => this.invalidateSize()).observe(this._container);
    }
    project(value) {
      const dimensions = this._dimensions();
      const point = worldPoint(value, this._zoom); const center = worldPoint(this._center, this._zoom);
      let dx = point.x - center.x; if (dx > point.size / 2) dx -= point.size; if (dx < -point.size / 2) dx += point.size;
      return { x: dimensions.width / 2 + dx, y: dimensions.height / 2 + (point.y - center.y) };
    }
    _drawGrid() {
      this._grid.innerHTML = ""; const ns = "http://www.w3.org/2000/svg";
      const step = this._zoom >= 5 ? 5 : this._zoom >= 4 ? 10 : this._zoom >= 3 ? 15 : 30;
      for (let lng = -180; lng <= 180; lng += step) {
        const points = []; for (let lat = -80; lat <= 80; lat += 5) { const p = this.project([lat, lng]); points.push(`${points.length ? "L" : "M"}${p.x.toFixed(1)},${p.y.toFixed(1)}`); }
        const path = document.createElementNS(ns, "path"); path.setAttribute("d", points.join(" ")); this._grid.appendChild(path);
      }
      for (let lat = -75; lat <= 75; lat += step) {
        const points = []; for (let lng = -180; lng <= 180; lng += 5) { const p = this.project([lat, lng]); points.push(`${points.length ? "L" : "M"}${p.x.toFixed(1)},${p.y.toFixed(1)}`); }
        const path = document.createElementNS(ns, "path"); path.setAttribute("d", points.join(" ")); this._grid.appendChild(path);
      }
    }
    _geometryPaths(geometry) {
      const type = geometry?.type; const c = geometry?.coordinates || [];
      if (type === "Polygon") return c;
      if (type === "MultiPolygon") return c.flat();
      if (type === "LineString") return [c];
      if (type === "MultiLineString") return c;
      return [];
    }
    _pathD(coords, close) {
      if (!Array.isArray(coords) || !coords.length) return "";
      let d = ""; let lastX = null;
      coords.forEach(coord => {
        const p = this.project([coord[1], coord[0]]);
        const jump = lastX !== null && Math.abs(p.x - lastX) > this._dimensions().width * 0.7;
        d += `${!d || jump ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)} `; lastX = p.x;
      });
      return d + (close ? "Z" : "");
    }
    _drawBoundaries() {
      this._basemapRoot.innerHTML = "";
      if (!this._boundaries?.features?.length) return;
      const ns = "http://www.w3.org/2000/svg";
      const zoomClass = this._zoom >= 6 ? "detail" : this._zoom >= 4 ? "regional" : "global";
      this._basemapRoot.setAttribute("data-zoom-class", zoomClass);
      this._boundaries.features.forEach(feature => {
        const close = /Polygon/.test(feature.geometry?.type || "");
        this._geometryPaths(feature.geometry).forEach(coords => {
          const d = this._pathD(coords, close); if (!d) return;
          const path = document.createElementNS(ns, "path"); path.setAttribute("d", d);
          const props = feature.properties || {};
          path.setAttribute("data-country", props.name || "");
          path.setAttribute("data-iso", props.iso_a3 || "");
          path.setAttribute("data-continent", props.cartography_class || "other");
          path.setAttribute("class", `scsi-country-shape scsi-continent-${props.cartography_class || "other"}`);
          const title = document.createElementNS(ns, "title"); title.textContent = `${props.name || "Country"} · local vector boundary`; path.appendChild(title);
          this._basemapRoot.appendChild(path);
        });
      });
    }
    _drawLabels() {
      this._labelRoot.innerHTML = "";
      if (!this._boundaries?.features?.length) return;
      const ns = "http://www.w3.org/2000/svg";
      const maxRank = this._zoom <= 1 ? 1 : this._zoom <= 2 ? 2 : this._zoom <= 3 ? 3 : this._zoom <= 4 ? 4 : 5;
      const dimensions = this._dimensions();
      this._boundaries.features
        .filter(feature => Number(feature.properties?.label_rank || 5) <= maxRank)
        .sort((a,b)=>Number(b.properties?.extent_score||0)-Number(a.properties?.extent_score||0))
        .slice(0, this._zoom <= 2 ? 35 : this._zoom <= 3 ? 70 : 130)
        .forEach(feature => {
          const props=feature.properties||{}; const point=this.project([props.label_lat,props.label_lng]);
          if(point.x < -80 || point.x > dimensions.width+80 || point.y < -30 || point.y > dimensions.height+30) return;
          const text=document.createElementNS(ns,"text"); text.setAttribute("x",point.x.toFixed(1)); text.setAttribute("y",point.y.toFixed(1));
          text.setAttribute("class",`scsi-country-label scsi-label-rank-${props.label_rank||5}`); text.setAttribute("text-anchor","middle");
          text.textContent=props.name||props.iso_a3||""; this._labelRoot.appendChild(text);
        });
    }
    _updateScale() {
      if(!this._scale) return;
      const center=this.project(this._center), offset=120;
      const left=this.unproject([center.x-offset/2,center.y]), right=this.unproject([center.x+offset/2,center.y]);
      const radians=v=>v*Math.PI/180, dLat=radians(right.lat-left.lat), dLng=radians(right.lng-left.lng);
      const a=Math.sin(dLat/2)**2+Math.cos(radians(left.lat))*Math.cos(radians(right.lat))*Math.sin(dLng/2)**2;
      const km=6371*2*Math.atan2(Math.sqrt(a),Math.sqrt(Math.max(0,1-a)));
      const rounded=km>=1000?Math.round(km/500)*500:km>=200?Math.round(km/100)*100:km>=50?Math.round(km/25)*25:Math.max(1,Math.round(km/5)*5);
      this._scale.innerHTML=`<span style="width:${Math.max(42,Math.min(120,120*(rounded/Math.max(km,1))))}px"></span><strong>${rounded.toLocaleString()} km</strong>`;
    }
    _updateCoordinateReadout() { if(this._readout) this._readout.textContent=`${Math.abs(this._center.lat).toFixed(2)}°${this._center.lat>=0?"N":"S"} · ${Math.abs(this._center.lng).toFixed(2)}°${this._center.lng>=0?"E":"W"} · z${this._zoom}`; }
    unproject(point) { const dimensions=this._dimensions(), center=worldPoint(this._center,this._zoom); const x=Number(point[0] ?? point.x), y=Number(point[1] ?? point.y); return worldToLatLng(center.x+(x-dimensions.width/2),center.y+(y-dimensions.height/2),this._zoom); }
    _redraw() {
      if (this._destroyed) return;
      const dimensions = this._dimensions(); this._svg.setAttribute("viewBox", `0 0 ${dimensions.width} ${dimensions.height}`);
      this._drawGrid(); this._drawBoundaries(); this._drawLabels(); this._layers.forEach(layer => layer?._redraw?.()); this._updateScale(); this._updateCoordinateReadout();
      this._container.dataset.scsiMapStatus = "ready";
      this._container.dataset.scsiMapCenter = `${this._center.lat.toFixed(3)},${this._center.lng.toFixed(3)}`;
      this._container.dataset.scsiMapZoom = String(this._zoom);
      this._container.dataset.scsiVisibleGeography = String(this._basemapRoot.querySelectorAll("path").length);
      this._container.dataset.scsiVisibleLabels = String(this._labelRoot.querySelectorAll("text").length);
    }
    setView(center, zoom) { this._center = this._normalizeCenter(center); if (Number.isFinite(Number(zoom))) this._zoom = clamp(Number(zoom), 1, 18); this._redraw(); this._emit("move"); this._emit("zoom"); this._emit("moveend"); this._emit("zoomend"); return this; }
    setZoom(zoom) { return this.setView(this._center, zoom); }
    zoomIn(delta = 1) { return this.setZoom(this._zoom + Number(delta || 1)); }
    zoomOut(delta = 1) { return this.setZoom(this._zoom - Number(delta || 1)); }
    panBy(offset) { const values = Array.isArray(offset) ? offset : [offset?.x || 0, offset?.y || 0]; const center = worldPoint(this._center, this._zoom); return this.setView(worldToLatLng(center.x + Number(values[0]), center.y + Number(values[1]), this._zoom), this._zoom); }
    panTo(center) { return this.setView(center, this._zoom); }
    flyTo(center, zoom) { return this.setView(center, zoom); }
    fitBounds(bounds, options = {}) {
      const points = Array.isArray(bounds) ? bounds.map(latLng) : bounds?._points || [];
      if (!points.length) return this;
      const minLat = Math.min(...points.map(p => p.lat)), maxLat = Math.max(...points.map(p => p.lat));
      const minLng = Math.min(...points.map(p => p.lng)), maxLng = Math.max(...points.map(p => p.lng));
      const dimensions = this._dimensions(); const padding = Number(options.padding?.[0] || 32) * 2;
      let chosen = 1;
      for (let zoom = 1; zoom <= 12; zoom += 1) {
        const a = worldPoint([minLat, minLng], zoom), b = worldPoint([maxLat, maxLng], zoom);
        if (Math.abs(b.x - a.x) <= dimensions.width - padding && Math.abs(b.y - a.y) <= dimensions.height - padding) chosen = zoom; else break;
      }
      return this.setView([(minLat + maxLat) / 2, (minLng + maxLng) / 2], chosen);
    }
    getCenter() { return { ...this._center }; } getZoom() { return this._zoom; } getContainer() { return this._container; }
    getPane(name) { if (name === "tilePane") return this._tileRoot; if (name === "overlayPane") return this._layerRoot; return this._canvas; }
    addLayer(layer) { this._layers.add(layer); layer?._attach?.(this); return this; }
    removeLayer(layer) { this._layers.delete(layer); layer?._detach?.(); return this; }
    hasLayer(layer) { return this._layers.has(layer); }
    eachLayer(callback) { this._layers.forEach(callback); return this; }
    invalidateSize() { this._redraw(); return this; }
    on(names, handler) { String(names).split(/\s+/).forEach(name => { if (!this._events.has(name)) this._events.set(name, new Set()); this._events.get(name).add(handler); }); return this; }
    off(names, handler) { String(names).split(/\s+/).forEach(name => handler ? this._events.get(name)?.delete(handler) : this._events.delete(name)); return this; }
    _emit(name, extra = {}) { (this._events.get(name) || []).forEach(handler => { try { handler({ target: this, type: name, ...extra }); } catch (_) {} }); }
    _showPopup(html, point) { if (!this._popup) return; this._popup.innerHTML = html || ""; this._popup.hidden = false; const p = this.project(point); this._popup.style.left = `${p.x}px`; this._popup.style.top = `${p.y}px`; }
    closePopup() { if (this._popup) this._popup.hidden = true; return this; }
    remove() { this._destroyed = true; this._layers.forEach(layer => layer?._detach?.()); this._layers.clear(); this._container.innerHTML = ""; managedMaps.delete(containerId(this._container)); return this; }
  }

  class SelfHostedTileLayer {
    constructor(url, options = {}) { this.url = String(url || ""); this.options = { ...options }; this._events = new Map(); this._map = null; this._root = null; this._errors = 0; this._loaded = 0; this._fallbackTried = false; this._disabled = false; }
    addTo(map) { map.addLayer(this); return this; }
    _attach(map) { this._map = map; this._root = document.createElement("div"); this._role = this.options.role || (this._isBase() ? "base" : (/gibs\.earthdata\.nasa\.gov|imagery|reflectance|temperature|thermal|ndvi/i.test(this.url) ? "imagery" : "overlay")); this._root.className = `scsi-map-tile-layer scsi-map-tile-layer--${this._role}`; this._root.dataset.tileRole=this._role; this._root.style.opacity = this.options.opacity ?? 1; map._tileRoot.appendChild(this._root); this._redraw(); }
    _detach() { this._root?.remove(); this._root = null; this._map = null; }
    _tileUrl(z, x, y) { const subs = this.options.subdomains || "abc"; const s = typeof subs === "string" ? subs[Math.abs(x + y) % subs.length] : "a"; return this.url.replace("{s}", s).replace("{z}", z).replace("{x}", x).replace("{y}", y).replace("{r}", window.devicePixelRatio > 1 ? "@2x" : ""); }
    _isBase() { return /cartocdn\.com|tile\.openstreetmap\.org/.test(this.url); }
    _redraw() {
      if (!this._map || !this._root || this._disabled) return;
      this._root.innerHTML = ""; this._errors = 0; this._loaded = 0;
      const z = clamp(Math.round(this._map.getZoom()), Number(this.options.minZoom || 0), Number(this.options.maxZoom || 19));
      const dimensions = this._map._dimensions(); const center = worldPoint(this._map.getCenter(), z); const count = Math.pow(2, z);
      const minX = Math.floor((center.x - dimensions.width / 2) / TILE_SIZE), maxX = Math.floor((center.x + dimensions.width / 2) / TILE_SIZE);
      const minY = Math.max(0, Math.floor((center.y - dimensions.height / 2) / TILE_SIZE)), maxY = Math.min(count - 1, Math.floor((center.y + dimensions.height / 2) / TILE_SIZE));
      let pending = 0;
      for (let tx = minX; tx <= maxX; tx += 1) for (let ty = minY; ty <= maxY; ty += 1) {
        pending += 1; const wrappedX = ((tx % count) + count) % count;
        const img = document.createElement("img"); img.className = "scsi-map-tile"; img.alt = ""; img.decoding = "async"; img.loading = "eager";
        img.style.left = `${tx * TILE_SIZE - center.x + dimensions.width / 2}px`; img.style.top = `${ty * TILE_SIZE - center.y + dimensions.height / 2}px`;
        const settle = ok => {
          pending -= 1; if (ok) this._loaded += 1; else { this._errors += 1; this._emit("tileerror"); }
          if (pending === 0) this._settled();
        };
        img.onload = () => settle(true); img.onerror = () => settle(false); img.src = this._tileUrl(z, wrappedX, ty); this._root.appendChild(img);
      }
      if (!pending) this._settled();
    }
    _settled() {
      if (!this._map) return; const container = this._map.getContainer();
      if (this._loaded > 0) {
        container.classList.remove("scsi-map-imagery-limited"); container.dataset.scsiMapMode = this._role === "imagery" ? "vector-plus-satellite" : "vector-plus-live-tiles"; container.dataset.scsiImageryMode = "normal"; container.dataset.scsiMapStatus = "ready";
        if(this._map._quality) this._map._quality.textContent = this._role === "imagery" ? "Satellite layer composed over vector context" : "Live tiles composed with local vector context";
        this._map._label.querySelector("strong").textContent = this._role === "imagery" ? "Satellite + vector composition" : "Live tiles + local vector context"; this._emit("load"); dispatch("scsi:map-recovered", { containerId: containerId(container), mode: container.dataset.scsiMapMode, source: this.url }); return;
      }
      if (/cartocdn\.com/.test(this.url) && !this._fallbackTried) {
        this._fallbackTried = true; const previous = this.url; this.url = OSM_TILES; dispatch("scsi:map-fallback", { containerId: containerId(container), reason: "carto-unavailable", source: previous, fallback: OSM_TILES }); this._redraw(); return;
      }
      this._disabled = true; this._root.style.display = "none";
      container.classList.add("scsi-map-imagery-limited"); container.dataset.scsiImageryMode = "limited"; container.dataset.scsiMapStatus = "ready";
      container.dataset.scsiMapMode = this._map._boundaries ? "self-hosted-vector-cartography" : "self-hosted-grid";
      if(this._map._quality) this._map._quality.textContent = this._map._boundaries ? "Local vector geography retained" : "Geographic grid retained";
      this._map._label.querySelector("strong").textContent = this._map._boundaries ? "Local boundaries and labels" : "Geographic context fallback";
      dispatch("scsi:imagery-degraded", { containerId: containerId(container), reason: this._isBase() ? "basemap-tiles-unavailable" : "optional-imagery-unavailable", source: this.url, applicationHealthy: true });
      this._emit("load");
    }
    on(name, handler) { if (!this._events.has(name)) this._events.set(name, new Set()); this._events.get(name).add(handler); return this; }
    once(name, handler) { const wrapped = event => { this._events.get(name)?.delete(wrapped); handler(event); }; return this.on(name, wrapped); }
    _emit(name) { (this._events.get(name) || []).forEach(handler => { try { handler({ target: this, type: name }); } catch (_) {} }); }
    setOpacity(value) { this.options.opacity = value; if (this._root) this._root.style.opacity = value; return this; }
    redraw() { this._disabled = false; if (this._root) this._root.style.display = ""; this._redraw(); return this; }
    bringToBack() { if (this._root?.parentNode) this._root.parentNode.prepend(this._root); return this; }
    bringToFront() { if (this._root?.parentNode) this._root.parentNode.append(this._root); return this; }
    remove() { this._map?.removeLayer(this); return this; }
  }

  class SelfHostedMarker {
    constructor(point, options = {}) { this._latlng = latLng(point); this.options = { ...options }; this._map = null; this._el = null; this._popupHtml = ""; this._events = new Map(); }
    addTo(target) { target.addLayer(this); return this; }
    _attach(map) { this._map = map; this._render(); }
    _detach() { this._el?.remove(); this._el = null; this._map = null; }
    _redraw() { if (this._map) this._render(); }
    _render() {
      this._el?.remove(); if (!this._map) return; const point = this._map.project(this._latlng); const icon = this.options.icon?.options;
      if (icon?.html) {
        const el = document.createElement("div"); el.className = `scsi-map-div-marker ${icon.className || ""}`; el.innerHTML = icon.html; el.style.left = `${point.x}px`; el.style.top = `${point.y}px`; el.tabIndex = 0; el.setAttribute("role", "button"); this._map._markerRoot.appendChild(el); this._el = el;
      } else {
        const ns = "http://www.w3.org/2000/svg"; const el = document.createElementNS(ns, "circle"); el.setAttribute("cx", point.x); el.setAttribute("cy", point.y); el.setAttribute("r", Math.max(4, Number(this.options.radius) || 7)); el.setAttribute("fill", this.options.fillColor || this.options.color || "#ff4b4b"); el.setAttribute("fill-opacity", this.options.fillOpacity ?? 0.86); el.setAttribute("stroke", this.options.color || "#ffffff"); el.setAttribute("stroke-width", this.options.weight || 1.5); el.setAttribute("opacity", this.options.opacity ?? 1); el.setAttribute("tabindex", "0"); el.setAttribute("role", "button"); this._map._layerRoot.appendChild(el); this._el = el;
      }
      this._el.setAttribute?.("aria-label", escapeText(this._popupHtml) || "Mapped record");
      this._el.addEventListener("click", event => { this._emit("click", event); this.openPopup(); });
      this._el.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); this._emit("click", event); this.openPopup(); } });
    }
    bindPopup(html) { this._popupHtml = String(html || ""); return this; } openPopup() { this._map?._showPopup(this._popupHtml, this._latlng); return this; }
    on(name, handler) { if (!this._events.has(name)) this._events.set(name, new Set()); this._events.get(name).add(handler); return this; }
    _emit(name, originalEvent) { (this._events.get(name) || []).forEach(handler => handler({ target: this, originalEvent, type: name })); }
    setStyle(style) { Object.assign(this.options, style || {}); this._redraw(); return this; } setLatLng(point) { this._latlng = latLng(point); this._redraw(); return this; }
    remove() { this._map?.removeLayer(this); return this; }
  }

  class SelfHostedLayerGroup {
    constructor(layers = []) { this._layers = new Set(layers || []); this._map = null; }
    addTo(map) { map.addLayer(this); return this; } _attach(map) { this._map = map; this._layers.forEach(layer => layer._attach?.(map)); }
    _detach() { this._layers.forEach(layer => layer._detach?.()); this._map = null; }
    addLayer(layer) { this._layers.add(layer); if (this._map) layer._attach?.(this._map); return this; }
    removeLayer(layer) { this._layers.delete(layer); layer?._detach?.(); return this; }
    clearLayers() { this._layers.forEach(layer => layer._detach?.()); this._layers.clear(); return this; }
    eachLayer(callback) { this._layers.forEach(callback); return this; } _redraw() { this._layers.forEach(layer => layer._redraw?.()); }
    remove() { this._map?.removeLayer(this); return this; }
  }

  class SelfHostedGeometryLayer {
    constructor(feature, style = {}) { this.feature = feature; this.options = style; this._map = null; this._elements = []; this._popupHtml = ""; }
    addTo(target) { target.addLayer(this); return this; } _attach(map) { this._map = map; this._render(); }
    _detach() { this._elements.forEach(el => el?.remove()); this._elements = []; this._map = null; } _redraw() { if (this._map) this._render(); }
    bindPopup(html) { this._popupHtml = String(html || ""); return this; } setStyle(style) { Object.assign(this.options, style || {}); this._redraw(); return this; }
    bringToBack() { this._elements.forEach(el => el.parentNode?.prepend(el)); return this; } bringToFront() { this._elements.forEach(el => el.parentNode?.append(el)); return this; }
    _render() {
      this._elements.forEach(el => el?.remove()); this._elements = []; if (!this._map) return;
      const geometry = this.feature?.geometry || {}; const type = geometry.type; const style = typeof this.options === "function" ? this.options(this.feature) : this.options;
      if (type === "Point") { const marker = new SelfHostedMarker([geometry.coordinates[1], geometry.coordinates[0]], style).bindPopup(this._popupHtml); marker._attach(this._map); this._elements.push(marker._el); marker._el = null; return; }
      const close = /Polygon/.test(type || ""); const lines = this._map._geometryPaths(geometry); const ns = "http://www.w3.org/2000/svg";
      lines.forEach(coords => { const d = this._map._pathD(coords, close); if (!d) return; const path = document.createElementNS(ns, "path"); path.setAttribute("d", d); path.setAttribute("fill", close ? (style.fillColor || style.color || "#7cd8ff") : "none"); path.setAttribute("fill-opacity", style.fillOpacity ?? 0.18); path.setAttribute("stroke", style.color || "#7cd8ff"); path.setAttribute("stroke-width", style.weight || 2); path.setAttribute("opacity", style.opacity ?? 0.95); const title = document.createElementNS(ns, "title"); title.textContent = escapeText(this._popupHtml) || "Spatial geometry"; path.appendChild(title); if (this._popupHtml) path.addEventListener("click", () => this._map._showPopup(this._popupHtml, flattenCoordinates(coords)[0] || this._map.getCenter())); this._map._layerRoot.appendChild(path); this._elements.push(path); });
    }
    remove() { this._map?.removeLayer(this); return this; }
  }

  class SelfHostedGeoJSON extends SelfHostedLayerGroup {
    constructor(data, options = {}) { super(); this.options = options; this._points = []; if (data) this.addData(data); }
    addData(data) {
      const features = data?.type === "FeatureCollection" ? data.features || [] : data?.type === "Feature" ? [data] : [{ type: "Feature", geometry: data, properties: {} }];
      features.forEach(feature => { const geometry = feature?.geometry; if (!geometry) return; this._points.push(...flattenCoordinates(geometry.coordinates)); if (geometry.type === "Point" && typeof this.options.pointToLayer === "function") { const marker = this.options.pointToLayer(feature, latLng([geometry.coordinates[1], geometry.coordinates[0]])); if (marker) this.addLayer(marker); } else { const style = typeof this.options.style === "function" ? this.options.style(feature) : (this.options.style || {}); const layer = new SelfHostedGeometryLayer(feature, style); if (typeof this.options.onEachFeature === "function") this.options.onEachFeature(feature, layer); this.addLayer(layer); } }); return this;
    }
    getBounds() { return boundsObject(this._points); }
  }

  const L = {
    version: `scsi-vector-${VERSION}`,
    __scsiFirstParty: true,
    __scsiSelfHosted: true,
    map: (target, options) => new SelfHostedMap(target, options),
    tileLayer: (url, options) => new SelfHostedTileLayer(url, options),
    layerGroup: layers => new SelfHostedLayerGroup(layers),
    marker: (point, options) => new SelfHostedMarker(point, options),
    circleMarker: (point, options) => new SelfHostedMarker(point, options),
    circle: (point, options) => new SelfHostedMarker(point, { ...options, radius: Math.max(5, Math.min(24, Math.sqrt(Number(options?.radius || 1000)) / 12)) }),
    divIcon: options => ({ options: options || {} }),
    geoJSON: (data, options) => new SelfHostedGeoJSON(data, options),
    latLngBounds: points => boundsObject(points),
  };
  window.L = L;
  window.SCSIMapReliability = {
    version: VERSION,
    install: () => L,
    snapshot: function () {
      const containers = Array.from(document.querySelectorAll(".scsi-map-managed"));
      const surfaces = containers.map(container => {
        const visible = Boolean(container.getClientRects?.().length);
        const localReady = container.dataset.scsiLocalBasemap === "ready" || container.dataset.scsiMapMode === "self-hosted-tiles";
        const degraded = visible && container.dataset.scsiMapStatus === "failed";
        return { id: containerId(container), mode: container.dataset.scsiMapMode || "self-hosted-vector-cartography", status: degraded ? "degraded" : "ready", degraded, imageryMode: container.dataset.scsiImageryMode || "normal", visible, localBasemap: localReady ? "ready" : (container.dataset.scsiLocalBasemap || "loading"), visibleGeography:Number(container.dataset.scsiVisibleGeography||0), visibleLabels:Number(container.dataset.scsiVisibleLabels||0), recoveryScheduled: false };
      });
      return { version: VERSION, libraryMode: "vector-cartography-engine", mapCount: containers.length, degradedCount: surfaces.filter(item => item.degraded).length, imageryLimitedCount: surfaces.filter(item => item.imageryMode === "limited").length, modes: surfaces.reduce((counts, item) => { counts[item.mode] = (counts[item.mode] || 0) + 1; return counts; }, {}), surfaces };
    },
    retry: function (id) { const item = managedMaps.get(id); if (!item) return false; item.map.invalidateSize?.(); item.map.eachLayer?.(layer => layer.redraw?.()); dispatch("scsi:map-retry", { containerId: id }); return true; },
  };
  dispatch("scsi:map-library-ready", { mode: "vector-cartography-engine", leafletVersion: L.version, firstParty: true, localBoundaries: true, labels: true, satelliteComposition: true });
})(window, document);
