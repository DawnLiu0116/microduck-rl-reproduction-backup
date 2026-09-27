"""Validate, tabulate, and plot the completed sensor-fault screening scan."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "sensor_fault_scan.json"
CSV_OUT = ROOT / "sensor_fault_scan.csv"
PLOT_OUT = ROOT / "sensor_fault_heatmaps.png"
REPORT_OUT = ROOT / "SENSOR_FAULT_SCREENING_REPORT.md"
MODELS = ["official_alpha_walking", "seed42_iter3999", "seed123_iter3999"]
MODEL_NAMES = ["Official", "Seed 42", "Seed 123"]


def main() -> None:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = payload["results"]
    faults = [item["name"] for item in payload["faults"]]
    expected = {(model, fault) for model in MODELS for fault in faults}
    actual = {(row["model_label"], row["fault_name"]) for row in rows}
    if not payload.get("complete") or actual != expected or len(rows) != len(expected):
        raise RuntimeError("Incomplete or duplicate scan")
    if any(float(row["nan_state_rate"]) != 0.0 for row in rows):
        raise RuntimeError("NaN state occurred; inspect raw results before analysis")

    flat_rows = []
    for row in rows:
        flat = dict(row)
        flat["fault_parameters"] = json.dumps(flat["fault_parameters"], sort_keys=True)
        flat_rows.append(flat)
    with CSV_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat_rows[0]))
        writer.writeheader()
        writer.writerows(flat_rows)

    lookup = {(row["model_label"], row["fault_name"]): row for row in rows}
    metrics = [
        ("success_rate", "Survival success (%)", lambda x: 100 * x, "RdYlGn", 0, 100),
        ("mean_xy_velocity_error_mps", "XY tracking error (m/s)", lambda x: x, "YlOrRd", None, None),
        ("mean_max_tilt_deg", "Mean maximum tilt (deg)", lambda x: x, "YlOrRd", None, None),
        ("action_jump_rate_gt_1", "Action-jump rate (%)", lambda x: 100 * x, "YlOrRd", None, None),
    ]
    fig, axes = plt.subplots(4, 1, figsize=(17, 11), constrained_layout=True)
    for ax, (metric, title, transform, cmap, vmin, vmax) in zip(axes, metrics):
        data = np.array(
            [[transform(float(lookup[(model, fault)][metric])) for fault in faults] for model in MODELS]
        )
        image = ax.imshow(data, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
        ax.set_yticks(range(len(MODELS)), MODEL_NAMES)
        ax.set_xticks(range(len(faults)), faults, rotation=35, ha="right")
        ax.set_title(title)
        for y in range(data.shape[0]):
            for x in range(data.shape[1]):
                value = data[y, x]
                label = f"{value:.0f}" if metric == "success_rate" else f"{value:.2f}"
                ax.text(x, y, label, ha="center", va="center", fontsize=7, color="black")
        fig.colorbar(image, ax=ax, fraction=0.015, pad=0.01)
    fig.suptitle("MicroDuck sensor-fault screening — Forward, seed 5005, 64 episodes/job")
    fig.savefig(PLOT_OUT, dpi=180)

    lines = [
        "# MicroDuck sensor-fault screening results",
        "",
        "Screening design: Forward command, evaluation seed 5005, 64 episodes per model/fault, "
        "three policies and sixteen conditions (3072 episodes total).",
        "",
        "This is a one-seed screening experiment. It identifies candidates for confirmatory "
        "three-seed evaluation but does not establish statistical superiority.",
        "",
        "## Per-model worst observed conditions",
        "",
        "| Model | Lowest survival | Largest XY error | Largest tilt | Largest action-jump rate |",
        "|---|---|---|---|---|",
    ]
    for model, display in zip(MODELS, MODEL_NAMES):
        model_rows = [lookup[(model, fault)] for fault in faults]
        worst_success = min(model_rows, key=lambda row: (row["success_rate"], row["mean_episode_seconds"]))
        worst_xy = max(model_rows, key=lambda row: row["mean_xy_velocity_error_mps"])
        worst_tilt = max(model_rows, key=lambda row: row["mean_max_tilt_deg"])
        worst_jump = max(model_rows, key=lambda row: row["action_jump_rate_gt_1"])
        lines.append(
            f"| {display} | {worst_success['fault_name']} "
            f"({100*worst_success['success_rate']:.1f}%) | "
            f"{worst_xy['fault_name']} ({worst_xy['mean_xy_velocity_error_mps']:.3f} m/s) | "
            f"{worst_tilt['fault_name']} ({worst_tilt['mean_max_tilt_deg']:.1f} deg) | "
            f"{worst_jump['fault_name']} ({100*worst_jump['action_jump_rate_gt_1']:.2f}%) |"
        )
    lines += [
        "",
        "## Interpretation rules",
        "",
        "- Compare each fault with the clean row for the same model.",
        "- A 100% survival rate does not imply successful command following; inspect XY error.",
        "- A large action-jump or tilt increase without falls is still a safety degradation.",
        "- Severe structured spikes are stress tests, not estimates of ordinary sensor noise.",
        "- Only degraded and scientifically interesting conditions should advance to the "
        "128-episode, three-evaluation-seed confirmatory stage.",
    ]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(CSV_OUT)
    print(PLOT_OUT)
    print(REPORT_OUT)


if __name__ == "__main__":
    main()
