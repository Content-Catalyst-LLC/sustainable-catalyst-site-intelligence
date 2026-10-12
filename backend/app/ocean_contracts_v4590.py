"""Site Intelligence 4.59.0: scientific ocean variable/source contracts.

Capabilities are intentionally explicit: only NOAA MUR SST has a certified read-only retrieval
adapter. Registry entries for other variables are definitions, not claims of live observations.
"""
from __future__ import annotations
from datetime import datetime
from math import isfinite

VARIABLES={
 "sea-surface-temperature":("Sea-surface temperature","degC","scalar"),
 "chlorophyll-a":("Chlorophyll-a concentration","mg/m3","scalar"),
 "sea-surface-salinity":("Sea-surface salinity","1e-3","scalar"),
 "surface-current":("Surface current velocity","m/s","vector"),
 "sea-surface-height-anomaly":("Sea-surface height anomaly","m","scalar"),
 "surface-wind":("Surface wind","m/s","vector"),
 "significant-wave-height":("Significant wave height","m","scalar"),
}
SOURCES={
 "noaa-mur-sst":dict(provider="NOAA ERDDAP",dataset_id="jplMURSST41",variable_id="analysed_sst",variable="sea-surface-temperature",evidence_type="satellite-derived",adapter="noaa-sst-grid-v4577",capability="live-verified",url="https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41.html"),
 "noaa-snpp-chlorophyll-monthly":dict(provider="NOAA OceanWatch PIFSC ERDDAP",dataset_id="noaa_snpp_chla_monthly",variable_id="chlor_a",variable="chlorophyll-a",evidence_type="satellite-derived",adapter="chlorophyll-grid-v4600",capability="integration-pending",url="https://oceanwatch.pifsc.noaa.gov/erddap/griddap/noaa_snpp_chla_monthly.html"),
 "noaa-smos-daily-salinity":dict(provider="NOAA NESDIS CoastWatch",dataset_id="coastwatchSMOSv662SSS1day",variable_id="sss",variable="sea-surface-salinity",evidence_type="satellite-derived",adapter="salinity-grid-v4610",capability="integration-pending",url="https://coastwatch.pfeg.noaa.gov/erddap/griddap/coastwatchSMOSv662SSS1day.html"),
}
def registry():
 return {"schema":"scsi-ocean-variable-registry/4.59.0","variables":[{"id":k,"label":v[0],"canonical_unit":v[1],"geometry":v[2],"retrieval_status":"live-verified" if any(s["variable"]==k and s["capability"]=="live-verified" for s in SOURCES.values()) else "not-connected"} for k,v in VARIABLES.items()],"sources":[{"id":k,**v} for k,v in SOURCES.items()],"policy":{"missing_is_not_zero":True,"cross_variable_arithmetic_requires_explicit_conversions":True,"forecasts_are_not_observations":True,"unconnected_variables_do_not_imply_data_availability":True}}

def normalize_record(*,variable_id,source_id,value,latitude,longitude,observed_at,evidence_type,receipt,unit=None):
 if variable_id not in VARIABLES:raise ValueError("Unknown variable")
 if source_id not in SOURCES or SOURCES[source_id]["variable"]!=variable_id:raise ValueError("Unsupported source and variable combination")
 name,canonical,geometry=VARIABLES[variable_id]
 if geometry!="scalar":raise ValueError("Vector records require explicit component normalization, not scalar coercion")
 if unit is not None and unit!=canonical:raise ValueError("Unit mismatch; explicit conversion required")
 if evidence_type!=SOURCES[source_id]["evidence_type"]:raise ValueError("Evidence classification mismatches source")
 if not isinstance(receipt,dict) or not isinstance(receipt.get("response_sha256"),str) or len(receipt["response_sha256"])!=64:raise ValueError("Missing response receipt")
 try:
  v=float(value);lat=float(latitude);lon=float(longitude)
  if not all(map(isfinite,(v,lat,lon))) or not -90<=lat<=90 or not -180<=lon<=180:raise ValueError()
  timestamp=datetime.fromisoformat(observed_at.replace("Z","+00:00"))
  if timestamp.tzinfo is None:raise ValueError()
 except (TypeError,ValueError,AttributeError) as exc:raise ValueError("Invalid numeric/geographic/time fields") from exc
 return {"schema":"scsi-ocean-observation/4.59.0","variable":{"id":variable_id,"name":name,"unit":canonical,"geometry":geometry},"source":{"id":source_id,"dataset_id":SOURCES[source_id]["dataset_id"],"provider":SOURCES[source_id]["provider"]},"measurement":{"value":v,"evidence_type":evidence_type,"observed_at":timestamp.isoformat()},"location":{"latitude":lat,"longitude":lon},"provenance":{"retrieval_receipt":receipt,"scientific_accuracy_independently_verified":False}}
