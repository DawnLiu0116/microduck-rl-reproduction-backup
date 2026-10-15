# 全项目协议与baseline总汇（2026-10-15收尾版）

本表将已有项目档案、实际协议和完成收据分层整理；历史结果不重跑、不重复计数。各阶段回合不能合并为同一统计总体；旧文件名/计划规模不等于已完成证据。当前新完成内容仅N/T与有效剂量，旧成果是引用，不作为当天新增成果。

|工作层|基线/对照与实际范围|状态与主要证据|可比性/限制|
|---|---|---|---|
|Walker历史原型|非MicroDuck平台|已归档/停用；不恢复|不能与MicroDuck成功率混排；本次未重新审计原始Walker数据|
|MicroDuck原生PPO|本地42/123/2026，4096env×24step×4000轮，最终3999；官方策略另列|三个原模型及导出已完成，RUN_SUMMARY、既有总档案/上游审计|本地复现不等于官方权重或全部训练配置一致；训练日志termination不当评估百分比|
|统一冻结任务|Nominal/Train-like/Stress/Forward/Turning/Standing，20秒128首回合|unified_evaluation/UNIFIED_EVAL_PROTOCOL.md及既有结果|随机命令与固定命令不混；推扰频率不同|
|任务测量v2|四模型×四任务×三eval seed×128=6144回合|task_protocol_v2/measurement_v2_results.json；既有档案已核验|固定命令连续误差，存活不是任务合格；恢复事件阈值不是安全阈值|
|旧传感器筛查|四冻结模型，seed5005/64回合，噪声/bias/delay/freeze/spike|sensor_fault_benchmark/PROTOCOL.md|首34维注入，34:61保护；legacy启动脉冲step1–4不可当纯行走脉冲|
|新seed故障确认|四模型×六条件×三eval seed×128=9216回合|INDEPENDENT_CONFIRMATION_PROTOCOL.md及既有档案|41041/52052/63063；旧脉冲时序保持，不能替换为后来的walking pulse|
|精细冻结响应|2072唯一任务/171328首回合，确认612项/78336回合|fine_response/results/COMPLETION_VERIFICATION.json complete；12视频另有解码核验|探索64/确认128；paired账本不同N不等同；幅度/通道/时序/命令分层，不重复加确认子集|
|原生延迟诊断|四模型×两native设置×四条件=32项/4096回合|priority_delay_audit/diagnostic_results/VERIFICATION.json|仅seed1001；关闭native delay是反事实，不替换原基准；额外40ms不是总年龄|
|脉冲机制拆分|两模型×十条件×两seed×64=2560回合|PULSE_MECHANISM_PROTOCOL.md；旧档案记录运行完成但独立逐回合分析待完成|按通道/启动/频次对照；不把相关性当交互机制唯一识别。本次不自动扩展旧研究|
|BC/监督小模型、replay、归一化pilot|同teacher样本/标签、顺序/优化器/统计处理对照|mechanism_audit内协议、ORDER_PILOT_FINAL_DECISION/REPLAY_DECISION；原载体暂停|离线MSE不等于PPO、闭环安全；单teacher多采集不是多训练策略|
|完整actor监督顺序|40case/2560回合；正常门槛未过分支不扩故障|FULL_WIDTH_ORDER_PROTOCOL.md与COMMON_CLEAN_RECOVERY_PROTOCOL.md记录实测|实际40不是计划48；正常质量失败不是攻击成功|
|共同clean恢复|60case/3840回合；统一256clean监督更新/Adam重置|COMMON_CLEAN_RECOVERY_PROTOCOL.md及旧档案|与上一阶段不同模型状态；差异缩小反对持久污染，不将两阶段视为同一总体|
|零更新克隆/预处理/跌倒滤波|旧档案640回合克隆、12case/192回合窄预处理；其余按各协议|PPO_CLONE_PROTOCOL/FALL_FILTER/SIM_FALL_FILTER等|克隆输出等价不保证独立仿真bitwise；不称部署防御成功|
|V2 N推理统计坐标|336case/43008回合，固定原权重、recalibration/累计/等价补偿等|n/analysis/verification_and_summary.json完整独立核验|N3干净重校准Forward失败，N6下降不证明污染；30752回合有关节超限步骤|
|V2 T真实PPO续训|24训练分支×200新增rollout；528case/67584回合，150/200及统计交换|t/analysis/VERIFICATION.json、INTERPRETATION；24最终/56评估模型SHA|两源×两训练seed×TC/TI/T0×F/U；clean seed波动与恢复不完全均保留，不普遍外推；24792回合有关节超限步骤|
|有效剂量人工矩状态|75模型×四条件×三eval seed=900case/115200回合|effective_dose_response/FINAL_AUDIT.json、INTERPRETATION.md、配对图|w=.001… .1/p=0/.1/.5/1；同w clean配对，原权重不训练；Delay40地板仅诊断|
|CPU旧插值|174离线条件/522留出行；旧闭环只已有基线，不混GPU900项|normalization_cpu_curve/VERIFICATION.json；worker1103保持暂停|离线验证不是174项闭环；225插值评估不恢复|
|三方式补测|162模型已准备，原计划1944case；实测0项0回合|用户取消，channel_supplement/CANCELLED_BY_USER.md|准备/计划不是评估成果；不执行集中subset或全铺|
|63run大训练|63×2000新增rollout设计|暂缓，NORMALIZATION_LARGE_TRAINING_PLAN.md|未启动，不写成完成|

## 当前结论与完成边界

N336+T528=864项/110592回合；加主900为1764项/225792回合，仅表示不同实验计算量，不是可合并的训练重复。补测0，不计入2844上限。物理失败、低存活和运行软件错误分别保存，不过滤NaN或更改指标。主900正常Forward全存活但脉冲配对有局部下降和改善，未证明统一单调安全边界。

本次收尾覆盖新授权N/T/900、既往协议/baseline文档总汇、备份核验和当前档案更新；不把历史明确待分析的机制探索偷偷标为完成。没有新增训练、视频、实体、上传或防御曲线。完整协议文件SHA索引由protocol_inventory.json提供；冻结历史协议不因当前取消决定改写。

## 备份

N原备份收据746文件，T评估备份1310文件、训练备份168文件；最终新900数据/75模型/全部诊断/分析/取消凭据、最新总汇和协议索引另存effective-dose-final-20261015，以BACKUP_STATUS.json为实际完成凭证。所有路径已迁至D，同盘副本不是异盘容灾；旧收据中C盘措辞是迁移前快照，不据此重复迁移或删除junction。
