#!/usr/bin/env python3
from pathlib import Path
from fastapi.testclient import TestClient
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
required={
 'backend/app/version.py':['APP_VERSION = "3.28.0"'],
 'backend/app/mutation_observer_recovery_v32362.py':['public_mutation_observer_recovery_contract'],
 'backend/data/mutation_observer_recovery_policy_v32362.json':['mutation-observer-recovery-and-complete-shell-browser-gate','maximum_summary_passes_per_second'],
 'backend/public_app/assets/browser-reliability-v3235.js':['summary.textContent!==nextText','requestAnimationFrame(flushMapSummaries)','state.observer?.disconnect()','MAX_SUMMARY_PASSES_PER_SECOND=8'],
 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/browser-reliability-v3235.js':['summary.textContent!==nextText','MAX_SUMMARY_PASSES_PER_SECOND=8'],
 'scripts/browser_complete_shell_gate_v32362.py':['ERROR: Chromium or Chrome is required','SCSIDataTruthV32371','SCSIProductionTruthV3231'],
 'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php':['Version: 3.28.0'],
 'RELEASE_NOTES_SITE_INTELLIGENCE_V32362.md':['Mutation Observer Recovery and Complete-Shell Browser Gate'],
}
for rel,tokens in required.items():
 p=ROOT/rel
 if not p.is_file():raise SystemExit(f'Missing {rel}')
 text=p.read_text(encoding='utf-8')
 for token in tokens:
  if token not in text:raise SystemExit(f'Missing {token!r} in {rel}')
js=(ROOT/'backend/public_app/assets/browser-reliability-v3235.js').read_text()
if 'new MutationObserver(()=>updateMapSummaries())' in js:raise SystemExit('Unbounded observer callback remains.')
if (ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/browser-reliability-v3235.js').read_text()!=js:raise SystemExit('WordPress browser reliability asset differs from standalone app.')
client=TestClient(app)
contract=client.get('/public/mutation-observer-recovery').json()
if not contract.get('ok') or contract.get('version')!='3.28.0' or not contract.get('complete_shell_gate',{}).get('required'):raise SystemExit('Mutation observer endpoint failed.')
health=client.get('/public/runtime-health').json()
checks={row['id']:row for row in health.get('checks',[])}
if not health.get('ok') or checks.get('mutation-observer-recovery',{}).get('status')!='pass':raise SystemExit('Runtime observer recovery check failed.')
manifest=json.loads((ROOT/'MANIFEST.json').read_text()) if (ROOT/'MANIFEST.json').is_file() else None
if manifest and manifest.get('release')!='3.28.0':raise SystemExit('Manifest release mismatch.')
print('Site Intelligence v3.28.0 mutation observer recovery and complete-shell browser gate contract passed.')
