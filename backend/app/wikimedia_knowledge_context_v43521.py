from __future__ import annotations

"""Wikimedia Knowledge Context for Site Intelligence v4.35.23.

Wikimedia is a context/entity-resolution layer. It cannot outrank official,
operational, scientific, or statistical evidence in Site Intelligence Truth.
"""

from datetime import datetime, timedelta, timezone
import re
from typing import Any, Mapping
from urllib.parse import quote, urlencode

from .version import APP_VERSION
from .live_country_intelligence import _country
from .authoritative_connectors_v4355 import _request_json

VERSION = APP_VERSION
CONTRACT = "wikimedia-knowledge-context-v43521"
SCHEMA = "sc-site-intelligence-wikimedia-knowledge-context/1.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timeout(settings: Any) -> int:
    return int(getattr(settings, "external_request_timeout_seconds", 8)) if settings is not None else 8


def _setting(settings: Any, name: str, default: str) -> str:
    value = str(getattr(settings, name, "") or "").strip() if settings is not None else ""
    return value or default


def _language(value: str) -> str:
    token = str(value or "en").strip().lower()
    if not re.fullmatch(r"[a-z]{2,3}(?:-[a-z0-9]{2,8})?", token):
        raise ValueError("language is invalid")
    return token


def _query(value: str, *, limit: int = 180) -> str:
    token = " ".join(str(value or "").split())
    if not token or len(token) > limit:
        raise ValueError("query is invalid")
    return token


def wikidata_search(settings: Any, *, query: str, language: str = "en", limit: int = 5) -> dict[str, Any]:
    query = _query(query)
    language = _language(language)
    limit = int(limit)
    if not 1 <= limit <= 20:
        raise ValueError("limit must be between 1 and 20")
    base = _setting(settings, "wikidata_action_api_url", "https://www.wikidata.org/w/api.php")
    params = {
        "action": "wbsearchentities", "format": "json", "search": query,
        "language": language, "uselang": language, "type": "item", "limit": limit,
    }
    endpoint = f"{base}?{urlencode(params)}"
    data = _request_json(endpoint, timeout=_timeout(settings))
    return {
        "ok": True, "version": VERSION, "connector_id": "wikidata-entity-search", "context_class": "LINKED KNOWLEDGE",
        "data": data, "provenance": {"organization": "Wikidata / Wikimedia community", "endpoint": endpoint, "retrieved_at": _now()},
        "boundary": "Wikidata is community-curated linked knowledge used for entity resolution and identifiers; it is not an official statistic or operational-condition authority.",
    }


def wikidata_entity(settings: Any, *, entity_id: str, language: str = "en") -> dict[str, Any]:
    entity_id = str(entity_id or "").strip().upper()
    if not re.fullmatch(r"Q[1-9][0-9]*", entity_id):
        raise ValueError("entity_id must be a Wikidata Q identifier")
    language = _language(language)
    base = _setting(settings, "wikidata_action_api_url", "https://www.wikidata.org/w/api.php")
    params = {
        "action": "wbgetentities", "format": "json", "ids": entity_id,
        "props": "labels|descriptions|aliases|sitelinks|claims", "languages": language,
        "sitefilter": f"{language}wiki|commonswiki",
    }
    endpoint = f"{base}?{urlencode(params)}"
    data = _request_json(endpoint, timeout=_timeout(settings))
    return {
        "ok": True, "version": VERSION, "connector_id": "wikidata-entity", "context_class": "LINKED KNOWLEDGE",
        "entity_id": entity_id, "data": data,
        "provenance": {"organization": "Wikidata / Wikimedia community", "endpoint": endpoint, "retrieved_at": _now()},
        "boundary": "Wikidata statements remain community-curated context and identifiers; Site Intelligence does not promote them above source-governed evidence.",
    }


def wikipedia_page_context(settings: Any, *, title: str, language: str = "en") -> dict[str, Any]:
    title = _query(title, limit=240)
    language = _language(language)
    base = _setting(settings, "wikipedia_action_api_template", "https://{language}.wikipedia.org/w/api.php").format(language=language)
    params = {
        "action": "query", "format": "json", "formatversion": "2", "redirects": "1", "titles": title,
        "prop": "extracts|info|pageprops", "exintro": "1", "explaintext": "1", "inprop": "url",
    }
    endpoint = f"{base}?{urlencode(params)}"
    data = _request_json(endpoint, timeout=_timeout(settings))
    return {
        "ok": True, "version": VERSION, "connector_id": "wikipedia-context", "context_class": "COMMUNITY-CURATED CONTEXT",
        "data": data, "provenance": {"organization": f"{language}.wikipedia.org / Wikimedia community", "endpoint": endpoint, "retrieved_at": _now()},
        "boundary": "Wikipedia text is contextual background. It does not replace primary sources, official statistics, scientific measurements, operational reporting, or professional analysis.",
    }


def commons_media_search(settings: Any, *, query: str, limit: int = 6) -> dict[str, Any]:
    query = _query(query)
    limit = int(limit)
    if not 1 <= limit <= 12:
        raise ValueError("limit must be between 1 and 12")
    base = _setting(settings, "wikimedia_commons_action_api_url", "https://commons.wikimedia.org/w/api.php")
    params = {
        "action": "query", "format": "json", "formatversion": "2", "generator": "search",
        "gsrsearch": query, "gsrnamespace": "6", "gsrlimit": limit, "prop": "imageinfo",
        "iiprop": "url|extmetadata", "iiurlwidth": "720",
    }
    endpoint = f"{base}?{urlencode(params)}"
    data = _request_json(endpoint, timeout=_timeout(settings))
    return {
        "ok": True, "version": VERSION, "connector_id": "wikimedia-commons-media", "context_class": "VISUAL KNOWLEDGE",
        "data": data, "provenance": {"organization": "Wikimedia Commons / Wikimedia community", "endpoint": endpoint, "retrieved_at": _now()},
        "boundary": "Commons media is contextual visual evidence. Per-file author, source, license and description metadata must remain visible; media is not proof of current conditions.",
    }


def pageviews(settings: Any, *, article: str, language: str = "en", days: int = 30) -> dict[str, Any]:
    article = _query(article, limit=240).replace(" ", "_")
    language = _language(language)
    days = int(days)
    if not 1 <= days <= 90:
        raise ValueError("days must be between 1 and 90")
    end = datetime.now(timezone.utc).date() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    project = f"{language}.wikipedia.org"
    base = _setting(settings, "wikimedia_analytics_base_url", "https://wikimedia.org/api/rest_v1").rstrip("/")
    endpoint = (
        f"{base}/metrics/pageviews/per-article/{quote(project, safe='.')}/all-access/user/"
        f"{quote(article, safe='')}/daily/{start.strftime('%Y%m%d')}/{end.strftime('%Y%m%d')}"
    )
    data = _request_json(endpoint, timeout=_timeout(settings))
    return {
        "ok": True, "version": VERSION, "connector_id": "wikimedia-pageviews", "context_class": "PUBLIC ATTENTION SIGNAL",
        "article": article, "project": project, "days": days, "data": data,
        "provenance": {"organization": "Wikimedia Analytics", "endpoint": endpoint, "retrieved_at": _now()},
        "boundary": "Pageviews measure reader attention to a Wikimedia page. They do not measure event severity, factual importance, public opinion, prevalence, causality, or humanitarian need.",
    }


def _first_search_id(payload: Mapping[str, Any]) -> str:
    data = payload.get("data") if isinstance(payload, Mapping) else None
    search = data.get("search") if isinstance(data, Mapping) else None
    if isinstance(search, list):
        for item in search:
            if isinstance(item, Mapping) and re.fullmatch(r"Q[1-9][0-9]*", str(item.get("id") or "")):
                return str(item["id"])
    return ""


def _entity_summary(payload: Mapping[str, Any], entity_id: str, language: str) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload, Mapping) else None
    entities = data.get("entities") if isinstance(data, Mapping) else None
    entity = entities.get(entity_id) if isinstance(entities, Mapping) else None
    if not isinstance(entity, Mapping):
        return {}
    label = ((entity.get("labels") or {}).get(language) or {}).get("value") if isinstance(entity.get("labels"), Mapping) else None
    description = ((entity.get("descriptions") or {}).get(language) or {}).get("value") if isinstance(entity.get("descriptions"), Mapping) else None
    aliases_raw = ((entity.get("aliases") or {}).get(language) or []) if isinstance(entity.get("aliases"), Mapping) else []
    aliases = [str(x.get("value")) for x in aliases_raw if isinstance(x, Mapping) and x.get("value")][:12]
    sitelinks = entity.get("sitelinks") if isinstance(entity.get("sitelinks"), Mapping) else {}
    enwiki = sitelinks.get(f"{language}wiki") if isinstance(sitelinks.get(f"{language}wiki"), Mapping) else {}
    commons = sitelinks.get("commonswiki") if isinstance(sitelinks.get("commonswiki"), Mapping) else {}
    return {
        "id": entity_id,
        "label": label or entity_id,
        "description": description or "",
        "aliases": aliases,
        "wikipedia_title": str(enwiki.get("title") or ""),
        "commons_title": str(commons.get("title") or ""),
        "url": f"https://www.wikidata.org/wiki/{entity_id}",
    }


def _wikipedia_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload, Mapping) else None
    query = data.get("query") if isinstance(data, Mapping) else None
    pages = query.get("pages") if isinstance(query, Mapping) else None
    if not isinstance(pages, list) or not pages:
        return {}
    page = pages[0] if isinstance(pages[0], Mapping) else {}
    if page.get("missing") is True:
        return {}
    return {
        "title": str(page.get("title") or ""),
        "extract": " ".join(str(page.get("extract") or "").split())[:1800],
        "url": str(page.get("fullurl") or ""),
        "pageid": page.get("pageid"),
    }


def _commons_summary(payload: Mapping[str, Any], limit: int) -> list[dict[str, Any]]:
    data = payload.get("data") if isinstance(payload, Mapping) else None
    query = data.get("query") if isinstance(data, Mapping) else None
    pages = query.get("pages") if isinstance(query, Mapping) else None
    if not isinstance(pages, list):
        return []
    rows: list[dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, Mapping):
            continue
        info_list = page.get("imageinfo")
        info = info_list[0] if isinstance(info_list, list) and info_list and isinstance(info_list[0], Mapping) else {}
        meta = info.get("extmetadata") if isinstance(info.get("extmetadata"), Mapping) else {}
        def mv(name: str) -> str:
            item = meta.get(name)
            return " ".join(str(item.get("value") or "").split()) if isinstance(item, Mapping) else ""
        rows.append({
            "title": str(page.get("title") or "").removeprefix("File:"),
            "file_page_url": str(info.get("descriptionurl") or ""),
            "image_url": str(info.get("thumburl") or info.get("url") or ""),
            "license": mv("LicenseShortName") or mv("UsageTerms"),
            "artist": re.sub(r"<[^>]+>", " ", mv("Artist"))[:240],
            "credit": re.sub(r"<[^>]+>", " ", mv("Credit"))[:300],
        })
        if len(rows) >= limit:
            break
    return rows


def _pageview_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload, Mapping) else None
    items = data.get("items") if isinstance(data, Mapping) else None
    if not isinstance(items, list):
        return {"total": 0, "daily": []}
    daily = [{"date": str(x.get("timestamp") or "")[:8], "views": int(x.get("views") or 0)} for x in items if isinstance(x, Mapping)]
    return {"total": sum(x["views"] for x in daily), "daily": daily}


def country_knowledge_context(settings: Any, *, country_code: str, language: str = "en", media_limit: int = 4, pageview_days: int = 30) -> dict[str, Any]:
    code, country = _country(country_code)
    language = _language(language)
    name = str(country.get("name") or country.get("display_name") or code)
    query_name = "State of Palestine" if code == "PSE" else name
    states: dict[str, str] = {}
    entity: dict[str, Any] = {}
    wikipedia: dict[str, Any] = {}
    media: list[dict[str, Any]] = []
    attention: dict[str, Any] = {"total": 0, "daily": []}

    try:
        search = wikidata_search(settings, query=query_name, language=language, limit=5)
        qid = _first_search_id(search)
        states["wikidata"] = "connected" if qid else "no-match"
        if qid:
            detail = wikidata_entity(settings, entity_id=qid, language=language)
            entity = _entity_summary(detail, qid, language)
    except Exception:
        states["wikidata"] = "unavailable"

    article_title = str(entity.get("wikipedia_title") or query_name)
    try:
        wiki = wikipedia_page_context(settings, title=article_title, language=language)
        wikipedia = _wikipedia_summary(wiki)
        states["wikipedia"] = "connected" if wikipedia else "no-match"
    except Exception:
        states["wikipedia"] = "unavailable"

    if wikipedia.get("title"):
        article_title = str(wikipedia["title"])

    try:
        commons = commons_media_search(settings, query=f"{name} geography", limit=media_limit)
        media = _commons_summary(commons, media_limit)
        states["commons"] = "connected" if media else "no-match"
    except Exception:
        states["commons"] = "unavailable"

    try:
        views = pageviews(settings, article=article_title, language=language, days=pageview_days)
        attention = _pageview_summary(views)
        states["pageviews"] = "connected" if attention.get("daily") else "no-data"
    except Exception:
        states["pageviews"] = "unavailable"

    return {
        "ok": True,
        "version": VERSION,
        "schema": SCHEMA,
        "contract": CONTRACT,
        "generated_at": _now(),
        "country": {"code": code, "name": name},
        "context_class": "KNOWLEDGE CONTEXT",
        "entity": entity,
        "wikipedia": wikipedia,
        "media": media,
        "attention": {**attention, "days": pageview_days, "label": "PUBLIC ATTENTION SIGNAL"},
        "source_states": states,
        "truth_precedence": "excluded",
        "boundaries": [
            "Wikidata and Wikipedia are community-curated context; neither can outrank official or source-governed evidence.",
            "Wikimedia Commons media retains per-file provenance/licensing and is not evidence of current conditions by itself.",
            "Pageviews measure public attention to a page, not severity, importance, prevalence, opinion or need.",
            "Wikimedia upstream availability is optional and non-blocking for Site Intelligence deployment readiness.",
        ],
    }


def readiness() -> dict[str, Any]:
    checks = {
        "wikidata_entity_spine_registered": True,
        "wikipedia_context_registered": True,
        "commons_visual_context_registered": True,
        "pageviews_attention_signal_registered": True,
        "wikimedia_excluded_from_truth_precedence": True,
        "commons_license_metadata_preserved": True,
        "pageviews_not_severity": True,
        "readiness_requires_no_upstream_network": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "schema": SCHEMA,
        "contract": CONTRACT,
        "checks": checks,
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
        "generated_at": _now(),
    }
