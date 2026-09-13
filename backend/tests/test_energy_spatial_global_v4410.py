from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.energy_spatial_global_v4410 import profile, compare, validate_result

client = TestClient(app)


def sample(name="Testland", lon=0.0):
    return {
        "geography": {"name": name, "iso3": "TST", "focus_point": {"latitude": 0.0, "longitude": lon}},
        "records": [
            {"record_id":"g1","source_ref":"ember:test","indicator":"electricity-generation","value":100,"unit":"GWh","year":2025,"feature_class":"generation","technology":"solar","point":{"latitude":0.0,"longitude":lon+1.0}},
            {"record_id":"s1","source_ref":"osm:test","indicator":"substation","feature_class":"substation","point":{"latitude":0.0,"longitude":lon+0.5}},
            {"record_id":"d1","source_ref":"eia:test","indicator":"electric-demand","value":80,"unit":"GWh","year":2024,"feature_class":"demand-center","point":{"latitude":1.0,"longitude":lon}},
        ],
        "provenance": [{"source_ref":"ember:test"},{"source_ref":"osm:test"},{"source_ref":"eia:test"}],
    }


def test_framework_and_registry_routes():
    f=client.get('/v1/energy-spatial/framework').json()
    assert f['ok'] is True
    assert f['version']=='1.5.0'
    assert f['site_intelligence_version']=='4.41.0'
    assert f['capabilities']['site_suitability_scoring'] is False
    reg=client.get('/v1/energy-spatial/source-registry').json()
    assert {x['key'] for x in reg['sources']} >= {'openstreetmap-power','eia-open-data','ember-electricity-data','entsoe-transparency'}


def test_profile_is_deterministic_and_spatial():
    a=profile(sample())
    b=profile(sample())
    assert a['profile_id']==b['profile_id']
    assert a['summary']['record_count']==3
    assert a['summary']['source_count']==3
    assert a['summary']['year_range']=={'earliest':2024,'latest':2025}
    assert a['nearest_to_focus']['substation']['record_id']=='s1'
    assert 55 < a['nearest_to_focus']['substation']['distance_km'] < 56
    assert a['truth']['site_suitability_determined'] is False
    assert a['truth']['technology_ranked'] is False


def test_profile_does_not_mix_units():
    body=sample()
    body['records'].append({"record_id":"g2","source_ref":"ember:test","indicator":"electricity-generation","value":1,"unit":"TWh","year":2025,"feature_class":"generation"})
    p=profile(body)
    groups={(x['indicator'],x['unit']):x for x in p['observation_summaries']}
    assert groups[('electricity-generation','GWh')]['mean']==100
    assert groups[('electricity-generation','TWh')]['mean']==1


def test_compare_is_neutral_and_validates():
    a=profile(sample('A',0))
    b=profile(sample('B',10))
    c=compare({'profiles':[a,b]})
    assert c['profile_count']==2
    assert c['ranking']['performed'] is False
    assert c['recommendation']['performed'] is False
    assert validate_result(c)['valid'] is True
    assert validate_result(a)['valid'] is True


def test_invalid_point_is_rejected():
    body=sample(); body['geography']['focus_point']['latitude']=91
    with pytest.raises(Exception): profile(body)
