#!/usr/bin/env python3
from __future__ import annotations
import os, subprocess, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OP=ROOT/'ops/bin/rpi5-maintenance-v28-activate'
LOCK=ROOT/'ops/lib/rpi5-maintenance-locks.sh'

def bash(script: str, *args: object, env: dict[str,str]|None=None) -> None:
    e=os.environ.copy(); e.update(env or {})
    p=subprocess.run(['bash','-c',script,'bash',*map(str,args)],cwd=ROOT,env=e,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert p.returncode==0,f'rc={p.returncode}\nstdout={p.stdout}\nstderr={p.stderr}'

with tempfile.TemporaryDirectory(prefix='rpi5-v28-activation-') as td:
    tmp=Path(td)
    bash(r'''
source "$1"
source "$2"
r="$3"; mkdir -p "$r"; u="$r/u"; b="$r/b"; s="$r/s"; : >"$u"; : >"$b"; : >"$s"
acquire_quiescent_one updater "$u" QUIESCENT_UPDATE_FD
acquire_quiescent_one backup "$b" QUIESCENT_BACKUP_FD
acquire_quiescent_one shared "$s" QUIESCENT_SHARED_FD
[[ -n "$QUIESCENT_UPDATE_FD" && -n "$QUIESCENT_BACKUP_FD" && -n "$QUIESCENT_SHARED_FD" ]]
set +e
flock -xn -E 200 "$u" true; a=$?
flock -xn -E 200 "$b" true; bb=$?
flock -xn -E 200 "$s" true; c=$?
set -e
[[ $a -eq 200 && $bb -eq 200 && $c -eq 200 ]]
release_quiescent_window
flock -xn -E 200 "$u" true
flock -xn -E 200 "$b" true
flock -xn -E 200 "$s" true
''',LOCK,OP,tmp/'locks')

    apt=tmp/'apt'; apt.mkdir(); (apt/'index').write_text('cached\n',encoding='utf-8')
    good=tmp/'good'; good.write_text("#!/usr/bin/env bash\n[[ ${1:-} == --check ]] || exit 2\necho '--check: APT repozitoriju metadata netiks refreshēta'\n",encoding='utf-8'); good.chmod(0o755)
    mutate=tmp/'mutate'; mutate.write_text("#!/usr/bin/env bash\n[[ ${1:-} == --check ]] || exit 2\necho changed >> \"$FAKE_APT_ROOT/index\"\necho '--check: APT repozitoriju metadata netiks refreshēta'\n",encoding='utf-8'); mutate.chmod(0o755)
    refresh=tmp/'refresh'; refresh.write_text("#!/usr/bin/env bash\n[[ ${1:-} == --check ]] || exit 2\necho '--check: APT repozitoriju metadata netiks refreshēta'\necho 'APT repozitoriju metadatu atjaunināšana...'\n",encoding='utf-8'); refresh.chmod(0o755)
    bash(r'''
source "$1"
good="$2"; mutate="$3"; refresh="$4"; apt="$5"; logs="$6"
verify_v28_check "$good" "$logs/good.log" "$apt"
[[ -n "$V28_APT_BEFORE" && "$V28_APT_BEFORE" == "$V28_APT_AFTER" ]]
set +e
verify_v28_check "$mutate" "$logs/mutate.log" "$apt"; m=$?
verify_v28_check "$refresh" "$logs/refresh.log" "$apt"; r=$?
set -e
[[ $m -ne 0 && $r -ne 0 ]]
''',OP,good,mutate,refresh,apt,tmp,env={'FAKE_APT_ROOT':str(apt)})

print('Maintenance V28 activation dynamic transaction tests: PASS')
