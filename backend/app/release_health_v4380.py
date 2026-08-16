from __future__ import annotations

from .release_health_v4370 import deployment_verification as prior_deployment, source_health_policy as prior_source_health
from .live_space_observation_v4380 import readiness as space_readiness, provider_catalog as space_providers
from .version import APP_VERSION

VERSION=APP_VERSION
CONTRACT='deployment-verification-live-space-observation-v4380'
REQUIRED=("/public/space-observation/providers","/public/space-observation/readiness")

def deployment_verification(settings):
    payload=prior_deployment(settings)
    space=space_readiness(settings)
    payload['version']=VERSION
    payload['contract']=CONTRACT
    checks=payload['checks']
    live=space.get('checks',{})
    checks['live_space_observation_ready']=space.get('ok') is True
    checks['planetary_archive_lane_ready']=live.get('planetary_stac_public') is True
    checks['mast_space_lane_ready']=live.get('mast_public_query') is True
    checks['jpl_horizons_lane_ready']=live.get('jpl_horizons_public') is True
    checks['nasa_exoplanet_lane_ready']=live.get('nasa_exoplanet_tap_public') is True
    checks['seti_archive_lane_ready']=live.get('breakthrough_archive_public') is True
    checks['space_credential_free_core_ready']=live.get('credential_free_core_space') is True
    checks['space_readiness_network_free']=space.get('network_calls_performed') is False
    routes=list(payload.get('required_routes') or [])
    for route in REQUIRED:
        if route not in routes:routes.append(route)
    payload['required_routes']=routes
    checks['required_route_contract_declared']=len(routes)==23
    payload['live_space_observation']=space
    payload['ok']=all(checks.values())
    return payload

def source_health_policy(settings):
    payload=prior_source_health(settings)
    providers=space_providers(settings)
    payload['version']=VERSION
    payload['contract']=CONTRACT
    payload['space_observation']={'provider_count':providers.get('provider_count'),'default_provider':providers.get('default_provider'),'providers':[{'id':r.get('id'),'configured':r.get('configured'),'configuration_required':r.get('configuration_required'),'release_blocking':False} for r in providers.get('providers',[])],'credential_required':False,'network_calls_performed':False}
    return payload
