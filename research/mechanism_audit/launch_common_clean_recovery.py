"""Launch one bounded clean-tail experiment and retain a resumable log."""
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'full_width_clean_recovery'
OUT.mkdir(exist_ok=True)
script=ROOT/'run_common_clean_recovery.py'
for line in subprocess.check_output(['ps','-eo','pid,args'],text=True).splitlines():
    words=line.split()
    if len(words)>2 and any(str(ROOT/name) in words[2:] for name in ('run_common_clean_recovery.py','run_full_width_order.py')):
        print('EXPERIMENT_ALREADY_RUNNING '+line.strip());sys.exit(0)
if (OUT/'progress.json').exists() and json.loads((OUT/'progress.json').read_text()).get('complete'):
    print('ALREADY_COMPLETE');sys.exit(0)
with (OUT/'run.log').open('ab',buffering=0) as log:
    child=subprocess.Popen([sys.executable,'-u',str(script)],cwd='/home/deuler/microduck_rl',stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
metadata={'pid':child.pid,'script':str(script),'python':sys.executable,'launched_utc':datetime.now(timezone.utc).isoformat()}
(OUT/'process.json').write_text(json.dumps(metadata,indent=2));print(json.dumps(metadata))
