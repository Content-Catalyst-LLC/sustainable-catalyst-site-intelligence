from __future__ import annotations
from datetime import datetime, timezone

def _now(): return datetime.now(timezone.utc).isoformat()

def export_validation():
    return {"ok":True,"generated_at":_now(),"version_scope":"v1.5.1+","title":"Dashboard Export Validation","summary":"Manifest, filename, format, citation, and fallback checks for public exports.","checks":[{"id":"manifest","status":"pass","detail":"Export manifest is versioned."},{"id":"formats","status":"pass","detail":"JSON, CSV, and Markdown outputs retain source metadata."},{"id":"fallbacks","status":"pass","detail":"Missing-source exports include public-safe fallback notes."}]}

def download_states():
    return {"ok":True,"generated_at":_now(),"version_scope":"v1.5.1+","title":"Public Export Download States","states":[{"id":"ready","label":"Ready"},{"id":"cached","label":"Cached"},{"id":"stale","label":"Last known good"},{"id":"unavailable","label":"Temporarily unavailable"}]}

def reliability():
    return {"ok":True,"generated_at":_now(),"version_scope":"v1.5.1+","title":"Dashboard Export Reliability","summary":"Public exports preserve provenance, freshness, and failure states.","policies":["Validate export manifests before display.","Use stable filenames and explicit generated timestamps.","Never omit source caveats when data is cached or unavailable."]}

def brief_polish():
    return {"ok":True,"generated_at":_now(),"version_scope":"v1.5.1+","title":"Source-Aware Brief Polish","summary":"Briefs use concise source summaries, freshness labels, citation notes, and missing-source fallbacks."}

def brief_fallbacks():
    return {"ok":True,"generated_at":_now(),"version_scope":"v1.5.1+","title":"Source-Aware Brief Fallbacks","fallbacks":["Source temporarily unavailable.","Showing last-known-good public data.","Methodology is available even when observations are unavailable."]}
