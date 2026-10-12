# Site Intelligence v4.57.0 — Standalone Visual Parity Restoration (in progress)

## Implemented on main
- Preserve the initial requested route before first map-driven URL synchronization and prevent premature overview URL mutation.
- Rehydrate Ocean Intelligence when direct navigation requests `?view=earth&oceanMode=hub` (optional `oceanSystem`).
- Cache-bust modified application and ocean assets in both standalone HTML entrypoints.
- Supply a read-only HTTPS/JSON map/source/imagery preflight at `scripts/certify-v4570.sh`.

## Not yet certified
- Browser-rendered NASA GIBS imagery or actual successful observation tiles.
- Interactive Earth imagery comparison, orbit visuals, and all 11 Ocean workspaces.
- Country maps and comparative/source cards across multiple providers.
- Science, Law, Resources and Humanitarian record counts, provenance, filters and charts.
- Backend runtime version alignment (still separately versioned 4.56.1).
- Full browser end-to-end suite against staging or production.

## Required release gates
1. Deep links to country, earth and ocean survive initial map startup and remain on their requested route.
2. Every map surface has nonzero size when active and shows real loaded imagery/geometry.
3. Ocean hub shows 11 live modules and their source evidence is verifiable.
4. Country views show actual source-by-source counts and provenance, not merely expected source labels.
5. World Bank Economics records and controls remain functional.
6. Staging and production use matching tested frontend artifact hashes, and rollback archives are retained.

This is an incremental in-repository build, not a production-certified v4.57.0. Do not mark release gate PASS until those checks succeed.
