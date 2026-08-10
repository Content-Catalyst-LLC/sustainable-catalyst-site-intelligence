#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];js=(ROOT/'backend/public_app/assets/agriculture-food-v42500.js').read_text();css=(ROOT/'backend/public_app/assets/agriculture-food-v42500.css').read_text();prev=(ROOT/'backend/public_app/assets/wetlands-inland-water-v42400.js').read_text()
for t in ['SCSIAgricultureFoodV42500','AGRICULTURAL EVIDENCE','/public/agriculture-food/catalog','agriculturePanel']:assert t in js,t
assert 'loadAgriculture' in prev and 'agriculture-food-v42500.js' in prev
assert '.af42500-panel' in css
print('PASS: v4.25.0 agriculture direct + iframe-compatible browser asset gate')
