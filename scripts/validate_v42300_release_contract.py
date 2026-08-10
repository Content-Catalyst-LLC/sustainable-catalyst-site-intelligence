#!/usr/bin/env python3
from app.biodiversity_intelligence_v42300 import catalog,overview,readiness,state
x=overview(); assert x['version']=='4.24.0' and x['contract']=='global-biodiversity-species-distribution-conservation-intelligence' and x['route']=='earth' and x['source_count']==4
c=catalog(); ids={s['id'] for s in c['sources']}; assert {'gbif-occurrence','obis','ebird-public','usfws-ecos'}<=ids
assert c['truth_boundaries']['zero_records_equals_absence'] is False and c['truth_boundaries']['critical_habitat_overlap_equals_project_effect'] is False
s=state('gbif-occurrence','species-occurrence','Danaus plexippus',None,None,'2026-07-01'); assert s['source_supports_indicator_type'] and s['truth']['zero_records_treated_as_absence'] is False and s['truth']['occurrence_treated_as_population'] is False
r=readiness(); assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
print('PASS: v4.24.0 biodiversity / species distribution / conservation release contract')
