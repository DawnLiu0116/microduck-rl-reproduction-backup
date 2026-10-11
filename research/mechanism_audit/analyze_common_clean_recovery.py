"""Absolute pre/post ordering spread and gate-aware closed-loop recovery report."""
import json
import math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from verify_ppo_clone import sha,atomic_json

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'full_width_clean_recovery'
BRANCHES=('frozen','no_update','random','ascending','descending')


def main():
    result=json.loads((OUT/'results.json').read_text())
    parent=json.loads((ROOT/'full_width_order_pilot'/'summary.json').read_text())
    assert result['complete'] and len(result['training'])==10 and len(result['gates'])==10
    cases=result['cases']
    assert len(cases)==result['expected_cases_after_gates']
    assert all(len(r['rows'])==64 and r['state_unchanged'] for r in cases)
    assert all(math.isfinite(row[k]) for r in cases for row in r['rows'] for k in ('seconds','return','mean_vx_error','mean_vy_error','mean_yaw_error','mean_action_delta'))
    rows=[]
    for t in (42,2026):
        for b in BRANCHES:
            metrics={}
            for a in (0,-6,6):
                selected=[r for r in cases if (r['teacher'],r['branch'],r['pitch_degrees'])==(t,b,a)]
                if not selected:continue
                assert len(selected)==2
                metrics[str(a)]={'episodes':128,'survival_count':sum(r['survival_count'] for r in selected),
                                 'mean_vx_error':float(np.mean([r['mean_vx_error'] for r in selected])),
                                 'mean_action_delta':float(np.mean([row['mean_action_delta'] for r in selected for row in r['rows']])),
                                 'per_eval_seed':[{k:r[k] for k in ('eval_seed','survival_count','mean_vx_error')} for r in selected]}
            trained=next(r for r in result['training'] if (r['teacher'],r['branch'])==(t,b))
            gate=next(r for r in result['gates'] if (r['teacher'],r['branch'])==(t,b))
            rows.append({'teacher':t,'branch':b,'gate':gate,'closed_loop':metrics,'offline_mse':trained['offline_mse']})
    spread=[]
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for ax,t in zip(axes,(42,2026)):
        old=[next(r for r in parent['rows'] if (r['teacher'],r['branch'])==(t,b))['closed_loop']['0']['mean_vx_error'] for b in ('random','ascending','descending')]
        new=[next(r for r in rows if (r['teacher'],r['branch'])==(t,b))['closed_loop']['0']['mean_vx_error'] for b in ('random','ascending','descending')]
        spread.append({'teacher':t,'pre_nominal_vx_error_range':max(old)-min(old),'post_nominal_vx_error_range':max(new)-min(new)})
        ax.plot(range(3),old,'o-',label='Before clean tail');ax.plot(range(3),new,'o-',label='After same clean tail')
        frozen=next(r for r in rows if (r['teacher'],r['branch'])==(t,'frozen'))['closed_loop']['0']['mean_vx_error']
        ax.axhline(frozen,color='#777777',linestyle='--',label='Fresh frozen evaluation')
        ax.set_xticks(range(3),('random','ascending','descending'));ax.set_ylabel('Mean absolute vx error (m/s)');ax.set_title(f'Source {t}');ax.legend(fontsize=8)
    fig.savefig(OUT/'nominal_pre_post.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(2,3,figsize=(13,7),layout='constrained')
    for i,t in enumerate((42,2026)):
        for j,a in enumerate((0,-6,6)):
            ax=axes[i,j]
            for k,b in enumerate(BRANCHES):
                r=next(r for r in rows if (r['teacher'],r['branch'])==(t,b))
                if str(a) in r['closed_loop']:
                    m=r['closed_loop'][str(a)];ax.bar(k,m['mean_vx_error'])
                    ax.text(k,m['mean_vx_error'],f"{m['survival_count']}/128",ha='center',va='bottom',fontsize=7)
                else:ax.text(k,.01,'not run',ha='center',rotation=90,fontsize=8)
            ax.set_xticks(range(5),BRANCHES,rotation=35,fontsize=7);ax.set_title(f'Source {t}, pitch {a} deg')
            ax.set_ylabel('Mean absolute vx error (m/s)')
    fig.savefig(OUT/'recovery_tracking.png',dpi=160);plt.close(fig)
    summary={'complete':True,'case_count':len(cases),'episode_count':64*len(cases),'rows':rows,'spread':spread,
             'nan_count':sum(r['nan_count'] for r in cases),'out_count':sum(r['out_count'] for r in cases),
             'scope':result['scope'],'limitations':'Two sources and two evaluation seeds only. Both tail data and Adam reset were standardized; cannot isolate their separate causes. Residual differences after finite recovery do not establish persistent poisoning.'}
    atomic_json(OUT/'summary.json',summary)
    lines=['# 同末尾 clean 恢复：实测报告','',result['scope'],'',
           'no_update 在此表表示第一阶段未更新的parent，本阶段也接受256次clean更新；frozen才是本阶段0更新。','',
           '| 来源 | parent分支 | 正常存活 | 正常vx误差 | -6°存活 | +6°存活 |', '|---|---|---:|---:|---:|---:|']
    for r in rows:
        m=r['closed_loop'];f=lambda a:f"{m[a]['survival_count']}/128" if a in m else '未测：正常门槛失败'
        lines.append(f"| {r['teacher']} | {r['branch']} | {f('0')} | {m['0']['mean_vx_error']:.6f} | {f('-6')} | {f('6')} |")
    lines+=['','## 顺序差异：正常前向误差范围','']
    for s in spread:lines.append(f"- source {s['teacher']}：三个顺序间误差范围从 {s['pre_nominal_vx_error_range']:.6f} 变为 {s['post_nominal_vx_error_range']:.6f} m/s。")
    lines+=['',f"完成 {len(cases)} 个case/{64*len(cases)} 个首回合；NaN={summary['nan_count']}，出界={summary['out_count']}。",'',
            '存活、速度跟踪、动作突变应分开解释；存活全满不能证明无风险或防御收益。两个评估seed不是大量独立模型重复。', '',summary['limitations'],'',
            '本轮是有限监督训练路径的终点效应诊断，不是原生PPO投毒或持久后门。无论结果正负，下一步都不自动提高偏差幅度或预算来凑效果。']
    (OUT/'REPORT.md').write_text('\n'.join(lines))
    atomic_json(OUT/'artifact_inventory.json',{'files':[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ('artifact_inventory.json','run.log','process.json')]})
    print('RECOVERY_ANALYSIS_COMPLETE '+json.dumps({k:summary[k] for k in ('case_count','episode_count','spread','nan_count','out_count')}),flush=True)


if __name__=='__main__':main()
