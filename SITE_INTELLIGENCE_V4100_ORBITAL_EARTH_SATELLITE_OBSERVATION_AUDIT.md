# v4.16.0 Orbital Earth & Satellite Observation Audit

The release extends the existing `earth` route instead of creating a new primary workspace. Orbital state preserves the selected observation layer, requested date, geographic center, and source attribution.

The visual globe is a 2.5D orbital perspective using the same registered NASA GIBS tile products already used by Earth Observation. It is intentionally not described as an orthographic geodesic renderer or physical spacecraft-camera simulation.

The API explicitly returns `real_time_spacecraft_position: null`, `ground_track: null`, `ephemeris_connected: false`, and `instantaneous_sensor_swath: null`. This prevents presentation graphics from being misread as current mission telemetry.
