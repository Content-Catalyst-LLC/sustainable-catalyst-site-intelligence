#!/usr/bin/env python3
"""Render existing owner-acquired Sentinel-2 source bytes. Offline and review-only."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "app"))
from verified_imagery_publication_pb032 import render_review_figure, SourceError

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--bbox", nargs=4, type=float, required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--stac-id", required=True)
    parser.add_argument("--provenance")
    parser.add_argument("--scl-geotiff")
    parser.add_argument("--scl-paired-provenance")
    parser.add_argument("--boundary-geojson")
    parser.add_argument("--boundary-sha256")
    parser.add_argument("--region-label", default="Wexford region")
    parser.add_argument("--figure-id", default="FIG-GEO01")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        result = render_review_figure(
            args.image, args.out,
            expected_sha256=args.source_sha256,
            bbox=args.bbox,
            acquisition_date=args.date,
            selected_stac_reference=args.stac_id,
            provenance_file=args.provenance,
            scl_tif=args.scl_geotiff,
            scl_paired_provenance=args.scl_paired_provenance,
            boundary_geojson=args.boundary_geojson,
            boundary_sha256=args.boundary_sha256,
            region_label=args.region_label,
            figure_id=args.figure_id,
        )
    except (SourceError, ValueError, OSError) as exc:
        print(f"PB032_RENDER=BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "PB032_RENDER": "PASS",
        "source_sha256": result["source"]["source_sha256"],
        "display_crs": result["display"]["derived_crs"],
        "publication": "REVIEW_ONLY",
        "workspace_write": False,
        "output": str(Path(args.out).resolve())
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
