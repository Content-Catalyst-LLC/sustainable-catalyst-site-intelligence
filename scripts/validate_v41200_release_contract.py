#!/usr/bin/env python3
from app.marine_human_activity_v41200 import catalog, overlap_preview, readiness, state

c=catalog()
assert c['version']=='4.13.0'
assert {x['id'] for x in c['sources']} == {
    'noaa-marine-cadastre-ais','noaa-mpa-inventory','emodnet-human-activities','global-fishing-watch'
}
s=state('global-fishing-watch','fishing-activity',41.1,-69.2,'2026-08-09')
assert s['truth']['zero_ais_treated_as_no_vessel'] is False
assert s['truth']['fishing_activity_treated_as_illegal'] is False
assert s['truth']['spatial_overlap_treated_as_violation'] is False
p=overlap_preview({'activity_latitude':40.5,'activity_longitude':-69.5,'zone_bbox':[-70,40,-69,41]})
assert p['preview']['spatial_overlap'] is True
assert p['preview']['legal_violation'] is False
assert p['preview']['enforcement_finding'] is False
r=readiness(); assert r['ok'] and all(r['checks'].values())
assert r['summary']['public_route_count_delta']==0
print('PASS: v4.13.0 marine human-activity release contract')
