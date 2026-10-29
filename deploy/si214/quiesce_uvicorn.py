#!/usr/bin/env python3
"""Run INSIDE only the specifically approved SI container. Default is dry-run.
The window identifier records external operator authorization; it is not an auth system.
Disable that container's automatic restart under the approved maintenance procedure first.
"""
import argparse,json,os,signal
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--approved-window');args=ap.parse_args()
pids=[]
for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:argv=(p/'cmdline').read_bytes().split(b'\0')
    except OSError:continue
    if b'app.main:app' in argv and any(a==b'uvicorn' or a.endswith(b'/uvicorn') for a in argv):pids.append(int(p.name))
if len(pids)!=1:raise SystemExit('Refuse: expected exactly one SI Uvicorn process')
if args.execute:
    if not args.approved_window:raise SystemExit('Explicit approved maintenance-window record required')
    os.kill(pids[0],signal.SIGTERM)
print(json.dumps({'uvicorn_process_count':1,'signal_sent':args.execute,'force_kill':False,'approved_window':args.approved_window}))
