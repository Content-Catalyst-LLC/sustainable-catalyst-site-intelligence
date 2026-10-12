"""v4.60.0 NOAA OceanWatch monthly chlorophyll-a read-only grid.

NOAA PIFSC published dataset: noaa_snpp_chla_monthly, chlor_a, time/lat/lon.
Date selection is explicit ERDDAP nearest-coordinate; returned actual time is checked
against requested month to prevent presenting wrong-month observations.
"""
import csv,hashlib,io,math
from datetime import date,datetime,timezone
from urllib.parse import quote
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
BASE="https://oceanwatch.pifsc.noaa.gov/erddap/griddap/"
DATASET="noaa_snpp_chla_monthly"
VARIABLE="chlor_a"

def retrieve_chlorophyll_grid(latitude,longitude,day,*,transport=None):
 try:
  lat=float(latitude);lon=float(longitude);d=date.fromisoformat(day)
  if not math.isfinite(lat) or not math.isfinite(lon) or not -68<=lat<=68 or not -178<=lon<=178:raise ValueError("Center outside bounded coverage")
  if d>date.today():raise ValueError("Future observations disallowed")
  south,north=lat-.5,lat+.5;west,east=lon-.5,lon+.5
  # Monthly composites are not daily observations. Select requested month's midpoint,
  # verify returned time belongs to requested calendar month before exposing cells.
  selector=f"{d.year:04d}-{d.month:02d}-01T12:00:00Z"
  # NOAA axis order: descending latitude, ascending longitude in 0..360.
  west360=(west+360)%360
  east360=(east+360)%360
  if east360<=west360:raise ValueError("0/360 boundary crossing needs split queries")
  constraint=f"{VARIABLE}[({selector})][({north:.4f}):3:({south:.4f})][({west360:.4f}):3:({east360:.4f})]"
  url=BASE+DATASET+".csv?"+quote(constraint,safe="[]():")
  raw=(transport or _fetch)(url)
  if isinstance(raw,str):raw=raw.encode()
  if len(raw)>262144:raise ValueError("Upstream response exceeds 256 KiB")
  reader=csv.reader(io.StringIO(raw.decode("utf-8-sig")))
  header=next(reader);units=next(reader)
  required=("time","latitude","longitude",VARIABLE)
  if not all(x in header for x in required):raise ValueError("Unexpected upstream columns")
  indices={k:header.index(k) for k in required}
  unit=units[indices[VARIABLE]].strip().replace(" ","")
  if unit not in ("mgm-3","mg/m3","mgm^-3","mgm**-3"):raise ValueError("Unexpected chlorophyll units")
  cells=[];missing=0;times=set()
  for row in reader:
   if len(cells)+missing>=2500:raise ValueError("Grid point cap exceeded")
   if len(row)!=len(header):raise ValueError("Malformed upstream row")
   actual=row[indices["time"]].strip()
   if not actual.startswith(f"{d.year:04d}-{d.month:02d}-"):raise ValueError("Upstream returned a different composite month")
   times.add(actual)
   value=row[indices[VARIABLE]].strip()
   if value.lower() in ("nan","","null"):missing+=1;continue
   v=float(value);la=float(row[indices["latitude"]]);lo=float(row[indices["longitude"]])
   if not all(math.isfinite(x) for x in (v,la,lo)) or v<0 or v>1000:missing+=1;continue
   cells.append({"latitude":la,"longitude":lo-360 if lo>180 else lo,"value":round(v,6)})
  if not times:raise ValueError("No rows returned for requested month")
  if len(times)!=1:raise ValueError("Multiple composite timestamps in one query")
  receipt=dict(dataset_id=DATASET,variable_id=VARIABLE,source_url=url,response_sha256=hashlib.sha256(raw).hexdigest(),retrieved_at=datetime.now(timezone.utc).isoformat(),response_bytes=len(raw),network_response_received=True,quality_assessment="not independently performed")
  return {"ok":True,"status":"retrieved" if cells else "no_data","date":day,"composite_time":next(iter(times)),"temporal_resolution":"monthly","variable":"chlorophyll-a","unit":"mg/m3","evidence_type":"satellite-derived","extent":{"south":south,"north":north,"west":west,"east":east},"cells":cells,"missing_count":missing,"receipt":receipt}
 except (ValueError,TypeError,OverflowError,HTTPError,URLError,TimeoutError,UnicodeError,StopIteration) as exc:
  return {"ok":False,"status":"unavailable","cells":[],"message":str(exc)[:220]}

def _fetch(url):
 with urlopen(Request(url,headers={"Accept":"text/csv","User-Agent":"SustainableCatalystOcean/4.60.0"}),timeout=18) as response:
  if response.status!=200:raise ValueError("Upstream HTTP non-200")
  return response.read(262145)
