# v3.25.0 Record Provenance and Indicator Truth Audit

## Scope

The release adds record-level disclosure without claiming that provenance metadata makes a source authoritative. The implementation separates the record's presentation state, truth state, source identity, observation date, retrieval date, units, transformations, limitations, and canonical fingerprint.

## Indicator truth

A country indicator contract identifies the country, World Bank indicator code, disclosed value, original/display unit, observation year, source URL, four-step transformation ledger, limitations, and fingerprint. Kenya and Ghana packaged values remain `historical_snapshot`; countries without a verified packaged observation remain `missing`. Missing records are not imputed.

## Map-layer truth

The active Earth-observation layer can be inspected independently of the visual map. The contract identifies the NASA GIBS layer, selected date, context-only status, source terms, rendering steps, and a no-pixel-inference boundary.

## Generic public record truth

Events, charts, and table records can be normalized through a bounded POST contract. Only HTTP(S) source URLs are retained. The normalized result does not independently contact or validate the upstream publisher.

## Fingerprints

Every record contains a SHA-256 fingerprint created from sorted canonical JSON with response-generation time excluded. Repeating the same record contract produces the same fingerprint. The fingerprint is a change detector, not an accuracy, authenticity, authority, or completeness certificate.

## Exports

The browser can export the current record as JSON and can export a country manifest containing indicator and map-layer record identifiers, truth states, source URLs, observation dates, and fingerprints.

## Browser and embed behavior

The Record Truth drawer runs inside the application document, works in direct and WordPress-iframe modes, restores prior focus when closed, and does not modify the host page height.
