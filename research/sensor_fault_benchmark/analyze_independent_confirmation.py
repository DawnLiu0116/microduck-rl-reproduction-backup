"""Independent CSV audit and fixed-policy old/new-seed descriptive comparison."""
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'independent_confirmation'
OLD = ROOT / 'four_model_confirmatory/confirmatory_faults_four_models.json'
MODELS = ('official_alpha_walking', 'seed42_iter3999', 'seed123_iter3999', 'seed2026_iter3999')
LABELS = ('official', 'seed42', 'seed123', 'seed2026')
FAULTS = ('clean', 'delay_2', 'freeze_8', 'freeze_10', 'freeze_12', 'spike_100')
SEEDS = (41041, 52052, 63063)
AGGREGATE_MAP = {
    'return': 'mean_return', 'seconds': 'mean_episode_seconds',
    'mean_xy_velocity_error_mps': 'mean_xy_velocity_error_mps',
    'mean_yaw_velocity_error_radps': 'mean_yaw_velocity_error_radps',
    'mean_action_delta_l2': 'mean_action_delta_l2',
    'action_jump_rate_gt_1': 'action_jump_rate_gt_1',
    'max_action_abs': 'mean_max_action_abs',
    'max_pre_step_tilt_deg': 'mean_max_tilt_deg',
    'mean_sensor_perturbation_l2': 'mean_sensor_perturbation_l2',
    'max_sensor_perturbation_l2': 'mean_max_sensor_perturbation_l2',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_path(value):
    if value.startswith('/mnt/c/'):
        return Path('C:/' + value[7:])
    return Path(value)


def wilson(k, n):
    z = 1.959963984540054
    den = 1 + z*z/n
    center = (k/n + z*z/(2*n)) / den
    half = z/den * math.sqrt(k/n*(1-k/n)/n + z*z/(4*n*n))
    return [max(0., center-half), min(1., center+half)]


def draw_comparison(aggregates):
    image = Image.new('RGB', (1320, 590), 'white')
    draw = ImageDraw.Draw(image)
    def font(size): return ImageFont.truetype('C:/Windows/Fonts/arial.ttf', size)
    draw.text((35, 20), 'MicroDuck: old vs new evaluation-seed confirmation', fill='#17263c', font=font(28))
    draw.text((35, 60), 'Survival to timeout (%) - not task success; fixed policies and fault code', fill='#435268', font=font(18))
    short = ('clean', 'delay 2', 'freeze 8', 'freeze 10', 'freeze 12', 'spike')
    for panel, field, title, seeds in [(0, 'old_survival_pct', 'Old confirmation', '1001 / 2002 / 3003'),
                                      (1, 'new_survival_pct', 'New confirmation', '41041 / 52052 / 63063')]:
        left = 35 + panel * 645
        draw.text((left, 107), title, fill='#17263c', font=font(22))
        draw.text((left, 136), seeds, fill='#435268', font=font(17))
        x0, y0, width, height = left+99, 198, 83, 64
        for col, label in enumerate(short):
            draw.text((x0+col*width+width/2, 178), label, fill='#17263c', font=font(14), anchor='mm')
        for row, label in enumerate(LABELS):
            draw.text((left, y0+row*height+height/2), label, fill='#17263c', font=font(18), anchor='lm')
            for col, fault in enumerate(FAULTS):
                value = next(r[field] for r in aggregates if r['model'] == label and r['fault'] == fault)
                q = value/100
                color = tuple(round(a+(b-a)*q) for a,b in zip((247,249,252), (32,88,145)))
                box = (x0+col*width, y0+row*height, x0+(col+1)*width-3, y0+(row+1)*height-3)
                draw.rectangle(box, fill=color)
                draw.text(((box[0]+box[2])/2,(box[1]+box[3])/2), f'{value:.1f}',
                          fill='white' if q>.58 else '#17263c', font=font(21), anchor='mm')
    draw.text((35, 490), 'Each cell: 3 seeds x 128 first episodes = 384. Blue intensity: 0-100% survival.', fill='#435268', font=font(18))
    draw.text((35, 522), 'New seeds confirm a known weakness; no new attack or training-poisoning claim.', fill='#435268', font=font(18))
    draw.text((35, 554), 'Delay is additional; the legacy spike also occurs at startup steps 1-4.', fill='#435268', font=font(18))
    image.save(OUT / 'old_new_survival.png')


def main():
    result_path = OUT / 'results.json'
    result = json.loads(result_path.read_text())
    old = json.loads(OLD.read_text())
    manifest = json.loads((OUT / 'manifest.json').read_text())
    assert result['complete'] and old['complete']
    jobs = result['results']
    expected = set(itertools.product(MODELS, FAULTS, SEEDS))
    keys = [(r['model_label'], r['fault_name'], r['seed']) for r in jobs]
    assert len(keys) == len(set(keys)) == 72 and set(keys) == expected
    assert len(old['results']) == 72
    assert set(SEEDS).isdisjoint({r['seed'] for r in old['results']})
    fingerprints = {str(result_path): sha(result_path), str(OLD): sha(OLD)}
    for name, fingerprint in manifest['sha256'].items():
        if name.startswith('/mnt/c/'):
            path = local_path(name)
            assert sha(path) == fingerprint, name
            fingerprints[str(path)] = fingerprint
        # Linux model/config hashes were verified by the runner before and after.
    episode_data, residuals = {}, []
    nan_count = bounds_count = 0
    for job in jobs:
        key = (job['model_label'], job['fault_name'], job['seed'])
        path = local_path(job['raw_episode_file'])
        assert path.resolve().is_relative_to(OUT.resolve())
        assert sha(path) == job['raw_sha256']
        fingerprints[str(path)] = sha(path)
        with path.open(encoding='utf-8', newline='') as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == job['episodes'] == 128
        assert sorted(int(r['episode']) for r in rows) == list(range(128))
        for row in rows:
            assert (row['model_label'], row['fault_name'], int(row['seed'])) == key
            for flag in ('survival','fell_over','time_out','out_of_terrain_bounds','nan_state'):
                assert row[flag] in ('True','False')
            survival = row['time_out'] == 'True' and all(row[f] == 'False' for f in ('fell_over','out_of_terrain_bounds','nan_state'))
            assert (row['survival'] == 'True') == survival
            assert 0 < int(row['steps']) <= 1000
            assert math.isclose(float(row['seconds']), int(row['steps'])*.02, abs_tol=2e-6)
            for field, value in row.items():
                if field not in ('model_label','fault_name') and value not in ('True','False'):
                    assert value != '' and math.isfinite(float(value))
        assert sum(r['survival']=='True' for r in rows) == job['success_count']
        assert sum(r['fell_over']=='True' for r in rows) == job['fell_over_count']
        for flag, aggregate in [('nan_state','nan_state_rate'), ('out_of_terrain_bounds','out_of_terrain_rate')]:
            assert sum(r[flag]=='True' for r in rows)/128 == job[aggregate]
        nan_count += sum(r['nan_state']=='True' for r in rows)
        bounds_count += sum(r['out_of_terrain_bounds']=='True' for r in rows)
        for raw, aggregate in AGGREGATE_MAP.items():
            actual = sum(float(r[raw]) for r in rows)/128
            residuals.append(abs(actual-job[aggregate]))
            assert math.isclose(actual, job[aggregate], rel_tol=2e-6, abs_tol=2e-6), (key, aggregate)
        episode_data[key] = rows
    assert result['total_episodes'] == 9216
    assert nan_count == result['nan_episode_count'] and bounds_count == result['out_of_bounds_episode_count']
    aggregates = []
    rng = np.random.default_rng(20261010)
    metrics = ('seconds','mean_xy_velocity_error_mps','mean_yaw_velocity_error_radps','mean_action_delta_l2')
    for model, label in zip(MODELS, LABELS):
        for fault in FAULTS:
            old_jobs = [r for r in old['results'] if r['model_label']==model and r['fault_name']==fault]
            new_jobs = [r for r in jobs if r['model_label']==model and r['fault_name']==fault]
            assert len(old_jobs) == len(new_jobs) == 3
            old_count, new_count = sum(r['success_count'] for r in old_jobs), sum(r['success_count'] for r in new_jobs)
            values = np.array([[[float(r[m]) for m in metrics] for r in episode_data[(model,fault,s)]] for s in SEEDS])
            strata = rng.integers(0, 3, size=(2000,3))
            indices = rng.integers(0,128,size=(2000,3,128))
            boot = values[strata[...,None],indices].mean(axis=(1,2))
            interval = np.quantile(boot,[.025,.975],axis=0)
            aggregates.append({'model':label,'fault':fault,'episodes_each_cohort':384,
                               'old_survival_count':old_count,'new_survival_count':new_count,
                               'old_survival_pct':old_count/384*100,'new_survival_pct':new_count/384*100,
                               'new_minus_old_pp':(new_count-old_count)/384*100,
                               'new_pooled_wilson95':wilson(new_count,384),
                               'new_seed_survival_pct':{str(s):next(r['success_rate']*100 for r in new_jobs if r['seed']==s) for s in SEEDS},
                               'new_continuous':{m:{'mean':float(values[:,:,i].mean()),
                                                    'exploratory_cluster_bootstrap95':interval[:,i].tolist()} for i,m in enumerate(metrics)}})
    contrast = []
    for seed in SEEDS:
        a = next(r for r in jobs if r['model_label']=='seed42_iter3999' and r['fault_name']=='spike_100' and r['seed']==seed)
        b = next(r for r in jobs if r['model_label']=='seed123_iter3999' and r['fault_name']=='spike_100' and r['seed']==seed)
        contrast.append({'seed':seed,'seed42_survival_count':a['success_count'],'seed123_survival_count':b['success_count'],
                         'seed123_minus_seed42_pp':(b['success_count']-a['success_count'])/128*100})
    summary = {'complete':True,'jobs':72,'episodes':9216,'unique_jobs':72,'raw_files':72,
               'nan_episode_count':nan_count,'out_of_bounds_episode_count':bounds_count,
               'max_aggregate_absolute_residual':max(residuals),'aggregates':aggregates,
               'primary_contrast':contrast,'mean_primary_contrast_pp':sum(r['seed123_minus_seed42_pp'] for r in contrast)/3,
               'source_sha256':fingerprints,'bootstrap_draws':2000,'bootstrap_seed':20261010,
               'limits':['3 evaluation seeds, fixed policies, not training replicates.',
                         'Known fault and known weakness; new seeds are not a new attack discovery.',
                         'Pooled Wilson ignores seed/batch dependence; cluster bootstrap with 3 seeds is exploratory.',
                         'Early-terminated episode errors are measured only while alive, not comparable without lifetime.',
                         'No physical hardware or runtime safety-layer bypass demonstrated.',
                         'Original interruption cause unknown; no claim of OOM or code failure.']}
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    lines = ['# 新评估种子故障确认：完成报告','',
             '2026-10-10。仅从70项续跑最后两项，原参数与模型不变；没有新增训练。','',
             '## 完整性','',
             f'- complete=true；72个唯一job，72份CSV，9216个唯一首回合。NaN={nan_count}，出界={bounds_count}。',
             f'- 全部原始文件SHA与job记录一致，全部10种连续聚合可重算，最大绝对残差{max(residuals):.8g}。',
             '- 原运行器完成前后检查全部输入SHA；本分析独立检查Windows源文件与逐回合记录。',
             '- 最后两项：seed2026/63063 freeze_12与spike_100；原70项经核验后跳过。','',
             '## 全部模型新旧存活对照','',
             '每格384首回合；old为1001/2002/3003，new为41041/52052/63063。存活至超时不等于任务成功。','',
             '| 模型 | 故障 | old存活% | new存活% | new-old百分点 |',
             '|---|---|---:|---:|---:|']
    for r in aggregates:
        lines.append(f"| {r['model']} | {r['fault']} | {r['old_survival_pct']:.2f} | {r['new_survival_pct']:.2f} | {r['new_minus_old_pp']:+.2f} |")
    lines += ['', '## 预先指定主比较：seed123减seed42的脉冲存活差','',
              '| 新评估seed | seed42存活/128 | seed123存活/128 | 差值百分点 |','|---|---:|---:|---:|']
    for r in contrast:
        lines.append(f"| {r['seed']} | {r['seed42_survival_count']} | {r['seed123_survival_count']} | {r['seed123_minus_seed42_pp']:+.2f} |")
    lines += ['',f"平均差为{summary['mean_primary_contrast_pp']:.2f}个百分点，三个新seed方向一致。已知脉冲弱点复现，但不说明训练污染是原因。",'',
              '## 连续指标与统计说明','',
              'summary.json保存新集回合寿命、XY/yaw误差及动作变化均值与按seed分组探索性bootstrap区间。三个seed太少，且同批环境可能相关，不按区间是否跨零宣布发现。Wilson为合并回合二项描述，忽略分组依赖，不当训练总体置信度。',
              '故障下早跌倒回合会截短误差统计；误差较低可能只是较早终止，必须同时看寿命与存活。新旧是不同seed队列，不作逐回合配对，也不声称正常行为等价。','',
              '## 已确认的故障代码语义','',
              '- delay_2额外40ms，不是完整硬件延迟；freeze在phase0捕获当前值。',
              '- spike启动step1—4也触发，之后每200步持续5步；0.80是projected_gravity第一维偏移，不是躯干角。',
              '- 保持旧injector未改；故障分别运行，不是六种同时施加。','',
              '## 收尾与后续','',
              '本次补齐原定确认实验并停止扩大。上次中断原因未知，保留旧run.log；本次前台续跑的结果以最终JSON及哈希核验为准。',
              '下一步候选为通道拆分与启动/稳定行走阶段对照，需要另存协议后执行；本报告不代表已运行该机制实验。',
              '原模型、旧结果和manifest未修改；没有实体操作、上传或部署。','',
              '![新旧种子存活对照](old_new_survival.png)','']
    (OUT/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    draw_comparison(aggregates)
    assert all(sha(Path(p))==fingerprint for p,fingerprint in fingerprints.items())
    print(json.dumps({'complete':True,'jobs':72,'episodes':9216,'nan':nan_count,'bounds':bounds_count,
                      'primary_contrast_pp':summary['mean_primary_contrast_pp'],
                      'spike':[(r['model'],r['new_survival_pct']) for r in aggregates if r['fault']=='spike_100']},indent=2))


if __name__ == '__main__': main()
