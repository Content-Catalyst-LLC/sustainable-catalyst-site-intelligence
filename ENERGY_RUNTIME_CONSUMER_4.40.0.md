# Site Intelligence 4.40.0 — Energy Systems Target-Side Runtime Consumer

This release activates the target-side consumer for Sustainable Catalyst Energy Systems Intelligence v1.2.0 handoff packets.

- Accepted packet schema: `sc-energy-runtime-handoff/1.0`
- Consumer contract: `sc-energy-runtime-site-intelligence-handoff/1.0`
- Intake: `POST /v1/energy-runtime/consume`
- Capability/status: `GET /v1/energy-runtime/consumer`
- Persistence: disabled
- Automatic execution: disabled
- Credential forwarding: disabled

Boundary: Handoff acceptance does not establish site suitability, current-year status, technical potential, or causal attribution.
