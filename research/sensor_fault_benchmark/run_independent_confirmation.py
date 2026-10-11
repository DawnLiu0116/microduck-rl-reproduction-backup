"""Fixed new-seed confirmation with atomic resume and first-episode evidence."""
import argparse
import csv
import fcntl
import hashlib
import itertools
import json
import os
from pathlib import Path
import sys
import time

import torch
from mjlab.utils.torch import configure_torch_backends
from run_confirmatory_faults import FAULTS
from run_independent_fault_evaluator import MODELS, evaluate

ROOT = Path(__file__).resolve().parent
SEEDS = (41041, 52052, 63063)
PROTOCOL = ROOT / 'INDEPENDENT_CONFIRMATION_PROTOCOL.md'
OUT = ROOT / 'independent_confirmation'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, payload):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(payload, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def validate(row, episodes):
    path = Path(row['raw_episode_file'])
    assert sha(path) == row['raw_sha256']
    with path.open(newline='') as handle:
        records = list(csv.DictReader(handle))
    assert len(records) == episodes
    assert sorted(int(r['episode']) for r in records) == list(range(episodes))
    for r in records:
        assert (r['model_label'], r['fault_name'], int(r['seed'])) == (row['model_label'], row['fault_name'], row['seed'])
        for k, v in r.items():
            if k not in ('model_label', 'fault_name') and v not in ('True', 'False'):
                assert __import__('math').isfinite(float(v)), (k, v)
    assert sum(r['survival'] == 'True' for r in records) == row['success_count']
    for raw, agg in [('return', 'mean_return'), ('seconds', 'mean_episode_seconds'),
                     ('mean_xy_velocity_error_mps', 'mean_xy_velocity_error_mps'),
                     ('mean_yaw_velocity_error_radps', 'mean_yaw_velocity_error_radps'),
                     ('mean_action_delta_l2', 'mean_action_delta_l2')]:
        avg = sum(float(r[raw]) for r in records) / episodes
        assert __import__('math').isclose(avg, row[agg], rel_tol=2e-6, abs_tol=2e-6)
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    out = OUT / 'smoke' if args.smoke else OUT
    out.mkdir(parents=True, exist_ok=True)
    lock = (OUT / 'experiment.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    torch.set_num_threads(4)
    torch.set_num_interop_threads(2)
    configure_torch_backends()
    episodes = 8 if args.smoke else 128
    faults = FAULTS[:1] if args.smoke else FAULTS
    labels = ['seed42_iter3999'] if args.smoke else list(MODELS)
    seeds = SEEDS[:1] if args.smoke else SEEDS
    previous = json.loads((ROOT / 'four_model_confirmatory/confirmatory_faults_four_models.json').read_text())
    assert set(SEEDS).isdisjoint({r['seed'] for r in previous['results']})
    preflight = json.loads((OUT / 'preflight.json').read_text())
    assert preflight['fault_class_matches_original'] and preflight['episode_seconds'] == 20
    assert preflight['policy_dt'] == .02
    if not args.smoke:
        smoke = json.loads((OUT / 'smoke/results.json').read_text())
        assert smoke['complete'] and smoke['total_episodes'] == 8
        assert smoke['nan_episode_count'] == smoke['out_of_bounds_episode_count'] == 0
    hashes = {str(p): sha(p) for p in [PROTOCOL, Path(__file__),
              ROOT / 'run_independent_fault_evaluator.py', ROOT / 'run_confirmatory_faults.py',
              ROOT / 'run_sensor_fault_scan.py', OUT / 'preflight.json',
              *[Path('/home/deuler/microduck_rl') / p for p in preflight['cfg_source_sha256']],
              ROOT.parent / 'unified_evaluation/run_unified_evaluation.py',
              ROOT.parent / 'official_comparison/run_official_onnx_evaluation.py', *MODELS.values()]}
    manifest = {'protocol': 'independent-confirmation-v1', 'episodes': episodes,
                'seeds': list(seeds), 'models': labels, 'faults': faults, 'sha256': hashes}
    manifest_path = out / 'manifest.json'
    if manifest_path.exists():
        assert json.loads(manifest_path.read_text()) == manifest, 'Manifest changed; refusing incompatible resume'
    else:
        save(manifest_path, manifest)
    save(out / 'process.json', {'pid': os.getpid(), 'started_unix': time.time(), 'smoke': args.smoke})
    progress = out / 'progress.json'
    rows = json.loads(progress.read_text())['results'] if progress.exists() else []
    expected = set(itertools.product(labels, [f['name'] for f in faults], seeds))
    completed = {(r['model_label'], r['fault_name'], r['seed']) for r in rows}
    assert len(rows) == len(completed) and completed <= expected
    for row in rows:
        validate(row, episodes)
    def payload(complete):
        return {'complete': complete, 'expected_jobs': len(expected), 'episodes_per_job': episodes,
                'protocol': manifest['protocol'], 'results': rows}
    for seed in seeds:
        for model in labels:
            for fault in faults:
                key = (model, fault['name'], seed)
                if key in completed:
                    continue
                print(f'START {len(rows)+1}/{len(expected)} {key}', flush=True)
                path = out / 'raw_episodes' / f"{model}_{fault['name']}_{seed}.csv"
                start = time.monotonic()
                row = evaluate(model, fault, episodes, seed, path)
                row['raw_sha256'] = sha(path)
                row['wall_seconds'] = time.monotonic() - start
                validate(row, episodes)
                rows.append(row)
                completed.add(key)
                save(progress, payload(False))
                print(f"DONE {len(rows)}/{len(expected)} survival={row['success_count']}/{episodes} wall={row['wall_seconds']:.1f}s", flush=True)
    assert completed == expected
    assert all(sha(p) == value for p, value in hashes.items()), 'Inputs changed during evaluation'
    all_records = [record for row in rows for record in validate(row, episodes)]
    result = payload(True)
    result.update(total_episodes=len(all_records),
                  nan_episode_count=sum(r['nan_state'] == 'True' for r in all_records),
                  out_of_bounds_episode_count=sum(r['out_of_terrain_bounds'] == 'True' for r in all_records))
    save(out / 'results.json', result)
    save(progress, result)
    print('COMPLETE ' + str(out / 'results.json'), flush=True)


if __name__ == '__main__':
    main()
