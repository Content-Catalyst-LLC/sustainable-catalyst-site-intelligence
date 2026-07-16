#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.config import Settings  # noqa: E402
from app.knowledge_graph_v2190 import KnowledgeGraphExplorer  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Site Intelligence v2.19.0 knowledge graph utility")
    parser.add_argument("command", choices=["summary", "methodology", "diagnostics", "entities", "relationships", "resolve", "traverse", "export", "core-handoff"])
    parser.add_argument("--entity-id", default="")
    parser.add_argument("--query", default="")
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    graph = KnowledgeGraphExplorer(Settings())
    if args.command == "summary": result = graph.public_summary() if args.public else graph.control_center()
    elif args.command == "methodology": result = graph.methodology()
    elif args.command == "diagnostics": result = graph.diagnostics(public=args.public)
    elif args.command == "entities": result = graph.entities(public=args.public, query=args.query)
    elif args.command == "relationships": result = graph.relationships(public=args.public, entity_id=args.entity_id)
    elif args.command == "resolve": result = graph.resolve(args.query, public=args.public)
    elif args.command == "traverse": result = graph.traverse(args.entity_id, public=args.public, depth=args.depth)
    elif args.command == "export": result = graph.export_subgraph(args.entity_id, public=args.public, depth=args.depth)
    else: result = graph.platform_core_handoff(args.entity_id, public=args.public, depth=args.depth)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
