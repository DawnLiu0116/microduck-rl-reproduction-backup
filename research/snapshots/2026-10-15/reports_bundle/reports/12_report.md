# 12 安全预处理研究报告

实际仿真轨迹上，中值滤波与一帧同步延迟的报警时刻全部一致，未显示超出普通延迟的额外异常机制。只有一个原生跌倒，证据很窄。

## 工作范围

三来源×两采集seed×Nominal/Stress、每项16环境10秒；12项192首回合，Python信号离线分析。

## 我们如何完成这项工作

保存原生终止判定后、reset前的gyro、gravity、四元数、位置和足部接触。对同一首回合轨迹离线比较raw、delay1、median3、median3_unit、gyro_delay1、gravity_delay1，报警不反馈到控制动作。

## 现有结果及解释

1. Nominal96回合无跌倒；Stress96回合仅1次fell_over。NaN和地形出界为0；192/192回合中值与同步一帧延迟的首次和全部报警事件相同。

2. 唯一跌倒为42/11011/Stress/env2：raw报警2.48s，其余分支2.50s，60°代理2.56s，原生70°姿态终止2.60s。采样网格20ms，不能解释为连续时间精确预测。

3. 四元数重构重力误差最大约5.97×10^-8。所有回合至少出现一帧无足部接触，因此无接触本身不能作为跌倒标签。

## 完整结果表

| 模型或分支 | 条件 | 阶段 | 存活分子/分母 | 存活率 | 平均寿命s | vx误差m/s | XY误差m/s |
|---|---|---|---|---|---|---|---|
| 42 | Nominal |  | 32/32 | 100.00% | 10.0000 | 未记录 | 未记录 |
| 42 | Stress |  | 31/32 | 96.88% | 9.7688 | 未记录 | 未记录 |
| 123 | Nominal |  | 32/32 | 100.00% | 10.0000 | 未记录 | 未记录 |
| 123 | Stress |  | 32/32 | 100.00% | 10.0000 | 未记录 | 未记录 |
| 2026 | Nominal |  | 32/32 | 100.00% | 10.0000 | 未记录 | 未记录 |
| 2026 | Stress |  | 32/32 | 100.00% | 10.0000 | 未记录 | 未记录 |

## 图表及读图注释

> 读图注释：原生fell_over是姿态阈值，不是记录了机身撞地。raw提前报警不等于执行保护动作后一定能避免损伤。

> 读图注释：图里的多条信号来自同一轨迹的离线处理，不是六套闭环防御各跑192回合。

> 英文坐标速查：survival=规定时长存活；duration/seconds=首回合有效寿命；vx=前向速度；XY=平面速度；yaw=绕竖直轴旋转；MSE=动作拟合平方误差；pp=百分点。完整解释见[读图指南](../READING_GUIDE.md)。

### 图1 全部任务点 all

![全部任务点 all](../figures/12_all_cases_all.png)

每个点是一项真实任务；横轴仅是文件记录顺序，不是连续变量，故不连线。点保留评估seed差异。条件、模型和分母可在全数据浏览器按编号查询；早停时误差只覆盖终止前。

### 图2 m42 s11011 Stress env2 fall

![m42 s11011 Stress env2 fall](../original_figures/12_3e8358911b_m42_s11011_Stress_env2_fall.png)

保留原实验图，不改变其样本、区间或协议定义。原图英文标注见本报告名词注释；探索、确认与历史快照不可混合累计。

### 图3 max tilt

![max tilt](../original_figures/12_848b610b64_max_tilt.png)

保留原实验图，不改变其样本、区间或协议定义。原图英文标注见本报告名词注释；探索、确认与历史快照不可混合累计。

### 图4 prediction comparison

![prediction comparison](../original_figures/12_f680d3ad75_prediction_comparison.png)

较早纯运动学探针，仅作机制背景，不计入本报告192个官方仿真首回合。

### 图5 defense pilot v2 survival

![defense pilot v2 survival](../original_figures/12_c78be335a7_defense_pilot_v2_survival.png)

历史补充图，保留用于追溯。本图的队列、幅度、分母或目的不同于本报告主表，不合并计数，不当成新增实验或最终主协议结论。

## 限制与不能支持的结论

没有运行Rust原函数、半精度打包/SFLP融合及实体标定，也没有保护动作闭环收益评估。一个阳性回合不足以支持检出率或普遍安全结论。

## 证据入口与复核范围

输入清单与SHA：[input_manifest.json](../data/input_manifest.json)。本轮计数/均值复算：[AUDIT.json](../data/AUDIT.json)。

- D:\MicroDuckResearch\ti\outputs\microduck_reproduction\mechanism_audit\sim_fall_filter\results.json　SHA256 3e212ecfb25663689aed7f99580559a8e2b5a2d088da98e10f7345fd6acda54e

## 这项工作的价值

价值是对“滤波可能造成新安全漏洞”的候选解释进行实际轨迹约束，保留有限负证据，并区分数学可能、信号报警与真正闭环安全介入。
