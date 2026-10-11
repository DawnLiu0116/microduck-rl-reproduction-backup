"""One background evaluator; runner lock also guards duplicate launch."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'independent_confirmation'
OUT.mkdir(exist_ok=True)
script = ROOT / 'run_independent_confirmation.py'
for line in subprocess.check_output(['ps', '-eo', 'pid,args'], text=True).splitlines():
    if str(script) in line.split()[2:]:
        raise SystemExit('ALREADY_RUNNING ' + line)
if (OUT / 'results.json').exists() and json.loads((OUT / 'results.json').read_text()).get('complete'):
    raise SystemExit('ALREADY_COMPLETE')
environment = dict(os.environ, OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4')
with (OUT / 'run.log').open('ab', buffering=0) as log:
    child = subprocess.Popen([sys.executable, '-u', str(script)], cwd='/home/deuler/microduck_rl',
                             env=environment, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print(json.dumps({'pid': child.pid, 'log': str(OUT / 'run.log')}))
