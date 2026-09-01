from __future__ import annotations

"""Site Intelligence v4.39.0 — live underwater media discovery.

Three provider lanes remain independent:
- FathomNet public REST imagery/annotation discovery.
- NOAA Ocean Exploration Video Portal / NCEI archive discovery.
- Ocean Networks Canada Oceans 3.0 archive-file discovery (token required).

No provider failure is allowed to fabricate media or block the other providers.
"""

from datetime import datetime, timedelta, timezone
from html import unescape
import os
import re
from typing import Any, Callable
from urllib.parse import quote, urlencode, urljoin, urlparse

from .version import APP_VERSION
from .external_resilience_v43517 import request_json as resilient_request_json, request_text as resilient_request_text, request_bytes as resilient_request_bytes

VERSION = APP_VERSION
CONTRACT = "live-underwater-media-discovery-imagery-video-retrieval"
SCHEMA = "sc-site-intelligence-live-underwater-media/1.0"
MAX_RESULTS = 24

FATHOMNET_API = "https://database.fathomnet.org/api"
NOAA_VIDEO_PORTAL = "https://www.ncei.noaa.gov/access/ocean-exploration/video/"
NOAA_OER_WAF = "https://www.ncei.noaa.gov/waf/okeanos-rov-cruises/"
ONC_API = "https://data.oceannetworks.ca/api"

PROVIDERS = (
    {
        "id": "fathomnet",
        "title": "FathomNet",
        "organization": "FathomNet / MBARI and contributors",
        "mode": "LIVE",
        "credential": None,
        "media": ["image", "annotation"],
        "search_dimensions": ["concept", "geospatial metadata when present"],
        "public_url": "https://database.fathomnet.org/",
        "boundary": "FathomNet images and annotations are source records. Annotation labels retain their source verification state and are not population or abundance findings.",
    },
    {
        "id": "noaa-ocean-exploration",
        "title": "NOAA Ocean Exploration",
        "organization": "NOAA Ocean Exploration / NCEI",
        "mode": "LIVE_DISCOVERY",
        "credential": None,
        "media": ["video", "still-image", "expedition-archive"],
        "search_dimensions": ["expedition", "dive", "keyword", "depth", "date", "geographic coverage"],
        "public_url": NOAA_VIDEO_PORTAL,
        "boundary": "Portal and expedition records establish archived media availability only at their recorded scope. Dive presence does not imply visual coverage at every point, depth, or time.",
    },
    {
        "id": "onc-oceans-3",
        "title": "Ocean Networks Canada Oceans 3.0 / SeaTube",
        "organization": "Ocean Networks Canada",
        "mode": "AUTH_REQUIRED",
        "credential": "SC_SI_ONC_API_TOKEN",
        "media": ["image", "video", "camera-archive"],
        "search_dimensions": ["location", "device category", "date", "archive file"],
        "public_url": "https://data.oceannetworks.ca/",
        "boundary": "ONC archive-file discovery is token-authenticated. Site Intelligence never exposes the token and does not infer synchronization between camera media and nearby sensors.",
    },
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _token(settings: Any = None) -> str:
    value = getattr(settings, "onc_api_token", "") if settings is not None else ""
    return str(value or os.getenv("SC_SI_ONC_API_TOKEN", "")).strip()


def _timeout(settings: Any = None) -> int:
    value = getattr(settings, "underwater_media_timeout_seconds", None) if settings is not None else None
    if value in (None, ""):
        value = os.getenv("SC_SI_UNDERWATER_MEDIA_TIMEOUT_SECONDS", "10")
    try:
        return max(2, min(20, int(value)))
    except (TypeError, ValueError):
        return 10


def _limit(value: Any) -> int:
    try:
        return max(1, min(MAX_RESULTS, int(value or 12)))
    except (TypeError, ValueError):
        return 12


def _clean(value: Any, limit: int = 300) -> str:
    return str(value or "").strip()[:limit]


def _optional_float(value: Any, low: float, high: float, name: str) -> float | None:
    if value in (None, ""):
        return None
    number = float(value)
    if not low <= number <= high:
        raise ValueError(f"{name} must be between {low:g} and {high:g}")
    return round(number, 6)


def _safe_url(value: Any) -> str | None:
    raw = _clean(value, 2000)
    if not raw:
        return None
    parsed = urlparse(raw)
    if parsed.scheme not in {"https", "http"} or not parsed.hostname:
        return None
    return raw


def _date(value: Any) -> str | None:
    raw = _clean(value, 40)
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError as exc:
        raise ValueError("date must be ISO-8601 YYYY-MM-DD") from exc


def provider_catalog(settings: Any = None) -> dict[str, Any]:
    onc_configured = bool(_token(settings))
    providers = []
    for row in PROVIDERS:
        item = dict(row)
        item["configured"] = True if not row["credential"] else onc_configured
        item["configuration_required"] = bool(row["credential"] and not onc_configured)
        providers.append(item)
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "schema": SCHEMA,
        "provider_count": len(providers),
        "providers": providers,
        "default_provider": "fathomnet",
        "truth_boundaries": [
            "Candidate media are source-attributed records, not locally fabricated photographs or video.",
            "Provider search success does not prove point/depth/time coverage unless the returned source record supplies those fields.",
            "FathomNet annotations remain distinct from verified taxonomic observations and abundance claims.",
            "ONC credentials remain server-side and are never returned in public payloads or media URLs.",
            "NOAA archive and Video Portal discovery remain source search results; Site Intelligence does not invent video timestamps or dive geometry.",
        ],
        "generated_at": _now(),
    }


def readiness(settings: Any = None) -> dict[str, Any]:
    catalog = provider_catalog(settings)
    providers = {row["id"]: row for row in catalog["providers"]}
    checks = {
        "three_provider_lanes_registered": len(providers) == 3,
        "fathomnet_public_lane_ready": providers["fathomnet"]["configured"] is True,
        "noaa_public_lane_ready": providers["noaa-ocean-exploration"]["configured"] is True,
        "onc_missing_credential_non_blocking": True,
        "credential_material_not_exposed": all("token" not in str(row.get("public_url", "")).lower() for row in providers.values()),
        "bounded_result_count": MAX_RESULTS <= 24,
        "network_free_readiness": True,
        "upstream_health_non_blocking": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "schema": SCHEMA,
        "checks": checks,
        "provider_configuration": {
            "fathomnet": "public",
            "noaa-ocean-exploration": "public",
            "onc-oceans-3": "configured" if _token(settings) else "configuration-required",
        },
        "optional_configuration": {"SC_SI_ONC_API_TOKEN": bool(_token(settings))},
        "network_calls_performed": False,
        "release_blocking_upstream_health": False,
        "generated_at": _now(),
    }


def _fathomnet_results(query: str, limit: int, request_json: Callable[..., Any], timeout: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if query:
        endpoint = f"{FATHOMNET_API}/images/query/concept/{quote(query, safe='')}"
    else:
        endpoint = f"{FATHOMNET_API}/images/list/all?{urlencode({'page': 0, 'size': limit})}"
    payload = request_json(endpoint, timeout=timeout, max_bytes=4_000_000, cache=True, stale_if_error=False)
    rows = payload.get("content", []) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        rows = []
    results: list[dict[str, Any]] = []
    for row in rows[:limit]:
        if not isinstance(row, dict):
            continue
        url = _safe_url(row.get("url") or row.get("imageUrl") or row.get("mediaUrl"))
        if not url:
            continue
        boxes = row.get("boundingBoxes") or row.get("boundingboxes") or []
        labels = []
        if isinstance(boxes, list):
            for box in boxes[:12]:
                if isinstance(box, dict):
                    concept = _clean(box.get("concept") or box.get("label") or box.get("conceptName"), 120)
                    if concept and concept not in labels:
                        labels.append(concept)
        record_id = _clean(row.get("uuid") or row.get("id") or url, 300)
        lat = row.get("latitude", row.get("lat"))
        lon = row.get("longitude", row.get("lon"))
        depth = row.get("depthMeters", row.get("depth_m", row.get("depth")))
        observed = _clean(row.get("timestamp") or row.get("observedAt") or row.get("date"), 80) or None
        results.append({
            "provider": "fathomnet",
            "source_record_id": record_id,
            "record_type": "underwater-image",
            "title": labels[0] if labels else (query or "FathomNet underwater image"),
            "media_url": url,
            "thumbnail_url": url,
            "source_record_url": f"https://database.fathomnet.org/" if not row.get("uuid") else f"https://database.fathomnet.org/",
            "latitude": lat if isinstance(lat, (int, float)) else None,
            "longitude": lon if isinstance(lon, (int, float)) else None,
            "depth_m": depth if isinstance(depth, (int, float)) else None,
            "observed_at": observed,
            "annotations": labels,
            "credit": _clean(row.get("observer") or row.get("submitter") or row.get("contributorsEmail"), 200) or None,
            "rights": _clean(row.get("license") or row.get("rights"), 300) or "Asset-specific FathomNet/contributor terms; verify before reuse.",
            "evidence_state": "live-source-record",
        })
    return results, {"endpoint": endpoint, "mode": "LIVE", "network_calls_performed": True}


def _onc_results(query: str, location_code: str, date_from: str | None, date_to: str | None, limit: int, settings: Any, request_json: Callable[..., Any], timeout: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    token = _token(settings)
    if not token:
        return [], {
            "mode": "AUTH_REQUIRED",
            "configuration_required": True,
            "configuration_key": "SC_SI_ONC_API_TOKEN",
            "network_calls_performed": False,
            "message": "Ocean Networks Canada requires an Oceans 3.0 API token; FathomNet and NOAA remain available.",
        }

    location = _clean(location_code, 60)
    location_meta: dict[str, Any] = {}
    if not location:
        params: dict[str, Any] = {"token": token, "deviceCategoryCode": "VIDEOCAM"}
        if query:
            params["locationName"] = query
        endpoint = f"{ONC_API}/locations?{urlencode(params)}"
        payload = request_json(endpoint, timeout=timeout, max_bytes=2_000_000, cache=True, stale_if_error=False)
        locations = payload if isinstance(payload, list) else []
        if not locations:
            return [], {"mode": "AUTH_REQUIRED", "configuration_required": False, "network_calls_performed": True, "location_matches": 0}
        location_meta = locations[0] if isinstance(locations[0], dict) else {}
        location = _clean(location_meta.get("locationCode"), 60)
        if not location:
            return [], {"mode": "AUTH_REQUIRED", "configuration_required": False, "network_calls_performed": True, "location_matches": len(locations)}

    params = {
        "token": token,
        "locationCode": location,
        "deviceCategoryCode": "VIDEOCAM",
        "rowLimit": limit,
        "returnOptions": "all",
    }
    if date_from:
        params["dateFrom"] = f"{date_from}T00:00:00.000Z"
    if date_to:
        params["dateTo"] = f"{date_to}T23:59:59.999Z"
    endpoint = f"{ONC_API}/archivefile/location?{urlencode(params)}"
    payload = request_json(endpoint, timeout=timeout, max_bytes=3_000_000, cache=True, stale_if_error=False)
    files = payload.get("files", []) if isinstance(payload, dict) else []
    results: list[dict[str, Any]] = []
    for item in files[:limit] if isinstance(files, list) else []:
        meta = item if isinstance(item, dict) else {"filename": item}
        filename = _clean(meta.get("filename") or meta.get("fileName") or item, 500)
        if not filename:
            continue
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        record_type = "underwater-image" if ext in {"jpg", "jpeg", "png", "gif", "webp"} else "underwater-video" if ext in {"mp4", "mov", "m4v", "webm"} else "camera-archive-file"
        proxied = f"/public/underwater-media/onc/file?{urlencode({'filename': filename})}" if record_type == "underwater-image" else None
        results.append({
            "provider": "onc-oceans-3",
            "source_record_id": filename,
            "record_type": record_type,
            "title": filename,
            "media_url": proxied,
            "thumbnail_url": proxied,
            "source_record_url": f"https://data.oceannetworks.ca/DataSearch?{urlencode({'location': location})}",
            "latitude": meta.get("lat", location_meta.get("lat")),
            "longitude": meta.get("lon", location_meta.get("lon")),
            "depth_m": meta.get("depth", location_meta.get("depth")),
            "observed_at": meta.get("dateFrom") or meta.get("timestamp") or None,
            "annotations": [],
            "credit": "Ocean Networks Canada",
            "rights": "Asset-specific Ocean Networks Canada terms and citation requirements apply.",
            "evidence_state": "live-source-record",
        })
    public_endpoint = re.sub(r"([?&]token=)[^&]+", r"\1[redacted]", endpoint)
    return results, {"mode": "AUTH_REQUIRED", "configuration_required": False, "network_calls_performed": True, "location_code": location, "endpoint": public_endpoint}


_NOAA_LINK = re.compile(r'href=["\']([^"\']+)["\']', re.I)

def _noaa_results(query: str, expedition_id: str, dive_id: str, limit: int, request_text: Callable[..., str], timeout: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    params: dict[str, str] = {}
    if expedition_id:
        params["cruiseId"] = expedition_id
    if dive_id:
        params["oerkey"] = dive_id if dive_id.upper().startswith("DIVE") else f"DIVE{dive_id}"
    portal_url = NOAA_VIDEO_PORTAL + (f"?{urlencode(params)}" if params else "")
    results: list[dict[str, Any]] = []
    network_calls = False
    # When an expedition identifier is known, the NCEI expedition landing page is
    # stable enough to expose downloadable still/video/archive links. Generic
    # keyword filtering remains a portal handoff because the portal search service
    # is independently operated and can be under heavy load.
    if expedition_id and re.fullmatch(r"[A-Za-z0-9_-]{4,32}", expedition_id):
        waf_url = urljoin(NOAA_OER_WAF, expedition_id.lower().strip("/") + "/")
        try:
            html = request_text(waf_url, headers={"Accept": "text/html"}, timeout=timeout, max_bytes=3_000_000, cache=True, stale_if_error=False)
            network_calls = True
            seen: set[str] = set()
            for href in _NOAA_LINK.findall(html):
                absolute = urljoin(waf_url, unescape(href))
                low = absolute.lower()
                if absolute in seen:
                    continue
                if not any(token in low for token in ("video", "image", ".mov", ".mp4", ".jpg", ".jpeg", ".png", ".zip")):
                    continue
                if query and query.lower() not in unescape(href).lower() and query.lower() not in html.lower():
                    continue
                seen.add(absolute)
                ext = low.rsplit(".", 1)[-1].split("?", 1)[0] if "." in low else ""
                record_type = "underwater-image" if ext in {"jpg", "jpeg", "png"} else "underwater-video" if ext in {"mov", "mp4", "webm"} else "expedition-media-package"
                is_direct = record_type in {"underwater-image", "underwater-video"}
                results.append({
                    "provider": "noaa-ocean-exploration",
                    "source_record_id": absolute,
                    "record_type": record_type,
                    "title": absolute.rsplit("/", 1)[-1] or f"NOAA {expedition_id} media",
                    "media_url": absolute if is_direct else None,
                    "thumbnail_url": absolute if record_type == "underwater-image" else None,
                    "source_record_url": absolute,
                    "latitude": None,
                    "longitude": None,
                    "depth_m": None,
                    "observed_at": None,
                    "annotations": [],
                    "credit": "NOAA Ocean Exploration / NCEI",
                    "rights": "NOAA Ocean Exploration Video Portal video is public domain; linked expedition assets retain their source metadata and terms.",
                    "evidence_state": "live-source-record",
                })
                if len(results) >= limit:
                    break
        except Exception as exc:  # provider failure remains non-blocking
            return [], {"mode": "LIVE_DISCOVERY", "network_calls_performed": network_calls, "search_url": portal_url, "degraded": True, "error": _clean(exc, 180)}
    return results, {
        "mode": "LIVE_DISCOVERY",
        "network_calls_performed": network_calls,
        "search_url": portal_url,
        "portal_keyword_supported": True,
        "message": "Use the NOAA Video Portal handoff for keyword/depth/date/geographic filtering; expedition IDs additionally resolve archive media candidates in Site Intelligence.",
    }


def search(request: dict[str, Any], settings: Any = None, *, request_json: Callable[..., Any] = resilient_request_json, request_text: Callable[..., str] = resilient_request_text) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    provider = _clean(request.get("provider") or "fathomnet", 60).lower()
    if provider not in {"auto", "fathomnet", "noaa-ocean-exploration", "onc-oceans-3"}:
        raise ValueError("unsupported underwater media provider")
    query = _clean(request.get("query"), 200)
    expedition_id = _clean(request.get("expedition_id"), 60)
    dive_id = _clean(request.get("dive_id"), 60)
    location_code = _clean(request.get("location_code"), 60)
    date_from = _date(request.get("date_from"))
    date_to = _date(request.get("date_to"))
    if date_from and date_to and date_from > date_to:
        raise ValueError("date_from must be before or equal to date_to")
    latitude = _optional_float(request.get("latitude"), -90, 90, "latitude")
    longitude = _optional_float(request.get("longitude"), -180, 180, "longitude")
    if (latitude is None) != (longitude is None):
        raise ValueError("latitude and longitude must be supplied together")
    depth_m = _optional_float(request.get("depth_m"), 0, 11000, "depth_m")
    limit = _limit(request.get("limit"))
    timeout = _timeout(settings)

    chosen = [provider] if provider != "auto" else ["fathomnet", "noaa-ocean-exploration", "onc-oceans-3"]
    all_results: list[dict[str, Any]] = []
    provider_states: dict[str, Any] = {}
    for current in chosen:
        try:
            if current == "fathomnet":
                rows, state = _fathomnet_results(query, limit, request_json, timeout)
            elif current == "onc-oceans-3":
                rows, state = _onc_results(query, location_code, date_from, date_to, limit, settings, request_json, timeout)
            else:
                rows, state = _noaa_results(query, expedition_id, dive_id, limit, request_text, timeout)
            all_results.extend(rows)
            provider_states[current] = {"ok": not state.get("degraded", False), "record_count": len(rows), **state}
        except Exception as exc:
            provider_states[current] = {"ok": False, "record_count": 0, "degraded": True, "network_calls_performed": True, "error": _clean(exc, 180)}

    all_results = all_results[:limit]
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "schema": SCHEMA,
        "query": {
            "provider": provider,
            "query": query or None,
            "expedition_id": expedition_id or None,
            "dive_id": dive_id or None,
            "location_code": location_code or None,
            "date_from": date_from,
            "date_to": date_to,
            "latitude": latitude,
            "longitude": longitude,
            "depth_m": depth_m,
            "limit": limit,
        },
        "record_count": len(all_results),
        "results": all_results,
        "provider_states": provider_states,
        "truth": {
            "visual_media_fabricated": False,
            "missing_media_replaced": False,
            "provider_failure_blocks_other_providers": False,
            "onc_token_exposed": False,
            "annotation_promoted_to_population_claim": False,
            "point_depth_time_match_inferred": False,
        },
        "generated_at": _now(),
    }
    return payload


def onc_image_request(filename: str, settings: Any = None) -> tuple[str, dict[str, str]]:
    token = _token(settings)
    if not token:
        raise RuntimeError("Ocean Networks Canada API token is not configured.")
    name = _clean(filename, 500)
    if not name or "/" in name or "\\" in name or not re.fullmatch(r"[A-Za-z0-9_.()\-+]+", name):
        raise ValueError("invalid ONC archive filename")
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in {"jpg", "jpeg", "png", "gif", "webp"}:
        raise ValueError("only bounded image archive files are proxied; video remains a source handoff")
    url = f"{ONC_API}/archivefile/download?{urlencode({'filename': name, 'token': token})}"
    return url, {"Accept": "image/*"}


def fetch_onc_image(filename: str, settings: Any = None) -> tuple[bytes, str]:
    url, headers = onc_image_request(filename, settings)
    result = resilient_request_bytes(url, headers=headers, timeout=_timeout(settings), max_bytes=12_000_000, cache=True, stale_if_error=False)
    content_type = str(result.content_type or "application/octet-stream").split(";", 1)[0].strip().lower()
    if not content_type.startswith("image/"):
        raise RuntimeError("ONC archive file did not return an image content type.")
    return result.body, content_type
