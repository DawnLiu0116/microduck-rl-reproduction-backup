from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OURS = ROOT / "unified_evaluation" / "multi_seed" / "multi_seed_aggregate.csv"
OFFICIAL = Path(__file__).with_name("official_multi_seed_aggregate.csv")
OUT_CSV = Path(__file__).with_name("three_model_comparison.csv")
OUT_PNG = Path(__file__).with_name("three_model_comparison.png")

LABELS = {
    "official_alpha_walking": "Official alpha_walking (iter 3750)",
    "seed42_iter3999": "Reproduction seed 42 (iter 3999)",
    "seed123_iter3999": "Reproduction seed 123 (iter 3999)",
}
SCENARIOS = ["Nominal", "Train-like", "Stress", "Forward", "Turning", "Standing"]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


rows = read_rows(OFFICIAL) + read_rows(OURS)
rows.sort(key=lambda r: (list(LABELS).index(r["model_label"]), SCENARIOS.index(r["scenario"])))

with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
    fields = [
        "model_label", "display_name", "scenario", "total_episodes", "success_count",
        "success_rate_percent", "success_wilson95_low_percent", "success_wilson95_high_percent",
        "mean_return", "mean_xy_velocity_error_mps", "mean_yaw_velocity_error_radps",
        "mean_action_delta_l2", "nan_state_rate", "out_of_terrain_rate",
    ]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for r in rows:
        writer.writerow({
            "model_label": r["model_label"],
            "display_name": LABELS[r["model_label"]],
            "scenario": r["scenario"],
            "total_episodes": r["total_episodes"],
            "success_count": r["success_count"],
            "success_rate_percent": 100 * float(r["success_rate"]),
            "success_wilson95_low_percent": 100 * float(r["success_wilson95_low"]),
            "success_wilson95_high_percent": 100 * float(r["success_wilson95_high"]),
            "mean_return": r["mean_return"],
            "mean_xy_velocity_error_mps": r["mean_xy_velocity_error_mps"],
            "mean_yaw_velocity_error_radps": r["mean_yaw_velocity_error_radps"],
            "mean_action_delta_l2": r["mean_action_delta_l2"],
            "nan_state_rate": r["nan_state_rate"],
            "out_of_terrain_rate": r["out_of_terrain_rate"],
        })

lookup = {(r["model_label"], r["scenario"]): r for r in rows}
models = list(LABELS)
colors = ["#334E68", "#2A9D8F", "#E76F51"]
x = np.arange(len(SCENARIOS))
width = 0.24

fig, axes = plt.subplots(2, 1, figsize=(12, 9), constrained_layout=True)
for i, model in enumerate(models):
    vals = np.array([100 * float(lookup[(model, s)]["success_rate"]) for s in SCENARIOS])
    low = np.array([100 * float(lookup[(model, s)]["success_wilson95_low"]) for s in SCENARIOS])
    high = np.array([100 * float(lookup[(model, s)]["success_wilson95_high"]) for s in SCENARIOS])
    pos = x + (i - 1) * width
    axes[0].bar(pos, vals, width, label=LABELS[model], color=colors[i])
    yerr = np.vstack((np.maximum(vals - low, 0.0), np.maximum(high - vals, 0.0)))
    axes[0].errorbar(pos, vals, yerr=yerr, fmt="none", ecolor="#222", capsize=2, lw=0.8)
axes[0].set_ylabel("Success rate (%)")
axes[0].set_ylim(65, 102)
axes[0].set_xticks(x, SCENARIOS)
axes[0].grid(axis="y", alpha=0.25)
axes[0].legend(frameon=False, ncols=1, loc="lower left")
axes[0].set_title("Frozen protocol: 3 evaluation seeds x 128 episodes per scenario")

tracking = ["Forward", "Turning", "Standing"]
tx = np.arange(len(tracking))
for i, model in enumerate(models):
    vals = []
    for scenario in tracking:
        r = lookup[(model, scenario)]
        vals.append(float(r["mean_yaw_velocity_error_radps"]) if scenario == "Turning" else float(r["mean_xy_velocity_error_mps"]))
    axes[1].bar(tx + (i - 1) * width, vals, width, label=LABELS[model], color=colors[i])
axes[1].set_xticks(tx, ["Forward\nXY error (m/s)", "Turning\nyaw error (rad/s)", "Standing\nXY error (m/s)"])
axes[1].set_ylabel("Mean tracking error (lower is better)")
axes[1].grid(axis="y", alpha=0.25)
axes[1].set_title("Command tracking accuracy (metric depends on scenario)")

fig.savefig(OUT_PNG, dpi=180)
print(OUT_CSV)
print(OUT_PNG)
