# Site Intelligence v2.1.0 — Global Conditions and Live Map Observatory

## Purpose

Version 2.1.0 connects the public Site Intelligence application to the public-read surface of Sustainable Catalyst Core v2.8.0. The browser receives normalized public records through the Site Intelligence backend; Core credentials remain server-side.

## Public workspace

Route:

```text
/app/?view=global
```

WordPress shortcode:

```text
[sc_global_conditions_observatory height="1150"]
```

## New public endpoints

```text
GET /public/global-conditions
GET /public/global-conditions/layers
GET /public/global-conditions/features
GET /public/global-conditions/signals
GET /public/global-conditions/diagnostics
```

## Configuration

```text
SC_SI_GLOBAL_CONDITIONS_ENABLED=true
SC_SI_PLATFORM_CORE_ENABLED=true
SC_SI_PLATFORM_CORE_URL=https://your-core-service.example
SC_SI_PLATFORM_CORE_PUBLIC_API_KEY=
SC_SI_GLOBAL_CONDITIONS_TIMEOUT_SECONDS=9
SC_SI_GLOBAL_CONDITIONS_CACHE_TTL_SECONDS=90
```

The Core public API key must have read-only `data:read` scope. It is used only by the Site Intelligence backend.

## Free-provider boundary

This release introduces no paid API dependency. When Core is unavailable, the workspace falls back to existing Site Intelligence event and Earth-observation services with a visible `local fallback` state.

## Responsible-use boundary

The global map is an orientation and research interface. It is not an emergency-response system, field survey, legal boundary service, engineering inspection, investment service, or professional certification tool.
