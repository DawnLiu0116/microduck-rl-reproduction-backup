"""WSL launcher: persistent append-only stdout/stderr, no duplicate live worker."""
import json
import os
from pathlib import Path
import subprocess
import time

root = Path(__file__).resolve().parent
out = root / 'pulse_mechanism'
out.mkdir(exist_ok=True)
record = out / 'launcher.json'
if record.exists():
    pid = json.loads(record.read_text())['pid']
    try:
        cmdline = Path(f'/proc/{pid}/cmdline').read_bytes()
    except FileNotFoundError:
        cmdline = b''
    if b'run_pulse_mechanism.py' in cmdline:
        raise SystemExit(f'Worker already running: {pid}')
if (out/'results.json').exists() and json.loads((out/'results.json').read_text())['complete']:
    raise SystemExit('Already complete; refusing unnecessary rerun')
env = dict(os.environ, OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4')
with (out/'run.log').open('a', buffering=1) as log:
    log.write(f'\nLAUNCH {time.time()}\n')
    log.flush()
    process = subprocess.Popen(['/home/deuler/microduck_rl/.venv/bin/python','-u',
                                str(root/'run_pulse_mechanism.py')],
                               cwd='/home/deuler/microduck_rl',env=env,
                               stdout=log,stderr=subprocess.STDOUT,
                               stdin=subprocess.DEVNULL,start_new_session=True)
temp = record.with_suffix('.tmp')
temp.write_text(json.dumps({'pid':process.pid,'started_unix':time.time()},indent=2))
temp.replace(record)
print(f'Launched PID {process.pid}; log={out / "run.log"}')
