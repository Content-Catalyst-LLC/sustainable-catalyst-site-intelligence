#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from backend.app.config import get_settings
from backend.app.evidence_synthesis_v2180 import EvidenceSynthesisCenter


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description="Site Intelligence v2.18.0 evidence synthesis control utility")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("summary")
    sub.add_parser("methodology")
    sub.add_parser("diagnostics")
    p = sub.add_parser("claim")
    p.add_argument("claim_id")
    p = sub.add_parser("export")
    p.add_argument("claim_id")
    p = sub.add_parser("handoff")
    p.add_argument("claim_id")
    p.add_argument("destination", choices=["knowledge-library", "research-librarian"])
    args = parser.parse_args()
    center = EvidenceSynthesisCenter(get_settings())
    if args.command == "summary": emit(center.public_summary())
    elif args.command == "methodology": emit(center.methodology())
    elif args.command == "diagnostics": emit(center.diagnostics())
    elif args.command == "claim": emit(center.claim_detail(args.claim_id))
    elif args.command == "export": emit(center.export_packet(args.claim_id))
    elif args.command == "handoff": emit(center.handoff(args.claim_id, args.destination))


if __name__ == "__main__":
    main()
