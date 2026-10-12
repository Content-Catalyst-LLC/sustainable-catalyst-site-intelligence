"""Read-only, bounded NOAA ERDDAP griddap SST retrieval. No arbitrary host or dataset URLs."""
from __future__ import annotations
import csv
import hashlib
import io
import math
from datetime import date as Date
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

DATASET="jplMURSST41"
VARIABLE="analysed_sst"
BASE="https://coastwatch.pfeg.noaa.gov/erddap/griddap/"
MAX_BYTES=32768

def retrieve_sst(latitude: float, longitude: float, day: str, *, transport=None):
    try:
        lat=float(latitude); lon=float(longitude); selected=Date.fromisoformat(day)
    except (TypeError,ValueError) as exc:
        raise ValueError("Valid latitude, longitude and ISO date are required") from exc
    if not (math.isfinite(lat) and math.isfinite(lon) and -89.99<=lat<=89.99 and -179.99<=lon<=179.99):
        raise ValueError("Coordinates must be finite and within ERDDAP query bounds")
    if selected>Date.today():
        raise ValueError("Future dates cannot be retrieved as observations")
    # ERDDAP permits coordinate constraints in axis order: time, latitude, longitude.
    constraint=f"{VARIABLE}[({selected.isoformat()}T00:00:00Z)][({lat:.4f})][({lon:.4f})]"
    url=BASE+DATASET+".csv?"+quote(constraint,safe="[]():")
    fetch=transport or _fetch
    try:
        raw=fetch(url)
        if isinstance(raw,str):raw=raw.encode()
        if len(raw)>MAX_BYTES:raise ValueError("NOAA reply exceeds single-point limit")
        rows=list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
        if len(rows)<3 or len(rows)>5:raise ValueError("Unexpected ERDDAP CSV shape")
        header=rows[0]
        if VARIABLE not in header:raise ValueError("ERDDAP variable is missing")
        idx=header.index(VARIABLE)
        unit=rows[1][idx].strip()
        if unit not in ("degree_C","degrees_C","degC","degree_Celsius","K"):
            raise ValueError("Unrecognized ERDDAP SST unit")
        readings=[]
        for fields in rows[2:]:
            if len(fields)!=len(header):raise ValueError("Malformed ERDDAP row")
            cell=fields[idx].strip()
            if cell.lower() in ("","nan","null"):continue
            val=float(cell)
            if not math.isfinite(val):continue
            if unit=="K":val-=273.15
            if not -5<=val<=50:raise ValueError("SST outside defensible range")
            readings.append((fields,val))
        digest=hashlib.sha256(raw).hexdigest()
        receipt={"retrieval_method":"https-erddap-griddap-csv","retrieved_at":datetime.now(timezone.utc).isoformat(),"source_url":url,"dataset_id":DATASET,"data_variable":VARIABLE,"response_sha256":digest,"bytes":len(raw),"network_response_received":True,"source_content_authenticity_independently_proven":False}
        if not readings:
            return {"ok":True,"status":"no_data","observation":None,"receipt":receipt,"message":"No finite NOAA SST value at the requested grid point/date."}
        if len(readings)!=1:raise ValueError("Expected one ocean-grid observation")
        fields,val=readings[0]
        timestamp=fields[header.index("time")] if "time" in header else selected.isoformat()+"T00:00:00Z"
        record={"variable":{"id":"sea-surface-temperature","title":"Sea-surface temperature"},"source":{"id":"noaa-coastwatch-erddap","title":"NOAA CoastWatch ERDDAP","url":BASE},"dataset_id":DATASET,"source_record_id":None,"evidence_type":"satellite-derived","value":round(val,5),"unit":"degC","point":{"latitude":lat,"longitude":lon},"observed_at":timestamp,"quality_flags":[],"network_response_independently_verified":True,"evidence_state":"retrieved-from-noaa-erddap","retrieval_receipt":receipt}
        return {"ok":True,"status":"retrieved","observation":record,"receipt":receipt}
    except (HTTPError,URLError,TimeoutError,UnicodeError,ValueError,IndexError,OverflowError) as exc:
        return {"ok":False,"status":"unavailable","observation":None,"message":str(exc)[:300]}

def _fetch(url):
    req=Request(url,headers={"Accept":"text/csv","User-Agent":"SustainableCatalystOcean/4.57.6"})
    with urlopen(req,timeout=12) as response:
        if response.status!=200:raise ValueError("NOAA upstream returned non-200")
        return response.read(MAX_BYTES+1)
