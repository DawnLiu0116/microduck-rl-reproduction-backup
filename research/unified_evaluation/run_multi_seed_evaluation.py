"""Run and aggregate the frozen protocol over three independent evaluation seeds.

Progress is saved after every model/scenario/seed result, so rerunning resumes
without repeating completed evaluations.
"""

from __future__ import annotations

import csv
import json
import os
import statistics
from collections import defaultdict
from pathlib import Path

from run_unified_evaluation import ALL_SCENARIOS, evaluate_scenario, wilson_interval


EVAL_SEEDS = (1001, 2002, 3003)
EPISODES = 128
REPO_ROOT = Path(os.environ.get("MICRODUCK_REPO_ROOT", Path.cwd()))
MODELS = {
    "seed42_iter3999": Path(
        REPO_ROOT / "logs/rsl_rl/velocity/"
        "2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2/model_3999.pt"
    ),
    "seed123_iter3999": Path(
        REPO_ROOT / "logs/rsl_rl/velocity/"
        "2026-09-22_19-08-01_walk_baseline_4096_seed123_4000_v1/model_3999.pt"
    ),
}
ROOT = Path(__file__).resolve().parent / "multi_seed"
PROGRESS_PATH = ROOT / "progress.json"


def key(row: dict) -> tuple[str, str, int]:
    return (row["model_label"], row["scenario"], int(row["seed"]))


def save_progress(rows: list[dict]) -> None:
    payload = {
        "protocol_version": "1.1",
        "evaluation_seeds": list(EVAL_SEEDS),
        "episodes_per_model_scenario_seed": EPISODES,
        "results": rows,
    }
    temporary = PROGRESS_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary.replace(PROGRESS_PATH)


def aggregate(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row["model_label"], row["scenario"])].append(row)

    metrics = (
        "mean_episode_seconds",
        "mean_return",
        "mean_xy_velocity_error_mps",
        "mean_yaw_velocity_error_radps",
        "mean_action_delta_l2",
        "nan_state_rate",
        "out_of_terrain_rate",
    )
    output = []
    for model_label in MODELS:
        for scenario in ALL_SCENARIOS:
            values = sorted(grouped[(model_label, scenario)], key=lambda row: row["seed"])
            if len(values) != len(EVAL_SEEDS):
                raise RuntimeError(f"Incomplete group {model_label}/{scenario}: {len(values)}")
            total = sum(int(row["episodes"]) for row in values)
            successes = sum(int(row["success_count"]) for row in values)
            falls = sum(int(row["fell_over_count"]) for row in values)
            success_ci = wilson_interval(successes, total)
            fall_ci = wilson_interval(falls, total)
            seed_rates = [float(row["success_rate"]) for row in values]
            result = {
                "model_label": model_label,
                "scenario": scenario,
                "evaluation_seeds": list(EVAL_SEEDS),
                "total_episodes": total,
                "success_count": successes,
                "success_rate": successes / total,
                "success_wilson95_low": success_ci[0],
                "success_wilson95_high": success_ci[1],
                "success_rate_between_seed_std": statistics.stdev(seed_rates),
                "fell_over_count": falls,
                "fell_over_rate": falls / total,
                "fell_over_wilson95_low": fall_ci[0],
                "fell_over_wilson95_high": fall_ci[1],
            }
            for metric in metrics:
                result[metric] = statistics.mean(float(row[metric]) for row in values)
            output.append(result)
    return output


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    if PROGRESS_PATH.is_file():
        rows = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))["results"]
    else:
        rows = []
    completed = {key(row) for row in rows}
    total_jobs = len(EVAL_SEEDS) * len(ALL_SCENARIOS) * len(MODELS)

    for eval_seed in EVAL_SEEDS:
        for scenario in ALL_SCENARIOS:
            for model_label, checkpoint in MODELS.items():
                job = (model_label, scenario, eval_seed)
                if job in completed:
                    print(f"SKIP {job}", flush=True)
                    continue
                print(f"START {job} ({len(rows) + 1}/{total_jobs})", flush=True)
                result = evaluate_scenario(
                    checkpoint=checkpoint,
                    model_label=model_label,
                    scenario=scenario,
                    episodes=EPISODES,
                    seed=eval_seed,
                )
                rows.append(result)
                completed.add(job)
                save_progress(rows)
                print(
                    f"DONE {job}: {result['success_count']}/{EPISODES} "
                    f"return={result['mean_return']:.3f}",
                    flush=True,
                )

    aggregates = aggregate(rows)
    payload = {
        "protocol_version": "1.1",
        "evaluation_seeds": list(EVAL_SEEDS),
        "episodes_per_model_scenario_seed": EPISODES,
        "total_episodes_per_model_scenario": EPISODES * len(EVAL_SEEDS),
        "raw_results": rows,
        "aggregate_results": aggregates,
    }
    json_path = ROOT / "multi_seed_evaluation.json"
    csv_path = ROOT / "multi_seed_aggregate.csv"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    csv_rows = []
    for row in aggregates:
        flat = dict(row)
        flat["evaluation_seeds"] = ",".join(map(str, flat["evaluation_seeds"]))
        csv_rows.append(flat)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"JSON={json_path}")
    print(f"CSV={csv_path}")


if __name__ == "__main__":
    main()
