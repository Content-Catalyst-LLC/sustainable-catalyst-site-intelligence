#!/usr/bin/env python3
from app.geosphere_v42000 import catalog,overview,readiness,state
x=overview(); assert x['version']=='4.20.0' and x['contract']=='global-geosphere-earthquake-volcano-intelligence' and x['route']=='earth' and x['source_count']==4
c=catalog(); ids={s['id'] for s in c['sources']}; assert {'usgs-earthquake-catalog','usgs-shakemap','usgs-volcano-hans','nasa-jpl-aria'}<=ids
s=state('usgs-earthquake-catalog','earthquake-event',41.88,-87.63,'2026-08-09'); assert s['source_supports_indicator_type'] and s['truth']['catalog_event_treated_as_emergency_warning'] is False and s['truth']['zero_records_treated_as_no_hazard'] is False
r=readiness(); assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
print('PASS: v4.20.0 geosphere / earthquake / volcano release contract')
