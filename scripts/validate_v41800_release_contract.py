#!/usr/bin/env python3
from app.hydrology_v41800 import catalog,overview,readiness,state
x=overview(); assert x['version']=='4.18.0' and x['contract']=='global-hydrology-rivers-flood-drought-intelligence' and x['route']=='earth' and x['source_count']==4
c=catalog(); ids={s['id'] for s in c['sources']}; assert {'usgs-water-data','nasa-gpm-imerg','copernicus-glofas','drought-gov'}<=ids
s=state('usgs-water-data','streamflow',41.88,-87.63,'2026-08-09'); assert s['source_supports_indicator_type'] and s['truth']['model_discharge_treated_as_gauge_observation'] is False and s['truth']['official_flood_warning_issued_by_platform'] is False
r=readiness(); assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
print('PASS: v4.18.0 global hydrology / rivers / flood / drought release contract')
