"""Correct report-only grouping and time-axis semantics found during visual review."""
import os,csv,json,hashlib,math
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
from all_reports_build import BASE,OUT,SOURCES,load,resolve,truth,dump
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':155})
jobs=json.loads((OUT/'data/cases.json').read_text());curves=json.loads((OUT/'data/survival_curves.json').read_text());cat=json.loads((OUT/'data/new_figure_catalog.json').read_text())
for j in jobs:
 if j['work'] in (4,8):j['condition']=j['fault']['name']
 if j['work']==11:j['condition']='Forward'
curves=[r for r in curves if r['work'] not in (4,8,11,13)]
for w in (4,8,11,13):
 d=load(SOURCES[w]);rows=d.get('results',d.get('cases',[]));ep=defaultdict(list)
 if w==13:rows+=load('mechanism_audit/ppo_clone_baseline/repeatability.json')['cases']
 for i,r in enumerate(rows):
  if r.get('raw_episode_file'):
   with resolve(r['raw_episode_file']).open(newline='') as f:rr=list(csv.DictReader(f))
  else:rr=r['rows']
  model=str(r.get('model_label',r.get('teacher_seed',r.get('seed'))));branch=r.get('branch',r.get('variant',''))
  cond=r['fault_name'] if w in (4,8) else ('Forward' if w==11 else r['scenario'])
  for x in rr:ep[(model,branch,cond)].append((float(x['seconds']),truth(x['survival'])))
 for (m,b,c),rr in ep.items():curves.append({'work':w,'model':m,'branch':b,'condition':c,'stage':'','command':'[0.3,0,0]' if w in (4,8,11) else 'see case','n':len(rr),'t':[k*.1 for k in range(201)],'alive':[sum(sv or sec>k*.1+1e-8 for sec,sv in rr)/len(rr) for k in range(201)]})
dump(OUT/'data/cases.json',jobs);dump(OUT/'data/survival_curves.json',curves)
def save(fig,w,name,title,note):
 file=f'figures/{w:02d}_{name}.png';fig.tight_layout();fig.savefig(OUT/file,bbox_inches='tight');plt.close(fig)
 f={'work':w,'file':file,'title':title,'note':note,'kind':'new_existing_data_plot'}
 for k,old in enumerate(cat):
  if old['file']==file:cat[k]=f;return
 cat.append(f)
for w in (4,8,11,13):
 cc=[r for r in curves if r['work']==w];conds=sorted(set(r['condition'] for r in cc))
 for b in range(0,len(conds),6):
  sub=conds[b:b+6];fig,axs=plt.subplots(math.ceil(len(sub)/2),2,figsize=(12,3.6*math.ceil(len(sub)/2)),squeeze=False)
  for ax,c in zip(axs.ravel(),sub):
   for r in cc:
    if r['condition']==c:ax.step(r['t'],np.array(r['alive'])*100,where='post',lw=1,label=r['model']+('/'+r['branch'] if r['branch'] else ''))
   ax.set(title=c,xlabel='First-episode time (s)',ylabel='Not yet terminated (%)',xlim=(0,20),ylim=(-2,103));ax.grid(alpha=.2);ax.legend(fontsize=7,ncol=2 if w==11 else 1,loc='lower left')
  for ax in axs.ravel()[len(sub):]:ax.set_visible(False)
  save(fig,w,f'survival_{b//6+1}',f'逐故障首回合存续曲线 第{b//6+1}组','每个面板严格保持同一故障条件，未混合clean、启动和行走故障。纵轴为尚未终止的首回合比例，20秒超时保留在终点；0.1秒显示网格。合并的是同模型同条件评估seed，不是独立训练重复。')
jj=[r for r in jobs if r['work']==8];conds=list(dict.fromkeys(r['condition'] for r in jj));fig,ax=plt.subplots(figsize=(13,5))
for k,m in enumerate(sorted(set(r['model'] for r in jj))):
 vals=[]
 for c in conds:
  rs=[r for r in jj if r['model']==m and r['condition']==c];vals.append(100*sum(r['survived'] for r in rs)/sum(r['n'] for r in rs))
 ax.bar(np.arange(len(conds))+(k-.5)*.35,vals,width=.35,label=m)
ax.set(xticks=np.arange(len(conds)),xticklabels=conds,ylabel='20s survival (%)',ylim=(0,106));ax.tick_params(axis='x',rotation=40);ax.legend();ax.grid(axis='y',alpha=.2)
save(fig,8,'mechanism_all_conditions','脉冲机制十条件完整对照','十个真实条件分别展示，每柱两评估seed合计128首回合。条件是类别，不连成剂量曲线；输入能量和早停暴露不同，不作单一因果解释。')
# TensorBoard /time tags use elapsed-time step, not PPO iteration. Retain the true axis and lineage cutoff.
path=OUT/'data/training_scalars.json';data=json.loads(path.read_text());time_tags=[k for k in data['raw_runs']['seed42'] if k.endswith('/time')]
fixed={}
prov=load(SOURCES[2])
for name,run in prov['runs'].items():
 dr=Path(run['directory'].replace('/home/deuler/microduck_rl','/mnt/d/MicroDuckResearch/microduck_rl'));all_events={}
 for p in dr.glob('events.out.tfevents.*'):
  ea=EventAccumulator(str(p),size_guidance={'scalars':0});ea.Reload()
  cutoff=next((e.wall_time for e in ea.Scalars('Train/mean_reward') if e.step==3250),None) if name=='seed2026_parent' else None
  for tag in time_tags:all_events[tag]=[(e.step,e.value) for e in ea.Scalars(tag) if cutoff is None or e.wall_time<=cutoff+1e-5]
 fixed[name]=all_events
fig,axs=plt.subplots(2,2,figsize=(12,7))
tags=['Train/mean_episode_length','Train/mean_episode_length/time','Train/mean_reward','Train/mean_reward/time']
for ax,tag in zip(axs.ravel(),tags):
 for name,color,ls in [('seed42','#2166ac','-'),('seed123','#b2182b','-'),('seed2026_parent','#238b45','-'),('seed2026_resume','#238b45','--')]:
  if tag.endswith('/time'):pp=fixed[name][tag]
  else:
   pp=data['raw_runs'][name][tag]
   if name=='seed2026_parent':pp=[p for p in pp if p[0]<=3250]
  if pp:ax.plot(*np.array(pp).T,color=color,ls=ls,lw=.8,label=name.replace('seed',''))
 ax.set(title=tag,xlabel='Logged elapsed time (s; run-local clock)' if tag.endswith('/time') else 'Logged PPO iteration',ylabel='Logged scalar');ax.grid(alpha=.2);ax.legend(fontsize=7)
save(fig,1,'train_Train_1','三个来源的回报与回合长度 迭代轴与时间轴','左列横轴为PPO迭代标签，右列为各运行日志elapsed秒，恢复段时钟单独保留，不能看作同一连续墙钟。2026父阶段按3250保存点对应wall_time截断，再与恢复段区分展示，不把/time的秒数误当迭代编号。')
data['time_axis_lineage']=fixed;dump(path,data)
dump(OUT/'data/new_figure_catalog.json',cat)
print(json.dumps({'corrected_condition_work':[4,8,11,13],'curve_groups':len(curves),'time_axis_fixed':time_tags,'new_figures':len(cat)}))
