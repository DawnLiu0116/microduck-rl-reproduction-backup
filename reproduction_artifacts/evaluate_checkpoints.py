"""Deterministic one-episode-per-env evaluation of milestone policies."""

from __future__ import annotations

import json
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
RUN_DIR = Path(
    "/home/deuler/microduck_rl/logs/rsl_rl/velocity/"
    "2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2"
)
ROOT = Path("/mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction")
ITERATIONS = (0, 500, 1000, 2000, 3000, 3999)
NUM_ENVS = 128
EVAL_SEED = 123
MAX_STEPS = 1100


def evaluate(iteration: int, push_interval: tuple[float, float] | None = None) -> dict:
    env_cfg = load_env_cfg(TASK_ID, play=True)
    agent_cfg = load_rl_cfg(TASK_ID)
    env_cfg.scene.num_envs = NUM_ENVS
    env_cfg.seed = EVAL_SEED
    if push_interval is not None:
        env_cfg.events["push_robot"].interval_range_s = push_interval
    base_env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0")
    env = RslRlVecEnvWrapper(base_env, clip_actions=agent_cfg.clip_actions)

    runner_cls = load_runner_cls(TASK_ID) or OnPolicyRunner
    runner = runner_cls(env, asdict(agent_cfg), device="cuda:0")
    runner.load(
        str(RUN_DIR / f"model_{iteration}.pt"),
        load_cfg={"actor": True},
        strict=True,
        map_location="cuda:0",
    )
    policy = runner.get_inference_policy(device="cuda:0")

    device = base_env.device
    done = torch.zeros(NUM_ENVS, dtype=torch.bool, device=device)
    steps = torch.zeros(NUM_ENVS, dtype=torch.long, device=device)
    returns = torch.zeros(NUM_ENVS, device=device)
    xy_error_sum = torch.zeros(NUM_ENVS, device=device)
    yaw_error_sum = torch.zeros(NUM_ENVS, device=device)
    action_delta_sum = torch.zeros(NUM_ENVS, device=device)
    action_delta_count = torch.zeros(NUM_ENVS, device=device)
    previous_action = None
    causes = {name: torch.zeros(NUM_ENVS, dtype=torch.bool, device=device) for name in (
        "fell_over", "time_out", "out_of_terrain_bounds", "nan_state"
    )}

    obs = env.get_observations()
    command = base_env.command_manager.get_term("twist")
    robot = base_env.scene["robot"]

    with torch.inference_mode():
        for _ in range(MAX_STEPS):
            active = ~done
            if not active.any():
                break
            xy_error = torch.linalg.vector_norm(
                command.vel_command_b[:, :2] - robot.data.root_link_lin_vel_b[:, :2], dim=-1
            )
            yaw_error = torch.abs(
                command.vel_command_b[:, 2] - robot.data.root_link_ang_vel_b[:, 2]
            )
            xy_error_sum += xy_error * active
            yaw_error_sum += yaw_error * active

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
        raise RuntimeError(f"Checkpoint {iteration}: only {done.sum().item()}/{NUM_ENVS} episodes completed")

    safe_steps = steps.float().clamp(min=1)
    successful = causes["time_out"] & ~causes["fell_over"] & ~causes["nan_state"] & ~causes["out_of_terrain_bounds"]
    result = {
        "iteration": iteration,
        "episodes": NUM_ENVS,
        "seed": EVAL_SEED,
        "success_rate": successful.float().mean().item(),
        "fell_over_rate": causes["fell_over"].float().mean().item(),
        "time_out_rate": causes["time_out"].float().mean().item(),
        "out_of_terrain_rate": causes["out_of_terrain_bounds"].float().mean().item(),
        "nan_state_rate": causes["nan_state"].float().mean().item(),
        "mean_episode_steps": steps.float().mean().item(),
        "mean_episode_seconds": (steps.float() * base_env.step_dt).mean().item(),
        "mean_return": returns.mean().item(),
        "mean_xy_velocity_error": (xy_error_sum / safe_steps).mean().item(),
        "mean_yaw_velocity_error": (yaw_error_sum / safe_steps).mean().item(),
        "mean_action_delta_l2": (
            action_delta_sum / action_delta_count.clamp(min=1)
        ).mean().item(),
        "play_push_interval_seconds": list(env_cfg.events["push_robot"].interval_range_s),
    }
    env.close()
    return result


def main() -> None:
    configure_torch_backends()
    results = []
    for iteration in ITERATIONS:
        result = evaluate(iteration)
        results.append(result)
        print(json.dumps(result, sort_keys=True), flush=True)
    output = {
        "protocol": {
            "task": TASK_ID,
            "num_envs_per_checkpoint": NUM_ENVS,
            "seed": EVAL_SEED,
            "one_first_episode_per_env": True,
            "deterministic_inference_policy": True,
            "play_config": True,
        },
        "results": results,
    }
    (ROOT / "checkpoint_evaluation.json").write_text(
        json.dumps(output, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
