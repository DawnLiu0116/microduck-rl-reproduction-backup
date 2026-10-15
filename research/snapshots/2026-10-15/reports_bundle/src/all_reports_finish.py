import csv,hashlib,html,json,os,re,shutil,sys,time,zipfile
from pathlib import Path
from collections import defaultdict,Counter
from PIL import Image,ImageOps,ImageDraw
from all_reports_build import BASE,OUT,SOURCES,TITLES,sha,load,dump,compact_case
from all_reports_content import REPORTS
H=html.escape
CSS='''body{margin:0;background:#f5f6f8;color:#20252b;font:16px/1.8 "Microsoft YaHei",system-ui,sans-serif}main{max-width:1160px;margin:0 auto;padding:36px 32px 80px;background:white}h1,h2,h3{color:#111;line-height:1.4}h1{font-size:29px;margin:8px 0 18px}h2{font-size:23px;margin-top:38px}h3{font-size:18px;margin-top:28px}p{margin:12px 0}a{color:#165a8a;overflow-wrap:anywhere}nav{padding:12px 0;border-bottom:1px solid #ddd}table{border-collapse:collapse;font-size:14px;width:100%;margin:18px 0}th,td{border:1px solid #d9d9d9;padding:7px 10px;text-align:left;overflow-wrap:anywhere}th{background:#eef2f6}td.num{text-align:right}figure{margin:28px 0 42px;padding-bottom:20px;border-bottom:1px solid #ddd}img{width:100%;height:auto;display:block;cursor:zoom-in}figcaption{font-size:14px;color:#394652;margin-top:12px}.note{padding:10px 16px;border-left:3px solid #8395a4;background:#f3f5f7}.small{font-size:13px;color:#52606b}.controls{display:flex;flex-wrap:wrap;gap:14px;padding:16px;background:#f1f4f7;position:sticky;top:0;z-index:2}select,input,button{font:inherit;max-width:100%;padding:6px}summary{cursor:pointer;font-weight:600}.scroll{overflow:auto;max-height:620px}svg{width:100%;height:auto;background:white;border:1px solid #ddd}footer{margin-top:40px;border-top:1px solid #ddd}.hidden{display:none!important}@media print{body,main{background:white}main{max-width:none;padding:0}.controls,nav,button{display:none}figure,table{break-inside:avoid}a{color:inherit}.scroll{max-height:none}img{max-height:230mm;object-fit:contain}}'''
def page(title,body,script=''):
 return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+H(title)+'</title><style>'+CSS+'</style><main>'+body+'</main>'+script+'</html>'
def table(headers,rows):return '<table><thead><tr>'+''.join('<th>'+H(str(x))+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+H(str(x))+'</td>' for x in r)+'</tr>' for r in rows)+'</tbody></table>'
def mdtable(headers,rows):return '| '+' | '.join(headers)+' |\n|'+'|'.join('---' for _ in headers)+'|\n'+''.join('| '+' | '.join(str(x).replace('|','/') for x in r)+' |\n' for r in rows)
def fmt(v,d=4):return '未记录' if v is None else (f'{v:.{d}f}' if isinstance(v,(float,int)) else str(v))
catalog=json.loads((OUT/'data/new_figure_catalog.json').read_text('utf-8'))
manifest=json.loads((OUT/'data/input_manifest.json').read_text('utf-8'))
jobs=json.loads((OUT/'data/cases.json').read_text('utf-8'))
aud=json.loads((OUT/'data/AUDIT.json').read_text('utf-8'))
extra=json.loads((OUT/'data/extra.json').read_text('utf-8'))
# Retain every numeric aggregate in the explorer, in addition to independently recomputed primary metrics.
for w,rel in SOURCES.items():
 if w in (2,12):continue
 d=load(rel);rows=d.get('jobs',d.get('cases',d.get('results',[])))
 jj=[j for j in jobs if j['work']==w and j.get('stage')!='repeat']
 assert len(jj)==len(rows),(w,len(jj),len(rows))
 for j,r in zip(jj,rows):
  j['recorded_metrics']={k:v for k,v in r.items() if isinstance(v,(int,float)) and not isinstance(v,bool) and (k.startswith('mean_') or k.endswith('_rate') or k.endswith('_count') or k.startswith('max_'))}
dump(OUT/'data/cases.json',jobs)
# Assign existing scientific figures to the work that produced them. No old figure is silently replaced.
groups={1:['plots'],3:['task_protocol_v2/four_model_final','official_comparison','unified_evaluation','mechanism_audit/acceptance_separation'],4:['sensor_fault_benchmark/independent_confirmation','sensor_fault_benchmark/four_model_confirmatory','sensor_fault_benchmark/preview'],5:['fine_response/results/plots','fine_response_assessment'],
6:['cpu_analysis_2026-10-12/plots'],7:['paper_report_2026-10-13/figures','paper_20261015_v1/figures'],
9:['mechanism_audit/full_width_order_pilot'],10:['mechanism_audit/full_width_clean_recovery'],
11:['curriculumtrap_pilot','mechanism_audit/normalization_pilot','mechanism_audit/normalization_confirmation','mechanism_audit/replay_fork_pilot','normalization_cpu_curve','mechanism_audit/normalizer_resume_probe','ordertrap_gate1'],
12:['mechanism_audit/sim_fall_filter','mechanism_audit/fall_filter_probe','adaptive_defense_pilot'],14:['preprocessing_integrity_v2/n/analysis'],15:['preprocessing_integrity_v2/t/analysis'],16:['effective_dose_response','data_reanalysis_20261015_v2']}
seen={};aliases=[]
for w,dirs in groups.items():
 for rel in dirs:
  for p in sorted((BASE/rel).rglob('*.png')):
   rp=p.relative_to(BASE).as_posix()
   if any(x in rp for x in ['/qa/','/tmp/','/smoke','diagnostics','partial_plot','channel_supplement','interruption']):continue
   if w==1 and any(x in p.name for x in ['storyboard','contact_sheet']):continue
   digest=sha(p)
   if digest in seen:aliases.append({'work':w,'title':p.stem.replace('_',' '),'source':rp,'same_as':seen[digest]});continue
   dest=f'original_figures/{w:02d}_{digest[:10]}_{p.name}'
   shutil.copy2(p,OUT/dest);seen[digest]=dest
   note='保留原实验图，不改变其样本、区间或协议定义。原图英文标注见本报告名词注释；探索、确认与历史快照不可混合累计。'
   if w==5:
    label=p.stem
    phase=('三新评估seed确认' if label.startswith('confirmation_') else '两个探索评估seed的幅度或机制扫描')
    channel=next((v for k,v in [('joint_velocity','关节速度'),('gravity_add','重力投影向量加性偏移'),('gyro','躯干角速度'),('imu_bias','IMU偏置'),('noise','传感段噪声')] if k in label),'联合传感段')
    note=f'{phase}。本图关注{channel}；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。'
    if 'delay' in label:note='横轴为额外观测延迟步或其对应毫秒，一控制步20ms；原生延迟仍保留，不能把该轴叫硬件端到端总时延。纵轴存活和寿命须同时看。探索与确认是不同seed队列，不合并为新样本。'
    if 'freeze' in label:note='横轴为观测冻结控制步数，一步20ms；名义持续时间与最后一帧实际陈旧年龄差一控制步。冻结越久不保证各模型排名不变；存活不等于任务成功。'
    if 'timing_duration' in label:note='横轴是每次脉冲持续控制步数，一步20ms；纵轴描述首回合结果。改变持续时间也改变计划暴露量，早终止会进一步改变实际暴露，不能当等剂量机制分离。'
    if 'timing_single_onset' in label:note='横轴为单次注入起点所在控制步；越靠后意味着机器人所处状态和剩余观察窗口不同。仅两个探索seed，不外推精确最危险时刻。'
    if 'timing_cluster' in label:note='比较脉冲在时间上的聚集安排。横轴为实际协议中的时间安排参数，不是新增训练轮数；暴露次数和早停的关系应结合原始条件查看。'
    if 'channel_combinations' in label:note='横轴是通道组合类别，纵轴为存活/寿命等结果。组合响应不等于各单通道损害之和；同alpha的输入范数不同，不能直接当协同作用的因果证明。'
    if 'nominal_' in label:note='固定命令扫描：Forward观察前向速度误差，Turning观察yaw误差及平移漂移。模型站住不等于跟随命令，目标速度变化时应按相应命令比较。'
   if w==6:note='历史中期CPU分析图，快照覆盖有限；最终完整数据与本轮重算另列，不把该快照冒充最终全部条件。'
   if 'normalization_cpu_curve' in rp:note='历史CPU部分曲线，旧插值队列仍暂停；未完成的格不补零，不混入正式GPU实验。'
   if 'fall_filter_probe' in rp:note='较早纯运动学探针，仅作机制背景，不计入本报告192个官方仿真首回合。'
   if w==7:note='既有论文选图，同一实验可能也在第5/15/16报告出现；只是不同表达，不增加样本。图中星号/误差条必须按原图解释。'
   if any(x in rp for x in ['official_comparison/','unified_evaluation/','acceptance_separation/','four_model_confirmatory/','/preview/','fine_response_assessment/','ordertrap_gate1/','adaptive_defense_pilot/']):note='历史补充图，保留用于追溯。本图的队列、幅度、分母或目的不同于本报告主表，不合并计数，不当成新增实验或最终主协议结论。'
   catalog.append({'work':w,'file':dest,'title':p.stem.replace('_',' '),'note':note,'kind':'retained_original','source':rp,'sha256':digest})
   manifest.append({'work':w,'path':str(p),'sha256':digest,'kind':'original_figure'})
# Two root-level legacy screening plots are separate from the later independent confirmation.
for name in ['sensor_fault_benchmark/confirmatory_summary.png','sensor_fault_benchmark/sensor_fault_heatmaps.png']:
 p=BASE/name;digest=sha(p)
 if digest not in seen:
  dest='original_figures/04_'+digest[:10]+'_'+p.name;shutil.copy2(p,OUT/dest);seen[digest]=dest
  catalog.append({'work':4,'file':dest,'title':p.stem.replace('_',' '),'note':'早期筛查或旧确认图，协议可能含启动脉冲，不能替代后来新seed确认或纯行走精细基准；不重复计入9216回合。','kind':'retained_original','source':name,'sha256':digest})
  manifest.append({'work':4,'path':str(p),'sha256':digest,'kind':'original_figure'})
 else:aliases.append({'work':4,'title':p.stem.replace('_',' '),'source':name,'same_as':seen[digest]})
# Video files: verify existing manifest against bytes; do not claim a new decode pass.
videos=extra['fine_response/results/videos/manifest.json'].get('videos',[])
video_rows=[];video_checks=[]
if isinstance(videos,dict):videos=list(videos.values())
for v in videos:
 candidates=[v[k] for k in ['path','file','video_file','output','output_file'] if k in v]
 pp=None
 for s in candidates:
  p=Path(str(s));p=(BASE/'fine_response/results/videos'/p) if not p.is_absolute() else p
  if not p.exists():
   from all_reports_build import resolve
   p=resolve(s)
  if p.exists():pp=p;break
 if pp:
  digest=sha(pp);expected=v.get('sha256',v.get('video_sha256'))
  video_checks.append({'path':str(pp),'sha256':digest,'expected':expected,'match':digest==expected if expected else None})
 video_rows.append([v.get('model',v.get('model_label','见manifest')),v.get('condition',v.get('alpha','见manifest')),str(pp) if pp else json.dumps(v,ensure_ascii=False)[:180]])
dump(OUT/'data/video_checks.json',video_checks)
# Aggregates per explicitly matched protocol cell. Stage and command remain in the grouping key.
agg=defaultdict(list)
for r in jobs:
 key=(r['work'],str(r['model']),r['condition'],r.get('branch',''),r.get('stage',''),json.dumps(r.get('command'),ensure_ascii=False))
 agg[key].append(r)
allgroups=[]
for key,rr in agg.items():
 n=sum(r['n'] for r in rr);ss=sum(r['survived'] for r in rr if r.get('survived') is not None)
 g={'work':key[0],'model':key[1],'condition':key[2],'branch':key[3],'stage':key[4],'command':key[5],'n':n,'survived':ss}
 for field in ['seconds','vx','xy','yaw','action']:
  valid=[r for r in rr if r.get(field) is not None]
  g[field]=sum(r[field]*r['n'] for r in valid)/sum(r['n'] for r in valid) if valid else None
 allgroups.append(g)
dump(OUT/'data/grouped_results.json',allgroups)
def rows_for(w):
 return [[g['model']+('/'+g['branch'] if g['branch'] else ''),g['condition'],g['stage'],f"{g['survived']}/{g['n']}",fmt(100*g['survived']/g['n'],2)+'%',fmt(g['seconds']),fmt(g['vx']),fmt(g['xy'])] for g in allgroups if g['work']==w]
headers=['模型或分支','条件','阶段','存活分子/分母','存活率','平均寿命s','vx误差m/s','XY误差m/s']
reports=[]
for w in range(1,17):
 c=REPORTS[w];title=f'{w:02d} {TITLES[w-1]}研究报告'
 body='<nav><a href="../index.html">总图册</a>　<a href="../data_explorer.html">全数据浏览器</a>　<a href="../ALL_REPORTS.md">合订文字版</a></nav><h1>'+H(title)+'</h1>'
 md='# '+title+'\n\n'+c['conclusion']+'\n\n'
 body+='<p>'+H(c['conclusion'])+'</p><p class="small">整理日期 2026年10月15日　本轮仅分析已有数据 不新增实验</p>'
 for head,key in [('工作范围','scope'),('我们如何完成这项工作','method')]:
  body+='<h2>'+head+'</h2><p>'+H(c[key])+'</p>';md+='## '+head+'\n\n'+c[key]+'\n\n'
 body+='<h2>现有结果及解释</h2>';md+='## 现有结果及解释\n\n'
 for i,p in enumerate(c['findings'],1):body+='<p>'+str(i)+'. '+H(p)+'</p>';md+=f'{i}. {p}\n\n'
 rr=rows_for(w)
 if w==1:
  d=load('metrics_summary.json');rr=[['42',4000,393216000,d['final']['Train/mean_reward']],['123',4000,393216000,'见完整原日志曲线'],['2026',4001,393314304,'父/恢复分段见图']];hh=['来源seed','最终谱系rollout','历史样本count','训练平均回报']
 elif w==2:
  d=load(SOURCES[2]);rr=[[k,len(v['checkpoints']),v['checkpoints'][0]['iter'],v['checkpoints'][-1]['iter']] for k,v in d['runs'].items()];hh=['真实训练目录','已保存checkpoint数','首标签','末标签']
 elif w==7:rr=video_rows;hh=['模型','视频条件','可追溯文件']
 else:hh=headers
 if rr:
  body+='<h2>完整结果表</h2><p class="small">阶段、条件和命令分别保留。未记录的指标显示未记录，不按0填充。表内百分比为存活，不是任务成功率。</p><details'+(' open' if len(rr)<=32 else '')+'><summary>查看本工作全部'+str(len(rr))+'个汇总单元</summary><div class="scroll">'+table(hh,rr)+'</div></details>'
  md+='## 完整结果表\n\n'+mdtable(hh,rr)+'\n'
 body+='<h2>图表及读图注释</h2>';md+='## 图表及读图注释\n\n'
 for p in c['notes']:body+='<p class="note">读图注释 '+H(p)+'</p>';md+='> 读图注释：'+p+'\n\n'
 body+='<p class="note">英文坐标速查：survival 是规定时长存活，不是任务完成率；duration / seconds 是首回合有效寿命；vx 是前向速度，XY 是平面速度；yaw 是绕竖直轴旋转；MSE 是动作拟合平方误差；pp 是百分点，例如90%到80%为下降10个百分点。完整解释见<a href="../READING_GUIDE.md">读图指南</a>。</p>'
 md+='> 英文坐标速查：survival=规定时长存活；duration/seconds=首回合有效寿命；vx=前向速度；XY=平面速度；yaw=绕竖直轴旋转；MSE=动作拟合平方误差；pp=百分点。完整解释见[读图指南](../READING_GUIDE.md)。\n\n'
 ff=[f for f in catalog if f['work']==w]
 for a in aliases:
  if a['work']==w and a['same_as'] not in {f['file'] for f in ff}:
   ff.append({'file':a['same_as'],'title':a['title'],'note':'本图与另一报告引用同一已有图文件，复用图像不增加实验样本。请按本报告协议与原图标注理解，不能把论文选图和原实验图重复计数。'})
 for i,f in enumerate(ff,1):
  link='../'+f['file'];body+='<figure><h3>图'+str(i)+' '+H(f['title'])+'</h3><a href="'+H(link)+'" target="_blank"><img loading="lazy" src="'+H(link)+'" alt="'+H(f['title'])+'"></a><figcaption>'+H(f['note'])+'</figcaption></figure>'
  md+=f"### 图{i} {f['title']}\n\n![{f['title']}]({link})\n\n{f['note']}\n\n"
 body+='<h2>限制与不能支持的结论</h2><p>'+H(c['limits'])+'</p>';md+='## 限制与不能支持的结论\n\n'+c['limits']+'\n\n'
 srcs=[m for m in manifest if m.get('work')==w and m.get('kind') not in ('raw_episodes','original_figure')]
 body+='<h2>证据入口与复核范围</h2><p>逐文件SHA及原始路径见<a href="../data/input_manifest.json">输入清单</a>；本轮复算范围见<a href="../data/AUDIT.json">数据审计</a>。下列输入在生成后再次核对未改。</p>'
 md+='## 证据入口与复核范围\n\n输入清单与SHA：[input_manifest.json](../data/input_manifest.json)。本轮计数/均值复算：[AUDIT.json](../data/AUDIT.json)。\n\n'
 for s in srcs:body+='<p class="small">'+H(s['path'])+'<br>SHA256 '+s['sha256']+'</p>';md+='- '+s['path']+'　SHA256 '+s['sha256']+'\n'
 body+='<h2>这项工作的价值</h2><p>'+H(c['value'])+'</p>';md+='\n## 这项工作的价值\n\n'+c['value']+'\n'
 slug=f'{w:02d}_report';(OUT/'reports'/f'{slug}.html').write_text(page(title,body),'utf-8');(OUT/'reports'/f'{slug}.md').write_text(md,'utf-8')
 reports.append({'work':w,'title':TITLES[w-1],'html':f'reports/{slug}.html','md':f'reports/{slug}.md','figures':len(ff),'groups':len(rr),'scope':c['scope'],'conclusion':c['conclusion'],'value':c['value']})
dump(OUT/'data/report_index.json',reports)
# Full chart atlas, searchable/filterable; no external JavaScript or network dependency.
body='<h1>MicroDuck全部工作图册与独立报告</h1><p>按16项工作分别整理。包含完整训练日志、正式评估、有限机制pilot及原图；保持协议分组，不新增实验，不恢复取消补测。</p><p><a href="data_explorer.html">打开全数据浏览器</a>　<a href="ALL_REPORTS.md">合订文字版</a>　<a href="COVERAGE.md">覆盖范围与未保存数据说明</a></p>'
body+='<h2>16份独立报告</h2><p class="small">各报告图数包含共享图的引用，不能相加当独立图或新增样本；总图册保留192份去重后的图像。</p>'+table(['工作','范围','图数','入口'],[[r['title'],r['scope'],r['figures'],r['html']] for r in reports]).replace('<td>reports/','<td>reports/')
# Replace plain filename cells with actual local links.
for r in reports:body=body.replace('<td>'+r['html']+'</td>','<td><a href="'+r['html']+'">阅读报告</a> · <a href="'+r['md']+'">Markdown</a></td>')
body+='<h2>全部曲线与图表</h2><p>共'+str(len(catalog))+'张图。先选工作，再逐图阅读图注；点击可打开原尺寸。全部任务的数值、指标选择和存续曲线见全数据浏览器。</p><div class="controls"><label>工作 <select id="work"><option value="all">全部工作</option>'+''.join(f'<option value="{i}">{i:02d} {H(t)}</option>' for i,t in enumerate(TITLES,1))+'</select></label><label>搜索 <input id="query" placeholder="关键词 如 paired delay replay"></label><span id="shown"></span></div>'
for i,f in enumerate(catalog,1):
 memberships=sorted({f['work']}|{a['work'] for a in aliases if a['same_as']==f['file']})
 body+=f'<figure class="chart" data-work="{",".join(map(str,memberships))}" data-search="{H(f["title"].lower())}"><h3>{i:03d}　{f["work"]:02d} {H(TITLES[f["work"]-1])}　{H(f["title"])}</h3><a href="{H(f["file"])}" target="_blank"><img loading="lazy" src="{H(f["file"])}" alt="{H(f["title"])}"></a><figcaption>{H(f["note"])}</figcaption></figure>'
script='''<script>function filter(){let w=document.querySelector('#work').value,q=document.querySelector('#query').value.toLowerCase(),n=0;document.querySelectorAll('.chart').forEach(e=>{let yes=(w==='all'||e.dataset.work.split(',').includes(w))&&e.dataset.search.includes(q);e.classList.toggle('hidden',!yes);n+=yes});document.querySelector('#shown').textContent='当前显示 '+n+' 张'}document.querySelector('#work').onchange=filter;document.querySelector('#query').oninput=filter;filter();</script>'''
(OUT/'index.html').write_text(page('MicroDuck全部工作图册',body,script),'utf-8')
# Machine-readable explorer embeds the data to work when opened directly from disk.
curves=json.loads((OUT/'data/survival_curves.json').read_text('utf-8'))
explorer='<nav><a href="index.html">返回总图册与16报告</a></nav><h1>全部已执行任务数据浏览器</h1><p>离散点图覆盖所有记录任务，可选择任意已记录数值聚合指标；下方存续曲线保持单一条件，不混合不同故障。完整raw CSV路径保存在任务数据中。</p><div class="controls"><label>工作 <select id="w">'+''.join(f'<option value="{w}">{w:02d} {H(TITLES[w-1])}</option>' for w in sorted(set(r['work'] for r in jobs)))+'</select></label><label>模型 <select id="model"></select></label><label>指标 <select id="metric"></select></label></div><p id="count"></p><svg id="plot" viewBox="0 0 1200 430"></svg><p class="note">横轴仅为所选任务的离散记录编号，不是时间或剂量；没有把类别点连成过程线。纵轴按字段原单位。原记录指标和本轮重算主要指标分开命名；未记录项不补零。</p><details><summary>查看当前筛选的全部任务</summary><div class="scroll" id="rows"></div></details><h2>单条件首回合存续曲线</h2><p>20秒超时是右侧观察边界，不算跌倒。0.1秒显示网格，不外推未保存过程。</p><label>曲线 <select id="curve"></select></label><svg id="survival" viewBox="0 0 1200 430"></svg><p id="curveNote"></p>'
js='''<script>const D=DATA,C=CURVES,T=TITLES;const $=x=>document.getElementById(x);function esc(s){return String(s??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}function chart(id,points,xmax,ymin,ymax,xtitle,ytitle,line=false){let a=80,b=25,c=335,W=1090,H=310,dx=x=>a+(x/(xmax||1))*W,dy=y=>c-(y-ymin)/(ymax-ymin||1)*H;let s='<rect width="1200" height="430" fill="white"/>';for(let i=0;i<=5;i++){let y=ymin+(ymax-ymin)*i/5;s+=`<line x1="${a}" y1="${dy(y)}" x2="1170" y2="${dy(y)}" stroke="#ddd"/><text x="70" y="${dy(y)+4}" text-anchor="end" font-size="13">${y.toPrecision(4)}</text>`;let x=xmax*i/5;s+=`<text x="${dx(x)}" y="360" text-anchor="middle" font-size="13">${x.toFixed(1)}</text>`}s+=`<text x="600" y="400" text-anchor="middle" font-size="16">${esc(xtitle)}</text><text x="15" y="16" font-size="14">${esc(ytitle)}</text>`;if(line)s+='<polyline fill="none" stroke="#175f97" stroke-width="2" points="'+points.map(p=>dx(p[0])+','+dy(p[1])).join(' ')+'"/>';else points.forEach(p=>s+=`<circle cx="${dx(p[0])}" cy="${dy(p[1])}" r="3.5" fill="#175f97"><title>${esc(p[2])}</title></circle>`);$(id).innerHTML=s}function value(r,k){return k.startsWith('recorded:')?r.recorded_metrics?.[k.slice(9)]:r[k]}function setup(){let rows=D.filter(r=>r.work==$('w').value),models=[...new Set(rows.map(r=>String(r.model)))].sort();$('model').innerHTML='<option value="all">全部</option>'+models.map(s=>`<option>${esc(s)}</option>`).join('');let keys=['rate','seconds','vx','xy','yaw','action','max_tilt'];rows.forEach(r=>Object.keys(r.recorded_metrics||{}).forEach(k=>keys.push('recorded:'+k)));keys=[...new Set(keys)].filter(k=>rows.some(r=>Number.isFinite(value(r,k))));$('metric').innerHTML=keys.map(k=>`<option value="${k}">${esc(({rate:'存活比例 0至1',seconds:'平均寿命 s',vx:'vx绝对误差 m/s',xy:'XY误差 m/s',yaw:'yaw误差 rad/s',action:'动作差 L2',max_tilt:'最大倾角 deg'})[k]||k)}</option>`).join('');let cc=C.map((r,i)=>[r,i]).filter(([r])=>r.work==$('w').value);$('curve').innerHTML=cc.map(([r,i])=>`<option value="${i}">${esc(r.model+' '+r.condition+' '+r.branch+' '+r.stage+' n='+r.n)}</option>`).join('');draw();scurve()}function draw(){let rr=D.filter(r=>r.work==$('w').value&&($('model').value==='all'||String(r.model)==$('model').value)),k=$('metric').value,p=rr.map((r,i)=>[i,value(r,k),r.model+' '+r.condition+' seed='+r.seed+' id='+r.id]).filter(r=>Number.isFinite(r[1]));if(p.length){let v=p.map(r=>r[1]),lo=Math.min(...v),hi=Math.max(...v),pad=(hi-lo)*.05||.01;chart('plot',p,rr.length-1,lo-pad,hi+pad,'Case index',k)}else $('plot').innerHTML='';$('count').textContent=rr.length+' 条任务记录；'+p.length+' 个有限实测指标值（未记录不补零）。';$('rows').innerHTML='<table><tr><th>id</th><th>模型</th><th>条件及阶段</th><th>seed</th><th>分子/分母</th><th>当前指标</th></tr>'+rr.map(r=>`<tr><td>${esc(r.id)}</td><td>${esc(r.model+' '+(r.branch||''))}</td><td>${esc(r.condition+' '+(r.stage||''))}</td><td>${esc(r.seed)}</td><td>${r.survived}/${r.n}</td><td>${Number.isFinite(value(r,k))?value(r,k).toPrecision(6):'未记录'}</td></tr>`).join('')+'</table>'}function scurve(){let r=C[$('curve').value];if(!r){$('survival').innerHTML='';$('curveNote').textContent='该工作无可用终止时间曲线，不能从终点指标虚构过程。';return}chart('survival',r.t.map((x,i)=>[x,r.alive[i]*100]),20,0,100,'First-episode time (s)','Not yet terminated (%)',true);$('curveNote').textContent=r.model+' / '+r.condition+' / '+r.stage+' / n='+r.n+'。此为固定条件合并评估seed的描述性比例，不是训练总体置信区间。'}$('w').onchange=setup;$('model').onchange=draw;$('metric').onchange=draw;$('curve').onchange=scurve;setup();</script>'''
js=js.replace('DATA',json.dumps(jobs,ensure_ascii=False)).replace('CURVES',json.dumps(curves,ensure_ascii=False)).replace('TITLES',json.dumps(TITLES,ensure_ascii=False))
(OUT/'data_explorer.html').write_text(page('MicroDuck全部任务数据浏览器',explorer,js),'utf-8')
# Coverage and combined source. These are research scope statements, not invented missing trajectories.
cover='''# 覆盖范围与数据边界\n\n本包覆盖用户列出的16项工作，不新增实验。曲线来自现存TensorBoard、正式训练metrics、逐回合终止时间、离线MSE时点及原图。\n\n- 三来源原训练：解析四个真实event文件的46个scalar tag。2026按已保存来源重建谱系，不把丢弃尾段并入最终预算。\n- T续训：24分支各200个正式rollout，共4800个真实逐轮训练记录；没有用被重做的stdout片段重复计数。\n- 正式及pilot闭环：所有已执行case的计数和可用聚合指标可在data_explorer.html查询；已有数值聚合均保留，不只选论文主指标。\n- 精细基准2072项的九阶段全保留，包括smoke与calibration，但不混进确认样本；612确认项是总2072的子集。\n- 原零更新512回合与额外128回合重复合并为该工作640回合，但重复不是新增训练。\n- 脉冲拆分40项2560回合本轮完成独立CSV复算，只更新本包报告状态，不覆盖旧报告。\n- 每工作单独报告，结尾为价值；总体结论不按不同协议回合加总做统计推断。\n\n## 无法由现有数据补画的部分\n\n不是所有回合都有完整姿态、动作和机械遥测。终止时间能画首回合存续曲线，不能重建未保存的逐帧信号。只有两端测量的恢复图不补中间点；未过门槛的故障case不填0；有限网格不拟合未采样的阈值。单seed诊断保留单seed身份。\n\n## 旧材料的保留方式\n\n原图36张和论文选图可能复用同一数据，均不增加样本。CPU部分曲线和中期快照明确标为历史。相同字节原图只复制一次，别名关系在data/figure_aliases.json。图册覆盖本16项工作已定位的图与数据，不声称穷尽整个磁盘的每个调试截图。\n\n## 执行边界\n\n1944项补测已取消，实测0；63run及旧CPUworker仍暂缓；没有训练、GPU评估、实体动作、上传或改驱动。新报告未自动写入旧不可变实验备份，也没有覆盖之前带注释的总档案。\n'''
(OUT/'COVERAGE.md').write_text(cover,'utf-8')
allmd='# MicroDuck十六项工作研究报告合订本\n\n[全部图册](index.html) · [全部任务浏览器](data_explorer.html)\n\n'
for r in reports:allmd+='- ['+r['title']+']('+r['md']+')\n'
for r in reports:
 text=(OUT/r['md']).read_text('utf-8').replace('(../figures/','(figures/').replace('(../original_figures/','(original_figures/').replace('(../data/','(data/')
 allmd+='\n---\n\n'+text.replace('(../READING_GUIDE.md)','(READING_GUIDE.md)')
(OUT/'ALL_REPORTS.md').write_text(allmd,'utf-8')
dump(OUT/'data/figure_catalog.json',catalog);dump(OUT/'data/figure_aliases.json',aliases);dump(OUT/'data/input_manifest.json',manifest)
# Visual QA contact sheets for every new figure, plus metadata needed for manual review.
qa=OUT/'qa';qa.mkdir(exist_ok=True)
new=[f for f in catalog if f['kind']=='new_existing_data_plot']
for k in range(0,len(new),9):
 sheet=Image.new('RGB',(1800,1500),'#e8eaed');draw=ImageDraw.Draw(sheet)
 for i,f in enumerate(new[k:k+9]):
  with Image.open(OUT/f['file']) as im:
   im=ImageOps.contain(im.convert('RGB'),(580,450))
   x=(i%3)*600+10;y=(i//3)*500+25;sheet.paste(im,(x,y));draw.text((x,y-20),Path(f['file']).name,fill='black')
 sheet.save(qa/f'contact_{k//9+1:02d}.jpg',quality=92)
print(json.dumps({'reports':len(reports),'figures':len(catalog),'new_figures':len(new),'original_unique':len(catalog)-len(new),'cases':len(jobs),'video_sha_checked':len(video_checks),'video_matches':sum(v['match'] is True for v in video_checks)},ensure_ascii=False))
