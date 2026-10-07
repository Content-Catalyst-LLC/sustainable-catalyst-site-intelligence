from __future__ import annotations

import os
from typing import Iterable

from .route_registry_v4430 import capability_manifest
from .standalone_authority_v4440 import CANONICAL_APP_PATH, build_bootstrap
from .version import APP_VERSION

BRIDGE_CONTRACT_VERSION = "1.1.0"
WORDPRESS_ROLE = "public-site-launch-bridge"
WEB_APP_URL = os.getenv("SC_SI_WEB_APP_URL", "https://intelligence.sustainablecatalyst.com").rstrip("/")
CANONICAL_SHORTCODES = (
    "sc_site_intelligence_app",
    "sc_site_intelligence_embed",
    "sc_site_intelligence_home",
    "sc_earth_observation_studio",
    "sc_live_event_intelligence",
    "sc_global_country_intelligence",
)
COMPATIBILITY_SHORTCODE_COUNT = 72


def bridge_contract(routes: Iterable[object]) -> dict:
    manifest = capability_manifest(routes)
    bootstrap = build_bootstrap(routes, "wordpress-embed")
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": BRIDGE_CONTRACT_VERSION,
        "integration": "wordpress",
        "wordpress_role": WORDPRESS_ROLE,
        "product_authority": "fastapi",
        "canonical_application": WEB_APP_URL + "/",
        "legacy_embed_application": CANONICAL_APP_PATH,
        "runtime_mode": bootstrap["runtime"]["mode"],
        "responsibilities": {
            "wordpress": [
                "navigation-entry-points",
                "standalone-application-launch-links",
                "selected-public-view-embeds",
                "release-compatibility-checks",
                "optional-auth-handoff",
                "publication-and-content-shell",
            ],
            "fastapi": [
                "feature-authority",
                "application-state-contracts",
                "data-and-analysis-apis",
                "capability-registry",
                "standalone-web-application",
            ],
        },
        "boundaries": {
            "wordpress_feature_authority": False,
            "wordpress_model_execution": False,
            "wordpress_data_authority": False,
            "wordpress_new_feature_shortcodes": False,
            "wordpress_application_runtime": False,
            "wordpress_routing_authority": False,
            "wordpress_state_authority": False,
            "legacy_shortcode_compatibility": True,
        },
        "endpoints": {
            "standalone_bootstrap": "/public/app/bootstrap?surface=wordpress-embed",
            "runtime_handshake": "/public/app/runtime-handshake?surface=wordpress-embed",
            "navigation": "/public/app/navigation",
            "release_gate": "/public/release-gate",
            "bridge": "/public/integrations/wordpress/bridge",
            "embed_contract": "/public/integrations/wordpress/embed-contract",
            "auth_handoff": "/public/integrations/wordpress/auth-handoff",
            "compatibility": "/public/integrations/wordpress/compatibility",
        },
        "capability_registry": {
            "registry_version": manifest["registry_version"],
            "capability_count": manifest["capability_count"],
            "route_count": manifest["route_count"],
        },
    }


def embed_contract() -> dict:
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": BRIDGE_CONTRACT_VERSION,
        "mode": "iframe",
        "source": CANONICAL_APP_PATH,
        "canonical_web_application": WEB_APP_URL + "/",
        "legacy_embed_only": True,
        "surface": "wordpress-embed",
        "query_transport": {
            "release": APP_VERSION,
            "surface": "wordpress-embed",
            "bridge": "wordpress",
            "bridge_version": BRIDGE_CONTRACT_VERSION,
            "supported": ["view", "country", "compare", "theme", "chrome", "institution"],
        },
        "messaging": {
            "parent_to_app": ["SC_SI_REQUEST_HEIGHT"],
            "app_to_parent": ["scsi-bootstrap-ready", "scsi-shell-ready", "scsi-wordpress-bridge-ready", "scsi-height"],
            "version_required": True,
            "origin_validation_required": True,
        },
        "security": {
            "referrer_policy": "strict-origin-when-cross-origin",
            "allow": ["fullscreen", "clipboard-write"],
            "credentials_in_query": False,
        },
    }


def auth_handoff_contract() -> dict:
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": BRIDGE_CONTRACT_VERSION,
        "mode": "optional-delegated-handoff",
        "provider": "wordpress",
        "status": "contract-ready-no-global-session-authority",
        "anonymous_access_supported": True,
        "fastapi_session_authority": False,
        "wordpress_session_authority": False,
        "token_transport": "not-enabled",
        "boundaries": [
            "No WordPress credentials are sent in embed query parameters.",
            "No global authentication state is created by this release.",
            "Future authenticated handoff must use an explicit signed exchange contract.",
        ],
    }


def compatibility_contract() -> dict:
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": BRIDGE_CONTRACT_VERSION,
        "retained_shortcode_count": COMPATIBILITY_SHORTCODE_COUNT,
        "canonical_bridge_shortcodes": list(CANONICAL_SHORTCODES),
        "policy": {
            "existing_published_shortcodes": "preserved",
            "new_feature_shortcodes": "prohibited",
            "new_product_features": "standalone-fastapi-first",
            "wordpress_role": WORDPRESS_ROLE,
        },
    }
