#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];js=(ROOT/'backend/public_app/assets/solid-waste-circular-v43300.js').read_text();css=(ROOT/'backend/public_app/assets/solid-waste-circular-v43300.css').read_text();prev=(ROOT/'backend/public_app/assets/water-sanitation-v43200.js').read_text()
for t in ['SCSISolidWasteCircularV43300','SOLID-WASTE & CIRCULAR-MATERIAL EVIDENCE','/public/solid-waste-circular-materials/catalog','solidWasteCircularPanel']: assert t in js,t
assert 'loadSolidWaste' in prev and 'solid-waste-circular-v43300.js' in prev
assert '.sw43300-panel' in css
print('PASS: v4.35.1 solid waste / recycling / circular-materials direct + iframe-compatible browser asset gate')
