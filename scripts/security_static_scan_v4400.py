#!/usr/bin/env python3
from pathlib import Path
import re,sys,json
ROOT=Path(__file__).resolve().parents[1]
findings=[]
patterns=[("private-key",re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),("aws-key",re.compile(r"AKIA[0-9A-Z]{16}")),("github-pat",re.compile(r"ghp_[A-Za-z0-9]{30,}"))]
for base in [ROOT/"backend/app",ROOT/"backend/public_app",ROOT/"wordpress-plugin",ROOT/"scripts"]:
  for p in base.rglob("*"):
    if not p.is_file() or p.suffix.lower() in {".png",".jpg",".jpeg",".webp",".woff",".woff2"}: continue
    try: text=p.read_text(errors="ignore")
    except Exception: continue
    for name,pat in patterns:
      if pat.search(text): findings.append({"type":name,"path":str(p.relative_to(ROOT))})
print(json.dumps({"ok":not findings,"findings":findings,"scanned_roots":["backend/app","backend/public_app","wordpress-plugin","scripts"]},indent=2))
if findings: sys.exit(1)
