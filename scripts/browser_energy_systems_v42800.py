#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];js=(ROOT/'backend/public_app/assets/energy-systems-v42800.js').read_text();css=(ROOT/'backend/public_app/assets/energy-systems-v42800.css').read_text();prev=(ROOT/'backend/public_app/assets/transportation-infrastructure-v42700.js').read_text()
for t in ['SCSIEnergySystemsV42800','ENERGY-SYSTEM EVIDENCE','/public/energy-systems/catalog','energySystemsPanel']: assert t in js,t
assert 'loadEnergy' in prev and 'energy-systems-v42800.js' in prev
assert '.es42800-panel' in css
print('PASS: v4.28.0 energy systems direct + iframe-compatible browser asset gate')
