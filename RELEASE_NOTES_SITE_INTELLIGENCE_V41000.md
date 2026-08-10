# Site Intelligence v4.16.0 — Ocean Missions, Vehicles & Observatory Network

v4.16.0 connects ocean-observing platforms and mission records without turning catalog metadata into fabricated live telemetry. The v4 six-area/35-route platform architecture remains unchanged.

## Added

- Argo/Argovis platform and track evidence contract.
- U.S. IOOS glider, buoy, mooring, and fixed-observatory registry contract.
- Ocean Networks Canada observatory, camera, hydrophone, AUV, and ROV contract.
- NOAA Ocean Exploration historical expedition, vessel, ROV, and AUV contract.
- Ten platform classes with explicit source compatibility.
- Source-attributed platform, mission, and discrete-track normalizers.
- Timestamp-required source positions and deterministic SHA-256 fingerprints.
- Deferred Missions & Network browser interface after Marine Biodiversity.

## Scientific / operational boundaries

- Registry presence does not prove a platform is currently active.
- A last-reported position is not a verified current position.
- Source-reported operating status is time-bounded and is not silently recast as current.
- Discrete track points are not interpolated into continuous trajectories.
- Historical expedition/dive tracks are not live feeds.
- Nearby observations are not treated as platform positions.
- Future positions and trajectories are never predicted by this contract.
