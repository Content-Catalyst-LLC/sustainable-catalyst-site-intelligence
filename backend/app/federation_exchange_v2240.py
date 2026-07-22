from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import hmac
import io
import json
from pathlib import Path
import re
from typing import Any, Callable
from uuid import uuid4

from .config import Settings

RELEASE_VERSION = "3.18.0"
SCHEMA_VERSION = "sc-site-intelligence-federation-exchange/1.0"
CATALOG_SCHEMA = "https://www.w3.org/ns/dcat#Catalog"
DATASET_SCHEMA = "https://www.w3.org/ns/dcat#Dataset"
PROV_SCHEMA = "https://www.w3.org/ns/prov#Entity"
FEDERATION_SCHEMA = "sc-institutional-federation-manifest/1.0"
IMPORT_SCHEMA = "sc-institutional-import-receipt/1.0"
SIGNATURE_ALGORITHM = "hmac-sha256"

RECORD_TYPES = {"dataset", "publication", "service", "model", "evidence-package", "spatial-layer"}
HOSTING_MODES = {"hosted", "mirrored", "referenced"}
VISIBILITY = {"private", "unlisted", "public"}
TRUST_STATES = {"untrusted", "review", "trusted", "blocked"}
IMPORT_STATES = {"preview", "accepted", "rejected", "quarantined"}
_SECRET = re.compile(r"(?:token|secret|password|authorization|api[_-]?key|cookie|session|private[_-]?key)", re.I)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else Path(__file__).resolve().parents[2] / path


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _safe_text(value: Any, limit: int = 4000) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value or "")).strip()[:limit]


def _safe_id(value: Any, fallback: str = "record") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.:@/-]+", "-", str(value or "").strip()).strip("-:./")
    return (cleaned or fallback)[:240]


def _safe_list(value: Any, maximum: int = 200, length: int = 500) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value[:maximum]:
        token = _safe_text(item, length)
        if token and token not in output:
            output.append(token)
    return output


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): ("[redacted]" if _SECRET.search(str(key)) else _redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _read_json(path: Path, default: Any) -> Any:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default
    return value


def _read_jsonl(path: Path, limit: int = 50000) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    except (FileNotFoundError, OSError):
        return []
    rows: list[dict[str, Any]] = []
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _append(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _latest(path: Path, key: str, limit: int) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in _read_jsonl(path, limit):
        identifier = str(row.get(key) or "")
        if identifier:
            rows[identifier] = row
    return [row for row in rows.values() if not row.get("deleted")]


class InstitutionalDataExchange:
    """Open standards, federation, and institutional exchange control plane.

    The exchange validates portable manifests, catalogs, licenses, provenance, and
    signatures. It never fetches or imports a remote catalog automatically and does
    not treat a shared-secret signature as proof of institutional identity.
    """

    def __init__(self, settings: Settings, now_fn: Callable[[], datetime] = _utc_now) -> None:
        self.settings = settings
        self.now_fn = now_fn
        self.institutions_path = _resolve(settings.federation_institutions_path)
        self.records_path = _resolve(settings.federation_records_path)
        self.manifests_path = _resolve(settings.federation_manifests_path)
        self.imports_path = _resolve(settings.federation_imports_path)
        self.trust_path = _resolve(settings.federation_trust_path)
        self.policy = _read_json(_resolve(settings.federation_policy_path), {})
        self.context = _read_json(_resolve(settings.federation_context_path), {})
        self.max_records = settings.federation_max_records
        self.max_manifest_bytes = settings.federation_max_manifest_bytes
        self.signing_key = settings.federation_signing_key
        self.signing_key_id = settings.federation_signing_key_id

    def institutions(self, public: bool = False) -> list[dict[str, Any]]:
        rows = _latest(self.institutions_path, "institution_id", self.max_records)
        if public:
            rows = [self._public_institution(row) for row in rows if row.get("visibility") == "public" and row.get("status") == "active"]
        return sorted(rows, key=lambda row: str(row.get("name") or row.get("institution_id")))

    def records(self, public: bool = False) -> list[dict[str, Any]]:
        rows = _latest(self.records_path, "record_id", self.max_records)
        if public:
            rows = [self._public_record(row) for row in rows if row.get("visibility") == "public" and row.get("status") == "active"]
        return sorted(rows, key=lambda row: str(row.get("title") or row.get("record_id")))

    def manifests(self, public: bool = False) -> list[dict[str, Any]]:
        rows = _latest(self.manifests_path, "manifest_id", self.max_records)
        if public:
            rows = [self._public_manifest(row) for row in rows if row.get("visibility") == "public" and row.get("status") == "published"]
        return sorted(rows, key=lambda row: str(row.get("generated_at") or ""), reverse=True)

    def trust_policies(self) -> list[dict[str, Any]]:
        return sorted(_latest(self.trust_path, "institution_id", self.max_records), key=lambda row: str(row.get("institution_id")))

    def register_institution(self, request: dict[str, Any]) -> dict[str, Any]:
        institution_id = _safe_id(request.get("institution_id") or request.get("name"), "institution")
        name = _safe_text(request.get("name"), 300)
        if not name:
            raise ValueError("name is required")
        visibility = _safe_text(request.get("visibility") or "private", 20).lower()
        if visibility not in VISIBILITY:
            raise ValueError("Unsupported visibility")
        row = {
            "schema": "sc-federated-institution/1.0",
            "institution_id": institution_id,
            "name": name,
            "description": _safe_text(request.get("description"), 3000),
            "homepage": _safe_text(request.get("homepage"), 1000),
            "catalog_url": _safe_text(request.get("catalog_url"), 1000),
            "identifiers": _safe_list(request.get("identifiers"), 50, 300),
            "contact_label": _safe_text(request.get("contact_label"), 200),
            "visibility": visibility,
            "status": _safe_text(request.get("status") or "active", 30),
            "created_at": _iso(self.now_fn()),
        }
        row["sha256"] = _digest(row)
        _append(self.institutions_path, row)
        return row

    def register_record(self, request: dict[str, Any]) -> dict[str, Any]:
        record_type = _safe_text(request.get("record_type") or "dataset", 40).lower()
        if record_type not in RECORD_TYPES:
            raise ValueError("Unsupported record_type")
        hosting_mode = _safe_text(request.get("hosting_mode") or "hosted", 30).lower()
        if hosting_mode not in HOSTING_MODES:
            raise ValueError("Unsupported hosting_mode")
        institution_id = _safe_id(request.get("institution_id"), "")
        if not institution_id:
            raise ValueError("institution_id is required")
        if not any(row.get("institution_id") == institution_id for row in self.institutions()):
            raise ValueError("institution_id is not registered")
        title = _safe_text(request.get("title"), 500)
        if not title:
            raise ValueError("title is required")
        visibility = _safe_text(request.get("visibility") or "private", 20).lower()
        if visibility not in VISIBILITY:
            raise ValueError("Unsupported visibility")
        distributions = request.get("distributions") if isinstance(request.get("distributions"), list) else []
        clean_distributions = []
        for distribution in distributions[:100]:
            if not isinstance(distribution, dict):
                continue
            clean_distributions.append({
                "title": _safe_text(distribution.get("title"), 300),
                "access_url": _safe_text(distribution.get("access_url"), 1200),
                "download_url": _safe_text(distribution.get("download_url"), 1200),
                "media_type": _safe_text(distribution.get("media_type"), 200),
                "format": _safe_text(distribution.get("format"), 100),
                "byte_size": max(0, int(distribution.get("byte_size") or 0)),
            })
        row = {
            "schema": "sc-institutional-catalog-record/1.0",
            "record_id": _safe_id(request.get("record_id") or f"{institution_id}:{record_type}:{uuid4().hex[:12]}", "record"),
            "record_type": record_type,
            "institution_id": institution_id,
            "title": title,
            "description": _safe_text(request.get("description"), 8000),
            "keywords": _safe_list(request.get("keywords"), 100, 200),
            "themes": _safe_list(request.get("themes"), 100, 300),
            "identifiers": _safe_list(request.get("identifiers"), 100, 500),
            "license": _safe_text(request.get("license"), 1000),
            "rights": _safe_text(request.get("rights"), 2000),
            "language": _safe_text(request.get("language") or "en", 20),
            "spatial": _redact(request.get("spatial") if isinstance(request.get("spatial"), dict) else {}),
            "temporal": _redact(request.get("temporal") if isinstance(request.get("temporal"), dict) else {}),
            "provenance": _redact(request.get("provenance") if isinstance(request.get("provenance"), dict) else {}),
            "distributions": clean_distributions,
            "source_url": _safe_text(request.get("source_url"), 1200),
            "hosting_mode": hosting_mode,
            "visibility": visibility,
            "status": _safe_text(request.get("status") or "active", 30),
            "issued_at": _safe_text(request.get("issued_at"), 100),
            "modified_at": _safe_text(request.get("modified_at"), 100) or _iso(self.now_fn()),
            "registered_at": _iso(self.now_fn()),
        }
        row["sha256"] = _digest(row)
        _append(self.records_path, row)
        return row

    def set_trust_policy(self, institution_id: str, request: dict[str, Any]) -> dict[str, Any]:
        institution_id = _safe_id(institution_id, "")
        if not any(row.get("institution_id") == institution_id for row in self.institutions()):
            raise ValueError("institution_id is not registered")
        state = _safe_text(request.get("trust_state") or "review", 30).lower()
        if state not in TRUST_STATES:
            raise ValueError("Unsupported trust_state")
        row = {
            "schema": "sc-institutional-trust-policy/1.0",
            "institution_id": institution_id,
            "trust_state": state,
            "allowed_record_types": [item for item in _safe_list(request.get("allowed_record_types"), 50, 50) if item in RECORD_TYPES],
            "allowed_hosting_modes": [item for item in _safe_list(request.get("allowed_hosting_modes"), 10, 30) if item in HOSTING_MODES],
            "require_signature": bool(request.get("require_signature", True)),
            "expected_key_id": _safe_text(request.get("expected_key_id"), 200),
            "notes": _safe_text(request.get("notes"), 2000),
            "reviewed_by": _safe_text(request.get("reviewed_by") or "administrator", 200),
            "reviewed_at": _iso(self.now_fn()),
        }
        row["sha256"] = _digest(row)
        _append(self.trust_path, row)
        return row

    def build_manifest(self, institution_id: str, request: dict[str, Any] | None = None) -> dict[str, Any]:
        request = request or {}
        institution_id = _safe_id(institution_id, "")
        institution = next((row for row in self.institutions() if row.get("institution_id") == institution_id), None)
        if not institution:
            raise KeyError("Institution not found")
        record_ids = set(_safe_list(request.get("record_ids"), self.max_records, 300))
        records = [row for row in self.records() if row.get("institution_id") == institution_id and (not record_ids or row.get("record_id") in record_ids)]
        public_only = bool(request.get("public_only", False))
        if public_only:
            records = [row for row in records if row.get("visibility") == "public" and row.get("status") == "active"]
        manifest = {
            "@context": self.context or {"dcat": "http://www.w3.org/ns/dcat#", "dct": "http://purl.org/dc/terms/", "prov": "http://www.w3.org/ns/prov#"},
            "schema": FEDERATION_SCHEMA,
            "manifest_id": _safe_id(request.get("manifest_id") or f"manifest:{institution_id}:{uuid4().hex[:12]}", "manifest"),
            "institution": self._public_institution(institution),
            "generated_at": _iso(self.now_fn()),
            "visibility": _safe_text(request.get("visibility") or ("public" if public_only else "private"), 20),
            "status": "draft",
            "catalog": [self._jsonld_record(row) for row in records],
            "record_count": len(records),
            "hosting_modes": dict(Counter(row.get("hosting_mode") for row in records)),
            "exchange": {
                "automatic_import": False,
                "remote_write_performed": False,
                "identity_verified": False,
                "signature_scope": "manifest-integrity-only",
            },
        }
        if len(_canonical(manifest)) > self.max_manifest_bytes:
            raise ValueError("Manifest exceeds configured maximum bytes")
        manifest["sha256"] = _digest(manifest)
        if bool(request.get("sign")):
            manifest = self.sign_manifest(manifest)
        if bool(request.get("persist", True)):
            _append(self.manifests_path, manifest)
        return manifest

    def publish_manifest(self, manifest_id: str, request: dict[str, Any]) -> dict[str, Any]:
        if request.get("confirm") is not True:
            raise ValueError("confirm=true is required")
        current = next((row for row in self.manifests() if row.get("manifest_id") == manifest_id), None)
        if not current:
            raise KeyError("Manifest not found")
        row = dict(current)
        row["status"] = "published"
        row["visibility"] = "public"
        row["published_at"] = _iso(self.now_fn())
        row["published_by"] = _safe_text(request.get("published_by") or "administrator", 200)
        row["sha256"] = _digest({key: value for key, value in row.items() if key not in {"sha256", "signature"}})
        if current.get("signature"):
            row = self.sign_manifest(row)
        _append(self.manifests_path, row)
        return row

    def sign_manifest(self, manifest: dict[str, Any], key: str | None = None, key_id: str | None = None) -> dict[str, Any]:
        secret = key or self.signing_key
        if not secret:
            raise ValueError("A federation signing key is not configured")
        payload = {key: value for key, value in manifest.items() if key not in {"signature", "sha256"}}
        sha256 = _digest(payload)
        signature = hmac.new(secret.encode("utf-8"), _canonical(payload), hashlib.sha256).hexdigest()
        output = dict(payload)
        output["sha256"] = sha256
        output["signature"] = {
            "algorithm": SIGNATURE_ALGORITHM,
            "key_id": _safe_text(key_id or self.signing_key_id or "local-default", 200),
            "value": signature,
            "signed_at": _iso(self.now_fn()),
            "identity_verified": False,
        }
        return output

    def validate_manifest(self, manifest: Any, institution_id: str | None = None, key: str | None = None) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        if not isinstance(manifest, dict):
            return {"valid": False, "errors": ["manifest must be an object"], "warnings": []}
        if len(_canonical(manifest)) > self.max_manifest_bytes:
            errors.append("manifest exceeds configured maximum bytes")
        if manifest.get("schema") != FEDERATION_SCHEMA:
            errors.append("unsupported manifest schema")
        institution = manifest.get("institution") if isinstance(manifest.get("institution"), dict) else {}
        source_id = _safe_id(institution_id or institution.get("institution_id"), "")
        if not source_id:
            errors.append("institution.institution_id is required")
        catalog = manifest.get("catalog")
        if not isinstance(catalog, list):
            errors.append("catalog must be an array")
            catalog = []
        if len(catalog) > self.max_records:
            errors.append("catalog exceeds configured record count")
        trust = next((row for row in self.trust_policies() if row.get("institution_id") == source_id), None)
        if not trust:
            warnings.append("No local trust policy is registered for this institution")
        elif trust.get("trust_state") == "blocked":
            errors.append("institution is blocked by local trust policy")
        elif trust.get("trust_state") != "trusted":
            warnings.append("institution is not marked trusted")
        signature = manifest.get("signature") if isinstance(manifest.get("signature"), dict) else None
        signature_valid: bool | None = None
        require_signature = bool(trust.get("require_signature")) if trust else True
        if require_signature and not signature:
            errors.append("signature is required by trust policy")
        if signature:
            if signature.get("algorithm") != SIGNATURE_ALGORITHM:
                errors.append("unsupported signature algorithm")
            expected_key_id = str(trust.get("expected_key_id") or "") if trust else ""
            if expected_key_id and signature.get("key_id") != expected_key_id:
                errors.append("signature key_id does not match trust policy")
            verification_key = key or self.signing_key
            if verification_key:
                payload = {name: value for name, value in manifest.items() if name not in {"signature", "sha256"}}
                expected = hmac.new(verification_key.encode("utf-8"), _canonical(payload), hashlib.sha256).hexdigest()
                signature_valid = hmac.compare_digest(expected, str(signature.get("value") or ""))
                if not signature_valid:
                    errors.append("signature verification failed")
            else:
                warnings.append("signature present but no local verification key was supplied")
        allowed_types = set(trust.get("allowed_record_types") or []) if trust else set()
        allowed_modes = set(trust.get("allowed_hosting_modes") or []) if trust else set()
        seen: set[str] = set()
        for index, record in enumerate(catalog):
            if not isinstance(record, dict):
                errors.append(f"catalog[{index}] must be an object")
                continue
            record_id = _safe_text(record.get("@id") or record.get("record_id"), 300)
            if not record_id:
                errors.append(f"catalog[{index}] requires an identifier")
            elif record_id in seen:
                errors.append(f"duplicate catalog identifier: {record_id}")
            seen.add(record_id)
            record_type = _safe_text(record.get("record_type") or "dataset", 50)
            hosting_mode = _safe_text(record.get("hosting_mode") or "referenced", 30)
            if record_type not in RECORD_TYPES:
                errors.append(f"catalog[{index}] has unsupported record_type")
            if hosting_mode not in HOSTING_MODES:
                errors.append(f"catalog[{index}] has unsupported hosting_mode")
            if allowed_types and record_type not in allowed_types:
                errors.append(f"catalog[{index}] record_type is not allowed by trust policy")
            if allowed_modes and hosting_mode not in allowed_modes:
                errors.append(f"catalog[{index}] hosting_mode is not allowed by trust policy")
            if not record.get("license"):
                warnings.append(f"catalog[{index}] has no machine-readable license")
            if not record.get("provenance"):
                warnings.append(f"catalog[{index}] has no provenance metadata")
        return {
            "valid": not errors,
            "errors": errors,
            "warnings": list(dict.fromkeys(warnings)),
            "institution_id": source_id,
            "record_count": len(catalog),
            "signature_present": bool(signature),
            "signature_valid": signature_valid,
            "identity_verified": False,
            "automatic_import": False,
        }

    def import_preview(self, manifest: Any, institution_id: str | None = None, key: str | None = None) -> dict[str, Any]:
        validation = self.validate_manifest(manifest, institution_id, key)
        existing_ids = {row.get("record_id") for row in self.records()}
        catalog = manifest.get("catalog") if isinstance(manifest, dict) and isinstance(manifest.get("catalog"), list) else []
        incoming_ids = [_safe_text(row.get("@id") or row.get("record_id"), 300) for row in catalog if isinstance(row, dict)]
        return {
            "schema": "sc-institutional-import-preview/1.0",
            "validation": validation,
            "new_record_count": sum(1 for item in incoming_ids if item and item not in existing_ids),
            "existing_record_count": sum(1 for item in incoming_ids if item and item in existing_ids),
            "automatic_import": False,
            "remote_fetch_performed": False,
            "requires_confirm": True,
        }

    def accept_import(self, manifest: Any, request: dict[str, Any]) -> dict[str, Any]:
        if request.get("confirm") is not True:
            raise ValueError("confirm=true is required")
        institution_id = _safe_id(request.get("institution_id") or ((manifest or {}).get("institution") or {}).get("institution_id"), "")
        validation = self.validate_manifest(manifest, institution_id, request.get("verification_key"))
        status = "accepted" if validation["valid"] else "quarantined"
        receipt = {
            "schema": IMPORT_SCHEMA,
            "import_id": f"import:{uuid4().hex}",
            "institution_id": institution_id,
            "manifest_id": _safe_text((manifest or {}).get("manifest_id"), 300),
            "manifest_sha256": _safe_text((manifest or {}).get("sha256") or _digest(manifest), 100),
            "status": status,
            "validation": validation,
            "record_count": validation.get("record_count", 0),
            "accepted_at": _iso(self.now_fn()),
            "accepted_by": _safe_text(request.get("accepted_by") or "administrator", 200),
            "records_materialized": False,
            "remote_write_performed": False,
            "identity_verified": False,
        }
        receipt["sha256"] = _digest(receipt)
        _append(self.imports_path, receipt)
        return receipt

    def export_catalog(self, format_name: str = "jsonld", public_only: bool = True) -> bytes:
        records = self.records(public=public_only)
        format_name = format_name.lower()
        if format_name in {"json", "jsonld", "dcat"}:
            body = {
                "@context": self.context,
                "@type": CATALOG_SCHEMA,
                "schema": "sc-institutional-catalog-export/1.0",
                "version": RELEASE_VERSION,
                "generated_at": _iso(self.now_fn()),
                "dataset": [self._jsonld_record(row) for row in records],
                "record_count": len(records),
            }
            return json.dumps(body, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")
        if format_name == "geojson":
            features = []
            for row in records:
                spatial = row.get("spatial") if isinstance(row.get("spatial"), dict) else {}
                geometry = spatial.get("geometry") if isinstance(spatial.get("geometry"), dict) else None
                if geometry:
                    features.append({"type": "Feature", "id": row.get("record_id"), "geometry": geometry, "properties": {"title": row.get("title"), "record_type": row.get("record_type"), "license": row.get("license"), "source_url": row.get("source_url")}})
            return json.dumps({"type": "FeatureCollection", "features": features, "generated_at": _iso(self.now_fn())}, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")
        if format_name == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=["record_id", "record_type", "institution_id", "title", "license", "hosting_mode", "source_url", "modified_at", "sha256"])
            writer.writeheader()
            for row in records:
                writer.writerow({key: row.get(key, "") for key in writer.fieldnames or []})
            return output.getvalue().encode("utf-8")
        raise ValueError("Unsupported catalog export format")

    def public_summary(self) -> dict[str, Any]:
        institutions = self.institutions(public=True)
        records = self.records(public=True)
        manifests = self.manifests(public=True)
        return {
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "title": "Open Standards, Federation, and Institutional Data Exchange",
            "institutions": institutions,
            "records": records,
            "manifests": manifests,
            "summary": {
                "institution_count": len(institutions),
                "record_count": len(records),
                "manifest_count": len(manifests),
                "record_types": dict(Counter(row.get("record_type") for row in records)),
                "hosting_modes": dict(Counter(row.get("hosting_mode") for row in records)),
            },
            "standards": ["DCAT-compatible JSON-LD", "PROV-compatible provenance", "GeoJSON", "CSV", "SHA-256", "HMAC-SHA256 manifest signatures"],
            "governance": {
                "automatic_import": False,
                "automatic_remote_fetch": False,
                "remote_write_performed": False,
                "identity_verified_by_signature": False,
                "trust_policy_required": True,
                "public_private_records_exposed": False,
                "individual_tracking": False,
            },
        }

    def diagnostics(self, public: bool = False) -> dict[str, Any]:
        institutions = self.institutions()
        records = self.records()
        manifests = self.manifests()
        imports = _read_jsonl(self.imports_path, self.max_records)
        trusts = self.trust_policies()
        summary = {
            "institution_count": len(institutions),
            "record_count": len(records),
            "manifest_count": len(manifests),
            "import_count": len(imports),
            "trust_policy_count": len(trusts),
            "public_record_count": sum(1 for row in records if row.get("visibility") == "public"),
            "signed_manifest_count": sum(1 for row in manifests if row.get("signature")),
            "quarantined_import_count": sum(1 for row in imports if row.get("status") == "quarantined"),
        }
        if public:
            return {"schema": SCHEMA_VERSION, "version": RELEASE_VERSION, "summary": {"institution_count": summary["institution_count"], "public_record_count": summary["public_record_count"], "signed_manifest_count": summary["signed_manifest_count"]}, "automatic_import": False, "identity_verified_by_signature": False}
        return {"schema": SCHEMA_VERSION, "version": RELEASE_VERSION, "summary": summary, "trust_states": dict(Counter(row.get("trust_state") for row in trusts)), "hosting_modes": dict(Counter(row.get("hosting_mode") for row in records))}

    def control_center(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "diagnostics": self.diagnostics(),
            "institutions": self.institutions(),
            "records": self.records(),
            "manifests": self.manifests(),
            "trust_policies": self.trust_policies(),
            "imports": list(reversed(_read_jsonl(self.imports_path, 500))),
            "policy": self.policy,
        }

    def _public_institution(self, row: dict[str, Any]) -> dict[str, Any]:
        return {key: row.get(key) for key in ["institution_id", "name", "description", "homepage", "catalog_url", "identifiers", "status", "sha256"]}

    def _public_record(self, row: dict[str, Any]) -> dict[str, Any]:
        return {key: row.get(key) for key in ["record_id", "record_type", "institution_id", "title", "description", "keywords", "themes", "identifiers", "license", "rights", "language", "spatial", "temporal", "provenance", "distributions", "source_url", "hosting_mode", "issued_at", "modified_at", "sha256"]}

    def _public_manifest(self, row: dict[str, Any]) -> dict[str, Any]:
        return {key: row.get(key) for key in ["manifest_id", "institution", "generated_at", "visibility", "status", "record_count", "hosting_modes", "sha256", "signature", "exchange"]}

    def _jsonld_record(self, row: dict[str, Any]) -> dict[str, Any]:
        record_type = str(row.get("record_type") or "dataset")
        mapped_type = DATASET_SCHEMA if record_type in {"dataset", "spatial-layer", "evidence-package"} else "http://purl.org/dc/dcmitype/Text"
        return {
            "@id": row.get("record_id"),
            "@type": mapped_type,
            "record_type": record_type,
            "title": row.get("title"),
            "description": row.get("description"),
            "publisher": row.get("institution_id"),
            "identifier": row.get("identifiers") or [row.get("record_id")],
            "keyword": row.get("keywords") or [],
            "theme": row.get("themes") or [],
            "license": row.get("license"),
            "rights": row.get("rights"),
            "language": row.get("language"),
            "spatial": row.get("spatial"),
            "temporal": row.get("temporal"),
            "provenance": row.get("provenance"),
            "distribution": row.get("distributions") or [],
            "landingPage": row.get("source_url"),
            "hosting_mode": row.get("hosting_mode"),
            "issued": row.get("issued_at"),
            "modified": row.get("modified_at"),
            "sha256": row.get("sha256"),
        }
