"""Detach only this authorized local pilot; preserve logs and refuse duplicate launches."""
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'full_width_order_pilot'
OUT.mkdir(exist_ok=True)
script=ROOT/'run_full_width_order.py'
processes=subprocess.check_output(['ps','-eo','pid,args'],text=True)
for line in processes.splitlines():
    words=line.split()
    if len(words)>2 and str(script) in words[2:]:
        print('ALREADY_RUNNING '+line.strip())
        sys.exit(0)
progress=OUT/'progress.json'
if progress.exists() and json.loads(progress.read_text()).get('complete'):
    print('ALREADY_COMPLETE')
    sys.exit(0)
with (OUT/'run.log').open('ab',buffering=0) as log:
    child=subprocess.Popen([sys.executable,'-u',str(script)],cwd='/home/deuler/microduck_rl',stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
metadata={'pid':child.pid,'script':str(script),'python':sys.executable,'log':str(OUT/'run.log'),'launched_utc':datetime.now(timezone.utc).isoformat()}
(OUT/'process.json').write_text(json.dumps(metadata,indent=2))
print(json.dumps(metadata))
