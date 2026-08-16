from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_exoplanet_overview_catalog_and_sources():
    o=client.get('/public/exoplanet-habitability').json(); c=client.get('/public/exoplanet-habitability/catalog').json()
    assert o['ok'] and o['version']=='4.38.0' and o['route']=='earth' and o['source_count']==4
    ids={x['id'] for x in c['sources']}
    assert {'nasa-exoplanet-archive-systems','nasa-exoplanet-archive-atmospheres','exo-mast','mast-jwst-spectraldb'} <= ids
    assert c['truth_boundaries']['habitable_zone_equals_habitable'] is False
    assert c['truth_boundaries']['biosignature_candidate_equals_life_detection'] is False


def test_empty_state_is_not_habitability_or_life_finding():
    d=client.get('/public/exoplanet-habitability/state?target=TRAPPIST-1%20e').json()
    assert d['ok'] and d['target']=='TRAPPIST-1 e'
    assert d['evidence']['life_confirmed'] is False
    assert d['truth']['habitable_zone_treated_as_habitability'] is False
    assert d['truth']['biosignature_treated_as_life_detection'] is False


def test_planet_hz_and_teq_do_not_confirm_habitability():
    p={'source_id':'nasa-exoplanet-archive-systems','source_url':'https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html','planet_name':'TRAPPIST-1 e','host_name':'TRAPPIST-1','equilibrium_temperature_k':251,'insolation_earth':0.66,'habitable_zone_flag_from_source':True}
    d=client.post('/public/exoplanet-habitability/planet/normalize',json=p).json()['planet']
    assert d['habitability_confirmed'] is False and d['surface_temperature_inferred'] is False and d['life_inferred'] is False


def test_archive_spectrum_does_not_confirm_molecule_or_life():
    p={'source_id':'nasa-exoplanet-archive-atmospheres','source_url':'https://exoplanetarchive.ipac.caltech.edu/docs/atmospheres/atmospheres_home.html','planet_name':'WASP-96 b','spectrum_type':'Transmission','facility':'JWST','instrument':'NIRISS','wavelength_min_um':0.6,'wavelength_max_um':2.8}
    d=client.post('/public/exoplanet-habitability/spectrum/normalize',json=p).json()['spectrum']
    assert d['molecule_confirmed_by_platform'] is False and d['biosignature_confirmed'] is False and d['life_confirmed'] is False


def test_jwst_pixel_product_is_observation_not_biosignature():
    p={'source_id':'mast-jwst-spectraldb','source_url':'https://mast.stsci.edu/spectra/docs/retrieve_pixels.html','evidence_class':'spectral-measurement-record','planet_name':'example b','facility':'JWST','data_product':'x1d'}
    d=client.post('/public/exoplanet-habitability/spectrum/normalize',json=p).json()['spectrum']
    assert d['biosignature_confirmed'] is False and d['abiotic_false_positive_excluded_by_platform'] is False


def test_biosignature_assessment_preserves_false_positive_boundary():
    p={'source_id':'nasa-exoplanet-archive-atmospheres','source_url':'https://exoplanetarchive.ipac.caltech.edu/docs/atmospheres/atmospheres_home.html','evidence_class':'biosignature-assessment-record','planet_name':'example b','species_or_feature':'O2','source_claim':'candidate atmospheric feature','abiotic_alternatives_considered_by_source':True}
    d=client.post('/public/exoplanet-habitability/biosignature/normalize',json=p).json()['assessment']
    assert d['biosignature_confirmed_by_platform'] is False and d['life_detected_by_platform'] is False
    assert d['abiotic_false_positive_excluded_by_platform'] is False and d['announcement_authorized'] is False


def test_exomast_context_is_not_life_evidence():
    d=client.get('/public/exoplanet-habitability/state?source=exo-mast&indicator_type=curated-spectrum&target=HAT-P-11%20b').json()
    assert d['source_supports_indicator_type'] is True
    assert d['truth']['molecule_treated_as_biosignature_confirmation'] is False


def test_manifest_and_readiness_preserve_life_boundary():
    m=client.get('/public/exoplanet-habitability/export-manifest?target=TRAPPIST-1%20e').json(); r=client.get('/public/exoplanet-habitability/readiness').json()
    assert m['schema']=='sc-site-intelligence-exoplanets-habitability-biosignatures/1.0'
    assert m['review']['habitable_zone_as_habitability'] is False and m['review']['biosignature_as_life_detection'] is False
    assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0
