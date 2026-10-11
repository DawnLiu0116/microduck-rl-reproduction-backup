"""Read-only episode audit; exploratory, conditional-on-fixed-model bootstrap."""
import csv
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'task_protocol_v2/four_model_final/four_model_results.json'
RAW = ROOT.parent / 'task_protocol_v2/raw_episodes_measurement'
OUT = ROOT / 'episode_uncertainty'
MODELS = ('official', 'seed42', 'seed123', 'seed2026')
SEEDS = (1001, 2002, 3003)
METRICS = {
    'Forward': ('mean_abs_vx_error_mps', 'mean_abs_vy_mps'),
    'Turning': ('mean_abs_yaw_error_radps', 'mean_planar_speed_mps'),
    'Standing': ('mean_planar_speed_mps', 'mean_abs_yaw_speed_radps'),
    'Stress-forward': ('mean_abs_vx_error_mps', 'recovered_push_fraction'),
}
DRAWS = 5000


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    data = json.loads(SOURCE.read_text(encoding='utf-8'))
    assert data['complete'] and len(data['jobs']) == 48
    arrays, checks, sources = {}, [], {str(SOURCE): digest(SOURCE)}
    keys = set()
    for job in data['jobs']:
        key = (job['model'], job['scenario'], job['seed'])
        assert key not in keys
        keys.add(key)
        # Require the exact filename referenced in the original aggregate.
        recorded = job['raw_episode_file']
        assert recorded.startswith('/mnt/c/')
        path = Path('C:/' + recorded[len('/mnt/c/'):])
        assert path.resolve().is_relative_to(ROOT.parent.resolve())
        assert path.name == f'{key[0]}_{key[1]}_{key[2]}.csv'
        sources[str(path)] = digest(path)
        with path.open(encoding='utf-8-sig', newline='') as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == job['episodes'] == 128
        assert sorted(int(r['episode']) for r in rows) == list(range(128))
        for row in rows:
            assert (row['model'], row['scenario'], int(row['seed'])) == key
            assert row['protocol_version'] == job['protocol_version']
            for name, value in row.items():
                if name in ('protocol_version', 'model', 'scenario') or value in ('True', 'False', ''):
                    continue
                assert np.isfinite(float(value)), (path, name, value)
            assert row['nan_state'] == row['out_of_terrain_bounds'] == 'False'
            assert row['survival'] in ('True', 'False')
        assert sum(r['survival'] == 'True' for r in rows) == job['survival_count']
        differences = {}
        for metric, aggregate in job.items():
            if metric not in rows[0] or not isinstance(aggregate, (float, int)):
                continue
            values = [float(r[metric]) for r in rows if r[metric] != '']
            if not values:
                continue
            actual = float(np.mean(values))
            differences[metric] = actual - aggregate
            # Aggregate was computed with float32. Numerical tolerance only,
            # never a task acceptance/equivalence threshold.
            assert np.isclose(actual, aggregate, rtol=2e-6, atol=2e-6), (key, metric, actual, aggregate)
        if job['mean_recovery_seconds'] is None:
            assert all(r['mean_recovery_seconds'] == '' for r in rows)
        for metric in METRICS[key[1]]:
            assert all(r[metric] != '' for r in rows)
            arrays[(*key, metric)] = np.array([float(r[metric]) for r in rows])
        checks.append({'model': key[0], 'scenario': key[1], 'seed': key[2],
                       'episodes': len(rows), 'survival_count': job['survival_count'],
                       'max_aggregate_absolute_difference': max(map(abs, differences.values()), default=0),
                       'recovery_missing_count': sum(r['mean_recovery_seconds'] == '' for r in rows)})
    assert keys == set(itertools.product(MODELS, METRICS, SEEDS))
    rng = np.random.default_rng(20261009)
    contrasts = []
    for scenario, metrics in METRICS.items():
        for metric in metrics:
            for a, b in itertools.combinations(MODELS, 2):
                x = np.stack([arrays[(a, scenario, s, metric)] for s in SEEDS])
                y = np.stack([arrays[(b, scenario, s, metric)] for s in SEEDS])
                delta = y.mean(axis=1) - x.mean(axis=1)
                # Match seed strata, not episodes/trajectories. Resample episodes
                # independently for each model within each selected seed stratum.
                seed_index = rng.integers(0, 3, size=(DRAWS, 3))
                ix = rng.integers(0, 128, size=(DRAWS, 3, 128))
                iy = rng.integers(0, 128, size=(DRAWS, 3, 128))
                boot = (y[seed_index[..., None], iy].mean(axis=2)
                        - x[seed_index[..., None], ix].mean(axis=2)).mean(axis=1)
                contrasts.append({'scenario': scenario, 'metric': metric, 'a': a, 'b': b,
                                  'mean_a': float(x.mean()), 'mean_b': float(y.mean()),
                                  'difference_b_minus_a': float(delta.mean()),
                                  'seed_differences': dict(zip(map(str, SEEDS), map(float, delta))),
                                  'exploratory_bootstrap95': list(map(float, np.quantile(boot, [.025, .975])))})
    limitations = [
        '仅三个评估seed；区间是固定这四个模型条件下的探索性bootstrap，不是训练随机性的置信区间。',
        '回合可能共享仿真批次；独立重采样不能建模全部批内相关，区间可能偏乐观。',
        '同seed不保证同轨迹，不做逐回合配对；不同协议不拼接回合。',
        '48项比较未作多重检验校正，不按区间是否跨零宣布发现。',
        '无预定物理等价界限，不能从小差异或区间跨零推出行为等价。',
        '传感器故障原始JSON只有job聚合，不能补造逐回合连续指标或对应区间。',
        '现有脉冲弱点已被观察；重分析不是独立holdout验证，也不是训练污染因果证据。',
    ]
    result = {'complete': True, 'jobs': len(checks), 'episodes': sum(r['episodes'] for r in checks),
              'nan_episode_count': 0, 'out_of_bounds_episode_count': 0,
              'bootstrap_draws': DRAWS, 'bootstrap_seed': 20261009,
              'checks': checks, 'contrasts': contrasts, 'limitations': limitations,
              'source_sha256': sources}
    OUT.mkdir(exist_ok=True)
    (OUT / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    selected = [r for r in contrasts if r['a'] == 'seed42' and r['b'] == 'seed123']
    lines = ['# 逐回合核验与正常任务差异', '',
             '2026-10-09。现有数据只读重分析；没有新增训练、仿真或任务合格阈值。', '',
             '## 数据完整性', '',
             f'- 48个job、6144首回合，每项128个唯一episode；NaN与出界均为0。',
             f"- 重算聚合最大绝对误差：{max(r['max_aggregate_absolute_difference'] for r in checks):.9g}；通过浮点核验。",
             '- 恢复时间空白保留为缺失，不当成0；存活不等于任务完成。', '',
             '## seed123减seed42：连续指标对照', '',
             '差值为后者减前者；误差/漂移通常越小越好，恢复比例越大越好。', '',
             '| 场景 | 指标 | seed42均值 | seed123均值 | 差值 | 探索性95%区间 |',
             '|---|---|---:|---:|---:|---|']
    for r in selected:
        lo, hi = r['exploratory_bootstrap95']
        lines.append(f"| {r['scenario']} | {r['metric']} | {r['mean_a']:.6f} | {r['mean_b']:.6f} | {r['difference_b_minus_a']:+.6f} | [{lo:+.6f}, {hi:+.6f}] |")
    lines += ['', '## 对研究主张的约束', '',
              'Forward差异较小但并非已证明等价；Turning能力存在明显差异，不能说二者完整正常行为一样。',
              'Turning目标平移命令为0：seed123角速度误差更低，但平移速度约0.1411 m/s，高于seed42的0.0257 m/s。因此转向跟踪提升伴随更大平移，不能只按yaw误差称全面更好。',
              'Forward中seed123前向误差约低0.00508 m/s，但横向速度约高0.00492 m/s；这些小而方向相反的差异不应被单一均值掩盖。',
              '已有故障协议中的脉冲存活差异，需要与正常能力分别呈现。它支持“单一正常任务指标不足以概括故障表现”的描述，不证明投毒或必然的性能-安全权衡。', '',
              '## 下一步：先补独立证据，不扩训练', '',
              '1. 设计新的评估seed作为后续确认集；在运行前保存比较对象、命令与故障设置，不能把现有seed重新命名为holdout。',
              '2. 后续故障评估保存首回合原始数据、终止原因和连续误差；停止自动重置片段混入评分。',
              '3. 不新增二元合格阈值；报告正常能力向量与故障响应向量，而非硬凑“clean等价”。',
              '4. 训练污染路线仍需独立的污染载体、同预算对照及闭环因果实验；本分析不替代它。', '',
              '## 限制', ''] + [f'- {s}' for s in limitations]
    (OUT / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'complete': True, 'jobs': len(checks), 'episodes': result['episodes'],
                      'selected_contrasts': selected}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
