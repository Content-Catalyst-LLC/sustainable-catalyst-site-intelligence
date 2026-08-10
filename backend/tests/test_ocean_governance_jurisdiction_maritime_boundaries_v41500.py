from fastapi.testclient import TestClient
from app.main import app
from app.ocean_governance_v41500 import catalog,export_manifest,normalize_management_area,normalize_zone,overlap_preview,readiness,state
CLIENT=TestClient(app)
def test_catalog():
 c=catalog(); assert {x['id'] for x in c['sources']}=={'noaa-maritime-boundaries','marine-regions-vliz','fao-major-fishing-areas','fao-regional-fishery-bodies'}; assert c['truth_boundaries']['geometry_is_legal_determination'] is False
def test_state_truth():
 s=state('marine-regions-vliz','exclusive-economic-zone',51.4,2.8,'2026-08-09'); assert s['source_supports_zone_type']; assert not s['truth']['platform_legal_boundary_determination']; assert not s['truth']['platform_sovereignty_determination']; assert not s['truth']['dispute_resolved_by_platform']
def test_zone_normalization():
 z=normalize_zone({'source_id':'marine-regions-vliz','source_url':'https://geo.vliz.be/geoserver/MarineRegions/wfs','zone_type':'exclusive-economic-zone','evidence_class':'maritime-zone-feature','bbox':[2.2,51,3.4,51.9],'source_version':'12','source_reports_dispute':True})['zone']; assert z['source_reports_dispute']; assert not z['platform_legal_determination']; assert not z['sovereignty_inferred']
def test_bad_host():
 r=CLIENT.post('/public/ocean-governance/zone/normalize',json={'source_id':'noaa-maritime-boundaries','source_url':'https://example.com/','zone_type':'territorial-sea','evidence_class':'maritime-zone-feature','bbox':[-75,35,-74,36]}); assert r.status_code==400
def test_fao_statistical_not_jurisdiction():
 a=normalize_management_area({'source_id':'fao-major-fishing-areas','source_url':'https://www.fao.org/fishery/en/area/search','zone_type':'fao-major-fishing-area','evidence_class':'statistical-area','area_code':'21','bbox':[-80,35,-40,78]})['management_area']; assert a['statistical_purpose']; assert not a['jurisdiction_inferred']; assert not a['fishing_authorization_inferred']
def test_rfb_not_sovereignty():
 a=normalize_management_area({'source_id':'fao-regional-fishery-bodies','source_url':'https://www.fao.org/fishery/geoserver/factsheets/rfbs.html','zone_type':'regional-fishery-body-area','evidence_class':'regional-fishery-body-area','bbox':[-60,-20,20,40]})['management_area']; assert not a['sovereignty_inferred']; assert not a['enforcement_finding']
def test_overlap_spatial_only():
 p=overlap_preview({'area_a_bbox':[0,0,5,5],'area_b_bbox':[4,4,8,8]})['preview']; assert p['spatial_intersection']; assert not p['legal_overlap_determination']; assert not p['jurisdiction_conflict_determined']
def test_manifest_readiness_architecture():
 p=export_manifest(); assert p['schema']=='sc-site-intelligence-ocean-governance/1.0'; assert not p['review']['geometry_as_legal_determination']; r=readiness(); assert r['ok'] and all(r['checks'].values()); assert r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
