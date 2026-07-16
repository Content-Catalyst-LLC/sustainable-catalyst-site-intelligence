# Site Intelligence v2.21.0 — Scheduled Monitoring, Digests, and Public Intelligence Feeds

## Purpose

v2.21.0 adds a governed operational layer above the existing public intelligence stream. Administrators can define reusable monitors, run explicit due checks, suppress duplicate matches, prepare daily or weekly digests, review publication decisions, and expose approved outputs through JSON, RSS, and Atom.

## Core contracts

- Monitor definitions support manual, hourly, daily, and weekly cadences.
- The backend does not claim an always-on scheduler. `/admin/scheduled-monitoring/run-due` is an explicit invocation point and defaults to `dry_run=true`.
- Alert fingerprints include the monitor, rule, signal identity, observation time, value, and source. Deduplication remains visible in check receipts.
- Digests are deterministic and remain drafts until a human explicitly approves or publishes them.
- Public feeds require no hosted subscriber account, subscriber tracking, or user profile.
- Email and webhook adapters are optional, disabled by default, and produce redacted delivery receipts.
- Quiet periods and delivery states are explicit.

## Public endpoints

- `GET /public/scheduled-monitoring`
- `GET /public/scheduled-monitoring/diagnostics`
- `GET /public/intelligence-digests`
- `GET /public/intelligence-digests/{digest_id}`
- `GET /public/intelligence-feeds`
- `GET /public/intelligence-feeds/{feed_id}?format=json|rss|atom`

## Administrative endpoints

- `GET /admin/scheduled-monitoring/control-center`
- `POST /admin/scheduled-monitoring/monitors`
- `POST /admin/scheduled-monitoring/monitors/{monitor_id}/check`
- `POST /admin/scheduled-monitoring/run-due?dry_run=true`
- `POST /admin/scheduled-monitoring/digests`
- `POST /admin/scheduled-monitoring/digests/{digest_id}/review`
- `POST /admin/scheduled-monitoring/digests/{digest_id}/deliver`
- `POST /admin/scheduled-monitoring/feeds`

## Responsible-use boundary

No match does not prove that no real-world event or change occurred. Monitor rules are not emergency warnings, official notices, individual risk scores, investment recommendations, or autonomous decisions. Public digests require human approval. Delivery adapters do not receive ChatGPT conversations or hidden user profiles.
