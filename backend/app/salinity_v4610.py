"""v4.61.0 NOAA CoastWatch SMOS daily surface salinity: read-only bounded adapter."""
from __future__ import annotations
import csv,hashlib,io,math
from datetime import date,datetime,timezone
from urllib.parse import quote
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
DATASET="coastwatchSMOSv662SSS1day"
VARIABLE="sss"
BASE="https://coastwatch.pfeg.noaa.gov/erddap/griddap/"
def retrieve_salinity_grid(latitude,longitude,day,*,transport=None):
 try:
  lat=float(latitude);lon=float(longitude);d=date.fromisoformat(day)
  if not math.isfinite(lat) or not math.isfinite(lon) or not -85<=lat<=85 or not -175<=lon<=175:raise ValueError("Coordinates outside supported safe bounds")
  if d>date.today():raise ValueError("Future day is not an observation")
  south,north=lat-.5,lat+.5;west,east=lon-.5,lon+.5
  stamp=d.isoformat()+"T12:00:00Z"
  constraint=f"{VARIABLE}[({stamp})][(0)][({south:.4f}):1:({north:.4f})][({west:.4f}):1:({east:.4f})]"
  url=BASE+DATASET+".csv?"+quote(constraint,safe="[]():")
  raw=(transport or _fetch)(url)
  if isinstance(raw,str):raw=raw.encode()
  if len(raw)>262144:raise ValueError("Upstream exceeds 256 KiB")
  reader=csv.reader(io.StringIO(raw.decode("utf-8-sig")))
  header=next(reader);units=next(reader)
  required=("time","altitude","latitude","longitude","sss")
  if any(x not in header for x in required):raise ValueError("Missing expected griddap coordinates or variable")
  ix={x:header.index(x) for x in required}
  if units[ix["sss"]].strip() not in ("PSU","1e-3",""):raise ValueError("Unexpected salinity units")
  cells=[];missing=0;times=set()
  for row in reader:
   if len(row)!=len(header):raise ValueError("Malformed upstream row")
   if len(cells)+missing>=2500:raise ValueError("Point cap exceeded")
   stamp_actual=row[ix["time"]].strip()
   if not stamp_actual.startswith(d.isoformat()):raise ValueError("Upstream returned a different observation day")
   times.add(stamp_actual)
   if abs(float(row[ix["altitude"]]))>0.01:raise ValueError("Non-surface measurement received")
   val=row[ix["sss"]].strip()
   if val.lower() in ("","nan","null"):missing+=1;continue
   v=float(val);la=float(row[ix["latitude"]]);lo=float(row[ix["longitude"]])
   if not all(map(math.isfinite,(v,la,lo))) or not 0<=v<=45:missing+=1;continue
   cells.append({"latitude":la,"longitude":lo,"value":round(v,5)})
  if not times or len(times)!=1:raise ValueError("No single daily sample returned")
  receipt={"dataset_id":DATASET,"variable_id":VARIABLE,"source_url":url,"response_sha256":hashlib.sha256(raw).hexdigest(),"response_bytes":len(raw),"retrieved_at":datetime.now(timezone.utc).isoformat(),"quality_assessment":"not independently performed"}
  return {"ok":True,"status":"retrieved" if cells else "no_data","date":day,"observation_time":next(iter(times)),"temporal_resolution":"daily","variable":"sea-surface-salinity","unit":"PSU","evidence_type":"satellite-derived","extent":{"south":south,"north":north,"west":west,"east":east},"cells":cells,"missing_count":missing,"receipt":receipt}
 except (ValueError,TypeError,OverflowError,HTTPError,URLError,TimeoutError,UnicodeError,StopIteration) as exc:
  return {"ok":False,"status":"unavailable","cells":[],"message":str(exc)[:220]}
def _fetch(url):
 with urlopen(Request(url,headers={"Accept":"text/csv","User-Agent":"SustainableCatalystOcean/4.61.0"}),timeout=18) as resp:
  if resp.status!=200:raise ValueError("Upstream HTTP non-200")
  return resp.read(262145)
