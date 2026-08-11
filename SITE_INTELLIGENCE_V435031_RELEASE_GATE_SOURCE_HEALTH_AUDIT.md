# v4.35.4 Release-Gate & Source-Health Audit

## Problem addressed

The prior promotion verifier required a large set of domain/runtime probes to be simultaneously true. The deployment log showed the correct v4.35.2 version and Git commit with the release gate ready, including at least one fully-green deep observation, but later independent domain probes fluctuated and caused the installer to fail verification.

## New release decision

Release promotion is based only on first-party deployment integrity:

1. Expected backend version.
2. Expected release id.
3. Expected Git commit.
4. Existing release gate ready.
5. `/health` healthy and version-aligned.
6. `/public/runtime-health` healthy with no upstream network probes.
7. `/public/deployment-verification` green.
8. `/public/v4/readiness` structurally preserves 35 routes.
9. `/public/authoritative-connectors/readiness` deterministic and network-free.
10. Application HTML, JavaScript and CSS are present and version-aligned.

## Source-health policy

External authoritative sources never block deployment. The source-health policy reports configuration separately and reserves operational states for healthy, degraded, unavailable and unknown conditions. The deterministic release check itself performs no external source probe.

## Regression protection

The v4.35.4 test suite asserts that the current promotion script contains no `Deep gate:` and does not probe representative domain state endpoints such as Climate, Biodiversity, Mining, Water/Sanitation or Exoplanet state routes.
