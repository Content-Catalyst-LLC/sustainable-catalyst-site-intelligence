from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from .sustainable_development_connectors import PLANETARY_BOUNDARIES, SOURCE_REGISTRY

SCHEMA = "sc-planetary-boundaries-observatory/1.0"

STATUS_LABELS = {
    "within_safe_operating_space": "Within safe operating space",
    "zone_of_increasing_risk": "Zone of increasing risk",
    "high_risk": "High risk",
    "not_globally_quantified": "Not globally quantified",
    "research_stage": "Research-stage assessment",
}

SCIENTIFIC_STATUS_LABELS = {
    "official_assessment_reference": "Published scientific assessment reference",
    "reported_observation": "Reported observation",
    "modeled_reanalysis": "Modeled or reanalysis data",
    "derived_sustainable_catalyst": "Derived Sustainable Catalyst comparison",
    "experimental_indicator": "Experimental indicator",
}

# Reference-layer records reproduce broad assessment categories only. They do not
# claim to be live measurements or a substitute for the cited scientific work.
BOUNDARY_DETAILS: Dict[str, Dict[str, Any]] = {
    "climate-change": {
        "summary": "Energy imbalance and greenhouse-gas concentrations alter the stability of the Earth system.",
        "status": "zone_of_increasing_risk",
        "coverage": "operational_foundation",
        "sdg_goals": [7, 11, 12, 13],
        "primary_sources": ["nasa-power", "un-sdg"],
        "control_variables": [
            {"id": "atmospheric-co2", "label": "Atmospheric carbon dioxide concentration", "unit": "ppm", "assessment_mode": "threshold comparison"},
            {"id": "radiative-forcing", "label": "Anthropogenic radiative forcing", "unit": "W/m²", "assessment_mode": "published assessment reference"},
        ],
    },
    "biosphere-integrity": {
        "summary": "Genetic and functional diversity support ecosystem resilience and Earth-system regulation.",
        "status": "high_risk",
        "coverage": "partial",
        "sdg_goals": [2, 14, 15],
        "primary_sources": ["un-sdg", "faostat"],
        "control_variables": [
            {"id": "genetic-diversity", "label": "Genetic diversity", "unit": "extinction-rate context", "assessment_mode": "published assessment reference"},
            {"id": "functional-integrity", "label": "Functional integrity", "unit": "ecosystem-function context", "assessment_mode": "research synthesis"},
        ],
    },
    "land-system-change": {
        "summary": "Conversion of forests and other ecosystems changes climate, water cycles, and habitat integrity.",
        "status": "zone_of_increasing_risk",
        "coverage": "partial",
        "sdg_goals": [2, 11, 13, 15],
        "primary_sources": ["faostat", "un-sdg"],
        "control_variables": [{"id": "forest-cover-biome", "label": "Forest cover by biome", "unit": "% of original forest cover", "assessment_mode": "derived indicator mapping"}],
    },
    "freshwater-change": {
        "summary": "Changes in blue and green water alter ecosystems, food systems, and hydrological stability.",
        "status": "zone_of_increasing_risk",
        "coverage": "partial",
        "sdg_goals": [2, 6, 11, 15],
        "primary_sources": ["un-water-sdg6", "un-sdg"],
        "control_variables": [
            {"id": "blue-water", "label": "Blue-water change", "unit": "basin and global context", "assessment_mode": "derived indicator mapping"},
            {"id": "green-water", "label": "Green-water change", "unit": "soil-moisture context", "assessment_mode": "research-stage adapter"},
        ],
    },
    "biogeochemical-flows": {
        "summary": "Human alteration of nitrogen and phosphorus cycles can destabilize terrestrial and aquatic systems.",
        "status": "high_risk",
        "coverage": "partial",
        "sdg_goals": [2, 6, 12, 14, 15],
        "primary_sources": ["faostat", "un-sdg"],
        "control_variables": [
            {"id": "nitrogen-flows", "label": "Nitrogen flows", "unit": "Tg N/year context", "assessment_mode": "derived indicator mapping"},
            {"id": "phosphorus-flows", "label": "Phosphorus flows", "unit": "Tg P/year context", "assessment_mode": "derived indicator mapping"},
        ],
    },
    "ocean-acidification": {
        "summary": "Ocean uptake of carbon dioxide reduces carbonate availability and threatens marine ecosystems.",
        "status": "within_safe_operating_space",
        "coverage": "annual_assessment_only",
        "sdg_goals": [13, 14],
        "primary_sources": ["un-sdg"],
        "control_variables": [{"id": "carbonate-saturation", "label": "Surface-ocean aragonite saturation", "unit": "% of preindustrial level", "assessment_mode": "published assessment reference"}],
    },
    "stratospheric-ozone": {
        "summary": "Stratospheric ozone protects life from harmful ultraviolet radiation.",
        "status": "within_safe_operating_space",
        "coverage": "annual_assessment_only",
        "sdg_goals": [3, 12, 13],
        "primary_sources": ["nasa-eonet"],
        "control_variables": [{"id": "stratospheric-ozone", "label": "Stratospheric ozone concentration", "unit": "Dobson units context", "assessment_mode": "published assessment reference"}],
    },
    "atmospheric-aerosol-loading": {
        "summary": "Aerosols affect climate, precipitation, ecosystems, and human health, with strong regional variation.",
        "status": "not_globally_quantified",
        "coverage": "research_stage",
        "sdg_goals": [3, 11, 13],
        "primary_sources": ["nasa-eonet"],
        "control_variables": [{"id": "aerosol-optical-depth", "label": "Regional aerosol optical depth", "unit": "dimensionless", "assessment_mode": "experimental regional indicator"}],
    },
    "novel-entities": {
        "summary": "Synthetic chemicals, plastics, and other novel entities may exceed society's capacity for assessment and safe management.",
        "status": "high_risk",
        "coverage": "research_stage",
        "sdg_goals": [3, 6, 12, 14, 15],
        "primary_sources": ["un-sdg"],
        "control_variables": [{"id": "novel-entities-release", "label": "Release and management of novel entities", "unit": "multi-indicator context", "assessment_mode": "research synthesis"}],
    },
}

MILESTONES = [
    {"year": 2009, "label": "Initial planetary-boundaries framework", "boundary_count_assessed": 9, "note": "Framework milestone; categories are not a time-series measurement."},
    {"year": 2015, "label": "Updated Earth-system framework", "boundary_count_assessed": 9, "note": "Control variables and regional context were refined."},
    {"year": 2023, "label": "Nine-boundary scientific assessment", "boundary_count_assessed": 9, "note": "Reference assessment used for broad status categories in this observatory."},
]

REFERENCES = [
    {"id": "stockholm-resilience-centre", "title": "Planetary Boundaries framework", "organization": "Stockholm Resilience Centre", "url": "https://www.stockholmresilience.org/research/planetary-boundaries.html", "role": "framework and public scientific context"},
    {"id": "science-advances-2023", "title": "Earth beyond six of nine planetary boundaries", "organization": "Science Advances", "url": "https://www.science.org/doi/10.1126/sciadv.adh2458", "role": "2023 reference assessment"},
    {"id": "pik-planetary-boundaries", "title": "Planetary Boundaries Science Lab", "organization": "Potsdam Institute for Climate Impact Research", "url": "https://www.pik-potsdam.de/en/institute/departments/planetary-boundaries-science", "role": "research and assessment context"},
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _source_rows(source_ids: List[str]) -> List[Dict[str, Any]]:
    rows = []
    for source_id in source_ids:
        source = next((item for item in SOURCE_REGISTRY if item["source_id"] == source_id), None)
        if source:
            rows.append({
                "source_id": source_id,
                "title": source["title"],
                "organization": source["organization"],
                "freshness_class": source["freshness_class"],
                "official_status": source["official_status"],
                "limitations": source["limitations"],
            })
    return rows


def _boundary_row(boundary_id: str) -> Dict[str, Any]:
    registry = next(item for item in PLANETARY_BOUNDARIES if item["boundary_id"] == boundary_id)
    detail = BOUNDARY_DETAILS[boundary_id]
    return {
        **registry,
        **detail,
        "status_label": STATUS_LABELS[detail["status"]],
        "scientific_status": "official_assessment_reference",
        "scientific_status_label": SCIENTIFIC_STATUS_LABELS["official_assessment_reference"],
        "is_live_assessment": False,
        "derived_assessment_available": detail["coverage"] in {"operational_foundation", "partial"},
        "sources": _source_rows(detail["primary_sources"]),
    }


def overview() -> Dict[str, Any]:
    boundaries = [_boundary_row(item["boundary_id"]) for item in PLANETARY_BOUNDARIES]
    counts = {status: sum(row["status"] == status for row in boundaries) for status in STATUS_LABELS}
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.7.0",
        "schema": SCHEMA,
        "title": "Planetary Boundaries Observatory",
        "summary": "A source-aware public observatory connecting published planetary-boundary assessments to operational environmental and sustainable-development data sources.",
        "counts": {"boundaries": len(boundaries), **counts},
        "boundaries": boundaries,
        "disclaimer": "Reference categories summarize cited scientific assessments. Sustainable Catalyst does not issue an official planetary-boundary assessment.",
        "derived_label": "Derived Sustainable Catalyst assessment based on cited observations and published planetary-boundary thresholds.",
    }


def boundary_detail(boundary_id: str) -> Dict[str, Any]:
    if boundary_id not in BOUNDARY_DETAILS:
        raise KeyError(boundary_id)
    row = _boundary_row(boundary_id)
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.7.0",
        "schema": SCHEMA,
        "boundary": row,
        "display_guidance": [
            "Show the scientific-status label beside every assessment category.",
            "Display source freshness separately from assessment date.",
            "Do not infer local legal, engineering, health, or emergency conclusions from a global boundary category.",
        ],
    }


def boundary_trend(boundary_id: str) -> Dict[str, Any]:
    if boundary_id not in BOUNDARY_DETAILS:
        raise KeyError(boundary_id)
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.7.0",
        "boundary_id": boundary_id,
        "title": f"{next(x['label'] for x in PLANETARY_BOUNDARIES if x['boundary_id'] == boundary_id)} — Assessment Milestones",
        "series_type": "scientific_assessment_milestones",
        "is_observation_time_series": False,
        "milestones": MILESTONES,
        "note": "This milestone series describes framework publications; future connector releases can add sourced observation trends for individual control variables.",
    }


def boundary_sources(boundary_id: str | None = None) -> Dict[str, Any]:
    if boundary_id:
        if boundary_id not in BOUNDARY_DETAILS:
            raise KeyError(boundary_id)
        rows = _boundary_row(boundary_id)["sources"]
    else:
        seen = []
        for detail in BOUNDARY_DETAILS.values():
            for source_id in detail["primary_sources"]:
                if source_id not in seen:
                    seen.append(source_id)
        rows = _source_rows(seen)
    return {"ok": True, "generated_at": _now(), "version_scope": "v1.7.0", "title": "Planetary Boundary Sources", "summary": "Operational data sources and scientific references supporting the observatory.", "boundary_id": boundary_id, "sources": rows, "connectors": [{**row, "label": row["title"], "status": "registered", "source_mode": row["official_status"], "family": "planetary-boundaries", "public_use": "Supports boundary control-variable context.", "safe_display": row["limitations"]} for row in rows], "references": REFERENCES}


def methodology() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.7.0",
        "schema": SCHEMA,
        "title": "Planetary Boundaries Observatory Methodology",
        "scientific_status_labels": SCIENTIFIC_STATUS_LABELS,
        "coverage_labels": {
            "operational_foundation": "Operational connector foundation",
            "partial": "Partial indicator coverage",
            "annual_assessment_only": "Published assessment context only",
            "research_stage": "Research-stage indicator mapping",
        },
        "methodology": [
            "Published framework assessments and live observations are stored and labeled separately.",
            "A fresh observation does not automatically update a global planetary-boundary conclusion.",
            "Derived comparisons must identify methodology version, source, threshold, date, unit, and uncertainty.",
            "Regional indicators must not be presented as direct replacements for global control variables.",
            "Missing or stale data remain visible through explicit coverage and freshness states.",
        ],
        "references": REFERENCES,
    }


def export_manifest() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.7.0",
        "schema": SCHEMA,
        "title": "Planetary Boundaries Observatory Export",
        "formats": ["json", "csv-ready"],
        "records": [_boundary_row(item["boundary_id"]) for item in PLANETARY_BOUNDARIES],
        "boundaries": [_boundary_row(item["boundary_id"]) for item in PLANETARY_BOUNDARIES],
        "references": REFERENCES,
        "export_notes": [
            "Broad assessment categories are reference labels, not live measurements.",
            "Source and methodology metadata must remain attached to downstream exports.",
            "Do not remove scientific-status, coverage, or derivation fields.",
        ],
    }
