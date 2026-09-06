#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
out=subprocess.check_output(['python3','scripts/build-release-manifest.py','--repo','.','--ref',commit,'--version','0.2.0-rc.1'],cwd=ROOT,text=True)
data=json.loads(out)
assert data['schema']==1
assert data['version']=='0.2.0-rc.1'
assert data['commit']==commit
assert data['repository']=='rozkalnsandris/RPi5-maintenance'
assert data['production_activation_authorized'] is False
up=(ROOT/'ops/bin/rpi5-update').read_bytes()
assert data['updater']['sha256']==hashlib.sha256(up).hexdigest()
assert data['updater']['size_bytes']==len(up)
assert data['candidate_stage'].startswith('v28-')
print('Maintenance release manifest contract: PASS')
