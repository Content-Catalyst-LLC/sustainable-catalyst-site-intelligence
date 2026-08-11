(function (window, document) {
  "use strict";

  const VERSION = "4.35.9";
  const OSM_TILES = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
  const ATTRIBUTION = "© OpenStreetMap contributors";
  const managedMaps = new Map();
  const recoveryTimers = new Map();
  let anonymousMapCount = 0;

  function dispatch(type, detail) {
    window.dispatchEvent(new CustomEvent(type, { detail: { version: VERSION, ...detail } }));
  }

  function containerFor(target) {
    return typeof target === "string" ? document.getElementById(target) : target;
  }

  function containerId(container) {
    if (!container) return "unknown-map";
    if (!container.id) {
      anonymousMapCount += 1;
      container.id = `scsiMap${anonymousMapCount}`;
    }
    return container.id;
  }

  function registerMap(map, mode) {
    const container = map && typeof map.getContainer === "function" ? map.getContainer() : map?._container;
    if (!container) return map;
    const id = containerId(container);
    container.classList.add("scsi-map-managed");
    if (!container.dataset.scsiMapMode) container.dataset.scsiMapMode = mode || "leaflet";
    container.dataset.scsiMapStatus = "ready";
    managedMaps.set(id, { map, container, initializedAt: new Date().toISOString() });
    dispatch("scsi:map-initialized", { containerId: id, mode: container.dataset.scsiMapMode });
    return map;
  }

  function markManagedMap(map) {
    return registerMap(map, "leaflet");
  }

  function scheduleOsmRecovery(layer, map, container) {
    const id = containerId(container);
    if (recoveryTimers.has(id)) return;
    const attempt = function () {
      if (navigator.onLine === false) {
        recoveryTimers.set(id, setTimeout(attempt, 30000));
        return;
      }
      const image = new Image();
      let settled = false;
      const finish = function (ok) {
        if (settled) return;
        settled = true;
        clearTimeout(timeout);
        if (ok) {
          const tilePane = typeof map.getPane === "function" ? map.getPane("tilePane") : null;
          if (tilePane) tilePane.style.opacity = "";
          try { layer.redraw?.(); } catch (_) {}
          container.classList.remove("scsi-map-tile-degraded", "scsi-map-grid-overlay");
          container.dataset.scsiMapMode = "leaflet-recovered";
          container.dataset.scsiMapStatus = "ready";
          recoveryTimers.delete(id);
          dispatch("scsi:map-recovered", { containerId: id, mode: "leaflet-recovered", source: OSM_TILES });
        } else {
          recoveryTimers.set(id, setTimeout(attempt, 60000));
        }
      };
      const timeout = setTimeout(function () { finish(false); }, 8000);
      image.onload = function () { finish(true); };
      image.onerror = function () { finish(false); };
      image.src = `https://tile.openstreetmap.org/0/0/0.png?scsi_probe=${Date.now()}`;
    };
    recoveryTimers.set(id, setTimeout(attempt, 30000));
  }

  function patchRealLeaflet(L) {
    if (!L || L.__scsiReliabilityPatched) return L;
    L.__scsiReliabilityPatched = true;
    const originalMap = L.map.bind(L);
    const originalTileLayer = L.tileLayer.bind(L);

    L.map = function patchedMap(target, options) {
      return markManagedMap(originalMap(target, options));
    };

    L.tileLayer = function reliableTileLayer(url, options) {
      const layer = originalTileLayer(url, options);
      const source = String(url || "");
      const isCarto = source.includes("basemaps.cartocdn.com");
      const isOsm = source.includes("tile.openstreetmap.org");
      let errors = 0;
      let fallbackActivated = false;

      layer.on("tileerror", function () {
        errors += 1;
        const map = layer._map;
        const container = map && typeof map.getContainer === "function" ? map.getContainer() : null;
        const id = containerId(container);
        if (container) { container.classList.add("scsi-map-tile-degraded"); container.dataset.scsiMapStatus = "degraded"; }
        if (errors === 1) dispatch("scsi:map-degraded", { containerId: id, reason: "tile-error", source });

        if (isCarto && errors >= 4 && !fallbackActivated && map) {
          fallbackActivated = true;
          try { map.removeLayer(layer); } catch (_) {}
          const fallback = originalTileLayer(OSM_TILES, {
            attribution: ATTRIBUTION,
            maxZoom: 19,
            crossOrigin: true,
          });
          fallback.addTo(map);
          if (typeof fallback.bringToBack === "function") fallback.bringToBack();
          if (container) {
            container.classList.add("scsi-map-tile-fallback");
            container.dataset.scsiMapMode = "openstreetmap-fallback";
          }
          dispatch("scsi:map-fallback", { containerId: containerId(container), reason: "carto-unavailable", source, fallback: OSM_TILES });
        } else if (isOsm && errors >= 4 && !fallbackActivated && map) {
          fallbackActivated = true;
          const tilePane = typeof map.getPane === "function" ? map.getPane("tilePane") : null;
          if (tilePane) tilePane.style.opacity = "0";
          if (container) {
            container.classList.add("scsi-map-grid-overlay");
            container.dataset.scsiMapMode = "grid-overlay";
          }
          dispatch("scsi:map-fallback", { containerId: containerId(container), reason: "openstreetmap-unavailable", source, fallback: "first-party-geographic-grid" });
          if (container) scheduleOsmRecovery(layer, map, container);
        } else if (!isCarto && !isOsm && errors === 4) {
          if (container) container.dataset.scsiImageryMode = "degraded";
          dispatch("scsi:imagery-degraded", { containerId: containerId(container), reason: "imagery-tile-error", source });
        }
      });

      layer.on("load", function () {
        const map = layer._map;
        const container = map && typeof map.getContainer === "function" ? map.getContainer() : null;
        if (container) {
          const wasDegraded = container.classList.contains("scsi-map-tile-degraded");
          container.classList.remove("scsi-map-tile-degraded");
          container.dataset.scsiMapStatus = "ready";
          if (wasDegraded) dispatch("scsi:map-recovered", { containerId: containerId(container), mode: container.dataset.scsiMapMode || "leaflet", source });
        }
      });
      return layer;
    };

    dispatch("scsi:map-library-ready", { mode: "leaflet", leafletVersion: L.version || "unknown" });
    return L;
  }

  function escapeText(value) {
    return String(value ?? "").replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
  }

  function latLng(value) {
    if (Array.isArray(value)) return { lat: Number(value[0]) || 0, lng: Number(value[1]) || 0 };
    return { lat: Number(value?.lat) || 0, lng: Number(value?.lng) || 0 };
  }

  function flattenCoordinates(value, out = []) {
    if (!Array.isArray(value)) return out;
    if (value.length >= 2 && Number.isFinite(Number(value[0])) && Number.isFinite(Number(value[1]))) {
      out.push([Number(value[1]), Number(value[0])]);
      return out;
    }
    value.forEach(item => flattenCoordinates(item, out));
    return out;
  }

  function boundsObject(points) {
    const clean = (points || []).map(latLng).filter(item => Number.isFinite(item.lat) && Number.isFinite(item.lng));
    return {
      _points: clean,
      isValid: () => clean.length > 0,
      pad: () => boundsObject(clean),
    };
  }

  class StaticMap {
    constructor(target, options = {}) {
      this._container = containerFor(target);
      if (!this._container) throw new Error("Map container was not found.");
      this.options = options;
      this._center = { lat: 12, lng: 20 };
      this._zoom = 2;
      this._layers = new Set();
      this._events = new Map();
      this._drag = null;
      this._container.classList.add("scsi-map-managed", "scsi-static-map", "scsi-first-party-map");
      this._container.dataset.scsiMapMode = "first-party-interactive";
      this._container.dataset.scsiMapStatus = "ready";
      this._container.dataset.scsiMapProvider = "sustainable-catalyst";
      this._container.innerHTML = "";
      this._container.tabIndex = this._container.tabIndex >= 0 ? this._container.tabIndex : 0;
      if (!this._container.getAttribute("aria-label")) this._container.setAttribute("aria-label", "Interactive geographic evidence map");
      this._canvas = document.createElement("div");
      this._canvas.className = "scsi-static-map-canvas";
      this._canvas.innerHTML = '<svg class="scsi-static-map-svg" viewBox="0 0 1000 500" preserveAspectRatio="none" role="presentation"><g class="scsi-static-grid"></g><g class="scsi-static-layers"></g></svg><div class="scsi-static-map-label">First-party interactive map · verified overlays</div><div class="scsi-map-controls" role="group" aria-label="Map controls"><button type="button" data-map-zoom-in aria-label="Zoom in">+</button><button type="button" data-map-zoom-out aria-label="Zoom out">−</button><button type="button" data-map-reset aria-label="Reset world view">⌂</button></div><div class="scsi-static-popup" hidden></div>';
      this._container.appendChild(this._canvas);
      this._svg = this._canvas.querySelector("svg");
      this._grid = this._canvas.querySelector(".scsi-static-grid");
      this._layerRoot = this._canvas.querySelector(".scsi-static-layers");
      this._popup = this._canvas.querySelector(".scsi-static-popup");
      this._bindInteraction();
      this._redraw();
      registerMap(this, "first-party-interactive");
      dispatch("scsi:map-first-party-ready", { containerId: containerId(this._container), mode: "first-party-interactive" });
    }
    _normalizeCenter(center) {
      const point = latLng(center);
      return {
        lat: Math.max(-85, Math.min(85, point.lat)),
        lng: ((point.lng + 540) % 360) - 180,
      };
    }
    _scale() { return Math.pow(2, Math.max(-1, Math.min(8, this._zoom)) - 2); }
    _bindInteraction() {
      this._canvas.querySelector("[data-map-zoom-in]")?.addEventListener("click", () => this.setZoom(this._zoom + 1));
      this._canvas.querySelector("[data-map-zoom-out]")?.addEventListener("click", () => this.setZoom(this._zoom - 1));
      this._canvas.querySelector("[data-map-reset]")?.addEventListener("click", () => this.setView([12, 20], 2));
      this._container.addEventListener("wheel", event => {
        event.preventDefault();
        this.setZoom(this._zoom + (event.deltaY < 0 ? 1 : -1));
      }, { passive: false });
      this._container.addEventListener("pointerdown", event => {
        if (event.button !== 0 || event.target.closest?.("button,a")) return;
        this._drag = { x: event.clientX, y: event.clientY, center: { ...this._center } };
        this._container.classList.add("is-dragging");
        this._container.setPointerCapture?.(event.pointerId);
      });
      this._container.addEventListener("pointermove", event => {
        if (!this._drag) return;
        const scale = this._scale();
        const dx = event.clientX - this._drag.x;
        const dy = event.clientY - this._drag.y;
        this._center = this._normalizeCenter({
          lng: this._drag.center.lng - (dx / Math.max(1, this._container.clientWidth)) * (360 / scale),
          lat: this._drag.center.lat + (dy / Math.max(1, this._container.clientHeight)) * (180 / scale),
        });
        this._redraw();
        this._emit("move");
      });
      const finishDrag = event => {
        if (!this._drag) return;
        this._drag = null;
        this._container.classList.remove("is-dragging");
        this._container.releasePointerCapture?.(event.pointerId);
        this._emit("moveend");
      };
      this._container.addEventListener("pointerup", finishDrag);
      this._container.addEventListener("pointercancel", finishDrag);
      this._container.addEventListener("keydown", event => {
        const step = 24;
        if (event.key === "+" || event.key === "=") { event.preventDefault(); this.setZoom(this._zoom + 1); }
        else if (event.key === "-") { event.preventDefault(); this.setZoom(this._zoom - 1); }
        else if (event.key === "ArrowLeft") { event.preventDefault(); this.panBy([step, 0]); }
        else if (event.key === "ArrowRight") { event.preventDefault(); this.panBy([-step, 0]); }
        else if (event.key === "ArrowUp") { event.preventDefault(); this.panBy([0, step]); }
        else if (event.key === "ArrowDown") { event.preventDefault(); this.panBy([0, -step]); }
        else if (event.key === "Home") { event.preventDefault(); this.setView([12, 20], 2); }
      });
    }
    _drawGrid() {
      if (!this._grid) return;
      this._grid.innerHTML = "";
      const ns = "http://www.w3.org/2000/svg";
      const step = this._zoom >= 5 ? 5 : this._zoom >= 4 ? 10 : this._zoom >= 3 ? 15 : 30;
      for (let lng = -180; lng <= 180; lng += step) {
        const projected = this.project([0, lng]);
        if (projected.x < -2 || projected.x > 1002) continue;
        const line = document.createElementNS(ns, "line");
        line.setAttribute("x1", projected.x); line.setAttribute("x2", projected.x); line.setAttribute("y1", 0); line.setAttribute("y2", 500);
        this._grid.appendChild(line);
      }
      for (let lat = -90; lat <= 90; lat += step) {
        const projected = this.project([lat, this._center.lng]);
        if (projected.y < -2 || projected.y > 502) continue;
        const line = document.createElementNS(ns, "line");
        line.setAttribute("x1", 0); line.setAttribute("x2", 1000); line.setAttribute("y1", projected.y); line.setAttribute("y2", projected.y);
        this._grid.appendChild(line);
      }
    }
    project(value) {
      const point = latLng(value);
      const scale = this._scale();
      let deltaLng = point.lng - this._center.lng;
      if (deltaLng > 180) deltaLng -= 360;
      if (deltaLng < -180) deltaLng += 360;
      return {
        x: 500 + (deltaLng / 360) * 1000 * scale,
        y: 250 + ((this._center.lat - point.lat) / 180) * 500 * scale,
      };
    }
    _redraw() {
      this._drawGrid();
      this._layers.forEach(layer => layer?._redraw?.());
      this._container.dataset.scsiMapStatus = "ready";
      this._container.dataset.scsiMapCenter = `${this._center.lat.toFixed(3)},${this._center.lng.toFixed(3)}`;
      this._container.dataset.scsiMapZoom = String(this._zoom);
    }
    setView(center, zoom) {
      this._center = this._normalizeCenter(center);
      if (Number.isFinite(Number(zoom))) this._zoom = Math.max(1, Math.min(8, Number(zoom)));
      this._redraw();
      this._emit("move"); this._emit("zoom"); this._emit("moveend"); this._emit("zoomend");
      return this;
    }
    setZoom(zoom) { return this.setView(this._center, zoom); }
    zoomIn(delta = 1) { return this.setZoom(this._zoom + Number(delta || 1)); }
    zoomOut(delta = 1) { return this.setZoom(this._zoom - Number(delta || 1)); }
    panBy(offset) {
      const values = Array.isArray(offset) ? offset : [offset?.x || 0, offset?.y || 0];
      const scale = this._scale();
      return this.setView({
        lng: this._center.lng - (Number(values[0]) / Math.max(1, this._container.clientWidth)) * (360 / scale),
        lat: this._center.lat + (Number(values[1]) / Math.max(1, this._container.clientHeight)) * (180 / scale),
      }, this._zoom);
    }
    panTo(center) { return this.setView(center, this._zoom); }
    flyTo(center, zoom) { return this.setView(center, zoom); }
    fitBounds(bounds) {
      const points = Array.isArray(bounds) ? bounds.map(latLng) : bounds?._points || [];
      if (points.length) {
        const minLat = Math.min(...points.map(item => item.lat));
        const maxLat = Math.max(...points.map(item => item.lat));
        const minLng = Math.min(...points.map(item => item.lng));
        const maxLng = Math.max(...points.map(item => item.lng));
        const latSpan = Math.max(1, maxLat - minLat);
        const lngSpan = Math.max(1, maxLng - minLng);
        const scale = Math.max(0.5, Math.min(32, Math.min(145 / latSpan, 300 / lngSpan)));
        this._center = this._normalizeCenter({ lat: (minLat + maxLat) / 2, lng: (minLng + maxLng) / 2 });
        this._zoom = Math.max(1, Math.min(7, Math.round(2 + Math.log2(scale))));
      }
      this._redraw(); this._emit("move"); this._emit("zoom"); this._emit("moveend"); this._emit("zoomend");
      return this;
    }
    getCenter() { return { ...this._center }; }
    getZoom() { return this._zoom; }
    getContainer() { return this._container; }
    addLayer(layer) { this._layers.add(layer); layer?._attach?.(this); return this; }
    removeLayer(layer) { this._layers.delete(layer); layer?._detach?.(); return this; }
    hasLayer(layer) { return this._layers.has(layer); }
    invalidateSize() { this._redraw(); return this; }
    on(names, handler) {
      String(names).split(/\s+/).forEach(name => {
        if (!this._events.has(name)) this._events.set(name, new Set());
        this._events.get(name).add(handler);
      });
      return this;
    }
    off(names, handler) {
      String(names).split(/\s+/).forEach(name => handler ? this._events.get(name)?.delete(handler) : this._events.delete(name));
      return this;
    }
    _emit(name) { (this._events.get(name) || []).forEach(handler => { try { handler({ target: this, type: name }); } catch (_) {} }); }
    _showPopup(html, point) {
      if (!this._popup) return;
      this._popup.innerHTML = html || "";
      this._popup.hidden = false;
      if (point) {
        const projected = this.project(point);
        this._popup.style.left = `${Math.max(4, Math.min(92, projected.x / 10))}%`;
        this._popup.style.top = `${Math.max(4, Math.min(88, projected.y / 5))}%`;
      }
    }
    closePopup() { if (this._popup) this._popup.hidden = true; return this; }
  }

  class StaticTileLayer {
    constructor(url, options = {}) { this.url = url; this.options = options; this._events = new Map(); this._map = null; }
    addTo(map) { map.addLayer(this); return this; }
    _attach(map) { this._map = map; setTimeout(() => this._emit("load"), 0); }
    _detach() { this._map = null; }
    on(name, handler) { if (!this._events.has(name)) this._events.set(name, new Set()); this._events.get(name).add(handler); return this; }
    once(name, handler) { const wrapped = event => { this._events.get(name)?.delete(wrapped); handler(event); }; return this.on(name, wrapped); }
    _emit(name) { (this._events.get(name) || []).forEach(handler => handler({ target: this, type: name })); }
    setOpacity(value) { this.options.opacity = value; return this; }
    bringToBack() { return this; }
    bringToFront() { return this; }
    remove() { this._map?.removeLayer(this); return this; }
  }

  class StaticMarker {
    constructor(point, options = {}) {
      this._latlng = latLng(point); this.options = { ...options }; this._map = null; this._group = null; this._el = null;
      this._popupHtml = ""; this._events = new Map();
    }
    addTo(target) { target.addLayer(this); return this; }
    _attach(map) { this._map = map; this._render(); }
    _detach() { this._el?.remove(); this._el = null; this._map = null; }
    _redraw() { if (this._map) this._render(); }
    _render() {
      this._el?.remove();
      if (!this._map) return;
      const ns = "http://www.w3.org/2000/svg";
      const point = this._map.project(this._latlng);
      const circle = document.createElementNS(ns, "circle");
      circle.setAttribute("cx", point.x); circle.setAttribute("cy", point.y);
      circle.setAttribute("r", Math.max(4, Number(this.options.radius) || 7));
      circle.setAttribute("fill", this.options.fillColor || this.options.color || "#ff4b4b");
      circle.setAttribute("fill-opacity", this.options.fillOpacity ?? 0.86);
      circle.setAttribute("stroke", this.options.color || "#ffffff");
      circle.setAttribute("stroke-width", this.options.weight || 1.5);
      circle.setAttribute("opacity", this.options.opacity ?? 1);
      circle.setAttribute("tabindex", "0");
      circle.setAttribute("role", "button");
      const title = document.createElementNS(ns, "title"); title.textContent = escapeText(this._popupHtml) || "Mapped record"; circle.appendChild(title);
      circle.addEventListener("click", event => { this._emit("click", event); this.openPopup(); });
      circle.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); this._emit("click", event); this.openPopup(); } });
      this._map._layerRoot.appendChild(circle); this._el = circle;
    }
    bindPopup(html) { this._popupHtml = String(html || ""); return this; }
    openPopup() { this._map?._showPopup(this._popupHtml, this._latlng); return this; }
    on(name, handler) { if (!this._events.has(name)) this._events.set(name, new Set()); this._events.get(name).add(handler); return this; }
    _emit(name, originalEvent) { (this._events.get(name) || []).forEach(handler => handler({ target: this, originalEvent, type: name })); }
    setStyle(style) { Object.assign(this.options, style || {}); this._redraw(); return this; }
    setLatLng(point) { this._latlng = latLng(point); this._redraw(); return this; }
  }

  class StaticLayerGroup {
    constructor(layers = []) { this._layers = new Set(layers); this._map = null; }
    addTo(map) { map.addLayer(this); return this; }
    _attach(map) { this._map = map; this._layers.forEach(layer => layer._attach?.(map)); }
    _detach() { this._layers.forEach(layer => layer._detach?.()); this._map = null; }
    addLayer(layer) { this._layers.add(layer); if (this._map) layer._attach?.(this._map); return this; }
    removeLayer(layer) { this._layers.delete(layer); layer?._detach?.(); return this; }
    clearLayers() { this._layers.forEach(layer => layer._detach?.()); this._layers.clear(); return this; }
    eachLayer(callback) { this._layers.forEach(callback); return this; }
    _redraw() { this._layers.forEach(layer => layer._redraw?.()); }
  }

  class StaticGeometryLayer {
    constructor(feature, style = {}) { this.feature = feature; this.options = style; this._map = null; this._elements = []; this._popupHtml = ""; }
    addTo(target) { target.addLayer(this); return this; }
    _attach(map) { this._map = map; this._render(); }
    _detach() { this._elements.forEach(el => el.remove()); this._elements = []; this._map = null; }
    _redraw() { if (this._map) this._render(); }
    bindPopup(html) { this._popupHtml = String(html || ""); return this; }
    _render() {
      this._detachElements(); if (!this._map) return;
      const geometry = this.feature?.geometry || {};
      const type = geometry.type;
      const style = typeof this.options === "function" ? this.options(this.feature) : this.options;
      if (type === "Point") {
        const marker = new StaticMarker([geometry.coordinates[1], geometry.coordinates[0]], style).bindPopup(this._popupHtml);
        marker._attach(this._map); this._elements.push(marker._el); marker._el = null; return;
      }
      const lines = [];
      if (type === "LineString") lines.push(geometry.coordinates);
      if (type === "MultiLineString" || type === "Polygon") lines.push(...geometry.coordinates);
      if (type === "MultiPolygon") geometry.coordinates.forEach(poly => lines.push(...poly));
      const ns = "http://www.w3.org/2000/svg";
      lines.forEach(coords => {
        const path = document.createElementNS(ns, "path");
        const d = (coords || []).map((coord, index) => {
          const point = this._map.project([coord[1], coord[0]]);
          return `${index ? "L" : "M"}${point.x.toFixed(2)},${point.y.toFixed(2)}`;
        }).join(" ") + ((type === "Polygon" || type === "MultiPolygon") ? " Z" : "");
        path.setAttribute("d", d);
        path.setAttribute("fill", (type === "Polygon" || type === "MultiPolygon") ? (style.fillColor || style.color || "#7cd8ff") : "none");
        path.setAttribute("fill-opacity", style.fillOpacity ?? 0.18);
        path.setAttribute("stroke", style.color || "#7cd8ff");
        path.setAttribute("stroke-width", style.weight || 2);
        path.setAttribute("opacity", style.opacity ?? 0.95);
        const title = document.createElementNS(ns, "title"); title.textContent = escapeText(this._popupHtml) || "Spatial geometry"; path.appendChild(title);
        this._map._layerRoot.appendChild(path); this._elements.push(path);
      });
    }
    _detachElements() { this._elements.forEach(el => el?.remove()); this._elements = []; }
  }

  class StaticGeoJSON extends StaticLayerGroup {
    constructor(data, options = {}) { super(); this.options = options; this._points = []; if (data) this.addData(data); }
    addData(data) {
      const features = data?.type === "FeatureCollection" ? data.features || [] : data?.type === "Feature" ? [data] : [{ type: "Feature", geometry: data, properties: {} }];
      features.forEach(feature => {
        const geometry = feature?.geometry;
        if (!geometry) return;
        this._points.push(...flattenCoordinates(geometry.coordinates));
        if (geometry.type === "Point" && typeof this.options.pointToLayer === "function") {
          const marker = this.options.pointToLayer(feature, latLng([geometry.coordinates[1], geometry.coordinates[0]]));
          if (marker) this.addLayer(marker);
        } else {
          const style = typeof this.options.style === "function" ? this.options.style(feature) : (this.options.style || {});
          const layer = new StaticGeometryLayer(feature, style);
          if (typeof this.options.onEachFeature === "function") this.options.onEachFeature(feature, layer);
          this.addLayer(layer);
        }
      });
      return this;
    }
    getBounds() { return boundsObject(this._points); }
  }

  function installFallback() {
    if (window.L) return patchRealLeaflet(window.L);
    const L = {
      version: `scsi-first-party-${VERSION}`,
      __scsiFallback: true,
      __scsiFirstParty: true,
      map: (target, options) => new StaticMap(target, options),
      tileLayer: (url, options) => new StaticTileLayer(url, options),
      layerGroup: layers => new StaticLayerGroup(layers),
      marker: (point, options) => new StaticMarker(point, options),
      circleMarker: (point, options) => new StaticMarker(point, options),
      circle: (point, options) => new StaticMarker(point, { ...options, radius: Math.max(5, Math.min(18, Math.sqrt(Number(options?.radius || 1000)) / 12)) }),
      divIcon: options => ({ options: options || {} }),
      geoJSON: (data, options) => new StaticGeoJSON(data, options),
      latLngBounds: points => boundsObject(points),
    };
    window.L = L;
    dispatch("scsi:map-library-ready", { mode: "first-party-interactive", leafletVersion: L.version, firstParty: true });
    return L;
  }

  window.SCSIMapReliability = {
    version: VERSION,
    install: installFallback,
    patch: patchRealLeaflet,
    snapshot: function () {
      const containers = Array.from(document.querySelectorAll(".scsi-map-managed, .scsi-static-map"));
      const surfaces = containers.map(function (container) {
        const mode = container.dataset.scsiMapMode || (container.classList.contains("scsi-static-map") ? "first-party-interactive" : "leaflet");
        const degraded = container.dataset.scsiMapStatus === "degraded" || container.classList.contains("scsi-map-tile-degraded") || container.classList.contains("scsi-map-grid-overlay");
        return {
          id: containerId(container),
          mode,
          status: degraded ? "degraded" : "ready",
          degraded,
          imageryMode: container.dataset.scsiImageryMode || "normal",
          visible: Boolean(container.getClientRects?.().length),
          recoveryScheduled: recoveryTimers.has(containerId(container)),
        };
      });
      return {
        version: VERSION,
        libraryMode: window.L && window.L.__scsiFirstParty ? "first-party-interactive" : window.L && window.L.__scsiFallback ? "geographic-fallback" : "leaflet",
        mapCount: containers.length,
        degradedCount: surfaces.filter(function (surface) { return surface.degraded; }).length,
        modes: surfaces.reduce(function (counts, surface) {
          counts[surface.mode] = (counts[surface.mode] || 0) + 1;
          return counts;
        }, {}),
        surfaces,
      };
    },
    retry: function (id) {
      const item = managedMaps.get(id);
      if (!item) return false;
      try { item.map.invalidateSize?.(); } catch (_) {}
      item.container.dataset.scsiMapStatus = "checking";
      dispatch("scsi:map-retry", { containerId: id });
      return true;
    },
  };

  installFallback();
})(window, document);
