#!/usr/bin/env python3
"""Draw source-linked field evidence matrix and conceptual MRV flow."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"backend"/"app"))
from scientific_policy_figures_pb032 import render_policy_figures

p = argparse.ArgumentParser()
p.add_argument("--evidence-json", required=True)
p.add_argument("--out", required=True)
args = p.parse_args()
result = render_policy_figures(args.evidence_json, args.out)
print(json.dumps({
  "PB032_SCIENCE_FIGURES":"PASS",
  "figure_ids": list(result["figures"]),
  "publication": "REVIEW_PENDING",
  "output": args.out
},indent=2))
