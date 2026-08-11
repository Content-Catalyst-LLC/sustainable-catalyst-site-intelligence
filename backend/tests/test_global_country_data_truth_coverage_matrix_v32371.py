from pathlib import Path
import json
from fastapi.testclient import TestClient
from app.config import Settings
from app.data_truth_v32371 import GlobalCountryDataTruth, COVERAGE_STATES
from app.main import app

ROOT=Path(__file__).resolve().parents[2]
CLIENT=TestClient(app)

def test_global_country_catalog_is_bundled_and_broad():
    payload=CLIENT.get('/public/data-truth/countries').json()
    assert payload['ok'] is True and payload['version']=='4.35.4'
    assert payload['country_count']>=170
    codes={row['code'] for row in payload['countries']}
    assert {'KEN','GHA','USA','IND','BRA','DEU'}.issubset(codes)

def test_country_truth_separates_eligibility_from_observation():
    payload=CLIENT.get('/public/data-truth/country/BRA').json()
    assert payload['contract']=='global-country-data-truth'
    assert payload['country']['name']=='Brazil'
    assert payload['source_count']==8
    by_id={row['feed_id']:row for row in payload['sources']}
    assert by_id['world_bank']['eligibility']=='eligible'
    assert by_id['world_bank']['coverage_state']=='unknown'
    assert by_id['noaa_nws']['coverage_state']=='not_applicable'
    assert by_id['platform_status']['coverage_state']=='not_applicable'
    assert by_id['openalex']['coverage_state']=='partial'

def test_kenya_and_ghana_packaged_indicator_snapshots_are_historical_only():
    for code in ('KEN','GHA'):
        payload=CLIENT.get(f'/public/data-truth/country/{code}/indicators').json()
        assert payload['indicator_count']==8
        assert all(row['coverage_state']=='historical_only' for row in payload['indicators'])
        assert all(row['evidence_level']=='packaged_snapshot' for row in payload['indicators'])

def test_non_fallback_country_indicator_truth_does_not_fabricate_records():
    payload=CLIENT.get('/public/data-truth/country/IND/indicators').json()
    assert all(row['coverage_state']=='unknown' for row in payload['indicators'])
    assert all(row['value'] is None and row['observation_year'] is None for row in payload['indicators'])

def test_query_country_alias_and_invalid_country_fail_closed():
    assert CLIENT.get('/public/data-truth?country=DEU').json()['country']['code']=='DEU'
    assert CLIENT.get('/public/data-truth/country/ZZZ').status_code==404
    assert CLIENT.get('/public/data-truth?country=ZZZ').status_code==404

def test_coverage_matrix_has_representative_countries_and_all_sources():
    payload=CLIENT.get('/public/data-truth/coverage-matrix?countries=KEN,GHA,USA,IND,BRA,DEU').json()
    assert payload['contract']=='global-country-source-coverage-matrix'
    assert payload['country_count']==6 and payload['source_count']==8
    assert len(payload['columns'])==8
    assert all(len(row['cells'])==8 for row in payload['rows'])
    assert set(payload['summary']).issuperset(COVERAGE_STATES)

def test_registry_declares_geographic_policy_for_every_source():
    registry=json.loads((ROOT/'backend/data/live_intelligence_source_registry_v320.json').read_text())
    for source in registry['sources']:
        policy=source['geographic_policy']
        assert policy['scope'] and policy['country_resolution'] and policy['observation_mode'] and policy['domain']
        assert policy['default_country_state'] in COVERAGE_STATES
        assert policy['boundary']

def test_global_truth_assets_and_service_worker_contract_are_shipped():
    html=(ROOT/'backend/public_app/index.html').read_text()
    worker=(ROOT/'backend/public_app/service-worker.js').read_text()
    js=(ROOT/'backend/public_app/assets/data-truth-v32371.js').read_text()
    assert 'data-truth-v32371.css?v=4.35.4' in html and 'data-truth-v32371.js?v=4.35.4' in html
    assert 'data-truth-v32371.js' in worker and 'data-truth-v32371.css' in worker
    for token in ('SCSIDataTruthV32371','Coverage matrix','eligibility','scsi:data-truth-country-ready'):
        assert token in js

def test_runtime_country_counts_can_upgrade_event_coverage(tmp_path):
    from app.live_intelligence_source_operations_v320 import LiveIntelligenceSourceOperations
    settings=Settings(
        live_source_operations_registry_path=str(ROOT/'backend/data/live_intelligence_source_registry_v320.json'),
        live_source_operations_state_path=str(tmp_path/'state.json'),
        live_source_operations_history_path=str(tmp_path/'history.jsonl'),
    )
    operations=LiveIntelligenceSourceOperations(settings)
    operations.record_result('usgs_earthquakes',ok=True,data_state='live',record_count=4,country_record_counts={'BRA':3,'KEN':0})
    center=GlobalCountryDataTruth(settings,source_center=__import__('app.data_truth_v3233',fromlist=['DataTruthCenter']).DataTruthCenter(settings,operations=operations))
    brazil={row['feed_id']:row for row in center.country_sources('BRA')['sources']}
    kenya={row['feed_id']:row for row in center.country_sources('KEN')['sources']}
    assert brazil['usgs_earthquakes']['coverage_state']=='available'
    assert brazil['usgs_earthquakes']['country_record_count']==3
    assert kenya['usgs_earthquakes']['coverage_state']=='no_recent_records'
