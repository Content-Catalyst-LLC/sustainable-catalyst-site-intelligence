# v4.36.0 R2 Science Discovery Audit

## Reported production failure

The Science workspace displayed `Platform Core is not configured; no scientific records are fabricated locally.` Its dropdowns were empty because the v2.4 Science UI populated every scientific selector from Platform Core records.

## Root cause

The Science route predates the v4.x Ocean and Space workspaces. It conflated **scientific record federation** with **science workspace discovery**. Ocean and Space now have substantial local Site Intelligence capabilities that do not require Platform Core, but the Science front door did not know how to expose them.

## R2 architecture

R2 separates:

1. **Local Science discovery** — always available, network-free, and limited to workspace/navigation metadata.
2. **Platform Core scientific record fabric** — optional source-backed records, assets, layers, STAC items, and time series.

No scientific evidence is fabricated to bridge the two layers.

## Always-available domains

- Earth
- Ocean
- Space

## Local workspaces

- Earth Observation
- Ocean Intelligence
- Orbital Earth
- Lunar & Planetary Intelligence
- Astronomical Observation
- Solar System Navigation
- Exoplanets & Atmospheres
- SETI & Technosignatures

## Truth boundary

An available workspace means only that the Site Intelligence interface and its registered source contracts are available. It does not imply that Platform Core scientific records are configured, that upstream scientific providers are live, or that a scientific observation has been loaded.
