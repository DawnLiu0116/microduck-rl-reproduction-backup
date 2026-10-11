"""Factual absolute metrics and gate-aware plots; no novelty or significance claims."""
import json
import math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from verify_ppo_clone import sha, atomic_json

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'full_width_order_pilot'
BRANCHES=('no_update','random','ascending','descending')


def main():
    result=json.loads((OUT/'results.json').read_text())
    assert result['complete'] and len(result['training'])==8
    cases=result['cases']
    assert all(len(r['rows'])==64 and r['state_unchanged'] for r in cases)
    assert all(math.isfinite(row[k]) for case in cases for row in case['rows'] for k in ('seconds','return','mean_vx_error','mean_vy_error','mean_yaw_error','mean_action_delta'))
    rows=[]
    for t in (42,2026):
        for b in BRANCHES:
            gate=next(r for r in result['gates'] if (r['teacher'],r['branch'])==(t,b))
            metrics={}
            for angle in (0,-6,6):
                selected=[r for r in cases if (r['teacher'],r['branch'],r['pitch_degrees'])==(t,b,angle)]
                if not selected:continue
                assert len(selected)==2
                metrics[str(angle)]={'episodes':128,'survival_count':sum(r['survival_count'] for r in selected),
                                    'mean_vx_error':float(np.mean([r['mean_vx_error'] for r in selected])),
                                    'mean_episode_seconds':float(np.mean([r['mean_episode_seconds'] for r in selected])),
                                    'nan_count':sum(r['nan_count'] for r in selected),'out_count':sum(r['out_count'] for r in selected),
                                    'per_eval_seed':[{k:r[k] for k in ('eval_seed','survival_count','mean_vx_error','mean_episode_seconds')} for r in selected]}
            trained=next(r for r in result['training'] if (r['teacher'],r['branch'])==(t,b))
            rows.append({'teacher':t,'branch':b,'gate':gate,'closed_loop':metrics,'offline_mse':trained['offline_mse'],
                         'max_weight_change':trained['max_weight_change']})
    fig,axes=plt.subplots(2,3,figsize=(13,7),layout='constrained')
    for i,t in enumerate((42,2026)):
        for j,angle in enumerate((0,-6,6)):
            ax=axes[i,j]
            for k,b in enumerate(BRANCHES):
                row=next(r for r in rows if (r['teacher'],r['branch'])==(t,b))
                if str(angle) in row['closed_loop']:
                    m=row['closed_loop'][str(angle)]
                    ax.bar(k,m['survival_count']/128,color=('#666666','#4477AA','#EE9944','#AA4477')[k])
                    ax.text(k,m['survival_count']/128+.02,f"{m['survival_count']}/128",ha='center',fontsize=8)
                else:ax.text(k,.1,'not run\nnominal gate failed',ha='center',fontsize=7,rotation=90)
            ax.set_ylim(0,1.17);ax.set_xticks(range(4),BRANCHES,rotation=25,fontsize=8)
            ax.set_title(f'Source {t}, pitch {angle} deg');ax.set_ylabel('First-episode survival (20 s)')
    fig.savefig(OUT/'closed_loop_survival.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for ax,t in zip(axes,(42,2026)):
        for b in BRANCHES:
            row=next(r for r in rows if (r['teacher'],r['branch'])==(t,b))
            vals=[np.mean([m[str(a)] for m in row['offline_mse'].values()]) for a in (-6,0,6)]
            ax.plot((-6,0,6),vals,marker='o',label=b)
        ax.set_title(f'Source {t}: two held-out collections');ax.set_xlabel('Observed pitch offset (deg)');ax.set_ylabel('Absolute action MSE');ax.legend(fontsize=8)
    fig.savefig(OUT/'offline_mse.png',dpi=160);plt.close(fig)
    summary={'complete':True,'case_count':len(cases),'episode_count':len(cases)*64,'passed_nominal_gates':sum(r['gate']['nominal_gate_passed'] for r in rows),
             'rows':rows,'scope':result['scope'],'limitations':['Two source models, one training collection per source, one random batch schedule, two evaluation seeds. No independent optimization-seed replication.',
                 'Fixed +/-6 degree observation transformation; not native IMU DR or physical pose change.',
                 'Orders share data but differ in their final batch angle; endpoint effects and ordinary forgetting remain explanations.',
                 'Fault trials are gated by nominal quality; missing cases are not zero outcomes.',
                 'No claim of statistical significance, real-hardware safety, poisoning novelty, or native PPO learning.']}
    atomic_json(OUT/'summary.json',summary)
    lines=['# 完整 PPO actor 训练顺序 pilot：实测报告','',result['scope'],'',
           f"完成 {len(cases)} 个case、{len(cases)*64} 个首回合；正常门槛通过 {summary['passed_nominal_gates']}/8 分支。",
           '', '| 来源 | 分支 | 正常存活 | 正常vx误差(m/s) | -6°存活 | +6°存活 |', '|---|---|---:|---:|---:|---:|']
    for r in rows:
        m=r['closed_loop'];n=m['0']
        f=lambda a:f"{m[a]['survival_count']}/128" if a in m else '未测：正常门槛失败'
        lines.append(f"| {r['teacher']} | {r['branch']} | {n['survival_count']}/128 | {n['mean_vx_error']:.6f} | {f('-6')} | {f('6')} |")
    lines+=['','## 解释边界','','正常性能回归和故障收益必须分别看；离线MSE改善不自动等于闭环安全改善。相同样本顺序差异也不自动等于投毒，尤其末批角度与普通遗忘可能解释差异。','',
            '完整逐回合数据、各评估seed分别结果及所有loss见 results.json；模型与优化器恢复文件仅供本监督实验，不作为原生PPO resume checkpoint。','',
            '## 限制','']+['- '+x for x in summary['limitations']]
    (OUT/'REPORT.md').write_text('\n'.join(lines))
    inventory=[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ('artifact_inventory.json','run.log','process.json')]
    atomic_json(OUT/'artifact_inventory.json',{'files':inventory,'excluded_mutable_runtime_files':['run.log','process.json']})
    print('ANALYSIS_COMPLETE '+json.dumps({k:summary[k] for k in ('case_count','episode_count','passed_nominal_gates')}),flush=True)


if __name__=='__main__':main()
