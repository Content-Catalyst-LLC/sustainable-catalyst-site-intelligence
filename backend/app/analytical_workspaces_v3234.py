"""Five core analytical workflow contracts for Site Intelligence v3.23.8."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Callable, Mapping

from .config import Settings
from .earth_observation_studio import overview as earth_overview, layers as earth_layers, presets as earth_presets, diagnostics as earth_diagnostics, comparison as earth_comparison, export_manifest as earth_export_manifest
from .global_conditions_observatory import build_global_conditions_overview, build_global_conditions_signals, build_global_conditions_features, build_global_conditions_diagnostics
from .live_country_intelligence import global_country_overview, country_trends, country_brief, country_diagnostics
from .comparative_intelligence import compare_countries, comparison_brief, comparison_diagnostics
from .spatial_evidence_v2150 import SpatialEvidenceStudio
from .version import APP_VERSION

SCHEMA_VERSION = "sc-site-intelligence-analytical-workspaces/1.0"
RELEASE_ID = f"site-intelligence-v{APP_VERSION}"
POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "analytical_workspace_policy_v3234.json"
VALID_STATES = ("initial", "ready", "empty", "degraded", "unavailable")


def _policy() -> dict[str, Any]:
    payload=json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != APP_VERSION:
        raise ValueError("Analytical workspace policy version does not match the application release.")
    return payload


def _state(payload: Mapping[str, Any] | None, *, records: int | None = None) -> dict[str, Any]:
    body=dict(payload or {})
    raw=str(body.get("state") or body.get("status") or body.get("data_state") or "ready").lower().replace("-","_")
    if raw in {"error","failed","offline","unavailable"}: state="unavailable"
    elif raw in {"degraded","cached","stale","partial","limited"}: state="degraded"
    elif raw in {"empty","no_data"} or records == 0: state="empty"
    else: state="ready"
    return {"state":state,"operational":state in {"ready","empty","degraded"},"records":records,"raw_state":raw}


class AnalyticalWorkspaceCenter:
    """Expose completion contracts and bounded snapshots for the five public workflows."""
    def __init__(self, settings: Settings, providers: Mapping[str, Callable[..., Any]] | None = None) -> None:
        self.settings=settings
        self.providers=dict(providers or {})
        self.policy=_policy()
        self._index={item["workflow_id"]:item for item in self.policy["workflows"]}

    def directory(self) -> dict[str, Any]:
        workflows=[]
        for item in self.policy["workflows"]:
            row=deepcopy(item)
            row["runtime_states"]=list(VALID_STATES)
            row["source_truth_endpoint"]="/public/data-truth"
            row["deep_link"] = f"/app/?view={row['route']}"
            row["completion"]={"contract_complete":True,"export_declared":bool(row.get("export_endpoint")),"states_complete":True}
            workflows.append(row)
        return {"ok":True,"version":APP_VERSION,"release_id":RELEASE_ID,"schema":SCHEMA_VERSION,"contract":"analytical-workspace-completion","workflow_count":len(workflows),"workflows":workflows,"completion_gate":deepcopy(self.policy["completion_gate"]),"summary":{"operational":len(workflows),"limited":0,"unavailable":0}}

    def workflow(self, workflow_id: str) -> dict[str, Any]:
        if workflow_id not in self._index: raise KeyError(workflow_id)
        row=deepcopy(self._index[workflow_id])
        row.update({"runtime_states":list(VALID_STATES),"source_truth_endpoint":"/public/data-truth","deep_link":f"/app/?view={row['route']}","completion":{"contract_complete":True,"export_declared":bool(row.get("export_endpoint")),"states_complete":True}})
        return {"ok":True,"version":APP_VERSION,"release_id":RELEASE_ID,"schema":SCHEMA_VERSION,"workflow":row}

    def _call(self, key: str, fallback: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        return self.providers.get(key, fallback)(*args, **kwargs)

    def snapshot(self, workflow_id: str, parameters: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if workflow_id not in self._index: raise KeyError(workflow_id)
        p=dict(parameters or {})
        if workflow_id == "global_conditions":
            overview=self._call("global_overview", build_global_conditions_overview, self.settings)
            signals=self._call("global_signals", build_global_conditions_signals, self.settings, 30)
            features=self._call("global_features", build_global_conditions_features, self.settings, "", "", "", "", 30, 100)
            diagnostics=self._call("global_diagnostics", build_global_conditions_diagnostics, self.settings)
            count=len(features.get("features") or [])
            data={"overview":overview,"signals":signals,"features":features,"diagnostics":diagnostics}
            state=_state(overview, records=count)
        elif workflow_id == "country_intelligence":
            code=str(p.get("country") or "KEN").upper()
            overview=self._call("country_overview", global_country_overview, code)
            trends=self._call("country_trends", country_trends, code)
            brief=self._call("country_brief", country_brief, code)
            diagnostics=self._call("country_diagnostics", country_diagnostics, code)
            count=len(overview.get("highlights") or overview.get("indicators") or [])
            data={"country":code,"overview":overview,"trends":trends,"brief":brief,"diagnostics":diagnostics}
            state=_state(overview, records=count)
        elif workflow_id == "compare":
            left=str(p.get("country") or "KEN").upper(); right=str(p.get("compare") or "GHA").upper()
            comparison=self._call("compare", compare_countries, left, right)
            brief=self._call("compare_brief", comparison_brief, left, right)
            diagnostics=self._call("compare_diagnostics", comparison_diagnostics, left, right)
            count=len(comparison.get("indicators") or comparison.get("rows") or [])
            data={"country":left,"compare":right,"comparison":comparison,"brief":brief,"diagnostics":diagnostics}
            state=_state(comparison, records=count)
        elif workflow_id == "spatial_evidence":
            studio=self.providers.get("spatial_studio") or SpatialEvidenceStudio(self.settings)
            summary=studio.public_summary(); layers=studio.layers(); methodology=studio.methodology()
            area_id=str(p.get("area_id") or ""); dataset_id=str(p.get("dataset_id") or "")
            evidence=None
            if area_id and dataset_id: evidence=studio.intersection(area_id,dataset_id,public=True)
            count=len((evidence or {}).get("features") or (evidence or {}).get("matches") or []) if evidence else int(summary.get("public_datasets") or summary.get("dataset_count") or 0)
            data={"summary":summary,"layers":layers,"methodology":methodology,"evidence":evidence}
            state=_state(evidence or summary, records=count)
        else:
            layer=str(p.get("layer_id") or "true-color"); date_a=str(p.get("date_a") or ""); date_b=str(p.get("date_b") or "")
            overview=self._call("earth_overview", earth_overview)
            layer_payload=self._call("earth_layers", earth_layers)
            presets=self._call("earth_presets", earth_presets)
            diagnostics=self._call("earth_diagnostics", earth_diagnostics)
            comparison=self._call("earth_comparison", earth_comparison, layer, date_a, date_b) if date_a or date_b else None
            export=self._call("earth_export", earth_export_manifest, layer, date_a, date_b) if date_a or date_b else None
            count=len(layer_payload.get("layers") or [])
            data={"overview":overview,"layers":layer_payload,"presets":presets,"diagnostics":diagnostics,"comparison":comparison,"export":export}
            state=_state(overview, records=count)
        return {"ok":True,"version":APP_VERSION,"release_id":RELEASE_ID,"schema":SCHEMA_VERSION,"workflow":self._index[workflow_id],"state":state,"parameters":p,"data":data,"boundaries":{"source_truth_required":True,"missing_values_imputed":False,"cached_data_may_claim_live":False,"human_interpretation_required":True}}


def public_analytical_workspaces(settings: Settings) -> dict[str, Any]:
    return AnalyticalWorkspaceCenter(settings).directory()


def public_analytical_workspace(settings: Settings, workflow_id: str) -> dict[str, Any]:
    return AnalyticalWorkspaceCenter(settings).workflow(workflow_id)


def public_analytical_snapshot(settings: Settings, workflow_id: str, parameters: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return AnalyticalWorkspaceCenter(settings).snapshot(workflow_id, parameters)
