# Site Intelligence v3.1.1 — Live Intelligence Content and Interface Repair

## What changed

Site Intelligence v3.1.1 repairs the electronic Live Intelligence board introduced in v3.1.0 and makes its homepage content materially more useful.

The feed now prioritizes verified public-interest records from the existing Site Intelligence event and environmental connector layers:

- latest significant USGS earthquake record;
- 14-day count of USGS M4.5+ earthquake records;
- latest open NASA EONET natural event;
- summarized open natural-event counts;
- latest ReliefWeb humanitarian report;
- current 14-day humanitarian-report count;
- NOAA/NWS active-alert and short-term temperature context when live or cached source data are available;
- one quiet Site Intelligence connection marker.

Demonstration event fixtures and sample weather values are explicitly excluded.

## Interface repairs

- Hover pause now works through both a higher-specificity CSS rule and explicit JavaScript hover state.
- Keyboard focus pauses the board while links or controls are being used.
- The pause button remains independent and continues to work.
- A temporary refresh failure preserves the last rendered verified signals and marks the board as cached/delayed.
- Automatic placement defaults to **Below Astra breadcrumb**.
- Administrators can choose **Below breadcrumb**, **Below global header**, or **Disabled — shortcode only**.
- The utility navigation and breadcrumb area can use a warm parchment surface matching the rest of Sustainable Catalyst.

## Shortcode

`[sc_live_intelligence]` remains available on any page. Supported attributes include `category`, `limit`, `motion`, `label`, `show_sources`, and `show_updated`.

## Public-data boundaries

The board does not show raw upstream API payloads, credentials, demonstration records, fabricated values, emergency instructions, causal claims, or financial recommendations. Annual or periodic records retain their source timing rather than being described as real-time.
