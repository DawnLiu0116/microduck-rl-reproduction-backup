"""Frozen-policy pulse decomposition; old experiment files are never edited."""
import argparse
import fcntl
import itertools
import json
import os
from pathlib import Path
import time

import torch
import run_independent_fault_evaluator as evaluator
from run_independent_confirmation import sha, save, validate

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'pulse_mechanism'
LABELS = ['seed42_iter3999', 'seed123_iter3999']
SEEDS = [41041, 52052]
NAMES = ['clean', 'legacy_all', 'startup4_all', 'startup5_all', 'walking_all',
         'walking_gyro', 'walking_gravity_add', 'walking_joint_velocity',
         'walking_gravity_direction', 'walking_gravity_norm']


def triggered(name, step):
    if name == 'clean':
        return False
    if name == 'legacy_all':
        return step > 0 and step % 200 < 5
    if name.startswith('startup'):
        return 1 <= step <= (4 if name == 'startup4_all' else 5)
    return step >= 200 and step % 200 < 5


class PulseInjector:
    def __init__(self, spec, seed, device):
        self.name = spec['name']
        self.step = 0

    def apply(self, observations):
        clean = observations['actor']
        assert clean.shape[-1] == 61
        actor = clean.clone()
        name = self.name
        if triggered(name, self.step):
            all_channels = name.endswith('_all')
            if all_channels or name == 'walking_gyro':
                actor[:, :3] += actor.new_tensor([12., -16., 24.])
            if all_channels or name == 'walking_gravity_add':
                actor[:, 3:6] += actor.new_tensor([.8, 0., 0.])
            if all_channels or name == 'walking_joint_velocity':
                actor[:, 20:34] += actor.new_tensor([8,-10,7,-8,10,-7,6,-6,8,-8,5,-5,7,-7])
            if name in ('walking_gravity_direction', 'walking_gravity_norm'):
                g = clean[:, 3:6]
                v = g + g.new_tensor([.8, 0., 0.])
                ng = g.norm(dim=-1, keepdim=True)
                nv = v.norm(dim=-1, keepdim=True)
                assert (ng > 1e-8).all() and (nv > 1e-8).all()
                actor[:, 3:6] = v / nv * ng if name.endswith('direction') else g / ng * nv
        assert torch.equal(actor[:, 34:], clean[:, 34:])
        assert torch.isfinite(actor).all()
        output = observations.clone()
        output['actor'] = actor
        self.step += 1
        return output, (actor[:, :34] - clean[:, :34]).norm(dim=-1)


def unit_tests():
    from tensordict import TensorDict
    x = torch.zeros(2, 61)
    x[:, 5] = -1
    x[:, 34:] = torch.arange(27)
    obs = TensorDict({'actor': x}, batch_size=[2])
    for name in NAMES:
        inj = PulseInjector({'name': name}, 0, 'cpu')
        inj.step = 200
        y, _ = inj.apply(obs)
        assert torch.equal(y['actor'][:, 34:], x[:, 34:])
        assert torch.equal(obs['actor'], x)
        if name == 'walking_gravity_direction':
            assert torch.allclose(y['actor'][:, 3:6].norm(dim=-1), torch.ones(2))
        if name == 'walking_gravity_norm':
            assert torch.allclose(y['actor'][:, 3:6].norm(dim=-1), torch.full((2,), 1.28062485))
    assert [s for s in range(206) if triggered('legacy_all', s)] == [1,2,3,4,200,201,202,203,204]
    assert [s for s in range(206) if triggered('startup5_all', s)] == [1,2,3,4,5]
    assert [s for s in range(206) if triggered('walking_all', s)] == [200,201,202,203,204]
    old = evaluator.FaultInjector({'name':'spike_100','type':'spike','scale':1.,'period':200,'duration':5},0,torch.device('cpu'))
    new = PulseInjector({'name':'legacy_all'},0,'cpu')
    for _ in range(406):
        a, p = old.apply(obs)
        b, q = new.apply(obs)
        assert torch.equal(a['actor'], b['actor']) and torch.equal(p,q)
    print('UNIT TESTS PASS: legacy equivalence, timing, fields, gravity decomposition', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--unit-only', action='store_true')
    args = parser.parse_args()
    unit_tests()
    if args.unit_only:
        return
    OUT.mkdir(parents=True, exist_ok=True)
    lock = (OUT / 'experiment.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    out = OUT / 'smoke' if args.smoke else OUT
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    torch.set_num_interop_threads(2)
    evaluator.configure_torch_backends()
    labels = LABELS[:1] if args.smoke else LABELS
    seeds = SEEDS[:1] if args.smoke else SEEDS
    names = ['clean', 'legacy_all'] if args.smoke else NAMES
    episodes = 8 if args.smoke else 64
    if not args.smoke:
        smoke = json.loads((OUT / 'smoke/results.json').read_text())
        assert smoke['complete'] and smoke['nan_episode_count'] == smoke['out_of_bounds_episode_count'] == 0
    preflight = json.loads((ROOT / 'independent_confirmation/preflight.json').read_text())
    paths = [Path(__file__), ROOT/'PULSE_MECHANISM_PROTOCOL.md',
             ROOT/'run_independent_fault_evaluator.py', ROOT/'run_independent_confirmation.py',
             ROOT.parent/'unified_evaluation/run_unified_evaluation.py',
             ROOT.parent/'official_comparison/run_official_onnx_evaluation.py',
             *[evaluator.MODELS[k] for k in labels],
             *[Path('/home/deuler/microduck_rl')/p for p in preflight['cfg_source_sha256']]]
    manifest = {'protocol':'pulse-mechanism-v1','labels':labels,'seeds':seeds,'names':names,
                'episodes':episodes,'sha256':{str(p):sha(p) for p in paths},
                'trigger_steps_20s':{n:[s for s in range(1000) if triggered(n,s)] for n in names}}
    if (out/'manifest.json').exists():
        assert json.loads((out/'manifest.json').read_text()) == manifest, 'Incompatible resume'
    else:
        save(out/'manifest.json',manifest)
    save(out/'process.json',{'pid':os.getpid(),'started_unix':time.time(),'smoke':args.smoke})
    progress = out/'progress.json'
    rows = json.loads(progress.read_text())['results'] if progress.exists() else []
    expected = set(itertools.product(labels,names,seeds))
    keys = {(r['model_label'],r['fault_name'],r['seed']) for r in rows}
    assert len(keys) == len(rows) and keys <= expected
    for row in rows:
        validate(row,episodes)
    evaluator.FaultInjector = PulseInjector
    def payload(complete):
        return {'complete':complete,'protocol':manifest['protocol'],'expected_jobs':len(expected),
                'episodes_per_job':episodes,'results':rows}
    for seed in seeds:
        for label in labels:
            for name in names:
                if (label,name,seed) in keys:
                    continue
                print(f'START {len(rows)+1}/{len(expected)} {label} {name} {seed}',flush=True)
                start = time.monotonic()
                row = evaluator.evaluate(label,{'name':name,'type':'pulse_decomposition','severity':'original_amplitude'},episodes,seed,
                                         out/'raw_episodes'/f'{label}_{name}_{seed}.csv')
                row.update(raw_sha256=sha(row['raw_episode_file']),wall_seconds=time.monotonic()-start)
                validate(row,episodes)
                rows.append(row)
                keys.add((label,name,seed))
                save(progress,payload(False))
                print(f"DONE {len(rows)}/{len(expected)} survival={row['success_count']}/{episodes}",flush=True)
    assert keys == expected
    assert all(sha(p)==h for p,h in manifest['sha256'].items())
    result = payload(True)
    records = [r for row in rows for r in validate(row,episodes)]
    result.update(total_episodes=len(records),nan_episode_count=sum(r['nan_state']=='True' for r in records),
                  out_of_bounds_episode_count=sum(r['out_of_terrain_bounds']=='True' for r in records))
    save(out/'results.json',result)
    save(progress,result)
    print('COMPLETE',flush=True)


if __name__ == '__main__':
    main()
