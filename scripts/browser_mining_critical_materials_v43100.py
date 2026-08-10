#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];js=(ROOT/'backend/public_app/assets/mining-critical-materials-v43100.js').read_text();css=(ROOT/'backend/public_app/assets/mining-critical-materials-v43100.css').read_text();prev=(ROOT/'backend/public_app/assets/industrial-manufacturing-v43000.js').read_text()
for t in ['SCSIMiningCriticalMaterialsV43100','MINERAL & MINING EVIDENCE','/public/mining-critical-materials/catalog','miningCriticalMaterialsPanel']: assert t in js,t
assert 'loadMiningCriticalMaterials' in prev and 'mining-critical-materials-v43100.js' in prev
assert '.mc43100-panel' in css
print('PASS: v4.32.0 mining / mineral resources / critical-materials direct + iframe-compatible browser asset gate')
