# Site Intelligence v4.37.0 R4

## Science/Ocean Workspace Controller, Route Ownership & Ocean/Space Prominence Repair

R4 repairs the production `Workspace unavailable` failure observed after the Science/Ocean discovery work. The backend contracts were healthy; the failure was in browser controller delivery and route/surface ownership.

### Runtime repair

- The main router now verifies the R4 Science controller and dynamically reloads it when an older or missing controller is present.
- Science initializes correctly even when loaded after `DOMContentLoaded`.
- Ocean waits for the Earth route transition before claiming `earth:ocean` workspace ownership and hydrating its catalog.
- Production Truth recognizes Ocean mode as a distinct visible surface and requires `data-ocean-hydration-state=ready` plus exactly 11 marine cards.
- R4-specific cache lineage is applied to the main router, Science, Ocean, Production Truth, bootstrap, and service worker.

### Ocean and Space prominence

- Ocean and Space are the two persistent **Featured science systems** at the top of the consolidated navigation.
- The Launch portfolio exposes direct **Explore Ocean** and **Explore Space** actions.
- Ocean and Space each have dedicated Launch portfolio cards.
- Space opens directly into the Science workspace filtered to six local modules: Orbital Earth, Lunar & Planetary Intelligence, Astronomical Observation, Solar System Navigation, Exoplanets & Atmospheres, and SETI & Technosignatures.
- No new canonical route is created; the six-area / 35-route architecture remains intact.
- Platform Core remains optional for these local discovery surfaces.
