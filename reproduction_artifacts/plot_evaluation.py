"""Plot checkpoint and final-condition evaluation results."""

import json
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path("/mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction")
milestones = json.loads((ROOT / "checkpoint_evaluation.json").read_text())["results"]
conditions = json.loads((ROOT / "final_condition_evaluation.json").read_text())

iterations = [x["iteration"] for x in milestones]
success = [100 * x["success_rate"] for x in milestones]
falls = [100 * x["fell_over_rate"] for x in milestones]
xy = [x["mean_xy_velocity_error"] for x in milestones]
yaw = [x["mean_yaw_velocity_error"] for x in milestones]
delta = [x["mean_action_delta_l2"] for x in milestones]

fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
ax = axes[0, 0]
ax.plot(iterations, success, marker="o", label="20 s success")
ax.plot(iterations, falls, marker="o", label="fell over")
ax.set(title="Stress test: push every 0.5-1.0 s", xlabel="checkpoint iteration", ylabel="episodes (%)", ylim=(-3, 103))
ax.grid(alpha=0.3)
ax.legend()

ax = axes[0, 1]
ax.plot(iterations, xy, marker="o", label="XY velocity error")
ax.plot(iterations, yaw, marker="o", label="yaw velocity error")
ax.set(title="Command tracking under stress", xlabel="checkpoint iteration", ylabel="mean absolute error")
ax.grid(alpha=0.3)
ax.legend()

ax = axes[1, 0]
ax.plot(iterations, delta, marker="o", color="#7a5195")
ax.set(title="Action change under stress", xlabel="checkpoint iteration", ylabel="mean L2 action delta / step")
ax.grid(alpha=0.3)

labels = ["0.5-1 s\nstress", "3-6 s\ntrain-like", "no push"]
order = ["stress_push_0.5_to_1.0_s", "train_like_push_3_to_6_s", "no_push_within_episode"]
values = [100 * conditions[key]["success_rate"] for key in order]
ax = axes[1, 1]
bars = ax.bar(labels, values, color=["#ef5675", "#7a5195", "#2f4b7c"])
ax.bar_label(bars, fmt="%.1f%%")
ax.set(title="Final checkpoint: 20 s success", ylabel="episodes (%)", ylim=(0, 108))
ax.grid(axis="y", alpha=0.3)

output = ROOT / "plots" / "checkpoint_evaluation.png"
fig.savefig(output, dpi=160)
print(output)
