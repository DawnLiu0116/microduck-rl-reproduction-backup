"""Evaluate official alpha_walking.onnx under the frozen multi-seed protocol.

The ONNX graph is mapped exactly to a CUDA torch module for batched inference.
An ONNX Runtime equivalence check is performed before simulation.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path

import numpy as np
import onnx
from onnx import numpy_helper
import onnxruntime as ort
import torch
import torch.nn.functional as F

import mjlab.tasks  # noqa: F401
import mjlab_microduck.tasks  # noqa: F401
from mjlab.envs import ManagerBasedRlEnv
from mjlab.rl import RslRlVecEnvWrapper
from mjlab.tasks.registry import load_env_cfg, load_rl_cfg
from mjlab.utils.torch import configure_torch_backends

import sys

UNIFIED_DIR = Path(
    "/mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/outputs/"
    "microduck_reproduction/unified_evaluation"
)
sys.path.insert(0, str(UNIFIED_DIR))
from run_unified_evaluation import (  # noqa: E402
    ALL_SCENARIOS,
    TASK_ID,
    configure_scenario,
    wilson_interval,
)


ROOT = Path(
    "/mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/outputs/"
    "microduck_reproduction/official_comparison"
)
ONNX_PATH = ROOT / "alpha_walking_official.onnx"
EVAL_SEEDS = (1001, 2002, 3003)
EPISODES = 128
MODEL_LABEL = "official_alpha_walking"
PROGRESS_PATH = ROOT / "official_progress.json"


class OfficialOnnxTorchPolicy(torch.nn.Module):
    def __init__(self, path: Path, device: str):
        super().__init__()
        model = onnx.load(path)
        arrays = {item.name: numpy_helper.to_array(item).copy() for item in model.graph.initializer}
        self.register_buffer("mean", torch.from_numpy(arrays["obs_normalizer._mean"]).to(device))
        self.register_buffer("denom", torch.from_numpy(arrays["onnx::Div_24"]).to(device))
        self.layers = torch.nn.ModuleList()
        for index in (0, 2, 4, 6):
            weight = arrays[f"mlp.{index}.weight"]
            bias = arrays[f"mlp.{index}.bias"]
            layer = torch.nn.Linear(weight.shape[1], weight.shape[0], bias=True, device=device)
            with torch.no_grad():
                layer.weight.copy_(torch.from_numpy(weight).to(device))
                layer.bias.copy_(torch.from_numpy(bias).to(device))
            self.layers.append(layer)
        self.eval()

    def forward(self, observations) -> torch.Tensor:
        x = observations["actor"] if hasattr(observations, "keys") else observations
        x = (x - self.mean) / self.denom
        for layer in self.layers[:-1]:
            x = F.elu(layer(x))
        return self.layers[-1](x)


def validate_mapping(policy: OfficialOnnxTorchPolicy) -> dict:
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(
        str(ONNX_PATH), sess_options=options, providers=["CPUExecutionProvider"]
    )
    rng = np.random.default_rng(20260923)
    errors = []
    with torch.inference_mode():
        for _ in range(100):
            value = rng.normal(0.0, 1.0, size=(1, 61)).astype(np.float32)
            expected = session.run(["actions"], {"obs": value})[0]
            actual = policy(torch.from_numpy(value).to("cuda:0")).cpu().numpy()
            errors.append(np.abs(expected - actual))
    errors_np = np.concatenate(errors)
    result = {
        "samples": 100,
        "action_values": int(errors_np.size),
        "max_absolute_error": float(errors_np.max()),
        "mean_absolute_error": float(errors_np.mean()),
        "all_finite": bool(np.isfinite(errors_np).all()),
    }
    if not result["all_finite"] or result["max_absolute_error"] > 1e-5:
        raise RuntimeError(f"ONNX-to-torch mapping mismatch: {result}")
    return result


def evaluate(policy: OfficialOnnxTorchPolicy, scenario: str, seed: int) -> dict:
    env_cfg = load_env_cfg(TASK_ID, play=True)
    agent_cfg = load_rl_cfg(TASK_ID)
    env_cfg.scene.num_envs = EPISODES
    env_cfg.seed = seed
    configure_scenario(env_cfg, scenario)
    base_env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0")
    env = RslRlVecEnvWrapper(base_env, clip_actions=agent_cfg.clip_actions)

    device = base_env.device
    done = torch.zeros(EPISODES, dtype=torch.bool, device=device)
    steps = torch.zeros(EPISODES, dtype=torch.long, device=device)
    returns = torch.zeros(EPISODES, device=device)
    xy_error_sum = torch.zeros(EPISODES, device=device)
    yaw_error_sum = torch.zeros(EPISODES, device=device)
    action_delta_sum = torch.zeros(EPISODES, device=device)
    action_delta_count = torch.zeros(EPISODES, device=device)
    command_sum = torch.zeros((EPISODES, 3), device=device)
    previous_action = None
    causes = {
        name: torch.zeros(EPISODES, dtype=torch.bool, device=device)
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
            command_sum += command_value * active[:, None]
            actions = policy(obs)
            if previous_action is not None:
                action_delta_sum += torch.linalg.vector_norm(
                    actions - previous_action, dim=-1
                ) * active
                action_delta_count += active
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
        raise RuntimeError(f"{scenario}/{seed}: {done.sum().item()}/{EPISODES} finished")
    safe_steps = steps.float().clamp(min=1)
    successful = (
        causes["time_out"]
        & ~causes["fell_over"]
        & ~causes["nan_state"]
        & ~causes["out_of_terrain_bounds"]
    )
    success_count = int(successful.sum().item())
    fall_count = int(causes["fell_over"].sum().item())
    success_ci = wilson_interval(success_count, EPISODES)
    fall_ci = wilson_interval(fall_count, EPISODES)
    mean_command = (command_sum / safe_steps[:, None]).mean(dim=0)
    result = {
        "model_label": MODEL_LABEL,
        "checkpoint": str(ONNX_PATH),
        "scenario": scenario,
        "episodes": EPISODES,
        "seed": seed,
        "success_count": success_count,
        "success_rate": success_count / EPISODES,
        "success_wilson95_low": success_ci[0],
        "success_wilson95_high": success_ci[1],
        "fell_over_count": fall_count,
        "fell_over_rate": fall_count / EPISODES,
        "fell_over_wilson95_low": fall_ci[0],
        "fell_over_wilson95_high": fall_ci[1],
        "time_out_rate": causes["time_out"].float().mean().item(),
        "out_of_terrain_rate": causes["out_of_terrain_bounds"].float().mean().item(),
        "nan_state_rate": causes["nan_state"].float().mean().item(),
        "mean_episode_steps": steps.float().mean().item(),
        "mean_episode_seconds": (steps.float() * base_env.step_dt).mean().item(),
        "mean_return": returns.mean().item(),
        "mean_xy_velocity_error_mps": (xy_error_sum / safe_steps).mean().item(),
        "mean_yaw_velocity_error_radps": (yaw_error_sum / safe_steps).mean().item(),
        "mean_action_delta_l2": (action_delta_sum / action_delta_count.clamp(min=1)).mean().item(),
        "measured_mean_command_x": mean_command[0].item(),
        "measured_mean_command_y": mean_command[1].item(),
        "measured_mean_command_yaw": mean_command[2].item(),
    }
    env.close()
    return result


def save_progress(rows: list[dict], equivalence: dict) -> None:
    temp = PROGRESS_PATH.with_suffix(".tmp")
    temp.write_text(
        json.dumps({"equivalence": equivalence, "results": rows}, indent=2),
        encoding="utf-8",
    )
    temp.replace(PROGRESS_PATH)


def aggregate(rows: list[dict]) -> list[dict]:
    output = []
    metrics = (
        "mean_episode_seconds", "mean_return", "mean_xy_velocity_error_mps",
        "mean_yaw_velocity_error_radps", "mean_action_delta_l2", "nan_state_rate",
        "out_of_terrain_rate",
    )
    for scenario in ALL_SCENARIOS:
        values = sorted((row for row in rows if row["scenario"] == scenario), key=lambda r: r["seed"])
        total = sum(row["episodes"] for row in values)
        successes = sum(row["success_count"] for row in values)
        falls = sum(row["fell_over_count"] for row in values)
        success_ci = wilson_interval(successes, total)
        fall_ci = wilson_interval(falls, total)
        result = {
            "model_label": MODEL_LABEL,
            "scenario": scenario,
            "evaluation_seeds": list(EVAL_SEEDS),
            "total_episodes": total,
            "success_count": successes,
            "success_rate": successes / total,
            "success_wilson95_low": success_ci[0],
            "success_wilson95_high": success_ci[1],
            "success_rate_between_seed_std": statistics.stdev(row["success_rate"] for row in values),
            "fell_over_count": falls,
            "fell_over_rate": falls / total,
            "fell_over_wilson95_low": fall_ci[0],
            "fell_over_wilson95_high": fall_ci[1],
        }
        for metric in metrics:
            result[metric] = statistics.mean(row[metric] for row in values)
        output.append(result)
    return output


def main() -> None:
    configure_torch_backends()
    policy = OfficialOnnxTorchPolicy(ONNX_PATH, "cuda:0")
    equivalence = validate_mapping(policy)
    print(f"EQUIVALENCE {json.dumps(equivalence)}", flush=True)
    if PROGRESS_PATH.is_file():
        rows = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))["results"]
    else:
        rows = []
    completed = {(row["scenario"], int(row["seed"])) for row in rows}
    for seed in EVAL_SEEDS:
        for scenario in ALL_SCENARIOS:
            if (scenario, seed) in completed:
                continue
            print(f"START official/{scenario}/{seed} ({len(rows)+1}/18)", flush=True)
            result = evaluate(policy, scenario, seed)
            rows.append(result)
            save_progress(rows, equivalence)
            print(f"DONE official/{scenario}/{seed}: {result['success_count']}/128", flush=True)

    aggregates = aggregate(rows)
    payload = {
        "source": "Pollen Robotics official alpha_walking.onnx",
        "source_url": "https://huggingface.co/pollen-robotics/microduck-policies/blob/main/alpha_walking.onnx",
        "repository_provenance": "wandb pollen-robotics/mjlab_microduck/441tzs6d model_3750.pt",
        "onnx_to_torch_equivalence": equivalence,
        "raw_results": rows,
        "aggregate_results": aggregates,
    }
    json_path = ROOT / "official_multi_seed_evaluation.json"
    csv_path = ROOT / "official_multi_seed_aggregate.csv"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    flat_rows = []
    for row in aggregates:
        flat = dict(row)
        flat["evaluation_seeds"] = ",".join(map(str, flat["evaluation_seeds"]))
        flat_rows.append(flat)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat_rows[0]))
        writer.writeheader()
        writer.writerows(flat_rows)
    print(f"JSON={json_path}")
    print(f"CSV={csv_path}")


if __name__ == "__main__":
    main()
