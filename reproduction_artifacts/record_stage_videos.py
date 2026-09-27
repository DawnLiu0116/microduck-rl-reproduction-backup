"""Record deterministic comparison videos for selected MicroDuck checkpoints."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import torch
from rsl_rl.runners import OnPolicyRunner

import mjlab.tasks  # noqa: F401 - populate the task registry
import mjlab_microduck.tasks  # noqa: F401 - populate MicroDuck tasks
from mjlab.envs import ManagerBasedRlEnv
from mjlab.rl import RslRlVecEnvWrapper
from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
from mjlab.utils.torch import configure_torch_backends
from mjlab.utils.wrappers import VideoRecorder


TASK_ID = "Mjlab-Velocity-Flat-MicroDuck"
RUN_DIR = Path(
    "/home/deuler/microduck_rl/logs/rsl_rl/velocity/"
    "2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2"
)
OUTPUT_DIR = Path(
    "/mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/"
    "outputs/microduck_reproduction/videos"
)
CHECKPOINTS = (0, 500, 1000, 2000, 3000, 3999)
EVAL_SEED = 123
VIDEO_STEPS = 500  # 10 seconds at the task's 50 Hz control rate.
WIDTH = 640
HEIGHT = 480


def record_checkpoint(iteration: int) -> Path:
    checkpoint = RUN_DIR / f"model_{iteration}.pt"
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)

    env_cfg = load_env_cfg(TASK_ID, play=True)
    agent_cfg = load_rl_cfg(TASK_ID)
    env_cfg.scene.num_envs = 1
    env_cfg.seed = EVAL_SEED
    env_cfg.viewer.width = WIDTH
    env_cfg.viewer.height = HEIGHT

    base_env = ManagerBasedRlEnv(
        cfg=env_cfg,
        device="cuda:0",
        render_mode="rgb_array",
    )
    prefix = f"microduck_iter_{iteration:04d}"
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
        str(checkpoint),
        load_cfg={"actor": True},
        strict=True,
        map_location="cuda:0",
    )
    policy = runner.get_inference_policy(device="cuda:0")

    obs = env.get_observations()
    with torch.inference_mode():
        for _ in range(VIDEO_STEPS):
            actions = policy(obs)
            obs, _, _, _ = env.step(actions)
    env.close()

    video = OUTPUT_DIR / f"{prefix}-step-0.mp4"
    if not video.is_file() or video.stat().st_size == 0:
        raise RuntimeError(f"Video was not written correctly: {video}")
    return video


def main() -> None:
    configure_torch_backends()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for iteration in CHECKPOINTS:
        output = record_checkpoint(iteration)
        print(f"RECORDED {iteration}: {output} ({output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
