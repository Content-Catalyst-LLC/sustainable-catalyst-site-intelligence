#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];js=(ROOT/'backend/public_app/assets/industrial-manufacturing-v43000.js').read_text();css=(ROOT/'backend/public_app/assets/industrial-manufacturing-v43000.css').read_text();prev=(ROOT/'backend/public_app/assets/digital-connectivity-v42900.js').read_text()
for t in ['SCSIIndustrialManufacturingV43000','INDUSTRIAL & TRADE EVIDENCE','/public/industrial-manufacturing/catalog','industrialManufacturingPanel']: assert t in js,t
assert 'loadIndustrialManufacturing' in prev and 'industrial-manufacturing-v43000.js' in prev
assert '.im43000-panel' in css
print('PASS: v4.30.0 industrial manufacturing / trade direct + iframe-compatible browser asset gate')
