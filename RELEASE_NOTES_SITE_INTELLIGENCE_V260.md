# Sustainable Catalyst Site Intelligence v2.6.0

## Trade, Energy, and Resource Security Observatory

Site Intelligence v2.6.0 adds a public, source-aware workspace for official trade, energy, electricity, agriculture, food, water, materials, supply-chain, and climate-transition records delivered through Sustainable Catalyst Core.

### Public workspace

- Route: `/app/?view=resources`
- WordPress shortcode: `[sc_trade_energy_resource_security_observatory height="1450"]`

### Public capabilities

- Official trade and counterpart records
- Energy generation, capacity, consumption, price, fuel, and transition records
- Agriculture and food-system indicators
- Water-resource and water-stress records
- Materials and strategic-resource discovery
- Country coverage map
- Published counterpart relationship lists
- Country resource profiles
- Source-aware CSV export
- Shareable filtered views
- Briefing workflow handoff

### Integrity boundaries

- Values with different units, currencies, price bases, directions, classifications, periods, and geographic definitions are not silently combined.
- Counterpart relationships are not automatically classified as dependency, vulnerability, coercion, sanctions exposure, or disruption risk.
- The observatory creates no proprietary resource-security score.
- No licensed real-time exchange feed is claimed.
- No demonstration values are created when Platform Core is unavailable.
- The workspace is not investment, trade, sanctions, legal, engineering, or national-security advice.

### Configuration

```text
SC_SI_TRADE_ENERGY_RESOURCE_SECURITY_ENABLED=true
SC_SI_TRADE_ENERGY_RESOURCE_SECURITY_TIMEOUT_SECONDS=9
SC_SI_TRADE_ENERGY_RESOURCE_SECURITY_CACHE_TTL_SECONDS=120
```
