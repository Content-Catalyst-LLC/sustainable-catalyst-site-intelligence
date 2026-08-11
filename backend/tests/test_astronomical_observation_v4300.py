from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.astronomical_observation_v4300 import catalog, state, readiness
CLIENT=TestClient(app); ROOT=Path(__file__).resolve().parents[2]

def test_overview_preserves_v4_route_architecture():
    p=CLIENT.get('/public/astronomical-observation').json()
    assert p['ok'] and p['version']=='4.35.1' and p['route']=='earth'
    assert p['target_count']>=6 and p['survey_count']>=7 and len(p['contract_sha256'])==64
    nav=CLIENT.get('/public/v4/navigation').json(); assert nav['route_count']==35 and nav['primary_area_count']==6

def test_catalog_is_multiwavelength_and_archive_grounded():
    p=catalog(); assert p['survey_count']>=7 and p['target_count']>=6
    wavelengths={x['wavelength'] for x in p['surveys']}
    assert {'optical','near infrared','mid infrared','ultraviolet','radio','soft X-ray'}.issubset(wavelengths)
    assert any('IRSA' in x['archive'] for x in p['surveys']) and any('SkyView' in x['archive'] for x in p['surveys'])
    assert all(x['live_telescope'] is False and x['embedded_verified_pixels'] is False for x in p['surveys'])

def test_irsa_state_builds_reproducible_source_handoff_without_claiming_pixels():
    p=state('m31','2mass-near-ir',field_deg=.25)
    assert p['target']['frame']=='equatorial J2000'
    assert 'irsa.ipac.caltech.edu' in p['observation']['official_observation_handoff']['url']
    assert p['truth']['local_orientation_is_survey_imagery'] is False
    assert p['truth']['live_telescope_feed_claimed'] is False
    assert p['observation']['observation_epoch'] is None
    assert len(p['state_sha256'])==64

def test_skyview_state_preserves_query_plan_and_color_semantics():
    p=state('crab','rosat-soft-xray',field_deg=.5)
    h=p['observation']['official_observation_handoff']
    assert 'skyview.gsfc.nasa.gov' in h['url'] and h['query_plan']['coordinates']=='J2000'
    assert 'X-ray' in p['observation']['wavelength'] and 'representational' in p['observation']['color_semantics']
    assert p['truth']['natural_color_claimed'] is False

def test_irsa_field_is_clamped_to_documented_finderchart_limit():
    p=state('m42','wise-mid-ir',field_deg=3)
    h=p['observation']['official_observation_handoff']
    assert h['query_field_deg']==1.0 and h['requested_field_was_clamped'] is True

def test_unknown_target_fails_explicitly_and_custom_coordinates_are_bounded():
    p=CLIENT.get('/public/astronomical-observation/target/not-real').json()
    assert p['ok'] is False and 'm31' in p['supported_targets']
    s=state('custom','dss-optical',ra_deg=361,dec_deg=95)
    assert s['target']['ra_deg']==1.0 and s['target']['dec_deg']==90.0

def test_export_and_readiness():
    p=CLIENT.get('/public/astronomical-observation/export-manifest',params={'target':'m51','survey':'wise-mid-ir'}).json()
    assert p['schema']=='sc-site-intelligence-astronomical-view/1.0'
    assert p['review']['survey_pixels_fabricated'] is False and p['review']['live_telescope_claimed'] is False
    assert len(p['manifest_sha256'])==64
    r=readiness(); assert r['ok'] and r['summary']['targets']>=6 and r['summary']['surveys']>=7

def test_assets_ship_in_app_service_worker_and_wordpress():
    html=(ROOT/'backend/public_app/index.html').read_text(); sw=(ROOT/'backend/public_app/service-worker.js').read_text()
    js=(ROOT/'backend/public_app/assets/astronomical-observation-v4300.js').read_text(); css=(ROOT/'backend/public_app/assets/astronomical-observation-v4300.css').read_text()
    assert 'data-scsi-astronomical-contract="astronomical-observation-v4300"' in html and 'id="earthAstronomyEnter"' in html
    assert 'astronomical-observation-v4300.js' in sw and 'astronomical-observation-v4300.css' in sw
    assert 'SCSIAstronomicalV4300' in js and '.astro4300-stage' in css
    assert js==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/astronomical-observation-v4300.js').read_text()
    assert css==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/astronomical-observation-v4300.css').read_text()
