# Site Intelligence v4.35.3 — Authoritative Connector Expansion I Audit

## Baseline

v4.35.2 established the distinction between a source being registered and a source actually being retrieved. v4.35.3 closes the first portion of that gap by implementing five authoritative interfaces.

## Post-build inventory

- Source registrations: **179**
- Unique endpoint/source records after host normalization: **120**
- Source-bearing workspace/inventory groups: **39**
- Machine-readable registrations: **96**
- LIVE registrations: **32**
- DISCOVERY registrations: **8**
- AUTH_REQUIRED registrations: **10**
- REGISTERED machine-readable registrations not yet retrieved: **56**
- BULK registrations: **4**
- STALE implemented connectors: **0**
- UNAVAILABLE/portal-only registrations: **69**
- Implemented/discovery/configuration-gated registrations: **50**

The difference between five newly implemented connector interfaces and the larger increase in LIVE/DISCOVERY registration counts is intentional: several existing workspaces register the same authoritative host. A generic connector can therefore service multiple registrations without duplicating transport code.

## Connector status

| Interface | Site Intelligence mode | Workspace use |
| --- | --- | --- |
| USGS Water Data OGC API | LIVE | Hydrology |
| NOAA CoastWatch ERDDAP | LIVE | Ocean Surface and compatible NOAA ocean registrations |
| NASA Exoplanet Archive TAP | LIVE | Exoplanets / planetary-system context |
| UNHCR Refugee Statistics API | LIVE | Humanitarian / displacement context |
| NASA Common Metadata Repository | DISCOVERY | Earth, science and space dataset discovery |

## Data-integrity decisions

The release intentionally does not declare a workspace fully authoritative merely because one provider is now live. Each workspace retains separate source registrations and gap counts. Provider-specific quality, timestamp and semantic fields remain attached to returned records. Discovery services remain distinct from observation services.

## Remaining connector gap

**56 machine-readable registrations remain registered but not retrieved.** This is now the main connector-expansion backlog. v4.35.3 provides the common transport, validation, readiness and workspace-alias patterns needed to continue closing that gap in later v4.35.x connector releases.
