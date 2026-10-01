"""Run measurement-only task protocol v2.1 and retain one row per first episode."""

from __future__ import annotations

import csv
import json
import math
import os
import statistics
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


ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
UNIFIED = BASE / "unified_evaluation"
OFFICIAL_DIR = BASE / "official_comparison"
sys.path[:0] = [str(UNIFIED), str(OFFICIAL_DIR)]

from run_unified_evaluation import TASK_ID, set_zero_pose_command, wilson_interval  # noqa: E402
from run_official_onnx_evaluation import ONNX_PATH, OfficialOnnxTorchPolicy, validate_mapping  # noqa: E402


PROTOCOL = json.loads((ROOT / "protocol.json").read_text(encoding="utf-8"))
SEEDS = tuple(PROTOCOL["evaluation_seeds"])
EPISODES = int(PROTOCOL["episodes_per_model_scenario_seed"])
SCENARIOS = ("Forward", "Turning", "Standing", "Stress-forward")
REPO_ROOT = Path(os.environ.get("MICRODUCK_REPO_ROOT", Path.cwd()))
MODEL_PATHS = {
    "seed42": REPO_ROOT / "logs/rsl_rl/velocity/2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2/model_3999.pt",
    "seed123": REPO_ROOT / "logs/rsl_rl/velocity/2026-09-22_19-08-01_walk_baseline_4096_seed123_4000_v1/model_3999.pt",
}
RAW_DIR = ROOT / "raw_episodes_measurement"
PROGRESS = ROOT / "measurement_progress.json"
FINAL_JSON = ROOT / "measurement_v2_results.json"
AGGREGATE_CSV = ROOT / "measurement_v2_aggregate.csv"


def configure(env_cfg, scenario: str) -> tuple[float, float, float]:
    cfg = PROTOCOL["scenarios"][scenario]
    command = tuple(float(value) for value in cfg["command"])
    env_cfg.events["push_robot"].interval_range_s = tuple(cfg["push_interval_seconds"])
    twist = env_cfg.commands["twist"]
    twist.ranges.lin_vel_x = (command[0], command[0])
    twist.ranges.lin_vel_y = (command[1], command[1])
    twist.ranges.ang_vel_z = (command[2], command[2])
    twist.resampling_time_range = (1000.0, 1001.0)
    twist.rel_standing_envs = 1.0 if scenario == "Standing" else 0.0
    twist.rel_forward_envs = 0.0
    twist.rel_turn_in_place_envs = 0.0
    twist.rel_heading_envs = 0.0
    set_zero_pose_command(env_cfg.commands["head_pose"])
    set_zero_pose_command(env_cfg.commands["body_pose"])
    return command


def interval_timer(base_env, term_name: str) -> torch.Tensor:
    names = base_env.event_manager.active_terms["interval"]
    return base_env.event_manager._interval_term_time_left[names.index(term_name)]


def evaluate(model: str, policy_source, scenario: str, seed: int) -> tuple[dict, list[dict]]:
    env_cfg = load_env_cfg(TASK_ID, play=True)
    agent_cfg = load_rl_cfg(TASK_ID)
    env_cfg.scene.num_envs = EPISODES
    env_cfg.seed = seed
    command_tuple = configure(env_cfg, scenario)
    base_env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0")
    env = RslRlVecEnvWrapper(base_env, clip_actions=agent_cfg.clip_actions)
    if model == "official":
        policy = policy_source
    else:
        runner_cls = load_runner_cls(TASK_ID) or OnPolicyRunner
        runner = runner_cls(env, asdict(agent_cfg), device="cuda:0")
        runner.load(str(policy_source), load_cfg={"actor": True}, strict=True, map_location="cuda:0")
        policy = runner.get_inference_policy(device="cuda:0")

    device = base_env.device
    zeros = lambda: torch.zeros(EPISODES, device=device)
    done = torch.zeros(EPISODES, dtype=torch.bool, device=device)
    steps = torch.zeros(EPISODES, dtype=torch.long, device=device)
    returns = zeros()
    sums = {name: zeros() for name in (
        "xy_error", "abs_vx_error", "abs_vy", "yaw_error", "planar_speed", "abs_yaw_speed", "action_delta"
    )}
    action_delta_count = zeros()
    push_count = torch.zeros(EPISODES, dtype=torch.long, device=device)
    recovered_push_count = torch.zeros_like(push_count)
    pending = torch.zeros(EPISODES, dtype=torch.bool, device=device)
    pending_steps = torch.zeros_like(push_count)
    stable_steps = torch.zeros_like(push_count)
    recovery_time_sum = zeros()
    causes = {name: torch.zeros(EPISODES, dtype=torch.bool, device=device) for name in ("fell_over", "time_out", "out_of_terrain_bounds", "nan_state")}

    robot = base_env.scene["robot"]
    twist = base_env.command_manager.get_term("twist")
    initial_xy = robot.data.root_link_pos_w[:, :2].clone()
    last_xy = initial_xy.clone()
    previous_action = None
    obs = env.get_observations()
    max_steps = math.ceil(env_cfg.episode_length_s / base_env.step_dt) + 100
    push_timer = interval_timer(base_env, "push_robot")

    with torch.inference_mode():
        for _ in range(max_steps):
            active = ~done
            if not active.any():
                break
            command = twist.vel_command_b
            lin = robot.data.root_link_lin_vel_b
            ang = robot.data.root_link_ang_vel_b
            xy_error = torch.linalg.vector_norm(command[:, :2] - lin[:, :2], dim=-1)
            abs_vx_error = torch.abs(command[:, 0] - lin[:, 0])
            abs_vy = torch.abs(lin[:, 1])
            yaw_error = torch.abs(command[:, 2] - ang[:, 2])
            planar_speed = torch.linalg.vector_norm(lin[:, :2], dim=-1)
            abs_yaw_speed = torch.abs(ang[:, 2])
            for name, values in (
                ("xy_error", xy_error), ("abs_vx_error", abs_vx_error), ("abs_vy", abs_vy),
                ("yaw_error", yaw_error), ("planar_speed", planar_speed), ("abs_yaw_speed", abs_yaw_speed),
            ):
                sums[name] += values * active
            last_xy[active] = robot.data.root_link_pos_w[active, :2]

            recovering = active & pending
            stable_steps = torch.where(recovering & (xy_error <= 0.20), stable_steps + 1, torch.where(recovering, torch.zeros_like(stable_steps), stable_steps))
            newly_recovered = recovering & (stable_steps >= 5)
            recovered_push_count += newly_recovered.long()
            recovery_time_sum += newly_recovered * ((pending_steps.float() + 1.0) * base_env.step_dt)
            pending &= ~newly_recovered
            pending_steps += (active & pending).long()

            if scenario == "Stress-forward":
                push_due = active & (push_timer <= base_env.step_dt + 1.0e-6)
                push_count += push_due.long()
                pending |= push_due
                pending_steps = torch.where(push_due, torch.zeros_like(pending_steps), pending_steps)
                stable_steps = torch.where(push_due, torch.zeros_like(stable_steps), stable_steps)

            actions = policy(obs)
            if previous_action is not None:
                sums["action_delta"] += torch.linalg.vector_norm(actions - previous_action, dim=-1) * active
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
        raise RuntimeError(f"{model}/{scenario}/{seed}: {int(done.sum())}/{EPISODES} finished")

    safe_steps = steps.float().clamp(min=1)
    displacement = last_xy - initial_xy
    recovered_fraction = recovered_push_count.float() / push_count.clamp(min=1).float()
    mean_recovery_gate = torch.where(recovered_push_count > 0, recovery_time_sum / recovered_push_count.clamp(min=1).float(), torch.full_like(recovery_time_sum, 1.0e9))
    metrics = {
        "mean_xy_velocity_error_mps": sums["xy_error"] / safe_steps,
        "mean_abs_vx_error_mps": sums["abs_vx_error"] / safe_steps,
        "mean_abs_vy_mps": sums["abs_vy"] / safe_steps,
        "mean_abs_yaw_error_radps": sums["yaw_error"] / safe_steps,
        "mean_planar_speed_mps": sums["planar_speed"] / safe_steps,
        "mean_abs_yaw_speed_radps": sums["abs_yaw_speed"] / safe_steps,
        "absolute_lateral_displacement_m": torch.abs(displacement[:, 1]),
        "planar_displacement_m": torch.linalg.vector_norm(displacement, dim=-1),
        "recovered_push_fraction": recovered_fraction,
        "mean_recovery_seconds_for_gate": mean_recovery_gate,
    }
    survival = causes["time_out"] & ~causes["fell_over"] & ~causes["nan_state"] & ~causes["out_of_terrain_bounds"]
    rows = []
    for index in range(EPISODES):
        recovered = int(recovered_push_count[index].item())
        rows.append({
            "protocol_version": "2.1-measurement-only", "model": model, "scenario": scenario, "seed": seed, "episode": index,
            "steps": int(steps[index].item()), "seconds": float(steps[index].item() * base_env.step_dt),
            "return": float(returns[index].item()), "survival": bool(survival[index].item()),
            **{name: bool(values[index].item()) for name, values in causes.items()},
            **{name: float(values[index].item()) for name, values in metrics.items() if name != "mean_recovery_seconds_for_gate"},
            "push_count": int(push_count[index].item()), "recovered_push_count": recovered,
            "mean_recovery_seconds": None if recovered == 0 else float(mean_recovery_gate[index].item()),
            "mean_action_delta_l2": float((sums["action_delta"][index] / action_delta_count[index].clamp(min=1)).item()),
        })
    survival_count = int(survival.sum().item())
    summary = {
        "protocol_version": "2.1-measurement-only", "model": model, "scenario": scenario, "seed": seed, "episodes": EPISODES,
        "survival_count": survival_count, "survival_rate": survival_count / EPISODES,
        "survival_wilson95": list(wilson_interval(survival_count, EPISODES)),
    }
    for name in (
        "mean_xy_velocity_error_mps", "mean_abs_vx_error_mps", "mean_abs_vy_mps",
        "mean_abs_yaw_error_radps", "mean_planar_speed_mps", "mean_abs_yaw_speed_radps",
        "absolute_lateral_displacement_m", "planar_displacement_m", "recovered_push_fraction",
    ):
        summary[name] = float(metrics[name].mean().item())
    recovered_times = [row["mean_recovery_seconds"] for row in rows if row["mean_recovery_seconds"] is not None]
    summary["mean_recovery_seconds"] = None if not recovered_times else statistics.mean(recovered_times)
    summary["raw_episode_file"] = str(RAW_DIR / f"{model}_{scenario}_{seed}.csv")
    env.close()
    return summary, rows


def write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def aggregate(jobs: list[dict]) -> list[dict]:
    output = []
    for model in ("official", "seed42", "seed123"):
        for scenario in SCENARIOS:
            selected = [row for row in jobs if row["model"] == model and row["scenario"] == scenario]
            total = sum(row["episodes"] for row in selected)
            survival = sum(row["survival_count"] for row in selected)
            item = {
                "model": model, "scenario": scenario, "episodes": total,
                "survival_count": survival, "survival_rate": survival / total,
                "survival_wilson95_low": wilson_interval(survival, total)[0],
                "survival_wilson95_high": wilson_interval(survival, total)[1],
            }
            for name in (
                "mean_xy_velocity_error_mps", "mean_abs_vx_error_mps", "mean_abs_vy_mps",
                "mean_abs_yaw_error_radps", "mean_planar_speed_mps", "mean_abs_yaw_speed_radps",
                "absolute_lateral_displacement_m", "planar_displacement_m", "recovered_push_fraction",
            ):
                item[name] = statistics.mean(row[name] for row in selected)
            recovery = [row["mean_recovery_seconds"] for row in selected if row["mean_recovery_seconds"] is not None]
            item["mean_recovery_seconds"] = None if not recovery else statistics.mean(recovery)
            output.append(item)
    return output


def save_progress(jobs: list[dict], equivalence: dict) -> None:
    temp = PROGRESS.with_suffix(".tmp")
    temp.write_text(json.dumps({"protocol_version": "2.1-measurement-only", "official_equivalence": equivalence, "jobs": jobs}, indent=2), encoding="utf-8")
    temp.replace(PROGRESS)


def main() -> None:
    configure_torch_backends()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    official = OfficialOnnxTorchPolicy(ONNX_PATH, "cuda:0")
    equivalence = validate_mapping(official)
    policies = {"official": official, **MODEL_PATHS}
    if PROGRESS.is_file():
        jobs = json.loads(PROGRESS.read_text(encoding="utf-8"))["jobs"]
    else:
        jobs = []
    completed = {(row["model"], row["scenario"], int(row["seed"])) for row in jobs}
    for seed in SEEDS:
        for scenario in SCENARIOS:
            for model, source in policies.items():
                key = (model, scenario, seed)
                if key in completed:
                    continue
                print(f"START {model}/{scenario}/{seed} ({len(jobs)+1}/36)", flush=True)
                summary, rows = evaluate(model, source, scenario, seed)
                write_rows(Path(summary["raw_episode_file"]), rows)
                jobs.append(summary)
                save_progress(jobs, equivalence)
                print(f"DONE {model}/{scenario}/{seed}: survival={summary['survival_count']}/{EPISODES}", flush=True)
    aggregates = aggregate(jobs)
    payload = {
        "complete": len(jobs) == 36,
        "protocol": PROTOCOL,
        "official_equivalence": equivalence,
        "job_count": len(jobs),
        "total_episodes": len(jobs) * EPISODES,
        "jobs": jobs,
        "aggregate": aggregates,
    }
    FINAL_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with AGGREGATE_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(aggregates[0]))
        writer.writeheader()
        writer.writerows(aggregates)
    print(json.dumps(aggregates, indent=2), flush=True)


if __name__ == "__main__":
    main()
