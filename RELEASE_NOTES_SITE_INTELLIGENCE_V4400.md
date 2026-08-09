# Site Intelligence v4.9.0 — Solar System Navigation & Mission Ephemeris

## Purpose

v4.9.0 connects Orbital Earth, Lunar & Planetary Intelligence, and Astronomical Observation through a single solar-system navigation state inside the existing Earth Observation route. The release preserves the v4 six-area / 35-route architecture.

## New capability

- Solar-system destination catalog covering the Sun, eight planets, Moon, and Pluto.
- Mission-context catalog for Voyager 1, Voyager 2, New Horizons, Juno, Mars Reconnaissance Orbiter, and Lunar Reconnaissance Orbiter.
- Explicit observation epoch, observer, and reference-frame request state.
- JPL Horizons ephemeris handoff and NAIF SPICE mission-geometry handoff.
- NASA Eyes external exploratory-visualization handoff kept separate from the numerical evidence contract.
- Source-attributed ephemeris normalization with registered-host enforcement and deterministic fingerprints.
- Reproducible solar-system navigation evidence manifests.
- Direct application and WordPress-iframe browser support.

## Evidence boundary

The local solar-system layout is an orientation diagram only. It is not an ephemeris, is not to scale, and does not claim current body positions. Site Intelligence does not invent spacecraft position, velocity, trajectory, ground track, instrument pointing, or mission geometry. Numerical ephemeris evidence is accepted only through an explicitly attributed JPL Horizons or NAIF SPICE record, and recognized source attribution is not represented as independent network verification.

## Public API

- `GET /public/solar-system-navigation`
- `GET /public/solar-system-navigation/catalog`
- `GET /public/solar-system-navigation/body/{body_id}`
- `GET /public/solar-system-navigation/mission/{mission_id}`
- `GET /public/solar-system-navigation/state`
- `POST /public/solar-system-navigation/ephemeris/normalize`
- `GET /public/solar-system-navigation/export-manifest`
- `GET /public/solar-system-navigation/readiness`

## Compatibility

Orbital Earth, Lunar & Planetary Intelligence, Astronomical Observation, Data Truth, record provenance, unified cross-view state, research workflows, publication, governance, monitoring, and the fixed WordPress embed remain intact. No top-level public route was added.
