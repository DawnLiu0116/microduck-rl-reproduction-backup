"""Record matched Forward, Turning and Stress videos for both final policies."""

from __future__ import annotations

import os
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
from mjlab.utils.wrappers import VideoRecorder

from evidence_video_v2 import record_first_episode


TASK_ID = "Mjlab-Velocity-Flat-MicroDuck"
REPO_ROOT = Path(os.environ.get("MICRODUCK_REPO_ROOT", Path.cwd()))
CHECKPOINTS = {
    "seed42": REPO_ROOT / "logs/rsl_rl/velocity/2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2/model_3999.pt",
    "seed123": REPO_ROOT / "logs/rsl_rl/velocity/2026-09-22_19-08-01_walk_baseline_4096_seed123_4000_v1/model_3999.pt",
    "seed2026": REPO_ROOT / "logs/rsl_rl/velocity/2026-09-29_10-44-28_walk_baseline_4096_seed2026_4000_v1_resume3250_quiet/model_3999.pt",
}
FIXED_VIDEO_COMMANDS = {
    "Forward": (0.3, 0.0, 0.0),
    "Turning": (0.0, 0.0, 0.6),
    "Stress": (0.3, 0.0, 0.0),
}
OUTPUT_DIR = Path(os.environ.get(
    "MICRODUCK_VIDEO_OUTPUT_DIR",
    Path(__file__).resolve().parent / "comparison_videos",
))
SCENARIOS = tuple(
    item.strip()
    for item in os.environ.get("MICRODUCK_VIDEO_SCENARIOS", "Forward,Turning,Stress").split(",")
    if item.strip()
)
MODELS = tuple(
    item.strip()
    for item in os.environ.get("MICRODUCK_VIDEO_MODELS", ",".join(CHECKPOINTS)).split(",")
    if item.strip()
)
EVAL_SEED = 1001
VIDEO_STEPS = int(os.environ.get("MICRODUCK_VIDEO_STEPS", "500"))
WIDTH = 640
HEIGHT = 480


def zero_pose_command(command_cfg) -> None:
    command_cfg.ranges = tuple((0.0, 0.0) for _ in command_cfg.ranges)
    command_cfg.resampling_time_range = (1000.0, 1001.0)
    command_cfg.zero_command_prob = 1.0


def configure_scenario(env_cfg, scenario: str) -> None:
    env_cfg.events["push_robot"].interval_range_s = (
        (0.5, 1.0) if scenario == "Stress" else (1000.0, 1001.0)
    )
    # Stress is deliberately a *fixed forward command under frequent pushes*.
    # Leaving the command random made different policies receive different tasks
    # after command resampling or an automatic episode reset.
    command = FIXED_VIDEO_COMMANDS[scenario]
    twist = env_cfg.commands["twist"]
    twist.ranges.lin_vel_x = (command[0], command[0])
    twist.ranges.lin_vel_y = (command[1], command[1])
    twist.ranges.ang_vel_z = (command[2], command[2])
    twist.resampling_time_range = (1000.0, 1001.0)
    twist.rel_standing_envs = 0.0
    twist.rel_forward_envs = 0.0
    twist.rel_turn_in_place_envs = 0.0
    twist.rel_heading_envs = 0.0
    zero_pose_command(env_cfg.commands["head_pose"])
    zero_pose_command(env_cfg.commands["body_pose"])


def record(model_label: str, checkpoint: Path, scenario: str) -> Path:
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    prefix = f"microduck_{model_label}_{scenario.lower()}"
    target = OUTPUT_DIR / f"{prefix}-step-0.mp4"
    if target.is_file() and target.stat().st_size > 0:
        print(f"SKIP existing {target}")
        return target

    env_cfg = load_env_cfg(TASK_ID, play=True)
    agent_cfg = load_rl_cfg(TASK_ID)
    env_cfg.scene.num_envs = 1
    env_cfg.seed = EVAL_SEED
    env_cfg.viewer.width = WIDTH
    env_cfg.viewer.height = HEIGHT
    configure_scenario(env_cfg, scenario)

    base_env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0", render_mode="rgb_array")
    recorded_env = VideoRecorder(
        base_env,
        video_folder=OUTPUT_DIR,
        step_trigger=lambda step: step == 0,
        video_length=VIDEO_STEPS,
        name_prefix=prefix,
        disable_logger=False,
    )
    env = RslRlVecEnvWrapper(recorded_env, clip_actions=agent_cfg.clip_actions)
    runner_cls = load_runner_cls(TASK_ID) or OnPolicyRunner
    runner = runner_cls(env, asdict(agent_cfg), device="cuda:0")
    runner.load(
        str(checkpoint), load_cfg={"actor": True}, strict=True, map_location="cuda:0"
    )
    policy = runner.get_inference_policy(device="cuda:0")
    summary = record_first_episode(
        base_env=base_env,
        env=env,
        policy=policy,
        target=target,
        scenario=scenario,
        command=FIXED_VIDEO_COMMANDS[scenario],
        video_steps=VIDEO_STEPS,
    )
    if not target.is_file() or target.stat().st_size == 0:
        raise RuntimeError(f"Video missing or empty: {target}")
    print(f"RECORDED {target} ({target.stat().st_size} bytes) {summary}")
    return target


def main() -> None:
    configure_torch_backends()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for scenario in SCENARIOS:
        for model_label in MODELS:
            if model_label not in CHECKPOINTS:
                raise ValueError(f"Unknown model label: {model_label}")
            record(model_label, CHECKPOINTS[model_label], scenario)


if __name__ == "__main__":
    main()
