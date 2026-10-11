"""Compare command sensitivity; numeric diagnostic, not locomotion quality."""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import onnx
import torch
import torch.nn.functional as F
from onnx import numpy_helper


ROOT = Path(os.environ.get("MICRODUCK_ARTIFACT_ROOT", Path(__file__).resolve().parent.parent))
REPO_ROOT = Path(os.environ.get("MICRODUCK_REPO_ROOT", Path.cwd()))
CHECKPOINTS = {
    "seed42": REPO_ROOT / "logs/rsl_rl/velocity/2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2/model_3999.pt",
    "seed123": REPO_ROOT / "logs/rsl_rl/velocity/2026-09-22_19-08-01_walk_baseline_4096_seed123_4000_v1/model_3999.pt",
    "seed2026": REPO_ROOT / "logs/rsl_rl/velocity/2026-09-29_10-44-28_walk_baseline_4096_seed2026_4000_v1_resume3250_quiet/model_3999.pt",
}
OFFICIAL = ROOT / "official_comparison" / "alpha_walking_official.onnx"
COMMAND_INDICES = {"vx": 48, "vy": 49, "yaw": 50}
NORMALIZATION_EPS = 0.01  # Verified installed rsl_rl EmpiricalNormalization default.


def normalization_denominator(state: dict[str, torch.Tensor]) -> torch.Tensor:
    if "normalization_denominator" in state:
        return state["normalization_denominator"]  # ONNX already folds eps into Div input.
    return state["obs_normalizer._std"] + NORMALIZATION_EPS


def forward_torch(state: dict[str, torch.Tensor], x: torch.Tensor) -> torch.Tensor:
    x = (x - state["obs_normalizer._mean"]) / normalization_denominator(state)
    for index in (0, 2, 4):
        x = F.elu(F.linear(x, state[f"mlp.{index}.weight"], state[f"mlp.{index}.bias"]))
    return F.linear(x, state["mlp.6.weight"], state["mlp.6.bias"])


def inspect_torch(path: Path) -> dict:
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    return inspect_state(checkpoint["actor_state_dict"])


def load_onnx_state(path: Path) -> dict[str, torch.Tensor]:
    model = onnx.load(path)
    arrays = {item.name: numpy_helper.to_array(item).copy() for item in model.graph.initializer}
    divisors = [node.input[1] for node in model.graph.node if node.op_type == "Div" and node.input[1] in arrays and arrays[node.input[1]].size == 61]
    if len(divisors) != 1:
        raise RuntimeError("Expected one constant 61D normalization denominator")
    state = {
        "obs_normalizer._mean": torch.from_numpy(arrays["obs_normalizer._mean"]),
        "normalization_denominator": torch.from_numpy(arrays[divisors[0]]),
    }
    for index in (0, 2, 4, 6):
        state[f"mlp.{index}.weight"] = torch.from_numpy(arrays[f"mlp.{index}.weight"])
        state[f"mlp.{index}.bias"] = torch.from_numpy(arrays[f"mlp.{index}.bias"])
    return state


def inspect_onnx(path: Path) -> dict:
    return inspect_state(load_onnx_state(path))


def inspect_state(state: dict[str, torch.Tensor]) -> dict:
    mean = state["obs_normalizer._mean"].reshape(-1).clone()
    denom = normalization_denominator(state).reshape(-1).clone()
    first = state["mlp.0.weight"]
    base = mean.clone()
    base[48:61] = 0.0
    outputs = {}
    with torch.inference_mode():
        zero = forward_torch(state, base)
        for yaw in (-1.0, -0.6, 0.0, 0.6, 1.0):
            sample = base.clone()
            sample[50] = yaw
            action = forward_torch(state, sample)
            outputs[str(yaw)] = {
                "action_l2": float(torch.linalg.vector_norm(action)),
                "delta_from_yaw0_l2": float(torch.linalg.vector_norm(action - zero)),
                "max_abs_delta_from_yaw0": float((action - zero).abs().max()),
            }
    return {
        "command_mean": {name: float(mean[index]) for name, index in COMMAND_INDICES.items()},
        "command_denominator": {name: float(denom[index]) for name, index in COMMAND_INDICES.items()},
        "effective_first_layer_column_l2": {
            name: float(torch.linalg.vector_norm(first[:, index] / denom[index]))
            for name, index in COMMAND_INDICES.items()
        },
        "yaw_sweep": outputs,
    }


def main() -> None:
    result = {label: inspect_torch(path) for label, path in CHECKPOINTS.items()}
    result["official"] = inspect_onnx(OFFICIAL)
    output = ROOT / "video_diagnostics" / "command_sensitivity_corrected.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
