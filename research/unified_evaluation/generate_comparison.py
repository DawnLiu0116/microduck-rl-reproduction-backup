"""Generate factual comparison artifacts from the frozen protocol JSON files."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
PLOTS = ROOT / "plots"
SCENARIOS = ["Nominal", "Train-like", "Stress", "Forward", "Turning", "Standing"]
MODELS = ["seed42_iter3999", "seed123_iter3999"]
LABELS = ["Seed 42", "Seed 123"]
COLORS = ["#2878B5", "#D95319"]


def load_model(label: str) -> dict[str, dict]:
    path = RESULTS / f"{label}_unified_eval.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {row["scenario"]: row for row in payload["results"]}


data = [load_model(model) for model in MODELS]
PLOTS.mkdir(parents=True, exist_ok=True)

fig, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
x = np.arange(len(SCENARIOS))
width = 0.36

ax = axes[0, 0]
for index, (rows, label, color) in enumerate(zip(data, LABELS, COLORS)):
    values = np.array([rows[s]["success_rate"] * 100 for s in SCENARIOS])
    low = np.array([rows[s]["success_wilson95_low"] * 100 for s in SCENARIOS])
    high = np.array([rows[s]["success_wilson95_high"] * 100 for s in SCENARIOS])
    ax.bar(x + (index - 0.5) * width, values, width, label=label, color=color,
           yerr=np.vstack((values - low, high - values)), capsize=3)
ax.set_title("Success rate with Wilson 95% CI")
ax.set_ylabel("Success rate (%)")
ax.set_ylim(0, 108)
ax.set_xticks(x, SCENARIOS, rotation=20)
ax.legend()
ax.grid(axis="y", alpha=0.25)

ax = axes[0, 1]
for index, (rows, label, color) in enumerate(zip(data, LABELS, COLORS)):
    values = [rows[s]["mean_return"] for s in SCENARIOS]
    ax.bar(x + (index - 0.5) * width, values, width, label=label, color=color)
ax.set_title("Mean episode return")
ax.set_ylabel("Return")
ax.set_xticks(x, SCENARIOS, rotation=20)
ax.grid(axis="y", alpha=0.25)

ax = axes[1, 0]
for rows, label, color in zip(data, LABELS, COLORS):
    values = [rows[s]["mean_xy_velocity_error_mps"] for s in SCENARIOS]
    ax.plot(SCENARIOS, values, marker="o", linewidth=2, label=label, color=color)
ax.set_title("Mean XY velocity tracking error")
ax.set_ylabel("Error (m/s), lower is better")
ax.tick_params(axis="x", rotation=20)
ax.legend()
ax.grid(alpha=0.25)

ax = axes[1, 1]
for rows, label, color in zip(data, LABELS, COLORS):
    values = [rows[s]["mean_yaw_velocity_error_radps"] for s in SCENARIOS]
    ax.plot(SCENARIOS, values, marker="o", linewidth=2, label=label, color=color)
ax.set_title("Mean yaw-rate tracking error")
ax.set_ylabel("Error (rad/s), lower is better")
ax.tick_params(axis="x", rotation=20)
ax.legend()
ax.grid(alpha=0.25)

fig.suptitle("MicroDuck final-policy unified evaluation (128 episodes/scenario, eval seed 123)", fontsize=15)
plot_path = PLOTS / "seed42_vs_seed123_unified_evaluation.png"
fig.savefig(plot_path, dpi=180)
plt.close(fig)

rows_out = []
for scenario in SCENARIOS:
    for model, label, rows in zip(MODELS, LABELS, data):
        row = rows[scenario]
        rows_out.append({
            "model": model,
            "model_display": label,
            "scenario": scenario,
            "episodes": row["episodes"],
            "success_count": row["success_count"],
            "success_rate_percent": row["success_rate"] * 100,
            "success_wilson95_low_percent": row["success_wilson95_low"] * 100,
            "success_wilson95_high_percent": row["success_wilson95_high"] * 100,
            "fell_over_count": row["fell_over_count"],
            "mean_return": row["mean_return"],
            "mean_episode_seconds": row["mean_episode_seconds"],
            "mean_xy_velocity_error_mps": row["mean_xy_velocity_error_mps"],
            "mean_yaw_velocity_error_radps": row["mean_yaw_velocity_error_radps"],
            "mean_action_delta_l2": row["mean_action_delta_l2"],
            "nan_state_rate": row["nan_state_rate"],
        })

comparison_csv = RESULTS / "seed42_vs_seed123_comparison.csv"
with comparison_csv.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows_out[0]))
    writer.writeheader()
    writer.writerows(rows_out)

summary = [
    "# MicroDuck 双种子统一评估结果\n",
    "协议版本：1.0；每个模型、每个场景128回合；确定性策略；评估种子123；每回合最长20秒。\n",
    "| 场景 | Seed 42 成功 | Seed 123 成功 | Seed 42 回报 | Seed 123 回报 | Seed 42 XY误差 | Seed 123 XY误差 | Seed 42 yaw误差 | Seed 123 yaw误差 |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
]
for scenario in SCENARIOS:
    a, b = data[0][scenario], data[1][scenario]
    summary.append(
        f"| {scenario} | {a['success_count']}/128 ({a['success_rate']*100:.2f}%) | "
        f"{b['success_count']}/128 ({b['success_rate']*100:.2f}%) | "
        f"{a['mean_return']:.2f} | {b['mean_return']:.2f} | "
        f"{a['mean_xy_velocity_error_mps']:.4f} | {b['mean_xy_velocity_error_mps']:.4f} | "
        f"{a['mean_yaw_velocity_error_radps']:.4f} | {b['mean_yaw_velocity_error_radps']:.4f} |"
    )
summary.extend([
    "\n## 事实性结论\n",
    "- 两个模型在 Nominal、Forward、Turning、Standing 中均完成128/128回合，且所有场景的 nan_state 均为0。",
    "- Train-like 中 Seed 42 为125/128，Seed 123 为117/128；Seed 42 在本批评估中高6.25个百分点。",
    "- Stress 中 Seed 42 为92/128，Seed 123 为96/128；Seed 123 在本批评估中高3.125个百分点。",
    "- Turning 的平均 yaw 跟踪误差：Seed 42 为0.5219 rad/s，Seed 123 为0.1937 rad/s；Seed 123 的转向跟踪明显更接近0.6 rad/s命令。",
    "- 这些比例都带有抽样不确定性；图中给出Wilson 95%区间。单一评估种子和128回合不足以证明总体显著性。",
    "- 结果仅来自仿真，包含域随机化和推扰，但不等同于真实硬件验证。",
])
summary_path = ROOT / "SEED42_VS_SEED123_RESULTS.md"
summary_path.write_text("\n".join(summary) + "\n", encoding="utf-8")

print(plot_path)
print(comparison_csv)
print(summary_path)
