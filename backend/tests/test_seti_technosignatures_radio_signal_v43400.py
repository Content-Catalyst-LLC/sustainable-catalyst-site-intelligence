from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_seti_overview_catalog_and_sources():
    o = client.get('/public/seti-technosignatures').json()
    c = client.get('/public/seti-technosignatures/catalog').json()
    assert o['ok'] and o['version'] == '4.35.4' and o['route'] == 'earth' and o['source_count'] == 4
    ids = {x['id'] for x in c['sources']}
    assert {'breakthrough-listen-open-data','breakthrough-listen-event-tables','seti-technosearch','nasa-exoplanet-target-context'} <= ids
    assert c['truth_boundaries']['signal_event_equals_technosignature'] is False
    assert c['truth_boundaries']['candidate_equals_confirmed_eti'] is False


def test_empty_state_is_not_detection_or_absence_finding():
    d = client.get('/public/seti-technosignatures/state?target=Proxima%20Centauri&telescope=Parkes&frequency_mhz=982').json()
    assert d['ok'] and d['target'] == 'Proxima Centauri'
    assert d['evidence']['signal_event_loaded'] is False and d['evidence']['technosignature_confirmed'] is False
    assert d['truth']['non_detection_treated_as_absence'] is False
    assert d['truth']['signal_event_treated_as_technosignature'] is False


def test_breakthrough_observation_does_not_infer_technosignature():
    payload = {'source_id':'breakthrough-listen-open-data','source_url':'https://seti.berkeley.edu/opendata','indicator_type':'observation-metadata','evidence_class':'observation-record','target':'Proxima Centauri','telescope':'Parkes','center_frequency_mhz':982.002,'file_type':'HDF5','file_id':'example.h5','ra_deg':217.4292,'dec_deg':-62.6795}
    d = client.post('/public/seti-technosignatures/observation/normalize', json=payload).json()['observation']
    assert d['technosignature_inferred'] is False and d['eti_origin_inferred'] is False and d['live_telescope_status_inferred'] is False


def test_signal_event_with_drift_and_snr_is_not_confirmation():
    payload = {'source_id':'breakthrough-listen-event-tables','source_url':'https://seti.berkeley.edu/listen2019/opendata.html','indicator_type':'signal-event','evidence_class':'signal-event-record','target':'HIP 12345','frequency_mhz':1420.405,'drift_rate_hz_per_s':-0.42,'snr':18.3,'bandwidth_hz':3.0,'file_id':'event-file'}
    d = client.post('/public/seti-technosignatures/signal/normalize', json=payload).json()['signal']
    assert d['technosignature_confirmed'] is False and d['eti_origin_confirmed'] is False
    assert d['rfi_excluded_by_platform'] is False and d['independent_confirmation_present'] is False


def test_candidate_followup_non_redetection_remains_unconfirmed():
    payload = {'source_id':'breakthrough-listen-event-tables','source_url':'https://seti.berkeley.edu/ml_gbt/','candidate_id':'candidate-1','target':'example target','source_status':'signal-of-interest','follow_up_result':'not-redetected'}
    d = client.post('/public/seti-technosignatures/candidate/normalize', json=payload).json()['candidate']
    assert d['re_detected'] is False and d['technosignature_confirmed'] is False and d['eti_origin_confirmed'] is False
    assert d['announcement_authorized'] is False and d['independent_verification_inferred'] is False


def test_technosearch_record_is_search_coverage_not_absence():
    d = client.get('/public/seti-technosignatures/state?source=seti-technosearch&indicator_type=search-coverage&target=TRAPPIST-1').json()
    assert d['source_supports_indicator_type'] is True
    assert d['truth']['non_detection_treated_as_absence'] is False


def test_nasa_target_context_is_not_technosignature_evidence():
    d = client.get('/public/seti-technosignatures/state?source=nasa-exoplanet-target-context&indicator_type=planetary-system-context&target=TRAPPIST-1').json()
    assert d['source_supports_indicator_type'] is True
    c = client.get('/public/seti-technosignatures/catalog').json()
    assert c['truth_boundaries']['target_context_equals_technosignature_evidence'] is False


def test_seti_manifest_and_readiness_preserve_announcement_boundary():
    m = client.get('/public/seti-technosignatures/export-manifest?target=Proxima%20Centauri').json()
    r = client.get('/public/seti-technosignatures/readiness').json()
    assert m['schema'] == 'sc-site-intelligence-seti-technosignatures/1.0'
    assert m['review']['candidate_as_confirmed_eti'] is False and m['review']['single_observation_as_announcement_authority'] is False
    assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta'] == 0
