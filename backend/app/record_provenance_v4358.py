from __future__ import annotations

"""v4.35.23 record-truth adapter over the canonical workspace observation contract."""

from typing import Any, Mapping
from .config import Settings
from . import record_provenance_v3238 as prior
from .workspace_evidence_unification_v4358 import canonical_country_indicator, canonical_country_observations


def _record_from_canonical(observation: Mapping[str, Any]) -> dict[str, Any]:
    indicator = observation.get("indicator") or {}
    source = observation.get("source") or {}
    dates = observation.get("dates") or {}
    semantics = observation.get("semantics")
    limitations = list(observation.get("limitations") or [])
    truth_state = str(observation.get("truth_state") or "unverified")
    if truth_state == "missing":
        assertion = "The canonical workspace observation has no verified value; the workspace and Truth layer both present the value as missing."
    elif semantics and semantics.get("concept_id") == "electricity_structural_access":
        assertion = "A dated structural electricity-access observation is disclosed from the same canonical object used by the workspace; it is not a statement about current electricity supply or reliability."
    else:
        assertion = "The workspace and Truth layer disclose the same canonical observation, including value, period, source state, semantics and freshness."
    payload = {
        "contract": "record-provenance-indicator",
        "unification_contract": "workspace-evidence-unified-record-truth",
        "record_id": f"indicator:{observation.get('country',{}).get('code')}:{indicator.get('id')}",
        "record_type": "indicator",
        "truth_state": truth_state,
        "presentation_state": observation.get("presentation_state"),
        "country": observation.get("country"),
        "title": indicator.get("label") or indicator.get("id"),
        "value": observation.get("value"),
        "units": observation.get("units"),
        "dates": {**dates, "generated_at": observation.get("generated_at")},
        "source": {
            "feed_id": source.get("source_id"),
            "publisher": source.get("publisher"),
            "indicator_id": source.get("indicator_id"),
            "url": source.get("url"),
            "authority_class": source.get("authority_class"),
            "license": "Source terms apply; verify current reuse terms at the publisher.",
        },
        "semantics": semantics,
        "freshness": observation.get("freshness"),
        "selection": observation.get("selection"),
        "lineage": {
            **dict(observation.get("lineage") or {}),
            "canonical_observation_endpoint": f"/public/workspace-evidence/country/{observation.get('country',{}).get('code')}/indicator/{indicator.get('id')}",
            "record_truth_endpoint": f"/public/record-truth/indicator/{observation.get('country',{}).get('code')}/{indicator.get('id')}",
        },
        "canonical_observation": dict(observation),
        "canonical_observation_sha256": (observation.get("fingerprint") or {}).get("value"),
        "transformations": [
            {"step": 1, "operation": "canonical-observation-resolution", "detail": "Resolve the same country-indicator observation used by the workspace headline."},
            {"step": 2, "operation": "type-normalization", "detail": "Preserve the canonical numeric value without imputation or replacement."},
            {"step": 3, "operation": "unit-presentation", "detail": "Display the canonical source unit without independent conversion."},
            {"step": 4, "operation": "truth-presentation", "detail": "Render canonical value, period, source state, semantics and freshness without a second evidence lookup."},
        ],
        "assertion": assertion,
        "limitations": limitations + [
            "The Record Truth response does not perform a second indicator lookup or consult a separate packaged-snapshot value path.",
            "The record-level provenance fingerprint and canonical-observation fingerprint serve different purposes; the latter identifies the shared observation consumed by all workspace surfaces.",
        ],
    }
    return prior._record_envelope(payload)


def public_indicator_record_truth(settings: Settings, country_code: str, indicator_id: str) -> dict[str, Any]:
    del settings  # Settings retained for endpoint compatibility; canonical country evidence owns retrieval.
    return _record_from_canonical(canonical_country_indicator(country_code, indicator_id))


def public_country_record_truth(settings: Settings, country_code: str) -> dict[str, Any]:
    del settings
    catalog = canonical_country_observations(country_code)
    records = [_record_from_canonical(row) for row in catalog["observations"]]
    summary: dict[str, int] = {}
    for record in records:
        state = record.get("truth_state") or "unverified"
        summary[state] = summary.get(state, 0) + 1
    return prior._record_envelope({
        "contract": "country-record-provenance-catalog",
        "unification_contract": "workspace-evidence-unified-country-record-truth",
        "record_type": "catalog",
        "country": catalog["country"],
        "record_count": len(records),
        "summary": summary,
        "records": records,
        "canonical_observation_count": catalog["observation_count"],
        "export_endpoint": f"/public/record-truth/manifest?country={catalog['country']['code']}",
        "boundaries": [
            "Every country indicator record in this catalog resolves from the same canonical observation used by the country workspace.",
            "Missing canonical observations remain missing across workspace and Truth surfaces.",
        ],
    })


def public_map_layer_truth(settings: Settings, layer_id: str, date: str | None = None) -> dict[str, Any]:
    return prior.public_map_layer_truth(settings, layer_id, date=date)


def public_normalized_record_truth(settings: Settings, record: Mapping[str, Any]) -> dict[str, Any]:
    return prior.public_normalized_record_truth(settings, record)


def public_record_truth_manifest(settings: Settings, country_code: str) -> dict[str, Any]:
    catalog = public_country_record_truth(settings, country_code)
    entries = [{
        "record_id": record.get("record_id"),
        "record_type": record.get("record_type"),
        "truth_state": record.get("truth_state"),
        "fingerprint": (record.get("fingerprint") or {}).get("value"),
        "canonical_observation_sha256": record.get("canonical_observation_sha256"),
        "record_truth_sha256": (record.get("fingerprint") or {}).get("value"),
        "source_url": (record.get("source") or {}).get("url"),
        "observation_at": (record.get("dates") or {}).get("observation_at"),
    } for record in catalog.get("records", [])]
    for layer_id in prior.MAP_LAYERS:
        record = prior.public_map_layer_truth(settings, layer_id)
        entries.append({
            "record_id": record.get("record_id"),
            "record_type": record.get("record_type"),
            "truth_state": record.get("truth_state"),
            "fingerprint": (record.get("fingerprint") or {}).get("value"),
            "source_url": (record.get("source") or {}).get("url"),
            "observation_at": (record.get("dates") or {}).get("observation_at"),
        })
    manifest_payload = {
        "country": catalog.get("country"),
        "entry_count": len(entries),
        "entries": entries,
        "method": "sha256 over each rendered record truth response, with canonical observation SHA-256 retained for unified country indicators.",
    }
    return prior._record_envelope({
        "contract": "record-provenance-export-manifest",
        "unification_contract": "workspace-evidence-unified-record-truth-manifest",
        "record_type": "manifest",
        **manifest_payload,
        "manifest_fingerprint": prior._fingerprint(manifest_payload),
        "boundaries": [
            "Indicator entries identify the canonical observation rendered into the workspace and Truth layer.",
            "Map-layer entries retain the established context-only provenance contract.",
            "The manifest does not independently validate upstream publisher accuracy.",
        ],
    })
