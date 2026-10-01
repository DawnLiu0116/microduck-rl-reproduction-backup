"""Confirm the most important findings from the MicroDuck fault screening.

The experiment uses three independent evaluation seeds and 128 parallel episodes
per model/fault/seed job. It reuses the exact policy loading, scenario setup,
metric definitions, and observation-field assertions from run_sensor_fault_scan.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mjlab.utils.torch import configure_torch_backends

from run_sensor_fault_scan import MODELS, SCENARIO, TASK_ID, evaluate


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "confirmatory_faults.json"
DEFAULT_SEEDS = [1001, 2002, 3003]
DEFAULT_EPISODES = 128

# Policy frequency is 50 Hz, so one policy step is 20 ms.
FAULTS = [
    {"name": "clean", "type": "clean", "severity": "none"},
    {"name": "delay_2", "type": "delay", "severity": "threshold", "steps": 2},
    {"name": "freeze_8", "type": "freeze", "severity": "threshold", "duration": 8, "period": 180},
    {"name": "freeze_10", "type": "freeze", "severity": "threshold", "duration": 10, "period": 180},
    {"name": "freeze_12", "type": "freeze", "severity": "threshold", "duration": 12, "period": 180},
    {"name": "spike_100", "type": "spike", "severity": "severe", "scale": 1.0, "duration": 5, "period": 200},
]


def save(path: Path, rows: list[dict], complete: bool, episodes: int, seeds: list[int], faults: list[dict]) -> None:
    payload = {
        "protocol_version": "0.2-confirmatory",
        "task": TASK_ID,
        "scenario": SCENARIO,
        "policy_frequency_hz": 50,
        "episodes_per_job": episodes,
        "evaluation_seeds": seeds,
        "complete": complete,
        "faults": faults,
        "models": list(MODELS),
        "actor_sensor_fields_modified": [0, 34],
        "action_history_and_commands_unchanged": True,
        "results": rows,
    }
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=DEFAULT_EPISODES)
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS)
    parser.add_argument("--models", nargs="+", choices=list(MODELS), default=list(MODELS))
    parser.add_argument("--faults", nargs="+", choices=[item["name"] for item in FAULTS])
    parser.add_argument("--output", type=Path, default=RESULT)
    args = parser.parse_args()

    selected_faults = FAULTS if not args.faults else [item for item in FAULTS if item["name"] in args.faults]
    progress = args.output.with_name(args.output.stem + "_progress.json")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    configure_torch_backends()

    rows: list[dict] = []
    if progress.is_file():
        previous = json.loads(progress.read_text(encoding="utf-8"))
        if int(previous["episodes_per_job"]) != args.episodes:
            raise RuntimeError("Existing progress uses a different episode count")
        rows = previous["results"]

    completed = {
        (row["model_label"], row["fault_name"], int(row["seed"])) for row in rows
    }
    total = len(args.models) * len(selected_faults) * len(args.seeds)
    for seed in args.seeds:
        for model_label in args.models:
            for fault in selected_faults:
                key = (model_label, fault["name"], seed)
                if key in completed:
                    continue
                print(
                    f"START seed={seed} {model_label}/{fault['name']} "
                    f"({len(rows) + 1}/{total})",
                    flush=True,
                )
                row = evaluate(model_label, fault, args.episodes, seed)
                rows.append(row)
                completed.add(key)
                save(progress, rows, False, args.episodes, args.seeds, selected_faults)
                print(
                    f"DONE seed={seed} {model_label}/{fault['name']} "
                    f"success={row['success_count']}/{args.episodes} "
                    f"fall={row['fell_over_count']} "
                    f"xy={row['mean_xy_velocity_error_mps']:.4f}",
                    flush=True,
                )

    if len(rows) != total:
        raise RuntimeError(f"Expected {total} results, found {len(rows)}")
    save(args.output, rows, True, args.episodes, args.seeds, selected_faults)
    print(f"RESULT={args.output}")


if __name__ == "__main__":
    main()
