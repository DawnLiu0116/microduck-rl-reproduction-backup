"""Compare the fresh seed 4004 check with the prior three-seed aggregate."""

from __future__ import annotations

import csv
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
RESULT = HERE / "seed4004_results.json"
OUT_CSV = HERE / "seed4004_consistency.csv"
OUT_MD = HERE / "SEED4004_VALIDATION.md"
SCENARIOS = ["Nominal", "Train-like", "Stress", "Forward", "Turning", "Standing"]
MODELS = ["official_alpha_walking", "seed42_iter3999", "seed123_iter3999"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    fresh = json.loads(RESULT.read_text(encoding="utf-8"))["results"]
    prior = read_csv(BASE / "official_comparison" / "official_multi_seed_aggregate.csv")
    prior += read_csv(BASE / "unified_evaluation" / "multi_seed" / "multi_seed_aggregate.csv")
    fresh_map = {(r["model_label"], r["scenario"]): r for r in fresh}
    prior_map = {(r["model_label"], r["scenario"]): r for r in prior}
    rows = []
    for scenario in SCENARIOS:
        for model in MODELS:
            f = fresh_map[(model, scenario)]
            p = prior_map[(model, scenario)]
            fresh_rate = 100 * float(f["success_rate"])
            prior_rate = 100 * float(p["success_rate"])
            rows.append({
                "model_label": model,
                "scenario": scenario,
                "seed4004_success_count": f["success_count"],
                "seed4004_episodes": f["episodes"],
                "seed4004_success_percent": fresh_rate,
                "prior_3_seed_success_percent": prior_rate,
                "difference_percentage_points": fresh_rate - prior_rate,
                "seed4004_xy_error_mps": f["mean_xy_velocity_error_mps"],
                "seed4004_yaw_error_radps": f["mean_yaw_velocity_error_radps"],
                "nan_state_rate": f["nan_state_rate"],
            })
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Independent seed 4004 validation",
        "",
        "This is a fresh-process check and is not merged into the frozen three-seed primary table.",
        "Each entry contains 128 episodes under the same scenario definition.",
        "",
        "| Scenario | Model | Seed 4004 | Prior 3-seed aggregate | Delta (pp) |",
        "|---|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['model_label']} | "
            f"{float(row['seed4004_success_percent']):.2f}% | "
            f"{float(row['prior_3_seed_success_percent']):.2f}% | "
            f"{float(row['difference_percentage_points']):+.2f} |"
        )
    lines += [
        "",
        "Interpretation rule: this extra seed checks whether the broad ordering is reproducible; "
        "it does not replace confidence intervals or make a four-seed table retroactively primary.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT_CSV)
    print(OUT_MD)


if __name__ == "__main__":
    main()
