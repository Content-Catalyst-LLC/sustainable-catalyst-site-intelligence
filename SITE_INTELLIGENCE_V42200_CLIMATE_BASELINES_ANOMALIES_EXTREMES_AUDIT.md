# Site Intelligence v4.22.0 Climate Baselines, Anomalies & Extremes Audit

## Architecture

- Primary public areas: **6 (unchanged)**
- Public routes: **35 (unchanged)**
- New environment: deferred Earth Observation climate panel after Soils & Land Condition
- New public contract family: `/public/climate`

## Evidence classes

- station climate observation
- climate normal
- climate reanalysis
- preliminary reanalysis
- gridded temperature-anomaly analysis
- global/zonal temperature-anomaly series
- source-calculated climate-extreme index
- WMO-certified climate record

## Source boundaries

### NOAA NCEI
Historical observations and Climate Normals retain station/location, quality-control, period-of-record, and normal-period context. CDO API v2 token requirements are explicit; credentials are not shipped in public state.

### Copernicus ERA5
ERA5 is model-observation reanalysis, not direct measurement at each grid cell. Preliminary ERA5T and final reanalysis remain distinct. Grid spacing is not represented as local-site accuracy.

### NASA GISTEMP v4
Temperature anomaly values retain baseline context and revision status. Anomalies are not converted into absolute local temperatures and are not represented as causal attribution findings.

### WMO climate extremes
Source-calculated indices and formally certified records remain different evidence classes. Site Intelligence never certifies a record, issues a WMO finding, or converts an index threshold into an emergency warning.

## Deployment-verifier findings carried forward

The v4.21 production wait exposed two verifier weaknesses:

1. a wrong inherited JavaScript symbol (`SCSIGeosphereV42100`) made the geosphere deep gate impossible to satisfy even when the v4.21 backend was live;
2. 80 polls, 15-second sleeps, and 45-second curl timeouts could leave the foreground installer apparently frozen for a prolonged period.

v4.22 corrects the symbol and makes polling bounded, visible, and diagnostically useful.
