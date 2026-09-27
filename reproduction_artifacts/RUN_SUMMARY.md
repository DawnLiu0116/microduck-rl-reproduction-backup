# MicroDuck 平地速度基线复现报告

## 运行配置

- 任务：`Mjlab-Velocity-Flat-MicroDuck`
- 代码提交：`cb70b792312d559a4da09064d92009079671815f`（`develop`）
- 并行环境数：4096
- agent seed：42
- PPO 迭代：4000（日志迭代 0–3999）
- 每环境每迭代步数：24
- 累计 transition：393,216,000
- 检查点间隔：50
- 最终检查点：`model_3999.pt`
- TensorBoard 中记录的总经过时间：43,118 秒，约 11.98 小时；逐迭代 `collection_time + learning_time` 求和也是约 11.98 小时。

## 训练结果

| 指标 | 测量值 |
|---|---:|
| 最终平均回报 | 118.5304 |
| 最高平均回报 | 127.9663（迭代 1438） |
| 最终平均回合长度 | 960.2600 |
| `nan_state` 最大记录值 | 0 |
| 最终 XY 速度误差日志值 | 0.4368 |
| 最终 yaw 速度误差日志值 | 1.0394 |
| 最终 mean action acceleration | 0.3320 |
| 最终 mean slip velocity | 0.0201 |
| 最终 policy mean std | 0.1759 |
| 最终吞吐日志值 | 31,382 steps/s |

曲线显示回报和回合长度在早期快速上升，之后随 curriculum 阶段变化出现若干台阶和回落，末期稳定在高于初期的区间。最高回报出现在迭代 1438，最终回报略低；这不等于训练失败，因为后续 curriculum 难度与权重发生了变化。动作加速度、脚滑速度和策略标准差均明显下降并在后期进入平台期。

`Episode_Termination/fell_over=0.25` 和 `time_out=4.0417` 是训练日志聚合项，不能直接解释为 25% 跌倒率或 404% 超时率。要得到百分比，仍需用固定评估协议逐回合计数。

## 视频对比

已为迭代 0、500、1000、2000、3000、3999 生成六段视频。所有视频都使用：

- 单环境
- seed 123
- 相同默认相机
- 640x480
- 500 帧，即按 50 Hz 控制频率对应 10 秒仿真时间
- play 配置中的相同 domain randomization 和每 0.5–1.0 秒一次的外力推扰设置

六段视频均已逐帧解码验证：每段 500 帧、640x480、文件非空。`plots/milestone_video_contact_sheet.png` 给出了六段视频的中间帧对照。

## ONNX 验证

- 导出方式：官方 `scripts/export.py`
- actor 输入：float32 `[1,61]`
- actor 输出：float32 `[1,14]`
- `onnx.checker`：通过
- ONNX Runtime：CPUExecutionProvider 推理通过
- 零输入输出：全部有限，范围约 `[-1.0499, 1.7229]`
- 最终 checkpoint SHA-256：`6452204f7b5ecdec45aa2009b2b1f5fe60a852e039d385200a92d2b97284ec3d`
- 最终 ONNX SHA-256：`369b8e92ab05c95702a1e938f8c84ad18bc3a053e62c5783d427bb6724d7e83a`

## 产物目录

- `checkpoints/`：六个里程碑检查点
- `videos/`：六段固定条件对比视频
- `plots/`：训练曲线和视频接触表
- `tensorboard/`：原始 TensorBoard event 文件
- `metrics_history.csv`：逐迭代指标
- `metrics_summary.json`：最终与汇总指标
- `agent.yaml`、`env.yaml`：训练配置
- `environment.txt`：提交和依赖版本
- `SHA256SUMS.txt`：最终模型校验值

## 局限

这是单 seed 的仿真训练基线，不是多 seed 统计实验。视频用于阶段性定性对比，不替代批量回合评估。当前没有与官方发布模型做同协议数值对齐，没有完成安全扰动/防御实验，也没有实体机器人或 sim-to-real 结论。
