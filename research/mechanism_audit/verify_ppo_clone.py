"""Zero-update official PPO clone: serialized module and paired closed-loop gate."""
import copy
import hashlib
import json
import shutil
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch
import mjlab.tasks
import mjlab_microduck.tasks
from mjlab.envs import ManagerBasedRlEnv
from mjlab.rl import RslRlVecEnvWrapper
from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
from rsl_rl.runners import OnPolicyRunner
from collect_long_teacher import RUNS

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'ppo_clone_baseline'
TASK = 'Mjlab-Velocity-Flat-MicroDuck'
DEVICE = 'cuda:0'
COMMANDS = {'Forward': [.3, 0., 0.], 'Turning': [0., 0., .5]}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def atomic_json(path, data):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


def snapshot(model):
    return {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}


def evaluate(seed, scenario, checkpoint, variant):
    cfg, agent = load_env_cfg(TASK, play=True), load_rl_cfg(TASK)
    cfg.scene.num_envs = 64
    cfg.seed = 11011
    cfg.episode_length_s = 20.
    cfg.curriculum = {}
    cfg.events['push_robot'].interval_range_s = (1000., 1001.)
    cfg.observations['actor'].enable_corruption = False
    for term in cfg.observations['actor'].terms.values():
        if 'max_angle_deg' in term.params:
            term.params['max_angle_deg'] = 0.
    command = COMMANDS[scenario]
    twist = cfg.commands['twist']
    for attr, value in zip(('lin_vel_x', 'lin_vel_y', 'ang_vel_z'), command):
        setattr(twist.ranges, attr, (value, value))
    twist.resampling_time_range = (1000., 1001.)
    for attr in ('rel_standing_envs', 'rel_forward_envs', 'rel_turn_in_place_envs', 'rel_heading_envs'):
        setattr(twist, attr, 0.)
    for name in ('head_pose', 'body_pose'):
        term = cfg.commands[name]
        term.ranges = tuple((0., 0.) for _ in term.ranges)
        term.resampling_time_range = (1000., 1001.)
        term.zero_command_prob = 1.
    env = None
    try:
        base = ManagerBasedRlEnv(cfg=cfg, device=DEVICE)
        env = RslRlVecEnvWrapper(base, clip_actions=agent.clip_actions)
        runner = (load_runner_cls(TASK) or OnPolicyRunner)(env, asdict(agent), device=DEVICE)
        runner.load(str(checkpoint), load_cfg={'actor': True}, strict=True, map_location=DEVICE)
        policy = runner.get_inference_policy(device=DEVICE)
        before = snapshot(policy)
        independent = copy.deepcopy(policy)
        actor_path = OUT / f'seed{seed}_serialized_actor.pt'
        if variant == 'original':
            torch.save(independent, actor_path)
        independent = torch.load(actor_path, weights_only=False, map_location=DEVICE).eval()
        independent_before = snapshot(independent)
        assert before.keys() == independent_before.keys()
        assert all(torch.equal(before[k], independent_before[k]) for k in before)
        obs = env.get_observations()
        initial_hash = hashlib.sha256(obs['actor'].cpu().numpy().tobytes()).hexdigest()
        active = torch.ones(64, dtype=torch.bool, device=DEVICE)
        steps = torch.zeros(64, dtype=torch.long, device=DEVICE)
        totals = {k: torch.zeros(64, device=DEVICE) for k in ('return', 'vx_error', 'vy_error', 'yaw_error', 'translation_speed')}
        causes = {k: torch.zeros(64, dtype=torch.bool, device=DEVICE) for k in ('fell_over', 'time_out', 'nan_state', 'out_of_terrain_bounds')}
        trace = hashlib.sha256()
        max_error = 0.
        max_command_error = 0.
        with torch.inference_mode():
            for frame in range(1100):
                if not bool(active.any()):
                    break
                assert obs['actor'].shape == (64, 61) and torch.isfinite(obs['actor']).all()
                actions = policy(obs)
                other = independent(obs)
                max_error = max(max_error, float((actions-other).abs().max()))
                assert actions.shape == (64, 14) and torch.isfinite(actions).all()
                assert torch.equal(actions, other), 'Serialized actor inference differs'
                actual_command = base.command_manager.get_term('twist').vel_command_b
                max_command_error = max(max_command_error, float((actual_command-torch.tensor(command, device=DEVICE)).abs().max()))
                assert max_command_error < 1e-6
                robot = base.scene['robot']
                vel = robot.data.root_link_lin_vel_b
                yaw = robot.data.root_link_ang_vel_b[:, 2]
                assert torch.isfinite(vel[active]).all() and torch.isfinite(yaw[active]).all()
                totals['vx_error'] += (vel[:, 0]-command[0]).abs()*active
                totals['vy_error'] += (vel[:, 1]-command[1]).abs()*active
                totals['yaw_error'] += (yaw-command[2]).abs()*active
                totals['translation_speed'] += vel[:, :2].norm(dim=-1)*active
                for tensor in (obs['actor'], actions, active):
                    trace.update(tensor.detach().cpu().numpy().tobytes())
                obs, reward, done, _ = env.step(actions)
                assert torch.isfinite(reward).all()
                for tensor in (reward, done):
                    trace.update(tensor.detach().cpu().numpy().tobytes())
                totals['return'] += reward*active
                steps += active.long()
                ended = done.bool() & active
                for name in causes:
                    causes[name] |= ended & base.termination_manager.get_term(name)
                active &= ~ended
        assert not bool(active.any())
        unchanged = all(torch.equal(before[k], snapshot(policy)[k]) for k in before)
        other_after = snapshot(independent)
        unchanged_independent = all(torch.equal(independent_before[k], other_after[k]) for k in independent_before)
        assert unchanged and unchanged_independent
        survive = causes['time_out'] & ~causes['fell_over'] & ~causes['nan_state'] & ~causes['out_of_terrain_bounds']
        rows = [{'env_id': i, 'steps': int(steps[i]), 'seconds': float(steps[i])*base.step_dt,
                 'survival': bool(survive[i]), **{k: bool(v[i]) for k, v in causes.items()},
                 'return': float(totals['return'][i]),
                 **{f'mean_{k}': float(v[i]/steps[i]) for k, v in totals.items() if k != 'return'}} for i in range(64)]
        return {'seed': seed, 'scenario': scenario, 'variant': variant, 'eval_seed': 11011,
                'checkpoint': str(checkpoint), 'checkpoint_sha256': sha(checkpoint),
                'architecture': str(policy.mlp), 'normalizer_eps': float(policy.obs_normalizer.eps),
                'normalizer_count': int(policy.obs_normalizer.count), 'clip_actions': agent.clip_actions,
                'state_unchanged': unchanged, 'serialized_state_unchanged': unchanged_independent,
                'serialized_actor_max_abs_error': max_error, 'max_command_error': max_command_error,
                'initial_obs_sha256': initial_hash, 'full_trace_sha256': trace.hexdigest(),
                'survival_count': int(survive.sum()), 'nan_count': int(causes['nan_state'].sum()),
                'terrain_exit_count': int(causes['out_of_terrain_bounds'].sum()),
                'mean_episode_seconds': float(np.mean([r['seconds'] for r in rows])),
                'mean_vx_error': float(np.mean([r['mean_vx_error'] for r in rows])),
                'mean_yaw_error': float(np.mean([r['mean_yaw_error'] for r in rows])), 'rows': rows}
    finally:
        if env is not None:
            env.close()


def main():
    torch.set_num_threads(2)
    OUT.mkdir(exist_ok=True)
    path = OUT / 'results.json'
    result = json.loads(path.read_text()) if path.exists() else {'complete': False, 'cases': [], 'pairs': []}
    for seed in (42, 2026):
        original = Path('/home/deuler/microduck_rl/logs/rsl_rl/velocity') / RUNS[seed] / 'model_3999.pt'
        clone = OUT / f'seed{seed}_clone_model3999.pt'
        original_hash = sha(original)
        if not clone.exists():
            shutil.copy2(original, clone)
        assert sha(clone) == original_hash
        for scenario in COMMANDS:
            for variant, checkpoint in (('original', original), ('clone', clone)):
                if any((r['seed'], r['scenario'], r['variant']) == (seed, scenario, variant) for r in result['cases']):
                    continue
                row = evaluate(seed, scenario, checkpoint, variant)
                result['cases'].append(row)
                atomic_json(path, result)
                print('CLONE_CASE '+json.dumps({k: v for k, v in row.items() if k not in ('rows', 'architecture')}), flush=True)
            pair = [next(r for r in result['cases'] if (r['seed'], r['scenario'], r['variant']) == (seed, scenario, v)) for v in ('original', 'clone')]
            checks = {'seed': seed, 'scenario': scenario,
                      'initial_observations_equal': pair[0]['initial_obs_sha256'] == pair[1]['initial_obs_sha256'],
                      'full_trace_equal': pair[0]['full_trace_sha256'] == pair[1]['full_trace_sha256'],
                      'per_episode_rows_equal': pair[0]['rows'] == pair[1]['rows']}
            result['pairs'] = [r for r in result['pairs'] if (r['seed'], r['scenario']) != (seed, scenario)] + [checks]
            assert sha(original) == original_hash == sha(clone), 'Checkpoint changed'
            atomic_json(path, result)
    assert len(result['cases']) == 8 and len(result['pairs']) == 4
    result['complete'] = True
    result['gate_passed'] = all(all(r[k] for k in ('initial_observations_equal', 'full_trace_equal', 'per_episode_rows_equal')) for r in result['pairs'])
    result['scope'] = 'Zero-update implementation equivalence; 2 training seeds, 1 evaluation seed, 2 command conditions. Not training or poisoning evidence.'
    atomic_json(path, result)
    lines = ['# Original PPO zero-update clone results', '', '| Model | Task | Original survival | Clone survival | Mean vx error | Mean yaw error | Trace equal |', '|---|---|---:|---:|---:|---:|---|']
    for pair in result['pairs']:
        cases = [r for r in result['cases'] if r['seed'] == pair['seed'] and r['scenario'] == pair['scenario']]
        a, b = cases
        lines.append(f"| {a['seed']} | {a['scenario']} | {a['survival_count']}/64 | {b['survival_count']}/64 | {a['mean_vx_error']:.6f} | {a['mean_yaw_error']:.6f} | {pair['full_trace_equal']} |")
    lines += ['', f"Strict clone gate passed: {result['gate_passed']}. Serialized actor max error: {max(r['serialized_actor_max_abs_error'] for r in result['cases'])}.", '', result['scope'], '', 'Velocity errors are m/s; yaw errors rad/s. Survival is not command success. No optimizer step, normalization update, or source checkpoint modification.']
    (OUT/'REPORT.md').write_text('\n'.join(lines))
    print('CLONE_COMPLETE '+json.dumps({'gate_passed': result['gate_passed'], 'cases': len(result['cases']), 'pairs': result['pairs']}), flush=True)


if __name__ == '__main__':
    main()
