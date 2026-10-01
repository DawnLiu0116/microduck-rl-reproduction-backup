"""Closed-loop yaw-command sweep for the three final walking policies."""

from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import asdict
from pathlib import Path

import torch
from rsl_rl.runners import OnPolicyRunner

import mjlab.tasks  # noqa: F401
import mjlab_microduck.tasks  # noqa: F401
from mjlab.envs import ManagerBasedRlEnv
from mjlab.rl import RslRlVecEnvWrapper
from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
from mjlab.utils.torch import configure_torch_backends


ROOT = Path(os.environ.get("MICRODUCK_ARTIFACT_ROOT", Path(__file__).resolve().parent.parent))
sys.path[:0] = [str(ROOT), str(ROOT / "official_comparison")]
from record_final_comparison_videos import CHECKPOINTS, TASK_ID, configure_scenario  # noqa: E402
from run_official_onnx_evaluation import ONNX_PATH, OfficialOnnxTorchPolicy  # noqa: E402

YAW_COMMANDS = (0.2, 0.4, 0.6, 0.8, 1.0)
NUM_ENVS = 64
EVAL_SEED = 4004


def policy_for(label: str, env, agent_cfg):
    if label == "official":
        return OfficialOnnxTorchPolicy(ONNX_PATH, "cuda:0")
    runner_cls = load_runner_cls(TASK_ID) or OnPolicyRunner
    runner = runner_cls(env, asdict(agent_cfg), device="cuda:0")
    runner.load(str(CHECKPOINTS[label]), load_cfg={"actor": True}, strict=True, map_location="cuda:0")
    return runner.get_inference_policy(device="cuda:0")


def evaluate(label: str, yaw_command: float) -> dict:
    env_cfg = load_env_cfg(TASK_ID, play=True)
    agent_cfg = load_rl_cfg(TASK_ID)
    env_cfg.scene.num_envs = NUM_ENVS
    env_cfg.seed = EVAL_SEED
    configure_scenario(env_cfg, "Turning")
    twist = env_cfg.commands["twist"]
    twist.ranges.ang_vel_z = (yaw_command, yaw_command)
    base_env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0")
    env = RslRlVecEnvWrapper(base_env, clip_actions=agent_cfg.clip_actions)
    policy = policy_for(label, env, agent_cfg)
    robot = base_env.scene["robot"]
    obs = env.get_observations()
    active = torch.ones(NUM_ENVS, dtype=torch.bool, device="cuda:0")
    yaw_sum = torch.zeros(NUM_ENVS, device="cuda:0")
    yaw_abs_error_sum = torch.zeros(NUM_ENVS, device="cuda:0")
    xy_speed_sum = torch.zeros(NUM_ENVS, device="cuda:0")
    steps = torch.zeros(NUM_ENVS, device="cuda:0")
    fell = torch.zeros(NUM_ENVS, dtype=torch.bool, device="cuda:0")
    max_steps = math.ceil(env_cfg.episode_length_s / base_env.step_dt)
    with torch.inference_mode():
        for _ in range(max_steps):
            yaw = robot.data.root_link_ang_vel_b[:, 2]
            yaw_sum += yaw * active
            yaw_abs_error_sum += torch.abs(yaw_command - yaw) * active
            xy_speed_sum += torch.linalg.vector_norm(robot.data.root_link_lin_vel_b[:, :2], dim=-1) * active
            steps += active
            obs, _, dones, _ = env.step(policy(obs))
            newly_done = dones.bool() & active
            if newly_done.any():
                fell |= newly_done & base_env.termination_manager.get_term("fell_over")
                active &= ~newly_done
            if not active.any():
                break
    safe_steps = steps.clamp(min=1)
    result = {
        "model": label,
        "yaw_command_radps": yaw_command,
        "episodes": NUM_ENVS,
        "seed": EVAL_SEED,
        "mean_achieved_yaw_radps": float((yaw_sum / safe_steps).mean()),
        "mean_abs_yaw_error_radps": float((yaw_abs_error_sum / safe_steps).mean()),
        "mean_xy_speed_mps": float((xy_speed_sum / safe_steps).mean()),
        "fell_over_rate": float(fell.float().mean()),
    }
    env.close()
    return result


def main() -> None:
    configure_torch_backends()
    rows = []
    for label in ("official", "seed42", "seed123"):
        for yaw in YAW_COMMANDS:
            row = evaluate(label, yaw)
            rows.append(row)
            print(json.dumps(row), flush=True)
    output = ROOT / "video_diagnostics" / "yaw_command_sweep.json"
    output.write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
