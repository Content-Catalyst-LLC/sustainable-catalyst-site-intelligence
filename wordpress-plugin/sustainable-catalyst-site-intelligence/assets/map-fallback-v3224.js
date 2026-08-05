(function (window, document) {
  "use strict";

  const VERSION = "3.22.4";
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
      this._container.classList.add("scsi-map-managed", "scsi-static-map");
      this._container.dataset.scsiMapMode = "static-fallback";
      this._container.dataset.scsiMapStatus = "degraded";
      this._container.innerHTML = "";
      this._canvas = document.createElement("div");
      this._canvas.className = "scsi-static-map-canvas";
      this._canvas.innerHTML = '<svg class="scsi-static-map-svg" viewBox="0 0 1000 500" preserveAspectRatio="none" role="presentation"><g class="scsi-static-grid"></g><g class="scsi-static-layers"></g></svg><div class="scsi-static-map-label">Static geographic grid · live basemap unavailable</div><div class="scsi-static-popup" hidden></div>';
      this._container.appendChild(this._canvas);
      this._svg = this._canvas.querySelector("svg");
      this._grid = this._canvas.querySelector(".scsi-static-grid");
      this._layerRoot = this._canvas.querySelector(".scsi-static-layers");
      this._popup = this._canvas.querySelector(".scsi-static-popup");
      this._drawGrid();
      registerMap(this, "static-fallback");
      dispatch("scsi:map-fallback", { containerId: containerId(this._container), reason: "leaflet-unavailable", mode: "static" });
    }
    _drawGrid() {
      const ns = "http://www.w3.org/2000/svg";
      for (let lng = -180; lng <= 180; lng += 30) {
        const line = document.createElementNS(ns, "line");
        const x = ((lng + 180) / 360) * 1000;
        line.setAttribute("x1", x); line.setAttribute("x2", x); line.setAttribute("y1", 0); line.setAttribute("y2", 500);
        this._grid.appendChild(line);
      }
      for (let lat = -60; lat <= 60; lat += 30) {
        const line = document.createElementNS(ns, "line");
        const y = ((90 - lat) / 180) * 500;
        line.setAttribute("x1", 0); line.setAttribute("x2", 1000); line.setAttribute("y1", y); line.setAttribute("y2", y);
        this._grid.appendChild(line);
      }
    }
    project(value) {
      const point = latLng(value);
      return { x: ((point.lng + 180) / 360) * 1000, y: ((90 - point.lat) / 180) * 500 };
    }
    setView(center, zoom) {
      this._center = latLng(center);
      if (Number.isFinite(Number(zoom))) this._zoom = Number(zoom);
      this._emit("move"); this._emit("zoom");
      return this;
    }
    flyTo(center, zoom) { return this.setView(center, zoom); }
    fitBounds(bounds) {
      const points = Array.isArray(bounds) ? bounds.map(latLng) : bounds?._points || [];
      if (points.length) {
        this._center = {
          lat: points.reduce((sum, item) => sum + item.lat, 0) / points.length,
          lng: points.reduce((sum, item) => sum + item.lng, 0) / points.length,
        };
        this._zoom = points.length === 1 ? 5 : 2;
      }
      this._emit("move"); this._emit("zoom");
      return this;
    }
    getCenter() { return { ...this._center }; }
    getZoom() { return this._zoom; }
    getContainer() { return this._container; }
    addLayer(layer) { this._layers.add(layer); layer?._attach?.(this); return this; }
    removeLayer(layer) { this._layers.delete(layer); layer?._detach?.(); return this; }
    hasLayer(layer) { return this._layers.has(layer); }
    invalidateSize() { this._layers.forEach(layer => layer?._redraw?.()); return this; }
    on(names, handler) {
      String(names).split(/\s+/).forEach(name => {
        if (!this._events.has(name)) this._events.set(name, new Set());
        this._events.get(name).add(handler);
      });
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
      version: `scsi-static-${VERSION}`,
      __scsiFallback: true,
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
    dispatch("scsi:map-library-ready", { mode: "static-fallback", leafletVersion: L.version });
    return L;
  }

  window.SCSIMapReliability = {
    version: VERSION,
    install: installFallback,
    patch: patchRealLeaflet,
    snapshot: function () {
      const containers = Array.from(document.querySelectorAll(".scsi-map-managed, .scsi-static-map"));
      const surfaces = containers.map(function (container) {
        const mode = container.dataset.scsiMapMode || (container.classList.contains("scsi-static-map") ? "static-fallback" : "leaflet");
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
        libraryMode: window.L && window.L.__scsiFallback ? "static-fallback" : "leaflet",
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
