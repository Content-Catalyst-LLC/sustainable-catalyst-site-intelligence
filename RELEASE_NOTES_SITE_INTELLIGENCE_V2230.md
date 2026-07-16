# Sustainable Catalyst Site Intelligence v2.23.0

## Typed Cross-Platform Intelligence Workflows

Site Intelligence v2.23.0 adds a governed handoff layer connecting Site Intelligence with Workbench, Decision Studio, Research Librarian, Knowledge Library, Research Lab, and Platform Core.

### Highlights

- Twelve typed bidirectional route contracts
- Required-field and route-direction validation
- Portable JSON packets with workflow IDs and SHA-256 integrity
- Provenance links to source records, packets, URLs, and methodologies
- Explicit external receipts and status updates
- Linkbacks to external records
- Bounded failed-handoff queues and human-confirmed retries
- Public route methodology with private operational records
- Dedicated Workflows public application surface
- WordPress public and administrator shortcodes

### Responsible operation

The release does not perform or claim automatic remote writes. A packet is not considered delivered until an external platform or Platform Core returns an explicit receipt. File-backed mode does not include a persistent message broker, automatic retry worker, account provisioning, individual tracking, or autonomous consequential decisions.

### Validation target

- 528 backend tests
- 502-file immutable release manifest
- Python, JavaScript, service-worker, PHP, JSON, and webmanifest checks
- Runtime-state exclusion and post-test manifest verification
