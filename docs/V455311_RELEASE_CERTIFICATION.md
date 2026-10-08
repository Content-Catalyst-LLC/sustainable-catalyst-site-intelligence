# Site Intelligence v4.55.3.1.1 — Certification

Certification requires the focused v4.55.3.1.1 test suite, the carried regression line, Python/JS/PHP/shell syntax checks, release-bound file alignment, and validation against the extracted shipped repository archive.

Production deployment is contract-certified only after `/health`, `/ready`, `/public/capability-health?probe=true`, and all six canonical reliable domain routes return structured responses. A 503 is acceptable evidence of a truthful unavailable dependency; a raw/unparseable 500 is not.
