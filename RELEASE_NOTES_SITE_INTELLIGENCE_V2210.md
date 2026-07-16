# Site Intelligence v2.21.0

## Scheduled Monitoring, Digests, and Public Intelligence Feeds

This release turns the existing public intelligence stream into a governed monitoring and delivery workflow.

### Added

- Reusable manual, hourly, daily, and weekly monitor definitions
- Explicit due-monitor previews and bounded batch execution
- Deterministic rule evaluation and SHA-256 alert fingerprints
- Duplicate suppression with configurable time windows
- Grouped daily and weekly digest generation
- Human approval and publication gates for public digests
- Public JSON, RSS, and Atom feeds
- Quiet periods and redacted delivery receipts
- Optional email and webhook adapter boundaries, disabled by default
- Public app Monitoring workspace
- Public and administrator WordPress shortcodes
- CLI, release-contract tests, immutable manifest validation, and installer isolation

### Responsible-use boundaries

The release does not claim an embedded always-on scheduler, emergency authority, guaranteed source completeness, individual tracking, subscriber profiling, hidden risk scoring, or automatic publication. A missing match is not evidence that no real-world event occurred.

### Validation

- 504 backend tests passed
- 622 unique application HTML IDs
- 471 immutable files verified
- Python, JavaScript, service-worker, PHP, JSON, and webmanifest checks passed
- Writable monitoring and inherited runtime state excluded from the package
