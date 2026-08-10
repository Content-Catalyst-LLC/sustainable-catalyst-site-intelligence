#!/usr/bin/env python3
from app.atmosphere_v41700 import catalog,overview,readiness,state
x=overview(); assert x['version']=='4.17.0' and x['contract']=='global-atmosphere-air-quality-aerosol-intelligence' and x['route']=='earth' and x['source_count']==4
c=catalog(); ids={s['id'] for s in c['sources']}; assert {'airnow','epa-aqs','cams-global','nasa-earthdata-aerosol'}<=ids
s=state('airnow','aqi',41.88,-87.63,'2026-08-09'); assert s['source_supports_indicator_type'] and s['truth']['preliminary_treated_as_regulatory'] is False and s['truth']['health_advisory_issued_by_platform'] is False
r=readiness(); assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
print('PASS: v4.17.0 global atmosphere / air-quality release contract')
