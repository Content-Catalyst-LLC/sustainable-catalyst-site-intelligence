from __future__ import annotations
from .release_health_v43531 import deployment_verification as prior_deployment, source_health_policy as prior_source_health
from .credential_configuration_v43516 import credential_readiness, credential_registry
from .version import APP_VERSION

VERSION=APP_VERSION
CONTRACT='deployment-verification-credential-control-plane-v43516'

def deployment_verification(settings):
    p=prior_deployment(settings)
    cr=credential_readiness(settings)
    p['version']=VERSION; p['contract']=CONTRACT
    p['checks']['credential_control_plane_ready']=cr['ok']
    p['checks']['missing_credentials_non_blocking']=True
    p['required_routes']=list(p['required_routes'])+['/public/credential-configuration/readiness']
    p['checks']['required_route_contract_declared']=len(p['required_routes'])==8
    p['credential_configuration']={'configuration_complete':cr['configuration_complete'],'completion_status':cr['completion_status'],'release_blocking':False}
    p['ok']=all(p['checks'].values())
    return p

def source_health_policy(settings):
    p=prior_source_health(settings); p['version']=VERSION; p['contract']=CONTRACT
    reg=credential_registry(settings)
    p['credential_configuration']={'profile_count':reg['profile_count'],'states':reg['states'],'configuration_complete':reg['configuration_complete'],'release_blocking':False}
    return p
