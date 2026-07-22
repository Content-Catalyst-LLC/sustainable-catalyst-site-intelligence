from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
requirements={"backend/app/version.py":['APP_VERSION = "3.18.0"'],"backend/app/live_intelligence_preservation_exchange_v3170.py":["class LiveIntelligencePreservationExchangeCenter","def create_exchange(","def verify_exchange(","def approve_exchange(","def record_external_verification(","bagit_manifest_1_0","external_verification_human_reported","network_verification_performed","remote_deposit_performed"],"backend/app/main.py":["/public/live-intelligence/preservation-exchange/policy","/public/live-intelligence/preservation-exchange/exchanges","/public/live-intelligence/preservation-exchange/verifications","/admin/live-intelligence/preservation-exchange"],"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php":["Version: 3.18.0","sc_live_intelligence_preservation_exchange","rest_live_intelligence_preservation_exchange_status"],"wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js":["setupLiveIntelligencePreservationExchange","BagIt-aligned manifests","External checksum receipts","No remote write"],"README.md":["v3.18.0 — Preservation Interoperability, External Verification, and Institutional Exchange"],"RELEASE_NOTES_SITE_INTELLIGENCE_V3170.md":["Preservation Interoperability","external verification"],"docs/RELEASE_MANIFEST_V3170.json":['"version": "3.18.0"','"network_verification_performed": false'],"docs/live-intelligence-preservation-exchange-v3170.schema.json":["Live Intelligence Preservation Exchange",'"additionalProperties": false']}
for rel,needles in requirements.items():
 p=ROOT/rel
 if not p.exists(): raise SystemExit(f"Missing required release file: {rel}")
 text=p.read_text(encoding="utf-8")
 for needle in needles:
  if needle not in text: raise SystemExit(f"Missing {needle!r} in {rel}")
print("Site Intelligence v3.18.0 release contract passed.")
