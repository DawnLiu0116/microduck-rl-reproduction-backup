"""Fetch provenance and the exact checkpoint behind official alpha_walking.onnx."""

from __future__ import annotations

import json
from pathlib import Path

import wandb


RUN_PATH = "pollen-robotics/mjlab_microduck/441tzs6d"
CHECKPOINT_NAME = "model_3750.pt"
ROOT = Path(
    "/mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/outputs/"
    "microduck_reproduction/official_comparison"
)


def json_safe(value):
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    run = wandb.Api().run(RUN_PATH)
    files = sorted(file.name for file in run.files())
    if CHECKPOINT_NAME not in files:
        raise FileNotFoundError(f"{CHECKPOINT_NAME} not in official run")

    checkpoint = ROOT / CHECKPOINT_NAME
    if not checkpoint.is_file():
        run.file(CHECKPOINT_NAME).download(root=str(ROOT), replace=False)

    summary = dict(run.summary)
    metric_keys = [
        key for key in summary
        if any(token in key.lower() for token in ("reward", "episode", "iteration", "timesteps", "nan"))
    ]
    selected_config_keys = [
        "seed", "max_iterations", "num_steps_per_env", "save_interval",
        "experiment_name", "run_name", "device", "num_envs",
    ]
    payload = {
        "source": "official Pollen Robotics W&B run referenced by repository source",
        "run_path": RUN_PATH,
        "run_id": run.id,
        "run_name": run.name,
        "state": run.state,
        "created_at": str(run.created_at),
        "checkpoint_name": CHECKPOINT_NAME,
        "checkpoint_path": str(checkpoint),
        "checkpoint_bytes": checkpoint.stat().st_size,
        "config_selected": {
            key: json_safe(run.config[key])
            for key in selected_config_keys if key in run.config
        },
        "summary_training_metrics": {
            key: json_safe(summary[key]) for key in sorted(metric_keys)
        },
        "available_checkpoint_files": [
            name for name in files if name.startswith("model_") and name.endswith(".pt")
        ],
    }
    output = ROOT / "official_wandb_metadata.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
