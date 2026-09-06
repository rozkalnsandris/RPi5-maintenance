#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path

def run(root: Path, *args: str) -> str:
    return subprocess.check_output(args, cwd=root, text=True).strip()

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    ap=argparse.ArgumentParser(description='Build deterministic RPi5-maintenance release manifest')
    ap.add_argument('--repo', default='.')
    ap.add_argument('--ref', default='HEAD')
    ap.add_argument('--version', required=True)
    ns=ap.parse_args()
    root=Path(ns.repo).resolve()
    commit=run(root,'git','rev-parse',f'{ns.ref}^{{commit}}')
    tree=run(root,'git','rev-parse',f'{commit}^{{tree}}')
    updater_rel='ops/bin/rpi5-update'
    prov_rel='ops/maintenance/updater-source-provenance.json'
    updater=subprocess.check_output(['git','show',f'{commit}:{updater_rel}'],cwd=root)
    prov=json.loads(run(root,'git','show',f'{commit}:{prov_rel}'))
    candidate=prov['candidate']
    updater_blob=run(root,'git','rev-parse',f'{commit}:{updater_rel}')
    actual_sha=sha256_bytes(updater)
    if candidate['sha256'] != actual_sha or candidate['git_blob_sha1'] != updater_blob or candidate['size_bytes'] != len(updater):
        raise SystemExit('candidate provenance does not match exact release ref')
    extraction=subprocess.check_output(['git','show',f'{commit}:SOURCE_EXTRACTION_MANIFEST.txt'],cwd=root)
    manifest={
      'schema':1,'version':ns.version,'repository':'rozkalnsandris/RPi5-maintenance',
      'commit':commit,'tree':tree,'updater':{'path':updater_rel,'sha256':actual_sha,'git_blob_sha1':updater_blob,'size_bytes':len(updater)},
      'candidate_stage':candidate['stage'],'source_extraction_manifest_sha256':sha256_bytes(extraction),
      'production_activation_authorized':False
    }
    print(json.dumps(manifest,sort_keys=True,separators=(',',':')))
    return 0
if __name__=='__main__': raise SystemExit(main())
