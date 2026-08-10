# Site Intelligence v4.12.0 — Security, Observability, Performance, and Scale Assurance

This release hardens the existing public-intelligence platform rather than adding another observatory.

## Production controls
- Production administrative access fails closed when the API token is absent or left at the development placeholder.
- Administrative rate limiting is enforced using a one-way token fingerprint rather than visitor IP persistence.
- CORS headers are narrowed to the documented public/admin request surface.
- The application shell receives a first-party CSP, object/base/form restrictions, and production HSTS.
- Response-local Server-Timing makes application latency inspectable without creating visitor profiles.

## Assurance surfaces
- Security posture
- Aggregate observability contract
- Shipped-asset performance budgets
- Rate-limit projection
- Dependency/supply-chain posture
- Post-deployment smoke-test preview

## Boundaries
This release does not claim penetration testing, compliance certification, distributed tracing, distributed rate limiting, or guaranteed performance on every device/network.
