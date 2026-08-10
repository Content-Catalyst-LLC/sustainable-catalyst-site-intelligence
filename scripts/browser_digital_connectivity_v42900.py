#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];js=(ROOT/'backend/public_app/assets/digital-connectivity-v42900.js').read_text();css=(ROOT/'backend/public_app/assets/digital-connectivity-v42900.css').read_text();prev=(ROOT/'backend/public_app/assets/energy-systems-v42800.js').read_text()
for t in ['SCSIDigitalConnectivityV42900','DIGITAL-CONNECTIVITY EVIDENCE','/public/digital-connectivity/catalog','digitalConnectivityPanel']: assert t in js,t
assert 'loadDigitalConnectivity' in prev and 'digital-connectivity-v42900.js' in prev
assert '.dc42900-panel' in css
print('PASS: v4.29.0 digital connectivity direct + iframe-compatible browser asset gate')
