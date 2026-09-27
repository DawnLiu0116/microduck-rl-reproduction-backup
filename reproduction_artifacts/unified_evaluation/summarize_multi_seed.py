"""Create the multi-seed comparison plot and factual Chinese summary."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent / "multi_seed"
AGGREGATE_CSV = ROOT / "multi_seed_aggregate.csv"
PROGRESS_JSON = ROOT / "progress.json"
PLOT_PATH = ROOT / "multi_seed_comparison.png"
REPORT_PATH = ROOT / "MULTI_SEED_RESULTS.md"
SCENARIOS = ["Nominal", "Train-like", "Stress", "Forward", "Turning", "Standing"]
MODELS = ["seed42_iter3999", "seed123_iter3999"]
DISPLAY = {"seed42_iter3999": "Seed 42", "seed123_iter3999": "Seed 123"}
COLORS = {"seed42_iter3999": "#2878B5", "seed123_iter3999": "#D95319"}


with AGGREGATE_CSV.open(encoding="utf-8") as handle:
    aggregate_rows = list(csv.DictReader(handle))
aggregates = {(row["model_label"], row["scenario"]): row for row in aggregate_rows}
raw_rows = json.loads(PROGRESS_JSON.read_text(encoding="utf-8"))["results"]
raw = {(row["model_label"], row["scenario"], int(row["seed"])): row for row in raw_rows}

fig, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
x = np.arange(len(SCENARIOS))
width = 0.36

ax = axes[0, 0]
for index, model in enumerate(MODELS):
    rows = [aggregates[(model, scenario)] for scenario in SCENARIOS]
    values = np.array([float(row["success_rate"]) * 100 for row in rows])
    low = np.array([float(row["success_wilson95_low"]) * 100 for row in rows])
    high = np.array([float(row["success_wilson95_high"]) * 100 for row in rows])
    ax.bar(
        x + (index - 0.5) * width,
        values,
        width,
        yerr=np.maximum(0.0, np.vstack((values - low, high - values))),
        capsize=3,
        label=DISPLAY[model],
        color=COLORS[model],
    )
ax.set_title("Success rate over 384 episodes (Wilson 95% CI)")
ax.set_ylabel("Success rate (%)")
ax.set_ylim(0, 106)
ax.set_xticks(x, SCENARIOS, rotation=20)
ax.legend()
ax.grid(axis="y", alpha=0.25)

ax = axes[0, 1]
hard_scenarios = ["Train-like", "Stress"]
eval_seeds = [1001, 2002, 3003]
positions = np.arange(len(eval_seeds))
for scenario, marker in zip(hard_scenarios, ("o", "s")):
    for model in MODELS:
        values = [raw[(model, scenario, seed)]["success_rate"] * 100 for seed in eval_seeds]
        ax.plot(
            positions,
            values,
            marker=marker,
            linewidth=2,
            linestyle="-" if model == MODELS[0] else "--",
            color=COLORS[model],
            label=f"{DISPLAY[model]} / {scenario}",
        )
ax.set_title("Success-rate variation across evaluation seeds")
ax.set_ylabel("Success rate (%)")
ax.set_xticks(positions, [str(seed) for seed in eval_seeds])
ax.set_xlabel("Evaluation seed")
ax.legend(fontsize=9)
ax.grid(alpha=0.25)

ax = axes[1, 0]
for model in MODELS:
    values = [float(aggregates[(model, scenario)]["mean_xy_velocity_error_mps"]) for scenario in SCENARIOS]
    ax.plot(SCENARIOS, values, marker="o", linewidth=2, label=DISPLAY[model], color=COLORS[model])
ax.set_title("Mean XY velocity tracking error")
ax.set_ylabel("Error (m/s), lower is better")
ax.tick_params(axis="x", rotation=20)
ax.legend()
ax.grid(alpha=0.25)

ax = axes[1, 1]
for model in MODELS:
    values = [float(aggregates[(model, scenario)]["mean_yaw_velocity_error_radps"]) for scenario in SCENARIOS]
    ax.plot(SCENARIOS, values, marker="o", linewidth=2, label=DISPLAY[model], color=COLORS[model])
ax.set_title("Mean yaw-rate tracking error")
ax.set_ylabel("Error (rad/s), lower is better")
ax.tick_params(axis="x", rotation=20)
ax.legend()
ax.grid(alpha=0.25)

fig.suptitle("MicroDuck independent multi-seed evaluation (3 seeds × 128 episodes)", fontsize=15)
fig.savefig(PLOT_PATH, dpi=180)
plt.close(fig)

lines = [
    "# MicroDuck 三评估种子统一评估结果\n",
    "- 评估种子：1001、2002、3003",
    "- 每个模型、场景和种子：128回合",
    "- 每个模型、场景合计：384回合",
    "- 策略：确定性推理；最长回合20秒",
    "- 本轮36个评估单元全部完成，所有 `nan_state_rate` 和 `out_of_terrain_rate` 均为0。\n",
    "| 场景 | Seed 42成功率 | Seed 123成功率 | Seed 42回报 | Seed 123回报 | Seed 42 XY误差 | Seed 123 XY误差 | Seed 42 yaw误差 | Seed 123 yaw误差 |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
]
for scenario in SCENARIOS:
    a = aggregates[(MODELS[0], scenario)]
    b = aggregates[(MODELS[1], scenario)]
    lines.append(
        f"| {scenario} | {int(a['success_count'])}/384 ({float(a['success_rate'])*100:.2f}%) | "
        f"{int(b['success_count'])}/384 ({float(b['success_rate'])*100:.2f}%) | "
        f"{float(a['mean_return']):.2f} | {float(b['mean_return']):.2f} | "
        f"{float(a['mean_xy_velocity_error_mps']):.4f} | {float(b['mean_xy_velocity_error_mps']):.4f} | "
        f"{float(a['mean_yaw_velocity_error_radps']):.4f} | {float(b['mean_yaw_velocity_error_radps']):.4f} |"
    )

train42 = aggregates[(MODELS[0], "Train-like")]
train123 = aggregates[(MODELS[1], "Train-like")]
stress42 = aggregates[(MODELS[0], "Stress")]
stress123 = aggregates[(MODELS[1], "Stress")]
turn42 = aggregates[(MODELS[0], "Turning")]
turn123 = aggregates[(MODELS[1], "Turning")]
lines.extend([
    "\n## 事实性解读\n",
    f"- Train-like：Seed 123为{float(train123['success_rate'])*100:.2f}%，Seed 42为{float(train42['success_rate'])*100:.2f}%，相差{(float(train123['success_rate'])-float(train42['success_rate']))*100:.2f}个百分点。",
    f"- Stress：Seed 42为{float(stress42['success_rate'])*100:.2f}%，Seed 123为{float(stress123['success_rate'])*100:.2f}%，相差{(float(stress42['success_rate'])-float(stress123['success_rate']))*100:.2f}个百分点。",
    f"- Stress种子间成功率标准差：Seed 42为{float(stress42['success_rate_between_seed_std'])*100:.2f}个百分点，Seed 123为{float(stress123['success_rate_between_seed_std'])*100:.2f}个百分点。Seed 123在这三个评估种子下更稳定，但平均成功率略低。",
    f"- Turning平均yaw误差：Seed 42为{float(turn42['mean_yaw_velocity_error_radps']):.4f} rad/s，Seed 123为{float(turn123['mean_yaw_velocity_error_radps']):.4f} rad/s；Seed 123更接近0.6 rad/s命令。",
    f"- Turning平均XY漂移：Seed 42为{float(turn42['mean_xy_velocity_error_mps']):.4f} m/s，Seed 123为{float(turn123['mean_xy_velocity_error_mps']):.4f} m/s；Seed 123转得更准，但平移漂移更大。",
    "- Train-like和Stress的Wilson 95%区间仍然重叠，因此当前差异不能直接表述为统计显著。",
    "- 先前单一评估种子123得出的Train-like排序与本次三独立种子合并结果不同，说明只用一个评估种子会产生不稳定结论。",
    "- 所有结果均来自仿真，不能替代真实硬件验证。",
])
REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(PLOT_PATH)
print(REPORT_PATH)
