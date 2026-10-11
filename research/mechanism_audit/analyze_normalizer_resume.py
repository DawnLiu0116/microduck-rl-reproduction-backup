"""Report only measured contract results, no safety/novelty claims."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent/'normalizer_resume_probe'
data=json.loads((OUT/'results.json').read_text())
assert data['complete'] and data['original_models_unchanged']
rows=data['rows']
assert len(rows)==len({(r['seed'],r['branch']) for r in rows})==12
assert all(r['strict_load_accepted'] and r['eval_update_unchanged'] for r in rows)
original=[r for r in rows if r['branch']=='original']
var=[r for r in rows if r['branch']=='var_only_1pct']
count=[r for r in rows if r['branch']=='count_zero']
assert all(r['pre_contract']['contract_passed'] for r in original)
assert all(r['pre_vs_original']['exact_equal'] and not r['pre_contract']['coherent'] for r in var)
table='\n'.join(f"| {r['seed']} | {r['branch']} | {r['pre_vs_original']['max_abs']:.8g} | {r['post_vs_original_post']['max_abs']:.8g} | {r['post_vs_original_post']['mean_abs']:.8g} | {'通过' if r['pre_contract']['contract_passed'] else '拒绝'} |" for r in rows)
report=f'''# 归一化恢复状态：确认的机制，不是已成立的安全攻击

日期：2026-10-09。协议执行前固定于 `../NORMALIZER_RESUME_PROTOCOL.md`。

## 结论

1. 三个原始最终checkpoint的 `_std == sqrt(_var)` 最大误差为0；全部正常。原checkpoint文件SHA在执行前后相同。
2. 实际EmpiricalNormalization的strict加载接受 `_var` 与 `_std` 不一致的内存副本。只把_var乘1.01而保留_std，当前推理完全相同；eval调用update也不变。train下显式更新一次统计后，动作开始变化。
3. 一致性检查可在加载时识别上述var-only故障；但它不能识别数学上自洽的错误统计，也不能证明count来源可信。
4. 清零count的副本当前推理也完全相同，但下一次256样本统计更新会替换历史，带来更大动作变化。这是刻意丢失历史的预期结果，不是微小扰动或官方自动行为。
5. 未做闭环安全、真实PPO恢复或新颖性验证；没有证据说明当前原模型存在漏洞利用或投毒。

## 代码因果链

`state_dict`分别保存_mean/_var/_std/count；forward仅用_mean和_std；update先用_var更新总体方差，随后 `_std = sqrt(_var)`。strict检查key/shape并不验证这些buffer的数学关系。eps/until是构造时普通属性，不随这些buffer自动恢复，需单独记录配置。

可概括为：**当前函数等价，不代表恢复更新的状态等价。** 用一次普通推理验收，无法覆盖所有后续训练状态。

上述var/std事实并非全新算法发现：前次审计已识别独立buffer，本次新增的是三个实际模型上的延迟显现对照与显式验收测试。

## 测量

三个模型分别在同一teacher42数据留出环境的2048帧上测量。一次统计更新使用前16个时刻×前16环境=256帧，与留出环境不重叠。没有优化器、梯度或权重更新；不能叫完成了一步PPO。

表内是14维原始动作输出的逐元素最大/平均绝对差，**不是电机角度、姿态或跌倒指标**。Post差异相对“原始分支也做同一次统计更新”比较，排除了正常累计更新本身。

| 模型 | 内存分支 | 更新前最大差 | 更新后最大差 | 更新后平均差 | 加载前数学合同 |
|---|---|---:|---:|---:|---|
{table}

`coherent_1pct`同时改变var与std，所以影响即刻出现，是即时尺度改变对照；它仍通过数学合同。`count_zero`并非正常原模型：明确由我们在内存中置0，它在下一次统计更新时舍弃既有历史。

## 什么可做、什么不应宣称

- 可做：在checkpoint加载/恢复前检查有限值、非负方差/std、count类型与范围、std与sqrt(var)的容差；单独核对eps/until、输入布局/单位、训练阶段与统计来源。
- 可做：把零更新验收和一次受控统计更新验收分开记录，报告状态与函数变化。
- 不应做：默默从var重算std“修复”未知checkpoint。两者不一致时不知道哪个可信，应拒绝或要求原始来源核验。
- 不应宣称：通过一致性检查就安全。我们的一致性正对照与count清零对照都说明其覆盖有限。
- 不应宣称：发现新颖后门或模型中毒。拥有checkpoint任意写权限本就可以改权重；必须阐明更受限、更真实的修改权限/转换失误机制，才有研究辨识度。
- 不应宣称：单字段1%变化足以使机器人跌倒。目前只有输出变化，幅度较小，没有闭环证据。

## 决策与下一步

暂作为**训练恢复验收的工程缺口**保留，不扩大成攻击训练。下一步优先只读检查我们真实恢复记录是否出现count/eps/输入合同变化，并建立元信息合同。若都一致，这条线止于工程回归测试。

若未来评估研究价值，关键不是扩大var扰动，而是找到真实数据转换流程会产生不一致或来源错配的证据，并证明普通验收通过而受控恢复/故障任务退化。没有这些证据，不给CCF档次或录用概率。

## 文件与限制

- `../probe_normalizer_resume.py`：实际库模块、内存副本探针，其中validate为数学一致性检查示例。
- `../NORMALIZER_RESUME_PROTOCOL.md`：预先固定的幅度、分支、数据和停止条件。
- `../analyze_normalizer_resume.py`：报告与图生成程序。
- `results.json`：12项原始记录、原模型/源码/协议SHA和依赖版本。
- `summary.json`：验证摘要。
- `post_update_difference.png`：两种不同量级的恢复变化，分别绘图，不混淆幅度。

单一现有数据源、无独立采集统计推断；没有ONNX变体、修改后模型文件、在线适应或硬件操作。原模型和历史报告只读。
'''
(OUT/'REPORT.md').write_text(report)
summary={'complete':True,'cases':12,'original_coherent':3,'var_only_strict_accepted':3,
         'var_only_pre_inference_exact_equal':3,'var_only_contract_rejected':3,
         'eval_update_unchanged':12,'original_models_unchanged':True,
         'closed_loop_tested':False,'scope':'Normalization single-update state contract only'}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
fig,axes=plt.subplots(1,2,figsize=(9,4))
for ax,group,title in zip(axes,(var,count),('Variance-only +1%','Count deliberately reset to zero')):
    ax.bar([str(r['seed']) for r in group],[r['post_vs_original_post']['max_abs'] for r in group])
    ax.set_title(title);ax.set_xlabel('Original model seed');ax.set_ylabel('Max absolute raw action difference')
fig.suptitle('After one statistics update: not robot safety metrics')
fig.tight_layout();fig.savefig(OUT/'post_update_difference.png',dpi=150);plt.close(fig)
print(json.dumps(summary,indent=2))
