#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'scripts/rpi5-maintenance-shadow-verify.py'
text=p.read_text()
assert 'mode\':\'read-only-shadow' in text.replace(' ', '')
required=['docker\',\'info','docker\',\'compose\',\'config','docker\',\'compose\',\'ps','docker\',\'inspect','systemctl\',\'is-active','/run/reboot-required','mutation_performed\':False']
compact=text.replace(' ', '')
for marker in required: assert marker in compact, marker
for forbidden in ['apt-get','docker compose pull','docker compose up','docker compose down','systemctl restart','systemctl start','systemctl stop','systemctl enable','systemctl disable','shutdown -','reboot -','rm -','unlink(','write_text(','mkdir(','install -']:
    assert forbidden not in text, forbidden
print('Maintenance shadow verifier read-only contract: PASS')
