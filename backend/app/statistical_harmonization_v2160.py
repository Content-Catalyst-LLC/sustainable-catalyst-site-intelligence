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
from typing import Any, Callable
from uuid import uuid4

from .config import Settings

RELEASE_VERSION = "3.4.0"
SCHEMA_VERSION = "sc-site-intelligence-statistical-harmonization/1.0"
SERIES_SCHEMA = "sc-site-intelligence-comparable-series/1.0"
TRANSFORMATION_SCHEMA = "sc-site-intelligence-transformation-lineage/1.0"
COMPARABILITY_SCHEMA = "sc-site-intelligence-comparability-diagnostic/1.0"
MISSING_CLASSES = {
    "observed", "not_available", "not_applicable", "suppressed", "estimated",
    "provisional", "break_in_series", "unknown",
}
_SECRET_KEY = re.compile(r"(?:token|secret|password|authorization|api[_-]?key|email|phone|user[_-]?id)", re.I)
_PERIOD_MONTH = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
_PERIOD_QUARTER = re.compile(r"^(\d{4})-Q([1-4])$")
_PERIOD_YEAR = re.compile(r"^(\d{4})$")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return Path(__file__).resolve().parents[2] / path


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _safe_id(value: str, fallback: str = "series") -> str:
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
        return {str(k): ("[redacted]" if _SECRET_KEY.search(str(k)) else _redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _frequency_for_period(period: str) -> str:
    if _PERIOD_MONTH.fullmatch(period):
        return "monthly"
    if _PERIOD_QUARTER.fullmatch(period):
        return "quarterly"
    if _PERIOD_YEAR.fullmatch(period):
        return "annual"
    return "irregular"


def _target_period(period: str, frequency: str) -> str:
    if frequency == "annual":
        match = re.match(r"^(\d{4})", period)
        if match:
            return match.group(1)
    if frequency == "quarterly":
        month = _PERIOD_MONTH.fullmatch(period)
        if month:
            quarter = (int(month.group(2)) - 1) // 3 + 1
            return f"{month.group(1)}-Q{quarter}"
        quarter = _PERIOD_QUARTER.fullmatch(period)
        if quarter:
            return period
    if frequency == "monthly" and _PERIOD_MONTH.fullmatch(period):
        return period
    raise ValueError(f"Period {period!r} cannot be aligned to {frequency} without an explicit supported rule.")


def _normalize_observations(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list) or not items:
        raise ValueError("A non-empty observations array is required.")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in items:
        if not isinstance(raw, dict):
            raise ValueError("Each observation must be an object.")
        period = str(raw.get("period") or "").strip()
        if not period or period in seen:
            raise ValueError("Observation periods must be non-empty and unique.")
        seen.add(period)
        value = _number(raw.get("value"))
        missing = str(raw.get("missing_class") or ("observed" if value is not None else "not_available")).strip().lower()
        if missing not in MISSING_CLASSES:
            raise ValueError(f"Unsupported missing-data class: {missing}")
        if missing == "observed" and value is None:
            raise ValueError(f"Observed period {period} requires a finite numeric value.")
        normalized.append({
            "period": period,
            "value": value,
            "missing_class": missing,
            "status": str(raw.get("status") or ("final" if missing == "observed" else missing)),
            "note": str(raw.get("note") or "")[:500],
            **({"denominator": float(raw["denominator"])} if _number(raw.get("denominator")) is not None else {}),
        })
    return sorted(normalized, key=lambda item: item["period"])


class StatisticalHarmonizationEngine:
    def __init__(self, settings: Settings, now_fn: Callable[[], datetime] = _utc_now) -> None:
        self.settings = settings
        self.now_fn = now_fn
        self.root = _resolve_path(settings.statistical_harmonization_root_path)
        self.index_path = _resolve_path(settings.statistical_harmonization_series_index_path)
        self.lineage_path = _resolve_path(settings.statistical_harmonization_lineage_path)
        self.policy = _read_json(_resolve_path(settings.statistical_harmonization_policy_path), {})
        registry = _read_json(_resolve_path(settings.statistical_harmonization_unit_registry_path), {})
        self.units = {item["code"]: item for item in registry.get("units", []) if isinstance(item, dict) and item.get("code")}
        self.currencies = {item["code"]: item for item in registry.get("currencies", []) if isinstance(item, dict) and item.get("code")}
        geography = _read_json(_resolve_path(settings.statistical_harmonization_geography_registry_path), {})
        self.geography_rules = geography.get("compatibility_rules", [])

    def _metadata(self) -> list[dict[str, Any]]:
        return _read_jsonl(self.index_path, self.settings.statistical_harmonization_max_records)

    def _payload_path(self, series_id: str, version_id: str) -> Path:
        return self.root / "series" / _safe_id(series_id) / f"{_safe_id(version_id)}.json"

    def _latest_meta(self, series_id: str, *, public: bool = False) -> dict[str, Any] | None:
        rows = [item for item in self._metadata() if item.get("series_id") == series_id]
        if public:
            rows = [item for item in rows if item.get("visibility") == "public"]
        return rows[-1] if rows else None

    def _load(self, series_id: str, version_id: str = "", *, public: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
        rows = [item for item in self._metadata() if item.get("series_id") == series_id]
        if public:
            rows = [item for item in rows if item.get("visibility") == "public"]
        meta = next((item for item in reversed(rows) if not version_id or item.get("version_id") == version_id), None)
        if not meta:
            raise KeyError(series_id if not version_id else version_id)
        payload = _read_json(self._payload_path(series_id, str(meta["version_id"])), None)
        if not isinstance(payload, dict):
            raise ValueError("Series payload is unavailable or corrupt.")
        if _digest(payload) != meta.get("payload_sha256"):
            raise ValueError("Series payload integrity verification failed.")
        return meta, payload

    def _unit(self, code: str) -> dict[str, Any]:
        if code not in self.units:
            raise ValueError(f"Unknown unit code: {code}")
        return self.units[code]

    def _convert_value(self, value: float, source_code: str, target_code: str) -> float:
        source, target = self._unit(source_code), self._unit(target_code)
        if source.get("dimension") != target.get("dimension"):
            raise ValueError(f"Units {source_code} and {target_code} are not dimensionally compatible.")
        base = value * float(source.get("factor_to_base", 1.0)) + float(source.get("offset_to_base", 0.0))
        result = (base - float(target.get("offset_to_base", 0.0))) / float(target.get("factor_to_base", 1.0))
        return result

    def register_series(self, request: dict[str, Any], *, derived_from: list[str] | None = None, lineage: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        series_id = _safe_id(str(request.get("series_id") or ""))
        if not series_id:
            raise ValueError("series_id is required.")
        unit_code = str(request.get("unit_code") or "").strip()
        self._unit(unit_code)
        observations = _normalize_observations(request.get("observations"))
        if len(observations) > self.settings.statistical_harmonization_max_observations:
            raise ValueError("Observation count exceeds the configured harmonization limit.")
        inferred = { _frequency_for_period(item["period"]) for item in observations }
        frequency = str(request.get("frequency") or (inferred.pop() if len(inferred) == 1 else "irregular")).lower()
        if frequency not in {"annual", "quarterly", "monthly", "irregular"}:
            raise ValueError("frequency must be annual, quarterly, monthly, or irregular.")
        currency_code = str(request.get("currency_code") or "").upper()
        if currency_code and currency_code not in self.currencies:
            raise ValueError(f"Unknown currency code: {currency_code}")
        geography = request.get("geography") if isinstance(request.get("geography"), dict) else {}
        payload = _redact({
            "schema": SERIES_SCHEMA,
            "series_id": series_id,
            "title": str(request.get("title") or series_id),
            "indicator_id": str(request.get("indicator_id") or series_id),
            "source": str(request.get("source") or "Source not supplied"),
            "methodology": str(request.get("methodology") or "")[:2000],
            "unit_code": unit_code,
            "currency_code": currency_code or None,
            "price_basis": str(request.get("price_basis") or "") or None,
            "base_year": request.get("base_year"),
            "frequency": frequency,
            "geography": {
                "code": str(geography.get("code") or ""),
                "name": str(geography.get("name") or geography.get("code") or "Unspecified geography"),
                "level": str(geography.get("level") or "unspecified"),
                "definition_version": str(geography.get("definition_version") or "unspecified"),
            },
            "observations": observations,
            "transformation_lineage": lineage or [],
            "derived_from": derived_from or [],
        })
        digest = _digest(payload)
        latest = self._latest_meta(series_id)
        if latest and latest.get("payload_sha256") == digest:
            return {"ok": True, "status": "unchanged", "deduplicated": True, "series": latest}
        now = self.now_fn()
        version_id = f"{now.strftime('%Y%m%dT%H%M%S%fZ')}-{digest[:12]}"
        meta = {
            "schema": SERIES_SCHEMA,
            "version": RELEASE_VERSION,
            "series_id": series_id,
            "version_id": version_id,
            "title": payload["title"],
            "indicator_id": payload["indicator_id"],
            "source": payload["source"],
            "unit_code": unit_code,
            "currency_code": currency_code or None,
            "price_basis": payload["price_basis"],
            "frequency": frequency,
            "geography": payload["geography"],
            "observation_count": len(observations),
            "observed_count": sum(1 for item in observations if item["missing_class"] == "observed"),
            "missing_count": sum(1 for item in observations if item["missing_class"] != "observed"),
            "period_start": observations[0]["period"],
            "period_end": observations[-1]["period"],
            "visibility": "public" if str(request.get("visibility") or "private").lower() == "public" else "private",
            "transformed": bool(lineage),
            "created_at": _iso(now),
            "payload_sha256": digest,
        }
        _write_json(self._payload_path(series_id, version_id), payload)
        _append_jsonl(self.index_path, meta)
        return {"ok": True, "status": "registered", "deduplicated": False, "series": meta}

    def series(self, *, public: bool = False, latest_only: bool = True) -> dict[str, Any]:
        rows = self._metadata()
        if public:
            rows = [item for item in rows if item.get("visibility") == "public"]
        if latest_only:
            latest: dict[str, dict[str, Any]] = {}
            for item in rows:
                latest[str(item.get("series_id"))] = item
            rows = list(latest.values())
        rows.sort(key=lambda item: (str(item.get("title")), str(item.get("created_at"))))
        return {"ok": True, "version": RELEASE_VERSION, "schema": SERIES_SCHEMA, "count": len(rows), "series": rows}

    def series_detail(self, series_id: str, version_id: str = "", *, public: bool = False) -> dict[str, Any]:
        meta, payload = self._load(series_id, version_id, public=public)
        return {"ok": True, "version": RELEASE_VERSION, "series": meta, "raw": payload, "view_modes": ["raw", "transformed"] if meta.get("transformed") else ["raw"]}

    def transform(self, request: dict[str, Any]) -> dict[str, Any]:
        source_id = str(request.get("series_id") or "")
        source_version = str(request.get("version_id") or "")
        meta, payload = self._load(source_id, source_version)
        observations = [dict(item) for item in payload["observations"]]
        current_unit = str(payload["unit_code"])
        current_currency = payload.get("currency_code")
        current_frequency = str(payload["frequency"])
        lineage: list[dict[str, Any]] = []
        options = request.get("transformations") if isinstance(request.get("transformations"), list) else []
        if not options:
            raise ValueError("At least one explicit transformation is required.")
        for step_number, step in enumerate(options, 1):
            if not isinstance(step, dict):
                raise ValueError("Transformation steps must be objects.")
            kind = str(step.get("type") or "").strip().lower()
            before = _digest(observations)
            parameters: dict[str, Any] = {}
            if kind == "unit_conversion":
                target = str(step.get("target_unit_code") or "")
                self._unit(target)
                for item in observations:
                    if item["missing_class"] == "observed":
                        item["value"] = self._convert_value(float(item["value"]), current_unit, target)
                parameters = {"source_unit_code": current_unit, "target_unit_code": target}
                current_unit = target
            elif kind == "per_capita":
                target_per = float(step.get("target_per") or 1)
                denominators = step.get("denominators") if isinstance(step.get("denominators"), dict) else {}
                missing = 0
                for item in observations:
                    if item["missing_class"] != "observed":
                        continue
                    denominator = _number(denominators.get(item["period"]))
                    if denominator is None:
                        denominator = _number(item.get("denominator"))
                    if denominator is None or denominator <= 0:
                        item["value"] = None
                        item["missing_class"] = "not_available"
                        item["note"] = "Denominator unavailable for explicit per-capita transformation."
                        missing += 1
                    else:
                        item["value"] = float(item["value"]) / denominator * target_per
                parameters = {"target_per": target_per, "missing_denominators": missing, "denominator_source": str(step.get("denominator_source") or "supplied transformation map")}
                parameters["output_unit_expression"] = f"{current_unit} per {int(target_per) if target_per.is_integer() else target_per:g} population units"
            elif kind == "frequency_alignment":
                target_frequency = str(step.get("target_frequency") or "").lower()
                aggregation = str(step.get("aggregation") or "").lower()
                if target_frequency not in {"annual", "quarterly", "monthly"} or aggregation not in {"sum", "mean", "latest"}:
                    raise ValueError("Frequency alignment requires target_frequency and aggregation=sum|mean|latest.")
                grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
                for item in observations:
                    grouped[_target_period(item["period"], target_frequency)].append(item)
                aligned: list[dict[str, Any]] = []
                for period, members in sorted(grouped.items()):
                    values = [float(item["value"]) for item in members if item["missing_class"] == "observed" and _number(item["value"]) is not None]
                    if not values:
                        aligned.append({"period": period, "value": None, "missing_class": "not_available", "status": "derived", "note": "No observed values available for explicit frequency aggregation."})
                    else:
                        value = sum(values) if aggregation == "sum" else (sum(values) / len(values) if aggregation == "mean" else values[-1])
                        aligned.append({"period": period, "value": value, "missing_class": "observed", "status": "derived", "note": f"Explicit {aggregation} aggregation from {len(members)} {current_frequency} records."})
                observations = aligned
                parameters = {"source_frequency": current_frequency, "target_frequency": target_frequency, "aggregation": aggregation}
                current_frequency = target_frequency
            elif kind == "currency_conversion":
                target = str(step.get("target_currency_code") or "").upper()
                if target not in self.currencies:
                    raise ValueError(f"Unknown target currency code: {target}")
                rates = step.get("rates") if isinstance(step.get("rates"), dict) else {}
                if not current_currency:
                    raise ValueError("Source series does not declare a currency code.")
                for item in observations:
                    if item["missing_class"] != "observed":
                        continue
                    rate = _number(rates.get(item["period"]))
                    if rate is None or rate <= 0:
                        item["value"] = None
                        item["missing_class"] = "not_available"
                        item["note"] = "Explicit exchange rate unavailable."
                    else:
                        item["value"] = float(item["value"]) * rate
                parameters = {"source_currency_code": current_currency, "target_currency_code": target, "rate_convention": str(step.get("rate_convention") or f"{target} per {current_currency}"), "rate_source": str(step.get("rate_source") or "supplied")}
                current_currency = target
            elif kind == "constant_price_adjustment":
                deflators = step.get("deflators") if isinstance(step.get("deflators"), dict) else {}
                base_index = float(step.get("base_index") or 100)
                for item in observations:
                    if item["missing_class"] != "observed":
                        continue
                    index = _number(deflators.get(item["period"]))
                    if index is None or index <= 0:
                        item["value"] = None
                        item["missing_class"] = "not_available"
                        item["note"] = "Deflator unavailable for constant-price adjustment."
                    else:
                        item["value"] = float(item["value"]) * base_index / index
                parameters = {"base_index": base_index, "base_year": step.get("base_year"), "deflator_source": str(step.get("deflator_source") or "supplied")}
            elif kind == "rebase_index":
                base_period = str(step.get("base_period") or "")
                target_value = float(step.get("target_value") or 100)
                base = next((_number(item["value"]) for item in observations if item["period"] == base_period and item["missing_class"] == "observed"), None)
                if base is None or base == 0:
                    raise ValueError("The requested index base period is unavailable or zero.")
                for item in observations:
                    if item["missing_class"] == "observed":
                        item["value"] = float(item["value"]) / base * target_value
                parameters = {"base_period": base_period, "target_value": target_value}
                current_unit = "index"
            else:
                raise ValueError(f"Unsupported transformation type: {kind}")
            lineage.append({
                "step": step_number,
                "type": kind,
                "parameters": _redact(parameters),
                "input_sha256": before,
                "output_sha256": _digest(observations),
                "applied_at": _iso(self.now_fn()),
                "silent": False,
            })
        output_id = _safe_id(str(request.get("output_series_id") or f"{source_id}-harmonized"))
        result = self.register_series({
            "series_id": output_id,
            "title": str(request.get("title") or f"{payload['title']} — harmonized"),
            "indicator_id": payload["indicator_id"],
            "source": payload["source"],
            "methodology": payload.get("methodology", ""),
            "unit_code": current_unit if current_unit in self.units else payload["unit_code"],
            "currency_code": current_currency,
            "price_basis": str(request.get("price_basis") or payload.get("price_basis") or "") or None,
            "base_year": request.get("base_year", payload.get("base_year")),
            "frequency": current_frequency,
            "geography": payload["geography"],
            "observations": observations,
            "visibility": str(request.get("visibility") or meta.get("visibility") or "private"),
        }, derived_from=[f"{source_id}:{meta['version_id']}"], lineage=lineage)
        result["lineage"] = lineage
        if result.get("series"):
            receipt = {"schema": TRANSFORMATION_SCHEMA, "version": RELEASE_VERSION, "transformation_id": uuid4().hex, "source_series_id": source_id, "output_series_id": output_id, "steps": lineage, "created_at": _iso(self.now_fn()), "output_version_id": result["series"].get("version_id")}
            _append_jsonl(self.lineage_path, receipt)
            result["transformation_receipt"] = receipt
        return result

    def compare(self, request: dict[str, Any], *, public: bool = False) -> dict[str, Any]:
        left_id, right_id = str(request.get("left_series_id") or ""), str(request.get("right_series_id") or "")
        left_meta, left = self._load(left_id, str(request.get("left_version_id") or ""), public=public)
        right_meta, right = self._load(right_id, str(request.get("right_version_id") or ""), public=public)
        checks: list[dict[str, Any]] = []
        def check(name: str, compatible: bool, detail: str, severity: str = "blocking") -> None:
            checks.append({"check": name, "compatible": compatible, "severity": "none" if compatible else severity, "detail": detail})
        left_unit, right_unit = self._unit(left["unit_code"]), self._unit(right["unit_code"])
        check("unit_dimension", left_unit.get("dimension") == right_unit.get("dimension"), f"{left['unit_code']} vs {right['unit_code']}")
        check("currency", left.get("currency_code") == right.get("currency_code"), f"{left.get('currency_code') or 'none'} vs {right.get('currency_code') or 'none'}")
        check("price_basis", left.get("price_basis") == right.get("price_basis"), f"{left.get('price_basis') or 'unspecified'} vs {right.get('price_basis') or 'unspecified'}")
        check("frequency", left.get("frequency") == right.get("frequency"), f"{left.get('frequency')} vs {right.get('frequency')}", "review")
        lg, rg = left.get("geography", {}), right.get("geography", {})
        same_geo = lg.get("code") == rg.get("code") and lg.get("level") == rg.get("level")
        check("geography", same_geo, f"{lg.get('code') or lg.get('name')} ({lg.get('level')}) vs {rg.get('code') or rg.get('name')} ({rg.get('level')})")
        same_definition = lg.get("definition_version") == rg.get("definition_version")
        check("geographic_definition", same_definition, f"{lg.get('definition_version')} vs {rg.get('definition_version')}", "review")
        left_periods = {item["period"] for item in left["observations"] if item["missing_class"] == "observed"}
        right_periods = {item["period"] for item in right["observations"] if item["missing_class"] == "observed"}
        overlap = sorted(left_periods & right_periods)
        check("time_overlap", bool(overlap), f"{len(overlap)} shared observed periods")
        blocking = [item for item in checks if not item["compatible"] and item["severity"] == "blocking"]
        paired = []
        if not blocking:
            lmap = {item["period"]: item for item in left["observations"]}
            rmap = {item["period"]: item for item in right["observations"]}
            for period in overlap:
                lv, rv = _number(lmap[period]["value"]), _number(rmap[period]["value"])
                if lv is not None and rv is not None:
                    converted_right = self._convert_value(rv, right["unit_code"], left["unit_code"])
                    paired.append({"period": period, "left_value": lv, "right_value": converted_right, "difference": lv - converted_right, "ratio": (lv / converted_right if converted_right else None)})
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "schema": COMPARABILITY_SCHEMA,
            "comparable": not blocking,
            "requires_review": any(not item["compatible"] for item in checks),
            "checks": checks,
            "blocking_issues": len(blocking),
            "shared_periods": overlap,
            "paired_values": paired,
            "ranking_created": False,
            "causal_claim_created": False,
            "left": left_meta,
            "right": right_meta,
        }

    def export(self, series_id: str, version_id: str = "", *, public: bool = False) -> dict[str, Any]:
        meta, payload = self._load(series_id, version_id, public=public)
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(["period", "value", "missing_class", "status", "unit_code", "currency_code", "geography_code"])
        for item in payload["observations"]:
            writer.writerow([item["period"], item["value"], item["missing_class"], item["status"], payload["unit_code"], payload.get("currency_code") or "", payload["geography"].get("code") or ""])
        packet = {"schema": SERIES_SCHEMA, "version": RELEASE_VERSION, "series": meta, "payload": payload, "exported_at": _iso(self.now_fn()), "silent_transformations": False}
        packet["packet_sha256"] = _digest(packet)
        return {"ok": True, "packet": packet, "csv": stream.getvalue(), "workbench_handoff": self.workbench_handoff(series_id, version_id, public=public)}

    def workbench_handoff(self, series_id: str, version_id: str = "", *, public: bool = False) -> dict[str, Any]:
        meta, payload = self._load(series_id, version_id, public=public)
        return {"schema": "sc-workbench-comparable-series-handoff/1.0", "source_product": "site-intelligence", "source_version": RELEASE_VERSION, "series_id": series_id, "version_id": meta["version_id"], "unit_code": payload["unit_code"], "frequency": payload["frequency"], "geography": payload["geography"], "observations": payload["observations"], "lineage": payload.get("transformation_lineage", []), "read_only": True}

    def standards(self) -> dict[str, Any]:
        return {"ok": True, "version": RELEASE_VERSION, "schema": SCHEMA_VERSION, "units": list(self.units.values()), "currencies": list(self.currencies.values()), "missing_data_classes": sorted(MISSING_CLASSES), "geography_compatibility_rules": self.geography_rules}

    def methodology(self) -> dict[str, Any]:
        return {"ok": True, "version": RELEASE_VERSION, "schema": SCHEMA_VERSION, **self.policy}

    def diagnostics(self, *, public: bool = False) -> dict[str, Any]:
        rows = self.series(public=public, latest_only=True)["series"]
        return {"ok": True, "version": RELEASE_VERSION, "counts": {"series": len(rows), "public_series": sum(1 for item in rows if item.get("visibility") == "public"), "transformed_series": sum(1 for item in rows if item.get("transformed")), "units": len(self.units), "currencies": len(self.currencies)}, "storage": {"persistent_path_configured": self.root.is_absolute(), "runtime_state_in_release": False}, "silent_normalization": False, "automatic_rankings": False}

    def public_summary(self) -> dict[str, Any]:
        diag = self.diagnostics(public=True)
        return {"ok": True, "version": RELEASE_VERSION, "schema": SCHEMA_VERSION, "title": "Statistical Harmonization and Comparable-Series Engine", "summary": "Inspect and explicitly transform units, currencies, population denominators, reporting periods, geographic definitions, price bases, missing-data classes, and index bases without silently manufacturing comparability.", "counts": diag["counts"], "recommended_shortcode": "[sc_public_comparable_series]", "capabilities": self.policy.get("capabilities", []), "boundaries": self.policy.get("boundaries", [])}

    def control_center(self) -> dict[str, Any]:
        rows = self.series(latest_only=True)["series"]
        return {"ok": True, "version": RELEASE_VERSION, "title": "Statistical Harmonization and Comparable-Series Engine", "counts": {**self.diagnostics()["counts"], "lineage_receipts": len(_read_jsonl(self.lineage_path, self.settings.statistical_harmonization_max_records))}, "series": rows[-25:], "recent_lineage": _read_jsonl(self.lineage_path, 25), "standards": {"units": len(self.units), "currencies": len(self.currencies), "missing_data_classes": len(MISSING_CLASSES)}, "rules": {"silent_normalization": False, "implicit_currency_rates": False, "implicit_imputation": False, "automatic_rankings": False}}
