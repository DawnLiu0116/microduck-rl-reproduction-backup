"""Record official alpha_walking videos using the frozen comparison settings."""

from __future__ import annotations

import sys
from pathlib import Path

import torch
import mjlab.tasks  # noqa: F401
import mjlab_microduck.tasks  # noqa: F401
from mjlab.envs import ManagerBasedRlEnv
from mjlab.rl import RslRlVecEnvWrapper
from mjlab.tasks.registry import load_env_cfg, load_rl_cfg
from mjlab.utils.torch import configure_torch_backends
from mjlab.utils.wrappers import VideoRecorder

BASE = Path("/mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction")
sys.path[:0] = [str(BASE), str(BASE / "official_comparison")]

from record_final_comparison_videos import (  # noqa: E402
    EVAL_SEED, HEIGHT, SCENARIOS, TASK_ID, VIDEO_STEPS, WIDTH, configure_scenario,
)
from run_official_onnx_evaluation import (  # noqa: E402
    ONNX_PATH, OfficialOnnxTorchPolicy, validate_mapping,
)

OUTPUT_DIR = BASE / "comparison_videos"


def record(policy: OfficialOnnxTorchPolicy, scenario: str) -> Path:
    prefix = f"microduck_official_{scenario.lower()}"
    target = OUTPUT_DIR / f"{prefix}-step-0.mp4"
    if target.is_file() and target.stat().st_size > 0:
        print(f"SKIP {target}")
        return target
    env_cfg = load_env_cfg(TASK_ID, play=True)
    agent_cfg = load_rl_cfg(TASK_ID)
    env_cfg.scene.num_envs = 1
    env_cfg.seed = EVAL_SEED
    env_cfg.viewer.width = WIDTH
    env_cfg.viewer.height = HEIGHT
    configure_scenario(env_cfg, scenario)
    base_env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0", render_mode="rgb_array")
    recorder = VideoRecorder(
        base_env, video_folder=OUTPUT_DIR, step_trigger=lambda step: step == 0,
        video_length=VIDEO_STEPS, name_prefix=prefix, disable_logger=False,
    )
    env = RslRlVecEnvWrapper(recorder, clip_actions=agent_cfg.clip_actions)
    obs = env.get_observations()
    with torch.inference_mode():
        for _ in range(VIDEO_STEPS):
            obs, _, _, _ = env.step(policy(obs))
    env.close()
    if not target.is_file() or target.stat().st_size == 0:
        raise RuntimeError(f"Missing video: {target}")
    print(f"RECORDED {target} {target.stat().st_size}")
    return target


def main() -> None:
    configure_torch_backends()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    policy = OfficialOnnxTorchPolicy(ONNX_PATH, "cuda:0")
    print(f"EQUIVALENCE {validate_mapping(policy)}")
    for scenario in SCENARIOS:
        record(policy, scenario)


if __name__ == "__main__":
    main()
