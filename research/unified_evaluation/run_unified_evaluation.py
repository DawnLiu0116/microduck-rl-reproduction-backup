"""Run the frozen six-scenario MicroDuck final-policy evaluation protocol."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
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


TASK_ID = "Mjlab-Velocity-Flat-MicroDuck"
ALL_SCENARIOS = ("Nominal", "Train-like", "Stress", "Forward", "Turning", "Standing")
PUSH_INTERVALS = {
    "Nominal": (1000.0, 1001.0),
    "Train-like": (3.0, 6.0),
    "Stress": (0.5, 1.0),
    "Forward": (1000.0, 1001.0),
    "Turning": (1000.0, 1001.0),
    "Standing": (1000.0, 1001.0),
}
FIXED_COMMANDS = {
    "Stress": (0.3, 0.0, 0.0),
    "Forward": (0.3, 0.0, 0.0),
    "Turning": (0.0, 0.0, 0.6),
    "Standing": (0.0, 0.0, 0.0),
}


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return (math.nan, math.nan)
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denominator
    margin = z / denominator * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total))
    return (max(0.0, center - margin), min(1.0, center + margin))


def set_zero_pose_command(command_cfg) -> None:
    command_cfg.ranges = tuple((0.0, 0.0) for _ in command_cfg.ranges)
    command_cfg.resampling_time_range = (1000.0, 1001.0)
    command_cfg.zero_command_prob = 1.0


def configure_scenario(env_cfg, scenario: str) -> None:
    env_cfg.events["push_robot"].interval_range_s = PUSH_INTERVALS[scenario]
    if scenario not in FIXED_COMMANDS:
        return

    x, y, yaw = FIXED_COMMANDS[scenario]
    twist = env_cfg.commands["twist"]
    twist.ranges.lin_vel_x = (x, x)
    twist.ranges.lin_vel_y = (y, y)
    twist.ranges.ang_vel_z = (yaw, yaw)
    twist.resampling_time_range = (1000.0, 1001.0)
    twist.rel_standing_envs = 1.0 if scenario == "Standing" else 0.0
    twist.rel_forward_envs = 0.0
    twist.rel_turn_in_place_envs = 0.0
    twist.rel_heading_envs = 0.0
    set_zero_pose_command(env_cfg.commands["head_pose"])
    set_zero_pose_command(env_cfg.commands["body_pose"])


def evaluate_scenario(
    checkpoint: Path,
    model_label: str,
    scenario: str,
    episodes: int,
    seed: int,
) -> dict:
    env_cfg = load_env_cfg(TASK_ID, play=True)
    agent_cfg = load_rl_cfg(TASK_ID)
    env_cfg.scene.num_envs = episodes
    env_cfg.seed = seed
    configure_scenario(env_cfg, scenario)

    base_env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0")
    env = RslRlVecEnvWrapper(base_env, clip_actions=agent_cfg.clip_actions)
    runner_cls = load_runner_cls(TASK_ID) or OnPolicyRunner
    runner = runner_cls(env, asdict(agent_cfg), device="cuda:0")
    runner.load(
        str(checkpoint),
        load_cfg={"actor": True},
        strict=True,
        map_location="cuda:0",
    )
    policy = runner.get_inference_policy(device="cuda:0")

    device = base_env.device
    done = torch.zeros(episodes, dtype=torch.bool, device=device)
    steps = torch.zeros(episodes, dtype=torch.long, device=device)
    returns = torch.zeros(episodes, device=device)
    xy_error_sum = torch.zeros(episodes, device=device)
    yaw_error_sum = torch.zeros(episodes, device=device)
    action_delta_sum = torch.zeros(episodes, device=device)
    action_delta_count = torch.zeros(episodes, device=device)
    command_sum = torch.zeros((episodes, 3), device=device)
    previous_action = None
    causes = {
        name: torch.zeros(episodes, dtype=torch.bool, device=device)
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
            xy_error = torch.linalg.vector_norm(
                command_value[:, :2] - robot.data.root_link_lin_vel_b[:, :2], dim=-1
            )
            yaw_error = torch.abs(command_value[:, 2] - robot.data.root_link_ang_vel_b[:, 2])
            xy_error_sum += xy_error * active
            yaw_error_sum += yaw_error * active
            command_sum += command_value * active[:, None]

            actions = policy(obs)
            if previous_action is not None:
                delta = torch.linalg.vector_norm(actions - previous_action, dim=-1)
                action_delta_sum += delta * active
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
        raise RuntimeError(f"{model_label}/{scenario}: only {done.sum().item()}/{episodes} episodes finished")

    safe_steps = steps.float().clamp(min=1)
    successful = (
        causes["time_out"]
        & ~causes["fell_over"]
        & ~causes["nan_state"]
        & ~causes["out_of_terrain_bounds"]
    )
    success_count = int(successful.sum().item())
    fall_count = int(causes["fell_over"].sum().item())
    success_ci = wilson_interval(success_count, episodes)
    fall_ci = wilson_interval(fall_count, episodes)
    mean_command = (command_sum / safe_steps[:, None]).mean(dim=0)

    result = {
        "model_label": model_label,
        "checkpoint": str(checkpoint),
        "scenario": scenario,
        "episodes": episodes,
        "seed": seed,
        "success_count": success_count,
        "success_rate": success_count / episodes,
        "success_wilson95_low": success_ci[0],
        "success_wilson95_high": success_ci[1],
        "fell_over_count": fall_count,
        "fell_over_rate": fall_count / episodes,
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
        "push_interval_seconds": list(PUSH_INTERVALS[scenario]),
    }
    env.close()
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-label", required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=128)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--scenarios", nargs="+", choices=ALL_SCENARIOS, default=list(ALL_SCENARIOS))
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.episodes < 128:
        raise ValueError("Frozen protocol requires at least 128 episodes per scenario")
    if not args.checkpoint.is_file():
        raise FileNotFoundError(args.checkpoint)
    configure_torch_backends()

    results = []
    for scenario in args.scenarios:
        result = evaluate_scenario(
            checkpoint=args.checkpoint,
            model_label=args.model_label,
            scenario=scenario,
            episodes=args.episodes,
            seed=args.seed,
        )
        results.append(result)
        print(json.dumps(result, sort_keys=True), flush=True)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "_", args.model_label)
    payload = {
        "protocol_version": "1.0",
        "task": TASK_ID,
        "model_label": args.model_label,
        "results": results,
    }
    json_path = args.output_dir / f"{safe_label}_unified_eval.json"
    csv_path = args.output_dir / f"{safe_label}_unified_eval.csv"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print(f"JSON={json_path}")
    print(f"CSV={csv_path}")


if __name__ == "__main__":
    main()
