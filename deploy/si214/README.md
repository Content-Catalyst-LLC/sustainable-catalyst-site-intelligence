# SI-2.1.4 consolidated candidate

SI-2.1.1–SI-2.1.4 are one corrective release candidate. The application API/schema identity remains 4.56.1; OCI/release metadata identifies SI-2.1.4 and the exact source commit. No new providers, routes, privileges or fabricated records are introduced.

The existing five energy-spatial routes predate the stale route-count assertions. Their public, request-local/read-only contract and infrastructure-energy ownership remain unchanged. Twelve count assertions plus the consolidation registry are reconciled to 1,530. Modularized routes remain 216 and capabilities remain 33. Legitimate World Bank fallback is 206/partial; invalid/failed/unavailable fallback remains 503. Source attribution is bounded diagnostic metadata.

Development uses the existing compose.yml + compose.dev.yml + compose.pi-core-read.yml, unchanged. Core write/public keys remain empty. Real runtime credentials, .env files, service-account files, runtime state and .bak files are excluded from source/deployment packages. The test-only dependency file supplies httpx for Starlette TestClient; runtime dependencies are not upgraded.

Build from a verified architecture-compatible existing runtime image (fixed image ID checked before tag/build), using this Dockerfile and a context containing only Git-tracked backend/app and backend/data. Preserve original image/source and all production writable state. No production Compose recreation is safe while unpersisted state in /app/data and /app/backend/data is unresolved. Production uses a separate image-pinned side-by-side Compose service, loopback port and narrow reversible Caddy API upstream switch only after approval. Never deploy development Compose files or an ARM64 image to x86_64 production.

The complete unexcluded backend/tests + tests run and baseline comparison are release evidence. Older version/packaging contract failures are reported separately; no silent exclusions or blanket version rewrites. A red relevant/security gate or missing state recovery is BLOCKED, not deployment approval.
