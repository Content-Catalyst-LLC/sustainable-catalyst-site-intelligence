from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.credential_configuration_v43516 import (
    PROFILES,
    credential_registry,
    credential_readiness,
    credential_workspaces,
    canonical_configuration_for_source,
)
from app.authoritative_api_audit_v43516 import source_inventory
from app.authoritative_api_production_audit_v43516 import production_audit
from app.release_health_v43516 import deployment_verification, source_health_policy

ROOT=Path(__file__).resolve().parents[2]


def configured_settings():
    return Settings(
        reliefweb_appname='sustainable-catalyst-prod-a1b2',
        airnow_api_key='airnow-abcdefgh',
        epa_aqs_email='data@sustainablecatalyst.com', epa_aqs_key='aqs-abcdefgh',
        eia_api_key='eia-abcdefgh', ember_api_key='ember-abcdefgh',
        entsoe_security_token='entsoe-abcdefgh', usda_nass_api_key='nass-abcdefgh',
        nasa_firms_map_key='firms-abcdefgh', hdx_hapi_app_identifier='hdx-abcdefgh',
        ipc_api_key='ipc-abcdefgh', copernicus_marine_username='marine-user',
        copernicus_marine_password='marine-password-abcdefgh',
        global_fishing_watch_api_token='gfw-abcdefgh',
    )


def test_canonical_registry_maps_all_current_auth_required_rows_without_secrets():
    p=credential_registry(Settings())
    assert p['profile_count']==12
    assert p['mapped_auth_required_registrations']==17
    assert p['states']=={'configured':0,'missing':12,'partial':0,'invalid':0}
    assert p['configuration_complete'] is False
    assert p['secret_material_exposed'] is False
    text=str(p).lower()
    assert 'password-abcdefgh' not in text and 'eia-abcdefgh' not in text


def test_all_profiles_can_be_configured_without_network_probe():
    p=credential_registry(configured_settings())
    assert p['states']=={'configured':12,'missing':0,'partial':0,'invalid':0}
    assert p['configuration_complete'] is True
    assert p['completion_status']=='complete'
    assert p['network_calls_performed'] is False


def test_partial_and_invalid_states_are_distinct():
    partial=Settings(epa_aqs_email='data@sustainablecatalyst.com')
    r=credential_registry(partial)
    assert next(x for x in r['profiles'] if x['id']=='epa-aqs')['state']=='partial'
    invalid=Settings(eia_api_key='change-me')
    r=credential_registry(invalid)
    assert next(x for x in r['profiles'] if x['id']=='eia-api-key')['state']=='invalid'


def test_readiness_is_control_plane_readiness_not_secret_completion():
    p=credential_readiness(Settings())
    assert p['ok'] is True
    assert p['configuration_complete'] is False
    assert p['checks']['missing_credentials_non_blocking_for_release'] is True
    assert p['network_calls_performed'] is False


def test_workspace_matrix_exposes_configuration_completion_only():
    p=credential_workspaces(configured_settings())
    assert p['workspace_count']>=10
    by={x['workspace']:x for x in p['workspaces']}
    assert by['Energy Infrastructure & Power Systems']['configuration_complete'] is True
    assert by['Ocean Surface']['configuration_complete'] is True
    assert by['Marine Human Activity & Protected Areas']['configuration_complete'] is True


def test_every_machine_auth_required_inventory_row_has_canonical_profile_and_env_key():
    rows=[r for r in source_inventory(Settings()) if r.get('machine_readable') and r.get('access_class')=='AUTH_REQUIRED']
    assert len(rows)==17
    assert all(r.get('credential_profile') for r in rows)
    assert all(r.get('configuration_key') for r in rows)
    assert all(r.get('configuration_state') in {'configuration-required','configuration-partial','configuration-invalid','configured'} for r in rows)
    cop=[r for r in rows if r.get('source_id')=='copernicus-marine']
    assert len(cop)==2 and all('SC_SI_COPERNICUS_MARINE_USERNAME' in r['configuration_key'] for r in cop)
    gfw=next(r for r in rows if r.get('source_id')=='global-fishing-watch')
    assert gfw['configuration_key']=='SC_SI_GLOBAL_FISHING_WATCH_API_TOKEN'


def test_source_profile_mapping_covers_duplicates_deliberately():
    assert canonical_configuration_for_source('Sources & Methodology','reliefweb',Settings())['credential_profile']=='reliefweb-appname'
    assert canonical_configuration_for_source('Unified Live Events','reliefweb',Settings())['credential_profile']=='reliefweb-appname'
    assert canonical_configuration_for_source('Legacy Live External Connectors','eia_energy',Settings())['credential_profile']=='eia-api-key'
    assert canonical_configuration_for_source('Legacy Live External Connectors','epa_aqs_air_quality',Settings())['credential_profile']=='epa-aqs'


def test_render_blueprints_declare_every_canonical_environment_name():
    envs={env for p in PROFILES for _field,env,_kind in p['fields']}
    for file in (ROOT/'render.yaml',ROOT/'backend/render.yaml'):
        text=file.read_text()
        missing=[e for e in envs if f'- key: {e}' not in text]
        assert not missing, (file,missing)


def test_public_routes_are_secret_safe_and_network_free():
    c=TestClient(app)
    for route in ('/public/credential-configuration','/public/credential-configuration/readiness','/public/credential-configuration/workspaces'):
        r=c.get(route); assert r.status_code==200
        p=r.json(); assert p['version']=='4.38.0'; assert p.get('network_calls_performed') is False
    text=c.get('/public/credential-configuration').text.lower()
    assert 'api_key=' not in text and 'password=' not in text and 'bearer ' not in text


def test_release_gate_requires_credential_control_plane_but_not_credentials():
    p=deployment_verification(Settings())
    assert p['ok'] is True
    assert '/public/credential-configuration/readiness' in p['required_routes']
    assert p['checks']['credential_control_plane_ready'] is True
    assert p['checks']['missing_credentials_non_blocking'] is True
    assert p['credential_configuration']['configuration_complete'] is False
    assert p['credential_configuration']['release_blocking'] is False


def test_source_health_and_production_audit_expose_secret_safe_completion_state():
    s=source_health_policy(Settings())
    assert s['credential_configuration']['profile_count']==12
    assert s['credential_configuration']['release_blocking'] is False
    p=production_audit(Settings())
    assert p['credential_configuration']['control_plane_ready'] is True
    assert p['credential_configuration']['mapped_auth_required_registrations']==17
    assert p['credential_configuration']['configuration_complete'] is False
    assert p['checks']['credential_control_plane_ready'] is True


def test_env_example_contains_all_canonical_names_but_no_secret_values():
    text=(ROOT/'backend/.env.example').read_text()
    for p in PROFILES:
        for _field,env,_kind in p['fields']:
            assert f'{env}=' in text
    for secret in ('marine-password-abcdefgh','eia-abcdefgh','gfw-abcdefgh'):
        assert secret not in text


def test_registry_contract_has_no_unknown_or_duplicate_profile_ids():
    ids=[p['id'] for p in PROFILES]
    assert len(ids)==len(set(ids))==12
    assert sum(p['registration_count'] for p in PROFILES)==17
    assert credential_readiness(configured_settings())['completion_status']=='complete'


def test_public_configuration_never_returns_value_length_hash_or_mask():
    p=credential_registry(configured_settings())
    forbidden={'value','masked_value','secret_hash','secret_fingerprint','last_four','length'}
    for profile in p['profiles']:
        assert forbidden.isdisjoint(profile.keys())
        assert profile['secret_material_exposed'] is False
