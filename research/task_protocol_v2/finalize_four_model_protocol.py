"""Merge the preserved three-model run with seed 2026 and build final statistics."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "four_model_final"
OLD_JSON = ROOT / "measurement_v2_results.json"
NEW_JSON = ROOT / "seed2026_extension" / "measurement_v2_seed2026_results.json"
MODELS = ("official", "seed42", "seed123", "seed2026")
SCENARIOS = ("Forward", "Turning", "Standing", "Stress-forward")
PRIMARY_METRIC = {
    "Forward": ("mean_abs_vx_error_mps", "Mean absolute vx error (m/s)"),
    "Turning": ("mean_abs_yaw_error_radps", "Mean absolute yaw error (rad/s)"),
    "Standing": ("mean_planar_speed_mps", "Mean planar speed (m/s)"),
    "Stress-forward": ("recovered_push_fraction", "Recovered push fraction"),
}


def wilson(successes: int, total: int) -> tuple[float, float]:
    z = 1.959963984540054
    p = successes / total
    den = 1 + z * z / total
    center = (p + z * z / (2 * total)) / den
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / den
    return center - margin, center + margin


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def bootstrap_mean(values: np.ndarray, rng: np.random.Generator, draws: int = 10000) -> tuple[float, float]:
    means = np.empty(draws, dtype=np.float64)
    for start in range(0, draws, 500):
        size = min(500, draws - start)
        sample = rng.choice(values, size=(size, values.size), replace=True)
        means[start:start + size] = sample.mean(axis=1)
    return tuple(float(x) for x in np.quantile(means, [0.025, 0.975]))


def main() -> None:
    old = json.loads(OLD_JSON.read_text(encoding="utf-8"))
    new = json.loads(NEW_JSON.read_text(encoding="utf-8"))
    if not old.get("complete") or old.get("job_count") != 36:
        raise RuntimeError("Preserved three-model result is incomplete")
    if not new.get("complete") or new.get("job_count") != 12:
        raise RuntimeError("Seed-2026 extension is incomplete")
    jobs = old["jobs"] + new["jobs"]
    keys = [(row["model"], row["scenario"], int(row["seed"])) for row in jobs]
    if len(keys) != 48 or len(set(keys)) != 48:
        raise RuntimeError("Expected 48 unique model/scenario/seed jobs")

    OUT.mkdir(parents=True, exist_ok=True)
    all_rows: dict[tuple[str, str], list[dict]] = defaultdict(list)
    nan_count = 0
    bounds_count = 0
    for job in jobs:
        rows = read_rows(Path(job["raw_episode_file"]))
        if len(rows) != 128:
            raise RuntimeError(f"Expected 128 rows in {job['raw_episode_file']}")
        all_rows[(job["model"], job["scenario"])].extend(rows)
        nan_count += sum(row["nan_state"].lower() == "true" for row in rows)
        bounds_count += sum(row["out_of_terrain_bounds"].lower() == "true" for row in rows)

    rng = np.random.default_rng(20260929)
    summary = []
    for model in MODELS:
        for scenario in SCENARIOS:
            rows = all_rows[(model, scenario)]
            if len(rows) != 384:
                raise RuntimeError(f"{model}/{scenario}: expected 384 episodes, got {len(rows)}")
            survival_count = sum(row["survival"].lower() == "true" for row in rows)
            low, high = wilson(survival_count, len(rows))
            metric, _ = PRIMARY_METRIC[scenario]
            values = np.asarray([float(row[metric]) for row in rows], dtype=np.float64)
            ci_low, ci_high = bootstrap_mean(values, rng)
            summary.append({
                "model": model,
                "scenario": scenario,
                "episodes": len(rows),
                "survival_count": survival_count,
                "survival_rate": survival_count / len(rows),
                "survival_wilson95_low": low,
                "survival_wilson95_high": high,
                "primary_metric": metric,
                "primary_mean": float(values.mean()),
                "primary_bootstrap95_low": ci_low,
                "primary_bootstrap95_high": ci_high,
            })

    with (OUT / "four_model_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    payload = {
        "complete": True,
        "protocol": old["protocol"],
        "models": list(MODELS),
        "job_count": len(jobs),
        "total_episodes": sum(len(rows) for rows in all_rows.values()),
        "unique_job_count": len(set(keys)),
        "nan_episode_count": nan_count,
        "out_of_bounds_episode_count": bounds_count,
        "continuous_metric_ci": "episode-level nonparametric bootstrap, 10000 draws, RNG seed 20260929",
        "survival_ci": "95% Wilson interval",
        "jobs": jobs,
        "summary": summary,
    }
    (OUT / "four_model_results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    colors = {"official": "#555555", "seed42": "#2878B5", "seed123": "#D95319", "seed2026": "#2A9D8F"}
    x = np.arange(len(SCENARIOS))
    width = 0.19
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for index, model in enumerate(MODELS):
        selected = [next(row for row in summary if row["model"] == model and row["scenario"] == scenario) for scenario in SCENARIOS]
        values = np.asarray([row["survival_rate"] for row in selected])
        lower = np.maximum(0.0, values - np.asarray([row["survival_wilson95_low"] for row in selected]))
        upper = np.maximum(0.0, np.asarray([row["survival_wilson95_high"] for row in selected]) - values)
        ax.bar(x + (index - 1.5) * width, values * 100, width, label=model, color=colors[model])
        ax.errorbar(x + (index - 1.5) * width, values * 100, yerr=np.vstack([lower, upper]) * 100, fmt="none", ecolor="black", capsize=2, lw=0.8)
    ax.set_xticks(x, SCENARIOS)
    ax.set_ylabel("Survival rate (%)")
    ax.set_ylim(0, 105)
    ax.set_title("MicroDuck unified protocol: survival over 3 eval seeds (n=384 each)")
    ax.legend(ncol=4, loc="lower left")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / "survival_comparison.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, scenario in zip(axes.flat, SCENARIOS):
        selected = [next(row for row in summary if row["model"] == model and row["scenario"] == scenario) for model in MODELS]
        values = np.asarray([row["primary_mean"] for row in selected])
        lower = np.maximum(0.0, values - np.asarray([row["primary_bootstrap95_low"] for row in selected]))
        upper = np.maximum(0.0, np.asarray([row["primary_bootstrap95_high"] for row in selected]) - values)
        ax.bar(MODELS, values, color=[colors[m] for m in MODELS])
        ax.errorbar(np.arange(len(MODELS)), values, yerr=np.vstack([lower, upper]), fmt="none", ecolor="black", capsize=3)
        ax.set_title(scenario)
        ax.set_ylabel(PRIMARY_METRIC[scenario][1])
        ax.tick_params(axis="x", rotation=20)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Primary continuous metrics (mean and episode-bootstrap 95% CI)")
    fig.tight_layout()
    fig.savefig(OUT / "primary_metrics_comparison.png", dpi=180)
    plt.close(fig)

    print(json.dumps({
        "complete": True,
        "jobs": 48,
        "episodes": payload["total_episodes"],
        "nan": nan_count,
        "out_of_bounds": bounds_count,
        "output": str(OUT),
    }, indent=2))


if __name__ == "__main__":
    main()
