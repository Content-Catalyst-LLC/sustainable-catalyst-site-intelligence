#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
js=(ROOT/'backend/public_app/assets/exoplanet-habitability-v43500.js').read_text();css=(ROOT/'backend/public_app/assets/exoplanet-habitability-v43500.css').read_text();astro=(ROOT/'backend/public_app/assets/astronomical-observation-v4300.js').read_text()
for t in ['SCSIExoplanetHabitabilityV43500','EXOPLANET &amp; ATMOSPHERIC EVIDENCE','/public/exoplanet-habitability/catalog','exoplanetHabitabilityPanel','Open NASA Exoplanet Archive']:
 assert t in js,t
assert 'astroExoplanets' in astro and 'SCSIExoplanetHabitabilityV43500' in astro
assert 'exoplanet-habitability-v43500.js?v=4.35.0' in astro and 'exoplanet-habitability-v43500.css?v=4.35.0' in astro
assert '.exo43500-panel' in css and '.exo43500-spectrum' in css
print('PASS: v4.35.0 exoplanet/habitability direct + iframe-compatible browser asset gate')
