from __future__ import annotations

from .version import APP_VERSION

PRESENTATION_SCHEMA = "sc-site-intelligence-live-intelligence-presentation/1.0"


def presentation_policy() -> dict:
    """Return the public, non-personalized presentation and accessibility contract."""
    return {
        "schema": PRESENTATION_SCHEMA,
        "version": APP_VERSION,
        "surface": "live-intelligence",
        "default_presentation": "ticker",
        "supported_presentations": ["ticker", "static", "manual"],
        "supported_mobile_presentations": ["rotator", "stacked", "marquee", "hidden"],
        "motion": {
            "slow_configurable_motion": True,
            "pause_on_hover": True,
            "pause_on_keyboard_focus": True,
            "manual_pause_control": True,
            "reduced_motion_default": "static",
            "reduced_motion_options": ["static", "manual"],
            "background_auto_advance": False,
            "hidden_document_auto_advance": False,
        },
        "navigation": {
            "previous_next_controls": True,
            "swipe_navigation": True,
            "arrow_key_navigation": True,
            "position_indicator": True,
            "minimum_touch_target_css_pixels": 44,
        },
        "accessibility": {
            "animated_viewport_live_region": False,
            "dedicated_status_live_region": True,
            "manual_navigation_announcements": True,
            "automatic_rotation_announcements": False,
            "full_signal_accessible_names": True,
            "no_javascript_fallback": True,
            "forced_colors_supported": True,
            "two_hundred_percent_zoom_supported": True,
        },
        "content": {
            "default_max_visible": 8,
            "minimum_max_visible": 1,
            "maximum_max_visible": 12,
            "duplicate_animation_set_hidden_from_assistive_technology": True,
            "long_visual_labels_may_be_truncated": True,
            "accessible_names_must_not_be_truncated": True,
        },
        "boundaries": [
            "The ticker is not an emergency warning service.",
            "Motion must never be required to access a signal.",
            "Automatic movement must not trigger repetitive screen-reader announcements.",
            "Static and manual presentations use the same validated public signal feed.",
            "Presentation settings do not alter source ranking, freshness, or evidence lineage.",
        ],
    }
