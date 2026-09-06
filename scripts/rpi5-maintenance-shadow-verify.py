#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, pwd, re, subprocess
from pathlib import Path

def cmd(args, cwd=None):
    p=subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return p.returncode,p.stdout.strip(),p.stderr.strip()

def sha256(path: Path):
    h=hashlib.sha256()
    try:
        with path.open('rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    except (PermissionError, OSError):
        return None
    return h.hexdigest()

def parse_allowlisted_config(path: Path):
    out={}
    if not path.is_file() or not os.access(path, os.R_OK): return out
    allowed={'UPDATE_USER','MAIN_COMPOSE_DIR','CV_COMPOSE_DIR'}
    for raw in path.read_text(errors='replace').splitlines():
        m=re.match(r'^\s*([A-Z0-9_]+)=(.*)$',raw)
        if not m or m.group(1) not in allowed: continue
        v=m.group(2).strip()
        if len(v)>=2 and v[0]==v[-1] and v[0] in "\"'": v=v[1:-1]
        if '$' in v or '`' in v: continue
        out[m.group(1)]=v
    return out

def compose_state(project_dir: str):
    result={'dir':project_dir,'config_ok':False,'expected_services':[],'actual_services':[],'bad_containers':[]}
    p=Path(project_dir)
    if not p.is_dir(): result['error']='directory-missing'; return result
    rc,out,err=cmd(['docker','compose','config','--services'],cwd=p)
    if rc: result['error']='config-failed'; result['stderr']=err[-400:]; return result
    result['config_ok']=True; result['expected_services']=[x for x in out.splitlines() if x]
    rc,out,err=cmd(['docker','compose','ps','--all','--services'],cwd=p)
    if rc: result['error']='ps-failed'; result['stderr']=err[-400:]; return result
    result['actual_services']=[x for x in out.splitlines() if x]
    rc,out,_=cmd(['docker','compose','ps','-aq'],cwd=p)
    if rc: result['error']='ps-ids-failed'; return result
    for cid in [x for x in out.splitlines() if x]:
        rc,s,_=cmd(['docker','inspect','-f','{{.Name}}|{{.State.Running}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}',cid])
        if rc: result['bad_containers'].append({'id':cid,'reason':'inspect-failed'}); continue
        name,running,health=s.lstrip('/').split('|',2)
        if running!='true' or health not in {'none','healthy'}: result['bad_containers'].append({'name':name,'running':running,'health':health})
    result['missing_services']=sorted(set(result['expected_services'])-set(result['actual_services']))
    return result

def main():
    ap=argparse.ArgumentParser(description='Read-only production shadow verification for RPi5-maintenance')
    ap.add_argument('--repo',default='.')
    ap.add_argument('--config',default='/etc/rpi-update.conf')
    ns=ap.parse_args(); root=Path(ns.repo).resolve()
    rc,commit,_=cmd(['git','rev-parse','HEAD'],cwd=root)
    if rc: raise SystemExit('repo HEAD unavailable')
    prov=json.loads((root/'ops/maintenance/updater-source-provenance.json').read_text())['candidate']
    source_sha=sha256(root/'ops/bin/rpi5-update')
    cfg=parse_allowlisted_config(Path(ns.config))
    user=cfg.get('UPDATE_USER','andris')
    try: home=pwd.getpwnam(user).pw_dir
    except KeyError: home=f'/home/{user}'
    main_dir=cfg.get('MAIN_COMPOSE_DIR') or f'{home}/docker'
    cv_dir=cfg.get('CV_COMPOSE_DIR') or f'{main_dir}/cv'
    installed=Path('/usr/local/sbin/rpi5-update')
    installed_sha=sha256(installed) if installed.is_file() else None
    docker_rc,_,docker_err=cmd(['docker','info'])
    result={
      'schema':1,'mode':'read-only-shadow','repo_commit':commit,
      'candidate':{'stage':prov['stage'],'sha256':source_sha,'provenance_matches':source_sha==prov['sha256']},
      'installed':{'path':str(installed),'sha256':installed_sha,'matches_candidate':installed_sha==source_sha if installed_sha else False},
      'docker':{'daemon_ok':docker_rc==0,'stderr':docker_err[-400:] if docker_rc else ''},
      'compose':{'main':compose_state(main_dir),'cv':compose_state(cv_dir)} if docker_rc==0 else {},
      'systemd':{},'reboot_required':Path('/run/reboot-required').exists(),
      'mutation_performed':False
    }
    for unit in ['docker.service','rpi5-update.timer','rpi5-update.service']:
        rc,out,_=cmd(['systemctl','is-active',unit]); result['systemd'][unit]={'active':rc==0,'state':out or 'unknown'}
    result['warnings']=[]
    if result['systemd']['rpi5-update.service']['state']=='failed':
        result['warnings'].append('rpi5-update.service-sticky-failed-state')
    if installed_sha is None:
        result['warnings'].append('installed-updater-identity-unreadable-with-current-privileges')
    result['shadow_pass']=bool(result['candidate']['provenance_matches'] and result['docker']['daemon_ok'] and all(v.get('config_ok') and not v.get('missing_services') and not v.get('bad_containers') for v in result.get('compose',{}).values()))
    print(json.dumps(result,sort_keys=True,separators=(',',':')))
    return 0 if result['shadow_pass'] else 1
if __name__=='__main__': raise SystemExit(main())
