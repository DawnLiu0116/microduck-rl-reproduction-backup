"""Validate the seed-123 ONNX and compare it with PyTorch on simulated observations."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import torch
from rsl_rl.runners import OnPolicyRunner

import mjlab.tasks  # noqa: F401
import mjlab_microduck.tasks  # noqa: F401
from mjlab.envs import ManagerBasedRlEnv
from mjlab.rl import RslRlVecEnvWrapper
from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls


TASK_ID = "Mjlab-Velocity-Flat-MicroDuck"
REPO_ROOT = Path(os.environ.get("MICRODUCK_REPO_ROOT", Path.cwd()))
CHECKPOINT = REPO_ROOT / "logs/rsl_rl/velocity/2026-09-22_19-08-01_walk_baseline_4096_seed123_4000_v1/model_3999.pt"
ROOT = Path(os.environ.get("MICRODUCK_ARTIFACT_ROOT", Path(__file__).resolve().parent))
ONNX_PATH = ROOT / "microduck_velocity_flat_seed123_iter3999.onnx"
OUTPUT_PATH = ROOT / "onnx_equivalence_seed123.json"


def main() -> None:
    model = onnx.load(ONNX_PATH)
    onnx.checker.check_model(model)

    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(
        str(ONNX_PATH), sess_options=options, providers=["CPUExecutionProvider"]
    )
    input_meta = session.get_inputs()[0]
    output_meta = session.get_outputs()[0]
    if input_meta.shape != [1, 61] or output_meta.shape != [1, 14]:
        raise RuntimeError(f"Unexpected ONNX interface: {input_meta.shape} -> {output_meta.shape}")

    smoke = session.run(
        [output_meta.name],
        {input_meta.name: np.zeros((1, 61), dtype=np.float32)},
    )[0]
    if not np.isfinite(smoke).all():
        raise RuntimeError("Non-finite ONNX CPU smoke-test output")

    env_cfg = load_env_cfg(TASK_ID, play=True)
    agent_cfg = load_rl_cfg(TASK_ID)
    env_cfg.scene.num_envs = 1
    env_cfg.seed = 1001
    env_cfg.events["push_robot"].interval_range_s = (1000.0, 1001.0)
    base_env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0")
    env = RslRlVecEnvWrapper(base_env, clip_actions=agent_cfg.clip_actions)

    runner_cls = load_runner_cls(TASK_ID) or OnPolicyRunner
    runner = runner_cls(env, asdict(agent_cfg), device="cuda:0")
    runner.load(
        str(CHECKPOINT),
        load_cfg={"actor": True},
        strict=True,
        map_location="cuda:0",
    )
    policy = runner.get_inference_policy(device="cuda:0")

    obs = env.get_observations()
    absolute_errors = []
    relative_errors = []
    all_outputs_finite = True
    with torch.inference_mode():
        for _ in range(200):
            torch_actions = policy(obs)
            obs_np = obs["actor"].detach().cpu().numpy().astype(np.float32)
            onnx_actions = session.run([output_meta.name], {input_meta.name: obs_np})[0]
            torch_np = torch_actions.detach().cpu().numpy()
            all_outputs_finite &= bool(np.isfinite(torch_np).all() and np.isfinite(onnx_actions).all())
            diff = np.abs(torch_np - onnx_actions)
            absolute_errors.append(diff)
            relative_errors.append(diff / np.maximum(np.abs(torch_np), 1e-6))
            obs, _, _, _ = env.step(torch_actions)

    absolute = np.concatenate(absolute_errors)
    relative = np.concatenate(relative_errors)
    result = {
        "checkpoint": str(CHECKPOINT),
        "onnx": str(ONNX_PATH),
        "onnx_checker_passed": True,
        "cpu_onnxruntime_passed": True,
        "input_name": input_meta.name,
        "input_shape": input_meta.shape,
        "output_name": output_meta.name,
        "output_shape": output_meta.shape,
        "observations_tested": 200,
        "action_values_compared": int(absolute.size),
        "max_absolute_error": float(absolute.max()),
        "mean_absolute_error": float(absolute.mean()),
        "max_relative_error": float(relative.max()),
        "all_outputs_finite": all_outputs_finite,
    }
    OUTPUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    env.close()


if __name__ == "__main__":
    main()
