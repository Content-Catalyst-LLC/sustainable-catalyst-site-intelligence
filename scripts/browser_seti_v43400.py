#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
js=(ROOT/'backend/public_app/assets/seti-technosignatures-v43400.js').read_text()
css=(ROOT/'backend/public_app/assets/seti-technosignatures-v43400.css').read_text()
astro=(ROOT/'backend/public_app/assets/astronomical-observation-v4300.js').read_text()
html=(ROOT/'backend/public_app/index.html').read_text()
for t in ['SCSISETIV43400','TECHNOSIGNATURE SEARCH EVIDENCE','/public/seti-technosignatures/catalog','setiPanel','Open public SETI archive']:
    assert t in js,t
assert 'astroSeti' in astro and 'SCSISETIV43400' in astro
assert 'seti-technosignatures-v43400' in astro
assert 'seti-technosignatures-v43400.js?v=4.35.1' in astro and 'seti-technosignatures-v43400.css?v=4.35.1' in astro
assert '.seti-panel' in css and '.seti43400-spectrum' in css
print('PASS: v4.35.1 SETI / technosignatures direct + iframe-compatible browser asset gate')
