"""Sustainable Catalyst Site Intelligence PB03.2: offline, evidence-first image rendering.

This is an additive, *non-HTTP*, local render core. Callers must provide files
already acquired under existing provider adapters. It does not authenticate,
fetch, publish, write private projects, invent a county boundary or certify CDR.
A signed Workspace service must independently authorize all persistence.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

SCHEMA = "sc-site-intelligence-verified-imagery-figure/1.0"
HANDOFF_SCHEMA = "sc-site-intelligence-publication-figure-handoff/1.0"
EXPECTED_SHA = re.compile(r"^[a-f0-9]{64}$")
CLOUD_CLASSES = {8, 9, 10}       # Medium/high cloud probability and cirrus
SHADOW_CLASSES = {3}           # Cloud shadow
UNUSABLE_CLASSES = {0, 1}      # SCL no-data and saturated/defective
LIMIT_BYTES = 80 * 1024 * 1024
LIMIT_PIXELS = 24_000_000
MAX_FIGURE_SIZE = 5000


class SourceError(ValueError):
    """Fail-closed provenance, geography, source or quality validation."""


def sha256_file(path: str | Path) -> str:
    p = Path(path)
    if not p.is_file() or p.stat().st_size > LIMIT_BYTES:
        raise SourceError("Source is missing or exceeds the permitted byte size")
    sha = hashlib.sha256()
    with p.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def check_sha(path: str | Path, expected: str) -> str:
    if not EXPECTED_SHA.fullmatch(expected):
        raise SourceError("A 64-character lowercase source SHA-256 is required")
    actual = sha256_file(path)
    if actual != expected:
        raise SourceError("Original source SHA-256 mismatch; processing stopped")
    return actual


def check_bbox(bbox: Any) -> tuple[float, float, float, float]:
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        raise SourceError("bbox must be [west,south,east,north] in EPSG:4326")
    try:
        west, south, east, north = map(float, bbox)
    except (ValueError, TypeError) as e:
        raise SourceError("Non-numeric geographic bbox") from e
    import math
    if not all(math.isfinite(v) for v in (west,south,east,north)):
        raise SourceError("Non-finite bbox coordinate")
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise SourceError("Invalid longitude/latitude bbox")
    if east - west > 8 or north - south > 8:
        raise SourceError("Context figure must have a bounded regional extent")
    return west, south, east, north


def sanitize_identifier(value: str, kind: str = "source") -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 220:
        raise SourceError(f"{kind} identifier is missing or too long")
    if not re.fullmatch(r"[A-Za-z0-9_.:+-]+", value):
        raise SourceError(f"Invalid {kind} identifier")
    return value


def inspect_source(
    original_png: str | Path,
    *,
    expected_sha256: str,
    bbox: list[float],
    acquisition_date: str,
    selected_stac_reference: str,
    process_type: str = "day-level leastCC mosaic",
    provenance_file: str | Path | None = None,
) -> dict[str, Any]:
    """Check *exact original bytes* without interpreting cloud from RGB colours.

    Source provenance may contain arbitrary fields. Never copy the complete
    upstream JSON into a public figure or manifest (secrets may be present).
    """
    image_sha = check_sha(original_png, expected_sha256)
    region = check_bbox(bbox)
    try:
        date.fromisoformat(acquisition_date)
    except ValueError as e:
        raise SourceError("Acquisition date must be ISO YYYY-MM-DD") from e
    source_id = sanitize_identifier(selected_stac_reference)
    if process_type not in ("day-level leastCC mosaic", "exact STAC granule"):
        raise SourceError("Processing identity must declare mosaic or exact granule")
    from PIL import Image, UnidentifiedImageError
    try:
        with Image.open(original_png) as img:
            if img.format != "PNG":
                raise SourceError("Only original PNG source images are accepted")
            width, height = img.size
            if width * height > LIMIT_PIXELS or width < 32 or height < 32:
                raise SourceError("Original image dimensions exceed bounds")
            img.verify()
    except (UnidentifiedImageError, OSError, ValueError) as e:
        raise SourceError("Original PNG could not be decoded and verified") from e
    provenance = {"present": False, "sha256": None}
    if provenance_file is not None:
        prov_sha = sha256_file(provenance_file)
        try:
            p = json.loads(Path(provenance_file).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeError) as e:
            raise SourceError("Acquisition provenance is not valid JSON") from e
        if not isinstance(p, dict):
            raise SourceError("Acquisition provenance must be a JSON object")
        provenance = {"present": True, "sha256": prov_sha}
    return {
        "provider": "European Union / Copernicus Sentinel-2 L2A",
        "collection": "sentinel-2-l2a",
        "source_sha256": image_sha,
        "source_bytes": Path(original_png).stat().st_size,
        "source_dimensions": [width, height],
        "source_bbox_epsg4326": list(region),
        "acquisition_date": acquisition_date,
        "selected_stac_reference": source_id,
        "process_type": process_type,
        "exact_stac_pixel_identity_proven": process_type == "exact STAC granule",
        "acquisition_provenance": provenance,
        "source_classification": "true-color optical visualization, not chemical measurement",
    }


def quality_from_scl(scl: Any, *, paired_response_verified: bool, min_valid_fraction: float = 0.70) -> dict[str, Any]:
    """Calculate local cloud/shadow fractions only from numeric SCL pixels.

    `paired_response_verified` must come from trusted same-request provenance
    checked externally, never a user-supplied HTTP boolean. Unpaired SCL values
    may be reported for review but are not publication-qualifying evidence.
    """
    import numpy as np
    array = np.asarray(scl)
    if array.ndim != 2 or array.size == 0 or array.size > LIMIT_PIXELS:
        raise SourceError("SCL mask must be a bounded, two-dimensional raster")
    if not np.issubdtype(array.dtype, np.integer):
        raise SourceError("SCL mask requires native integer class labels")
    if np.any((array < 0) | (array > 11)):
        raise SourceError("SCL values must be Sentinel-2 classes 0 through 11")
    valid = ~np.isin(array, tuple(UNUSABLE_CLASSES))
    valid_count = int(valid.sum())
    if not valid_count:
        raise SourceError("No valid SCL pixels")
    cloudy = int((np.isin(array, tuple(CLOUD_CLASSES)) & valid).sum())
    shadow = int((np.isin(array, tuple(SHADOW_CLASSES)) & valid).sum())
    valid_fraction = valid_count / array.size
    fraction = (cloudy + shadow) / valid_count
    return {
        "state": "PAIRED_VERIFIED" if paired_response_verified else "UNPAIRED_REVIEW_ONLY",
        "paired_source_proof": bool(paired_response_verified),
        "pixel_count": int(array.size),
        "valid_fraction": round(float(valid_fraction), 6),
        "cloud_fraction_of_valid": round(float(cloudy / valid_count), 6),
        "shadow_fraction_of_valid": round(float(shadow / valid_count), 6),
        "cloud_and_shadow_fraction_of_valid": round(float(fraction), 6),
        "min_valid_fraction_required": min_valid_fraction,
        "quality_threshold_pass": bool(valid_fraction >= min_valid_fraction and fraction <= 0.15),
        "quality_threshold_is_project_policy": True,
    }


def _load_scl(scl_tif: str | Path, source: dict[str, Any]) -> Any:
    """Read same-grid SCL as numeric GeoTIFF. Original PNG is EPSG:4326 bbox-based.

    Any other mask requires documented reprojection and a separately audited
    source-alignment process. This function refuses silent resampling.
    """
    import numpy as np
    import rasterio
    from rasterio.transform import from_bounds
    check_size = Path(scl_tif).stat().st_size
    if check_size > LIMIT_BYTES:
        raise SourceError("SCL source file is too large")
    width, height = source["source_dimensions"]
    expected_transform = from_bounds(*source["source_bbox_epsg4326"], width, height)
    with rasterio.open(scl_tif) as ds:
        if ds.count != 1 or ds.width != width or ds.height != height or ds.crs is None or ds.crs.to_epsg() != 4326:
            raise SourceError("SCL raster grid does not match the original RGB grid")
        if not ds.transform.almost_equals(expected_transform):
            raise SourceError("SCL geotransform differs from original RGB bbox")
        arr = ds.read(1)
    if not np.issubdtype(arr.dtype, np.integer):
        raise SourceError("SCL class band must be integer")
    return arr


def _boundary_shape(geojson_file: str | Path, sha: str, source: dict[str, Any], target_crs: str):
    """Review-only verified-source optional boundary. Never fabricate Wexford polygon."""
    import shapely.geometry
    import shapely.ops
    from pyproj import Transformer
    check_sha(geojson_file, sha)
    data = json.loads(Path(geojson_file).read_text(encoding="utf-8"))
    if data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
        raise SourceError("Official boundary must be a GeoJSON FeatureCollection")
    if not data["features"]:
        raise SourceError("Boundary has no features")
    features = [shapely.geometry.shape(x["geometry"]) for x in data["features"]]
    if any(x.geom_type not in ("Polygon", "MultiPolygon") or not x.is_valid for x in features):
        raise SourceError("Boundary polygon has invalid geometry")
    # Caller must prove authority/licensing separately. This only checks bytes and geometry.
    from shapely.ops import unary_union
    union = unary_union(features)
    minx,miny,maxx,maxy = union.bounds
    west,south,east,north = source["source_bbox_epsg4326"]
    if not (minx>=west-0.05 and maxx<=east+0.05 and miny>=south-0.05 and maxy<=north+0.05):
        raise SourceError("Boundary extends outside the declared context area")
    tf=Transformer.from_crs("EPSG:4326",target_crs,always_xy=True).transform
    return shapely.ops.transform(tf,union)


def render_review_figure(
    original_png: str | Path,
    output_dir: str | Path,
    *,
    expected_sha256: str,
    bbox: list[float],
    acquisition_date: str,
    selected_stac_reference: str,
    provenance_file: str | Path | None = None,
    scl_tif: str | Path | None = None,
    scl_paired_provenance: str | Path | None = None,
    boundary_geojson: str | Path | None = None,
    boundary_sha256: str | None = None,
    boundary_license_reviewed: bool = False,
    region_label: str = "Wexford region",
    figure_id: str = "FIG-GEO01",
    attribution: str = "Contains modified Copernicus Sentinel data (2026). Processed by Sustainable Catalyst.",
) -> dict[str, Any]:
    """Generate source-derived **review** PNG, SVG, georeferenced TIFF, metadata.

    Optional SCL requires independently checked, same Process API response id
    provenance. Here we only accept paired proof as a manifest with source SHA,
    SCL SHA, Process request id and paired=true; release still needs signed human
    approval. This CLI is not a signing/authorization mechanism.
    """
    import numpy as np
    import rasterio
    from rasterio.transform import from_bounds
    from rasterio.warp import reproject, calculate_default_transform, Resampling
    from PIL import Image
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import ticker

    source = inspect_source(original_png, expected_sha256=expected_sha256, bbox=bbox,
        acquisition_date=acquisition_date, selected_stac_reference=selected_stac_reference,
        provenance_file=provenance_file)
    if not isinstance(region_label,str) or not 1<=len(region_label)<=90 or any(ord(c)<32 for c in region_label):
        raise SourceError("Invalid region label")
    figure_id=sanitize_identifier(figure_id,"figure")
    out=Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    with Image.open(original_png) as img:
        rgba=np.asarray(img.convert("RGBA"), dtype=np.uint8)
    h,w=rgba.shape[:2]
    west,south,east,north=source["source_bbox_epsg4326"]
    src_transform=from_bounds(west,south,east,north,w,h)
    central_longitude=(west+east)/2
    central_latitude=(south+north)/2
    utm_zone=min(60,max(1,int((central_longitude+180)//6)+1))
    epsg=(32600 if central_latitude>=0 else 32700)+utm_zone
    target_crs=f"EPSG:{epsg}"
    hemisphere="N" if central_latitude>=0 else "S"
    trans, dw, dh=calculate_default_transform("EPSG:4326", target_crs, w,h, left=west,bottom=south,right=east,top=north)
    if dw*dh > LIMIT_PIXELS or dw > MAX_FIGURE_SIZE or dh > MAX_FIGURE_SIZE:
        raise SourceError("Projected preview would exceed rendering limits")
    dst=np.zeros((4,dh,dw),dtype=np.uint8)
    for band in range(4):
        reproject(rgba[:,:,band],dst[band],src_transform=src_transform,src_crs="EPSG:4326",
           dst_transform=trans,dst_crs=target_crs,
           resampling=Resampling.nearest if band==3 else Resampling.bilinear)
    geotiff=out/f"context_georectified_EPSG{epsg}.tif"
    profile={"driver":"GTiff","height":dh,"width":dw,"count":4,"dtype":"uint8",
            "crs":target_crs,"transform":trans,"compress":"deflate", "tiled":True}
    with rasterio.open(geotiff,"w",**profile) as ds:
        ds.write(dst)
        ds.update_tags(AREA_OR_POINT="Area", note="Georeferenced Process API preview, NOT native 10m analysis pixels")
    x0,y0,x1,y1=rasterio.transform.array_bounds(dh,dw,trans)
    scl_info={"state":"NOT_ACQUIRED", "cloud_fraction_of_valid":None,
              "shadow_fraction_of_valid":None,"paired_source_proof":False,
              "quality_threshold_pass":False}
    if scl_tif is not None:
        mask=_load_scl(scl_tif,source)
        paired=False
        if scl_paired_provenance is not None:
            proof=json.loads(Path(scl_paired_provenance).read_text(encoding="utf-8"))
            # A *declaration* in a local file is only a review claim and not
            # independently authenticated evidence of server origin.
            paired=(proof.get("source_sha256")==source["source_sha256"] and
                    proof.get("scl_sha256")==sha256_file(scl_tif) and
                    proof.get("same_process_response") is True and
                    isinstance(proof.get("response_id"),str) and bool(proof["response_id"].strip()))
        scl_info=quality_from_scl(mask,paired_response_verified=False)
        scl_info["same_response_evidence_declared"] = paired
        scl_info["scl_sha256"]=sha256_file(scl_tif)
        # Untrusted caller can't assert verified=True. A separate secured
        # object-ingestion service must verify source response receipts.
    boundary_status="NOT_SUPPLIED"
    boundary_geom=None
    if boundary_geojson is not None:
        if not boundary_sha256:
            raise SourceError("Boundary original SHA-256 is required")
        boundary_geom=_boundary_shape(boundary_geojson,boundary_sha256,source,target_crs)
        boundary_status="GEOMETRY_CHECKED_LICENSE_REVIEWED" if boundary_license_reviewed else "GEOMETRY_CHECKED_RIGHTS_PENDING"

    # Layout deliberately labels this a regional context image, not a verified
    # county outline or an ERW study treatment plot.
    fig,ax=plt.subplots(figsize=(7.5,8.15))
    fig.patch.set_facecolor("white")
    # Reserve a fixed caption region: constrained_layout previously let the
    # projected image/tick labels overlap the scientific provenance footer.
    fig.subplots_adjust(left=.14,right=.95,top=.91,bottom=.23)
    ax.imshow(np.moveaxis(dst,0,2),extent=(x0,x1,y0,y1),origin="upper")
    if boundary_geom is not None:
        geometries=[boundary_geom] if boundary_geom.geom_type=="Polygon" else list(boundary_geom.geoms)
        for poly in geometries:
            xs,ys=poly.exterior.xy
            ax.plot(xs,ys,linewidth=1.0,label="Provided boundary (rights unverified)")
    ax.set_aspect("equal",adjustable="box")
    ax.set_title(f"{region_label} | Sentinel-2 true-colour context",loc="left",fontsize=12)
    ax.set_xlabel(f"UTM {utm_zone}{hemisphere} easting (km; {target_crs})",fontsize=9)
    ax.set_ylabel(f"UTM {utm_zone}{hemisphere} northing (km; {target_crs})",fontsize=9)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v,pos: f"{v/1000:.0f}"))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v,pos: f"{v/1000:.0f}"))
    ax.tick_params(labelsize=8)
    ax.grid(alpha=.17)
    fig.text(.13,.14,"REVIEW ONLY — optical cloud quality / research ownership pending",fontsize=10,weight="bold")
    fig.text(.13,.11, f"{acquisition_date} · regional day-level Process API mosaic · no verified study site",fontsize=8)
    fig.text(.13,.085,attribution,fontsize=7)
    png=out/f"{figure_id}_region_context_REVIEW.png"
    svg=out/f"{figure_id}_region_context_REVIEW.svg"
    fig.savefig(png,dpi=200,metadata={"Software":"Sustainable Catalyst Site Intelligence"})
    fig.savefig(svg,metadata={"Creator":"Sustainable Catalyst Site Intelligence"})
    plt.close(fig)
    # A provisional Figure-to-Publication contract. Explicitly NOT an
    # authenticated research object or permission to redistribute originals.
    derived={
        "png":{"name":png.name,"sha256":sha256_file(png),"bytes":png.stat().st_size},
        "svg":{"name":svg.name,"sha256":sha256_file(svg),"bytes":svg.stat().st_size},
        "geotiff":{"name":geotiff.name,"sha256":sha256_file(geotiff),"bytes":geotiff.stat().st_size},
    }
    manifest={
        "schema":SCHEMA,
        "figure_id":figure_id,
        "title":f"{region_label} Sentinel-2 geographic context",
        "source":source,
        "display":{"derived_crs":target_crs,"geotiff_width":dw,"geotiff_height":dh,
           "preview_ground_pixel_m_approx":round((abs(trans.a)+abs(trans.e))/2,2),
           "not_native_10m_sentinel_bands":True,"reprojection":"rasterio bilinear for RGB, nearest for alpha"},
        "quality":{"scl":scl_info,"boundary":boundary_status,
            "source_geography":"REGIONAL_RECTANGLE_NOT_VERIFIED_COUNTY_OR_PLOT",
            "bbox_authority":"OPERATOR_SUPPLIED_FROM_PRESERVED_ACQUISITION_METADATA",
            "visual_review":"REQUIRED", "scl_same_response_independent_verification":"REQUIRED"},
        "rights":{"copernicus_original_source":"OPEN_SENTINEL_DATA_LICENSE_REVIEW_REQUIRED",
            "derivative_attribution":attribution,"third_party_layers":"NONE" if boundary_geom is None else "REVIEW_REQUIRED"},
        "assets":derived,
        "scientific_interpretation":"Geographical context only; not evidence of chemical weathering, CO2 removal, or source attribution to one tile.",
        "publication":{"eligible":False,"approval":"REVIEW_ONLY","signed_owner_project_binding":"NOT_PERFORMED",
            "save_reopen_export":"NOT_PERFORMED", "automatic_publication":False},
        "site_intelligence_handoff":{"target":"Site Intelligence v4.51 spatial research object",
            "server_object_created":False,"owner_authorization":"UNVERIFIED"},
    }
    handoff={
        "schema":HANDOFF_SCHEMA,
        "figureId":figure_id, "role":"optional-geographic-context", "classification":"review-only",
        "sourceSha256":source["source_sha256"],"sourceId":source["selected_stac_reference"],
        "derivedAssets":derived,"caption":f"{region_label}, {acquisition_date}. Optical satellite context; clouds and study sites not verified.",
        "attribution":attribution,
        "publicationEligible":False,
        "projectId":None,
        "projectOwnerVerified":False,
        "persistence":"NOT_PERFORMED",
    }
    (out/"FIG-GEO01-manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"FIG-GEO01-publication-handoff.json").write_text(json.dumps(handoff,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return manifest