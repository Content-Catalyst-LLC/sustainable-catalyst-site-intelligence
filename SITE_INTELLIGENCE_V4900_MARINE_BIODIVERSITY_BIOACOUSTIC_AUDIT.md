# Site Intelligence v4.11.0 — Marine Biodiversity & Bioacoustic Intelligence Audit

## Architecture

The feature is a deferred extension of Underwater Observation inside the existing Earth Observation route. No public route is added; the v4 platform remains six primary areas and 35 routes.

## Registered source contracts

1. **OBIS** — occurrence/event records. Occurrence evidence is not population size, continued presence, or habitat suitability. An explicit absence record is preserved as explicit absence; zero query results are not recast as absence.
2. **WoRMS** — taxonomic names/classification/accepted-name resolution. Taxonomy is an authority record, not occurrence or distribution evidence.
3. **FathomNet** — underwater visual annotations and model-oriented labels. Model inference remains machine inference unless separately verified by source evidence; a visual label does not become abundance or an OBIS occurrence record automatically.
4. **Ocean Networks Canada hydrophones** — recordings, spectrograms, manual/expert annotations, and model detections. A recording is not itself a species detection; detections remain method- and interval-bounded.

## Evidence separation

The release keeps occurrence, taxonomy, visual annotation, acoustic recording, acoustic detection, and environmental context as distinct evidence classes. Cross-class promotion requires explicit source evidence and is never inferred from UI proximity.

## Browser behavior

The local interface renders an evidence-relationship orientation field rather than fabricated biological observations. Initial state loads no occurrence, visual, acoustic, taxonomy, abundance, presence, or absence claim.

## Security and provenance

Normalizer source URLs are restricted to registered HTTPS provider hosts. Each normalized record receives a deterministic SHA-256 fingerprint and retains retrieval/source context. No upstream credentials are embedded in public code.
