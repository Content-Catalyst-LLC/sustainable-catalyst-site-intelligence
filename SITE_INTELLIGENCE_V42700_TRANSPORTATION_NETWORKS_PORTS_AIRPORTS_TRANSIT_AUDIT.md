# Site Intelligence v4.27.0 Transportation Evidence Audit

## Scope

This audit covers the v4.27.0 Transportation Networks, Ports, Airports & Transit Intelligence increment.

## Evidence classes

- `open-transport-network-feature`
- `unlocode-location-record`
- `community-airport-record`
- `mobility-feed-catalog-record`

## Required non-inference rules

- Network segment ≠ guaranteed navigable route.
- Network access attribute ≠ legal authorization.
- UN/LOCODE location/function ≠ current operating facility.
- OurAirports airport/runway record ≠ official aeronautical information.
- GTFS Schedule or Realtime feed ≠ service guarantee.
- Mobility feed catalog ≠ complete transit coverage.
- Missing records ≠ absence of infrastructure or service.
- Accessibility screening ≠ actual travel time, route operability, emergency access or navigation instruction.

## Source-specific limitations

### Overture Maps Transportation

The transportation model represents roads, rails, waterways, connectors and associated attributes from multiple source systems. Dataset geometry and attributes must retain release/source context and must not be treated as real-time route condition or legal-access evidence.

### UNECE UN/LOCODE

UN/LOCODE is a trade/transport location coding system. Location records and function codes identify recognized trade/transport places but do not independently establish current facility operation, capacity, ownership, security status or shipment suitability.

### OurAirports

OurAirports is community-maintained open data released to the public domain. Its airport/runway/navaid records are orientation evidence only and are not an authoritative aeronautical publication.

### MobilityData Mobility Database

The Mobility Database catalogs and mirrors producer GTFS/GTFS-RT/GBFS feeds. Individual feed licenses, freshness, service periods, quality reports and producer authority remain source-specific. Feed presence does not prove live service or complete network coverage.

## Release-governance checks

- 4 source families registered.
- 17 indicator types registered.
- 4 evidence classes registered.
- 8 public endpoint contracts present.
- six-area / 35-route shell unchanged.
- backend/WordPress transportation assets byte-identical.
- service worker includes v4.27 JS/CSS.
- bounded Render polling retained.
- transportation live deep gate required before WordPress installation.
