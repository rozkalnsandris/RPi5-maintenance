#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, importlib.machinery, json, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'ops/bin/rpi5-docker-retention-report'
loader=importlib.machinery.SourceFileLoader('retention_report',str(REPORT))
spec=importlib.util.spec_from_loader('retention_report',loader)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


def load_py(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def sid(ch): return 'sha256:'+ch*64
CURRENT=sid('1'); PREV=sid('2'); CAND=sid('3'); CV=sid('4'); OLD=sid('5'); CVOLD=sid('6'); OTHER=sid('7')
CID_MAIN='a'*64; CID_CV='b'*64; CID_OTHER='c'*64

class FakeRunner:
    def __init__(self,main,cv): self.main=main; self.cv=cv
    def run(self,argv,*,cwd=None):
        t=tuple(argv); c=None if cwd is None else Path(cwd)
        if t==('docker','ps','-aq'): return f'{CID_MAIN}\n{CID_CV}\n{CID_OTHER}\n'
        if t[:2]==('docker','inspect'):
            return json.dumps([
              {'Id':CID_MAIN,'Name':'/main-web-1','Image':CURRENT},
              {'Id':CID_CV,'Name':'/cv-web-1','Image':CV},
              {'Id':CID_OTHER,'Name':'/other-1','Image':OTHER},
            ])
        if t==('docker','image','ls','--all','--no-trunc','--quiet'): return '\n'.join([CURRENT,PREV,CAND,CV,OLD,CVOLD,OTHER])+'\n'
        if t[:3]==('docker','image','inspect') and len(t)>4:
            refs={
              CURRENT:['ghcr.io/example/app@sha256:'+'a'*64], PREV:['ghcr.io/example/app@sha256:'+'b'*64], CAND:['ghcr.io/example/app:latest'],
              CV:['ghcr.io/example/cv:latest'], OLD:['ghcr.io/example/app@sha256:'+'c'*64], CVOLD:['ghcr.io/example/cv@sha256:'+'d'*64]}
            rows=[]
            for i,iid in enumerate(t[3:]):
                values=refs.get(iid,[])
                rows.append({'Id':iid,'Created':'2026-08-%02dT00:00:00Z'%(1+i),'Size':1000+i,'RepoTags':values if values and ':' in values[0] and '@' not in values[0] else [],'RepoDigests':values if values and '@' in values[0] else []})
            return json.dumps(rows)
        if t==('docker','image','inspect','ghcr.io/example/app:latest'): return json.dumps([{'Id':CAND}])
        if t==('docker','image','inspect','ghcr.io/example/cv:latest'): return json.dumps([{'Id':CV}])
        if t==('docker','compose','config','--format','json') and c==self.main:
            return json.dumps({'services':{'web':{'image':'ghcr.io/example/app:latest'},'local':{'build':'.','image':'local/build:latest'}}})
        if t==('docker','compose','config','--format','json') and c==self.cv:
            return json.dumps({'services':{'web':{'image':'ghcr.io/example/cv:latest'}}})
        if t==('docker','compose','ps','-q','web') and c==self.main: return CID_MAIN+'\n'
        if t==('docker','compose','ps','-q','web') and c==self.cv: return CID_CV+'\n'
        if t==('docker','volume','ls','-q'): return 'db_data\n'+'f'*64+'\n'
        if t[:3]==('docker','volume','inspect'):
            return json.dumps([{'Name':'db_data','Labels':{'com.docker.compose.project':'main','com.docker.compose.volume':'db'}},{'Name':'f'*64,'Labels':None}])
        if t==('docker','system','df','--format','{{json .}}'):
            return json.dumps({'Type':'Images','Size':'10GB','Reclaimable':'2GB (20%)'})+'\n'+json.dumps({'Type':'Build Cache','Size':'5.324GB','Reclaimable':'4.313GB (81%)'})+'\n'
        if t==('df','-P','/'):
            return 'Filesystem 1024-blocks Used Available Capacity Mounted on\n/dev/root 100 46 54 46% /\n'
        raise AssertionError((t,c))

with tempfile.TemporaryDirectory() as td:
    root=Path(td); main=root/'main'; cv=root/'cv'; evidence=root/'evidence'; main.mkdir(); cv.mkdir(); evidence.mkdir()
    run=evidence/'20260920_022000'; run.mkdir()
    phases=[]
    for project in ('main','cv'):
        phases += [
          {'run_id':'20260920_022000','project':project,'phase':'reconcile','command':'compose-up','outcome':'succeeded','rc':0},
          {'run_id':'20260920_022000','project':project,'phase':'final-health','command':'compose-runtime-check','outcome':'healthy','rc':0},
        ]
    (run/'phases.jsonl').write_text('\n'.join(json.dumps(x) for x in phases)+'\n')
    (run/'docker-main-images-before.tsv').write_text(f'ghcr.io/example/app:latest\t{PREV}\tv1\n')
    (run/'docker-cv-images-before.tsv').write_text(f'ghcr.io/example/cv:latest\t{CV}\tv1\n')
    raw=mod.collect_raw(FakeRunner(main,cv),[('main',main),('cv',cv)],evidence,['20260920_022000'],1789000000,14*86400,0,80,8*1024**3)
    assert raw['schema']=='rpi5-docker-runtime-inventory.v1'
    assert len(raw['managed_services'])==2
    assert raw['rollback_evidence']==[{'project':'main','service':'web','source':'v28-compose-evidence','phase':'pre-mutation','outcome':'success','image_id':PREV}]
    assert raw['policy']['root_used_percent']==46
    assert raw['build_cache']['bytes']==5324000000
    assert raw['build_cache']['reclaimable_bytes']==4313000000
    assert {x['kind'] for x in raw['volumes']}=={'named','anonymous'}
    images={x['id']:x for x in raw['images']}
    assert 'ghcr.io/example/app' in images[PREV]['repositories']
    assert 'ghcr.io/example/app' in images[CURRENT]['repositories']
    assert images[OTHER]['repositories']==[]
    inv=load_py('retention_inventory',ROOT/'ops/lib/rpi5-docker-retention-inventory.py')
    planner=load_py('retention_plan',ROOT/'ops/lib/rpi5-docker-retention-plan.py')
    plan=planner.build_plan(inv.build_inventory(raw))
    assert OLD in plan['delete_ids']
    assert CVOLD not in plan['delete_ids']
    assert plan['blocked_lineages']['ghcr.io/example/cv']==['missing-previous-known-good']
    decisions={x['id']:x for x in plan['images']}
    assert decisions[OTHER]['action']=='protect'
    assert decisions[OTHER]['role']=='container-referenced'

try:
    mod.Runner(1).run(['docker','image','prune','-a'])
except mod.ReportError as exc:
    assert 'refusing non-read-only command' in str(exc)
else:
    raise AssertionError('mutating Docker command was not rejected')

print('Docker retention read-only report collector: PASS')
