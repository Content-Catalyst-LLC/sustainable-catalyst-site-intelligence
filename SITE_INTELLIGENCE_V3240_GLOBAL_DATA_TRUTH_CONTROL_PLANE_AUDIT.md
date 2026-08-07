# Site Intelligence v3.26.0 Global Data Truth Control Plane Audit

## Scope

The release composes the eight source contracts already present in Site Intelligence. It does not add connectors, contact upstream APIs during control-plane rendering, or create synthetic source history.

## Control-plane dimensions

1. **Operational state** — presentation, freshness, last attempt, last success, and record count.
2. **Schema state** — expected and observed fingerprints, review state, and disclosed check timestamps.
3. **Resilience state** — circuit state, consecutive failures, and last-known-good availability.
4. **Metadata state** — required source and coverage metadata completeness.
5. **Country coverage** — eligibility and country-linked evidence remain separate.
6. **Workspace state** — each major workspace reports the status of its disclosed source dependencies for the selected country.

## History boundary

The history register is derived from current runtime metadata. It is not an append-only telemetry archive and does not claim completeness. Events without disclosed timestamps remain release snapshots rather than fabricated dated events.

## Incident boundary

The incident register identifies source contracts requiring attention. A control-plane incident is not proof of a worldwide publisher outage. The release performs no automatic remediation, connector mutation, public outage publication, or credentialed action.

## Export integrity

The export contains overview, schema drift, incident, coverage, and workspace payloads plus a SHA-256 fingerprint over the exported disclosure. The fingerprint detects changes to that disclosure; it is not a digital signature or source certification.
