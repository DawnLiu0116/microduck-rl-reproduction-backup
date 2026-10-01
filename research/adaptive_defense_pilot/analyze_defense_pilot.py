#!/usr/bin/env python3
"""Validate and summarize the MicroDuck temporal-defense screening pilot."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "defense_pilot_v2.json"
CSV_OUT = ROOT / "defense_pilot_v2_summary.csv"
PLOT_OUT = ROOT / "defense_pilot_v2_survival.png"
REPORT_OUT = ROOT / "DEFENSE_PILOT_V2_REPORT.md"

DEFENSES = ["none", "static_clip", "naive_adaptive", "constrained_timestamp"]
LABELS = ["None", "Static clip", "Naive adaptive", "Constrained / timestamp"]
COLORS = ["#6b7280", "#f59e0b", "#2563eb", "#dc2626"]


def pct(value: float) -> str:
    return f"{100.0 * value:.1f}%"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


payload = json.loads(INPUT.read_text(encoding="utf-8"))
rows = payload["results"]
assert payload.get("complete") is True, "result file is not marked complete"
assert len(rows) == 24, f"expected 24 rows, got {len(rows)}"
keys = {(r["model_label"], r["fault_name"], r["defense"], r["seed"]) for r in rows}
assert len(keys) == 24, "duplicate experiment keys"
assert all(r["episodes"] == 64 for r in rows), "episode count mismatch"
assert all(r["nan_state_rate"] == 0 for r in rows), "NaN termination detected"
assert all(r["out_of_terrain_rate"] == 0 for r in rows), "out-of-terrain termination detected"

fields = [
    "model_label", "fault_name", "defense", "seed", "episodes", "success_count",
    "success_rate", "mean_return", "mean_xy_velocity_error_mps",
    "mean_max_tilt_deg", "action_jump_rate_gt_1", "mean_anomaly_score",
    "mean_intervention_fraction", "nan_state_rate", "out_of_terrain_rate",
    "timestamp_metadata_used",
]
with CSV_OUT.open("w", newline="", encoding="utf-8-sig") as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows({field: row[field] for field in fields} for row in rows)

lookup = {(r["model_label"], r["fault_name"], r["defense"]): r for r in rows}
models = ["seed123_iter3999", "seed2026_iter3999"]
faults = ["clean", "delay_2", "spike_100"]

fig, axes = plt.subplots(1, 2, figsize=(15, 6.0), sharey=True)
for ax, model in zip(axes, models, strict=True):
    x = np.arange(len(faults))
    width = 0.19
    for idx, (defense, label, color) in enumerate(zip(DEFENSES, LABELS, COLORS, strict=True)):
        values = [100 * lookup[(model, fault, defense)]["success_rate"] for fault in faults]
        bars = ax.bar(x + (idx - 1.5) * width, values, width, label=label, color=color)
        ax.bar_label(bars, fmt="%.0f", fontsize=8, padding=2)
    ax.set_title(model)
    ax.set_xticks(x, ["Clean", "Delay 40 ms", "Spike / 100 steps"])
    ax.set_ylim(0, 112)
    ax.grid(axis="y", alpha=0.25)
    ax.set_xlabel("Scenario")
axes[0].set_ylabel("Episode survival (%)")
handles, labels = axes[0].get_legend_handles_labels()
fig.suptitle("MicroDuck temporal-defense screening pilot (64 episodes, eval seed 5005)", y=0.985)
fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.935), ncol=4, frameon=False)
fig.tight_layout(rect=(0, 0, 1, 0.84))
fig.savefig(PLOT_OUT, dpi=180, bbox_inches="tight")
plt.close(fig)

table_lines = []
for model in models:
    for fault in faults:
        vals = [lookup[(model, fault, d)] for d in DEFENSES]
        table_lines.append(
            "| " + " | ".join(
                [model, fault] +
                [f"{v['success_count']}/64 ({pct(v['success_rate'])})" for v in vals]
            ) + " |"
        )

report = f"""# MicroDuck temporal-defense pilot v2

## Scope and validation

- Screening experiment only: 2 trained policies x 3 scenarios x 4 defenses x 64 episodes, one evaluation seed (5005).
- Completed rows: 24/24; unique keys: 24/24; total episodes: 1536.
- NaN-state terminations: 0; out-of-terrain terminations: 0.
- `delay_2` is a fixed two-policy-step delay (40 ms). `spike_100` is the existing structured pulse injected every 100 steps.
- The timestamp defense is given configured sensor age for the delay experiment. This is privileged metadata, so it is not a blind value-only detector.

## Survival results

| Model | Fault | None | Static clip | Naive adaptive | Constrained / timestamp |
|---|---|---:|---:|---:|---:|
{chr(10).join(table_lines)}

![Survival comparison](defense_pilot_v2_survival.png)

## What the pilot actually shows

1. **Clean behavior is preserved in v2.** All four methods reached 64/64 on both policies, with zero interventions for the constrained method. This fixes the v1 clean false-positive failure (seed123 constrained v1: 34/64, intervention fraction 0.1721).
2. **The proposed timestamp linear extrapolator fails on 40 ms delay.** It reduced both policies to 0/64, versus 5/64 and 7/64 with no defense. Intervention fractions were 0.9771 and 0.9600 and action-jump rates rose to 0.7308 and 0.7699. A first-order sensor projection is therefore not a valid delay solution for this closed-loop gait.
3. **The constrained spike repair also fails on seed123.** It reached 5/64 versus 12/64 with no defense; static clipping reached 4/64. The detector/replacement rule appears to alter legitimate fast motion or reconstruct the structured pulse poorly.
4. **Naive adaptive filtering is the only positive screening signal for seed123 spike.** Survival increased from 12/64 (18.8%) to 30/64 (46.9%), while maximum tilt fell from 57.53 to 43.21 degrees and action-jump rate from 0.0637 to 0.0447.
5. **That gain is not universal.** On seed2026 spike, no defense and naive adaptive both reached 52/64 (81.2%); constrained reached 51/64. Static clipping collapsed to 0/64. This reinforces the earlier observation that fault responses are policy-seed dependent.

## Decision

- Reject `constrained_timestamp` v2 as a deployable defense.
- Reject static clipping as a general defense.
- Keep naive adaptive filtering only as a promising baseline for structured spikes, not as a validated method.
- Do not run a broad three-seed confirmation of the rejected v2 method. The next defensible experiment is a narrow confirmation of `none` versus `naive_adaptive` for spike_100 on all trained policies and three evaluation seeds, followed by contamination tests that deliberately poison the adaptive statistics.

## Limitations

- One evaluation seed and 64 episodes per cell make this a screening result, not final statistical evidence.
- Only two policy-training seeds are included here.
- Survival is binary; the CSV also preserves return, tracking error, tilt, action jumps and intervention rates.
- Delay metadata was supplied by the benchmark, so timestamp compensation assumes an available freshness signal.

## Reproducibility

- Input SHA-256: `{sha256(INPUT)}`
- Protocol version: `{payload.get('protocol_version')}`
- Raw JSON: `defense_pilot_v2.json`
- Flat data: `defense_pilot_v2_summary.csv`
- Plot: `defense_pilot_v2_survival.png`
"""
REPORT_OUT.write_text(report, encoding="utf-8")

print(f"validated={len(rows)} total_episodes={sum(r['episodes'] for r in rows)}")
print(f"csv={CSV_OUT}")
print(f"plot={PLOT_OUT}")
print(f"report={REPORT_OUT}")
