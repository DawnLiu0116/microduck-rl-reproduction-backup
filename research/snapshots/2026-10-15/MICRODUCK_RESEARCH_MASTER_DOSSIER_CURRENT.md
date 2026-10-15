# MicroDuck 端侧策略安全研究总档案：当前研究注释版

## 2026-10-15最新完成状态（覆盖下文历史待办）

N336项/43008回合、T24个真实PPO续训分支与528项/67584回合、人工统计状态900项/115200回合均已完成并独立复算。分阶段合计1764项/225792首回合只是计算量，不能混为同一统计总体或大量独立训练重复。900来源/75模型/CSV SHA最终核验见effective_dose_response/FINAL_AUDIT.json。

900正常Forward全存活；Pulse07中123来源w=.02/p1相对同w clean下降7.55个百分点，42来源w=.1/p1下降6.77个百分点，均为三个eval seed同向，但其他格有改善/混合，没有统一单调剂量边界。clean统计更新自身也能退化，不计为污染贡献。完整正反结果、连续指标及描述性区间见effective_dose_response/INTERPRETATION.md和四张paired图。它是人工normalizer矩构造，未训练权重，不能写成新增PPO或持久后门证据。

V2 T的部分污染末退化经clean尾段恢复，部分来源/训练seed残留；统计交换在123/73002格主要跟随权重侧，不支持单靠终点统计污染解释。N干净重校准失配反证保留。NaN/地形出界0不等于无关节超限或安全。驱动/传感器中断证据完整保留，同case有限重试不是根因修复。

用户已取消1944项三方式补测，实际0项0回合；162模型准备材料保留、等待器已停止、approved_to_run=false。旧正文或heartbeat不得恢复它。63run大训练和旧CPU225项仍暂缓，CPU1103保持暂停；不新增加密、实体、视频、防御或上传。

全项目协议与baseline总汇已完成。最终备份2,245文件SHA一致，同时复核既有T评估1,310文件、训练168文件副本；D同盘不是异盘容灾。研究监控已按完成约定暂停，每日日志不变。历史机制探索尚缺的独立分析仍明确保留，不伪称全部研究问题都解决。

本次深入复盘已融入下文第2.8节、第四/五章及附录F；完整可复算分析见[现有结果深入复盘](D:/MicroDuckResearch/ti/outputs/microduck_reproduction/existing_results_review_20261015/RESEARCH_CONCLUSIONS.md)。本版修订晚于最终实验备份；修改前版本另存existing_results_review_20261015/DOSSIER_BEFORE_ANNOTATED_UPDATE.md，不声称旧备份已包含此次新文字。

当前存储位置（2026-10-14）：全部本项目实验产物/代码/备份迁至 `D:\MicroDuckResearch\ti`；WSL实际仓库及venv在 `/mnt/d/MicroDuckResearch/microduck_rl`，旧C盘和`/home/deuler/microduck_rl`保留兼容入口。下文历史证据路径仍可用，不为迁移重写模型或原始数据。完整核验与续跑入口见 [迁移报告](D:/MicroDuckResearch/MIGRATION_REPORT.md)。

证据与研究判断更新：2026-10-15。本文面向当前完成结果与决策，保留有用技术注释及反证；历史评分明确标注适用时间，不当成最新排名。原始证据与修改前副本保留。

## 阅读导航

正文先回答“做了什么、结果是什么”，再解释系统和研究方向；方法论与查询资料集中在附录。Markdown会随阅读器、字体和纸张改变分页，因此使用可点击章节定位，不编造固定页码。

| 部分 | 阅读目标 |
|---|---|
| [一、实验全景与当前状态](#experiment-map) | 快速掌握已完成与未完成 |
| [二、实验结果与证据解释](#results) | 看协议、数字、负结果和限制 |
| [三、技术原理与安全系统](#system) | 理解真实策略、训练、接口和安全层 |
| [四、研究问题与方向选择](#directions) | 区分主线、备用与暂停方向 |
| [五、下一步与实验文件入口](#next) | 找待办及代码、协议、结果 |
| [附录A：高频术语](#terms) | 查询名词 |
| [附录B：指标与统计解释](#statistics) | 正确阅读实验数据 |
| [附录C：参考文献](#references) | 找原文及迁移边界 |
| [附录D：CCF投稿档位与证据建议](#publication) | 看目标定位，不当录用承诺 |
| [附录E：实验风格与科学工作流](#workflow) | 保留完整方法论与改进建议 |
| [附录F：手工复核与导师汇报](#verification) | 从结论追到原始证据 |

<a id="experiment-map"></a>

## 一、实验全景与当前状态

### 1.1 当前结论

我们已经复现真实MicroDuck的仿真训练、模型导出和闭环评估链路，得到三个本地最终PPO策略。完整精细响应基准已完成2,072项、171,328首回合，包含幅度/局部加密、三seed确认、通道组合、时间安排和命令扫描；原始文件/唯一任务/有限性已核验，统计图与12段统一视频完成。seed123联合脉冲弱点得到新seed确认，正常Forward全存活并不能揭示它；原生延迟消融也显示观测时间合同显著参与退化。

我们尚未证明恶意训练污染、持久后门或实体安全层绕过。监督顺序实验主要支持普通训练路径/终点效应，统一clean恢复显著缩小差异；真实归一化状态审计没有发现污染。当前优先解释故障机制，再决定是否开发针对性验收/防御，而不是继续扩大缺少支持的投毒叙事。

新增完成的N/T/900三层实验，将结论进一步收敛为：**正常行走存活验收不足以刻画故障鲁棒性；训练输入变换、归一化处理与学习路径的组合会产生来源和训练seed相关的响应差异。** T提供真实PPO续训中的有限实证，但没有证明仅改变时间排列即可成功投毒；900只改变人工统计状态，不是又做了900项训练。现阶段主线宜称“预处理兼容性与故障鲁棒性验收”，新颖性和独特机制仍待验证。

> 阅读注释：复现沿用固定公开提交的架构与任务配方，不等于得到官方发布模型相同权重，也不等于已拿到其完整历史训练配置。训练seed、恢复边界及随机轨迹都可能改变策略。

### 1.2 实验地图

不同协议分别回答不同问题，不能把回合数相加后当成一个统一统计样本。

| 工作 | 规模/范围 | 状态 | 能支持什么 |
|---|---|---|---|
| 完整PPO训练 | seed42、123、2026；4096环境；最终checkpoint3999 | 完成 | 三个真实大小的本地运动策略 |
| 导出与来源核验 | 三个ONNX；244份真实checkpoint统计审计 | 完成 | 模型接口、数值一致性与来源检查 |
| 固定命令任务评估 | 4模型×4任务×3评估seed×128首回合＝6144 | 完成，已重算核验 | 任务能力与抗推扰比较 |
| 独立评估seed故障确认 | 4模型×6条件×3seed×128＝9216 | 完成，逐回合核验 | 故障指纹在新评估seed重复 |
| 精细响应完整基准 | 2,072项／171,328首回合；确认612项／78,336回合 | 全部完成，独立完整性与原始哈希核验 | 幅度、通道、时序和命令的可复核响应 |
| 原生延迟诊断 | 4模型×2原生设置×4条件×128＝4096 | 完成，独立复算；单评估seed | 时间合同与通道选择的消融线索 |
| 论文报告与统一视频 | 7张论文图；全部原实验图36张；12段20秒视频 | 完成，逐段解码核验 | 含样本/协议/来源的可视证据；不是新增训练成果 |
| 脉冲机制拆分 | 2模型×10条件×2seed×64＝2560 | 运行完成；键/原始文件哈希已核对 | 当前描述性通道/时机线索；独立逐回合分析待完成 |
| 完整actor监督顺序 | 40case／2560首回合 | 完成 | 顺序差异与正常性能门槛 |
| 同末尾clean恢复 | 60case／3840首回合 | 完成 | 对持久污染解释的反证 |
| 小型BC、归一化、replay | 离线机制筛查＋闭环基线检查 | 完成，当前载体暂停 | 优化路径、数据覆盖及基线有效性 |
| 安全预处理 | 12case／192首回合；Python信号分析 | 完成，证据有限 | 中值滤波与一帧延迟的窄对照 |
| 零更新克隆 | 640首回合，含原模型重复 | 完成 | 状态一致性与仿真非逐位确定性 |
| V2 N推理统计对照 | 336项／43,008首回合 | 完成、独立复算 | 干净重校准失败反证、统计坐标/权重兼容性 |
| V2 T真实PPO续训 | 24分支×200新增rollout；528项／67,584首回合 | 完成、来源/模型/CSV核验 | 训练变换×F/U×来源/训练seed的故障鲁棒性交互 |
| 人工有效剂量状态 | 75模型；900项／115,200首回合 | 完成、独立核验与配对分析 | 固定权重下同w污染相对clean的局部额外影响，不是PPO训练 |
| 三方式污染补测 | 162模型已准备；原计划1,944项 | 用户取消，实测0项 | 准备不当实验成果，不自动恢复 |
| 新防御、实体验证与普适投毒方法 | 尚无完成的有效方法证明 | 未完成 | T的局部干预实证不等于新攻击/防御方法成立 |

### 1.3 环境与可复现基线

| 项目 | 记录值 |
|---|---|
| 平台 | Windows＋WSL2 Ubuntu-20.04 |
| Linux仓库 | /home/deuler/microduck_rl |
| 仓库提交 | cb70b792312d559a4da09064d92009079671815f |
| GPU | RTX 5070 Laptop，约8GiB显存 |
| Python / PyTorch | 3.12.14 / 2.9.1+cu128 |
| MjLab / MuJoCo / Warp | 1.3.0 / 3.10.0 / 1.12.0 |
| ONNX / ONNX Runtime | 1.22.0 / 1.24.4 |
| 任务 | Mjlab-Velocity-Flat-MicroDuck |
| 控制周期 / 首回合时长 | 20ms（50Hz）/ 20s |
| 安全范围 | 本地仿真；未操作实体机器人 |

这些是实验记录中的环境，不保证未来升级后仍相同。重新运行时以配置、依赖锁定与模型SHA为准；安静限速改变墙钟耗时，不改变20ms仿真控制周期，也没有实测声压值。

<a id="results"></a>

## 二、实验结果与证据解释

### 2.1 三个本地最终PPO模型

三个模型沿用官方任务体系，4096并行环境，每轮24步，通常每50迭代保存checkpoint。seed42/123采样约393,216,000条环境转移；seed2026的恢复谱系多一轮rollout，约393,314,304条。

seed42训练墙钟约11.98小时；最终训练平均回报118.5304，曾在迭代1438达到127.9663；最终平均回合长度960.26步，训练记录nan为0。训练曲线受课程/命令分布影响，最高回报不等于最佳部署checkpoint，也不能仅凭后期回报下降判定失败。

三个最终ONNX通过checker、CPU有限推理和PyTorch数值对照，最大绝对输出误差约4.17×10⁻⁷至5.36×10⁻⁷。这证明测试输入上的导出一致性，不证明所有状态下的安全性。2026-10-13另核对三个最终WSL checkpoint与既有Windows备份SHA一致；seed123副本位于backups/microduck-local-20261011/wsl_final_checkpoints/seed123_model_3999.pt，SHA为94d11f5910faf6573ef59b20dff20fe5b2695866ce75630eb403f26f909d0f10。新完整快照状态须以BACKUP_STATUS.json为准。

### 2.2 固定命令任务评估

协议：官方＋三个本地策略；评估seed1001/2002/3003；每项128首回合、20s；第一次终止后不把reset回合混入评分。报告连续指标，不事后建立二值“任务成功”阈值。

| 任务 | 命令/推扰 | 重点指标 |
|---|---|---|
| Forward | vx=0.3m/s，vy=0，yaw=0 | 存活、前向误差、横向漂移 |
| Turning | vx=vy=0，yaw=0.6rad/s | 存活、yaw误差、平移漂移 |
| Standing | 零速度命令 | 存活、平面速度、yaw速度 |
| Stress-forward | 同Forward；每0.5–1s推扰 | 存活、恢复时间、跟踪误差 |

| 模型 | Forward vx误差 m/s | Turning yaw误差 rad/s | Standing平面速度 m/s | Stress存活 | Stress恢复时间 s |
|---|---:|---:|---:|---:|---:|
| official | 0.1542 | 0.5851 | 0.001205 | 84.90% | 0.8231 |
| seed42 | 0.1211 | 0.5194 | 0.001630 | 85.68% | 0.9159 |
| seed123 | 0.1161 | 0.1968 | 0.001529 | 83.85% | 0.9008 |
| seed2026 | 0.1248 | 0.2047 | 0.001531 | 79.69% | 0.8830 |

Forward、Turning、Standing各模型都是384/384存活，但Turning跟踪能力明显不同。seed123转得更接近命令，同时平移速度约0.1411m/s，seed42约0.0257m/s；原地转向目标平移为0，所以不能宣称seed123全面更好。

6144逐回合CSV与48job已重算，最大聚合残差约2.1653×10⁻⁷。置信区间用于这些固定策略及评估分布，不代表所有可能训练出的MicroDuck。推扰后恢复时间也不是倒地后自主站起时间。

### 2.3 完整精细响应与独立确认

完整队列2,072项、171,328首回合，于北京时间2026-10-12 23:09完成视频后处理。探索seed71201/71202，每项64回合；确认seed81201/81202/81203，各128回合。确认共同网格在selection.json中先锁定，再读取新seed结果。以下主表每格384回合，均为规定20秒存活比例，不是命令完成率。

| 模型 | Clean | 额外40ms延迟 | Freeze 8 | Freeze 10 | Freeze 12 | 行走联合脉冲alpha1 |
|---|---:|---:|---:|---:|---:|---:|
| official | 384/384（100%） | 182/384（47.40%） | 382/384（99.48%） | 336/384（87.50%） | 237/384（61.72%） | 374/384（97.40%） |
| seed42 | 384/384（100%） | 8/384（2.08%） | 374/384（97.40%） | 301/384（78.39%） | 252/384（65.63%） | 372/384（96.88%） |
| seed123 | 384/384（100%） | 48/384（12.50%） | 376/384（97.92%） | 330/384（85.94%） | 297/384（77.34%） | 73/384（19.01%） |
| seed2026 | 384/384（100%） | 12/384（3.13%） | 380/384（98.96%） | 302/384（78.65%） | 259/384（67.45%） | 330/384（85.94%） |

NaN终止和场地越界均0，不能称关节限位违反0。零跌倒384回合的Wilson95%上界约0.99%，不是零风险。每个图点的job_id、seed、分母和输入SHA见论文报告REPORT_DATA.json。

- Delay为保留原生延迟基础上的额外观测延迟，不是端到端总延迟；20/40ms间的真实25/30/35ms采样仍未实现。
- Freeze 8/10/12名义持续160/200/240ms，每180步触发；末帧实际陈旧年龄为7/9/11策略步。正式网格已扩展4至16步，但不从有限网格推普适精确阈值。
- 正式行走脉冲起点200/400/600/800，每次5步；启动脉冲只在校准桥接中，不混入当前主表。
- 0:34传感器段按载体修改，历史动作与命令不改。重力0.8是投影向量分量，不是0.8rad倾角。
- 组合与时间扫描只有两个探索seed；相同alpha不等同总输入范数、物理能量或早停后的实际暴露。

本结果支持固定策略的故障指纹重复，不证明恶意训练、后门或实体入口。联合故障可能比某些单通道更温和，但耦合/抵消只是候选解释，尚未因果分离。

### 2.3.1 原生观测延迟诊断

单seed1001、每格128回合，共32项4096回合；原生保留/清零两设置均clean全存活。全观测额外40ms保留/清零存活：official63/127，42为5/105，123为18/118，2026为7/119。仅IMU延迟时official两设置都0/128；原生清零后的42/123/2026分别64/67/82存活。仅关节速度延迟各模型均全存活。

这说明原生时间合同参与退化，且通道选择能改变模型排名；不是“所有本地训练都坏了”的充分证据。清零属于另一观测合同，只用作消融，不替代正式基准。未完成跨三seed诊断确认、关节位置单独测试或因果对齐证明。

### 2.4 脉冲先导机制pilot与仍成立的线索

当前结果文件complete=true，40唯一job，2560首回合；40份原始CSV存在且SHA与记录一致。下表仅合并运行器success_count，每格128回合；本次文档整理没有独立重算CSV全部指标、生成新置信区间或录制新视频。

| 条件 | seed42存活 | seed123存活 | 对照内容 |
|---|---:|---:|---|
| clean | 128/128 | 128/128 | 无故障 |
| legacy_all | 118/128 | 31/128 | 启动＋周期性三通道脉冲，保留既定条件名 |
| startup4_all | 128/128 | 128/128 | 仅step1–4 |
| startup5_all | 128/128 | 128/128 | 仅step1–5 |
| walking_all | 119/128 | 22/128 | 去掉启动，step≥200的三通道周期脉冲 |
| walking_gyro | 13/128 | 0/128 | 行走期角速度通道 |
| walking_gravity_add | 4/128 | 1/128 | 行走期重力字段加向量 |
| walking_joint_velocity | 121/128 | 36/128 | 行走期关节速度通道 |
| walking_gravity_direction | 54/128 | 40/128 | 只保留受扰重力方向，维持原模长 |
| walking_gravity_norm | 128/128 | 128/128 | 只改变重力模长，维持原方向 |

固定Forward，20s、50Hz；2个模型、2个评估seed41041/52052、每case64首回合。这两个seed此前已用于确认，不是完全未使用的评估holdout。

脉冲幅度：角速度加[12,-16,24]；重力投影加[0.8,0,0]；14个关节速度加[8,-10,7,-8,10,-7,6,-6,8,-8,5,-5,7,-7]。重力字段0.8是向量分量，不是0.8rad躯干角；也没有依据称这一联合脉冲“小幅”或“处于训练DR范围”。

拆分方式：设原重力观测g，受扰v=g+[0.8,0,0]。方向分支使用v/||v||×||g||，模长分支使用g/||g||×||v||。这是观测空间对照，不等价于物理安装旋转。

目前值得追踪的线索：

1. 去掉启动后seed123仍显著失败，因此启动异常不是唯一解释；但启动与行走分支暴露次数不同，尚未排除总剂量差异。
2. 两个模型在角速度或重力加性单通道下都非常脆弱，不能把联合脉冲排名直接解释成“seed42单通道均稳健”。
3. 三通道联合反而比部分单通道存活高，提示非单调交互/补偿可能，机制未定。不能把单通道跌倒率相加预测组合。
4. 纯模长分支存活128/128，方向分支有失稳；这只是支持方向因素更值得检查，不证明模长绝对无害，也不证明简单单位化能解决。

动作指标是原始网络输出的代理量；最大倾斜为pre-step记录，可能遗漏终止物理帧。NaN/场地出界0不代表关节机械限位0。下一步先独立重算、核对终止及采样时间，再用匹配预算对照排除替代解释。

### 2.5 监督训练顺序与恢复：保留反证

这一组不是原生PPO投毒：使用teacher动作标签做监督更新，不运行完整奖励—优势—actor/critic学习链路。

| 实验 | 关键设计 | 实测与决策 |
|---|---|---|
| 小型BC顺序 | 12288训练＋4096留出；固定128批×96；8角度±6°；小网络61→128→64→14 | 候选最坏MSE增幅6.32%/8.5%，未过预声明10%门槛；单调分支的84.57%/111.61%为探索MSE差异，不是跌倒率 |
| 完整actor顺序 | 来源42/2026；no_update/random/ascending/descending；256次LR1e-5更新；原normalizer不变 | 40case/2560全部存活；两个ascending正常vx误差退化，未通过正常门槛，故障未测，不填0 |
| 共同clean恢复 | 八个parent各256次相同clean监督更新、fresh Adam；另两个frozen，共十策略 | 60case/3840全部存活；正常误差分支范围42约0.042122→0.000986，2026约0.034796→0.000462 |
| 归一化确认 | 288离线条件，5184有限MSE记录 | 顺序差异主要涉及random改善；不支持自动改称投毒 |
| 后续归一化/终点对照 | 162离线条件，其中108计划、54探索 | 最终统计趋近；保留普通遗忘/终点解释 |
| replay分叉 | 72分叉、216分支、6480 MSE；闭环8case/512首回合 | replay可改善离线最坏MSE，但小BC闭环基线不成立：teacher各64/64，no_update/replay各0/64；停止扩展故障 |

teacher采样64环境×256步，只覆盖约5.12s片段；小BC容量、覆盖与多步误差累积都可能导致闭环失败，不能称安全攻击成功。replay离线最坏MSE改善约32.3%–52.8%，伴随clean MSE代价约1%–2.1%；离线好看仍不等于机器人能走。

clean恢复阶段的no_update只是父分支名称，它也接受clean更新；frozen才是零更新。共同clean尾段与Adam重置同时变化，不能分离两者原因；残余差异不能直接称持久后门。停止此载体不等于否定所有原生PPO课程假设。

### 2.6 安全层、归一化与可重复性审计

| 审计 | 结果 | 结论边界 |
|---|---|---|
| 推理时同multiset排序 | 有效协议32case/2048回合，全存活；最大XY误差约+0.6% | 当前轻量载体NO-GO，不证明所有时序扰动无害 |
| 简单防御pilot | 1536首回合，单评估seed；seed123脉冲naive分支12/64→30/64 | 仅初步正向信号；其他防御存在明显损害，未形成稳定方法 |
| 线性延迟外推/静态限幅 | delay下123为5/64→0、2026为7/64→0；静态clip使2026脉冲52/64→0 | 限幅/滤波可破坏纠正动作，不能默认防御全面更好 |
| Python安全预处理 | 192回合仅1次原生跌倒；中值与一帧延迟报警事件一致 | 原报警2.48s，两处理2.50s，60°代理2.56s，70°fell_over2.60s；未证明额外组合机制 |
| 人为normalizer副本 | strict加载可接受var/std不一致；只改var时冻结推理可不变，更新后差异出现 | strict检查键/形状不等于语义一致性；无真实污染来源、PPO或闭环结论 |
| 真实checkpoint来源 | 244份统计满足一致性；seed2026多一轮rollout | 未发现同类真实污染；恢复不保证完整RNG/模拟状态复原 |
| 零更新克隆 | 文件字节一致，同观测actor输出最大差0；原/克隆及原/原独立仿真轨迹非逐位一致 | 严格闭环门槛失败，不能事后放宽称通过；非确定性来源尚未定位 |

零更新克隆的Forward逐回合差值绝对均值约0.00044–0.00058m/s，是基线重复性参照，不是未经预注册的新“可接受阈值”。仿真fell_over是姿态终止条件，非机身接触地面时间；脚无接触也可能是正常步态或初始化。

### 2.7 可视化协议与实体边界

已完成12段正式说明视频：四模型各clean、联合脉冲alpha0.7、alpha0.8；seed91201、固定Forward、无推扰、640×480、同相机、20秒。每段全解码1000帧/50fps，SHA与manifest一致。第一次终止后填充末帧并显示FALL/TERMINATED，不混入reset回合；目标与实际速度、脉冲/终止标志叠加。视频是独立说明回合，不增加171,328统计样本量。

普通步行策略没有经验证的倒地站起能力。Fall recovery必须单列任务与控制方式，不能靠仿真reset当恢复。当前有限任务保存了指定回合完整trace，未覆盖每个回合完整机械遥测。中期事件时间曲线已生成，不能冒称所有最终条件都已有完整生存分析。

### 2.8 N／T／900：预处理、学习路径与有效剂量

#### 2.8.1 先分清三个问题

N改变推理统计及等价补偿，回答“统计坐标与原权重是否匹配”；T进行真实PPO续训，回答“训练变换与统计处理如何影响学习结果”；900固定权重，仅合并normalizer总体矩，回答“终点统计状态本身的直接影响”。三者相互约束，不能把N失配、T跌幅和900剂量拼成一个已证明的攻击链。

> 阅读注释：F是归一化统计冻结，U是沿历史正常累计；T0为同预算clean，TC为角速度/重力共同旋转，TI为相反旋转。统计冻结不表示网络权重冻结。w是新数据在合并统计中的有效权重，p是其中污染比例；virtual mass不是实际新采集样本量。

#### 2.8.2 900项：看完整配对网格，不只看最差格

每来源有6个w×3个非零p，共18个Pulse07配对格；每格比较同w、同评估seed的clean。

| 来源 | 平均存活下降格/18 | 三eval seed均下降格/18 | 配对差中位数 | 最差至最好配对差 |
|---|---|---|---|---|
| 42 | 13 | 3 | -0.52个百分点 | -6.77至+1.56个百分点 |
| 123 | 13 | 6 | -3.26个百分点 | -7.55至+2.60个百分点 |
| 2026 | 6 | 2 | +0.65个百分点 | -3.65至+2.86个百分点 |

54格只有11格在三个eval seed上均下降。这是方向性描述，不是11格统计显著或11次独立训练确认；共享clean对照和嵌套样本使格间相关。改善格也无一在三个seed上都严格改善，不能包装稳健增强。Forward全存活不证明正常行为等价；没有预注册等价界，不能用“差异小”代替等价检验。Delay20差异很小，Delay40的clean已接近地板，仅作诊断。

来源123、Pulse07、w=.1：原模型77.08%，clean更新70.83%，p=.5为64.84%。相对原模型总下降12.24个百分点，其中6.25个百分点在无污染更新时已经出现，污染相对同w clean额外下降5.99个百分点；不能全归为攻击贡献。这是本格描述性分解，不是普遍可加因果模型。

> 阅读注释：paired图阴影是三eval-seed重采样完整包络，实质等于其极值范围，不是95%训练总体CI；Wilson只描述固定模型回合比例。相同seed不保证不同策略的episode轨迹逐位配对。误差按终止前平均，须同时看存活时间。

#### 2.8.3 T阶段：训练路径证据强于简单终点统计故事

冻结统计F时，TC在150轮相对同预算clean的Pulse07差异，42两训练seed为-19.79/-33.85个百分点，123为-63.28/-38.54个百分点；200轮共同clean尾段后为-5.99/-2.86/-7.29/+2.60个百分点。四块均明显缩小差距，其中一块翻为略高于clean。因此已有“训练输入变换影响故障响应”的实测，但TC普遍持久破坏的叙事不成立。

F下仍有退化，排除了“必须先改变当前normalizer状态才会退化”的必要条件，但不排除固定归一化坐标与变换输入的交互。没有污染的T0最终U相对F四块差异也为-9.64/-1.30/-63.28/+7.81个百分点，故不能把F普遍推荐为经过验证的防御。123/TI_U两训练seed最终效应+3.39/-54.43个百分点，方向翻转。

终点统计交换的关键格123/73002：TI_U为26.56%，换clean统计PC为26.82%；clean权重配TI统计CP为82.55%，原clean80.99%。差异主要跟随权重侧，但权重包含训练时统计历史、优化器及访问分布的共同作用；不能跳到“已定位后门权重”或“统计历史无关”。123/TI_F残留下降68.49/14.06个百分点，仅支持本条件有限恢复不完全，不是无限期持久证明。

#### 2.8.4 N的反证、安全计数与运行限制

N3干净重校准与N6污染校准Forward都为0%，首先说明管线与原策略不兼容。不能用N6相对原模型跌幅证明污染，也不能用两者都0%证明污染完全无效——已有地板。首层等价补偿支持统计坐标改变的函数传递路径，尚未锁定采集分布、安装旋转或数据覆盖中的唯一原因。

N/T/900有关节超限步骤的回合分别30,752/24,792/47,538；NaN与地形出界0不等于全面安全，非零超限步数也不直接证明实体损伤。多次软件中断跨clean/污染组发生，GPU事件有时间关联但根因未知；SHA核验只证明记录一致，重试成功不证明数值稳定或尝试间同分布。不能将软件崩溃计作跌倒或污染贡献。

<a id="system"></a>

## 三、MicroDuck技术原理、安全层与系统构建

### 3.1 端到端链路

```text
官方训练配置、DR事件与课程（已复现）
        ↓
MuJoCo / MjLab 并行环境 ── PPO actor/critic 训练 ── checkpoint
        ↓                                      ↓
  独立统一评估                         export.py + 归一化固化
        ↓                                      ↓
逐回合指标、视频、故障指纹                  ONNX [1,61]→[1,14]
                                               ↓
                        robotd 观测组装 → policy inference
                                               ↓
                      动作缩放/滤波 → safety → RobotIo → 14 舵机
```

checkpoint/ONNX之前是已执行的仿真训练与评估；robotd到舵机是开源运行时参考链路，**不是我们已部署或实机验证的流程**。这个图对应训练输入、模型激活与运行时控制三类边界。

> **【名词解释】MuJoCo是物理模拟器：计算机器人、地面接触、力与下一时刻状态。MjLab组织任务、观测、奖励、终止与并行环境。WSL2是Windows上的Linux运行环境，不是机器人仿真器。“在WSL训练”和“用MuJoCo仿真”描述的是不同层。robotd是开源运行时守护进程；我们读过其源码，不代表它已在实体机部署。**

#### 配置与“日程”到底如何实现

三原模型主要沿用 `/home/deuler/microduck_rl/src/mjlab_microduck/tasks/microduck_velocity_env_cfg.py`：startup初始化随机化、reset回合随机化、interval推扰、观测模块延迟与训练进度curriculum。质量/惯量为startup；质心、执行器增益和摩擦等为reset；IMU延迟选择配置每64步更新。不能统称所有变量每步IID采样。

我们另做固定teacher数据的监督日程pilot：`curriculumtrap_pilot/run_bc.py` 将12288训练样本固定为128批×96样本；8个角度分布在±6度内，每角度16批，保存样本索引/角度ledger；random、block、monotonic和候选极端交替顺序各使用全部批次一次。随机分支是固定账本的随机排列，不是严格的重新IID采样。同步旋转角速度与重力投影，teacher标签不变。

后来 `mechanism_audit/run_full_width_order.py` 使用完整actor结构、原归一化和256次LR1e-5监督更新，再闭环评估。**完整PPO actor结构不等于原生PPO训练方法；这些脚本没有把恶意DR日程接入三个原模型的PPO训练。**

### 3.2 训练与策略接口

本项目复现任务是 `Mjlab-Velocity-Flat-MicroDuck`。已核验配置如下：

- MuJoCo 物理步长 0.005 s，decimation 4，策略控制周期 0.02 s，即 50 Hz；
- 14 个舵机关节，actor 输出 14 维动作；
- actor 输入 61 维：48 维本体状态与历史动作，加 13 维命令字段；
- actor MLP：`61 → 512 → 256 → 128 → 14`，ELU；
- critic 使用 76 维特权观测；
- PPO：5 epochs、4 mini-batches、初始学习率 `1e-3`、`gamma=0.99`、`GAE lambda=0.95`、clip 0.2；
- 每回合最多 20 s，即 1000 个控制步；
- 平移命令范围约 x `[-0.4,0.4]` m/s、y `[-0.3,0.3]` m/s，yaw `[-1,1]` rad/s；
- 执行器模型包含 BAM M6、供电电压/压降、摩擦、力矩限制和3–6个物理步命令延迟，约15–30ms，不是3–6个20ms策略步；
- domain randomization 还覆盖质量/惯量、质心、armature、编码器偏置、IMU 安装误差、外力推扰等；
- 当前本地提交中的观测延迟训练范围较窄：IMU 0–1 步、关节速度 1 步；
- `nan_state` 终止用于阻止非有限状态继续污染 rollout。

导出的 ONNX 把经验观测归一化固化到模型中。三个本地最终模型均通过 `onnx.checker`、CPU ONNX Runtime 和 PyTorch/ONNX 数值等价检查。

#### 3.2.1 一次控制步，实际上发生什么

1. 从仿真取得61维actor观测。评价器按既有接口分为：角速度0:3、重力投影3:6、关节位置6:20、关节速度20:34、历史动作34:48、命令/姿态48:61。冒号右端不包含：20:34一共14维。
2. 如测试故障，只修改指定传感器字段。命令不改，避免把“目标变了”误说成“策略不跟踪”。这不是修改真实传感器硬件或物理状态。
3. actor内部先做已学到的观测归一化，再通过 `61→512→256→128→14` 的MLP输出动作。MLP是多层全连接网络；ELU是非线性激活函数，不是安全滤波。
4. 环境包装/动作模块按配置处理动作，再交给执行器动力学。**14维原始网络输出不应未经核验直接叫14个角度、14个力矩或14次机械越界。**应追踪缩放、裁剪、目标生成和实际关节状态。
5. 物理模拟推进4次，每次0.005秒；随后计算奖励/终止并产生新观测。20ms为控制周期，物理仍按5ms细步推进。

> **【名词解释】Projected gravity是重力方向在机器人自身坐标系中的表示，能让网络推断倾斜。它不是“躯干角”这一标量。理想向量(0,0,-1)加上(0.8,0,0)后变成(0.8,0,-1)，模长约1.281；同时改变了方向和模长，不能称“倾角增加0.8rad”。**

#### 3.2.2 PPO训练与后来的监督pilot，区别在哪

原生PPO：让4096个环境并行采样，每轮24个控制步，训练时利用奖励、critic价值估计和优势（advantage）更新actor/critic。每轮采样 `4096×24=98,304` 条环境步；同一采样集可多轮优化，但多轮优化不等于多采了一份物理轨迹。

后来的监督pilot：固定teacher样本和动作标签，主要以动作预测误差更新actor；不使用完整原生PPO的轨迹—优势—actor/critic优化链路。使用相同的actor架构，只能证明对真实大小策略网络做了监督实验，不能证明原生PPO训练已被污染。

| 参数 | 怎么理解 | 不应误解为 |
|---|---|---|
| gamma=0.99 | 未来奖励折扣，越远的奖励通常权重越小 | “99%的安全保证” |
| GAE lambda=0.95 | 估计优势时折中偏差与方差 | 物理滤波系数或异常检测阈值 |
| 5 epochs / 4 mini-batches | 一份采样数据分批、重复用于优化 | 每次都新生成完整环境数据 |
| PPO clip=0.2 | 限制优化目标中策略概率比的激进变化 | 对电机动作做±0.2限幅 |
| 学习率1e-3 | 参数优化步长的初始设置 | 每秒更新次数 |
| clip_actions | 环境包装器对动作的裁剪设置 | PPO clip参数；两者必须分开核验 |

只需先掌握：输入输出、一次采样/更新、奖励与终止、部署时actor冻结、监督pilot不是PPO。若之后实施训练污染，再深入PPO目标、GAE、critic bootstrap、课程与normalizer更新路径；现在不用为了看实验结果先推完整收敛证明。

### 3.3 官方运行时安全层做了什么

开源运行时已经考虑了不少传统安全问题：

- safety 模块持有唯一电机写句柄；
- 非有限观测和动作会被拒绝；
- 速度命令有 deadman，过期后归零；
- IMU 解码验证四元数并使用三点中值滤波，能抑制单样本尖峰；
- 总线短暂失败时可短时沿用旧样本，随后停止策略步进；
- 官方守护进程/更新包有签名、哈希、健康门和回滚；
- ONNX 加载会检查接口形状并做基本推理烟测；
- 官方策略通道有来源与 manifest 机制。

所以，不能把该系统描述成“完全没有安全层”。我们的研究问题是这些安全层没有覆盖的**语义安全**。

> **【名词解释】deadman类似“持续收到有效指令才允许动”，命令太久未更新就归零。三点中值取相邻三次读数的中间值：1、100、2得到2；但1、100、100得到100，因此不能保证抑制连续异常。NaN/Inf是数值非法，不是“动作危险”的同义词。签名证明来源/完整性，不证明该来源训练出的策略会正确转弯。**

**【实验边界】** 我们的观测注入发生在仿真actor接口，通常不经过实体IMU解码、总线、Rust预处理及真实舵机保护。Python预处理pilot也未替代真实Rust链路。因此“仿真有弱点”与“官方安全层已被绕过”是不同结论，后者目前没有证据。

### 3.4 安全覆盖边界与待验证缺口

| 编号 | 缺口 | 证据状态 | 研究意义 |
|---|---|---|---|
| F1 | 61 维策略观测不含时间戳、age、valid mask 或故障状态 | 代码确认；40 ms 延迟敏感性仿真确认 | 有限但过期的数据与新鲜数据对策略不可区分 |
| F2 | 冻结检测主要针对整块 IMU 字节完全相同，关节通道没有同等时序检测 | 代码确认 | 缓慢变化或局部冻结可能绕过简单规则 |
| F3 | 三点中值只适合短单点 IMU spike | 代码确认；结构化脉冲策略差异已测 | 多帧、关节或协调脉冲不在其保证范围内 |
| F4 | 动作夹紧是通用 `[-π,π]`，不是解剖学逐关节限制 | 代码确认 | 有限合法输出仍可能是机械上不合理的组合 |
| F5 | 社区/本地策略可以是未签名模型 | 文档确认；需授权用户安装 | 这是供应链信任问题，不是未认证远程安装漏洞 |
| F6 | 模型验证以结构、有限性和烟测为主，不证明行为安全 | 代码确认 | 正常样本表现干净的后门模型可能通过 |
| F7 | 低层 fall verdict 主要报告；高层 limp-fall 可选且存在 skill 窗口 | 代码/文档确认 | 失稳后有限动作仍可能继续下发 |
| F8 | 基础 PPO 部署时不在线更新权重 | 重要负结论 | 不能宣称官方基础模型存在“部署期持续投毒” |

完整代码证据见 `upstream_audit/MICRODUCK_SECURITY_GAP_AUDIT.md`。这些是研究缺口或未验证攻击面，不等于 CVE，也不等于已经对实体设备证明可利用。

### 3.5 我们构建的实验系统

系统由六个层次组成：

1. **训练层**：三个agent seed、4096并行环境、迭代终点3999、50迭代保存一次checkpoint；seed2026恢复边界使其最终谱系比另两模型多一个rollout。
2. **模型完整性层**：保存关键里程碑、检查张量 NaN/Inf、导出 ONNX、做 61→14 有限推理和 PyTorch 等价验证。
3. **统一任务评估层**：Forward、Turning、Standing、Stress-forward，固定命令、3 个评估种子、逐回合数据。
4. **传感器故障层**：clean、40 ms delay、160/200/240 ms freeze、100 ms structured spike。
5. **可视证据层**：同相机、分辨率、种子和时长的视频；修正版在第一次终止后冻结并标记，不把重置后的新回合混入。
6. **开源运行时审计层**：把仿真弱点与 `robotd/duck-control` 的观测、模型加载和安全边界逐项对应。



<a id="directions"></a>

## 四、研究问题与方向选择

### 4.1 背景与当前威胁模型

端侧运动策略是闭环系统：观测错误改变动作，动作改变接触与姿态，下一帧又反馈到策略。因此“有限输出、正常平均回报、单次存活”都不等于安全。

当前研究聚焦训练过程、安全层和数据变换，不把基础冻结ONNX写成在线学习系统。任何“投毒”实验都必须说明攻击者能控制哪段训练/转换输入、范围与预算；有故障退化不等于有恶意训练者。

原候选问题：同一组合法、幅值受限的外生样本，仅改变排列或处理状态，能否保留正常能力却改变故障鲁棒性？现在已有T阶段的原生PPO续训干预证据，但T改变的是训练输入变换，不是仅改变时间排列；不能把它写成顺序投毒已成立。PPO闭环数据由策略反过来影响，“外生日程相同”不等于“实际采集数据相同”。

当前已支持的较窄命题：固定策略在正常任务及不同传感器故障下具有不同表现，官方结构/有限性验收不足以替代任务—故障行为评估。机制和方法创新仍须文献比较与因果实验。

当前更具体的问题是：如何区分干净统计更新失配、训练seed波动和干预造成的额外鲁棒性变化？已知TC_F污染末效应跨四块同向但大多可恢复，900效应局部且非单调；这些反证决定优先研究验收与兼容，而非预设“统计投毒必然成功”。

### 4.2 方向权重与评级

**当前决策（2026-10-15）**：先完成现有数据表达与近邻定位；未来若另行批准实验，优先一个锁定T现象的独立训练重复及clean对照，其次校准—权重匹配机制，最后才是局部剂量加密。补测取消、63run暂缓。下表为10月13日历史资源评分，保留方法注释供回看，不再作为当前执行顺序；本次不伪造一组新的精确评分。

分数用于未来1–2周研究资源分配，不是录用概率、攻击成功率或论文质量测量。维度各0–5：证据E30%、机制可辨识性M20%、低成本可证伪F20%、新颖性支持N15%、系统/后期实体价值V10%、主线匹配U5%。

优先级＝(30E＋20M＋20F＋15N＋10V＋5U)/5。当前N均保守为1，表示近邻差异未证实；并非已确认1/5创新或判断领域饱和。

| 方向 | E/M/F/N/V/U | 分/100 | 决策 |
|---|---|---:|---|
| 脉冲机制定位 | 4/3/5/1/4/4 | 71 | 首要：从完成曲线/组合中做匹配预算机制解释 |
| 任务—故障指纹与行为验收benchmark | 5/2/5/1/3/3 | 70 | 精细基准已完成；与机制诊断组成工作包 |
| Behavioral Admission＋针对性Shield | 3/2/4/1/4/5 | 58 | 条件性方法方向，尚未证明防御有效 |
| TransformationTrap：具体转换/恢复来源载体 | 2/3/3/1/3/5 | 50 | 备用；先找真实受限入口 |
| 中值滤波组合失效载体 | 1/1/3/1/3/4 | 35 | 暂停扩大，保留工程核验 |
| CurriculumTrap当前监督顺序载体 | 1/1/2/1/3/5 | 32 | 暂停；不自动上4000迭代PPO |
| 相位错配动作后门 | 0/0/2/1/2/3 | 18 | idea库，无实现或机制证据 |

这套评分是资源决策启发式，本次保留既有数值，不把171328回合或论文式排版自动兑换为创新分。精细基准现已完成，数据充分性提高，但机制唯一性和新颖差异仍未证实；历史40项pilot的独立完整聚合另列限制。71与70不是有意义的精确竞争排名。以更重创新的E20/M25/F15/N25/V10/U5作敏感性检查，分数依次63/59/52/48/33/31/18；近期工作包未变，不证明任意权重都稳定。

归一化合同和恢复来源核验属于有价值工程维护，不因244checkpoint正常就反过来宣称投毒创新。低优先级不表示负结果没有价值。

### 4.3 推进、暂停与排除的方向

| 类别 | 方向 | 原因/重新进入条件 |
|---|---|---|
| 推进（仅现有材料） | 预处理兼容性、训练路径与故障鲁棒性验收 | N/T/900分层证据与反证已形成；先整理，不新增实验 |
| 条件性第一优先 | 一个提前锁定T现象的独立训练重复 | 先量化同预算clean训练波动；新增eval回合不能替代训练重复 |
| 条件性第二优先 | 校准数据分布与权重功能匹配 | 排除管线失配，不换数据制造正结果 |
| 后置/需另行授权 | 通道、方向/模长、暴露预算和w局部加密 | 更密曲线不能解决训练重复不足；1944项补测仍取消 |
| 条件推进 | 行为准入、数据物理一致性、任务感知安全层 | 必须证明正常代价、故障收益与延迟开销 |
| 备用 | 转换/normalizer恢复合同 | 有接口审计价值；真实输入权限及可达失败链未成立 |
| 暂停 | 当前BC与监督顺序污染 | 小BC闭环不成立；完整actor差异在clean恢复后收敛 |
| 暂停 | 推理时轻量排序、中值组合额外失效 | 当前窄试验未支持目标机制 |
| 排除近期主线 | 部署期在线自演化/在线投毒 | 基础MicroDuck无该在线状态；额外加入模块会换研究对象 |
| 不独立作为创新 | checkpoint替换、社区模型后门、一般供应链 | 权限过强或已有成熟范式，需特定新机制才有价值 |
| 不采用 | 只加大bias直到跌倒、任意改权重造结果 | 不能解释合法约束内机制或现实攻击面 |
| 不继续 | 玩具步行环境 | 不作为MicroDuck证据，不再扩展 |

CurriculumTrap若重新进入，至少需要：受限真实载体、实际消费的相同外生账本、同预算与末尾分布对照、可用的零更新基线、两训练seedpilot、正常门槛和固定canary。random应称固定multiset的随机排列，而非严格IID重新采样。未满足条件就不恢复大训练，不抬故障幅度追结果。

<a id="next"></a>

## 五、下一步与实验文件入口

### 5.1 当前待办

1. 当前完成：N/T/900原始核验、分层判读、配对图、协议总汇及2,245文件最终备份；本次继续更新带注释总档案，不重复计为新实验成果。
2. 不新增实验时：优先把“验收盲点—校准失配反证—训练路径/恢复—终点统计局部效应”组织成可汇报故事；创新声称前另做针对性文献定位，本次未宣称文献空白。
3. 如以后授权实验，首先提前选一个T现象做独立训练重复和同预算clean对照。123/TI_F可作恢复残留候选，42/TC_F可作恢复现象候选；不是同时全部追加。
4. 其次澄清校准分布与原策略统计/权重匹配；只有前两类证据值得继续，才考虑局部w加密或通道分解。若重复中变号、效应被clean波动覆盖或正常质量无法保持，转向验收/兼容性，不抬幅度追正结果。
5. 旧5ms端点桥接、匹配暴露机制等仍是备选而非当前已批准任务；历史机制pilot独立分析缺口不以本轮数据替代。1944项补测取消、63run及225插值暂缓，研究监控暂停、每日日志不变。
6. 不恢复防御曲线或部署期在线学习，不新增视频、上传或实体操作；实体阶段如有新授权需另立吊架/急停/空间隔离/人工监护协议。

上述未来实验仅是优先级建议，不构成启动授权。核验完成不等于所有机制已经解释或所有历史待办都已完成。

### 5.2 实验文件入口

本文为“能找到并理解证据”的导航，不复制海量逐回合文件名或过时文件数量。协议、代码、模型和原始数据分别定位；已有总清单是有时间边界的盘点，不冒充实时全量。

| 模块 | 入口 | 主要产物 |
|---|---|---|
| 最新深入复盘 | [结论与建议](D:/MicroDuckResearch/ti/outputs/microduck_reproduction/existing_results_review_20261015/RESEARCH_CONCLUSIONS.md)；[复算证据](D:/MicroDuckResearch/ti/outputs/microduck_reproduction/existing_results_review_20261015/EVIDENCE.json) | 网格方向、clean代价、T分训练seed恢复、下一步与停止条件 |
| V2 N/T | [N判读](D:/MicroDuckResearch/ti/outputs/microduck_reproduction/preprocessing_integrity_v2/n/analysis/INTERPRETATION.md)；[T判读](D:/MicroDuckResearch/ti/outputs/microduck_reproduction/preprocessing_integrity_v2/t/analysis/INTERPRETATION.md) | 336/528项及原始核验；历史后续建议以本档案当前取消决定为准 |
| 主900项 | [判读](D:/MicroDuckResearch/ti/outputs/microduck_reproduction/effective_dose_response/INTERPRETATION.md)；[最终核验](D:/MicroDuckResearch/ti/outputs/microduck_reproduction/effective_dose_response/FINAL_AUDIT.json) | 115200回合、同w配对、四张连续指标图 |
| 协议总汇与最终备份 | [协议/baseline](D:/MicroDuckResearch/ti/outputs/microduck_reproduction/PROTOCOL_BASELINE_SUMMARY_2026-10-15.md)；[备份收据](D:/MicroDuckResearch/ti/backups/effective-dose-final-20261015/BACKUP_STATUS.json) | 最终实验快照2245文件；本版新文字另留修改前副本 |
| 训练与导出 | [RUN_SUMMARY.md](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/RUN_SUMMARY.md)；[seed2026说明](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/SEED2026_HANDOFF_REPORT.md) | WSL最终checkpoint；三个seed*_iter3999.onnx |
| 论文式最终实验报告 | [Markdown报告](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/paper_report_2026-10-13/MICRODUCK_EXPERIMENT_PAPER.md)；[PDF](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/paper_report_2026-10-13/output/pdf/MICRODUCK_EXPERIMENT_PAPER.pdf) | 7图、协议/分母、参考文献、REPORT_DATA逐点来源 |
| 精细响应完整结果 | [最终结果](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/fine_response/results/results.json)；[完成核验](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/fine_response/results/COMPLETION_VERIFICATION.json) | 2072唯一项、171328首回合、episodes、36图、区间 |
| 统一视频 | [视频manifest](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/fine_response/results/videos/manifest.json)；[解码核验](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/fine_response/results/VIDEO_DECODE_VERIFICATION.json) | 12段v2；失败版仅作证据保留 |
| 延迟机制审计 | [宏观审计](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/priority_delay_audit/MACRO_REPRODUCTION_AUDIT.md)；[原生消融](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/priority_delay_audit/diagnostic_results/ASSESSMENT.md) | CPU接口合同、来源与4096诊断回合 |
| 本地数据备份 | [当前快照状态](C:/Users/21045/Documents/Codex/2026-09-14/ti/backups/microduck-local-20261013/BACKUP_STATUS.json) | 新成果＋继承的训练/源码/模型；逐文件SHA；非异地备份 |
| 固定命令任务 | [四模型任务结果](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/task_protocol_v2/four_model_final/four_model_results.json) | 48job与逐回合记录 |
| 任务统计复核 | [统计核验报告](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/mechanism_audit/episode_uncertainty/REPORT.md) | 6144回合重算与区间 |
| 上游安全审计 | [安全覆盖审计](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/upstream_audit/MICRODUCK_SECURITY_GAP_AUDIT.md) | 引用代码、运行时边界 |
| 独立seed确认 | [评价器](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/sensor_fault_benchmark/run_independent_fault_evaluator.py)；[分析脚本](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/sensor_fault_benchmark/analyze_independent_confirmation.py) | [确认报告](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/sensor_fault_benchmark/independent_confirmation/REPORT.md)；results、summary、raw_episodes |
| 脉冲拆分 | [协议](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/sensor_fault_benchmark/PULSE_MECHANISM_PROTOCOL.md)；[运行脚本](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/sensor_fault_benchmark/run_pulse_mechanism.py)；[手操说明](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/sensor_fault_benchmark/PULSE_MECHANISM_RUNBOOK.md) | [最终结果](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/sensor_fault_benchmark/pulse_mechanism/results.json)；progress、manifest、run.log、raw_episodes |
| 小型BC | [顺序脚本](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/curriculumtrap_pilot/run_bc.py)；[报告](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/curriculumtrap_pilot/REPORT.md) | ledger、样本与MSE |
| 完整actor顺序 | [脚本](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/mechanism_audit/run_full_width_order.py)；[报告](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/mechanism_audit/full_width_order_pilot/REPORT.md) | 模型、case、raw数据 |
| clean恢复 | [脚本](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/mechanism_audit/run_common_clean_recovery.py)；[报告](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/mechanism_audit/full_width_clean_recovery/REPORT.md) | 十策略、60case及校验 |
| 归一化确认 | [确认决策](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/mechanism_audit/CONFIRMATION_DECISION.md)；[后续决策](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/mechanism_audit/CONTINUATION_DECISION.md) | 离线条件与normalization_confirmation |
| replay | [replay决策](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/mechanism_audit/REPLAY_DECISION.md)；[闭环报告](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/mechanism_audit/replay_fork_pilot/REPORT.md) | 分叉MSE、闭环基线 |
| 安全预处理 | [报告](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/mechanism_audit/sim_fall_filter/REPORT.md) | 信号、报警时刻、artifact_inventory |
| normalizer探针 | [报告](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/mechanism_audit/normalizer_resume_probe/REPORT.md) | 内存副本、统计更新对照 |
| 真实来源 | [来源审计](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/mechanism_audit/resume_provenance_audit/REPORT.md) | 244 checkpoint合同与谱系 |
| 零更新克隆 | [中文报告](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/mechanism_audit/ppo_clone_baseline/REPORT_ZH.md) | 字节/同观测/独立仿真核验 |
| 整体文件盘点 | [JSON清单](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/EXPERIMENT_FILE_MANIFEST.json)；[清单生成器](C:/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/build_complete_manifest.ps1) | 有盘点时间边界的全量路径记录 |

最终checkpoint路径：

- seed42：/home/deuler/microduck_rl/logs/rsl_rl/velocity/2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2/model_3999.pt
- seed123：/home/deuler/microduck_rl/logs/rsl_rl/velocity/2026-09-22_19-08-01_walk_baseline_4096_seed123_4000_v1/model_3999.pt
- seed2026：/home/deuler/microduck_rl/logs/rsl_rl/velocity/2026-09-29_10-44-28_walk_baseline_4096_seed2026_4000_v1_resume3250_quiet/model_3999.pt

源码锚点：/home/deuler/microduck_rl/src/mjlab_microduck/tasks/microduck_velocity_env_cfg.py；导出使用仓库scripts/export.py，不能遗漏观测归一化。

<a id="terms"></a>

## 附录A：高频术语

| 名词 | 通俗解释与小例子 | 在本项目中的位置/易错点 |
|---|---|---|
| 端侧（on-device） | 模型在机器人本机推理，不必每步请求云端 | 我们当前验证的是仿真与导出；还没验证真实板载时延 |
| 策略（policy） | 把“现在看到什么”变成“下一步怎么动”的函数 | 61维观测进入actor，输出14维原始动作 |
| 闭环（closed loop） | 动作改变状态，状态再反馈到下一次动作 | 错动作会改变脚与地面接触，不能只看一次模型输出 |
| 本体观测（proprioception） | 机器人对自身的测量，例如角速度、关节角和速度 | 本项目不是摄像头识别；“眼镜混淆分类”只是类比 |
| Actor / Critic | actor负责选动作；critic训练时估计状态价值 | critic不是一个部署时逐帧检查actor的安全审查器 |
| PPO | 根据仿真轨迹改善策略、并约束一次更新别过猛的RL算法 | 不能把“监督更新PPO actor”简称成“又跑了PPO” |
| 回报（return/reward） | 回合或片段内奖励的累计，包含跟踪、姿态、惩罚等 | 奖励权重/课程变化时，不同阶段回报不能直接横比 |
| DR（domain randomization） | 训练时改变质量、摩擦、延迟等，让策略见过多种条件 | 覆盖变量范围不代表覆盖所有时间顺序或现实故障 |
| Curriculum（课程） | 训练难度/参数随训练进展变化 | 合法课程不是攻击；恶意污染需要单独权限和因果证据 |
| Seed（随机种子） | 随机数生成器起点，例如42 | 训练seed改变最终模型；评估seed改变测试随机条件，两者不能混算 |
| Rollout / Episode / Iteration | rollout是采样片段；episode是从初始化到终止的回合；iteration是一轮采样和更新 | 24步rollout可以跨越回合；4000迭代不是4000回合 |
| Checkpoint / ONNX | checkpoint像训练存档；ONNX像用于推理的模型包 | checkpoint有优化器等训练状态；ONNX不等于完整续训存档 |
| Normalization（归一化） | 用均值/尺度把不同输入整理到便于网络处理的范围 | 类似把厘米换到共同尺度；改错尺度可改行为，但真实污染需证据 |
| BC / Teacher / Student | BC模仿老师的动作；teacher提供标签，student学习 | 像照着答案练，不是自己通过PPO奖励探索；离线答得像不保证走得稳 |
| Pilot / Gate / Ablation | pilot是小预算试验；gate是是否扩大；ablation是拆掉一个因素看变化 | 没过gate要留反证；“未测”不是“存活率0%” |

> **【阅读提醒】“安全”至少有四层：文件/数值合法、关节物理约束、闭环存活、任务完成。输出是有限数只满足第一层；没有跌倒只支持部分第三层；原地站着不等于转向任务成功。**


<a id="statistics"></a>

## 附录B：指标与统计解释


### B.1 常见指标及单位

| 指标 | 含义/计算直觉 | 好坏与容易误读的点 |
|---|---|---|
| Survival rate | 首回合在规定时长存活的比例 | 20秒存活不是永久可靠或完成命令 |
| Fell-over rate | 因fell_over终止的比例 | 不是全部失败；还可能有出界/NaN等原因 |
| Mean episode seconds | 首回合实际持续多久的平均值 | 超时者被20秒截断；不是全部人的真实跌倒时间 |
| vx绝对误差（m/s） | 目标vx与实际vx之差的绝对值，再取平均 | 目标0.3实际0.1，瞬时误差0.2m/s |
| XY速度误差（m/s） | 二维差向量的长度 | 同时包含前向跟踪和横向漂移，不能冒称vx误差 |
| yaw误差（rad/s） | 转向角速度与目标差 | 1rad约57.3度；越小通常越接近转向命令 |
| 平面速度（m/s） | sqrt(vx²+vy²) | Standing/原地Turning目标为0，越大可能越漂移 |
| Action delta L2 | 相邻原始14维动作差的向量长度 | 是动作突变代理，不是机械关节加速度或力矩 |
| Perturbation L2 | 不同传感器字段差向量的长度 | 单位混合，不能解释成物理能量或与不同通道幅度直接等价 |
| Max pre-step tilt | 每步推进前记录的最大倾斜 | 可能遗漏终止物理帧，不能当完整峰值 |
| Action MSE | student动作与teacher标签平方误差均值 | 离线模仿指标，不是任务成功、跌倒率或安全证明 |
| NaN/Inf与bounds | 数值异常/场地越界计数 | 场地越界不是关节限位；0计数不代表所有风险为0 |

### B.2 为什么要看寿命/生存曲线

假设A走20秒才结束、B在2秒跌倒，两者平均速度误差都0.2m/s，不能说它们一样可靠：B少经历18秒风险。报误差时必须同时报存活/寿命和有效采样时间。后续可画“时间t仍未跌倒的比例”，区分启动就失败和后段累积失败。

20秒超时是右删失（right censoring）：只知道直到观察结束还没倒，不知道21秒是否跌倒。NaN/出界等其他终止不能无说明地当普通跌倒或无信息删失。中期cpu_analysis_2026-10-12已生成40ms额外延迟的事件未发生曲线，任一失败终止作为事件、20秒存活保留至端点；它是固定中期快照的描述，不是全部最终条件的生存推断。

### B.3 CI、Bootstrap、Wilson与统计显著性

- **置信区间（CI）**：描述估计不确定性，不是“95%回合在此范围内”，也不是安全保证。应写清对哪个固定模型/种子层级作推断。
- **Bootstrap**：对已有样本重复重抽，观察估计值波动。分层bootstrap先抽评估seed，再在其内抽回合；只有3个seed，高层不确定性估计很有限。重抽不能制造新的独立训练模型。
- **Wilson区间**：适合比例的常用区间；把384回合直接合池时若忽略组依赖，只能作有条件的描述性区间。
- **统计显著性**：需预先明确假设与有效独立单位。大量探索条件会增加偶然差异，不能挑最显著的一格就当确认结论。
- **等价性**：没发现显著差异不等于证明相等；“正常表现相近”要限定具体指标。当前Turning漂移等差别不支持全正常行为等价。
- **本轮配对图阴影**：三eval-seed均值重采样的完整包络等同极值范围，不是95%CI；只有三个seed时不能把平滑阴影当可靠训练总体不确定性。共享clean与嵌套污染索引使网格相关，11个三seed同向下降格不是11次独立训练确认。
- **消融（ablation）**：一次只改一个因素帮助解释机制。clean尾段与Adam同时变化不是二者分离消融；startup与walking脉冲次数不同也不是完美同预算对照。

### B.4 四级证据与一句话边界

| 证据 | 可说 | 不能直接说 |
|---|---|---|
| 代码审计 | 某接口没编码age/valid mask；某路径接受某副本 | 任意真实攻击都可成功 |
| 人为机制探针 | 修改统计能影响更新路径 | 真实checkpoint已经被投毒 |
| 闭环故障实验 | 固定模型在规定故障下更易失稳 | 存在恶意训练者、触发器或实体后门 |
| 恢复/消融 | 某备选解释被削弱/仍未排除 | 机制唯一且普遍成立 |

“鲁棒性缺陷”是某输入变化下性能降低；“投毒”要求攻击者影响训练/数据来源；“后门”还要求明确的触发行为与干净条件性质。三者不是程度递增的同义词。



<a id="references"></a>

## 附录C：参考文献与阅读边界

以下按用途组织文献入口，不构成系统综述。论文报告核对了4篇方法近邻的原文入口；10月12日另有11篇相关实验章节/图表阅读记录，不等于全部证明和补充材料精读。平台、攻击权限与我们的实测必须分开，不据此宣称无人研究或领域饱和。

### C.1 运动策略与鲁棒性

| 原文入口 | 对本研究的用途 | 迁移边界 |
|---|---|---|
| [RMA，RSS 2021](https://www.roboticsproceedings.org/rss17/p011.html) | 理解历史观测、隐变量与快速运动适应 | 基础MicroDuck不是RMA在线适应模型 |
| [Robust Deep RL against Adversarial State Observations，NeurIPS 2020](https://proceedings.neurips.cc/paper_files/paper/2020/hash/f0eb6568ea114ba6e293f903c34d7488-Abstract.html) | 观测扰动与闭环鲁棒RL问题形式化 | 其基准不等于MicroDuck执行器和接触系统 |
| [Deep RL at the Edge of the Statistical Precipice，NeurIPS 2021](https://proceedings.neurips.cc/paper/2021/hash/f514cec81cb148559cf475e7426eed5e-Abstract.html) | 少量训练run下统计不确定性与评估方法 | 不为本项目权重或录用概率背书 |
| [Rethinking Robustness Assessment，RSS 2024](https://arxiv.org/abs/2405.12424) | 时序、多模态腿式控制器测试与现实预算 | 组合/时序本身已有近邻，不是我们的独有创新 |
| [Empirical Design in RL，JMLR 2024](https://www.jmlr.org/papers/v25/23-0183.html) | 敏感性取值、实验偏差和比较设计 | 加密测点提高证据，不能替代机制贡献 |
| [RL with Random Delays，ICLR 2021](https://arxiv.org/abs/2010.02966) | 分离观测/动作年龄和延迟合同 | 延迟感知训练与冻结部署故障是不同问题 |

### C.2 训练污染、顺序与适应

| 原文入口 | 对本研究的用途 | 迁移边界 |
|---|---|---|
| [Policy Teaching via Environment Poisoning，ICML 2020](https://proceedings.mlr.press/v119/rakhsha20a.html) | 明确奖励/转移控制的训练期威胁模型 | 不证明仅重排合法DR能教出目标行为 |
| [Adaptive Reward-Poisoning Attacks against RL，ICML 2020](https://proceedings.mlr.press/v119/zhang20u.html) | 训练状态相关污染与攻击预算 | 改奖励与仅改顺序是不同权限 |
| [Accumulative Poisoning Attacks on Real-time Data，NeurIPS 2021](https://proceedings.neurips.cc/paper_files/paper/2021/hash/16d11e9595188dbad0418a85f0351aba-Abstract.html) | 累积影响、后续触发与路径记忆 | 不证明冻结MicroDuck正在持续学习 |
| [Online Data Poisoning Attacks，L4DC 2020](https://proceedings.mlr.press/v120/zhang20b.html) | 动态数据到达及攻击者建模 | 近期不转回部署期在线学习主线 |
| [CoTTA，CVPR 2022](https://openaccess.thecvf.com/content/CVPR2022/html/Wang_Continual_Test-Time_Domain_Adaptation_CVPR_2022_paper.html) | 错误累积、遗忘与恢复的设计启发 | 不是当前策略已实现的组件 |

DreamWaQ、Learning robust perceptive locomotion、EATA、持续学习腿式控制和test-time poisoning保留为扩展阅读关键词；在没有锁定具体论文版本与内容前，不用于新颖性排除结论。

### C.3 物理传感器与控制安全

| 原文入口 | 用途 | 限制 |
|---|---|---|
| [Injected and Delivered，USENIX Security 2018](https://www.usenix.org/conference/usenixsecurity18/presentation/tu) | IMU欺骗的物理可实现性背景 | 我们在actor观测层注入，没有证明硬件入口可达 |
| [Drift with Devil，USENIX Security 2020](https://www.usenix.org/conference/usenixsecurity20/presentation/shen) | 慢变操纵与检测规避背景 | 传感器操纵不等于训练课程污染 |

待核验条目单独列出，不将标题、平台细节和影响力写成已确认事实：

- [BADControl候选入口](https://www.usenix.org/conference/usenixsecurity26/presentation/burbano)：核对正式论文、控制器对象、触发条件与防御后再比较。
- [Slow Drift Temporal Poisoning候选入口](https://link.springer.com/article/10.1007/s44465-026-00048-7)：核对题名、任务、权限、年份与方法；不能仅凭相似命名判断我们的创新或重复。

### C.4 研究方法与刊会目录

- [DARPA Heilmeier Catechism](https://www.darpa.mil/about/heilmeier-catechism)：用目标、现状、差异、受益、风险、成本、时间和阶段验证组织研究问题；附录E给出本项目工作流，不声称DARPA规定我们的实验门槛。
- [CCF正式目录入口](https://www.ccf.org.cn/Academic_Evaluation/By_category/)：本次检索确认第七版正式发布公告；具体刊会分级仍应逐项核对下载目录与学校口径。
- [CCF人工智能类别](https://www.ccf.org.cn/Academic_Evaluation/AI/)及[机器人期刊目录项](https://www.ccf.org.cn/Academic_Evaluation/Cross_Compre_Emerging/zgjsjxhtjgjxskw/bl/2017-04-25/592169.shtml)：网页索引可能与最新下载文件不同，不能以搜索摘要代替完整目录审查。

<a id="publication"></a>

## 附录D：CCF投稿档位与证据建设建议

### D.1 评级口径与候选刊会

A/B/C对标CCF，不自定义“优秀/一般/较差”。CCF等级描述推荐刊会，不保证某篇文章的质量或录用机会；会议与期刊必须区分，学校成果认定以提交当年正式文件为准。

CCF第七版目录已正式发布，本次分类网页直读受405限制，不能声称完成全部最新分级核验。下表是研究定位与候选列表，部分沿用既有目录记录，**正式定刊前必须逐项对照最新正式目录**；不作为考核证明。

| 定位 | 候选刊会 | 本研究的证据建设建议 |
|---|---|---|
| CCF A伸展 | 安全：CCS、IEEE S&P、USENIX Security、NDSS；普适ML方法：ICML、NeurIPS、AAAI | 现实且新颖的受限攻击面，强因果机制，跨平台/实机外部效度，适应性对手与有效防御 |
| CCF B目标 | ICRA（会议）；IEEE Transactions on Robotics（期刊） | 完整方法，多训练seed、扰动/变换、机制消融、运行开销，HIL或受控实体实验 |
| CCF C候选定位，待核对当年分级 | IROS（会议）；EAAI、ESWA（期刊，按文章重心选择） | 即使单平台也需要明确机制/方法、充分基线、严谨协议和可复核数据，不能只有加噪观察跌倒 |
| 机器人主流，不能自行换算CCF | RA-L等 | 按领域影响力与当年目录分别判断；不能因未收录就说低质量，也不编造等价B |

安全完整性主题更贴近安全刊会，具身控制与可靠方法更贴近机器人刊会，普适训练机制才适合ML刊会。CCF分类和机器人社区地位不是同一尺度。

中国自动化学会等国内目录可作补充，但应提供具体当年条目；不根据名称自行映射“相当于CCF A/B/C”。国内中文期刊与国际刊会的要求、审稿周期和成果认定须分别确认。

### D.2 当前成果达到哪里

现有训练、任务和故障基准可以构成论文的实验底座与动机，但尚未形成稳健的新方法、唯一机制或实体证据。较现实的阶段性交流是workshop/实验报告/数据与应用工作；是否足够CCF C也依赖明确贡献和近邻比较，不能承诺录用。B/A是证据建设目标，不是目前已有成就。

“3–5训练seed”“有效防御”“HIL/实体”是本项目建议，不是这些刊会公开统一最低录用规则。128回合与大量仿真不能替代新颖性、现实权限和独立训练重复；实体实验本身也不能把普通方法自动升为A。

### D.3 方向与投稿的连接

- 故障指纹＋机制：先形成可复核平台与新的系统性解释，再考虑机器人/安全应用渠道。
- Behavioral Admission＋Shield：需验证正常效用、故障收益、延迟、资源开销与适应性失效，才有方法论文资格。
- CurriculumTrap：当前反证要求暂停该载体；若未来有原生PPO受限顺序污染、预算对照、机制和防御，再重新判断档位。
- TransformationTrap：须有真实转换权限与可达错误链，不能凭人为修改统计量提出高档投毒论文。
- 基础审计与备份工具：可以独立有工程价值，但不强行包装攻击创新。

不输出精确录用概率：没有校准数据，优先级评分也不能转换为录用率。

<a id="workflow"></a>

## 附录E：实验风格与科学工作流

以下是基于合作行为的工作建议，不是人格诊断或精确日期/时间统计。没有用户对话的日期不据此认定用户工作；自动后台运行与个人投入分别记录。本文不展开每日沿革。

### E.1 合作中体现的优势

1. **证据敏感**：明确要求“不允许胡编乱造”，并多次要求与官方、不同 seed、视频和原始数据交叉验证。
2. **视觉审查能力强**：发现短视频看不出差异、Turning 静止、Stress 不公平、倒地后 reset 不是自主恢复。很多实验错误正是被这一习惯抓出。
3. **会挑战直觉**：主动提出“安全限制为何不一定更好”，最终由数据证明静态滤波可能破坏闭环控制。
4. **持续推进能力强**：能够让数小时到十余小时训练连续完成，愿意做第二、第三 seed，而不是停在单次漂亮结果。
5. **重视实际约束**：考虑 GPU、噪声、时间预算、WSL 与 Linux 差异、备份和浏览器面板，具备工程研究意识。
6. **能接受负结果**：在 OrderTrap Gate-1 未过后，没有要求包装成功，而是允许转向训练期机制。

### E.2 需要改进的地方

1. **研究问题切换过快**：故障鲁棒性、在线自演化、后门、供应链、慢漂移和安全层曾并行扩张，容易让每条线都缺最后一公里。
2. **时间压力影响设计**：“两小时做完”“尽快”“额度快用完”会诱导先跑后定义；视频旧协议和 Stress 不公平就是典型代价。
3. **层次概念容易混合**：传感器攻击、训练投毒、部署期在线适应、模型替换和后门触发是不同攻击面；必须每次先写 victim state 是否会更新。
4. **曾把 survival 当任务成功**：Turning 100% 存活却几乎不转，说明任务语义需要连续指标。
5. **曾期待安全层必然提高总分**：防御会改变闭环分布，强滤波可能阻断必要纠正动作；安全、性能和干预率必须同时报告。
6. **协议冻结较晚**：评估看完后再讨论阈值会带来研究者自由度；后来撤回事后阈值是正确修正。
7. **备份和 manifest 应更早**：直到多轮训练后才集中备份，增加了单点丢失风险。

### E.3 十步科学工作流

#### 步骤 1：研究问题卡

每个 idea 开跑前只写一页：claim、victim、攻击者权限、允许修改的变量、禁止修改的变量、预期机制、最小反例、停止条件。

#### 步骤 2：证据标签

所有陈述分成四类：`代码确认`、`实验测得`、`文献报告`、`研究假设`。论文草稿禁止把后一类改写成前一类。

#### 步骤 3：协议版本化

在运行前冻结：commit、配置、模型 hash、训练/评估 seed、回合数、命令、注入位置、指标定义、统计方法。任何修改生成新版本，旧结果不覆盖。

#### 步骤 4：先做 Gate pilot

用 1–2 个模型、较少回合做筛选，并提前写 GO/NO-GO 条件。未过 gate 就记录负结果并停止，不通过反复扩大攻击来制造成功。

#### 步骤 5：正式多层随机性

> **【名词解释】可把训练seed看成不同“学生”，评估seed看成不同“考场”，episode看成每个考场的考题。一个学生考几百题，不等于几百个学生。固定模型的评估置信区间不能用来概括所有可能训练出的模型。128并行环境也可能共享随机化或计算结构，不能不解释地当128个完全独立受试者。**

把训练 seed 作为高层样本，把评估 seed 和 episode 作为低层样本。正式方法验证建议争取3–5个训练seed和至少3个评估seed，具体按问题与资源论证；这不是刊会统一规定。置信区间应明确推断对象，不能把一个模型的128个回合当128次独立训练。

#### 步骤 6：保存原始证据

必须保存逐回合 CSV/JSON、TensorBoard、checkpoint、ONNX、配置、commit、依赖、命令、stdout/stderr 摘要和校验值。聚合均值不可替代原始数据。

#### 步骤 7：自动完整性检查

每轮完成后自动检查键唯一、预期任务数、NaN/Inf、越界、视频帧数、ONNX 接口和 hash。失败时从最新有效 checkpoint/进度恢复。

#### 步骤 8：统计与视频双盲审查

数值负责总体结论；视频负责发现协议错误和行为语义。盲评答案键隔离，视频不得自动混入新回合。

#### 步骤 9：错误账本

维护 `assumption → observed contradiction → protocol fix → affected artifacts`。被新协议替代的结果标记superseded，不删除原始证据，以便解释研究如何收敛。

#### 步骤 10：里程碑备份

每个正式训练完成、协议冻结和论文图表生成后立即做：Git commit、模型/数据 hash、Windows 备份、远端代码备份。大模型可用 release/LFS，不要把 checkpoint 无选择地塞进普通 Git 历史。

### E.4 应持续避免的实验错误

1. 不把停用原型结果作为MicroDuck证据；平台、接口与动力学不同，必须独立验证。
2. 不预设安全限制全面优于无防御；闭环防御可能带来明显效用损失。
3. 用不固定命令的Stress片段比较模型会失去公平性；当前统一使用fixed Stress-forward。
4. 视频不让自动reset混入评分，否则观众无法区分一次失败与新回合。
5. 不将“没倒”当Turning成功；分开报告survival、yaw误差和平移漂移。
6. 不把仿真重置当自主恢复；fall recovery是独立策略任务。
7. 不在看完结果后增设二值任务成败阈值；当前报告连续指标。预先固定测量定义不等于冻结任务成功阈值。
8. 不根据单评估seed锁定模型排名；多seed重复并报告范围，训练seed与评估seed分开。
9. 不把基础PPO与在线学习攻击面混写；当前部署模型为冻结推理。
10. 不因线性延迟补偿听起来合理就认定有效；当前pilot反而显示退化。
11. 生成序列与实际消费horizon必须一致；同multiset主张只对完整、实际消费的1000步账本成立。
12. 名称不能代表创新；慢漂移相关论文入口仍须核验，贡献要落在具体训练期权限、机制与闭环证据上。
13. 不将“配置与随机化日程”示意图当作恶意DR已接入PPO：官方训练复现与独立监督pilot必须分开。
14. 不以部分clean指标接近宣称整体等价；Turning能力与平移漂移存在差异。
15. 脉冲0.80属于重力投影分量，不是躯干角；描述时同时写出启动step1–4与行走期周期脉冲。
16. 不把精确录用概率或高idea评分当承诺；分数须有透明口径，并随反证调整优先级。

### E.5 好点子的产生方法

好点子通常不是靠“突然灵感”得到的，而是长期维护问题地图，然后在**事实与现有解释不一致**的地方下手。[DARPA 的 Heilmeier Catechism](https://www.darpa.mil/about/heilmeier-catechism) 要求研究者回答目标、现状局限、新方法、受益者、风险、成本、时间和阶段考试；同时应持续思考领域中真正重要、且现有资源能推进的问题。把二者放到计算机与机器人实验中，可以归纳为以下套路。

#### 来源一：异常现象，而不是热门名词

研究人员会记录所有“不应该发生但发生了”的现象。例如：

- 四个模型 clean 都是 100%，故障下却相差数十个百分点；
- static clip 本应更安全，却让模型更容易跌倒；
- Turning 生存率 100%，视频却几乎静止；
- 相同架构和训练配方，不同 seed 出现不同脉冲弱点。

异常本身不是贡献。下一步要问：**哪一个隐藏变量能同时解释这些异常？** 我们训练路径、课程顺序和随机化时序只是候选解释；现有顺序实验不足以把故障指纹归因于它们。

#### 来源二：系统边界错位

成熟论文经常来自两个模块各自“正确”，组合后却失败：

- ONNX 结构检查正确，但不保证行为安全；
- 动作限幅能压小动作，却可能阻止必要恢复；
- domain randomization 覆盖了合法范围，却没有约束时间排列；
- walking policy 能抗推扰，但跌倒终止后不具备 stand-up 能力。

这类问题比“再加一种噪声”更有价值，因为它揭示的是接口假设不一致。

#### 来源三：把现有方法的默认假设翻过来

阅读论文时不要只问“方法是什么”，而要为每篇论文写一张 assumption card：

1. 它默认数据是 IID 还是有序流？
2. 默认模型冻结还是持续更新？
3. 默认攻击者能改幅值、标签、奖励，还是只能改顺序？
4. 默认安全由单帧阈值、长期统计还是行为结果定义？
5. 如果只取消其中一个假设，方法还成立吗？

CurriculumTrap 就来自取消“domain randomization 的出现顺序无关紧要”这一默认假设。

#### 来源四：先找最小可证伪实验

优秀研究者不会先训练十个大模型，而会优先攻击最大不确定性：

- 若冻结推理阶段的同 multiset 重排就能造成大退化，说明策略本身有时序敏感性；
- 若不能，则不要继续包装，转而测试训练路径依赖；
- 若固定 teacher 数据仅改 batch 顺序仍产生差异，说明优化路径是机制之一；
- 若只有 PPO 层出现，需检查 endogenous state distribution、critic bootstrap 和 curriculum 反馈。

这就是 Gate 实验的意义：OrderTrap 的 NO-GO 不是浪费，而是把问题空间从“推理顺序攻击”引向“训练路径依赖是否具有安全意义”的待验证问题。

#### 来源五：让负结果改变理论，而不是只改变参数

普通调参思路是“效果不强就加大幅度”；研究思路是“效果不强说明原机制可能错了”。当前两个例子：

- 线性外推失败后，不应继续放大外推系数，而应承认腿式接触动力学不满足该局部线性假设；
- Gate-1 没过后，不应增加观测噪声直到摔倒，而应把攻击状态移到真正存在路径记忆的训练过程。

#### 一套可执行的每周研究循环

1. **周一：问题地图**——只读 3–5 篇最接近主线的论文，为每篇写贡献、假设、证据和未覆盖边界。
2. **周二：矛盾账本**——整理代码/实验中与论文假设不一致的现象，最多保留三个候选问题。
3. **周三：Heilmeier 一页纸**——不用术语写清楚做什么、现状为何不够、谁关心、成本和中期考试。
4. **周四：最小反证实验**——用最小模型和最少回合先尝试推翻自己的 idea。
5. **周五：机制复盘**——不是只看有没有显著差异，而是判断哪个机制解释被支持或否定。
6. **每四周：方向淘汰**——只允许一条主线、一条备用线；其余进入 idea backlog，避免同时开五条线。

#### 好 idea 的五项评分

以下五问用于讨论idea，不设置固定总分准入线；执行优先级采用正文第四章的证据加权评分。

- **重要性**：解决后是否改变别人训练、部署或评价机器人的方式？
- **具体性**：能否写成一句可证伪命题，而不是“提高安全性”？
- **新颖性**：新的是攻击能力、机制、系统边界还是防御，而不只是换平台？
- **可实施性**：现有 GPU、代码和三个月时间能否得到第一版答案？
- **证据连续性**：是否能复用现有模型、故障协议和结果，而不是全部推倒重来？

研究体系的核心不是永远猜对，而是让每次实验都减少不确定性，并且让失败结果决定下一步。可复核与独立重复也对应这一点：代码、协议、原始数据和独立重复不是论文装饰，而是把一个有趣现象变成可信知识的条件。


<a id="verification"></a>

## 附录F：手工复核与导师汇报

### F.1 看代码时先找五个位置

1. 模型来源与SHA：是哪份checkpoint，是否包含normalizer，官方与本地是否明确区分。
2. 场景：固定命令、推扰、num_envs、控制周期、首回合时长。
3. 注入：字段slice、单位、起止步、变化规则，命令/历史动作是否不变。
4. 首回合掩码：首次done后停止累计，不把reset当恢复。
5. 保存与核验：逐回合记录、唯一键、有限数、manifest、模型/原始数据哈希和断点状态。

阅读顺序：独立故障评价器→运行编排→分析器。脉冲机制对应run_pulse_mechanism.py与PULSE_MECHANISM_RUNBOOK.md；手操前先查真实进程，禁止重复启动已有worker。不修改锁定输入去“看看会怎样”。

### F.2 从结果追到证据

以当前seed123行走联合脉冲19.01%为例：进入fine_response/results/results.json，筛选stage=confirmation、channel=all、alpha=1，定位81201/81202/81203三条128回合任务及原始CSV/SHA，合计73/384。不要用legacy启动脉冲、另一个协议或探索64回合替代。REPORT_DATA.json提供同一图点的原始job_id。

40case/2560与60case/3840属于两个监督阶段；相加可描述运算量，不能当同协议、独立的6400个统计样本。未过正常门槛的故障case没有测量值，不补0。结果complete也不代替原始数据重算。

模型输出一致与独立仿真轨迹逐位一致分开检查；原模型自身重复不同，是建立训练干预差异预算前需要处理的基线问题。

### F.3 导师汇报四段式

已经完成：真实MicroDuck PPO复现、三个本地最终模型及ONNX、统一任务/故障评估、逐回合核验与运行时审计；不是独立开发MicroDuck。

新增完成：N336项、T24个真实PPO续训分支与528评估项、人工有效剂量900项；三层共1764项/225792回合仅表示计算量，不作为同一总体。完整分析、协议总汇及最终备份已核验；本次是现有结果复盘和文档更新。

主要发现：正常存活不能代替任务能力或故障鲁棒性；T冻结统计条件仍有训练干预效应，clean尾段后多格恢复；900有局部额外脉冲退化但54配对格仅11格三eval seed均下降，来源异质且非统一单调。已有精细基准和原生延迟诊断仍是底座，不取代新三层对照。

反证与限制：N干净重校准本身失败，T的clean训练波动及F/U代价很大，终点统计交换关键格主要跟随权重侧；900干净更新亦可退化，三eval seed不等于训练重复。未证明通用持久投毒、后门、有效防御或实体安全层绕过；正常存活/NaN0也不是安全证书。

下一步：当前先完成“预处理兼容性与学习路径影响故障鲁棒性”的证据表达及文献定位；若另获实验授权，优先锁定一个T现象进行独立训练重复和clean对照，再考虑校准机制与局部加密。1944项补测取消、63run暂缓、监控暂停，均不自动恢复。171328回合旧精细基准、T续训与900人工状态分开报告。

