"""CPU preflight for exact fault semantics and runtime provenance."""
import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess

import torch
from mjlab.tasks.registry import load_env_cfg
from run_independent_fault_evaluator import FaultInjector, TASK_ID, configure_scenario

ROOT = Path(__file__).resolve().parent
def extract(path):
    tree = ast.parse(path.read_text())
    return ast.dump(next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'FaultInjector'), include_attributes=False)
assert extract(ROOT / 'run_sensor_fault_scan.py') == extract(ROOT / 'run_independent_fault_evaluator.py')
cfg = load_env_cfg(TASK_ID, play=True)
configure_scenario(cfg, 'Forward')
assert cfg.episode_length_s == 20
step_dt = cfg.sim.mujoco.timestep * cfg.decimation
assert abs(step_dt - .02) < 1e-10
checks = {}
# A minimal mapping clone reproduces the injector's observation-container surface.
class Obs(dict):
    def clone(self):
        return Obs({k: v.clone() for k, v in self.items()})
for spec in [{'name':'delay_2', 'type':'delay', 'steps':2},
             {'name':'freeze_8', 'type':'freeze', 'duration':8, 'period':180},
             {'name':'spike_100', 'type':'spike', 'scale':1., 'duration':5, 'period':200}]:
    injector = FaultInjector(spec, 41041, torch.device('cpu'))
    changed = []
    for step in range(206):
        obs = Obs(actor=torch.full((1,61), float(step)))
        out, _ = injector.apply(obs)
        assert torch.equal(out['actor'][:,34:], obs['actor'][:,34:])
        if not torch.equal(out['actor'][:,:34], obs['actor'][:,:34]):
            changed.append(step)
        if spec['type'] == 'delay':
            assert out['actor'][0,0].item() == max(0, step-2)
    if spec['type'] == 'freeze':
        # First sample is the captured clean value; 7 subsequent frames stale.
        assert changed == list(range(181,188))
    if spec['type'] == 'spike':
        assert changed == list(range(1,5)) + list(range(200,205))
    checks[spec['name']] = {'passed':True, 'modified_steps_first_206':changed}
versions = {}
for package in ['torch', 'mjlab', 'mujoco', 'mujoco-warp', 'rsl-rl-lib', 'onnx', 'onnxruntime']:
    try: versions[package] = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError: versions[package] = None
repo = Path('/home/deuler/microduck_rl')
files = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in repo.rglob('microduck_velocity_env_cfg.py') if '.venv' not in p.parts}
payload = {'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
           'git_status':subprocess.check_output(['git','status','--short'],cwd=repo,text=True),
           'dependency_versions':versions, 'cfg_source_sha256':files,
           'episode_seconds':cfg.episode_length_s, 'policy_dt':step_dt,
           'fault_class_matches_original':True, 'injector_checks':checks}
out = ROOT / 'independent_confirmation'
out.mkdir(exist_ok=True)
(out / 'preflight.json').write_text(json.dumps(payload,indent=2)+'\n')
print(json.dumps(payload,indent=2))
