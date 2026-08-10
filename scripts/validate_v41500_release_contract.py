#!/usr/bin/env python3
from app.ocean_governance_v41500 import catalog,overlap_preview,readiness,state
c=catalog(); assert c['version']=='4.16.0'; assert {x['id'] for x in c['sources']}=={'noaa-maritime-boundaries','marine-regions-vliz','fao-major-fishing-areas','fao-regional-fishery-bodies'}
s=state('marine-regions-vliz','exclusive-economic-zone',51.4,2.8,'2026-08-09'); assert not s['truth']['platform_legal_boundary_determination']; assert not s['truth']['platform_sovereignty_determination']; assert not s['truth']['dispute_resolved_by_platform']
p=overlap_preview({'area_a_bbox':[0,0,5,5],'area_b_bbox':[4,4,8,8]}); assert p['preview']['spatial_intersection']; assert not p['preview']['legal_overlap_determination']; assert not p['preview']['jurisdiction_conflict_determined']
r=readiness(); assert r['ok'] and all(r['checks'].values()); assert r['summary']['public_route_count_delta']==0
print('PASS: v4.16.0 ocean governance / jurisdiction / maritime boundaries release contract')
