"""Compare how strongly the three final actors respond to command inputs."""

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
}
OFFICIAL = ROOT / "official_comparison" / "alpha_walking_official.onnx"
COMMAND_INDICES = {"vx": 48, "vy": 49, "yaw": 50}


def forward_torch(state: dict[str, torch.Tensor], x: torch.Tensor) -> torch.Tensor:
    x = (x - state["obs_normalizer._mean"]) / state["obs_normalizer._std"]
    for index in (0, 2, 4):
        x = F.elu(F.linear(x, state[f"mlp.{index}.weight"], state[f"mlp.{index}.bias"]))
    return F.linear(x, state["mlp.6.weight"], state["mlp.6.bias"])


def inspect_torch(path: Path) -> dict:
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    state = checkpoint["actor_state_dict"]
    mean = state["obs_normalizer._mean"].reshape(-1).clone()
    std = state["obs_normalizer._std"].reshape(-1).clone()
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
        "command_std": {name: float(std[index]) for name, index in COMMAND_INDICES.items()},
        "effective_first_layer_column_l2": {
            name: float(torch.linalg.vector_norm(first[:, index] / std[index]))
            for name, index in COMMAND_INDICES.items()
        },
        "yaw_sweep": outputs,
    }


def inspect_onnx(path: Path) -> dict:
    model = onnx.load(path)
    arrays = {item.name: numpy_helper.to_array(item).copy() for item in model.graph.initializer}
    state = {
        "obs_normalizer._mean": torch.from_numpy(arrays["obs_normalizer._mean"]),
        "obs_normalizer._std": torch.from_numpy(arrays["onnx::Div_24"]),
    }
    for index in (0, 2, 4, 6):
        state[f"mlp.{index}.weight"] = torch.from_numpy(arrays[f"mlp.{index}.weight"])
        state[f"mlp.{index}.bias"] = torch.from_numpy(arrays[f"mlp.{index}.bias"])
    return inspect_state(state)


def inspect_state(state: dict[str, torch.Tensor]) -> dict:
    mean = state["obs_normalizer._mean"].reshape(-1).clone()
    std = state["obs_normalizer._std"].reshape(-1).clone()
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
        "command_std": {name: float(std[index]) for name, index in COMMAND_INDICES.items()},
        "effective_first_layer_column_l2": {
            name: float(torch.linalg.vector_norm(first[:, index] / std[index]))
            for name, index in COMMAND_INDICES.items()
        },
        "yaw_sweep": outputs,
    }


def main() -> None:
    result = {label: inspect_torch(path) for label, path in CHECKPOINTS.items()}
    result["official"] = inspect_onnx(OFFICIAL)
    output = ROOT / "video_diagnostics" / "command_sensitivity.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
