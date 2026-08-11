#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];js=(ROOT/'backend/public_app/assets/water-sanitation-v43200.js').read_text();css=(ROOT/'backend/public_app/assets/water-sanitation-v43200.css').read_text();prev=(ROOT/'backend/public_app/assets/mining-critical-materials-v43100.js').read_text()
for t in ['SCSIWaterSanitationV43200','WATER & SANITATION EVIDENCE','/public/water-sanitation-infrastructure/catalog','waterSanitationPanel']: assert t in js,t
assert 'loadWaterSanitation' in prev and 'water-sanitation-v43200.js' in prev
assert '.ws43200-panel' in css
print('PASS: v4.35.0 water supply / wastewater / sanitation direct + iframe-compatible browser asset gate')
