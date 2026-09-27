"""Add compute-time accounting and preserve the TensorBoard event file."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator


RUN = Path(
    "/home/deuler/microduck_rl/logs/rsl_rl/velocity/"
    "2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2"
)
ROOT = Path(
    "/mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/"
    "outputs/microduck_reproduction"
)


def main() -> None:
    event_files = sorted(RUN.glob("events.out.tfevents.*"))
    if len(event_files) != 1:
        raise RuntimeError(f"Expected one event file, found {len(event_files)}")
    event_file = event_files[0]
    accumulator = EventAccumulator(str(event_file), size_guidance={"scalars": 0})
    accumulator.Reload()

    collection = accumulator.Scalars("Perf/collection_time")
    learning = accumulator.Scalars("Perf/learning_time")
    if len(collection) != 4000 or len(learning) != 4000:
        raise RuntimeError(
            f"Unexpected perf series lengths: {len(collection)}, {len(learning)}"
        )
    active_seconds = sum(x.value for x in collection) + sum(x.value for x in learning)

    summary_path = ROOT / "metrics_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["active_collection_plus_learning_seconds"] = active_seconds
    summary["active_collection_plus_learning_hours"] = active_seconds / 3600.0
    summary["wall_clock_note"] = (
        "TensorBoard wall time includes host suspension; active time is the sum of "
        "logged collection_time and learning_time."
    )
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    tensorboard_dir = ROOT / "tensorboard"
    tensorboard_dir.mkdir(parents=True, exist_ok=True)
    copied = tensorboard_dir / event_file.name
    shutil.copy2(event_file, copied)
    print(f"ACTIVE_SECONDS={active_seconds:.6f}")
    print(f"ACTIVE_HOURS={active_seconds / 3600.0:.6f}")
    print(f"EVENT_COPY={copied}")


if __name__ == "__main__":
    main()
