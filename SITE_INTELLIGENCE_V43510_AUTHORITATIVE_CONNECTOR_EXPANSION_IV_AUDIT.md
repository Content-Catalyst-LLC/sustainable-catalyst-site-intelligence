# Site Intelligence v4.35.13 — Authoritative Connector Expansion IV Audit

## Purpose
Continue closing the production connector backlog using first-party governmental and intergovernmental machine interfaces without weakening source semantics, provenance, missing-value handling, or deployment reliability.

## Added connector interfaces

### FAOSTAT Data API — LIVE implementation
Authority: Food and Agriculture Organization of the United Nations.
Workspace scope: Agriculture, food security, human development.
Controls: server-configurable API base; requires at least one bounded dimension filter; preserves domain, area, item, element, year, units, flags, and notes. Statistical observations are not treated as real-time food-security conditions.

### ILOSTAT SDMX / indicator service — LIVE
Authority: International Labour Organization.
Workspace scope: labor, economics, human development.
Controls: validated indicator and reference-area identifiers; bounded year windows; preserves distinctions among survey observations, harmonized series, and modelled estimates.

### OECD Data Explorer SDMX — LIVE
Authority: OECD.
Workspace scope: economics, development, environment.
Controls: explicit agency/dataflow/version/key; rejects all/unbounded keys; bounded response size; preserves frequency, unit, and SDMX attributes.

### EPA Facility Registry Service — LIVE
Authority: U.S. Environmental Protection Agency.
Workspace scope: industrial/manufacturing facilities.
Controls: requires facility/locality/program/ZIP or bounded spatial query; maximum 25-mile radius. Facility registry inclusion is not a compliance, emissions, exposure, or legal finding.

### USGS Volcano HANS — LIVE
Authority: U.S. Geological Survey Volcano Hazards Program.
Workspace scope: geosphere / volcanoes.
Controls: recent-notice request limited to 1–7 days and allowlisted observatories. Site Intelligence preserves USGS alert/color-code statements and never creates, escalates, downgrades, or supersedes an alert.

## Closure impact
Machine-readable production audit: 105 registrations; LIVE 41; DISCOVERY 6; AUTH_REQUIRED 11; REGISTERED-not-retrieved 43; BULK 4; STALE 0. The machine-readable retrieval backlog falls from 44 to 43 because the existing USGS HANS registry gap is genuinely closed; the other four new interfaces are additive first-party registrations implemented at introduction.

## Deployment policy
External provider availability remains operational source health, not a release blocker. Deterministic readiness performs no upstream network calls.
