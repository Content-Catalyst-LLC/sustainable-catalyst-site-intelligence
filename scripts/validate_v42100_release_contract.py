#!/usr/bin/env python3
from app.soils_land_degradation_v42100 import catalog,overview,readiness,state
x=overview(); assert x['version']=='4.21.0' and x['contract']=='global-soils-land-degradation-desertification-intelligence' and x['route']=='earth' and x['source_count']==4
c=catalog(); ids={s['id'] for s in c['sources']}; assert {'isric-soilgrids','usda-nrcs-soil-data-access','nasa-smap-soil-moisture','unccd-land-degradation'}<=ids
assert c['truth_boundaries']['soilgrids_equals_ground_sample'] is False and c['truth_boundaries']['soil_carbon_equals_carbon_credit'] is False
s=state('isric-soilgrids','soil-organic-carbon',41.88,-87.63,'2026-08-09'); assert s['source_supports_indicator_type'] and s['truth']['soilgrids_treated_as_ground_sample'] is False and s['truth']['zero_records_treated_as_healthy_soil'] is False
r=readiness(); assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
print('PASS: v4.21.0 soils / land degradation / desertification release contract')
