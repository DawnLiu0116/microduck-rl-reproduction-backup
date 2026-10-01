"""Pilot temporal defenses on MicroDuck without retraining the walking policy.

The timestamp-aware defense is given sensor age for the delay condition. This is
explicit protocol metadata, not an inferred anomaly label: a pure fixed delay is
generally not identifiable from a smooth observation vector alone.
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
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
FAULT_DIR = BASE / "sensor_fault_benchmark"
sys.path[:0] = [str(FAULT_DIR), str(BASE / "unified_evaluation")]

from run_sensor_fault_scan import (  # noqa: E402
    MODELS, SCENARIO, SENSOR_SLICE, TASK_ID, FaultInjector, load_policy,
)
from run_confirmatory_faults import FAULTS  # noqa: E402
from run_unified_evaluation import configure_scenario, wilson_interval  # noqa: E402


MODEL_LABELS = ("seed123_iter3999", "seed2026_iter3999")
FAULT_NAMES = ("clean", "delay_2", "spike_100")
DEFENSES = ("none", "static_clip", "naive_adaptive", "constrained_timestamp")
EPISODES = 64
EVAL_SEED = 5005
RESULT = ROOT / "defense_pilot_v2.json"
PROGRESS = ROOT / "defense_pilot_v2_progress.json"
DT = 0.02


class TemporalDefense:
    def __init__(self, name: str, envs: int, device: torch.device):
        self.name = name
        self.envs = envs
        self.device = device
        self.previous_clean: torch.Tensor | None = None
        self.previous_raw: torch.Tensor | None = None
        self.ema_mean: torch.Tensor | None = None
        self.ema_var: torch.Tensor | None = None
        self.base_thresholds = torch.tensor(
            [3.0] * 3 + [0.20] * 3 + [0.25] * 14 + [5.0] * 14,
            device=device,
        )
        self.thresholds = self.base_thresholds.clone()

    def _prediction(self, previous: torch.Tensor) -> torch.Tensor:
        predicted = previous.clone()
        omega = previous[:, 0:3]
        gravity = previous[:, 3:6]
        predicted[:, 3:6] = gravity - DT * torch.linalg.cross(omega, gravity, dim=-1)
        predicted[:, 3:6] /= torch.linalg.vector_norm(predicted[:, 3:6], dim=-1, keepdim=True).clamp(min=1e-6)
        predicted[:, 6:20] = previous[:, 6:20] + DT * previous[:, 20:34]
        return predicted

    def _timestamp_compensate(self, raw: torch.Tensor, delay_steps: int) -> torch.Tensor:
        if delay_steps <= 0 or self.previous_raw is None:
            return raw
        output = raw.clone()
        correction = delay_steps * (raw - self.previous_raw)
        correction = torch.clamp(
            correction,
            -delay_steps * self.base_thresholds,
            delay_steps * self.base_thresholds,
        )
        output[:, 0:3] = raw[:, 0:3] + correction[:, 0:3]
        gravity = raw[:, 3:6] - (delay_steps * DT) * torch.linalg.cross(
            raw[:, 0:3], raw[:, 3:6], dim=-1
        )
        output[:, 3:6] = gravity / torch.linalg.vector_norm(gravity, dim=-1, keepdim=True).clamp(min=1e-6)
        output[:, 6:20] = raw[:, 6:20] + delay_steps * DT * raw[:, 20:34]
        output[:, 20:34] = raw[:, 20:34] + correction[:, 20:34]
        return output

    def sanitize(self, observations, fault: dict) -> tuple[object, torch.Tensor, torch.Tensor]:
        output = observations.clone()
        raw = observations["actor"][:, SENSOR_SLICE]
        zeros = torch.zeros(self.envs, device=self.device)
        if self.previous_clean is None:
            self.previous_clean = raw.clone()
            self.previous_raw = raw.clone()
            self.ema_mean = raw.clone()
            self.ema_var = self.base_thresholds.square().unsqueeze(0).expand_as(raw).clone()
            return output, zeros, zeros

        predicted = self._prediction(self.previous_clean)
        if self.name == "none":
            clean = raw
            anomaly = zeros
        elif self.name == "static_clip":
            clean = torch.clamp(raw, self.previous_clean - self.base_thresholds, self.previous_clean + self.base_thresholds)
            anomaly = (clean != raw).float().mean(dim=-1)
        elif self.name == "naive_adaptive":
            assert self.ema_mean is not None and self.ema_var is not None
            scale = torch.sqrt(self.ema_var).clamp(min=0.5 * self.base_thresholds)
            bad = torch.abs(raw - self.ema_mean) > 6.0 * scale
            clean = torch.where(bad, self.ema_mean, raw)
            anomaly = bad.float().mean(dim=-1)
            # Deliberately naive: polluted observations update the reference state.
            alpha = 0.02
            delta = raw - self.ema_mean
            self.ema_mean = (1 - alpha) * self.ema_mean + alpha * raw
            self.ema_var = (1 - alpha) * self.ema_var + alpha * delta.square()
        elif self.name == "constrained_timestamp":
            delay_steps = int(fault.get("steps", 0)) if fault["type"] == "delay" else 0
            candidate = self._timestamp_compensate(raw, delay_steps)
            if delay_steps > 0:
                # Sensor age comes from timestamp metadata, so accept the bounded
                # kinematic projection instead of trying to detect an unobservable delay.
                clean = candidate
                anomaly = zeros
                triggered = torch.zeros(self.envs, dtype=torch.bool, device=self.device)
                innovation = candidate - raw
            else:
                # Detect abrupt corruption against the last raw frame. Reconstruct
                # only implausible channels; preserving the rest avoids whole-frame
                # false-positive cascades on a clean gait.
                innovation = raw - self.previous_raw
                bad = torch.abs(innovation) > self.thresholds
                severe = torch.abs(innovation) > 2.5 * self.thresholds
                triggered = (bad.sum(dim=-1) >= 4) | severe[:, :6].any(dim=-1)
                replace = bad & triggered.unsqueeze(-1)
                clean = torch.where(replace, predicted, raw)
                anomaly = torch.where(triggered, bad.float().mean(dim=-1), zeros)
            # Adapt only on accepted frames, and keep thresholds within fixed safety bounds.
            accepted = ~triggered
            if accepted.any():
                observed = torch.quantile(torch.abs(innovation[accepted]), 0.95, dim=0)
                proposal = 0.995 * self.thresholds + 0.005 * (2.0 * observed)
                self.thresholds = torch.maximum(
                    0.5 * self.base_thresholds,
                    torch.minimum(2.0 * self.base_thresholds, proposal),
                )
        else:
            raise ValueError(self.name)

        output["actor"][:, SENSOR_SLICE] = clean
        intervention = (torch.abs(clean - raw) > 1e-7).float().mean(dim=-1)
        self.previous_raw = raw.clone()
        self.previous_clean = clean.clone()
        return output, anomaly, intervention


def evaluate(model_label: str, fault: dict, defense_name: str) -> dict:
    env_cfg = load_env_cfg(TASK_ID, play=True)
    agent_cfg = load_rl_cfg(TASK_ID)
    env_cfg.scene.num_envs = EPISODES
    env_cfg.seed = EVAL_SEED
    configure_scenario(env_cfg, SCENARIO)
    base_env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0")
    env = RslRlVecEnvWrapper(base_env, clip_actions=agent_cfg.clip_actions)
    policy = load_policy(model_label, env, agent_cfg)
    injector = FaultInjector(fault, EVAL_SEED, base_env.device)
    defense = TemporalDefense(defense_name, EPISODES, base_env.device)

    done = torch.zeros(EPISODES, dtype=torch.bool, device=base_env.device)
    steps = torch.zeros(EPISODES, dtype=torch.long, device=base_env.device)
    returns = torch.zeros(EPISODES, device=base_env.device)
    xy_error_sum = torch.zeros(EPISODES, device=base_env.device)
    max_tilt = torch.zeros(EPISODES, device=base_env.device)
    action_jump = torch.zeros(EPISODES, device=base_env.device)
    action_count = torch.zeros(EPISODES, device=base_env.device)
    anomaly_sum = torch.zeros(EPISODES, device=base_env.device)
    intervention_sum = torch.zeros(EPISODES, device=base_env.device)
    previous_action = None
    causes = {
        name: torch.zeros(EPISODES, dtype=torch.bool, device=base_env.device)
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
            tilt = torch.acos(torch.clamp(-robot.data.projected_gravity_b[:, 2], -1.0, 1.0))
            max_tilt = torch.maximum(max_tilt, tilt * active)
            corrupted, _ = injector.apply(obs)
            guarded, anomaly, intervention = defense.sanitize(corrupted, fault)
            anomaly_sum += anomaly * active
            intervention_sum += intervention * active
            actions = policy(guarded)
            if previous_action is not None:
                delta = torch.linalg.vector_norm(actions - previous_action, dim=-1)
                action_jump += (delta > 1.0).float() * active
                action_count += active
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
        raise RuntimeError(f"{model_label}/{fault['name']}/{defense_name}: incomplete")
    safe_steps = steps.float().clamp(min=1)
    successful = causes["time_out"] & ~causes["fell_over"] & ~causes["nan_state"] & ~causes["out_of_terrain_bounds"]
    count = int(successful.sum().item())
    result = {
        "model_label": model_label,
        "fault_name": fault["name"],
        "defense": defense_name,
        "episodes": EPISODES,
        "seed": EVAL_SEED,
        "success_count": count,
        "success_rate": count / EPISODES,
        "success_wilson95": list(wilson_interval(count, EPISODES)),
        "fell_over_count": int(causes["fell_over"].sum().item()),
        "mean_episode_seconds": float((steps.float() * base_env.step_dt).mean().item()),
        "mean_return": float(returns.mean().item()),
        "mean_xy_velocity_error_mps": float((xy_error_sum / safe_steps).mean().item()),
        "mean_max_tilt_deg": float(torch.rad2deg(max_tilt).mean().item()),
        "action_jump_rate_gt_1": float((action_jump / action_count.clamp(min=1)).mean().item()),
        "mean_anomaly_score": float((anomaly_sum / safe_steps).mean().item()),
        "mean_intervention_fraction": float((intervention_sum / safe_steps).mean().item()),
        "nan_state_rate": float(causes["nan_state"].float().mean().item()),
        "out_of_terrain_rate": float(causes["out_of_terrain_bounds"].float().mean().item()),
        "timestamp_metadata_used": defense_name == "constrained_timestamp" and fault["type"] == "delay",
    }
    env.close()
    return result


def save(rows: list[dict], complete: bool) -> None:
    payload = {
        "protocol": "defense-pilot-0.2",
        "purpose": "screening only; one evaluation seed",
        "episodes_per_job": EPISODES,
        "evaluation_seed": EVAL_SEED,
        "models": list(MODEL_LABELS),
        "faults": list(FAULT_NAMES),
        "defenses": list(DEFENSES),
        "complete": complete,
        "timestamp_disclosure": "constrained_timestamp receives the configured sensor age only for delay faults",
        "results": rows,
    }
    target = RESULT if complete else PROGRESS
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp.replace(target)


def main() -> None:
    configure_torch_backends()
    ROOT.mkdir(parents=True, exist_ok=True)
    faults = {item["name"]: item for item in FAULTS}
    rows = []
    if PROGRESS.is_file():
        rows = json.loads(PROGRESS.read_text(encoding="utf-8"))["results"]
    completed = {(r["model_label"], r["fault_name"], r["defense"]) for r in rows}
    total = len(MODEL_LABELS) * len(FAULT_NAMES) * len(DEFENSES)
    for model in MODEL_LABELS:
        for fault_name in FAULT_NAMES:
            for defense in DEFENSES:
                key = (model, fault_name, defense)
                if key in completed:
                    continue
                print(f"START {model}/{fault_name}/{defense} ({len(rows)+1}/{total})", flush=True)
                row = evaluate(model, faults[fault_name], defense)
                rows.append(row)
                save(rows, False)
                print(
                    f"DONE success={row['success_count']}/{EPISODES} "
                    f"intervention={row['mean_intervention_fraction']:.4f} "
                    f"tilt={row['mean_max_tilt_deg']:.2f}",
                    flush=True,
                )
    if len(rows) != total:
        raise RuntimeError(f"Expected {total} rows, found {len(rows)}")
    save(rows, True)
    print(f"RESULT={RESULT}")


if __name__ == "__main__":
    main()
