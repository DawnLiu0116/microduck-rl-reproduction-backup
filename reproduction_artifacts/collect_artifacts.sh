#!/usr/bin/env bash
set -euo pipefail

REPO=/home/deuler/microduck_rl
RUN=/home/deuler/microduck_rl/logs/rsl_rl/velocity/2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2
OUT=/mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction

mkdir -p "$OUT/checkpoints"
cp "$RUN/model_0.pt" "$OUT/checkpoints/"
cp "$RUN/model_500.pt" "$OUT/checkpoints/"
cp "$RUN/model_1000.pt" "$OUT/checkpoints/"
cp "$RUN/model_2000.pt" "$OUT/checkpoints/"
cp "$RUN/model_3000.pt" "$OUT/checkpoints/"
cp "$RUN/model_3999.pt" "$OUT/checkpoints/"
cp "$RUN/params/agent.yaml" "$OUT/agent.yaml"
cp "$RUN/params/env.yaml" "$OUT/env.yaml"

{
  echo "git_commit=$(git -C "$REPO" rev-parse HEAD)"
  echo "git_branch=$(git -C "$REPO" branch --show-current)"
  echo "uv=$($HOME/.local/bin/uv --version)"
  echo "python=$($HOME/.local/bin/uv run --directory "$REPO" python --version 2>&1)"
  "$HOME/.local/bin/uv" run --directory "$REPO" python - <<'PY'
import mujoco
import onnx
import onnxruntime
import torch
import warp

print(f"torch={torch.__version__}")
print(f"cuda={torch.version.cuda}")
print(f"mujoco={mujoco.__version__}")
print(f"warp={warp.__version__}")
print(f"onnx={onnx.__version__}")
print(f"onnxruntime={onnxruntime.__version__}")
PY
} > "$OUT/environment.txt"

sha256sum \
  "$OUT/checkpoints/model_3999.pt" \
  "$OUT/microduck_velocity_flat_seed42_iter3999.onnx" \
  > "$OUT/SHA256SUMS.txt"

ls -lh "$OUT/checkpoints" "$OUT/microduck_velocity_flat_seed42_iter3999.onnx"
