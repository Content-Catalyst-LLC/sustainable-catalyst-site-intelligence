# Site Intelligence v4.56.1 — Platform Core International Law Bridge & Connector Activation

## Purpose

v4.56.1 repairs the Core-backed data path exposed by the standalone Site Intelligence application. The initial trigger was International Law, but the same read bridge is shared by Economics, Humanitarian, Science/Earth Systems, Trade/Energy/Resources, and Country Dossiers, so the repair certifies all six workspaces together.

## Source recovery

Platform Core remains the provider registry, adapter, ingestion, normalization, and provenance authority. At the v4.56.1 baseline Core contains at least 40 registered source definitions and 39 executable connector definitions. The deployment helper re-runs Core's idempotent migration/seed routine and refuses certification if those minimum counts are not present.

Site Intelligence does not copy the adapters. When Core is addressed through the private `sc-internal` service URL (`http://sc-core:8090`), Site Intelligence converts its existing `/api/v1/...` reads to Core's equivalent `/v1/...` read routes and does not send a public API key. If Core is external, the scoped `/api/v1` API remains authoritative and requires a valid Core public key with the appropriate read scope.

## Breadth policy

Each workspace is allowed to expose as many applicable Core source families as it can safely interpret:

- Law: international-law and human-rights authority records.
- Economics: economics, finance, labour, company finance, energy, agriculture, demographics, and sustainability.
- Humanitarian: humanitarian, demographic, international-law/human-rights, and sustainability context.
- Science: Earth, atmosphere, hydrology, biomedical, chemistry, biodiversity, materials, astronomy, high-energy, infrared, and space-science sources.
- Resources: energy, economic/trade, agriculture, hydrology, Earth science, and sustainability sources.
- Dossiers: the complete applicable Core connector catalog.

Registration is not represented as successful ingestion. Many Core connectors require explicit query parameters, dataset identifiers, series identifiers, dates, geography, or free provider credentials. v4.56.1 restores and audits the connection; it does not fabricate records or automatically launch arbitrary provider ingestion from public reads.

## Production behavior

The backend deployment helper:

1. Backs up Site Intelligence backend and environment state.
2. Re-seeds/audits the Core source catalog.
3. Enables the private Core bridge on the shared Docker network.
4. Enables all six Core-backed workspaces.
5. Rebuilds Site Intelligence.
6. Requires at least 40 sources and 39 connectors through the Site Intelligence bridge.
7. Probes Law, Economics, Humanitarian, Science, Resources, and Dossiers using their canonical reliable-route semantics.
8. Keeps WordPress as a thin public launch bridge only.

Backend remains first; standalone web deployment follows only after backend certification passes.
