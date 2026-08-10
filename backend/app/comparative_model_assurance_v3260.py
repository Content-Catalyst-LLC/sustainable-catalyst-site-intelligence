"""Comparative, scenario, and model assurance for Site Intelligence v4.20.0.

The assurance layer does not create forecasts or normalize incompatible records.
It makes comparison assumptions, scenario arithmetic, model-card completeness,
and reproducibility boundaries explicit and machine-readable.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from .config import Settings
from .version import APP_VERSION

SCHEMA_VERSION = "sc-site-intelligence-comparative-model-assurance/1.0"
RELEASE_ID = f"site-intelligence-v{APP_VERSION}"
POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "comparative_model_assurance_policy_v3260.json"


def _policy() -> dict[str, Any]:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != APP_VERSION:
        raise ValueError("Comparative/model assurance policy version does not match the application release.")
    return payload


def _text(value: Any, limit: int = 500) -> str:
    return str(value or "").strip()[:limit]


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def _list(value: Any, limit: int = 30) -> list[Any]:
    return list(value)[:limit] if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) else []


class ComparativeModelAssuranceCenter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.policy = _policy()

    def schema(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": APP_VERSION,
            "release_id": RELEASE_ID,
            "schema": SCHEMA_VERSION,
            "contract": "comparative-scenario-model-assurance",
            "comparison_dimensions": list(self.policy["comparison_dimensions"]),
            "scenario_modes": list(self.policy["scenario_modes"]),
            "model_card_required_fields": list(self.policy["model_card_required_fields"]),
            "method_card_count": len(self.policy["method_cards"]),
            "capabilities": [
                "baseline and reference-period disclosure",
                "unit and definition compatibility review",
                "missing-data disclosure",
                "scenario assumption ledger",
                "deterministic sensitivity analysis",
                "non-probabilistic uncertainty envelope",
                "model-card completeness review",
                "reproducible assurance packages",
            ],
            "boundaries": list(self.policy["boundaries"]),
        }

    def comparison(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        raw_records = _list((request or {}).get("records"), 200)
        normalized: list[dict[str, Any]] = []
        for index, raw in enumerate(raw_records):
            if not isinstance(raw, Mapping):
                continue
            normalized.append({
                "record_id": _text(raw.get("record_id") or raw.get("id") or f"record-{index+1}", 160),
                "geography": _text(raw.get("geography") or raw.get("geography_code") or raw.get("country"), 80).upper(),
                "indicator": _text(raw.get("indicator") or raw.get("indicator_code") or raw.get("metric"), 160),
                "value": _number(raw.get("value") if "value" in raw else raw.get("value_number")),
                "unit": _text(raw.get("unit"), 120),
                "definition_id": _text(raw.get("definition_id") or raw.get("definition") or raw.get("methodology_id"), 180),
                "period": _text(raw.get("period") or raw.get("period_start") or raw.get("year"), 80),
                "frequency": _text(raw.get("frequency"), 80).upper(),
                "price_basis": _text(raw.get("price_basis"), 160),
                "seasonal_adjustment": _text(raw.get("seasonal_adjustment"), 160),
                "source_id": _text(raw.get("source_id"), 160),
                "missing": _number(raw.get("value") if "value" in raw else raw.get("value_number")) is None,
            })
        groups: dict[str, list[dict[str, Any]]] = {}
        for record in normalized:
            key = record["indicator"] or "[unspecified indicator]"
            groups.setdefault(key, []).append(record)
        reviews: list[dict[str, Any]] = []
        for indicator, records in sorted(groups.items()):
            dimension_review: dict[str, Any] = {}
            warnings: list[str] = []
            for field in self.policy["comparison_dimensions"]:
                values = sorted({str(item.get(field) or "") for item in records if str(item.get(field) or "")})
                missing = sum(1 for item in records if not str(item.get(field) or ""))
                match = len(values) <= 1 and missing == 0
                dimension_review[field] = {"match": match, "values": values, "missing": missing}
                if not match:
                    warnings.append(f"{field.replace('_', ' ')} requires review")
            missing_values = sum(1 for item in records if item["missing"])
            if missing_values:
                warnings.append(f"{missing_values} record(s) have missing numeric values")
            state = "compatible" if not warnings else "review_required"
            reviews.append({
                "indicator": indicator,
                "record_count": len(records),
                "geographies": sorted({item["geography"] for item in records if item["geography"]}),
                "state": state,
                "direct_difference_allowed": state == "compatible" and missing_values == 0,
                "dimensions": dimension_review,
                "missing_value_count": missing_values,
                "warnings": warnings,
            })
        payload = {
            "records": normalized,
            "reviews": reviews,
            "baseline_period": _text((request or {}).get("baseline_period"), 80),
            "reference_period": _text((request or {}).get("reference_period"), 80),
            "silent_normalization": False,
            "imputation": False,
        }
        return {
            "ok": True,
            "version": APP_VERSION,
            "release_id": RELEASE_ID,
            "schema": SCHEMA_VERSION,
            "contract": "comparison-assurance-review",
            **payload,
            "summary": {
                "indicator_count": len(reviews),
                "compatible": sum(item["state"] == "compatible" for item in reviews),
                "review_required": sum(item["state"] == "review_required" for item in reviews),
                "missing_values": sum(item["missing_value_count"] for item in reviews),
            },
            "fingerprint": _digest(payload),
            "boundaries": list(self.policy["boundaries"]),
        }

    @staticmethod
    def _apply(baseline: float, assumptions: list[dict[str, Any]], overrides: Mapping[str, str] | None = None) -> tuple[float, list[dict[str, Any]]]:
        outcome = baseline
        ledger: list[dict[str, Any]] = []
        overrides = dict(overrides or {})
        for assumption in assumptions:
            selector = overrides.get(assumption["id"], "base")
            amount = assumption.get(selector)
            if amount is None:
                amount = assumption["base"]
                selector = "base"
            before = outcome
            outcome = outcome * (1 + amount / 100.0) if assumption["mode"] == "percent" else outcome + amount
            outcome = round(outcome, 12)
            ledger.append({**assumption, "applied_case": selector, "applied_value": amount, "before": before, "after": outcome})
        return outcome, ledger

    def scenario(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        source = dict(request or {})
        baseline = _number(source.get("baseline"))
        if baseline is None:
            raise ValueError("A finite numeric baseline is required.")
        assumptions: list[dict[str, Any]] = []
        for index, raw in enumerate(_list(source.get("assumptions"), 24)):
            if not isinstance(raw, Mapping):
                continue
            mode = _text(raw.get("mode"), 30).lower()
            base = _number(raw.get("base") if "base" in raw else raw.get("value"))
            if mode not in self.policy["scenario_modes"] or base is None:
                continue
            low = _number(raw.get("low")); high = _number(raw.get("high"))
            if low is not None and high is not None and low > high:
                low, high = high, low
            assumptions.append({
                "id": _text(raw.get("id") or f"assumption-{index+1}", 120),
                "label": _text(raw.get("label") or raw.get("id") or f"Assumption {index+1}", 200),
                "mode": mode,
                "base": base,
                "low": low,
                "high": high,
                "unit": _text(raw.get("unit"), 80),
                "source": _text(raw.get("source"), 300),
                "rationale": _text(raw.get("rationale"), 800),
            })
        base_outcome, ledger = self._apply(baseline, assumptions)
        sensitivity: list[dict[str, Any]] = []
        outcomes = [base_outcome]
        for assumption in assumptions:
            row: dict[str, Any] = {"assumption_id": assumption["id"], "label": assumption["label"], "base_outcome": base_outcome}
            for case in ("low", "high"):
                if assumption[case] is None:
                    row[f"{case}_outcome"] = None
                    row[f"{case}_delta"] = None
                    continue
                outcome, _ = self._apply(baseline, assumptions, {assumption["id"]: case})
                outcomes.append(outcome)
                row[f"{case}_outcome"] = outcome
                row[f"{case}_delta"] = outcome - base_outcome
            candidates = [abs(value) for value in (row.get("low_delta"), row.get("high_delta")) if value is not None]
            row["max_absolute_effect"] = max(candidates) if candidates else 0.0
            sensitivity.append(row)
        sensitivity.sort(key=lambda item: item["max_absolute_effect"], reverse=True)
        envelope = {"minimum": min(outcomes), "base": base_outcome, "maximum": max(outcomes), "probabilistic": False, "confidence_interval": False}
        packet = {
            "baseline": baseline,
            "baseline_label": _text(source.get("baseline_label"), 240),
            "baseline_period": _text(source.get("baseline_period"), 80),
            "baseline_unit": _text(source.get("unit"), 120),
            "assumptions": assumptions,
            "base_outcome": base_outcome,
            "ledger": ledger,
            "sensitivity": sensitivity,
            "uncertainty_envelope": envelope,
        }
        return {
            "ok": True,
            "version": APP_VERSION,
            "release_id": RELEASE_ID,
            "schema": SCHEMA_VERSION,
            "contract": "scenario-assurance-review",
            **packet,
            "methodology": {
                "hypothetical": True,
                "forecast": False,
                "probability": False,
                "causal_model": False,
                "recommendation": False,
                "sensitivity_method": "One assumption at a time, holding other assumptions at supplied base values.",
                "uncertainty_statement": "The envelope is the deterministic range of supplied sensitivity cases, not a confidence or prediction interval.",
            },
            "fingerprint": _digest(packet),
            "boundaries": list(self.policy["boundaries"]),
        }

    def model_review(self, card: Mapping[str, Any] | None = None) -> dict[str, Any]:
        source = dict(card or {})
        normalized: dict[str, Any] = {}
        missing: list[str] = []
        for field in self.policy["model_card_required_fields"]:
            value = source.get(field)
            if field in {"prohibited_uses", "inputs", "outputs"}:
                cleaned = [_text(item, 500) for item in _list(value, 40) if _text(item, 500)]
                normalized[field] = cleaned
                if not cleaned:
                    missing.append(field)
            else:
                normalized[field] = _text(value, 3000)
                if not normalized[field]:
                    missing.append(field)
        flags: list[str] = []
        if source.get("autonomous_decision_authority") is True:
            flags.append("autonomous decision authority is outside the public assurance boundary")
        if source.get("individual_risk_scoring") is True:
            flags.append("individual risk scoring is outside the public assurance boundary")
        state = "complete" if not missing and not flags else "review_required"
        review = {
            "card": normalized,
            "state": state,
            "complete": state == "complete",
            "missing_fields": missing,
            "boundary_flags": flags,
            "field_count": len(self.policy["model_card_required_fields"]),
            "completed_field_count": len(self.policy["model_card_required_fields"]) - len(missing),
        }
        return {
            "ok": True,
            "version": APP_VERSION,
            "release_id": RELEASE_ID,
            "schema": SCHEMA_VERSION,
            "contract": "model-card-assurance-review",
            **review,
            "fingerprint": _digest(review),
            "statement": "Completeness review does not establish predictive validity, accuracy, safety, fairness, or institutional approval.",
            "boundaries": list(self.policy["boundaries"]),
        }

    def model_cards(self) -> dict[str, Any]:
        cards = [dict(item) for item in self.policy["method_cards"]]
        registered: list[dict[str, Any]] = []
        try:
            from .model_forecast_early_warning_v2170 import ModelForecastEarlyWarningCenter
            payload = ModelForecastEarlyWarningCenter(self.settings).models(public=True)
            rows = payload.get("models") if isinstance(payload, Mapping) else []
            for row in rows or []:
                if isinstance(row, Mapping):
                    registered.append({
                        "model_id": _text(row.get("model_id"), 160),
                        "title": _text(row.get("title"), 240),
                        "model_version": _text(row.get("model_version"), 120),
                        "model_type": _text(row.get("model_type"), 120),
                        "intended_use": _text(row.get("intended_use"), 1200),
                        "limitations": _text(row.get("limitations"), 1200),
                        "prohibited_uses": [_text(item, 500) for item in _list(row.get("prohibited_uses"), 30)],
                        "uncertainty": _text(row.get("uncertainty"), 1200),
                        "validation": _text(row.get("validation"), 1200),
                        "provenance": _text(row.get("provider") or row.get("provenance"), 1200),
                        "registered_public_model": True,
                    })
        except Exception:
            registered = []
        all_cards = cards + registered
        return {
            "ok": True,
            "version": APP_VERSION,
            "release_id": RELEASE_ID,
            "schema": SCHEMA_VERSION,
            "contract": "public-assurance-model-cards",
            "method_card_count": len(cards),
            "registered_model_count": len(registered),
            "count": len(all_cards),
            "cards": all_cards,
            "boundaries": list(self.policy["boundaries"]),
        }

    def package(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        source = dict(request or {})
        payload: dict[str, Any] = {
            "title": _text(source.get("title") or "Comparative and model assurance package", 240),
            "version": APP_VERSION,
            "comparison": self.comparison(source.get("comparison")) if isinstance(source.get("comparison"), Mapping) else None,
            "scenario": self.scenario(source.get("scenario")) if isinstance(source.get("scenario"), Mapping) else None,
            "model_review": self.model_review(source.get("model_card")) if isinstance(source.get("model_card"), Mapping) else None,
            "notes": _text(source.get("notes"), 3000),
            "boundaries": list(self.policy["boundaries"]),
        }
        return {
            "ok": True,
            "version": APP_VERSION,
            "release_id": RELEASE_ID,
            "schema": SCHEMA_VERSION,
            "contract": "reproducible-assurance-package",
            **payload,
            "integrity": {"algorithm": "sha256", "digest": _digest(payload), "meaning": "content-change fingerprint, not source authentication"},
        }


def public_assurance(settings: Settings) -> dict[str, Any]:
    return ComparativeModelAssuranceCenter(settings).schema()


def public_comparison_assurance(settings: Settings, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return ComparativeModelAssuranceCenter(settings).comparison(request)


def public_scenario_assurance(settings: Settings, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return ComparativeModelAssuranceCenter(settings).scenario(request)


def public_model_assurance_review(settings: Settings, card: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return ComparativeModelAssuranceCenter(settings).model_review(card)


def public_assurance_model_cards(settings: Settings) -> dict[str, Any]:
    return ComparativeModelAssuranceCenter(settings).model_cards()


def public_assurance_package(settings: Settings, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return ComparativeModelAssuranceCenter(settings).package(request)
