"""Post-hoc descriptive reanalysis of existing JSON; no new task thresholds."""
import hashlib
import json
from pathlib import Path
import itertools
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'acceptance_separation'
FAULT=ROOT.parent/'sensor_fault_benchmark/four_model_confirmatory/confirmatory_faults_four_models.json'
TASK=ROOT.parent/'task_protocol_v2/four_model_final/four_model_results.json'
MAP={'official_alpha_walking':'official','seed42_iter3999':'seed42','seed123_iter3999':'seed123','seed2026_iter3999':'seed2026'}
SEEDS=(1001,2002,3003)
FAULTS=('clean','delay_2','freeze_8','freeze_10','freeze_12','spike_100')


def mean(rows,key):return float(np.mean([r[key] for r in rows]))


def main():
    OUT.mkdir(exist_ok=True)
    f=json.loads(FAULT.read_text());t=json.loads(TASK.read_text())
    assert f['complete'] and t['complete']
    fr=f['results'];tr=t['jobs']
    assert len(fr)==len({(r['model_label'],r['fault_name'],r['seed']) for r in fr})==72
    assert len(tr)==len({(r['model'],r['scenario'],r['seed']) for r in tr})==48
    assert all(r['episodes']==128 and r['nan_state_rate']==r['out_of_terrain_rate']==0 for r in fr)
    assert t['nan_episode_count']==t['out_of_bounds_episode_count']==0
    lookup={(MAP[r['model_label']],r['fault_name'],r['seed']):r for r in fr}
    nominal={(r['model'],r['scenario'],r['seed']):r for r in tr}
    aggregated=[]
    for source,model in MAP.items():
        clean=[lookup[(model,'clean',s)] for s in SEEDS]
        by_fault={}
        for fault in FAULTS:
            jobs=[lookup[(model,fault,s)] for s in SEEDS]
            by_fault[fault]={'survival_count':sum(r['success_count'] for r in jobs),'episodes':384,
                            'survival_pct':sum(r['success_count'] for r in jobs)/384*100,
                            'seed_survival_pct':[r['success_rate']*100 for r in jobs],
                            'mean_xy_error':mean(jobs,'mean_xy_velocity_error_mps')}
        tasks={}
        for scenario in ('Forward','Turning','Standing','Stress-forward'):
            jobs=[nominal[(model,scenario,s)] for s in SEEDS]
            keys=('mean_abs_vx_error_mps','mean_abs_vy_mps','mean_abs_yaw_error_radps','mean_planar_speed_mps')
            tasks[scenario]={k:mean(jobs,k) for k in keys}
            tasks[scenario]['survival_pct']=sum(r['survival_count'] for r in jobs)/384*100
        aggregated.append({'model':model,'clean_return':mean(clean,'mean_return'),
                           'clean_xy_error':mean(clean,'mean_xy_velocity_error_mps'),
                           'clean_yaw_error':mean(clean,'mean_yaw_velocity_error_radps'),
                           'faults':by_fault,'tasks':tasks})
    contrasts=[]
    for a,b in itertools.combinations(MAP.values(),2):
        for fault in FAULTS[1:]:
            paired=[]
            for seed in SEEDS:
                ca,cb=lookup[(a,'clean',seed)],lookup[(b,'clean',seed)]
                fa,fb=lookup[(a,fault,seed)],lookup[(b,fault,seed)]
                paired.append({'seed':seed,'clean_return_b_minus_a':cb['mean_return']-ca['mean_return'],
                               'clean_xy_error_b_minus_a':cb['mean_xy_velocity_error_mps']-ca['mean_xy_velocity_error_mps'],
                               'survival_b_minus_a_pp':(fb['success_rate']-fa['success_rate'])*100})
            contrasts.append({'a':a,'b':b,'fault':fault,'by_eval_seed':paired,
                              'mean_survival_difference_pp':mean(paired,'survival_b_minus_a_pp'),
                              'min_survival_difference_pp':min(r['survival_b_minus_a_pp'] for r in paired),
                              'max_survival_difference_pp':max(r['survival_b_minus_a_pp'] for r in paired)})
    result={'complete':True,'fault_jobs':72,'task_jobs':48,'aggregated':aggregated,'contrasts':contrasts,
            'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (FAULT,TASK)},
            'scope':'Exploratory descriptive analysis, no pass/fail thresholds or equivalence claim.',
            'limits':['Three evaluation seeds are not independent training replicates for each model.',
                      'Matched evaluation seeds do not establish identical physical trajectories or episode-level pairing.',
                      'Fault file has per-job aggregates only, not raw episode metrics.',
                      'Task-protocol measurements are a separate experiment; no cross-file episode joining.',
                      'Official policy training provenance differs; not matched-budget training.',
                      'delay_2 is additional injected delay, not exact end-to-end latency.',
                      'Known spike weakness is not new, and observed-data reuse is not holdout validation.']}
    (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    table='\n'.join(f"| {r['model']} | {r['clean_return']:.3f} | {r['clean_xy_error']:.4f} | "+' | '.join(f"{r['faults'][k]['survival_pct']:.2f}%" for k in FAULTS)+' |' for r in aggregated)
    task_table='\n'.join(f"| {r['model']} | {r['tasks']['Forward']['mean_abs_vx_error_mps']:.4f} | {r['tasks']['Forward']['mean_abs_vy_mps']:.4f} | {r['tasks']['Turning']['mean_abs_yaw_error_radps']:.4f} | {r['tasks']['Standing']['mean_planar_speed_mps']:.4f} |" for r in aggregated)
    selected=next(r for r in contrasts if r['a']=='seed42' and r['b']=='seed123' and r['fault']=='spike_100')
    report=f'''# 正常验收与故障安全是否分离：现有证据重分析

2026-10-09。只读两份最终JSON：72个传感器故障job（9216首回合）与48个任务协议job（6144首回合）。不是新仿真、不合并不同实验的回合、不重新定义任务成功阈值。

## 结论

**仅看clean存活或总回报，确实不足以描述故障鲁棒性；但还不能宣称模型完整正常行为等价。** 已知seed123脉冲弱点跨三个评估seed存在，不是本次发现的新攻击。常规任务误差也提供模型差异，必须与回报/存活一起看。

## 最可靠的比较：同一传感器协议内部

固定Forward=(0.3,0,0)、无推扰、20秒、3评估seed×128首回合，干净与各故障分支使用相同的评估程序。表内success实际为存活至超时且无fall/nan/out，不是速度任务完成率。

| 模型 | clean回报 | clean XY误差(m/s) | clean存活 | delay_2 | freeze_8 | freeze_10 | freeze_12 | spike_100 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{table}

seed123减seed42，spike存活率平均差为{selected['mean_survival_difference_pp']:.2f}个百分点；三个评估seed差值范围为[{selected['min_survival_difference_pp']:.2f}, {selected['max_survival_difference_pp']:.2f}]个百分点。完整种子级对比见results.json。没有把384回合当成384个独立训练模型。

故障是额外注入到actor传感器[0:34]的延迟/冻结/脉冲；历史动作与命令不变。delay_2的40ms是额外延迟，原生观测仍有自身延迟。脉冲幅度沿用旧协议，非实测硬件故障分布。

## 不可忽略的正常任务差异

下表来自另一份20秒任务协议2.1，仅用于显示Forward/Turning/Standing的任务维度，不能与故障数据逐回合配对。

| 模型 | Forward vx误差(m/s) | Forward横向速度(m/s) | Turning yaw误差(rad/s) | Standing平面速度(m/s) |
|---|---:|---:|---:|---:|
{task_table}

Turning目标yaw=0.6rad/s。必须看yaw跟踪，不能因为存活就说转向表现相同。没有设置新的“合格/不合格”界限，也没有以p>0.05冒充等价证明。

具体关系：seed123较seed42的Turning yaw误差更低，freeze_10/12存活更高，但spike存活明显更低；因此不能简单说seed123是低性能坏模型。它呈现故障类型依赖的强弱。此现象值得保留，但尚未证明训练奖励、数据覆盖或其他因素造成了这种分化，也不是已证明的不可避免安全权衡。

## 有价值但有限的研究结论

- 支持：clean存活100%并不保证额外传感器故障下仍存活；clean回报排名不能直接当鲁棒性排名。
- 不支持：所有常规任务等价；隐蔽投毒；某个训练顺序/归一化因素导致这个弱点。
- 不支持：目前canary已在独立holdout上证明降低错误放行。现有脉冲是已知弱点，不能同时用它选规则并把同一数据当独立验证。
- 模型数量只有3个本地训练seed和1个训练背景不同的官方参考，不能泛化为训练seed分布上的显著性。

## 下一步：先补分析证据，不新增训练

1. 保留任务级连续指标，不冻结二值成功阈值；明确验收究竟承诺Forward、Turning还是全部任务。
2. 列出“常规指标已可看出差异”和“只有故障才明显分离”的模型对，先不要宣称前者隐蔽。
3. 若设计canary，development与holdout故障/种子必须分开，新增逐回合记录；当前故障JSON只有job聚合，不能补造个体分布和区间。
4. 在至少更多独立训练模型上验证验收能力之前，定位为基准/验收研究候选，不给CCF录用概率，也不新增训练预算。

## 文件

- `../analyze_acceptance_separation.py`：CPU分析脚本。
- `results.json`：模型汇总、30个模型对×故障对比、种子级差值、输入SHA和限制。
- `clean_vs_fault.png`：正常回报/XY误差与脉冲存活的关系，误差棒为3个评估seed范围而非置信区间。
- `fault_fingerprints.png`：同一协议的5类故障存活指纹，避免只盯单一脉冲。

旧报告、模型与原始结果均未改动。该分析是事后探索，不伪装预注册或新确认实验。
'''
    (OUT/'REPORT.md').write_text(report)
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for r in aggregated:
        y=r['faults']['spike_100']['survival_pct'];ys=r['faults']['spike_100']['seed_survival_pct']
        for ax,key in zip(axes,('clean_return','clean_xy_error')):
            ax.errorbar(r[key],y,yerr=[[y-min(ys)],[max(ys)-y]],fmt='o',capsize=4)
            ax.annotate(r['model'],(r[key],y),xytext=(4,5),textcoords='offset points',fontsize=8)
    axes[0].set_xlabel('Clean return (same fault protocol)');axes[1].set_xlabel('Clean XY velocity error (m/s)')
    for ax in axes:ax.set_ylabel('Spike survival (%)');ax.set_ylim(0,108);ax.grid(alpha=.2);ax.margins(x=.23)
    fig.suptitle('Existing evidence; seed ranges, not CI or normal-task equivalence')
    fig.tight_layout();fig.savefig(OUT/'clean_vs_fault.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,3.5))
    values=np.array([[r['faults'][fault]['survival_pct'] for fault in FAULTS[1:]] for r in aggregated])
    image=ax.imshow(values,vmin=0,vmax=100,cmap='viridis',aspect='auto')
    ax.set_xticks(range(5),FAULTS[1:]);ax.set_yticks(range(4),[r['model'] for r in aggregated])
    for i in range(4):
        for j in range(5):ax.text(j,i,f'{values[i,j]:.1f}%',ha='center',va='center',color='white' if values[i,j]<55 else 'black')
    fig.colorbar(image,ax=ax,label='Survival (%)');ax.set_title('Existing fault fingerprints: same Forward protocol')
    fig.tight_layout();fig.savefig(OUT/'fault_fingerprints.png',dpi=150);plt.close(fig)
    print(json.dumps({'aggregated':aggregated,'seed42_seed123_spike':selected},indent=2))


if __name__=='__main__':main()
