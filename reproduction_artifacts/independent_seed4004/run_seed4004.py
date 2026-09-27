"""Fresh single-seed replication check for all three policies and six scenarios."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from mjlab.utils.torch import configure_torch_backends


BASE = Path(
    "/mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/outputs/"
    "microduck_reproduction"
)
UNIFIED_DIR = BASE / "unified_evaluation"
OFFICIAL_DIR = BASE / "official_comparison"
OUT_DIR = BASE / "independent_seed4004"
OUT_PATH = OUT_DIR / "seed4004_results.json"
PROGRESS_PATH = OUT_DIR / "progress.json"

sys.path.insert(0, str(UNIFIED_DIR))
sys.path.insert(0, str(OFFICIAL_DIR))

from run_unified_evaluation import ALL_SCENARIOS, evaluate_scenario  # noqa: E402
import run_official_onnx_evaluation as official_eval  # noqa: E402


EVAL_SEED = 4004
EPISODES = 128
CHECKPOINTS = {
    "seed42_iter3999": Path(
        "/home/deuler/microduck_rl/logs/rsl_rl/velocity/"
        "2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2/model_3999.pt"
    ),
    "seed123_iter3999": Path(
        "/home/deuler/microduck_rl/logs/rsl_rl/velocity/"
        "2026-09-22_19-08-01_walk_baseline_4096_seed123_4000_v1/model_3999.pt"
    ),
}


def save(rows: list[dict], complete: bool = False) -> None:
    payload = {
        "purpose": "fresh-process independent check outside the frozen 3-seed aggregate",
        "evaluation_seed": EVAL_SEED,
        "episodes_per_model_scenario": EPISODES,
        "complete": complete,
        "results": rows,
    }
    temp = PROGRESS_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp.replace(PROGRESS_PATH)
    if complete:
        OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    configure_torch_backends()
    official_eval.EPISODES = EPISODES
    official_policy = official_eval.OfficialOnnxTorchPolicy(official_eval.ONNX_PATH, "cuda:0")
    equivalence = official_eval.validate_mapping(official_policy)
    print(f"OFFICIAL_EQUIVALENCE {json.dumps(equivalence)}", flush=True)

    rows = []
    if PROGRESS_PATH.is_file():
        rows = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))["results"]
    completed = {(r["model_label"], r["scenario"], int(r["seed"])) for r in rows}
    total = len(ALL_SCENARIOS) * 3

    for scenario in ALL_SCENARIOS:
        for label, checkpoint in CHECKPOINTS.items():
            key = (label, scenario, EVAL_SEED)
            if key in completed:
                continue
            print(f"START {label}/{scenario}/{EVAL_SEED} ({len(rows)+1}/{total})", flush=True)
            row = evaluate_scenario(
                checkpoint=checkpoint,
                model_label=label,
                scenario=scenario,
                episodes=EPISODES,
                seed=EVAL_SEED,
            )
            rows.append(row)
            completed.add(key)
            save(rows)
            print(f"DONE {label}/{scenario}: {row['success_count']}/{EPISODES}", flush=True)

        label = official_eval.MODEL_LABEL
        key = (label, scenario, EVAL_SEED)
        if key not in completed:
            print(f"START {label}/{scenario}/{EVAL_SEED} ({len(rows)+1}/{total})", flush=True)
            row = official_eval.evaluate(official_policy, scenario, EVAL_SEED)
            rows.append(row)
            completed.add(key)
            save(rows)
            print(f"DONE {label}/{scenario}: {row['success_count']}/{EPISODES}", flush=True)

    if len(rows) != total:
        raise RuntimeError(f"Expected {total} results, found {len(rows)}")
    save(rows, complete=True)
    print(f"RESULT={OUT_PATH}", flush=True)


if __name__ == "__main__":
    main()
