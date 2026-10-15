import csv,hashlib,html,json,math,os,re,shutil,time,zipfile
from pathlib import Path
from collections import Counter
from html.parser import HTMLParser
from PIL import Image,ImageOps,ImageDraw
from all_reports_build import BASE,OUT,SOURCES,TITLES,load,sha,dump
guide='''# 图表阅读指南\n\n## 先分清图在回答什么\n\n训练曲线表示学习过程，固定任务图表示命令能力，故障曲线表示特定注入下的首回合响应，MSE曲线表示学生对teacher动作的离线拟合。它们不能直接合成同一个总分，也不能把回合数合并成独立训练重复。\n\n## 英文坐标和单位\n\n| 英文 | 中文读法 | 怎么看 |\n|---|---|---|\n| iteration | 原日志迭代编号 | 2026在恢复边界重复标签，不能只按最大编号算实际rollout |\n| rollout | 一批PPO采样及更新 | 原训练每批4096×24条转移；不等于一个完整回合 |\n| elapsed time | 各运行日志的经过秒数 | 恢复段时钟单独记录，不与迭代轴混淆 |\n| mean reward | 训练平均回报 | 受课程、奖励权重和命令分布影响，不是安全分数 |\n| mean_reward_per_step | 每环境步的平均奖励 | T训练记录定义，不能直接与原4000轮mean_reward数值比较 |\n| Episode_Reward | 训练奖励分项 | 按代码权重缩放，没有跨分项统一物理尺度 |\n| Episode_Termination | 训练日志终止聚合 | 不可直接乘100解释为固定评估跌倒率 |\n| survival / success_rate | 规定观察时长存活比例 | 本项目success旧字段实际为存活，不是任务完成率 |\n| not yet terminated | 尚未发生终止的比例 | 从首回合终止时间重算，20秒超时不是死亡 |\n| mean seconds / duration | 首回合有效寿命秒 | 早终止越多通常越低；要与速度误差同时看 |\n| vx error | 前向速度绝对误差 m/s | 通常越低越好，但早停可能截短统计 |\n| XY velocity error | 平面速度向量误差 m/s | 不等同单独vx误差 |\n| yaw error | 竖直轴旋转速度误差 rad/s | Turning还要看平移漂移，不能只看yaw |\n| action delta L2 | 相邻网络动作的L2变化 | 不等于真实电机力矩或损伤 |\n| max tilt | 最大倾角 度 | 注意pre-step记录可能漏终止物理帧 |\n| MSE | 学生与teacher动作的平方误差 | 离线低误差不保证闭环能走 |\n| pp | 百分点 | 90%到80%为-10个百分点，不是-10%相对变化 |\n| count | 归一化历史样本计数 | 来源账本；900的virtual mass不是实际收集量 |\n| w | 人工矩合并的新部分有效权重 | 不是新增PPO训练步数 |\n| p | 新部分内的污染比例 | p=0为同w clean，对照不等于原模型 |\n| F / U | 统计冻结 / 沿历史追加 | F仍训练网络权重，不是整个模型冻结 |\n| T0 / TC / TI | clean / 共同旋转 / 相反旋转 | 仅T真实PPO干预合同 |\n\n## 误差条不是同一种东西\n\nWilson区间描述固定模型在给定回合分布中的存活比例；回合bootstrap有它自身重采样单位；三个评估seed的极值竖线只是范围，不是95%训练总体置信区间。11个三seed均下降的剂量格不是11个统计显著发现，共享clean与嵌套样本使网格相关。\n\n## 读图顺序\n\n先确认模型来源和协议，再看分母及评估seed，随后对照存活、寿命、跟踪误差，最后阅读反证和限制。不同故障的同alpha不代表等输入范数；冻结步数与额外延迟也不代表硬件总时延。类别点不连线，有限端点连线不补测量，未测不填0。\n'''
(OUT/'READING_GUIDE.md').write_text(guide,'utf-8')
manifest=json.loads((OUT/'data/input_manifest.json').read_text('utf-8'))
unique={m['path']:m for m in manifest};mismatches=[];raw_count=0;raw_rows=0
for name,m in unique.items():
 p=Path(name)
 if sha(p)!=m['sha256']:mismatches.append(name)
 if m.get('kind')=='raw_episodes':
  with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
  key=next((k for k in ['episode','env_id'] if k in rows[0]),None)
  if key and len({r[key] for r in rows})!=len(rows):raise ValueError(('duplicate first-episode identifier',name))
  raw_count+=1;raw_rows+=len(rows)
assert not mismatches,mismatches
jobs=json.loads((OUT/'data/cases.json').read_text('utf-8'));curves=json.loads((OUT/'data/survival_curves.json').read_text('utf-8'))
expected={3:(48,6144),4:(72,9216),5:(2072,171328),6:(32,4096),8:(40,2560),9:(40,2560),10:(60,3840),11:(8,512),12:(192,192),13:(10,640),14:(336,43008),15:(528,67584),16:(900,115200)}
coverage=[]
for w,(count,n) in expected.items():
 rr=[r for r in jobs if r['work']==w];assert (len(rr),sum(r['n'] for r in rr))==(count,n)
 assert len({r['id'] for r in rr})==len(rr)
 coverage.append({'work':w,'indexed_records':count,'episodes':n,'note':'192 episode records from 12 physical cases' if w==12 else ''})
for r in curves:
 assert len(r['t'])==len(r['alive'])==201
 assert all(0<=x<=1 for x in r['alive'])
 assert all(a>=b for a,b in zip(r['alive'],r['alive'][1:])),r
 rr=[j for j in jobs if j['work']==r['work'] and str(j['model'])==str(r['model']) and j['condition']==r['condition'] and j.get('branch','')==r['branch']]
 if r['work'] not in (4,8,11,13):rr=[j for j in rr if j.get('stage','')==r['stage'] and json.dumps(j.get('command'))==r['command']]
 assert sum(j['n'] for j in rr)==r['n'],(r['work'],r['model'],r['condition'])
 assert abs(r['alive'][-1]-sum(j['survived'] for j in rr)/r['n'])<1e-12,(r['work'],r['model'],r['condition'],'endpoint')
assert sum(r['n'] for r in jobs if r['work']==5 and r['stage']=='confirmation')==78336
assert len([r for r in jobs if r['work']==5 and r['stage']=='confirmation'])==612
for model,expected_n in [('seed42_iter3999',119),('seed123_iter3999',22)]:assert sum(r['survived'] for r in jobs if r['work']==8 and r['model']==model and r['condition']=='walking_all')==expected_n
cat=json.loads((OUT/'data/figure_catalog.json').read_text('utf-8'))
for f in cat:
 with Image.open(OUT/f['file']) as im:im.verify()
class Links(HTMLParser):
 def __init__(self):super().__init__();self.targets=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ('href','src'):self.targets.append(v)
bad=[]
for p in [OUT/'index.html',OUT/'data_explorer.html',*sorted((OUT/'reports').glob('*.html'))]:
 parser=Links();parser.feed(p.read_text('utf-8'))
 for target in parser.targets:
  if target.startswith(('http:','https:','data:','#','javascript:')):continue
  if not (p.parent/html.unescape(target)).resolve().exists():bad.append((str(p),target))
assert not bad,bad
browser=json.loads((OUT/'qa/browser_QA.json').read_text('utf-8'));assert browser['complete']
# Add sources used for training curves and check those bytes too.
train=json.loads((OUT/'data/training_scalars.json').read_text('utf-8'))
T=json.loads((OUT/'data/T_training_records.json').read_text('utf-8'))
for m in train['sources']+T['sources']:
 p=Path(m['path'].replace('/mnt/d/','D:/'));assert sha(p)==m['sha256']
 unique[str(p)]={'path':str(p),'sha256':m['sha256'],'kind':'training_curve_source'}
dump(OUT/'data/input_manifest.json',list(unique.values()))
# Preserve reproducible report code inside the new package; no experiment source is edited.
src=OUT/'src';src.mkdir(exist_ok=True)
for name in ['all_reports_build.py','all_reports_plot.py','all_reports_extra_plots.py','all_reports_correct.py','all_reports_content.py','all_reports_finish.py','all_reports_verify.py','all_reports_browser_qa.cjs']:
 shutil.copy2(Path(__file__).parent/name,src/name)
# First-screen visual QA for every report is collated for review, separate from deliverable content.
for b in range(0,16,4):
 sheet=Image.new('RGB',(1400,1100),'#ddd');draw=ImageDraw.Draw(sheet)
 for k in range(4):
  n=b+k+1
  with Image.open(OUT/'qa'/f'report_{n:02d}.png') as im:im=ImageOps.contain(im.convert('RGB'),(690,500))
  x=(k%2)*700;y=(k//2)*550+25;sheet.paste(im,(x,y));draw.text((x,y-20),f'Report {n:02d}',fill='black')
 sheet.save(OUT/'qa'/f'reports_contact_{b//4+1}.jpg',quality=94)
status={'complete':True,'reports':16,'figures':len(cat),'new_existing_data_figures':sum(f['kind']=='new_existing_data_plot' for f in cat),'retained_original_figures':sum(f['kind']=='retained_original' for f in cat),'source_files_sha_rechecked':len(unique),'raw_csv_unique_files_rechecked':raw_count,'raw_rows_rechecked':raw_rows,'survival_curve_groups_checked':len(curves),'work_coverage':coverage,'new_experiments':0,'new_training':0,'source_mutations':0,'video_sha_matches':12,'video_decode':'inherited prior verification; no new decode claim','scope':'No inferred unrecorded telemetry; cancelled supplement remains 0.'}
dump(OUT/'VERIFICATION.json',status)
(OUT/'README.md').write_text('# MicroDuck全部工作报告\n\n先打开[index.html](index.html)：16份独立报告和192张图。\n\n[data_explorer.html](data_explorer.html)可离线选择工作、模型、全部已记录数值指标和1692条单条件存续曲线；无需网络。\n\n[ALL_REPORTS.md](ALL_REPORTS.md)为合订文字版；每项报告末尾均有价值说明。[READING_GUIDE.md](READING_GUIDE.md)解释英文坐标，[COVERAGE.md](COVERAGE.md)说明范围和未保存数据。[VERIFICATION.json](VERIFICATION.json)为最终核验。\n\n源实验与之前注释总档案均未覆盖。取消补测、暂停队列、每日记录保持原状态。\n','utf-8')
files=[]
for p in sorted(OUT.rglob('*')):
 if p.is_file() and p.name not in ['PACKAGE_MANIFEST.json','MicroDuck_All_Work_Reports.zip'] and 'qa' not in p.relative_to(OUT).parts:
  files.append({'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
dump(OUT/'PACKAGE_MANIFEST.json',{'complete':True,'files':files,'note':'This is a new report package, not a claim that the old immutable experiment backup contains it.'})
with zipfile.ZipFile(OUT/'MicroDuck_All_Work_Reports.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for r in files:z.write(OUT/r['path'],r['path'])
 z.write(OUT/'PACKAGE_MANIFEST.json','PACKAGE_MANIFEST.json')
with zipfile.ZipFile(OUT/'MicroDuck_All_Work_Reports.zip') as z:assert z.testzip() is None
print(json.dumps(status,ensure_ascii=False));print('ZIP', (OUT/'MicroDuck_All_Work_Reports.zip').stat().st_size)
