# MicroDuck 统一评估协议 v1.0

## 固定原则

- 每个最终模型使用相同脚本、相同场景参数和相同评估 seed。
- 每个场景至少 128 个环境，每个环境只统计首次回合。
- 策略使用确定性推理；回合上限 20 秒、控制频率 50 Hz。
- 保留 play 配置中的质量、质心、摩擦、编码器、执行器和传感器随机化。
- 评估期间不训练、不更新网络，不与训练进程并发运行。

## 六个场景

| 场景 | 推扰 | 速度命令 | 目的 |
|---|---|---|---|
| Nominal | 无 | 任务默认随机命令 | 基本步态与综合跟踪 |
| Train-like | 3–6 秒一次 | 任务默认随机命令 | 训练分布内稳定性 |
| Stress | 0.5–1.0 秒一次 | 任务默认随机命令 | 分布外高频推扰 |
| Forward | 无 | `[0.3, 0, 0]` | 前进速度跟踪 |
| Turning | 无 | `[0, 0, 0.6]` | 原地转向跟踪 |
| Standing | 无 | `[0, 0, 0]` | 静态稳定和漂移 |

固定命令场景同时把头部和身体姿态命令置零，避免额外命令影响单项指标。

## 主要指标

- 20 秒成功率、成功数和 Wilson 95% 区间
- 跌倒率、跌倒数和 Wilson 95% 区间
- 平均存活时间与平均回报
- XY 速度平均绝对误差（m/s）
- yaw 速度平均绝对误差（rad/s）
- 每控制步动作变化的 14 维 L2 范数
- NaN 与地形越界终止率
- 实际命令均值，用于检查固定命令是否正确生效

## seed 42 最终模型运行命令

```bash
cd /home/deuler/microduck_rl
uv run python /mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/unified_evaluation/run_unified_evaluation.py \
  --model-label seed42_iter3999 \
  --checkpoint /home/deuler/microduck_rl/logs/rsl_rl/velocity/2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2/model_3999.pt \
  --episodes 128 \
  --seed 123 \
  --output-dir /mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/unified_evaluation/results
```

seed 123 完成后只需要替换 `--model-label` 和 `--checkpoint`。两个模型必须在六个场景全部完成后再做均值和差异比较。
