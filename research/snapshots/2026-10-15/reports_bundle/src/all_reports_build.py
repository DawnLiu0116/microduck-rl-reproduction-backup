"""Read-only experiment inputs; write a new, versioned reporting package only."""
import csv, hashlib, html, json, math, os, re, shutil, sys, statistics, time
from collections import defaultdict, Counter
from pathlib import Path
BASE=Path('D:/MicroDuckResearch/ti/outputs/microduck_reproduction') if os.name=='nt' else Path('/mnt/d/MicroDuckResearch/ti/outputs/microduck_reproduction')
OUT=BASE/'all_work_reports_20261015'
SOURCES={
 2:'mechanism_audit/resume_provenance_audit/results.json',
 3:'task_protocol_v2/four_model_final/four_model_results.json',
 4:'sensor_fault_benchmark/independent_confirmation/results.json',
 5:'fine_response/results/results.json',
 6:'priority_delay_audit/diagnostic_results/results.json',
 8:'sensor_fault_benchmark/pulse_mechanism/results.json',
 9:'mechanism_audit/full_width_order_pilot/results.json',
 10:'mechanism_audit/full_width_clean_recovery/results.json',
 11:'mechanism_audit/replay_fork_pilot/closed_loop_smoke.json',
 12:'mechanism_audit/sim_fall_filter/results.json',
 13:'mechanism_audit/ppo_clone_baseline/results.json',
 14:'preprocessing_integrity_v2/n/formal/results.json',
 15:'preprocessing_integrity_v2/t/evaluation/results.json',
 16:'effective_dose_response/evaluation/results.json'}
TITLES=['完整PPO训练','导出与来源核验','固定命令任务评估','独立评估seed故障确认','精细响应完整基准','原生延迟诊断','论文报告与统一视频','脉冲机制拆分','完整actor监督顺序','同末尾clean恢复','小型BC 归一化与replay','安全预处理','零更新克隆','V2 N推理统计对照','V2 T真实PPO续训','人工有效剂量状态']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for buf in iter(lambda:f.read(1024*1024),b''):h.update(buf)
 return h.hexdigest()
def load(rel):return json.loads((BASE/rel).read_text('utf-8-sig'))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),'utf-8')
def truth(x):return str(x).lower() in ('true','1','1.0')
def resolve(s):
 s=str(s).replace('\\','/')
 marker='outputs/microduck_reproduction/'
 if marker in s:return BASE/s.split(marker,1)[1]
 if s.startswith('/mnt/d/'):return Path(s) if os.name!='nt' else Path('D:/'+s[7:])
 return Path(s)
def number(x):
 try:return float(x)
 except (ValueError,TypeError):return None
def pick(r,*ks):return next((r[k] for k in ks if k in r and r[k] is not None),None)
def compact_case(w,r,i):
 model=str(pick(r,'model_label','model','teacher','teacher_seed','seed'))
 cond=str(pick(r,'condition','scenario','fault_name') or 'unknown')
 if w in (4,6,8):cond=r['fault_name']
 if w==11:cond='Forward'
 if w in (9,10):cond='pitch='+str(r['pitch_degrees'])
 if w==13:cond=r['scenario']
 branch=str(r.get('branch',r.get('variant','')))
 return {'work':w,'id':str(r.get('job_id',i)), 'model':model,'condition':cond,'branch':branch,
 'seed':r.get('eval_seed',r.get('seed')),'stage':r.get('stage',''),
 'fault':r.get('fault_parameters',{}),'command':r.get('command'),
 'n':r.get('episodes',len(r.get('rows',[])) or None),
 'survived':pick(r,'success_count','survival_count'),
 'seconds':pick(r,'mean_seconds','mean_episode_seconds'),
 'vx':pick(r,'mean_vx_error_mps','mean_abs_vx_error_mps','mean_vx_error'),
 'xy':pick(r,'mean_xy_velocity_error_mps'),'yaw':pick(r,'mean_yaw_velocity_error_radps','mean_abs_yaw_error_radps','mean_yaw_error'),
 'action':pick(r,'mean_action_delta_l2'),'raw':r.get('raw_episode_file'), 'raw_sha_expected':r.get('raw_sha256')}
def extract():
 OUT.mkdir(parents=True,exist_ok=True)
 for name in ['figures','data','reports','original_figures']:(OUT/name).mkdir(exist_ok=True)
 manifest=[];jobs=[]; audits=[]; curves=[]; issues=[]
 for w,rel in SOURCES.items():
  p=BASE/rel;d=load(rel);manifest.append({'work':w,'path':str(p),'sha256':sha(p)})
  if w==2:continue
  if w==12:
   for i,r in enumerate(d['episodes']):
    jobs.append({'work':w,'id':str(i),'model':r['model'],'condition':r['scenario'],'branch':'','seed':r['seed'],'stage':'','n':1,'survived':int(r['termination']['time_out']),'seconds':r['duration_s'],'max_tilt':r['max_tilt_deg']})
   audits.append({'work':w,'cases':12,'episodes':len(d['episodes']),'raw_csv_audit':'embedded episode records; original signal tensor checks inherited'})
   continue
  rows=d.get('jobs',d.get('cases',d.get('results',[])))
  n_total=0;sha_checked=0;count_checked=0;maxdiff=defaultdict(float);epcache=defaultdict(list)
  for i,r in enumerate(rows):
   j=compact_case(w,r,i)
   rr=None
   if j['raw']:
    p=resolve(j['raw'])
    if not p.exists():issues.append({'work':w,'case':j['id'],'missing':str(p)})
    else:
     rawsha=sha(p)
     if j['raw_sha_expected'] and rawsha!=j['raw_sha_expected']:issues.append({'work':w,'case':j['id'],'raw_sha_mismatch':str(p)})
     if j['raw_sha_expected']:sha_checked+=1
     with p.open(encoding='utf-8-sig',newline='') as f:rr=list(csv.DictReader(f))
     manifest.append({'work':w,'path':str(p),'sha256':rawsha,'kind':'raw_episodes'})
   elif 'rows' in r:rr=r['rows']
   if rr is not None:
    count_checked+=1;n=len(rr);s=sum(truth(x.get('survival')) for x in rr)
    if j['n'] is not None and n!=j['n']:issues.append({'work':w,'case':j['id'],'count':n,'expected':j['n']})
    if j['survived'] is not None and s!=j['survived']:issues.append({'work':w,'case':j['id'],'survival':s,'expected':j['survived']})
    j['n']=n;j['survived']=s
    metric_keys={'seconds':['seconds'],'vx':['mean_vx_error_mps','mean_abs_vx_error_mps','mean_vx_error'],'xy':['mean_xy_velocity_error_mps'],'yaw':['mean_yaw_velocity_error_radps','mean_yaw_error'],'action':['mean_action_delta_l2','mean_action_delta']}
    for key,ks in metric_keys.items():
     vals=[number(pick(x,*ks)) for x in rr]
     if all(x is not None for x in vals):
      if not all(math.isfinite(x) for x in vals):raise ValueError((w,j['id'],key,'nonfinite'))
      v=sum(vals)/n
      if j.get(key) is not None:maxdiff[key]=max(maxdiff[key],abs(j[key]-v))
      j[key]=v
    # The curve is the proportion not yet terminated for any reason. Timeouts at 20s remain at endpoint.
    # Keep all cases; only labels separate smoke/calibration/confirmation.
    group=(j['model'],j['condition'],j['branch'],j['stage'],json.dumps(j['command']))
    if w in (5,14,15,16):group=(j['model'],j['condition'],j['branch'],j['stage'],json.dumps(j['command']))
    for x in rr:
     sec=number(x.get('seconds'));sv=truth(x.get('survival'))
     if sec is not None:epcache[group].append((sec,sv))
    if w==8:
     # Independently recompute every recorded continuous mean and abnormal terminal count.
     cmap={'mean_return':'return','mean_action_delta_l2':'mean_action_delta_l2','action_jump_rate_gt_1':'action_jump_rate_gt_1','mean_max_action_abs':'max_action_abs','mean_max_tilt_deg':'max_pre_step_tilt_deg','mean_sensor_perturbation_l2':'mean_sensor_perturbation_l2','mean_max_sensor_perturbation_l2':'max_sensor_perturbation_l2'}
     for a,b in cmap.items():
      vv=[float(x[b]) for x in rr]
      if not all(math.isfinite(x) for x in vv):raise ValueError(('pulse',a,'nonfinite'))
      maxdiff[a]=max(maxdiff[a],abs(sum(vv)/len(vv)-r[a]))
     for a,b in [('fell_over_count','fell_over'),('nan_state_rate','nan_state'),('out_of_terrain_rate','out_of_terrain_bounds')]:
      v=sum(truth(x[b]) for x in rr);expected=r[a]*(len(rr) if a.endswith('rate') else 1)
      if v!=expected:issues.append({'work':w,'case':j['id'],'mismatch':a})
   if j['n'] is None:j['n']=64 if w==11 else 0
   n_total+=j['n'];j['rate']=j['survived']/j['n'] if j['n'] and j['survived'] is not None else None
   if j.get('vx') is None and j.get('xy') is not None:j['vx_missing']=True
   jobs.append(j)
  for g,ep in epcache.items():
   curves.append({'work':w,'model':g[0],'condition':g[1],'branch':g[2],'stage':g[3],'command':g[4],'n':len(ep),
    't':[k*.1 for k in range(201)],'alive':[sum(sv or sec>k*.1+1e-8 for sec,sv in ep)/len(ep) for k in range(201)]})
  audits.append({'work':w,'cases':len(rows),'episodes':n_total,'raw_cases_recomputed':count_checked,'raw_sha_checked':sha_checked,'max_absolute_mean_residual':dict(maxdiff)})
 # Supplemental read-only evidence and offline curves, kept separate from closed-loop n.
 extra=['metrics_summary.json','metrics_history.csv','mechanism_audit/ppo_clone_baseline/repeatability.json',
 'curriculumtrap_pilot/results.json','curriculumtrap_pilot/matrix/results.json',
 'mechanism_audit/normalization_pilot/results.json','mechanism_audit/normalization_pilot/fixed_endpoint_results.json',
 'mechanism_audit/normalization_confirmation/results.json','mechanism_audit/replay_fork_pilot/results.json',
 'data_reanalysis_20261015_v2/analysis.json','data_reanalysis_20261015_v2/AUDIT.json',
 'fine_response/results/COMPLETION_VERIFICATION.json','fine_response/results/videos/manifest.json',
 'fine_response/results/VIDEO_DECODE_VERIFICATION.json','paper_report_2026-10-13/REPORT_DATA.json']
 extra_data={}
 for rel in extra:
  p=BASE/rel
  if p.exists():
   manifest.append({'work':0,'path':str(p),'sha256':sha(p),'kind':'support'})
   if p.suffix=='.json':extra_data[rel]=load(rel)
 dump(OUT/'data/extra.json',extra_data)
 dump(OUT/'data/cases.json',jobs);dump(OUT/'data/survival_curves.json',curves)
 dump(OUT/'data/input_manifest.json',manifest)
 dump(OUT/'data/AUDIT.json',{'checked_at':time.strftime('%Y-%m-%d %H:%M:%S'),'mode':'CPU existing-data analysis only','work_audits':audits,'issues':issues,'new_experiments':0,'new_training':0,'scope_note':'Raw CSV primary means/counts checked. N/T/Dose complete tensor/model audits inherited from prior recorded audit; no new model loads.'})
 if issues:raise RuntimeError('Evidence issues preserved in data/AUDIT.json; inspect before reporting')
 print(json.dumps({'cases':len(jobs),'audit':audits,'curve_groups':len(curves)},ensure_ascii=False),flush=True)

if __name__=='__main__':
 if sys.argv[1]=='extract':extract()
