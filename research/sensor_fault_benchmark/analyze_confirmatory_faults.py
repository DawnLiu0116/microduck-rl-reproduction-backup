"""Validate and analyze the three-seed MicroDuck fault confirmation experiment."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT / "confirmatory_faults.json"
MODELS = ["official_alpha_walking", "seed42_iter3999", "seed123_iter3999"]
MODEL_NAMES = {
    "official_alpha_walking": "Official",
    "seed42_iter3999": "Seed 42",
    "seed123_iter3999": "Seed 123",
}
SEEDS = [1001, 2002, 3003]
FAULTS = ["clean", "delay_2", "freeze_8", "freeze_10", "freeze_12", "spike_100"]
FAULT_NAMES = {
    "clean": "Clean",
    "delay_2": "Delay 40 ms",
    "freeze_8": "Freeze 160 ms",
    "freeze_10": "Freeze 200 ms",
    "freeze_12": "Freeze 240 ms",
    "spike_100": "Structured spike",
}
METRICS = [
    "mean_episode_seconds",
    "mean_return",
    "mean_xy_velocity_error_mps",
    "mean_yaw_velocity_error_radps",
    "mean_action_delta_l2",
    "action_jump_rate_gt_1",
    "mean_max_action_abs",
    "mean_max_tilt_deg",
    "mean_sensor_perturbation_l2",
    "mean_max_sensor_perturbation_l2",
]


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return float("nan"), float("nan")
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def load_and_validate(path: Path, allow_incomplete: bool) -> tuple[dict, list[dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["results"]
    keys = [(row["model_label"], row["fault_name"], int(row["seed"])) for row in rows]
    if len(keys) != len(set(keys)):
        raise RuntimeError("Duplicate model/fault/seed rows found")
    expected = {(model, fault, seed) for model in MODELS for fault in FAULTS for seed in SEEDS}
    actual = set(keys)
    unexpected = actual - expected
    if unexpected:
        raise RuntimeError(f"Unexpected rows: {sorted(unexpected)}")
    if not allow_incomplete:
        missing = expected - actual
        if not payload.get("complete") or missing or len(rows) != 54:
            raise RuntimeError(f"Confirmation is incomplete; {len(missing)} rows missing")
    for row in rows:
        if int(row["episodes"]) != 128:
            raise RuntimeError(f"Unexpected episode count in {keys[rows.index(row)]}")
        if float(row["nan_state_rate"]) != 0.0:
            raise RuntimeError(f"NaN state in {keys[rows.index(row)]}")
        if float(row["out_of_terrain_rate"]) != 0.0:
            raise RuntimeError(f"Out-of-terrain termination in {keys[rows.index(row)]}")
    return payload, rows


def write_jobs(rows: list[dict], path: Path) -> None:
    flattened = []
    for row in rows:
        item = dict(row)
        item["fault_parameters"] = json.dumps(item["fault_parameters"], sort_keys=True)
        flattened.append(item)
    if not flattened:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flattened[0]))
        writer.writeheader()
        writer.writerows(flattened)


def aggregate(rows: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row["model_label"], row["fault_name"])].append(row)
    output = []
    for model in MODELS:
        for fault in FAULTS:
            group = sorted(groups.get((model, fault), []), key=lambda row: int(row["seed"]))
            if not group:
                continue
            successes = sum(int(row["success_count"]) for row in group)
            episodes = sum(int(row["episodes"]) for row in group)
            low, high = wilson(successes, episodes)
            seed_rates = [float(row["success_rate"]) for row in group]
            item = {
                "model_label": model,
                "model_name": MODEL_NAMES[model],
                "fault_name": fault,
                "fault_display": FAULT_NAMES[fault],
                "seed_count": len(group),
                "seeds": ",".join(str(int(row["seed"])) for row in group),
                "success_count": successes,
                "episodes": episodes,
                "success_rate": successes / episodes,
                "success_wilson95_low": low,
                "success_wilson95_high": high,
                "seed_success_rate_mean": mean(seed_rates),
                "seed_success_rate_std": stdev(seed_rates) if len(seed_rates) > 1 else 0.0,
                "seed_success_rate_min": min(seed_rates),
                "seed_success_rate_max": max(seed_rates),
                "fell_over_count": sum(int(row["fell_over_count"]) for row in group),
            }
            for metric in METRICS:
                item[metric] = mean(float(row[metric]) for row in group)
            output.append(item)
    return output


def write_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_summary(rows: list[dict], path: Path, complete: bool) -> None:
    lookup = {(row["model_label"], row["fault_name"]): row for row in rows}
    available_faults = [
        fault for fault in FAULTS if all((model, fault) in lookup for model in MODELS)
    ]
    if not available_faults:
        return
    x = np.arange(len(available_faults), dtype=float)
    width = 0.8 / len(MODELS)
    colors = ["#4c78a8", "#f58518", "#54a24b", "#2a9d8f"]
    fig, axes = plt.subplots(2, 2, figsize=(15, 9), constrained_layout=True)
    panels = [
        ("success_rate", "Survival success (%)", 100.0),
        ("mean_max_tilt_deg", "Mean maximum tilt (deg)", 1.0),
        ("action_jump_rate_gt_1", "Action-jump rate > 1 L2 (%)", 100.0),
        ("mean_xy_velocity_error_mps", "XY tracking error (m/s)", 1.0),
    ]
    for ax, (metric, title, scale) in zip(axes.flat, panels):
        for index, (model, color) in enumerate(zip(MODELS, colors)):
            values = [float(lookup[(model, fault)][metric]) * scale for fault in available_faults]
            positions = x + (index - (len(MODELS) - 1) / 2) * width
            if metric == "success_rate":
                lower = [
                    max(
                        0.0,
                        (float(lookup[(model, fault)]["success_rate"]) - float(lookup[(model, fault)]["success_wilson95_low"])) * 100,
                    )
                    for fault in available_faults
                ]
                upper = [
                    max(
                        0.0,
                        (float(lookup[(model, fault)]["success_wilson95_high"]) - float(lookup[(model, fault)]["success_rate"])) * 100,
                    )
                    for fault in available_faults
                ]
                error = np.array([lower, upper])
            else:
                error = None
            ax.bar(positions, values, width, label=MODEL_NAMES[model], color=color, yerr=error, capsize=2)
        ax.set_title(title)
        ax.set_xticks(x, [FAULT_NAMES[fault] for fault in available_faults], rotation=25, ha="right")
        ax.grid(axis="y", alpha=0.25)
        if metric == "success_rate":
            ax.set_ylim(0, 105)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=len(MODELS), loc="upper center", bbox_to_anchor=(0.5, 0.965))
    state = "complete 3-seed confirmation" if complete else "INCOMPLETE PREVIEW"
    fig.suptitle(f"MicroDuck sensor-fault confirmation — {state}", y=1.02)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def write_report(rows: list[dict], path: Path, complete: bool) -> None:
    lookup = {(row["model_label"], row["fault_name"]): row for row in rows}
    lines = [
        "# MicroDuck confirmatory sensor-fault results",
        "",
        "Status: **complete**." if complete else "Status: **incomplete preview; do not cite as final**.",
        "",
        "The table pools independent evaluation seeds. Wilson 95% intervals are computed from "
        "the pooled success count; seed-to-seed ranges are reported separately.",
        "",
        "| Condition | Model | Success | Wilson 95% | Seed range | Max tilt | Action jumps | XY error |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for fault in FAULTS:
        for model in MODELS:
            row = lookup.get((model, fault))
            if row is None:
                continue
            lines.append(
                f"| {FAULT_NAMES[fault]} | {MODEL_NAMES[model]} | "
                f"{row['success_count']}/{row['episodes']} ({pct(row['success_rate'])}) | "
                f"[{pct(row['success_wilson95_low'])}, {pct(row['success_wilson95_high'])}] | "
                f"{pct(row['seed_success_rate_min'])}–{pct(row['seed_success_rate_max'])} | "
                f"{row['mean_max_tilt_deg']:.2f} deg | "
                f"{100 * row['action_jump_rate_gt_1']:.2f}% | "
                f"{row['mean_xy_velocity_error_mps']:.3f} m/s |"
            )
    lines += [
        "",
        "## Interpretation constraints",
        "",
        "- Survival alone is not a complete safety measure; inspect tilt, action jumps, and tracking error.",
        "- Overlapping Wilson intervals do not support a claim of general statistical superiority.",
        "- The synchronous all-sensor faults are simulation stress tests, not measured hardware fault distributions.",
        "- No physical-robot or sim-to-real claim is supported by this experiment.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    payload, jobs = load_and_validate(args.source, args.allow_incomplete)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    complete = bool(payload.get("complete")) and len(jobs) == 54
    aggregated = aggregate(jobs)
    write_jobs(jobs, args.output_dir / "confirmatory_jobs.csv")
    write_csv(aggregated, args.output_dir / "confirmatory_aggregate.csv")
    plot_summary(aggregated, args.output_dir / "confirmatory_summary.png", complete)
    write_report(aggregated, args.output_dir / "CONFIRMATORY_FAULT_REPORT.md", complete)
    print(f"jobs={len(jobs)} aggregate_rows={len(aggregated)} complete={complete}")


if __name__ == "__main__":
    main()
