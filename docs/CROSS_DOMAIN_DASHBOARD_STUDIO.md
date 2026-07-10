# Cross-Domain Intelligence and Public Dashboard Studio — v1.12.1

## Purpose

The studio composes existing Site Intelligence domains into public dashboards using versioned configuration rather than dashboard-specific backend code.

## Public endpoints

- `/public/dashboard-studio`
- `/public/dashboard-studio/manifest`
- `/public/dashboard-studio/{dashboard_id}`
- `/public/dashboard-studio/{dashboard_id}/data`
- `/public/dashboard-studio/{dashboard_id}/sources`
- `/public/dashboard-studio/{dashboard_id}/brief`
- `/public/dashboard-studio/{dashboard_id}/export`
- `/public/country-intelligence/{country_code}`
- `/public/cross-domain-comparison`

## WordPress shortcodes

- `[sc_public_dashboard_studio]`
- `[sc_public_cross_domain_dashboard_directory]`
- `[sc_public_intelligence_dashboard id="climate-human-vulnerability" country="KEN"]`
- `[sc_public_country_intelligence country="KEN"]`
- `[sc_public_cross_domain_comparison country="KEN" compare="GHA"]`
- `[sc_public_dashboard_sources id="climate-human-vulnerability"]`
- `[sc_public_dashboard_export id="climate-human-vulnerability" country="KEN"]`

## Governance

Cross-domain associations are contextual. The studio preserves source-specific definitions, units, dates, uncertainty, freshness, and legal or procedural status. It does not establish causality, legal responsibility, eligibility, or professional advice.
