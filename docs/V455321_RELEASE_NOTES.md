# Site Intelligence v4.55.3.2.1 — Runtime Health Truth & Domain Context Repair

This corrective release repairs two production defects found after v4.55.3.2 standalone deployment.

1. **Runtime health truth.** Site Intelligence no longer reports the entire application as Offline merely because three or more optional diagnostics fail. Offline is reserved for browser/network loss or failure of the canonical `/health` endpoint. Optional diagnostics, domain dependencies, maps, or secondary services produce a truthful Degraded state.
2. **Domain country context.** Standalone deep links now propagate country context into the query key each domain actually consumes. `/economics/KEN`, `/science/KEN`, and `/resources/KEN` carry `geography_code=KEN`; Law, Humanitarian, and Dossiers retain `country=KEN`.
3. **Economics empty-state truth.** Economics reads the global country context, follows global country changes, and does not display a green “records available” claim when Platform Core is connected but the current query returns zero records.

No new providers or fabricated records are introduced. Economics may still have zero substantive domain records until v4.55.4 activates provider/data coverage.
