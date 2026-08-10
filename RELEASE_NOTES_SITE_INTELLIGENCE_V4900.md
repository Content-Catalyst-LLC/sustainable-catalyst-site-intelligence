# Site Intelligence v4.12.0 — Marine Biodiversity & Bioacoustic Intelligence

v4.12.0 extends Underwater Observation from visual media into structured biological and acoustic evidence while preserving the v4 six-area/35-route platform architecture.

## Added

- OBIS occurrence/event evidence contract.
- WoRMS taxonomy/accepted-name evidence contract.
- FathomNet visual annotation evidence contract.
- Ocean Networks Canada hydrophone/acoustic evidence contract.
- Six distinct evidence classes: occurrence, taxonomy, visual annotation, acoustic recording, acoustic detection, and environmental context.
- Source-bound normalizers for occurrence, taxonomy, visual, and acoustic evidence.
- Deterministic SHA-256 fingerprints and export manifests.
- Deferred direct/iframe browser interface reachable from Underwater Observation.

## Scientific boundaries

- Zero returned occurrence records do not prove absence.
- Explicit source absence remains distinct from a search with no records.
- Taxonomy records do not prove occurrence or distribution.
- Visual annotations do not automatically become occurrence records.
- Model visual/acoustic detections are not automatically verified species identifications.
- An acoustic recording is not itself a biological detection.
- Acoustic detection does not imply abundance or population size.
- Environmental context is not assumed co-temporal/co-located unless the source relationship says so.
