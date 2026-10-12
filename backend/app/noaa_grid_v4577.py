"""v4.57.7: bounded, source-backed NOAA ERDDAP geographic SST grid."""
from __future__ import annotations
import csv,hashlib,io,math
from datetime import date as Date,datetime,timezone
from urllib.parse import quote
from urllib.error import HTTPError,URLError
from .noaa_erddap_v4576 import BASE,DATASET,VARIABLE,_fetch

def retrieve_grid(latitude:float,longitude:float,day:str,*,transport=None):
    try:
        lat=float(latitude);lon=float(longitude);d=Date.fromisoformat(day)
    except (ValueError,TypeError) as exc:raise ValueError("A valid ISO date and coordinates are required") from exc
    if not all(map(math.isfinite,(lat,lon))) or not -85<=lat<=85 or not -175<=lon<=175:raise ValueError("Center must be within grid safety bounds")
    if d>Date.today():raise ValueError("Future dates cannot be observations")
    # Bounded 11x11 grid with 0.1 degree stride (approximate ERDDAP nearest resolution).
    south,north=lat-.5,lat+.5;west,east=lon-.5,lon+.5
    constraint=f"{VARIABLE}[({d.isoformat()}T00:00:00Z)][({south:.4f}):({north:.4f})][({west:.4f}):({east:.4f})]"
    url=BASE+DATASET+".csv?"+quote(constraint,safe="[]():")
    fetch=transport or _fetch
    try:
        raw=fetch(url)
        if isinstance(raw,str):raw=raw.encode()
        if len(raw)>262144:raise ValueError("NOAA grid response exceeds 256 KiB")
        reader=csv.reader(io.StringIO(raw.decode("utf-8-sig")))
        header=next(reader);units=next(reader)
        if not all(x in header for x in ("latitude","longitude",VARIABLE)):raise ValueError("NOAA coordinate/value columns absent")
        vi=header.index(VARIABLE);li=header.index("latitude");oi=header.index("longitude")
        unit=units[vi].strip()
        if unit not in ("degree_C","degrees_C","degC","degree_Celsius","K"):raise ValueError("NOAA unit unrecognized")
        cells=[];missing=0
        for row in reader:
            if len(cells)+missing>=2500:raise ValueError("NOAA grid exceeds point cap")
            if len(row)!=len(header):raise ValueError("Malformed NOAA grid row")
            value=row[vi].strip()
            if value.lower() in ("","nan","null"):missing+=1;continue
            v=float(value);la=float(row[li]);lo=float(row[oi])
            if not all(map(math.isfinite,(v,la,lo))):missing+=1;continue
            if unit=="K":v-=273.15
            if not -5<=v<=50:missing+=1;continue
            cells.append({"latitude":la,"longitude":lo,"value":round(v,4)})
        receipt={"dataset_id":DATASET,"variable_id":VARIABLE,"source_url":url,"response_sha256":hashlib.sha256(raw).hexdigest(),"retrieved_at":datetime.now(timezone.utc).isoformat(),"response_bytes":len(raw),"network_response_received":True,"quality_assessment":"not independently performed"}
        return {"ok":True,"status":"retrieved" if cells else "no_data","date":day,"unit":"degC","evidence_type":"satellite-derived","extent":{"south":south,"north":north,"west":west,"east":east},"cells":cells,"missing_count":missing,"receipt":receipt}
    except (HTTPError,URLError,TimeoutError,UnicodeError,ValueError,StopIteration,OverflowError) as exc:
        return {"ok":False,"status":"unavailable","cells":[],"message":str(exc)[:250]}
