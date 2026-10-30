#!/usr/bin/env python3
"""Narrow SI API proxy switch. Default is a blocked dry-run, never deployment.
Receipt fields are externally verified attestations, not cryptographic approval.
This tool does not pause writers, copy state or launch containers.
"""
import argparse,datetime as dt,hashlib,json,os,re,socket,stat,subprocess,tempfile
from pathlib import Path


def sha(b):return hashlib.sha256(b).hexdigest()
def require(ok,why):
    if not ok:raise ValueError(why)


def patch_host(text,host,old,new):
    pattern=r'(?m)^'+re.escape(host)+r'\s*\{\n([^{}]*)\n\}'
    matches=list(re.finditer(pattern,text));require(len(matches)==1,'unique simple SI API block required')
    m=matches[0];body=m.group();needle='reverse_proxy 127.0.0.1:'+str(old)
    require(len(re.findall(r'(?m)^[ \t]*reverse_proxy[ \t]+127\.0\.0\.1:'+re.escape(str(old))+r'[ \t]*$',body))==1 and len(re.findall(r'\breverse_proxy\b',body))==1,'unexpected SI upstream')
    return text[:m.start()]+body.replace(needle,'reverse_proxy 127.0.0.1:'+str(new),1)+text[m.end():]


def patch(text,old,new):
    return patch_host(text,'site-intelligence-api.sustainablecatalyst.com',old,new)

def patch_frontend(text,old,new):
    return patch_host(text,'intelligence.sustainablecatalyst.com',old,new)


STATE_PATHS = {
    "backend-data/live_intelligence_analytics_state_v372.json",
    "backend-data/live_intelligence_last_known_good_v361.json",
    "backend-data/live_intelligence_rotation_state_v371.json",
    "backend-data/platform_core_queue.jsonl",
    "app-data/live_intelligence_source_operations_history_v320.jsonl",
    "app-data/country_last_known_good.json",
    "app-data/live_intelligence_source_operations_state_v320.json",
}

def verify_snapshot(root, expected):
    require(set(expected) == STATE_PATHS, 'state snapshot scope mismatch')
    require(root.is_dir() and not root.is_symlink() and stat.S_IMODE(root.stat().st_mode)&0o077==0, 'restricted immutable snapshot required')
    for name, value in expected.items():
        file=root/name
        require(not file.parent.is_symlink() and file.is_file() and not file.is_symlink(), 'regular snapshot file required')
        require(sha(file.read_bytes())==value, 'snapshot hash mismatch: '+name)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--receipt',type=Path,required=True)
    ap.add_argument('--direction',choices=['deploy','rollback'],required=True);ap.add_argument('--execute',action='store_true');ap.add_argument('--check-state-only',action='store_true');a=ap.parse_args()
    p=json.loads(a.plan.read_text());r=json.loads(a.receipt.read_text());require(socket.gethostname()==p['hostname'],'wrong host')
    for field in ['owner_approval_record','writer_quiescence_verified','independent_pi_state_restore_verified','rollback_state_compatibility_verified']:
        require(r.get(field),'open gate: '+field)
    require(r['source_commit']==p['source_commit'],'wrong receipt source')
    require(dt.datetime.fromisoformat(r['expires_utc'].replace('Z','+00:00'))>dt.datetime.now(dt.timezone.utc),'receipt expired')
    require(r.get('private_state_snapshot_sha256') and r.get('pi_state_archive_sha256'),'state recovery hashes required')
    state=Path(r['active_state_root']);require(state.is_dir() and not state.is_symlink(),'verified state root missing')
    require(stat.S_IMODE(state.stat().st_mode)&0o077==0,'state root must be restricted')
    verify_snapshot(Path(r['immutable_snapshot_root']),r['snapshot_paths_sha256'])
    if a.check_state_only:
        old=json.loads(subprocess.check_output(['docker','inspect','sc-site-intelligence'],text=True))[0]
        require(not old['State']['Running'] and old['Image']==p['rollback_image'], 'original SI writer not quiescent')
        require(old['Id']==p['old_container_id'], 'original container identity changed')
        peer='sc-site-intelligence-si214-rollback' if a.direction=='deploy' else 'sc-site-intelligence-si214'
        check=subprocess.run(['docker','inspect',peer],capture_output=True,text=True)
        if check.returncode==0:require(not json.loads(check.stdout)[0]['State']['Running'], 'other SI writer still running')
        print(json.dumps({'result':'STATE_GUARDS_PASS','execution_performed':False}));return
    deploy=a.direction=='deploy';container='sc-site-intelligence-si214' if deploy else 'sc-site-intelligence-si214-rollback'
    image=p['candidate_image'] if deploy else p['rollback_image'];port=18091 if deploy else 8091
    d=json.loads(subprocess.check_output(['docker','inspect',container],text=True))[0]
    require(d['State']['Running'] and d['Image']==image,'target container/image not verified')
    peer='sc-site-intelligence' if deploy else 'sc-site-intelligence-si214'
    other=json.loads(subprocess.check_output(['docker','inspect',peer],text=True))[0];require(not other['State']['Running'],'previous writer still running')
    import urllib.request
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=8) as f:require(f.status==200,'target liveness failed')
    if deploy:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/ready',timeout=90) as f:require(f.status==200 and json.load(f).get('ready') is True,'target readiness failed')
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/public/build-info',timeout=8) as f:require(json.load(f)['git_commit']==p['source_commit'],'target source mismatch')
    if p.get('frontend_candidate_image'):
        front='sc-site-intelligence-web-si214' if deploy else 'sc-site-intelligence-web'
        fd=json.loads(subprocess.check_output(['docker','inspect',front],text=True))[0]
        require(fd['State']['Running'] and fd['Image']==p['frontend_candidate_image' if deploy else 'frontend_rollback_image'],'frontend image not verified')
        if not deploy:require(fd['Id']==p['frontend_old_container_id'],'original frontend identity changed')
        frontport=18096 if deploy else 8096
        with urllib.request.urlopen(f'http://127.0.0.1:{frontport}/healthz',timeout=8) as f:require(f.status==200,'frontend health failed')
        if deploy:
            for name,digest in p['frontend_assets_sha256'].items():
                require(name in {'index.html','assets/bootstrap-v32361.js','assets/startup-stability-v32364.js'},'unexpected frontend asset scope')
                with urllib.request.urlopen(f'http://127.0.0.1:{frontport}/app/{name}',timeout=8) as f:require(sha(f.read())==digest,'frontend recovery asset mismatch')
    config=Path('/etc/caddy/Caddyfile');old=config.read_bytes();expected=p['proxy_before_sha256'] if deploy else r['proxy_after_sha256'];require(sha(old)==expected,'concurrent proxy/config drift')
    newtext=patch(old.decode(),8091 if deploy else 18091,18091 if deploy else 8091)
    if p.get('frontend_candidate_image'):newtext=patch_frontend(newtext,8096 if deploy else 18096,18096 if deploy else 8096)
    new=newtext.encode()
    if not a.execute:
        print(json.dumps({'result':'DRY_RUN_ONLY','before_sha256':sha(old),'after_sha256':sha(new),'direction':a.direction}));return
    require(os.geteuid()==0,'authorized administrator required for proxy execution')
    metadata=config.stat();temp=None;written=False
    try:
        with tempfile.NamedTemporaryFile(prefix='.si214-',dir=config.parent,delete=False) as f:
            temp=Path(f.name);f.write(new);f.flush();os.fsync(f.fileno())
        os.chmod(temp,stat.S_IMODE(metadata.st_mode));os.chown(temp,metadata.st_uid,metadata.st_gid)
        subprocess.run(['caddy','validate','--adapter','caddyfile','--config',str(temp)],check=True,capture_output=True)
        require(sha(config.read_bytes())==expected,'proxy changed during validation')
        os.replace(temp,config);temp=None;written=True
        subprocess.run(['systemctl','reload','caddy'],check=True,capture_output=True)
        print(json.dumps({'result':'PROXY_SWITCH_EXECUTED','direction':a.direction,'proxy_after_sha256':sha(new)}))
    except Exception:
        if written:
            require(sha(config.read_bytes())==sha(new),'cannot reverse concurrent config changes')
            with tempfile.NamedTemporaryFile(prefix='.si214-reverse-',dir=config.parent,delete=False) as f:
                restore=Path(f.name);f.write(old);f.flush();os.fsync(f.fileno())
            os.chmod(restore,stat.S_IMODE(metadata.st_mode));os.chown(restore,metadata.st_uid,metadata.st_gid);os.replace(restore,config)
            subprocess.run(['systemctl','reload','caddy'],check=True,capture_output=True)
        raise
    finally:
        if temp:temp.unlink(missing_ok=True)

if __name__=='__main__':
    try:main()
    except Exception as e:print(json.dumps({'result':'BLOCKED','reason':str(e)}));raise SystemExit(78)
