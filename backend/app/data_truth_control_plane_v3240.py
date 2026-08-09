"""Global Data Truth Control Plane for Site Intelligence v4.11.0.

The control plane composes existing source, country, and record truth contracts into a
public-safe operational view. It does not invent source history, perform network
retrieval, or convert eligibility into observed coverage.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, Sequence

from .config import Settings
from .data_truth_v3233 import DataTruthCenter
from .data_truth_v32371 import GlobalCountryDataTruth, DEFAULT_MATRIX_COUNTRIES
from .version import APP_VERSION

SCHEMA_VERSION = "sc-site-intelligence-global-data-truth-control-plane/1.0"
RELEASE_ID = f"site-intelligence-v{APP_VERSION}"
ATTENTION_STATES = ("operational", "degraded", "review", "unavailable", "unknown")
DEFAULT_CONTROL_COUNTRIES = tuple(DEFAULT_MATRIX_COUNTRIES[:12])

WORKSPACE_SOURCE_MAP: tuple[dict[str, Any], ...] = (
    {"workspace_id": "overview", "label": "Live Overview", "source_ids": ("usgs_earthquakes", "reliefweb", "nasa_eonet", "world_bank")},
    {"workspace_id": "global-conditions", "label": "Global Conditions", "source_ids": ("usgs_earthquakes", "reliefweb", "nasa_eonet", "nasa_power")},
    {"workspace_id": "economics", "label": "Economics and Markets", "source_ids": ("world_bank",)},
    {"workspace_id": "science", "label": "Earth Systems and Science", "source_ids": ("nasa_eonet", "nasa_power", "openalex")},
    {"workspace_id": "humanitarian", "label": "Humanitarian", "source_ids": ("reliefweb",)},
    {"workspace_id": "resources", "label": "Trade, Energy, and Resources", "source_ids": ("world_bank", "nasa_power")},
    {"workspace_id": "dossiers", "label": "Country and Regional Dossiers", "source_ids": ("world_bank", "reliefweb", "openalex")},
    {"workspace_id": "compare", "label": "Comparative Intelligence", "source_ids": ("world_bank",)},
    {"workspace_id": "spatial-evidence", "label": "Spatial Evidence", "source_ids": ("usgs_earthquakes", "nasa_eonet", "reliefweb")},
    {"workspace_id": "earth-observation", "label": "Earth Observation", "source_ids": ("nasa_eonet", "nasa_power")},
    {"workspace_id": "record-truth", "label": "Record Provenance", "source_ids": ("world_bank", "nasa_eonet", "usgs_earthquakes")},
    {"workspace_id": "publishing", "label": "Publishing and Monitoring", "source_ids": ("world_bank", "reliefweb", "openalex")},
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fingerprint(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return sha256(body).hexdigest()


def _source_id(value: Any) -> str:
    key = str(value or "").strip().lower().replace("-", "_")
    if not key:
        raise KeyError(key)
    return key


def _iso3_list(values: Sequence[str] | None) -> list[str]:
    rows: list[str] = []
    for value in values or DEFAULT_CONTROL_COUNTRIES:
        code = str(value or "").strip().upper()
        if len(code) == 3 and code.isalpha() and code not in rows:
            rows.append(code)
    return rows[:60]


def _attention(row: Mapping[str, Any]) -> tuple[str, list[str]]:
    state = str((row.get("data_state") or {}).get("presentation") or "unknown")
    schema = str((row.get("schema") or {}).get("status") or "not_observed")
    circuit = str((row.get("resilience") or {}).get("circuit_breaker_state") or "closed")
    complete = bool((row.get("completeness") or {}).get("complete"))
    last_success = (row.get("retrieval") or {}).get("last_success_at")
    reasons: list[str] = []
    if state == "unavailable":
        reasons.append("Source retrieval is unavailable or has no recorded production success.")
    elif state in {"recently_cached", "historical_snapshot"}:
        reasons.append(f"Source is presented as {state.replace('_', ' ')} rather than live.")
    elif state in {"demonstration", "context_only"}:
        reasons.append(f"Source is classified as {state.replace('_', ' ')} and cannot support a live claim.")
    if schema == "changed":
        reasons.append("Observed schema fingerprint differs from the declared contract.")
    elif schema == "not_observed":
        reasons.append("No observed schema fingerprint has been recorded.")
    if circuit == "open":
        reasons.append("Circuit breaker is open.")
    elif circuit == "watch":
        reasons.append("Recent failures place the source under watch.")
    if not complete:
        reasons.append("Required source or coverage metadata is incomplete.")
    if not last_success:
        reasons.append("No successful retrieval timestamp is recorded.")

    if state == "unavailable" or circuit == "open":
        return "unavailable", reasons
    if state in {"recently_cached", "historical_snapshot"} or circuit == "watch":
        return "degraded", reasons
    if schema in {"changed", "not_observed"} or not complete:
        return "review", reasons
    if state == "live" and not reasons:
        return "operational", reasons
    return "unknown", reasons


class GlobalDataTruthControlPlane:
    """Compose source operations, geographic coverage, and workspace truth state."""

    def __init__(self, settings: Settings, source_center: DataTruthCenter | None = None, country_center: GlobalCountryDataTruth | None = None) -> None:
        self.settings = settings
        self.source_center = source_center or DataTruthCenter(settings)
        self.country_center = country_center or GlobalCountryDataTruth(settings, self.source_center)

    def _source_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for source in self.source_center.directory().get("sources", []):
            attention, reasons = _attention(source)
            retrieval = source.get("retrieval") or {}
            schema = source.get("schema") or {}
            resilience = source.get("resilience") or {}
            data_state = source.get("data_state") or {}
            completeness = source.get("completeness") or {}
            row = {
                "feed_id": source.get("feed_id"),
                "label": source.get("label"),
                "publisher": source.get("publisher"),
                "category": source.get("category"),
                "attention_state": attention,
                "attention_reasons": reasons,
                "presentation_state": data_state.get("presentation", "unknown"),
                "live_claim_allowed": bool(data_state.get("live_claim_allowed", False)),
                "freshness": retrieval.get("freshness", "unknown"),
                "last_attempt_at": retrieval.get("last_attempt_at"),
                "last_success_at": retrieval.get("last_success_at"),
                "last_status": retrieval.get("last_status", "never_run"),
                "last_record_count": retrieval.get("last_record_count", 0),
                "schema_state": schema.get("status", "not_observed"),
                "expected_schema_fingerprint": schema.get("expected_fingerprint"),
                "observed_schema_fingerprint": schema.get("observed_fingerprint"),
                "last_schema_check_at": schema.get("last_checked_at"),
                "last_schema_change_at": schema.get("last_change_at"),
                "circuit_state": resilience.get("circuit_breaker_state", "closed"),
                "consecutive_failures": resilience.get("consecutive_failures", 0),
                "metadata_complete": bool(completeness.get("complete")),
                "metadata_score_percent": completeness.get("score_percent", 0),
                "geographic_scope": (source.get("coverage") or {}).get("geographic") or "undeclared",
                "source_truth_url": f"/public/data-truth/{source.get('feed_id')}",
                "control_plane_url": f"/public/data-truth/control-plane/source/{source.get('feed_id')}",
            }
            row["status_fingerprint"] = _fingerprint({k: v for k, v in row.items() if k not in {"control_plane_url", "source_truth_url"}})
            rows.append(row)
        return rows

    @staticmethod
    def _summary(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
        summary = {state: 0 for state in ATTENTION_STATES}
        summary.update({"schema_changed": 0, "schema_unobserved": 0, "circuit_open": 0, "metadata_incomplete": 0, "live_claim_allowed": 0})
        for row in rows:
            attention = str(row.get("attention_state") or "unknown")
            summary[attention] = summary.get(attention, 0) + 1
            if row.get("schema_state") == "changed":
                summary["schema_changed"] += 1
            if row.get("schema_state") == "not_observed":
                summary["schema_unobserved"] += 1
            if row.get("circuit_state") == "open":
                summary["circuit_open"] += 1
            if not row.get("metadata_complete"):
                summary["metadata_incomplete"] += 1
            if row.get("live_claim_allowed"):
                summary["live_claim_allowed"] += 1
        return summary

    def overview(self) -> dict[str, Any]:
        rows = self._source_rows()
        summary = self._summary(rows)
        payload = {
            "ok": True,
            "version": APP_VERSION,
            "release_id": RELEASE_ID,
            "schema": SCHEMA_VERSION,
            "contract": "global-data-truth-control-plane",
            "generated_at": _now(),
            "source_count": len(rows),
            "summary": summary,
            "sources": rows,
            "attention_policy": {
                "states": list(ATTENTION_STATES),
                "live_claim_requires_live_presentation": True,
                "schema_change_requires_review": True,
                "missing_success_is_operational": False,
                "coverage_eligibility_is_observation": False,
            },
            "links": {
                "history": "/public/data-truth/control-plane/history",
                "schema_drift": "/public/data-truth/control-plane/schema-drift",
                "outages": "/public/data-truth/control-plane/outages",
                "coverage": "/public/data-truth/control-plane/coverage",
                "workspaces": "/public/data-truth/control-plane/workspaces",
                "export": "/public/data-truth/control-plane/export",
            },
            "boundaries": [
                "This control plane summarizes disclosed runtime metadata; it does not independently contact upstream publishers.",
                "Derived status events are not a complete historical event log.",
                "Source health does not establish country-level record availability, accuracy, causality, or authority.",
                "Unknown, missing, cached, historical, demonstration, and context-only states remain visibly distinct.",
            ],
        }
        payload["control_plane_fingerprint"] = _fingerprint({"summary": summary, "sources": [{k: v for k, v in row.items() if k != "status_fingerprint"} for row in rows]})
        return payload

    def sources(self) -> dict[str, Any]:
        overview = self.overview()
        return {k: overview[k] for k in ("ok", "version", "release_id", "schema", "generated_at", "source_count", "summary", "sources", "boundaries")}

    def source(self, feed_id: str) -> dict[str, Any]:
        key = _source_id(feed_id)
        overview = self.overview()
        row = next((item for item in overview["sources"] if item["feed_id"] == key), None)
        if row is None:
            raise KeyError(key)
        country_examples: list[dict[str, Any]] = []
        for code in ("KEN", "BRA", "USA"):
            try:
                source_rows = self.country_center.country_sources(code).get("sources", [])
                match = next((item for item in source_rows if item.get("feed_id") == key), None)
                if match:
                    country_examples.append({"country": match["country"], "eligibility": match["eligibility"], "coverage_state": match["coverage_state"], "evidence_level": match["evidence_level"]})
            except KeyError:
                continue
        return {
            "ok": True, "version": APP_VERSION, "release_id": RELEASE_ID, "schema": SCHEMA_VERSION,
            "contract": "global-data-truth-control-plane-source", "generated_at": overview["generated_at"],
            "source": row, "country_examples": country_examples,
            "history_url": f"/public/data-truth/control-plane/history?source={key}",
            "boundaries": overview["boundaries"],
        }

    def history(self, feed_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        key = _source_id(feed_id) if feed_id else None
        rows = self._source_rows()
        if key:
            rows = [row for row in rows if row["feed_id"] == key]
            if not rows:
                raise KeyError(key)
        events: list[dict[str, Any]] = []
        for row in rows:
            base = {"feed_id": row["feed_id"], "label": row["label"]}
            if row.get("last_attempt_at"):
                events.append({**base, "event_type": "retrieval_attempt", "observed_at": row["last_attempt_at"], "state": row["last_status"], "detail": "Latest disclosed retrieval attempt."})
            if row.get("last_success_at"):
                events.append({**base, "event_type": "retrieval_success", "observed_at": row["last_success_at"], "state": row["presentation_state"], "detail": f"Latest disclosed successful retrieval; {row['last_record_count']} record(s)."})
            if row.get("last_schema_check_at"):
                events.append({**base, "event_type": "schema_check", "observed_at": row["last_schema_check_at"], "state": row["schema_state"], "detail": "Latest disclosed schema comparison."})
            if row.get("last_schema_change_at"):
                events.append({**base, "event_type": "schema_change", "observed_at": row["last_schema_change_at"], "state": row["schema_state"], "detail": "Latest disclosed schema-change timestamp."})
            events.append({**base, "event_type": "release_snapshot", "observed_at": None, "state": row["attention_state"], "detail": "Current release control-plane status snapshot."})
        for event in events:
            event["event_id"] = _fingerprint(event)[:24]
        events.sort(key=lambda event: (event.get("observed_at") is not None, event.get("observed_at") or "", event["feed_id"], event["event_type"]), reverse=True)
        events = events[: max(1, min(int(limit), 500))]
        return {
            "ok": True, "version": APP_VERSION, "release_id": RELEASE_ID, "schema": SCHEMA_VERSION,
            "contract": "global-data-truth-derived-status-history", "generated_at": _now(),
            "source_filter": key, "event_count": len(events), "events": events,
            "complete_event_log": False,
            "boundaries": [
                "Events are derived only from currently disclosed runtime timestamps and release status.",
                "Absence of an event does not prove that no outage, schema change, or retrieval occurred.",
            ],
        }

    def schema_drift(self) -> dict[str, Any]:
        rows = self._source_rows()
        items = [{
            "feed_id": row["feed_id"], "label": row["label"], "schema_state": row["schema_state"],
            "expected_fingerprint": row["expected_schema_fingerprint"], "observed_fingerprint": row["observed_schema_fingerprint"],
            "last_checked_at": row["last_schema_check_at"], "last_change_at": row["last_schema_change_at"],
            "review_required": row["schema_state"] in {"changed", "not_observed"},
            "resolution_policy": "flag_and_review; never silently substitute fields",
        } for row in rows]
        return {
            "ok": True, "version": APP_VERSION, "release_id": RELEASE_ID, "schema": SCHEMA_VERSION,
            "contract": "global-data-truth-schema-drift-register", "generated_at": _now(),
            "source_count": len(items), "changed_count": sum(i["schema_state"] == "changed" for i in items),
            "unobserved_count": sum(i["schema_state"] == "not_observed" for i in items), "sources": items,
            "boundaries": ["Schema status compares declared and disclosed fingerprints; it does not validate semantic equivalence."],
        }

    def outages(self) -> dict[str, Any]:
        rows = self._source_rows()
        incidents: list[dict[str, Any]] = []
        for row in rows:
            if row["attention_state"] == "operational":
                continue
            incident_state = "open" if row["attention_state"] == "unavailable" else "degraded" if row["attention_state"] == "degraded" else "review"
            incidents.append({
                "incident_id": _fingerprint({"feed_id": row["feed_id"], "attention": row["attention_state"], "status": row["last_status"]})[:24],
                "feed_id": row["feed_id"], "label": row["label"], "incident_state": incident_state,
                "attention_state": row["attention_state"], "presentation_state": row["presentation_state"],
                "circuit_state": row["circuit_state"], "last_success_at": row["last_success_at"],
                "reasons": row["attention_reasons"], "automatically_resolved": False,
            })
        return {
            "ok": True, "version": APP_VERSION, "release_id": RELEASE_ID, "schema": SCHEMA_VERSION,
            "contract": "global-data-truth-source-outage-register", "generated_at": _now(),
            "incident_count": len(incidents), "open_count": sum(i["incident_state"] == "open" for i in incidents),
            "degraded_count": sum(i["incident_state"] == "degraded" for i in incidents), "incidents": incidents,
            "boundaries": [
                "An incident is a control-plane status requiring attention, not proof that the upstream publisher is globally offline.",
                "The public control plane does not automatically mutate source configuration or publish outage claims.",
            ],
        }

    def coverage(self, countries: Sequence[str] | None = None) -> dict[str, Any]:
        codes = _iso3_list(countries)
        matrix = self.country_center.matrix(countries=codes, limit=len(codes), offset=0)
        state_counts: dict[str, int] = {}
        country_gaps: list[dict[str, Any]] = []
        source_gaps: dict[str, dict[str, Any]] = {column["feed_id"]: {"feed_id": column["feed_id"], "label": column["label"], "available_or_partial": 0, "unknown_or_unavailable": 0, "not_applicable": 0} for column in matrix["columns"]}
        for row in matrix["rows"]:
            unresolved = 0
            for cell in row["cells"]:
                state = cell["coverage_state"]
                state_counts[state] = state_counts.get(state, 0) + 1
                bucket = source_gaps[cell["feed_id"]]
                if state in {"available", "partial", "historical_only", "no_recent_records"}:
                    bucket["available_or_partial"] += 1
                elif state == "not_applicable":
                    bucket["not_applicable"] += 1
                else:
                    bucket["unknown_or_unavailable"] += 1
                    unresolved += 1
            country_gaps.append({"country": row["country"], "unresolved_source_count": unresolved, "source_count": len(row["cells"])})
        country_gaps.sort(key=lambda item: (-item["unresolved_source_count"], item["country"]["name"]))
        return {
            "ok": True, "version": APP_VERSION, "release_id": RELEASE_ID, "schema": SCHEMA_VERSION,
            "contract": "global-data-truth-coverage-monitor", "generated_at": _now(),
            "country_count": matrix["country_count"], "source_count": matrix["source_count"],
            "state_counts": state_counts, "country_gaps": country_gaps, "source_gaps": list(source_gaps.values()),
            "matrix_endpoint": "/public/data-truth/coverage-matrix",
            "boundaries": ["Coverage status distinguishes contract eligibility from observed country-linked records."],
        }

    def workspaces(self, country_code: str = "KEN") -> dict[str, Any]:
        code = str(country_code or "KEN").strip().upper()
        country_payload = self.country_center.country_sources(code)
        source_by_id = {row["feed_id"]: row for row in country_payload["sources"]}
        operational_by_id = {row["feed_id"]: row for row in self._source_rows()}
        rows: list[dict[str, Any]] = []
        for definition in WORKSPACE_SOURCE_MAP:
            dependencies: list[dict[str, Any]] = []
            for feed_id in definition["source_ids"]:
                country_source = source_by_id.get(feed_id)
                operation = operational_by_id.get(feed_id)
                dependencies.append({
                    "feed_id": feed_id,
                    "label": (operation or country_source or {}).get("label", feed_id),
                    "attention_state": (operation or {}).get("attention_state", "unknown"),
                    "coverage_state": (country_source or {}).get("coverage_state", "unknown"),
                    "eligibility": (country_source or {}).get("eligibility", "unknown"),
                })
            unavailable = sum(dep["attention_state"] == "unavailable" for dep in dependencies)
            unresolved = sum(dep["coverage_state"] in {"unknown", "unavailable"} for dep in dependencies)
            degraded = sum(dep["attention_state"] in {"degraded", "review"} for dep in dependencies)
            if unavailable == len(dependencies):
                state = "unavailable"
            elif unavailable or degraded or unresolved:
                state = "degraded"
            else:
                state = "operational"
            rows.append({
                "workspace_id": definition["workspace_id"], "label": definition["label"], "country": country_payload["country"],
                "truth_state": state, "dependency_count": len(dependencies), "dependencies": dependencies,
                "limitations_visible": True, "truth_drawer_available": True,
            })
        return {
            "ok": True, "version": APP_VERSION, "release_id": RELEASE_ID, "schema": SCHEMA_VERSION,
            "contract": "cross-workspace-data-truth-status", "generated_at": _now(),
            "country": country_payload["country"], "workspace_count": len(rows),
            "summary": {state: sum(row["truth_state"] == state for row in rows) for state in ("operational", "degraded", "unavailable")},
            "workspaces": rows,
            "boundaries": ["Workspace status summarizes disclosed dependencies and does not validate every visible record."],
        }

    def export(self, countries: Sequence[str] | None = None, country_code: str = "KEN") -> dict[str, Any]:
        overview = self.overview()
        export_payload = {
            "overview": overview,
            "schema_drift": self.schema_drift(),
            "outages": self.outages(),
            "coverage": self.coverage(countries),
            "workspaces": self.workspaces(country_code),
        }
        return {
            "ok": True, "version": APP_VERSION, "release_id": RELEASE_ID, "schema": SCHEMA_VERSION,
            "contract": "global-data-truth-control-plane-export", "generated_at": _now(),
            "payload": export_payload,
            "export_fingerprint": _fingerprint(export_payload),
            "boundaries": overview["boundaries"],
        }


def public_control_plane(settings: Settings) -> dict[str, Any]:
    return GlobalDataTruthControlPlane(settings).overview()


def public_control_plane_sources(settings: Settings) -> dict[str, Any]:
    return GlobalDataTruthControlPlane(settings).sources()


def public_control_plane_source(settings: Settings, feed_id: str) -> dict[str, Any]:
    return GlobalDataTruthControlPlane(settings).source(feed_id)


def public_control_plane_history(settings: Settings, feed_id: str | None = None, limit: int = 100) -> dict[str, Any]:
    return GlobalDataTruthControlPlane(settings).history(feed_id, limit)


def public_control_plane_schema_drift(settings: Settings) -> dict[str, Any]:
    return GlobalDataTruthControlPlane(settings).schema_drift()


def public_control_plane_outages(settings: Settings) -> dict[str, Any]:
    return GlobalDataTruthControlPlane(settings).outages()


def public_control_plane_coverage(settings: Settings, countries: Sequence[str] | None = None) -> dict[str, Any]:
    return GlobalDataTruthControlPlane(settings).coverage(countries)


def public_control_plane_workspaces(settings: Settings, country_code: str = "KEN") -> dict[str, Any]:
    return GlobalDataTruthControlPlane(settings).workspaces(country_code)


def public_control_plane_export(settings: Settings, countries: Sequence[str] | None = None, country_code: str = "KEN") -> dict[str, Any]:
    return GlobalDataTruthControlPlane(settings).export(countries, country_code)
