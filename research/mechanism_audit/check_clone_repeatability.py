"""Post-gate diagnostic: native source/source repeat versus source/clone."""
import json
import importlib.metadata
import subprocess
from pathlib import Path
import numpy as np
import torch
from verify_ppo_clone import OUT, evaluate, atomic_json, sha


def compare(a, b):
    fields = ('seconds', 'return', 'mean_vx_error', 'mean_vy_error', 'mean_yaw_error', 'mean_translation_speed')
    return {'initial_observations_equal': a['initial_obs_sha256'] == b['initial_obs_sha256'],
            'full_trace_equal': a['full_trace_sha256'] == b['full_trace_sha256'],
            'survival_count_difference': b['survival_count']-a['survival_count'],
            'survival_disagreements': sum(x['survival'] != y['survival'] for x, y in zip(a['rows'], b['rows'])),
            'metrics': {k: {'mean_signed_difference': float(np.mean([y[k]-x[k] for x, y in zip(a['rows'], b['rows'])])),
                            'mean_absolute_paired_difference': float(np.mean([abs(y[k]-x[k]) for x, y in zip(a['rows'], b['rows'])])),
                            'max_absolute_paired_difference': max(abs(y[k]-x[k]) for x, y in zip(a['rows'], b['rows']))} for k in fields}}


def main():
    torch.set_num_threads(2)
    result = json.loads((OUT/'results.json').read_text())
    assert result['complete']
    path = OUT/'repeatability.json'
    audit = json.loads(path.read_text()) if path.exists() else {'complete': False, 'cases': [], 'comparisons': []}
    for seed in (42, 2026):
        a = next(r for r in result['cases'] if (r['seed'], r['scenario'], r['variant']) == (seed, 'Forward', 'original'))
        b = next(r for r in result['cases'] if (r['seed'], r['scenario'], r['variant']) == (seed, 'Forward', 'clone'))
        if not any(r['seed'] == seed for r in audit['cases']):
            assert sha(a['checkpoint']) == a['checkpoint_sha256']
            repeat = evaluate(seed, 'Forward', Path(a['checkpoint']), 'repeat_original')
            audit['cases'].append(repeat)
            atomic_json(path, audit)
        repeat = next(r for r in audit['cases'] if r['seed'] == seed)
        row = {'seed': seed, 'original_vs_clone': compare(a, b), 'original_vs_original_repeat': compare(a, repeat)}
        audit['comparisons'] = [r for r in audit['comparisons'] if r['seed'] != seed] + [row]
        atomic_json(path, audit)
        print('REPEATABILITY '+json.dumps(row), flush=True)
    audit['complete'] = True
    audit['scope'] = 'One extra original-policy Forward repeat per model; descriptive simulator repeatability, not a significance test or relaxed clone gate.'
    audit['numeric_serialization_gate_passed'] = all(r['serialized_actor_max_abs_error'] == 0 and r['state_unchanged'] and r['serialized_state_unchanged'] for r in result['cases']+audit['cases'])
    audit['strict_trajectory_gate_passed'] = result['gate_passed']
    audit['provenance'] = {'repository_commit': subprocess.check_output(['git', '-C', '/home/deuler/microduck_rl', 'rev-parse', 'HEAD'], text=True).strip(),
                           'versions': {name: importlib.metadata.version(name) for name in ('torch', 'mjlab', 'rsl-rl-lib', 'mujoco', 'warp-lang')},
                           'script_sha256': {name: sha(OUT.parent/name) for name in ('verify_ppo_clone.py', 'check_clone_repeatability.py', 'PPO_CLONE_PROTOCOL.md')}}
    atomic_json(path, audit)
    lines = ['# 零更新 PPO 克隆与仿真重复性核验', '', '## 实测结果', '', '| PPO seed | 场景 | 原模型存活 | 克隆存活 | 原/克隆逐位轨迹相同 |', '|---|---|---:|---:|---|']
    for pair in result['pairs']:
        a = next(r for r in result['cases'] if (r['seed'], r['scenario'], r['variant']) == (pair['seed'], pair['scenario'], 'original'))
        b = next(r for r in result['cases'] if (r['seed'], r['scenario'], r['variant']) == (pair['seed'], pair['scenario'], 'clone'))
        lines.append(f"| {a['seed']} | {a['scenario']} | {a['survival_count']}/64 | {b['survival_count']}/64 | {pair['full_trace_equal']} |")
    lines += ['', '两份完整 checkpoint 文件字节一致。官方 runner 加载原模型/克隆，并与独立序列化的同结构 actor 在每一帧同一观测上比较，动作最大绝对误差均为0。归一化 eps=0.01，均值、方差、std、count 与所有 actor 参数均未更新。', '', '## 严格门槛与重复运行', '', f"原先预声明的逐位闭环门槛通过：{result['gate_passed']}。不因看到结果而修改门槛。", '']
    for row in audit['comparisons']:
        c, r = row['original_vs_clone'], row['original_vs_original_repeat']
        lines.append(f"- seed {row['seed']}：原/克隆轨迹相同={c['full_trace_equal']}；原/原重复轨迹相同={r['full_trace_equal']}；前向误差逐回合差值绝对均值分别为 {c['metrics']['mean_vx_error']['mean_absolute_paired_difference']:.6f}/{r['metrics']['mean_vx_error']['mean_absolute_paired_difference']:.6f} m/s。")
    lines += ['', '不能把独立仿真不完全相同直接归因于克隆错误。如果原模型自身重复也不同，则严格逐位复现实验的前提本身未满足；具体数值非确定性来源仍未定位。本轮没有调整 PPO 权重、没有重训、没有加入故障。', '', '## 决策', '', '克隆文件/模型状态/同观测数值一致性已单独核验。闭环严格门槛与数值门槛必须分开报告。后续沿用本轮已经完成的同观测影子 actor 检查，并针对训练干预预先确定任务级差异预算与重复评估协议；不能事后用宽松门槛把本次严格失败改称通过。Turning 存活不代表转向质量；完整跟踪指标及逐回合数据见 results.json。', '', '## 证据范围', '', '2个训练seed、1个评估seed、Forward/Turning各64个首回合，原/克隆共512回合；额外原模型Forward重复128回合，共640回合。没有验证投毒或新的防御机制，没有操作实体机器人。']
    (OUT/'REPORT_ZH.md').write_text('\n'.join(lines))
    inventory = [{'file': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'artifact_inventory.json']
    atomic_json(OUT/'artifact_inventory.json', {'files': inventory})
    print('REPEATABILITY_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
