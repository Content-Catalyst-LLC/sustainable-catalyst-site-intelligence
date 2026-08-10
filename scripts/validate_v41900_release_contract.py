#!/usr/bin/env python3
from app.terrestrial_ecosystems_v41900 import catalog,overview,readiness,state
x=overview(); assert x['version']=='4.19.0' and x['contract']=='terrestrial-ecosystems-vegetation-wildfire-intelligence' and x['route']=='earth' and x['source_count']==4
c=catalog(); ids={s['id'] for s in c['sources']}; assert {'nasa-firms','nasa-modis-vegetation','copernicus-lcfm','copernicus-global-vegetation'}<=ids
s=state('nasa-firms','active-fire-detection',41.88,-87.63,'2026-08-09'); assert s['source_supports_indicator_type'] and s['truth']['active_fire_treated_as_burned_area'] is False and s['truth']['platform_wildfire_warning_issued'] is False
r=readiness(); assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
print('PASS: v4.19.0 terrestrial ecosystems / vegetation / wildfire release contract')
