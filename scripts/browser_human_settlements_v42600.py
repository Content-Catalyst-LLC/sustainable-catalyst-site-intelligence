#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];js=(ROOT/'backend/public_app/assets/human-settlements-v42600.js').read_text();css=(ROOT/'backend/public_app/assets/human-settlements-v42600.css').read_text();prev=(ROOT/'backend/public_app/assets/agriculture-food-v42500.js').read_text()
for t in ['SCSIHumanSettlementsV42600','HUMAN SETTLEMENT EVIDENCE','/public/human-settlements/catalog','humanSettlementsPanel']: assert t in js,t
assert 'loadHumanSettlements' in prev and 'human-settlements-v42600.js' in prev
assert '.hs42600-panel' in css
print('PASS: v4.26.0 human settlements direct + iframe-compatible browser asset gate')
