"""Screen MicroDuck policies under controlled actor-observation sensor faults.

This is a sensitivity scan, not an adversarial optimizer. Only actor sensor fields
[0:34] are modified; action history and command fields remain unchanged.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import zlib
from collections import deque
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


BASE = Path(os.environ.get("MICRODUCK_ARTIFACT_ROOT", Path(__file__).resolve().parent.parent))
REPO_ROOT = Path(os.environ.get("MICRODUCK_REPO_ROOT", Path.cwd()))
UNIFIED_DIR = BASE / "unified_evaluation"
OFFICIAL_DIR = BASE / "official_comparison"
ROOT = BASE / "sensor_fault_benchmark"
PROGRESS = ROOT / "progress.json"
RESULT = ROOT / "sensor_fault_scan.json"

sys.path[:0] = [str(UNIFIED_DIR), str(OFFICIAL_DIR)]
from run_unified_evaluation import TASK_ID, configure_scenario, wilson_interval  # noqa: E402
from run_official_onnx_evaluation import ONNX_PATH, OfficialOnnxTorchPolicy  # noqa: E402


MODELS = {
    "official_alpha_walking": ONNX_PATH,
    "seed42_iter3999": Path(
        REPO_ROOT / "logs/rsl_rl/velocity/"
        "2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2/model_3999.pt"
    ),
    "seed123_iter3999": Path(
        REPO_ROOT / "logs/rsl_rl/velocity/"
        "2026-09-22_19-08-01_walk_baseline_4096_seed123_4000_v1/model_3999.pt"
    ),
    "seed2026_iter3999": Path(
        REPO_ROOT / "logs/rsl_rl/velocity/"
        "2026-09-29_10-44-28_walk_baseline_4096_seed2026_4000_v1_resume3250_quiet/"
        "model_3999.pt"
    ),
}
SEED = 5005
EPISODES = 64
SCENARIO = "Forward"
SENSOR_SLICE = slice(0, 34)
ACTION_HISTORY_SLICE = slice(34, 48)
COMMAND_AND_POSE_SLICE = slice(48, 61)


FAULTS = [
    {"name": "clean", "type": "clean", "severity": "none"},
    {"name": "noise_mild", "type": "noise", "severity": "mild", "scale": 1.0},
    {"name": "noise_medium", "type": "noise", "severity": "medium", "scale": 4.0},
    {"name": "noise_severe", "type": "noise", "severity": "severe", "scale": 10.0},
    {"name": "imu_bias_mild", "type": "imu_bias", "severity": "mild", "scale": 1.0},
    {"name": "imu_bias_medium", "type": "imu_bias", "severity": "medium", "scale": 3.0},
    {"name": "imu_bias_severe", "type": "imu_bias", "severity": "severe", "scale": 8.0},
    {"name": "delay_1", "type": "delay", "severity": "mild", "steps": 1},
    {"name": "delay_3", "type": "delay", "severity": "medium", "steps": 3},
    {"name": "delay_5", "type": "delay", "severity": "severe", "steps": 5},
    {"name": "freeze_5", "type": "freeze", "severity": "mild", "duration": 5, "period": 180},
    {"name": "freeze_15", "type": "freeze", "severity": "medium", "duration": 15, "period": 180},
    {"name": "freeze_30", "type": "freeze", "severity": "severe", "duration": 30, "period": 180},
    {"name": "spike_025", "type": "spike", "severity": "mild", "scale": 0.25, "duration": 5, "period": 200},
    {"name": "spike_050", "type": "spike", "severity": "medium", "scale": 0.5, "duration": 5, "period": 200},
    {"name": "spike_100", "type": "spike", "severity": "severe", "scale": 1.0, "duration": 5, "period": 200},
]


class FaultInjector:
    def __init__(self, spec: dict, seed: int, device: torch.device):
        self.spec = spec
        self.step = 0
        self.delay_buffer: deque[torch.Tensor] = deque()
        self.freeze_value: torch.Tensor | None = None
        self.generator = torch.Generator(device=device)
        stable_offset = zlib.crc32(spec["name"].encode("utf-8"))
        self.generator.manual_seed(seed + stable_offset)

    def apply(self, observations):
        output = observations.clone()
        clean = observations["actor"]
        if clean.shape[-1] != 61:
            raise RuntimeError(f"Expected 61 actor observations, got {clean.shape}")
        actor = clean.clone()
        fault_type = self.spec["type"]

        if fault_type == "noise":
            scale = float(self.spec["scale"])
            actor[:, 0:3] += torch.randn(actor[:, 0:3].shape, generator=self.generator, device=actor.device) * (0.05 * scale)
            actor[:, 3:6] += torch.randn(actor[:, 3:6].shape, generator=self.generator, device=actor.device) * (0.005 * scale)
            actor[:, 6:20] += torch.randn(actor[:, 6:20].shape, generator=self.generator, device=actor.device) * (0.005 * scale)
            actor[:, 20:34] += torch.randn(actor[:, 20:34].shape, generator=self.generator, device=actor.device) * (0.10 * scale)
        elif fault_type == "imu_bias":
            scale = float(self.spec["scale"])
            actor[:, 0:3] += actor.new_tensor([0.10, -0.10, 0.05]) * scale
            actor[:, 3:6] += actor.new_tensor([0.025, -0.020, 0.0]) * scale
        elif fault_type == "delay":
            delay = int(self.spec["steps"])
            self.delay_buffer.append(clean[:, SENSOR_SLICE].clone())
            while len(self.delay_buffer) > delay + 1:
                self.delay_buffer.popleft()
            actor[:, SENSOR_SLICE] = self.delay_buffer[0]
        elif fault_type == "freeze":
            period = int(self.spec["period"])
            duration = int(self.spec["duration"])
            phase = self.step % period
            if self.step > 0 and phase == 0:
                self.freeze_value = clean[:, SENSOR_SLICE].clone()
            if self.step > 0 and phase < duration and self.freeze_value is not None:
                actor[:, SENSOR_SLICE] = self.freeze_value
        elif fault_type == "spike":
            period = int(self.spec["period"])
            duration = int(self.spec["duration"])
            phase = self.step % period
            if self.step > 0 and phase < duration:
                scale = float(self.spec["scale"])
                actor[:, 0:3] += actor.new_tensor([12.0, -16.0, 24.0]) * scale
                actor[:, 3:6] += actor.new_tensor([0.80, 0.0, 0.0]) * scale
                joint_pattern = actor.new_tensor(
                    [8, -10, 7, -8, 10, -7, 6, -6, 8, -8, 5, -5, 7, -7]
                )
                actor[:, 20:34] += joint_pattern * scale
        elif fault_type != "clean":
            raise ValueError(f"Unknown fault type: {fault_type}")

        if not torch.equal(actor[:, ACTION_HISTORY_SLICE], clean[:, ACTION_HISTORY_SLICE]):
            raise RuntimeError("Fault modified action-history fields")
        if not torch.equal(actor[:, COMMAND_AND_POSE_SLICE], clean[:, COMMAND_AND_POSE_SLICE]):
            raise RuntimeError("Fault modified command/pose fields")
        output["actor"] = actor
        self.step += 1
        perturbation = torch.linalg.vector_norm(
            actor[:, SENSOR_SLICE] - clean[:, SENSOR_SLICE], dim=-1
        )
        return output, perturbation


def load_policy(model_label: str, env, agent_cfg):
    checkpoint = MODELS[model_label]
    if model_label == "official_alpha_walking":
        return OfficialOnnxTorchPolicy(checkpoint, "cuda:0")
    runner_cls = load_runner_cls(TASK_ID) or OnPolicyRunner
    runner = runner_cls(env, asdict(agent_cfg), device="cuda:0")
    runner.load(str(checkpoint), load_cfg={"actor": True}, strict=True, map_location="cuda:0")
    return runner.get_inference_policy(device="cuda:0")


def evaluate(model_label: str, fault: dict, episodes: int, seed: int, episode_output: Path) -> dict:
    env_cfg = load_env_cfg(TASK_ID, play=True)
    agent_cfg = load_rl_cfg(TASK_ID)
    env_cfg.scene.num_envs = episodes
    env_cfg.seed = seed
    configure_scenario(env_cfg, SCENARIO)
    base_env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0")
    env = RslRlVecEnvWrapper(base_env, clip_actions=agent_cfg.clip_actions)
    policy = load_policy(model_label, env, agent_cfg)
    injector = FaultInjector(fault, seed, base_env.device)

    done = torch.zeros(episodes, dtype=torch.bool, device=base_env.device)
    steps = torch.zeros(episodes, dtype=torch.long, device=base_env.device)
    returns = torch.zeros(episodes, device=base_env.device)
    xy_error_sum = torch.zeros(episodes, device=base_env.device)
    yaw_error_sum = torch.zeros(episodes, device=base_env.device)
    action_delta_sum = torch.zeros(episodes, device=base_env.device)
    action_delta_count = torch.zeros(episodes, device=base_env.device)
    action_jump_count = torch.zeros(episodes, device=base_env.device)
    max_action_abs = torch.zeros(episodes, device=base_env.device)
    max_tilt_rad = torch.zeros(episodes, device=base_env.device)
    perturbation_sum = torch.zeros(episodes, device=base_env.device)
    perturbation_max = torch.zeros(episodes, device=base_env.device)
    previous_action = None
    causes = {
        name: torch.zeros(episodes, dtype=torch.bool, device=base_env.device)
        for name in ("fell_over", "time_out", "out_of_terrain_bounds", "nan_state")
    }
    obs = env.get_observations()
    command = base_env.command_manager.get_term("twist")
    robot = base_env.scene["robot"]
    max_steps = math.ceil(env_cfg.episode_length_s / base_env.step_dt) + 100

    with torch.inference_mode():
        for _ in range(max_steps):
            active = ~done
            if not active.any():
                break
            command_value = command.vel_command_b
            xy_error_sum += torch.linalg.vector_norm(
                command_value[:, :2] - robot.data.root_link_lin_vel_b[:, :2], dim=-1
            ) * active
            yaw_error_sum += torch.abs(
                command_value[:, 2] - robot.data.root_link_ang_vel_b[:, 2]
            ) * active
            tilt = torch.acos(torch.clamp(-robot.data.projected_gravity_b[:, 2], -1.0, 1.0))
            max_tilt_rad = torch.maximum(max_tilt_rad, tilt * active)

            corrupted_obs, perturbation = injector.apply(obs)
            perturbation_sum += perturbation * active
            perturbation_max = torch.maximum(perturbation_max, perturbation * active)
            actions = policy(corrupted_obs)
            max_action_abs = torch.maximum(max_action_abs, actions.abs().amax(dim=-1) * active)
            if previous_action is not None:
                delta = torch.linalg.vector_norm(actions - previous_action, dim=-1)
                action_delta_sum += delta * active
                action_delta_count += active
                action_jump_count += (delta > 1.0).float() * active
            previous_action = actions.clone()
            obs, reward, dones, _ = env.step(actions)
            steps += active.long()
            returns += reward * active
            newly_done = dones.bool() & active
            if newly_done.any():
                for name in causes:
                    causes[name] |= newly_done & base_env.termination_manager.get_term(name)
                done |= newly_done

    if not done.all():
        env.close()
        raise RuntimeError(f"{model_label}/{fault['name']}: {done.sum().item()}/{episodes} finished")
    safe_steps = steps.float().clamp(min=1)
    safe_delta_count = action_delta_count.clamp(min=1)
    successful = causes["time_out"] & ~causes["fell_over"] & ~causes["nan_state"] & ~causes["out_of_terrain_bounds"]
    success_count = int(successful.sum().item())
    fall_count = int(causes["fell_over"].sum().item())
    result = {
        "model_label": model_label,
        "fault_name": fault["name"],
        "fault_type": fault["type"],
        "severity": fault["severity"],
        "fault_parameters": fault,
        "scenario": SCENARIO,
        "episodes": episodes,
        "seed": seed,
        "success_count": success_count,
        "success_rate": success_count / episodes,
        "success_wilson95_low": wilson_interval(success_count, episodes)[0],
        "success_wilson95_high": wilson_interval(success_count, episodes)[1],
        "fell_over_count": fall_count,
        "fell_over_rate": fall_count / episodes,
        "mean_episode_seconds": (steps.float() * base_env.step_dt).mean().item(),
        "mean_return": returns.mean().item(),
        "mean_xy_velocity_error_mps": (xy_error_sum / safe_steps).mean().item(),
        "mean_yaw_velocity_error_radps": (yaw_error_sum / safe_steps).mean().item(),
        "mean_action_delta_l2": (action_delta_sum / safe_delta_count).mean().item(),
        "action_jump_rate_gt_1": (action_jump_count / safe_delta_count).mean().item(),
        "mean_max_action_abs": max_action_abs.mean().item(),
        "mean_max_tilt_deg": torch.rad2deg(max_tilt_rad).mean().item(),
        "mean_sensor_perturbation_l2": (perturbation_sum / safe_steps).mean().item(),
        "mean_max_sensor_perturbation_l2": perturbation_max.mean().item(),
        "nan_state_rate": causes["nan_state"].float().mean().item(),
        "out_of_terrain_rate": causes["out_of_terrain_bounds"].float().mean().item(),
    }
    # Preserve first-episode records; reset episodes are excluded by the done mask.
    values = {
        "episode": torch.arange(episodes, device=base_env.device),
        "steps": steps,
        "seconds": steps.float() * base_env.step_dt,
        "return": returns,
        "survival": successful,
        **causes,
        "mean_xy_velocity_error_mps": xy_error_sum / safe_steps,
        "mean_yaw_velocity_error_radps": yaw_error_sum / safe_steps,
        "mean_action_delta_l2": action_delta_sum / safe_delta_count,
        "action_jump_rate_gt_1": action_jump_count / safe_delta_count,
        "max_action_abs": max_action_abs,
        "max_pre_step_tilt_deg": torch.rad2deg(max_tilt_rad),
        "mean_sensor_perturbation_l2": perturbation_sum / safe_steps,
        "max_sensor_perturbation_l2": perturbation_max,
    }
    for name, tensor in values.items():
        if not torch.isfinite(tensor).all():
            env.close()
            raise RuntimeError(f"Nonfinite episode metric: {name}")
    columns = {name: tensor.cpu().tolist() for name, tensor in values.items()}
    records = [
        {"model_label": model_label, "fault_name": fault["name"], "seed": seed,
         **{name: column[i] for name, column in columns.items()}}
        for i in range(episodes)
    ]
    import csv
    episode_output.parent.mkdir(parents=True, exist_ok=True)
    temp = episode_output.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    temp.replace(episode_output)
    result["raw_episode_file"] = str(episode_output)
    result["success_semantics"] = "time_out_without_fall_nan_or_bounds; survival_not_task_success"
    env.close()
    return result



