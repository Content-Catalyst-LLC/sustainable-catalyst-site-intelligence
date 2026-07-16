from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
from typing import Any, Callable, Iterable
from uuid import uuid4

from .config import Settings
from .version import APP_VERSION

RELEASE_VERSION = "2.22.0"
SCHEMA_VERSION = "sc-site-intelligence-spatial-evidence/1.0"
AREA_SCHEMA = "sc-site-intelligence-area-of-interest/1.0"
DATASET_SCHEMA = "sc-site-intelligence-spatial-dataset/1.0"
ANALYSIS_SCHEMA = "sc-site-intelligence-spatial-analysis/1.0"
EARTH_RADIUS_KM = 6371.0088
_SECRET_KEY = re.compile(r"(?:token|secret|password|authorization|api[_-]?key|email|phone|user[_-]?id)", re.I)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    root = Path(__file__).resolve().parents[2]
    return root / path


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _safe_id(value: str, fallback: str = "record") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(value or "").strip()).strip("-.")
    return (cleaned or fallback)[:120]


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _read_jsonl(path: Path, limit: int = 10000) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    except (FileNotFoundError, OSError):
        return []
    rows: list[dict[str, Any]] = []
    for line in lines:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): ("[redacted]" if _SECRET_KEY.search(str(key)) else _redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _get_path(value: Any, path: str) -> Any:
    current = value
    for part in [item for item in path.split(".") if item]:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(h)))


def _valid_position(position: Any) -> tuple[float, float]:
    if not isinstance(position, (list, tuple)) or len(position) < 2:
        raise ValueError("GeoJSON positions require longitude and latitude.")
    lon = _number(position[0])
    lat = _number(position[1])
    if lon is None or lat is None or not -180 <= lon <= 180 or not -90 <= lat <= 90:
        raise ValueError("Coordinates must use WGS84 longitude [-180,180] and latitude [-90,90].")
    return lon, lat


def _iter_positions(geometry: dict[str, Any]) -> Iterable[tuple[float, float]]:
    kind = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if kind == "Point":
        yield _valid_position(coordinates)
    elif kind in {"MultiPoint", "LineString"}:
        for position in coordinates or []:
            yield _valid_position(position)
    elif kind in {"MultiLineString", "Polygon"}:
        for group in coordinates or []:
            for position in group or []:
                yield _valid_position(position)
    elif kind == "MultiPolygon":
        for polygon in coordinates or []:
            for ring in polygon or []:
                for position in ring or []:
                    yield _valid_position(position)
    else:
        raise ValueError(f"Unsupported GeoJSON geometry type: {kind}")


def _geometry_bbox(geometry: dict[str, Any]) -> list[float]:
    positions = list(_iter_positions(geometry))
    if not positions:
        raise ValueError("Geometry has no positions.")
    lons = [item[0] for item in positions]
    lats = [item[1] for item in positions]
    return [min(lons), min(lats), max(lons), max(lats)]


def _bbox_intersects(a: list[float], b: list[float]) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _point_in_ring(point: tuple[float, float], ring: list[list[float]]) -> bool:
    x, y = point
    vertices = [_valid_position(item) for item in ring]
    if len(vertices) < 3:
        return False
    inside = False
    j = len(vertices) - 1
    for i, (xi, yi) in enumerate(vertices):
        xj, yj = vertices[j]
        on_edge = abs((y - yi) * (xj - xi) - (x - xi) * (yj - yi)) < 1e-10 and min(xi, xj) - 1e-10 <= x <= max(xi, xj) + 1e-10 and min(yi, yj) - 1e-10 <= y <= max(yi, yj) + 1e-10
        if on_edge:
            return True
        if (yi > y) != (yj > y):
            cross_x = (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi
            if x < cross_x:
                inside = not inside
        j = i
    return inside


def _point_in_polygon(point: tuple[float, float], coordinates: list[Any]) -> bool:
    if not coordinates or not _point_in_ring(point, coordinates[0]):
        return False
    return not any(_point_in_ring(point, hole) for hole in coordinates[1:])


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])


def _on_segment(a: tuple[float, float], b: tuple[float, float], p: tuple[float, float]) -> bool:
    return (
        min(a[0], b[0]) - 1e-12 <= p[0] <= max(a[0], b[0]) + 1e-12
        and min(a[1], b[1]) - 1e-12 <= p[1] <= max(a[1], b[1]) + 1e-12
    )


def _segments_intersect(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float], d: tuple[float, float]) -> bool:
    o1, o2, o3, o4 = _orientation(a, b, c), _orientation(a, b, d), _orientation(c, d, a), _orientation(c, d, b)
    eps = 1e-12
    if o1 * o2 < -eps and o3 * o4 < -eps:
        return True
    if abs(o1) <= eps and _on_segment(a, b, c):
        return True
    if abs(o2) <= eps and _on_segment(a, b, d):
        return True
    if abs(o3) <= eps and _on_segment(c, d, a):
        return True
    if abs(o4) <= eps and _on_segment(c, d, b):
        return True
    return False


def _segments(geometry: dict[str, Any]) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    kind = geometry.get("type")
    coords = geometry.get("coordinates") or []
    groups: list[list[Any]] = []
    if kind == "LineString":
        groups = [coords]
    elif kind in {"MultiLineString", "Polygon"}:
        groups = coords
    elif kind == "MultiPolygon":
        groups = [ring for polygon in coords for ring in polygon]
    return [(a, b) for group in groups for a, b in zip([_valid_position(v) for v in group], [_valid_position(v) for v in group][1:])]


def _bbox_polygon(bbox: list[float]) -> dict[str, Any]:
    west, south, east, north = bbox
    return {"type": "Polygon", "coordinates": [[[west, south], [east, south], [east, north], [west, north], [west, south]]]}


def _polygon_area_sq_km(geometry: dict[str, Any]) -> float | None:
    if geometry.get("type") != "Polygon" or not geometry.get("coordinates"):
        return None
    ring = [_valid_position(item) for item in geometry["coordinates"][0]]
    if len(ring) < 4:
        return None
    mean_lat = math.radians(sum(item[1] for item in ring) / len(ring))
    scale_x = 111.320 * math.cos(mean_lat)
    scale_y = 110.574
    area = 0.0
    for (lon1, lat1), (lon2, lat2) in zip(ring, ring[1:]):
        area += (lon1 * scale_x) * (lat2 * scale_y) - (lon2 * scale_x) * (lat1 * scale_y)
    return abs(area) / 2


def _geometry_intersects_polygon(geometry: dict[str, Any], polygon: dict[str, Any]) -> bool:
    if not _bbox_intersects(_geometry_bbox(geometry), _geometry_bbox(polygon)):
        return False
    polygon_coords = polygon.get("coordinates") or []
    if any(_point_in_polygon(point, polygon_coords) for point in _iter_positions(geometry)):
        return True
    geom_type = geometry.get("type")
    if geom_type == "Polygon":
        geom_coords = geometry.get("coordinates") or []
        if any(_point_in_polygon(point, geom_coords) for point in _iter_positions(polygon)):
            return True
    if geom_type == "MultiPolygon":
        for poly in geometry.get("coordinates") or []:
            if any(_point_in_polygon(point, poly) for point in _iter_positions(polygon)):
                return True
    return any(_segments_intersect(a, b, c, d) for a, b in _segments(geometry) for c, d in _segments(polygon))


def _representative_points(geometry: dict[str, Any]) -> list[tuple[float, float]]:
    positions = list(_iter_positions(geometry))
    if not positions:
        return []
    if geometry.get("type") == "Point":
        return positions
    centroid = (sum(item[0] for item in positions) / len(positions), sum(item[1] for item in positions) / len(positions))
    return positions + [centroid]


def _feature_id(feature: dict[str, Any], index: int) -> str:
    properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    candidate = feature.get("id") or properties.get("id") or properties.get("identifier")
    return _safe_id(str(candidate or f"feature-{index}-{_digest(feature)[:12]}"), f"feature-{index}")


@dataclass(frozen=True)
class Area:
    area_id: str
    geometry: dict[str, Any]
    mode: str
    center: tuple[float, float] | None = None
    radius_km: float | None = None


class SpatialEvidenceStudio:
    def __init__(self, settings: Settings, now_fn: Callable[[], datetime] = _utc_now) -> None:
        self.settings = settings
        self.now_fn = now_fn
        self.policy_path = _resolve_path(settings.spatial_evidence_policy_path)
        self.catalog_path = _resolve_path(settings.spatial_evidence_layer_catalog_path)
        self.root = _resolve_path(settings.spatial_evidence_root_path)
        self.areas_path = _resolve_path(settings.spatial_evidence_areas_path)
        self.datasets_path = _resolve_path(settings.spatial_evidence_datasets_path)
        self.analysis_path = _resolve_path(settings.spatial_evidence_analysis_path)
        self.payload_root = self.root / "datasets"
        self.policy = _read_json(self.policy_path, {})
        self.catalog = _read_json(self.catalog_path, {})
        if self.policy.get("schema") != SCHEMA_VERSION:
            raise ValueError("Spatial evidence policy is missing or has an unsupported schema.")

    def _now(self) -> str:
        return _iso(self.now_fn())

    def _validate_feature_collection(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
            raise ValueError("Spatial datasets must be GeoJSON FeatureCollections.")
        if len(payload["features"]) > self.settings.spatial_evidence_max_features:
            raise ValueError("Spatial dataset exceeds the configured feature limit.")
        normalized: list[dict[str, Any]] = []
        for index, raw in enumerate(payload["features"]):
            if not isinstance(raw, dict) or raw.get("type") != "Feature" or not isinstance(raw.get("geometry"), dict):
                raise ValueError(f"Feature {index} is not a valid GeoJSON Feature.")
            geometry = raw["geometry"]
            _geometry_bbox(geometry)
            properties = _redact(raw.get("properties") if isinstance(raw.get("properties"), dict) else {})
            normalized.append({"type": "Feature", "id": _feature_id(raw, index), "geometry": geometry, "properties": properties})
        result = {"type": "FeatureCollection", "features": normalized}
        if len(_canonical(result)) > self.settings.spatial_evidence_max_payload_bytes:
            raise ValueError("Spatial dataset exceeds the configured payload-size limit.")
        return result

    def _area_object(self, record: dict[str, Any]) -> Area:
        mode = str(record.get("mode") or "polygon")
        geometry = record.get("geometry") if isinstance(record.get("geometry"), dict) else {}
        center = None
        radius = None
        if mode == "radius":
            center = _valid_position(record.get("center"))
            radius = float(record.get("radius_km") or 0)
        return Area(str(record.get("area_id")), geometry, mode, center, radius)

    def create_area(self, request: dict[str, Any]) -> dict[str, Any]:
        name = str(request.get("name") or "Area of interest").strip()[:180]
        visibility = str(request.get("visibility") or "private")
        if visibility not in {"private", "public"}:
            raise ValueError("Area visibility must be private or public.")
        mode = str(request.get("mode") or "polygon")
        center = None
        radius_km = None
        if mode == "bbox":
            bbox = request.get("bbox")
            if not isinstance(bbox, list) or len(bbox) != 4:
                raise ValueError("Bounding-box areas require [west,south,east,north].")
            west, south = _valid_position([bbox[0], bbox[1]])
            east, north = _valid_position([bbox[2], bbox[3]])
            if east <= west or north <= south:
                raise ValueError("Bounding-box east/north values must exceed west/south values.")
            geometry = _bbox_polygon([west, south, east, north])
        elif mode == "radius":
            center = _valid_position(request.get("center"))
            radius_km = _number(request.get("radius_km"))
            if radius_km is None or not 0 < radius_km <= self.settings.spatial_evidence_max_radius_km:
                raise ValueError("Radius must be positive and within the configured maximum.")
            lat_delta = radius_km / 110.574
            lon_delta = radius_km / max(1e-6, 111.320 * math.cos(math.radians(center[1])))
            geometry = _bbox_polygon([max(-180, center[0] - lon_delta), max(-90, center[1] - lat_delta), min(180, center[0] + lon_delta), min(90, center[1] + lat_delta)])
        elif mode == "polygon":
            geometry = request.get("geometry")
            if not isinstance(geometry, dict) or geometry.get("type") != "Polygon":
                raise ValueError("Polygon areas require a GeoJSON Polygon geometry.")
            _geometry_bbox(geometry)
        else:
            raise ValueError("Area mode must be bbox, radius, or polygon.")
        area_id = _safe_id(str(request.get("area_id") or f"aoi-{uuid4().hex[:12]}"), "aoi")
        if any(item.get("area_id") == area_id for item in _read_jsonl(self.areas_path, self.settings.spatial_evidence_max_records)):
            raise ValueError(f"Area already exists: {area_id}")
        record = {
            "schema": AREA_SCHEMA,
            "version": APP_VERSION,
            "area_id": area_id,
            "name": name,
            "description": str(request.get("description") or "")[:1000],
            "mode": mode,
            "visibility": visibility,
            "geometry": geometry,
            "bbox": _geometry_bbox(geometry),
            "center": list(center) if center else None,
            "radius_km": radius_km,
            "approximate_area_sq_km": round(math.pi * radius_km**2, 3) if radius_km else (round(_polygon_area_sq_km(geometry) or 0, 3)),
            "created_at": self._now(),
        }
        _append_jsonl(self.areas_path, record)
        return {"ok": True, "area": record}

    def areas(self, public: bool = False) -> dict[str, Any]:
        rows = _read_jsonl(self.areas_path, self.settings.spatial_evidence_max_records)
        if public:
            rows = [item for item in rows if item.get("visibility") == "public"]
        return {"ok": True, "schema": AREA_SCHEMA, "version": APP_VERSION, "count": len(rows), "areas": rows}

    def area(self, area_id: str, public: bool = False) -> dict[str, Any]:
        for item in reversed(_read_jsonl(self.areas_path, self.settings.spatial_evidence_max_records)):
            if item.get("area_id") == area_id and (not public or item.get("visibility") == "public"):
                return item
        raise KeyError(area_id)

    def register_dataset(self, request: dict[str, Any]) -> dict[str, Any]:
        dataset_id = _safe_id(str(request.get("dataset_id") or ""), "dataset")
        if not request.get("dataset_id"):
            raise ValueError("dataset_id is required.")
        visibility = str(request.get("visibility") or "private")
        if visibility not in {"private", "public"}:
            raise ValueError("Dataset visibility must be private or public.")
        collection = self._validate_feature_collection(_redact(request.get("feature_collection")))
        digest = _digest(collection)
        previous = [item for item in _read_jsonl(self.datasets_path, self.settings.spatial_evidence_max_records) if item.get("dataset_id") == dataset_id]
        if previous and previous[-1].get("sha256") == digest:
            return {"ok": True, "status": "unchanged", "deduplicated": True, "dataset": previous[-1]}
        version_id = f"spatial-{dataset_id}-{self.now_fn().strftime('%Y%m%dT%H%M%S')}-{digest[:10]}"
        payload_path = self.payload_root / dataset_id / f"{version_id}.geojson"
        _write_json(payload_path, collection)
        bboxes = [_geometry_bbox(item["geometry"]) for item in collection["features"]]
        bbox = [min(item[0] for item in bboxes), min(item[1] for item in bboxes), max(item[2] for item in bboxes), max(item[3] for item in bboxes)] if bboxes else []
        metadata = {
            "schema": DATASET_SCHEMA,
            "version": APP_VERSION,
            "dataset_id": dataset_id,
            "version_id": version_id,
            "title": str(request.get("title") or dataset_id)[:180],
            "source": str(request.get("source") or "Unspecified source")[:240],
            "source_url": str(request.get("source_url") or "")[:1000],
            "license": str(request.get("license") or "Unspecified")[:120],
            "layer_id": _safe_id(str(request.get("layer_id") or "custom"), "custom"),
            "visibility": visibility,
            "observed_at": str(request.get("observed_at") or self._now()),
            "registered_at": self._now(),
            "feature_count": len(collection["features"]),
            "geometry_types": sorted({item["geometry"].get("type") for item in collection["features"]}),
            "bbox": bbox,
            "sha256": digest,
            "payload_path": str(payload_path),
            "stable_identifier_rule": "Feature id, properties.id, properties.identifier, or deterministic content digest.",
        }
        _append_jsonl(self.datasets_path, metadata)
        return {"ok": True, "status": "registered", "deduplicated": False, "dataset": self._sanitize_dataset(metadata)}

    def _sanitize_dataset(self, item: dict[str, Any]) -> dict[str, Any]:
        result = dict(item)
        result.pop("payload_path", None)
        return result

    def datasets(self, public: bool = False, latest_only: bool = True) -> dict[str, Any]:
        rows = _read_jsonl(self.datasets_path, self.settings.spatial_evidence_max_records)
        if public:
            rows = [item for item in rows if item.get("visibility") == "public"]
        if latest_only:
            latest: dict[str, dict[str, Any]] = {}
            for item in rows:
                latest[str(item.get("dataset_id"))] = item
            rows = list(latest.values())
        sanitized = [self._sanitize_dataset(item) for item in rows]
        return {"ok": True, "schema": DATASET_SCHEMA, "version": APP_VERSION, "count": len(sanitized), "datasets": sanitized}

    def _dataset_metadata(self, dataset_id: str, version_id: str = "", public: bool = False) -> dict[str, Any]:
        matches = [item for item in _read_jsonl(self.datasets_path, self.settings.spatial_evidence_max_records) if item.get("dataset_id") == dataset_id]
        if version_id:
            matches = [item for item in matches if item.get("version_id") == version_id]
        if public:
            matches = [item for item in matches if item.get("visibility") == "public"]
        if not matches:
            raise KeyError(dataset_id if not version_id else version_id)
        return matches[-1]

    def _dataset(self, dataset_id: str, version_id: str = "", public: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
        metadata = self._dataset_metadata(dataset_id, version_id, public)
        payload = _read_json(Path(metadata["payload_path"]), None)
        if not isinstance(payload, dict) or _digest(payload) != metadata.get("sha256"):
            raise ValueError("Spatial dataset payload is missing or failed integrity verification.")
        return metadata, payload

    def _inside_area(self, point: tuple[float, float], area: Area) -> bool:
        if area.mode == "radius" and area.center and area.radius_km is not None:
            return _haversine_km(point, area.center) <= area.radius_km
        return _point_in_polygon(point, area.geometry.get("coordinates") or [])

    def _feature_intersects_area(self, feature: dict[str, Any], area: Area) -> bool:
        geometry = feature["geometry"]
        if area.mode == "radius":
            return any(self._inside_area(point, area) for point in _representative_points(geometry))
        return _geometry_intersects_polygon(geometry, area.geometry)

    def _record_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        record = {
            "schema": ANALYSIS_SCHEMA,
            "version": APP_VERSION,
            "analysis_id": f"analysis-{uuid4().hex}",
            "generated_at": self._now(),
            **payload,
        }
        record["analysis_sha256"] = _digest(record)
        _append_jsonl(self.analysis_path, record)
        return record

    def intersection(self, area_id: str, dataset_id: str, version_id: str = "", public: bool = False) -> dict[str, Any]:
        area_record = self.area(area_id, public=public)
        area = self._area_object(area_record)
        metadata, collection = self._dataset(dataset_id, version_id, public=public)
        selected = [feature for feature in collection["features"] if self._feature_intersects_area(feature, area)]
        record = self._record_analysis({
            "analysis_type": "intersection",
            "area_id": area_id,
            "dataset_id": dataset_id,
            "dataset_version_id": metadata["version_id"],
            "source": metadata["source"],
            "method": "WGS84 point-in-polygon, segment-aware polygon intersection, or geodesic-radius representative-point test.",
            "input_feature_count": len(collection["features"]),
            "matched_feature_count": len(selected),
            "limitations": ["No automatic coordinate reprojection is performed.", "Radius tests for non-point geometry use vertices plus centroid and may not capture every curved-edge crossing."],
        })
        return {"ok": True, **record, "feature_collection": {"type": "FeatureCollection", "features": selected}}

    def proximity(self, dataset_id: str, longitude: float, latitude: float, max_distance_km: float = 100.0, version_id: str = "", public: bool = False) -> dict[str, Any]:
        origin = _valid_position([longitude, latitude])
        if not 0 < max_distance_km <= self.settings.spatial_evidence_max_proximity_km:
            raise ValueError("max_distance_km is outside the configured boundary.")
        metadata, collection = self._dataset(dataset_id, version_id, public=public)
        rows = []
        approximate_count = 0
        for feature in collection["features"]:
            points = _representative_points(feature["geometry"])
            distance = min((_haversine_km(origin, item) for item in points), default=math.inf)
            if distance <= max_distance_km:
                approximate = feature["geometry"].get("type") != "Point"
                approximate_count += int(approximate)
                rows.append({"feature_id": feature["id"], "distance_km": round(distance, 3), "distance_method": "exact point distance" if not approximate else "minimum vertex/centroid approximation", "properties": feature["properties"]})
        rows.sort(key=lambda item: item["distance_km"])
        record = self._record_analysis({
            "analysis_type": "proximity",
            "dataset_id": dataset_id,
            "dataset_version_id": metadata["version_id"],
            "origin": [longitude, latitude],
            "max_distance_km": max_distance_km,
            "match_count": len(rows),
            "approximate_non_point_count": approximate_count,
            "method": "Haversine great-circle distance; non-point features use minimum vertex/centroid distance.",
            "limitations": ["Non-point distance is explicitly approximate and is not a geodesic edge-distance calculation."],
        })
        return {"ok": True, **record, "matches": rows}

    def aggregate(self, area_id: str, dataset_id: str, metric: str = "", version_id: str = "", public: bool = False) -> dict[str, Any]:
        intersection = self.intersection(area_id, dataset_id, version_id=version_id, public=public)
        features = intersection["feature_collection"]["features"]
        values = [_number(_get_path(item.get("properties") or {}, metric)) for item in features] if metric else []
        numeric = [item for item in values if item is not None]
        summary = {
            "feature_count": len(features),
            "metric": metric or None,
            "numeric_observation_count": len(numeric),
            "missing_metric_count": len(features) - len(numeric) if metric else 0,
            "sum": round(sum(numeric), 9) if numeric else None,
            "mean": round(sum(numeric) / len(numeric), 9) if numeric else None,
            "minimum": min(numeric) if numeric else None,
            "maximum": max(numeric) if numeric else None,
            "imputation_applied": False,
        }
        record = self._record_analysis({
            "analysis_type": "geographic_aggregation",
            "area_id": area_id,
            "dataset_id": dataset_id,
            "dataset_version_id": intersection["dataset_version_id"],
            "method": "Intersection-filtered count and optional numeric property aggregation.",
            "summary": summary,
            "limitations": ["Aggregation does not infer values for missing records and does not normalize by population or area unless an explicit metric already does so."],
        })
        return {"ok": True, **record}

    def compare(self, dataset_id: str, previous_version_id: str, current_version_id: str, metric: str = "", public: bool = False) -> dict[str, Any]:
        previous_meta, previous = self._dataset(dataset_id, previous_version_id, public=public)
        current_meta, current = self._dataset(dataset_id, current_version_id, public=public)
        old = {item["id"]: item for item in previous["features"]}
        new = {item["id"]: item for item in current["features"]}
        added = sorted(set(new) - set(old))
        removed = sorted(set(old) - set(new))
        retained = sorted(set(old) & set(new))
        geometry_changed = [item for item in retained if _digest(old[item]["geometry"]) != _digest(new[item]["geometry"])]
        property_changed = [item for item in retained if _digest(old[item]["properties"]) != _digest(new[item]["properties"])]
        metric_changes = []
        if metric:
            for identifier in retained:
                before = _number(_get_path(old[identifier]["properties"], metric))
                after = _number(_get_path(new[identifier]["properties"], metric))
                if before is not None and after is not None and before != after:
                    metric_changes.append({"feature_id": identifier, "previous": before, "current": after, "delta": after - before})
        record = self._record_analysis({
            "analysis_type": "temporal_layer_comparison",
            "dataset_id": dataset_id,
            "previous_version_id": previous_meta["version_id"],
            "current_version_id": current_meta["version_id"],
            "previous_observed_at": previous_meta["observed_at"],
            "current_observed_at": current_meta["observed_at"],
            "counts": {"previous": len(old), "current": len(new), "added": len(added), "removed": len(removed), "retained": len(retained), "geometry_changed": len(geometry_changed), "property_changed": len(property_changed)},
            "added_feature_ids": added,
            "removed_feature_ids": removed,
            "geometry_changed_feature_ids": geometry_changed,
            "property_changed_feature_ids": property_changed,
            "metric": metric or None,
            "metric_changes": metric_changes,
            "method": "Stable-identifier set comparison with geometry/property SHA-256 checks; no interpolation.",
            "limitations": ["Changes in source identifiers can appear as removal plus addition.", "No causal conclusion is inferred from spatial or temporal coincidence."],
        })
        return {"ok": True, **record}

    def export_evidence(self, area_id: str, dataset_id: str, version_id: str = "", public: bool = False) -> dict[str, Any]:
        result = self.intersection(area_id, dataset_id, version_id=version_id, public=public)
        features = result["feature_collection"]["features"]
        property_keys = sorted({str(key) for feature in features for key in (feature.get("properties") or {}).keys()})
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["feature_id", "geometry_type", *property_keys])
        for feature in features:
            props = feature.get("properties") or {}
            writer.writerow([feature.get("id"), feature.get("geometry", {}).get("type"), *[json.dumps(props.get(key), ensure_ascii=False) if isinstance(props.get(key), (dict, list)) else props.get(key) for key in property_keys]])
        packet = {
            "schema": "sc-site-intelligence-spatial-evidence-packet/1.0",
            "version": APP_VERSION,
            "generated_at": self._now(),
            "analysis_id": result["analysis_id"],
            "area_id": area_id,
            "dataset_id": dataset_id,
            "dataset_version_id": result["dataset_version_id"],
            "source": result["source"],
            "matched_feature_count": result["matched_feature_count"],
            "method": result["method"],
            "limitations": result["limitations"],
            "responsible_use": self.policy.get("responsible_use", []),
        }
        packet["packet_sha256"] = _digest(packet)
        return {"ok": True, "packet": packet, "geojson": result["feature_collection"], "csv": output.getvalue()}

    def public_summary(self) -> dict[str, Any]:
        public_areas = self.areas(public=True)["areas"]
        public_datasets = self.datasets(public=True)["datasets"]
        return {
            "ok": True,
            "schema": SCHEMA_VERSION,
            "version": APP_VERSION,
            "title": "Geospatial Analysis and Spatial Evidence Studio",
            "summary": "Transparent areas of interest, spatial intersection, proximity, geographic aggregation, temporal layer comparison, and evidence exports without individual tracking or operational targeting.",
            "counts": {"public_areas": len(public_areas), "public_datasets": len(public_datasets), "catalog_layers": len(self.catalog.get("layers", []))},
            "capabilities": self.policy.get("capabilities", []),
            "public_areas": public_areas[:20],
            "public_datasets": public_datasets[:20],
            "responsible_use": self.policy.get("responsible_use", []),
            "recommended_shortcode": "[sc_public_spatial_evidence]",
        }

    def layers(self) -> dict[str, Any]:
        return {"ok": True, "schema": self.catalog.get("schema"), "version": APP_VERSION, "count": len(self.catalog.get("layers", [])), "layers": self.catalog.get("layers", []), "methodology": self.catalog.get("methodology", [])}

    def methodology(self) -> dict[str, Any]:
        return {
            "ok": True,
            "schema": SCHEMA_VERSION,
            "version": APP_VERSION,
            "coordinate_reference_system": "WGS84 / EPSG:4326 only",
            "methods": self.policy.get("methods", []),
            "limitations": self.policy.get("limitations", []),
            "responsible_use": self.policy.get("responsible_use", []),
            "privacy": {"individual_tracking": False, "precise_personal_location_profiles": False, "military_targeting": False, "credentials_exposed": False},
        }

    def analyses(self, limit: int = 100) -> dict[str, Any]:
        rows = list(reversed(_read_jsonl(self.analysis_path, min(limit, self.settings.spatial_evidence_max_records))))
        return {"ok": True, "schema": ANALYSIS_SCHEMA, "version": APP_VERSION, "count": len(rows), "analyses": rows}

    def control_center(self) -> dict[str, Any]:
        areas = self.areas()["areas"]
        datasets = self.datasets(latest_only=True)["datasets"]
        analyses = self.analyses(limit=25)["analyses"]
        return {
            "ok": True,
            "schema": SCHEMA_VERSION,
            "version": APP_VERSION,
            "title": "Geospatial Analysis and Spatial Evidence Studio",
            "counts": {"areas": len(areas), "public_areas": sum(item.get("visibility") == "public" for item in areas), "datasets": len(datasets), "public_datasets": sum(item.get("visibility") == "public" for item in datasets), "analyses": len(_read_jsonl(self.analysis_path, self.settings.spatial_evidence_max_records)), "catalog_layers": len(self.catalog.get("layers", []))},
            "areas": list(reversed(areas[-20:])),
            "datasets": list(reversed(datasets[-20:])),
            "recent_analyses": analyses,
            "storage": {"mode": "file-backed", "root": str(self.root), "persistent_disk_recommended": True, "paid_gis_server_required": False},
            "methodology": self.methodology(),
        }
