#!/usr/bin/env python3
from app.marine_pollution_v41300 import catalog, readiness, state, threshold_preview

c = catalog()
assert c['version'] == '4.13.0'
assert {x['id'] for x in c['sources']} == {
    'noaa-ncei-marine-microplastics','emodnet-chemistry','copernicus-marine-biogeochemistry','water-quality-portal'
}
s = state('emodnet-chemistry','heavy-metals',54.0,5.0,'2026-08-09')
assert s['truth']['zero_records_treated_as_clean_water'] is False
assert s['truth']['non_detect_treated_as_zero'] is False
assert s['truth']['platform_health_risk_finding'] is False
assert s['truth']['platform_compliance_finding'] is False
p = threshold_preview({'measurement_value':12,'threshold_value':10,'measurement_unit':'ug/L','threshold_unit':'ug/L'})
assert p['preview']['orientation_condition_met'] is True
assert p['preview']['regulatory_exceedance'] is False
assert p['preview']['health_advisory'] is False
r = readiness()
assert r['ok'] and all(r['checks'].values())
assert r['summary']['public_route_count_delta'] == 0
print('PASS: v4.13.0 marine pollution / debris / water-quality release contract')
