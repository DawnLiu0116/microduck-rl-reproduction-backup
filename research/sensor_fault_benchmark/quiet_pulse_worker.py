"""Throttle only the verified pulse worker; do not modify experiment inputs.

Two seconds running / three seconds resting. Results and simulated time remain
unchanged; wall time increases. SIGCONT is guaranteed on controller exit.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent / 'pulse_mechanism'


def identity(pid):
    try:
        command = Path(f'/proc/{pid}/cmdline').read_bytes()
        stat = Path(f'/proc/{pid}/stat').read_text().split(') ', 1)[1].split()
    except FileNotFoundError:
        return None
    if b'run_pulse_mechanism.py' not in command or stat[0] == 'Z':
        return None
    return stat[19]  # /proc field 22: process start time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pid', type=int)
    parser.add_argument('--controller', action='store_true')
    args = parser.parse_args()
    token = identity(args.pid)
    if token is None:
        raise SystemExit('Verified experiment worker is not running')
    state = OUT / 'quiet_controller.json'
    if not args.controller:
        if state.exists():
            previous = json.loads(state.read_text())
            try:
                command = Path(f"/proc/{previous['controller_pid']}/cmdline").read_bytes()
            except FileNotFoundError:
                command = b''
            if b'quiet_pulse_worker.py' in command:
                raise SystemExit('Quiet controller already running')
        with (OUT / 'quiet_controller.log').open('a') as log:
            worker = subprocess.Popen([sys.executable, '-u', str(Path(__file__).resolve()),
                                       str(args.pid), '--controller'],
                                      stdout=log, stderr=subprocess.STDOUT,
                                      stdin=subprocess.DEVNULL, start_new_session=True)
        print(f'Quiet controller launched: {worker.pid}; target={args.pid}')
        return
    def end(signum, frame):
        raise SystemExit(f'Controller signal {signum}')
    signal.signal(signal.SIGTERM, end)
    signal.signal(signal.SIGINT, end)
    os.setpriority(os.PRIO_PROCESS, args.pid, 15)
    payload = {'controller_pid': os.getpid(), 'target_pid': args.pid,
               'target_start_ticks': token, 'active_seconds': 2,
               'rest_seconds': 3, 'started_unix': time.time(), 'active': True,
               'experiment_inputs_modified': False}
    state.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload), flush=True)
    try:
        while identity(args.pid) == token:
            os.kill(args.pid, signal.SIGCONT)
            time.sleep(2)
            if identity(args.pid) != token:
                break
            os.kill(args.pid, signal.SIGSTOP)
            time.sleep(3)
    finally:
        if identity(args.pid) == token:
            os.kill(args.pid, signal.SIGCONT)
        payload.update(active=False, ended_unix=time.time())
        state.write_text(json.dumps(payload, indent=2))
        print('Controller finished; surviving worker resumed', flush=True)


if __name__ == '__main__':
    main()
