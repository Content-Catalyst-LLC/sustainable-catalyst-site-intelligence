#!/usr/bin/env python3
from app.coastal_change_v41400 import catalog, readiness, scenario_preview, state

c = catalog()
assert c['version'] == '4.15.0'
assert {x['id'] for x in c['sources']} == {'noaa-coops','noaa-digital-coast','usgs-coastal-change','global-mangrove-watch'}
s = state('noaa-digital-coast','sea-level-scenario',29.0,-90.0,'2026-08-09')
assert s['truth']['scenario_treated_as_exact_flood_forecast'] is False
assert s['truth']['platform_property_loss_finding'] is False
assert s['truth']['habitat_treated_as_carbon_credit'] is False
p = scenario_preview({'scenario_height':3,'unit':'ft','bbox':[-90,29,-89,30]})
assert p['preview']['screening_scenario'] is True
assert p['preview']['exact_flood_boundary'] is False
assert p['preview']['parcel_level_forecast'] is False
r = readiness()
assert r['ok'] and all(r['checks'].values())
assert r['summary']['public_route_count_delta'] == 0
print('PASS: v4.15.0 coastal change / sea level / blue-carbon release contract')
