"""Evaluate the final policy with stress, train-like, and effectively no pushes."""

import json

from evaluate_checkpoints import ROOT, evaluate


def main() -> None:
    milestone = json.loads((ROOT / "checkpoint_evaluation.json").read_text(encoding="utf-8"))
    stress = next(item for item in milestone["results"] if item["iteration"] == 3999)
    conditions = {
        "train_like_push_3_to_6_s": (3.0, 6.0),
        "no_push_within_episode": (1000.0, 1001.0),
    }
    results = {"stress_push_0.5_to_1.0_s": stress}
    for name, interval in conditions.items():
        result = evaluate(3999, push_interval=interval)
        results[name] = result
        print(json.dumps({"condition": name, **result}, sort_keys=True), flush=True)
    (ROOT / "final_condition_evaluation.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
