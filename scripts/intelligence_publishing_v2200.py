#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from app.config import Settings
from app.intelligence_publishing_v2200 import IntelligencePublishingStudio


def main() -> None:
    parser=argparse.ArgumentParser(description="Site Intelligence v2.20.0 publication studio CLI")
    parser.add_argument("command", choices=["summary","methodology","diagnostics","directory","detail","story-map","versions","export","handoff"])
    parser.add_argument("--publication-id", default="")
    args=parser.parse_args()
    studio=IntelligencePublishingStudio(Settings())
    if args.command=="summary": result=studio.public_summary()
    elif args.command=="methodology": result=studio.methodology()
    elif args.command=="diagnostics": result=studio.diagnostics()
    elif args.command=="directory": result=studio.public_publications()
    elif args.command=="detail": result=studio.publication_detail(args.publication_id, public=False)
    elif args.command=="story-map": result=studio.story_map(args.publication_id, public=False)
    elif args.command=="versions": result=studio.version_history(args.publication_id, public=False)
    elif args.command=="export": result=studio.export_publication(args.publication_id, public=False)
    else: result=studio.wordpress_handoff(args.publication_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__=="__main__": main()
