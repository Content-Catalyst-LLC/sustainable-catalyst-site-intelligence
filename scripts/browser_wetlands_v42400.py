#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];js=(ROOT/'backend/public_app/assets/wetlands-inland-water-v42400.js').read_text();css=(ROOT/'backend/public_app/assets/wetlands-inland-water-v42400.css').read_text();prev=(ROOT/'backend/public_app/assets/biodiversity-v42300.js').read_text()
for t in ['SCSIWetlandsInlandWaterV42400','WETLAND & INLAND-WATER EVIDENCE','/public/wetlands-inland-water/catalog','wetlandsPanel']:assert t in js,t
assert 'loadWetlands' in prev and 'wetlands-inland-water-v42400.js' in prev
assert '.wi42400-panel' in css
print('PASS: v4.24.0 wetlands direct + iframe-compatible browser asset gate')
