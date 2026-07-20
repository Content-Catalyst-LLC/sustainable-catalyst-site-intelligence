# Site Intelligence v3.1.3 — Feed Selection and Placement Reliability Repair

## Purpose

This release gives administrators direct control over the public sources represented in the electronic Live Intelligence ticker and prevents the automatic homepage ticker from disappearing when Astra does not emit the configured breadcrumb hook.

## Feed controls

The WordPress settings page now provides independent checkboxes for:

- NOAA / National Weather Service
- USGS Earthquakes
- NASA EONET Natural Events
- ReliefWeb Humanitarian Reports
- NASA POWER Observations
- OpenAlex Research
- World Bank Indicators
- Site Intelligence Platform Status

The automatic ticker uses the saved feed set. Platform status remains optional and is not enabled in the WordPress default feed set.

Administrators can also choose a one-to-five item repetition limit per displayed source. The default is two.

## Shortcode controls

`[sc_live_intelligence]` now supports:

- `feeds="usgs_earthquakes,noaa_nws,reliefweb"`
- `exclude="platform_status,world_bank"`
- `max_per_source="2"`
- the existing `category`, `limit`, `motion`, source, freshness, label, and placement controls

Shortcode feed overrides can be disabled globally so manually placed tickers follow the administrator-selected feed set.

## Placement reliability

Below-breadcrumb placement still follows Astra's configured breadcrumb hook. A duplicate-safe content fallback now restores the ticker when a front-page or page-builder layout does not emit that hook. A render guard prevents the primary hook and fallback from producing two tickers.

The release does not change navigation, utility-navigation, breadcrumb, or page-surface colors.

## Backend contract

`GET /public/live-intelligence` now accepts:

- `feeds`
- `exclude`
- `max_per_source`
- existing `category` and `limit` parameters

Each returned signal includes a canonical `feed_id`, and the response reports active, excluded, and represented feed counts.

## Boundaries

- No browser API keys are introduced.
- Demonstration and sample values remain excluded.
- Disabling a feed prevents it from appearing; it does not alter the upstream source.
- Feed selection does not imply importance, endorsement, severity, or completeness.
- Astra and the active theme remain responsible for navigation and breadcrumb colors.
