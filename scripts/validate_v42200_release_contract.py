#!/usr/bin/env python3
from app.climate_intelligence_v42200 import catalog,overview,readiness,state
x=overview(); assert x['version']=='4.22.0' and x['contract']=='global-climate-baselines-anomalies-extremes-intelligence' and x['route']=='earth' and x['source_count']==4
c=catalog(); ids={s['id'] for s in c['sources']}; assert {'noaa-ncei-cdo','copernicus-era5','nasa-gistemp-v4','wmo-climate-extremes'}<=ids
assert c['truth_boundaries']['climate_normal_equals_forecast'] is False and c['truth_boundaries']['anomaly_equals_attribution'] is False
s=state('nasa-gistemp-v4','global-temperature-anomaly',None,None,'2026-07-01'); assert s['source_supports_indicator_type'] and s['truth']['gistemp_anomaly_treated_as_local_absolute_temperature'] is False and s['truth']['zero_records_treated_as_no_climate_risk'] is False
r=readiness(); assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
print('PASS: v4.22.0 climate baselines / anomalies / extremes release contract')
