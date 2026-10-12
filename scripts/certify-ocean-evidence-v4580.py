"""Offline v4.58.0 integrity check for exported NOAA SST packages.

Checks internal consistency only, never asserts NOAA scientific authenticity.
Usage: python3 scripts/certify-ocean-evidence-v4580.py /path/evidence.json
"""
import json, math, sys
from pathlib import Path

def certify(package):
    problems=[]
    def fail(s):problems.append(s)
    primary=package.get("primary_grid")
    second=package.get("comparison_grid")
    comp=package.get("comparison")
    if not isinstance(primary,dict):return ["Missing primary grid"]
    for label,grid in (("primary",primary),("comparison",second)):
        if grid is None:
            if label=="comparison" and comp is None:continue
            fail(label+" grid missing");continue
        receipt=grid.get("receipt") or {}
        if not isinstance(receipt.get("response_sha256"),str) or len(receipt["response_sha256"])!=64 or any(ch not in "0123456789abcdef" for ch in receipt["response_sha256"].lower()):fail(label+" receipt hash invalid")
        if not receipt.get("source_url","").startswith("https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41.csv?"):fail(label+" source URL unexpected")
        if grid.get("status")!="retrieved" or grid.get("unit")!="degC":fail(label+" status/unit unexpected")
        cells=grid.get("cells")
        if not isinstance(cells,list) or not cells:fail(label+" no measured cells");continue
        keys=set()
        for cell in cells:
            try:
                k=(round(float(cell["latitude"]),4),round(float(cell["longitude"]),4))
                value=float(cell["value"])
                if not all(map(math.isfinite,(*k,value))) or not -5<=value<=50:raise ValueError()
                if k in keys:fail(label+" duplicate coordinate")
                keys.add(k)
            except (KeyError,ValueError,TypeError):fail(label+" malformed cell")
    if comp is not None:
        if not isinstance(second,dict):fail("Missing comparison grid")
        else:
            if primary.get("date")==second.get("date"):fail("Comparison dates identical")
            if primary.get("unit")!=second.get("unit"):fail("Units differ")
            if primary.get("receipt",{}).get("dataset_id")!=second.get("receipt",{}).get("dataset_id"):fail("Dataset differs")
            p={(round(c["latitude"],4),round(c["longitude"],4)):c["value"] for c in primary["cells"]}
            s={(round(c["latitude"],4),round(c["longitude"],4)):c["value"] for c in second["cells"]}
            common=p.keys() & s.keys()
            if comp.get("matching_cells")!=len(common) or comp.get("unmatched_first")!=len(p.keys()-common) or comp.get("unmatched_second")!=len(s.keys()-common):fail("Coordinate counts inconsistent")
            rows=comp.get("cells",[])
            if len(rows)!=len(common):fail("Delta count inconsistent")
            delta=[]
            for row in rows:
                key=(round(row["latitude"],4),round(row["longitude"],4))
                if key not in common:fail("Unmatched coordinate in comparison");continue
                expected=round(s[key]-p[key],4)
                if abs(row.get("first",0)-p[key])>0.00001 or abs(row.get("second",0)-s[key])>0.00001 or abs(row.get("delta",0)-expected)>0.00001:fail("Difference mismatch "+str(key))
                delta.append(expected)
            if delta and abs(comp.get("mean_delta",0)-round(sum(delta)/len(delta),4))>0.00001:fail("Mean difference mismatch")
    if package.get("receipt_assessment",{}).get("scientific_accuracy_independently_verified") is not False:fail("Scientific assessment claim invalid")
    return sorted(set(problems))

def main():
    if len(sys.argv)!=2:raise SystemExit("Usage: certify-ocean-evidence-v4580.py FILE.json")
    data=json.loads(Path(sys.argv[1]).read_text())
    issues=certify(data)
    print(json.dumps({"status":"FAIL" if issues else "PASS","checks":"internal arithmetic, receipts present, schema consistency; not independent NOAA verification","issues":issues},indent=2))
    raise SystemExit(1 if issues else 0)

if __name__=="__main__":main()
