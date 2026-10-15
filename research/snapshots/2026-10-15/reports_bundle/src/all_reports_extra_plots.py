import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import json,hashlib,math
from pathlib import Path
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path('/mnt/d/MicroDuckResearch/ti/outputs/microduck_reproduction');O=B/'all_work_reports_20261015'
cat=json.loads((O/'data/new_figure_catalog.json').read_text());inputs=[]
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':155})
def rd(p):return json.loads(p.read_text())
def sv(fig,w,slug,title,note):
 fig.tight_layout();name=f'figures/{w:02d}_{slug}.png';fig.savefig(O/name,bbox_inches='tight');plt.close(fig)
 cat.append({'work':w,'file':name,'title':title,'note':note,'kind':'new_existing_data_plot'})
dd=[]
for p in sorted((B/'preprocessing_integrity_v2/t/formal').glob('*/results.json')):
 d=rd(p)
 if not d.get('complete') or d.get('completed_rollouts')!=200:raise ValueError(str(p))
 rr=d['metrics']
 if len(rr)!=200 or sorted(r['rollout'] for r in rr)!=list(range(1,201)):raise ValueError(('rollout coverage',str(p)))
 dd.append(d);inputs.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
assert len(dd)==24
metrics=[('mean_reward_per_step','Mean reward per environment step'),('done_count','Terminated environments per rollout'),('actor_count','Actor normalizer historical count'),('critic_count','Critic normalizer historical count'),('modified_consumed','Modified actor inputs per rollout'),('collect_seconds','Collection wall time (s)'),('value','Value loss'),('surrogate','Surrogate loss'),('entropy','Entropy loss')]
for key,title in metrics:
 fig,axs=plt.subplots(2,2,figsize=(12,7))
 for ax,(s,seed) in zip(axs.ravel(),[(42,73001),(42,73002),(123,73001),(123,73002)]):
  for d in dd:
   if (d['source'],d['seed'])!=(s,seed):continue
   rr=sorted(d['metrics'],key=lambda r:r['rollout']);vals=[r.get(key,r.get('losses',{}).get(key)) for r in rr]
   assert all(isinstance(v,(float,int)) and math.isfinite(v) for v in vals)
   ax.plot([r['rollout'] for r in rr],vals,lw=.9,label=d['branch']+'_'+d['normalization'])
  ax.axvspan(50,150,color='#cccccc',alpha=.2);ax.set(title=f'Source {s} / train {seed}',xlabel='Completed added rollout',ylabel=title);ax.grid(alpha=.2);ax.legend(fontsize=7,ncol=2)
 sv(fig,15,'train_'+key,'T24分支逐轮训练 '+title,'原正式results的200个rollout指标，六线为T0/TC/TI×F/U，灰区为第51—150轮干预期。没有合并TensorBoard中被恢复覆盖的旧尝试；NaN终止另在原数据中保留。训练done_count不是固定评估跌倒率。')
(O/'data/T_training_records.json').write_text(json.dumps({'runs':dd,'sources':inputs},ensure_ascii=False))
# Include the additional original-policy repeats in the same machine-readable case index.
cases=rd(O/'data/cases.json');rep=rd(B/'mechanism_audit/ppo_clone_baseline/repeatability.json')
for i,r in enumerate(rep['cases']):
 if any(j['work']==13 and j['branch']=='repeat_original' and str(j['model'])==str(r['seed']) for j in cases):continue
 rows=r['rows'];assert len(rows)==64
 cases.append({'work':13,'id':'repeat_'+str(i),'model':str(r['seed']),'condition':'Forward','branch':'repeat_original','seed':r['eval_seed'],'stage':'repeat','n':64,'survived':sum(x['survival'] for x in rows),'rate':sum(x['survival'] for x in rows)/64,'seconds':np.mean([x['seconds'] for x in rows]),'vx':np.mean([x['mean_vx_error'] for x in rows]),'yaw':np.mean([x['mean_yaw_error'] for x in rows])})
(O/'data/cases.json').write_text(json.dumps(cases,ensure_ascii=False))
orig=rd(B/'mechanism_audit/ppo_clone_baseline/results.json')
fig,axs=plt.subplots(1,2,figsize=(12,4))
for ax,s in zip(axs,[42,2026]):
 rows={r['variant']:r['rows'] for r in orig['cases'] if r['seed']==s and r['scenario']=='Forward'}
 rr=next(r['rows'] for r in rep['cases'] if r['seed']==s)
 baseline=np.array([r['mean_vx_error'] for r in rows['original']])
 for name,vs in [('clone',rows['clone']),('repeat original',rr)]:
  diff=np.array([r['mean_vx_error'] for r in vs])-baseline
  ax.plot(np.sort(np.abs(diff)),np.arange(1,len(diff)+1)/len(diff),label=name)
 ax.set(title=f'Source {s}',xlabel='Absolute paired vx error difference (m/s)',ylabel='Empirical cumulative fraction');ax.legend();ax.grid(alpha=.2)
sv(fig,13,'clone_repeat_ecdf','原克隆与原原重复的误差差值分布','横轴为相同环境编号的逐回合vx误差绝对差，纵轴为经验累积分布。两组差异相近不构成统计等价证明；闭环严格逐位门槛仍为失败。原/原重复128回合也计入本工作640总量。')
# Mechanism decomposition: categorical conditions are not joined into a dose curve.
jj=[r for r in cases if r['work']==8];conds=list(dict.fromkeys(r['condition'] for r in jj))
fig,ax=plt.subplots(figsize=(12,5))
for k,m in enumerate(sorted(set(r['model'] for r in jj))):
 vals=[]
 for c in conds:
  rs=[r for r in jj if r['model']==m and r['condition']==c];vals.append(100*sum(r['survived'] for r in rs)/sum(r['n'] for r in rs))
 ax.bar(np.arange(len(conds))+(k-.5)*.34,vals,width=.34,label=m)
ax.set(xticks=np.arange(len(conds)),xticklabels=conds,ylabel='20s survival (%)',ylim=(0,106));ax.tick_params(axis='x',rotation=35);ax.legend();ax.grid(axis='y',alpha=.2)
sv(fig,8,'mechanism_all_conditions','脉冲机制十条件完整对照','每柱两评估seed合计128首回合。条件是类别，不是可连续加总的剂量；startup、walking和各单通道暴露不同，不能把柱高差直接当独立因果效应。')
# Basic BC pre/post endpoints for all eight students.
d=rd(B/'curriculumtrap_pilot/results.json');fig,axs=plt.subplots(1,2,figsize=(12,4))
for ax,seed in zip(axs,sorted(set(r['seed'] for r in d['rows']))):
 for r in d['rows']:
  if r['seed']!=seed:continue
  yy=[max(v for a,v in r[z].items() if a!='0') for z in ['before_tail_mse','after_tail_mse']]
  ax.plot([0,1],yy,'o-',label=r['schedule'])
 ax.set(title=f'Student init {seed}',xticks=[0,1],xticklabels=['Before clean tail','After clean tail'],ylabel='Worst canary action MSE');ax.legend(fontsize=8);ax.grid(alpha=.2)
sv(fig,11,'basic_bc_endpoints','小BC全部学生的clean尾段前后','只在两端有测量，中间连线不表示完整学习曲线。学生初始化seed不是PPO来源seed。保留未过门槛的结果，不把MSE换算成跌倒率。')
(O/'data/new_figure_catalog.json').write_text(json.dumps(cat,ensure_ascii=False,indent=2));print(json.dumps({'figures':len(cat),'T_runs':len(dd),'T_rollouts':sum(len(d['metrics']) for d in dd),'clone_total':sum(r['n'] for r in cases if r['work']==13)}))
