"""Compare final ONNX actions with the loaded PyTorch actor on real observations."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

import numpy as np
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
RUN_DIR = REPO_ROOT / "logs/rsl_rl/velocity/2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2"
ROOT = Path(os.environ.get("MICRODUCK_ARTIFACT_ROOT", Path(__file__).resolve().parent))


def main() -> None:
    env_cfg = load_env_cfg(TASK_ID, play=True)
    agent_cfg = load_rl_cfg(TASK_ID)
    env_cfg.scene.num_envs = 1
    env_cfg.seed = 123
    env_cfg.events["push_robot"].interval_range_s = (1000.0, 1001.0)
    base_env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0")
    env = RslRlVecEnvWrapper(base_env, clip_actions=agent_cfg.clip_actions)

    runner_cls = load_runner_cls(TASK_ID) or OnPolicyRunner
    runner = runner_cls(env, asdict(agent_cfg), device="cuda:0")
    runner.load(
        str(RUN_DIR / "model_3999.pt"),
        load_cfg={"actor": True},
        strict=True,
        map_location="cuda:0",
    )
    policy = runner.get_inference_policy(device="cuda:0")

    session = ort.InferenceSession(
        str(ROOT / "microduck_velocity_flat_seed42_iter3999.onnx"),
        providers=["CPUExecutionProvider"],
    )
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    obs = env.get_observations()
    absolute_errors = []
    relative_errors = []
    with torch.inference_mode():
        for _ in range(200):
            torch_actions = policy(obs)
            obs_np = obs["actor"].detach().cpu().numpy().astype(np.float32)
            onnx_actions = session.run([output_name], {input_name: obs_np})[0]
            torch_np = torch_actions.detach().cpu().numpy()
            diff = np.abs(torch_np - onnx_actions)
            absolute_errors.append(diff)
            relative_errors.append(diff / np.maximum(np.abs(torch_np), 1e-6))
            obs, _, _, _ = env.step(torch_actions)

    absolute = np.concatenate(absolute_errors)
    relative = np.concatenate(relative_errors)
    result = {
        "observations_tested": 200,
        "action_values_compared": int(absolute.size),
        "max_absolute_error": float(absolute.max()),
        "mean_absolute_error": float(absolute.mean()),
        "max_relative_error": float(relative.max()),
        "all_finite": bool(np.isfinite(absolute).all()),
    }
    (ROOT / "onnx_equivalence.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    env.close()


if __name__ == "__main__":
    main()
