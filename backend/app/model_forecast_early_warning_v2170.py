from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
from statistics import mean
from typing import Any, Callable
from uuid import uuid4

from .config import Settings

RELEASE_VERSION = "3.1.3"
SCHEMA_VERSION = "sc-site-intelligence-model-forecast-governance/1.0"
MODEL_SCHEMA = "sc-site-intelligence-model-card/1.0"
FORECAST_SCHEMA = "sc-site-intelligence-forecast-record/1.0"
EVALUATION_SCHEMA = "sc-site-intelligence-forecast-evaluation/1.0"
WARNING_SCHEMA = "sc-site-intelligence-early-warning/1.0"
ALLOWED_MODEL_TYPES = {"statistical", "mechanistic", "machine_learning", "ensemble", "external_published"}
ALLOWED_STATUS = {"draft", "active", "paused", "retired", "expired"}
ALLOWED_VISIBILITY = {"public", "private"}
ALLOWED_DIRECTIONS = {"above", "below", "increase_pct", "decrease_pct"}
_SECRET_KEY = re.compile(r"(?:token|secret|password|authorization|api[_-]?key|email|phone|user[_-]?id)", re.I)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return Path(__file__).resolve().parents[2] / path


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _safe_id(value: str, fallback: str = "record") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(value or "").strip()).strip("-.")
    return (cleaned or fallback)[:140]


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _read_jsonl(path: Path, limit: int = 10000) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    except (FileNotFoundError, OSError):
        return []
    rows: list[dict[str, Any]] = []
    for line in lines:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): ("[redacted]" if _SECRET_KEY.search(str(k)) else _redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _validate_points(values: Any) -> list[dict[str, Any]]:
    if not isinstance(values, list) or not values:
        raise ValueError("A non-empty values array is required.")
    normalized: list[dict[str, Any]] = []
    periods: set[str] = set()
    for raw in values:
        if not isinstance(raw, dict):
            raise ValueError("Each forecast value must be an object.")
        period = str(raw.get("period") or "").strip()
        value = _number(raw.get("value"))
        if not period or period in periods or value is None:
            raise ValueError("Forecast periods must be unique and each value must be finite.")
        periods.add(period)
        lower, upper = _number(raw.get("lower")), _number(raw.get("upper"))
        if (lower is None) != (upper is None):
            raise ValueError("Forecast intervals require both lower and upper bounds.")
        if lower is not None and not lower <= value <= upper:
            raise ValueError("Forecast values must fall within their declared intervals.")
        row = {"period": period, "value": value}
        if lower is not None:
            row.update({"lower": lower, "upper": upper})
        normalized.append(row)
    return sorted(normalized, key=lambda item: item["period"])


def _metric_values(pairs: list[dict[str, float]]) -> dict[str, Any]:
    errors = [item["forecast"] - item["actual"] for item in pairs]
    abs_errors = [abs(value) for value in errors]
    squared = [value * value for value in errors]
    percentage = [abs(item["forecast"] - item["actual"]) / abs(item["actual"]) * 100 for item in pairs if item["actual"] != 0]
    smape = [200 * abs(item["forecast"] - item["actual"]) / (abs(item["forecast"]) + abs(item["actual"])) for item in pairs if abs(item["forecast"]) + abs(item["actual"]) > 0]
    return {
        "count": len(pairs),
        "mae": mean(abs_errors),
        "rmse": math.sqrt(mean(squared)),
        "bias": mean(errors),
        "mape": mean(percentage) if percentage else None,
        "smape": mean(smape) if smape else None,
    }


class ModelForecastEarlyWarningCenter:
    def __init__(self, settings: Settings, now_fn: Callable[[], datetime] = _utc_now) -> None:
        self.settings = settings
        self.now_fn = now_fn
        self.root = _resolve_path(settings.model_governance_root_path)
        self.models_path = _resolve_path(settings.model_governance_models_path)
        self.forecasts_path = _resolve_path(settings.model_governance_forecasts_path)
        self.evaluations_path = _resolve_path(settings.model_governance_evaluations_path)
        self.warning_rules_path = _resolve_path(settings.model_governance_warning_rules_path)
        self.warning_events_path = _resolve_path(settings.model_governance_warning_events_path)
        self.policy = _read_json(_resolve_path(settings.model_governance_policy_path), {})
        metrics = _read_json(_resolve_path(settings.model_governance_metric_registry_path), {})
        self.metric_registry = metrics.get("metrics", []) if isinstance(metrics, dict) else []

    def _rows(self, path: Path) -> list[dict[str, Any]]:
        return _read_jsonl(path, self.settings.model_governance_max_records)

    def _latest_models(self, public: bool = False) -> list[dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for item in self._rows(self.models_path):
            latest[str(item.get("model_id"))] = item
        rows = list(latest.values())
        if public:
            rows = [item for item in rows if item.get("visibility") == "public" and item.get("status") == "active"]
        return sorted(rows, key=lambda item: (str(item.get("title")), str(item.get("model_id"))))

    def _model(self, model_id: str, model_version: str = "", public: bool = False) -> dict[str, Any]:
        rows = [item for item in self._rows(self.models_path) if item.get("model_id") == model_id]
        if model_version:
            rows = [item for item in rows if item.get("model_version") == model_version]
        if public:
            rows = [item for item in rows if item.get("visibility") == "public" and item.get("status") == "active"]
        if not rows:
            raise KeyError(model_id)
        return rows[-1]

    def register_model(self, request: dict[str, Any]) -> dict[str, Any]:
        raw_model_id = str(request.get("model_id") or "").strip()
        model_id = _safe_id(raw_model_id)
        title = str(request.get("title") or "").strip()
        version = str(request.get("model_version") or "").strip()
        model_type = str(request.get("model_type") or "").strip().lower()
        status = str(request.get("status") or "draft").strip().lower()
        visibility = str(request.get("visibility") or "private").strip().lower()
        if not raw_model_id or not title or not version:
            raise ValueError("model_id, title, and model_version are required.")
        if model_type not in ALLOWED_MODEL_TYPES:
            raise ValueError("Unsupported model_type.")
        if status not in ALLOWED_STATUS or visibility not in ALLOWED_VISIBILITY:
            raise ValueError("Unsupported status or visibility.")
        intended = str(request.get("intended_use") or "").strip()
        limitations = str(request.get("limitations") or "").strip()
        if not intended or not limitations:
            raise ValueError("intended_use and limitations are required for every model card.")
        prohibited = [str(item)[:240] for item in request.get("prohibited_uses", []) if str(item).strip()]
        expiry = _parse_time(request.get("expires_at"))
        now = self.now_fn()
        if expiry and expiry <= now and status == "active":
            status = "expired"
        record = {
            "schema": MODEL_SCHEMA,
            "release_version": RELEASE_VERSION,
            "model_id": model_id,
            "model_version": version,
            "title": title[:240],
            "description": str(request.get("description") or "")[:2000],
            "model_type": model_type,
            "provider": str(request.get("provider") or "unknown")[:240],
            "target": str(request.get("target") or "")[:240],
            "geography": _redact(request.get("geography") or {}),
            "forecast_horizon": str(request.get("forecast_horizon") or "unspecified")[:120],
            "frequency": str(request.get("frequency") or "irregular")[:120],
            "training_period": _redact(request.get("training_period") or {}),
            "evaluation_period": _redact(request.get("evaluation_period") or {}),
            "features": [str(item)[:160] for item in request.get("features", []) if str(item).strip()][:100],
            "intended_use": intended[:2000],
            "limitations": limitations[:3000],
            "prohibited_uses": prohibited or list(self.policy.get("default_prohibited_uses", [])),
            "uncertainty_method": str(request.get("uncertainty_method") or "not declared")[:500],
            "owner": str(request.get("owner") or "Sustainable Catalyst")[:240],
            "license": str(request.get("license") or "unspecified")[:160],
            "source_url": str(request.get("source_url") or "")[:1000],
            "documentation_url": str(request.get("documentation_url") or "")[:1000],
            "visibility": visibility,
            "status": status,
            "registered_at": _iso(now),
            "expires_at": _iso(expiry) if expiry else None,
            "human_review_required": True,
            "individual_level_data_allowed": False,
            "automatic_decision_authority": False,
        }
        record["model_card_sha256"] = _digest(record)
        _append_jsonl(self.models_path, record)
        return {"ok": True, "status": "registered", "model": record}

    def models(self, public: bool = False) -> dict[str, Any]:
        rows = self._latest_models(public=public)
        return {"ok": True, "version": RELEASE_VERSION, "schema": SCHEMA_VERSION, "count": len(rows), "models": rows}

    def model_detail(self, model_id: str, model_version: str = "", public: bool = False) -> dict[str, Any]:
        model = self._model(model_id, model_version, public=public)
        forecasts = [item for item in self._rows(self.forecasts_path) if item.get("model_id") == model_id and (not public or item.get("visibility") == "public")]
        evaluations = [item for item in self._rows(self.evaluations_path) if item.get("model_id") == model_id and (not public or item.get("visibility") == "public")]
        return {"ok": True, "version": RELEASE_VERSION, "model": model, "forecast_count": len(forecasts), "evaluation_count": len(evaluations), "latest_evaluation": evaluations[-1] if evaluations else None}

    def ingest_forecast(self, request: dict[str, Any]) -> dict[str, Any]:
        model_id = _safe_id(str(request.get("model_id") or ""))
        model_version = str(request.get("model_version") or "").strip()
        model = self._model(model_id, model_version)
        if model.get("status") != "active":
            raise ValueError("Forecasts may only be ingested for active models.")
        values = _validate_points(request.get("values"))
        if len(values) > self.settings.model_governance_max_forecast_points:
            raise ValueError("Forecast point count exceeds the configured limit.")
        confidence = _number(request.get("confidence_level"))
        if confidence is not None and not 0 < confidence < 1:
            raise ValueError("confidence_level must be between 0 and 1.")
        issued = _parse_time(request.get("issued_at")) or self.now_fn()
        forecast_id = _safe_id(str(request.get("forecast_id") or f"{model_id}-{issued.strftime('%Y%m%dT%H%M%S')}"), "forecast")
        visibility = str(request.get("visibility") or model.get("visibility") or "private").lower()
        if visibility not in ALLOWED_VISIBILITY:
            raise ValueError("Unsupported forecast visibility.")
        record = {
            "schema": FORECAST_SCHEMA,
            "release_version": RELEASE_VERSION,
            "forecast_id": forecast_id,
            "model_id": model_id,
            "model_version": model.get("model_version"),
            "issued_at": _iso(issued),
            "target": str(request.get("target") or model.get("target") or "")[:240],
            "geography": _redact(request.get("geography") or model.get("geography") or {}),
            "frequency": str(request.get("frequency") or model.get("frequency") or "irregular")[:120],
            "values": values,
            "confidence_level": confidence,
            "uncertainty_method": str(request.get("uncertainty_method") or model.get("uncertainty_method") or "not declared")[:500],
            "source_reference": str(request.get("source_reference") or model.get("source_url") or "")[:1000],
            "visibility": visibility,
            "scenario_label": str(request.get("scenario_label") or "forecast")[:160],
            "forecast_not_scenario": True,
            "human_review_required": True,
        }
        record["forecast_sha256"] = _digest(record)
        _append_jsonl(self.forecasts_path, record)
        return {"ok": True, "status": "ingested", "forecast": record}

    def forecasts(self, public: bool = False, model_id: str = "", limit: int = 100) -> dict[str, Any]:
        rows = self._rows(self.forecasts_path)
        if model_id:
            rows = [item for item in rows if item.get("model_id") == model_id]
        if public:
            active = {item["model_id"] for item in self._latest_models(public=True)}
            rows = [item for item in rows if item.get("visibility") == "public" and item.get("model_id") in active]
        rows = rows[-max(1, min(limit, 1000)):]
        return {"ok": True, "version": RELEASE_VERSION, "count": len(rows), "forecasts": rows}

    def _forecast(self, forecast_id: str, public: bool = False) -> dict[str, Any]:
        rows = [item for item in self._rows(self.forecasts_path) if item.get("forecast_id") == forecast_id]
        if public:
            rows = [item for item in rows if item.get("visibility") == "public"]
        if not rows:
            raise KeyError(forecast_id)
        return rows[-1]

    def evaluate_forecast(self, request: dict[str, Any]) -> dict[str, Any]:
        forecast = self._forecast(str(request.get("forecast_id") or ""))
        actual_values = request.get("actuals")
        if not isinstance(actual_values, list) or not actual_values:
            raise ValueError("A non-empty actuals array is required.")
        actuals: dict[str, float] = {}
        for item in actual_values:
            if not isinstance(item, dict) or not str(item.get("period") or "").strip() or _number(item.get("value")) is None:
                raise ValueError("Each actual observation requires a period and finite value.")
            actuals[str(item["period"])] = float(item["value"])
        pairs: list[dict[str, float]] = []
        covered = 0
        interval_widths: list[float] = []
        for point in forecast["values"]:
            if point["period"] not in actuals:
                continue
            pair = {"period": point["period"], "forecast": float(point["value"]), "actual": actuals[point["period"]]}
            pairs.append(pair)
            if "lower" in point and "upper" in point:
                covered += int(float(point["lower"]) <= pair["actual"] <= float(point["upper"]))
                interval_widths.append(float(point["upper"]) - float(point["lower"]))
        if not pairs:
            raise ValueError("No overlapping forecast and actual periods were supplied.")
        metrics = _metric_values(pairs)
        interval_count = len(interval_widths)
        target_coverage = forecast.get("confidence_level")
        empirical_coverage = covered / interval_count if interval_count else None
        calibration_gap = abs(empirical_coverage - target_coverage) if empirical_coverage is not None and target_coverage is not None else None
        baseline_count = int(request.get("baseline_count") or max(1, len(pairs) // 2))
        baseline_count = max(1, min(baseline_count, len(pairs)))
        baseline = pairs[:baseline_count]
        recent = pairs[baseline_count:] or pairs[-baseline_count:]
        baseline_mae = _metric_values(baseline)["mae"]
        recent_mae = _metric_values(recent)["mae"]
        ratio = recent_mae / baseline_mae if baseline_mae else (0.0 if recent_mae == 0 else None)
        drift_threshold = float(request.get("drift_threshold") or self.policy.get("default_drift_ratio", 1.5))
        drift_status = "insufficient_baseline" if ratio is None else ("review" if ratio >= drift_threshold else ("watch" if ratio >= 1.2 else "stable"))
        evaluation = {
            "schema": EVALUATION_SCHEMA,
            "release_version": RELEASE_VERSION,
            "evaluation_id": _safe_id(str(request.get("evaluation_id") or f"eval-{uuid4().hex}")),
            "forecast_id": forecast["forecast_id"],
            "model_id": forecast["model_id"],
            "model_version": forecast["model_version"],
            "evaluated_at": _iso(self.now_fn()),
            "pairs": pairs,
            "metrics": metrics,
            "interval_diagnostics": {
                "interval_count": interval_count,
                "target_coverage": target_coverage,
                "empirical_coverage": empirical_coverage,
                "calibration_gap": calibration_gap,
                "mean_interval_width": mean(interval_widths) if interval_widths else None,
            },
            "drift": {
                "status": drift_status,
                "baseline_count": len(baseline),
                "recent_count": len(recent),
                "baseline_mae": baseline_mae,
                "recent_mae": recent_mae,
                "recent_to_baseline_ratio": ratio,
                "review_threshold": drift_threshold,
            },
            "visibility": str(request.get("visibility") or forecast.get("visibility") or "private"),
            "human_review_required": True,
            "accuracy_not_guaranteed": True,
        }
        evaluation["evaluation_sha256"] = _digest(evaluation)
        _append_jsonl(self.evaluations_path, evaluation)
        return {"ok": True, "status": "evaluated", "evaluation": evaluation}

    def evaluations(self, public: bool = False, model_id: str = "", limit: int = 100) -> dict[str, Any]:
        rows = self._rows(self.evaluations_path)
        if model_id:
            rows = [item for item in rows if item.get("model_id") == model_id]
        if public:
            rows = [item for item in rows if item.get("visibility") == "public"]
        rows = rows[-max(1, min(limit, 1000)):]
        return {"ok": True, "version": RELEASE_VERSION, "count": len(rows), "evaluations": rows}

    def register_warning_rule(self, request: dict[str, Any]) -> dict[str, Any]:
        raw_rule_id = str(request.get("rule_id") or "").strip()
        rule_id = _safe_id(raw_rule_id, "warning-rule")
        direction = str(request.get("direction") or "").strip().lower()
        threshold = _number(request.get("threshold"))
        if not raw_rule_id or direction not in ALLOWED_DIRECTIONS or threshold is None:
            raise ValueError("rule_id, a supported direction, and a finite threshold are required.")
        severity = str(request.get("severity") or "watch").lower()
        if severity not in {"watch", "advisory", "high"}:
            raise ValueError("severity must be watch, advisory, or high.")
        record = {
            "schema": WARNING_SCHEMA,
            "release_version": RELEASE_VERSION,
            "rule_id": rule_id,
            "title": str(request.get("title") or rule_id)[:240],
            "model_id": _safe_id(str(request.get("model_id") or "")) if request.get("model_id") else None,
            "indicator": str(request.get("indicator") or "")[:240],
            "direction": direction,
            "threshold": threshold,
            "severity": severity,
            "minimum_points": max(1, min(int(request.get("minimum_points") or 1), 100)),
            "intended_use": str(request.get("intended_use") or "Analyst review and situational awareness only.")[:1000],
            "limitations": str(request.get("limitations") or "Threshold crossings do not establish cause or guarantee an outcome.")[:1500],
            "visibility": str(request.get("visibility") or "private"),
            "active": bool(request.get("active", True)),
            "registered_at": _iso(self.now_fn()),
            "automatic_emergency_action": False,
            "individual_targeting": False,
        }
        record["rule_sha256"] = _digest(record)
        _append_jsonl(self.warning_rules_path, record)
        return {"ok": True, "status": "registered", "rule": record}

    def warning_rules(self, public: bool = False) -> list[dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for item in self._rows(self.warning_rules_path):
            latest[str(item.get("rule_id"))] = item
        rows = list(latest.values())
        if public:
            rows = [item for item in rows if item.get("visibility") == "public" and item.get("active")]
        return sorted(rows, key=lambda item: str(item.get("title")))

    def evaluate_warning(self, request: dict[str, Any]) -> dict[str, Any]:
        rule_id = str(request.get("rule_id") or "")
        rule = next((item for item in reversed(self.warning_rules()) if item.get("rule_id") == rule_id), None)
        if not rule or not rule.get("active"):
            raise KeyError(rule_id)
        values = _validate_points(request.get("values"))
        if len(values) < int(rule.get("minimum_points") or 1):
            raise ValueError("Not enough observations to evaluate the warning rule.")
        latest = float(values[-1]["value"])
        previous = float(values[-2]["value"]) if len(values) > 1 else None
        direction, threshold = rule["direction"], float(rule["threshold"])
        matched = latest > threshold if direction == "above" else latest < threshold if direction == "below" else False
        change_pct = None
        if direction in {"increase_pct", "decrease_pct"}:
            if previous is None or previous == 0:
                raise ValueError("Percent-change rules require two values and a non-zero previous value.")
            change_pct = (latest - previous) / abs(previous) * 100
            matched = change_pct >= threshold if direction == "increase_pct" else change_pct <= -abs(threshold)
        event = {
            "schema": WARNING_SCHEMA,
            "release_version": RELEASE_VERSION,
            "event_id": _safe_id(f"warning-{uuid4().hex}"),
            "rule_id": rule_id,
            "evaluated_at": _iso(self.now_fn()),
            "matched": matched,
            "severity": rule["severity"] if matched else "none",
            "latest_period": values[-1]["period"],
            "latest_value": latest,
            "previous_value": previous,
            "change_pct": change_pct,
            "threshold": threshold,
            "direction": direction,
            "evidence": values[-2:] if len(values) > 1 else values,
            "visibility": rule.get("visibility", "private"),
            "human_review_required": True,
            "not_an_emergency_service": True,
            "causation_not_established": True,
        }
        event["event_sha256"] = _digest(event)
        _append_jsonl(self.warning_events_path, event)
        return {"ok": True, "status": "matched" if matched else "clear", "event": event}

    def warning_summary(self, public: bool = False, limit: int = 100) -> dict[str, Any]:
        rules = self.warning_rules(public=public)
        allowed = {item["rule_id"] for item in rules}
        events = self._rows(self.warning_events_path)
        if public:
            events = [item for item in events if item.get("visibility") == "public" and item.get("rule_id") in allowed]
        events = events[-max(1, min(limit, 1000)):]
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "schema": WARNING_SCHEMA,
            "rule_count": len(rules),
            "event_count": len(events),
            "matched_count": sum(1 for item in events if item.get("matched")),
            "rules": rules,
            "events": events,
            "not_an_emergency_service": True,
        }

    def methodology(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "schema": SCHEMA_VERSION,
            "title": "Model, forecast, and early-warning methodology",
            "principles": self.policy.get("principles", []),
            "boundaries": self.policy.get("boundaries", []),
            "metric_registry": self.metric_registry,
            "forecast_vs_scenario": "Forecasts are model-attributed expected values. Scenarios remain user-defined assumptions and are not relabeled as forecasts.",
            "human_governance": "Every model, evaluation, drift flag, and threshold crossing requires human interpretation and review.",
        }

    def diagnostics(self, public: bool = False) -> dict[str, Any]:
        models = self._latest_models(public=public)
        forecasts = self.forecasts(public=public, limit=1000)["forecasts"]
        evaluations = self.evaluations(public=public, limit=1000)["evaluations"]
        warnings = self.warning_summary(public=public, limit=1000)
        expired = 0
        now = self.now_fn()
        for model in models:
            expiry = _parse_time(model.get("expires_at"))
            expired += int(bool(expiry and expiry <= now))
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "schema": SCHEMA_VERSION,
            "counts": {"models": len(models), "forecasts": len(forecasts), "evaluations": len(evaluations), "warning_rules": warnings["rule_count"], "warning_events": warnings["event_count"]},
            "models_needing_review": sum(1 for item in evaluations if item.get("drift", {}).get("status") in {"watch", "review"}),
            "expired_models": expired,
            "public_safe": public,
            "persistent_scheduler_active": False,
            "automatic_decision_authority": False,
        }

    def public_summary(self) -> dict[str, Any]:
        diagnostics = self.diagnostics(public=True)
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "schema": SCHEMA_VERSION,
            "title": "Model Registry, Forecast Evaluation, and Early-Warning Indicators",
            "summary": "Inspect published model cards, forecast records, evaluation evidence, calibration and drift diagnostics, and threshold-based warning indicators.",
            "counts": diagnostics["counts"],
            "models_needing_review": diagnostics["models_needing_review"],
            "methodology_endpoint": "/public/model-governance/methodology",
            "models_endpoint": "/public/models",
            "forecasts_endpoint": "/public/forecasts",
            "evaluations_endpoint": "/public/forecast-evaluations",
            "early_warning_endpoint": "/public/early-warning",
            "boundaries": ["No guaranteed outcomes", "No emergency-service claims", "No individual targeting", "No autonomous consequential decisions", "No forecast-to-scenario relabeling"],
        }

    def control_center(self) -> dict[str, Any]:
        diagnostics = self.diagnostics(public=False)
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "schema": SCHEMA_VERSION,
            "title": "Model and Forecast Governance Control Center",
            "diagnostics": diagnostics,
            "models": self.models()["models"],
            "latest_forecasts": self.forecasts(limit=25)["forecasts"],
            "latest_evaluations": self.evaluations(limit=25)["evaluations"],
            "warning_rules": self.warning_rules(),
            "latest_warning_events": self.warning_summary(limit=25)["events"],
            "operations": ["register_model", "ingest_forecast", "evaluate_forecast", "register_warning_rule", "evaluate_warning", "export_governance_packet"],
        }

    def export_governance_packet(self, model_id: str, model_version: str = "", public: bool = False) -> dict[str, Any]:
        detail = self.model_detail(model_id, model_version, public=public)
        forecasts = self.forecasts(public=public, model_id=model_id, limit=1000)["forecasts"]
        evaluations = self.evaluations(public=public, model_id=model_id, limit=1000)["evaluations"]
        warnings = [item for item in self.warning_rules(public=public) if item.get("model_id") in {None, model_id}]
        packet = {
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "generated_at": _iso(self.now_fn()),
            "model": detail["model"],
            "forecasts": forecasts,
            "evaluations": evaluations,
            "warning_rules": warnings,
            "methodology": self.methodology(),
        }
        packet["packet_sha256"] = _digest(packet)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["forecast_id", "period", "forecast", "lower", "upper"])
        for forecast in forecasts:
            for point in forecast.get("values", []):
                writer.writerow([forecast.get("forecast_id"), point.get("period"), point.get("value"), point.get("lower", ""), point.get("upper", "")])
        return {"ok": True, "version": RELEASE_VERSION, "packet": packet, "csv": output.getvalue(), "read_only": True}
