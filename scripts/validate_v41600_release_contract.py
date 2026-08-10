#!/usr/bin/env python3
from app.cryosphere_v41600 import catalog,overview,readiness,state
x=overview(); assert x['version']=='4.16.0' and x['contract']=='global-cryosphere-intelligence-frozen-earth-conditions' and x['route']=='earth' and x['source_count']==4
c=catalog(); ids={s['id'] for s in c['sources']}; assert {'noaa-nsidc-sea-ice-index','nasa-nsidc-daac','glims','modis-snow-sea-ice'}<=ids
s=state('noaa-nsidc-sea-ice-index','sea-ice-extent',80,-30,'2026-08-09'); assert s['source_supports_indicator_type'] and s['truth']['near_real_time_treated_as_final'] is False and s['truth']['local_safety_determination'] is False
r=readiness(); assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
print('PASS: v4.16.0 global cryosphere release contract')
