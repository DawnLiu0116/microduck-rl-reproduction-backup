"""CPU-only plotting of existing artifacts. Does not import experiment engines."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import csv, hashlib, json, math, re, sys
from pathlib import Path
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
BASE=Path('/mnt/d/MicroDuckResearch/ti/outputs/microduck_reproduction')
OUT=BASE/'all_work_reports_20261015'; FIG=OUT/'figures'
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':120,'savefig.dpi':155})
catalog=[]
def read(rel):return json.loads((BASE/rel).read_text())
def save(fig,w,slug,title,note):
 fig.tight_layout();p=FIG/f'{w:02d}_{slug}.png';fig.savefig(p,bbox_inches='tight');plt.close(fig)
 catalog.append({'work':w,'file':str(p.relative_to(OUT)),'title':title,'note':note,'kind':'new_existing_data_plot'})
def panel(n=1,nc=2,h=3.2):
 nr=math.ceil(n/nc);fig,ax=plt.subplots(nr,nc,figsize=(12,nr*h),squeeze=False)
 for a in ax.ravel()[n:]:a.set_visible(False)
 return fig,ax.ravel()
def label(r):return str(r['model'])+('/'+str(r['branch']) if r.get('branch') else '')
jobs=read('all_work_reports_20261015/data/cases.json')
extra=read('all_work_reports_20261015/data/extra.json')
curves=read('all_work_reports_20261015/data/survival_curves.json')
# Read actual event files for all three completed policies. Stitch only saved seed2026 lineage.
prov=read('mechanism_audit/resume_provenance_audit/results.json')
training={};training_sources=[]
for runname,run in prov['runs'].items():
 directory=Path(run['directory'].replace('/home/deuler/microduck_rl','/mnt/d/MicroDuckResearch/microduck_rl'))
 files=sorted(directory.glob('events.out.tfevents.*'))
 tags=defaultdict(dict)
 for f in files:
  ea=EventAccumulator(str(f),size_guidance={'scalars':0});ea.Reload()
  for tag in ea.Tags()['scalars']:
   for e in ea.Scalars(tag):tags[tag][e.step]=e.value
  training_sources.append({'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'run':runname})
 training[runname]={k:sorted(v.items()) for k,v in tags.items()}
merged={}
for seed in ['42','123','2026']:
 if seed!='2026':merged[seed]=training['seed'+seed]
 else:
  merged[seed]={}
  for tag in set(training['seed2026_parent'])|set(training['seed2026_resume']):
   parent=[p for p in training['seed2026_parent'].get(tag,[]) if p[0]<=3250]
   resume=training['seed2026_resume'].get(tag,[])
   merged[seed][tag]={'parent':parent,'resume':resume}
alltags=sorted(set(t for d in training.values() for t in d))
for cat in sorted(set(t.split('/')[0] for t in alltags)):
 ts=[t for t in alltags if t.startswith(cat+'/')]
 for block in range(0,len(ts),6):
  subset=ts[block:block+6];fig,axs=panel(len(subset),2,3)
  for ax,tag in zip(axs,subset):
   for seed,color in zip(['42','123','2026'],['#2166ac','#b2182b','#238b45']):
    points=merged[seed].get(tag,[])
    if isinstance(points,dict):
     for part,style in [('parent','-'),('resume','--')]:
      pp=points[part]
      if pp:ax.plot(*np.array(pp).T,color=color,lw=.8,ls=style,label='2026 '+part)
     ax.axvline(3250,color='gray',ls=':',lw=.6)
    elif points:ax.plot(*np.array(points).T,label=seed,color=color,lw=.8)
   ax.set(title=tag,xlabel='Logged PPO iteration',ylabel='Logged scalar');ax.grid(alpha=.2);ax.legend(fontsize=7)
  save(fig,1,f'train_{cat}_{block//6+1}',f'三个来源的训练日志 {cat}',
   '横轴为原日志迭代编号，未平滑。2026实线为保留的parent至3250，虚线为恢复段3250至3999；重复编号不合并为同一训练轮，丢弃parent的3251至3272。训练聚合量不是闭环评估百分比。')
(OUT/'data/training_scalars.json').write_text(json.dumps({'raw_runs':training,'merged_lineage':merged,'sources':training_sources},ensure_ascii=False))
# 244 checkpoints provenance: expose counts and resume offsets without model loading.
fig,axs=panel(4,2,3)
for ax,(name,run) in zip(axs,prov['runs'].items()):
 rr=run['checkpoints'];ax.plot([r['iter'] for r in rr],[r['actor']['count']/1e6 for r in rr],'.-',label='actor count / 1e6')
 ax.plot([r['iter'] for r in rr],[r['critic']['count']/1e6 for r in rr],'--',label='critic count / 1e6')
 ax.set(title=name,xlabel='Saved iteration',ylabel='Historical sample count (million)');ax.legend(fontsize=8);ax.grid(alpha=.2)
save(fig,2,'checkpoint_counts','244份checkpoint历史统计量与迭代对应','点为真实保存点，不是新增训练。actor与critic曲线重合；2026恢复边界实际多一轮，应结合报告中的rollout账本。统计一致性不证明历史从未遭受任何攻击。')
# Every case is represented in a point inventory, and the data explorer retains exact identifiers.
for w in [3,4,5,6,8,9,10,11,12,13,14,15,16]:
 jj=[r for r in jobs if r['work']==w]
 batches=sorted(set(r.get('stage','') for r in jj)) if w==5 else ['all']
 for stage in batches:
  rr=[r for r in jj if stage=='all' or r.get('stage','')==stage]
  metrics=[('rate','20s survival (%)',100),('seconds','Observed first-episode duration (s)',1)]
  if w==12:metrics=[('max_tilt','Maximum tilt (deg)',1)]
  elif any(r.get('vx') is not None for r in rr):metrics.append(('vx','Mean abs vx error (m/s)',1))
  elif any(r.get('xy') is not None for r in rr):metrics.append(('xy','Mean XY velocity error (m/s)',1))
  fig,axs=plt.subplots(len(metrics),1,figsize=(12,2.45*len(metrics)),squeeze=False)
  labels=sorted(set(label(r) for r in rr));colors=plt.get_cmap('tab20',max(1,len(labels)))
  for ax,(key,title,mul) in zip(axs.ravel(),metrics):
   for li,lab in enumerate(labels):
    inds=[i for i,r in enumerate(rr) if label(r)==lab and r.get(key) is not None]
    if inds:ax.scatter(inds,[rr[i][key]*mul for i in inds],s=12,alpha=.8,label=lab,color=colors(li))
   ax.set(ylabel=title,xlabel='Case index (discrete inventory; not time or dose)');ax.grid(alpha=.2)
   if key=='rate':ax.set_ylim(-3,103)
  if len(labels)<=10:axs[0,0].legend(fontsize=7,ncol=min(4,len(labels)))
  fig.suptitle(f'Work {w:02d} / {stage}: every recorded case ({len(rr)})',y=1.01)
  save(fig,w,f'all_cases_{stage}',f'全部任务点 {stage}',
   '每个点是一项真实任务；横轴仅是文件记录顺序，不是连续变量，故不连线。点保留评估seed差异。条件、模型和分母可在全数据浏览器按编号查询；早停时误差只覆盖终止前。')
# Survival curves on a physical time axis, keeping distinct policies and fault contracts separate.
for w in [3,4,6,8,9,10,11,13,14,15,16]:
 cc=[r for r in curves if r['work']==w]
 facets=defaultdict(list)
 for r in cc:
  if w==16:
   mm=re.match(r's(\d+)_',r['model']);source=mm[1] if mm else 'official'
   ww=re.search(r'w([^_]+)',r['model']);weight=ww[1] if ww else 'original'
   fk=f'{source} / w={weight} / {r["condition"]}'
  elif w==15:
   mm=re.match(r's(\d+)_r(\d+)',r['model']);fk=('/'.join(mm.groups()) if mm else r['model'])+' / '+r['condition']
  elif w==14:fk=r['model'].split('_')[0]+' / '+r['condition']
  else:fk=r['condition']
  facets[fk].append(r)
 keys=sorted(facets)
 for b in range(0,len(keys),6):
  chosen=keys[b:b+6];fig,axs=panel(len(chosen),2,3.3)
  for ax,key in zip(axs,chosen):
   for r in facets[key]:
    lab=r['model']+('/'+r['branch'] if r['branch'] else '')
    if w in (9,10):lab+=' / '+r['branch']
    if w==16:lab=lab.replace('s','').replace('_',' / ')
    ax.step(r['t'],100*np.array(r['alive']),where='post',label=lab,lw=1)
   ax.set(title=key,xlabel='First-episode time (s)',ylabel='Not yet terminated (%)',xlim=(0,20),ylim=(-2,103));ax.grid(alpha=.2)
   ax.legend(fontsize=6,ncol=2 if len(facets[key])>5 else 1,loc='lower left')
  save(fig,w,f'survival_{b//6+1}',f'首回合存续曲线 第{b//6+1}组',
   '横轴为首回合仿真秒，纵轴为尚未因任何原因终止的比例；20秒超时保留在终点，不画成死亡。由已保存终止时间重算，在0.1秒网格显示；不是完整姿态轨迹，也不把跨评估seed回合当独立训练。相同曲线可能重合。')
# Full-width supervised training actually saved per-minibatch losses.
for w,rel in [(9,'mechanism_audit/full_width_order_pilot/results.json'),(10,'mechanism_audit/full_width_clean_recovery/results.json')]:
 d=read(rel);fig,axs=panel(2,2,3.8)
 for ax,source in zip(axs,[42,2026]):
  for r in d['training']:
   if r['teacher']!=source or not r.get('loss'):continue
   ax.plot(range(1,len(r['loss'])+1),r['loss'],label=r['branch'],alpha=.85)
  ax.set(title=f'Source {source}',xlabel='Actual supervised optimizer update',ylabel='Mini-batch loss');ax.set_yscale('log');ax.grid(alpha=.2);ax.legend(fontsize=8)
 save(fig,w,'supervised_loss','监督更新过程的原始小批次loss','每条线为真实记录的监督更新，不是PPO回报。排序会改变每批样本难度，loss不可直接当全数据收敛或闭环安全。无更新分支没有loss，不补零。')
# Paired T effects, all 16 source/train/branch/norm contrasts.
a=extra['data_reanalysis_20261015_v2/analysis.json']
fig,axs=panel(4,2,3.7)
for ax,(s,seed) in zip(axs,[('42',73001),('42',73002),('123',73001),('123',73002)]):
 for r in a['T_paired']:
  if str(r['source'])!=s or int(r['training_seed'])!=seed:continue
  yy=[r['delta150']['survival']['mean'],r['delta200']['survival']['mean']]
  ax.plot([150,200],yy,'o-',label=r['branch']+'_'+r['norm'])
  for x,kk in zip([150,200],['delta150','delta200']):ax.vlines(x,r[kk]['survival']['min'],r[kk]['survival']['max'],alpha=.45)
 ax.axhline(0,color='gray',ls=':');ax.set(title=f'Source {s} / train {seed}',xlabel='Added rollout checkpoint',ylabel='Pulse07 delta vs matched clean (pp)',xticks=[150,200]);ax.legend(fontsize=8);ax.grid(alpha=.2)
save(fig,15,'all_paired_recovery','T全部16格的故障差异与clean尾段恢复','与同来源、同训练seed、同F/U的T0比较。竖线是三个评估seed差值范围，不是95%置信区间。仅150和200两个实测终点，连线不代表中间连续测量。')
# All 4 conditions and 54 contrasts each, not only the strongest Pulse07 cells.
for metric,unit,scale in [('survival','Survival delta (pp)',100),('seconds','Duration delta (s)',1),('vx_error','Vx error delta (m/s)',1),('action_delta','Action delta difference',1)]:
 fig,axs=plt.subplots(4,3,figsize=(13,12),squeeze=False)
 for ri,cond in enumerate(['Forward','Delay20','Delay40','Pulse07']):
  for ci,s in enumerate(['42','123','2026']):
   ax=axs[ri,ci]
   for p in [.1,.5,1.]:
    rr=sorted([r for r in a['dose_paired'] if str(r['source'])==s and r['condition']==cond and r['p']==p],key=lambda r:r['w'])
    # Existing analysis stores survival difference in percentage points already.
    mul=1
    ax.plot([r['w'] for r in rr],[r[metric]['mean']*mul for r in rr],'o-',ms=3,label=f'p={p:g}')
   ax.axhline(0,c='gray',ls=':',lw=.7);ax.set_xscale('log');ax.set(title=f'{s} / {cond}',xlabel='Effective moment weight w',ylabel=unit);ax.grid(alpha=.2);ax.legend(fontsize=7)
 save(fig,16,f'paired_full_{metric}',f'全部条件的同w配对曲线 {metric}',
  '每格先在同w、同评估seed下减p=0 clean，再汇总三个seed。横轴w为人工矩合并权重，不是PPO步数或实际采样量；p为新部分污染比例。点间连线仅辅助读图，不外推边界；所有正负结果都保留。')
# Offline mechanisms: all real measured timepoints and conditions, aggregated only within explicitly shown design cells.
for kind,rel in [('normalization','mechanism_audit/normalization_confirmation/results.json'),('replay','mechanism_audit/replay_fork_pilot/results.json')]:
 d=read(rel);by=defaultdict(lambda:defaultdict(list))
 for r in d['rows']:
  if kind=='normalization':
   key=f"{r['teacher_seed']} LR{r['lr']} a{r['amplitude']} {r['normalization']}"
   for stage,vals in r['metrics'].items():
    x=int(stage.split('_')[-1])+(1024 if stage.startswith('clean_recovery') else 0)
    by[key][(r['order'],x)].append(max(v for kk,v in vals.items() if str(kk)!='0'))
  else:
   key=f"{r['teacher_seed']} LR{r['lr']}"
   for stage,ev in r['metrics'].items():
    for values in ev.values():by[key][(r['branch'],int(stage))].append(max(v for kk,v in values.items() if str(kk)!='0'))
 keys=sorted(by)
 for b in range(0,len(keys),6):
  chosen=keys[b:b+6];fig,axs=panel(len(chosen),2,3.5)
  for ax,key in zip(axs,chosen):
   schedules=sorted(set(k[0] for k in by[key]))
   for branch in schedules:
    xs=sorted(k[1] for k in by[key] if k[0]==branch);ys=[np.mean(by[key][(branch,x)]) for x in xs]
    ax.plot(xs,ys,'o-',ms=3,label=branch)
   ax.set(title=key,xlabel='Optimizer updates (measured checkpoints)',ylabel='Mean worst-direction MSE');ax.legend(fontsize=7);ax.grid(alpha=.2)
   if kind=='normalization':ax.axvline(1024,c='gray',ls=':')
  save(fig,11,f'offline_{kind}_{b//6+1}',f'离线机制的全部条件与测量时点 {kind} 第{b//6+1}组',
   '纵轴为学生拟合teacher动作的MSE，越低只表示离线拟合更接近。按标题所列设计单元对学生/采集重复取均值，未把它们称独立PPO模型。实测离散时点间连线，不代表中间均有测量。')
(OUT/'data/new_figure_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2))
print(json.dumps({'new_figures':len(catalog),'training_tags':len(alltags),'training_event_files':len(training_sources)},ensure_ascii=False),flush=True)
