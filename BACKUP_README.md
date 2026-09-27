# MicroDuck RL reproduction backup

Private research backup created on 2026-09-27.

## Contents

- Upstream source history from `pollen-robotics/microduck_rl` at commit
  `cb70b792312d559a4da09064d92009079671815f`.
- All locally created evaluation, export, plotting, video, audit, and reporting
  scripts under `reproduction_artifacts/`.
- Final ONNX policies for seed 42 and seed 123, plus the public official
  `alpha_walking.onnx` used for comparison.
- Raw and aggregated evaluation JSON/CSV files, figures, nine matched comparison
  videos, and the anonymous human-review package.
- Seed 42 and seed 123 checkpoints at iterations 0, 500, 1000, 2000, 3000, and
  3999 under `training_runs/`.
- TensorBoard event files for both 4000-iteration training runs.

## Intentionally excluded

- Python virtual environments, package caches, Warp caches, and generated build
  caches.
- Intermediate checkpoints saved every 50 iterations other than the listed
  milestones. These are redundant for reproduction and would make the backup
  several hundred megabytes larger.

## Primary entry points

- `reproduction_artifacts/RUN_SUMMARY.md`
- `reproduction_artifacts/TECHNICAL_REVIEW.md`
- `reproduction_artifacts/OFFICIAL_COMPARISON_REPORT.md` (inside
  `official_comparison/`)
- `reproduction_artifacts/ADDITIONAL_VALIDATION_REPORT.md`
- `reproduction_artifacts/FINAL_INTEGRITY_AUDIT.json`
- `reproduction_artifacts/SHA256SUMS_FINAL.txt`

The physical robot was not controlled or tested. All reported experiments are
simulation results unless explicitly stated otherwise.
