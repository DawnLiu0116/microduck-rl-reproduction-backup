"""First-episode-only recording, telemetry, and visible protocol overlays."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import imageio
import imageio.v3 as iio
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont


FPS = 50
TERMINATION_NAMES = ("fell_over", "time_out", "out_of_terrain_bounds", "nan_state")


def _push_due(base_env) -> bool:
    names = base_env.event_manager.active_terms.get("interval", [])
    if "push_robot" not in names:
        return False
    index = names.index("push_robot")
    timer = base_env.event_manager._interval_term_time_left[index]
    return bool((timer[0] <= base_env.step_dt + 1.0e-6).item())


def _termination_cause(base_env) -> str:
    active = [name for name in TERMINATION_NAMES if bool(base_env.termination_manager.get_term(name)[0].item())]
    return "+".join(active) if active else "unknown"


def _annotate(frame: np.ndarray, row: dict, scenario: str) -> np.ndarray:
    image = Image.fromarray(frame)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.rectangle((0, 0, image.width, 58), fill=(0, 0, 0))
    draw.text((8, 5), f"{scenario} | t={row['time_s']:.2f}s | first episode only", fill="white", font=font)
    draw.text(
        (8, 22),
        "cmd [vx vy yaw]="
        f"[{row['cmd_vx']:+.2f} {row['cmd_vy']:+.2f} {row['cmd_yaw']:+.2f}]  "
        "actual="
        f"[{row['actual_vx']:+.2f} {row['actual_vy']:+.2f} {row['actual_yaw']:+.2f}]",
        fill="white",
        font=font,
    )
    if row.get("push_visible"):
        draw.rectangle((8, 40, 82, 56), fill=(255, 184, 0))
        draw.text((23, 42), "PUSH", fill="black", font=font)
    if row.get("terminated"):
        draw.rectangle((90, 40, image.width - 8, 56), fill=(185, 28, 28))
        draw.text(
            (100, 42),
            f"TERMINATED: {row['termination_cause']} | FRAME FROZEN - NOT STAND-UP",
            fill="white",
            font=font,
        )
    return np.asarray(image)


def record_first_episode(
    *,
    base_env,
    env,
    policy,
    target: Path,
    scenario: str,
    command: tuple[float, float, float],
    video_steps: int,
) -> dict:
    """Step only the first episode, then freeze and label the remaining video frames."""
    obs = env.get_observations()
    robot = base_env.scene["robot"]
    rows: list[dict] = []
    terminated_step = None
    termination_cause = ""
    push_visible_until = -1

    with torch.inference_mode():
        for step in range(video_steps):
            velocity = robot.data.root_link_lin_vel_b[0]
            angular = robot.data.root_link_ang_vel_b[0]
            push = _push_due(base_env) if scenario == "Stress" else False
            if push:
                push_visible_until = step + 9
            actions = policy(obs)
            obs, _, dones, _ = env.step(actions)
            terminated = bool(dones[0].item())
            cause = _termination_cause(base_env) if terminated else ""
            rows.append({
                "frame": step,
                "time_s": step * base_env.step_dt,
                "cmd_vx": command[0],
                "cmd_vy": command[1],
                "cmd_yaw": command[2],
                "actual_vx": float(velocity[0].item()),
                "actual_vy": float(velocity[1].item()),
                "actual_yaw": float(angular[2].item()),
                "push_event": push,
                "push_visible": step <= push_visible_until,
                "terminated": terminated,
                "termination_cause": cause,
                "frozen_after_termination": False,
            })
            if terminated:
                terminated_step = step
                termination_cause = cause
                break
    env.close()

    if not target.is_file() or target.stat().st_size == 0:
        raise RuntimeError(f"Raw video missing: {target}")
    raw_dir = target.parent / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / target.name
    if raw_path.exists():
        raw_path.unlink()
    shutil.move(target, raw_path)

    telemetry_dir = target.parent / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    csv_path = telemetry_dir / f"{target.stem}.csv"
    json_path = telemetry_dir / f"{target.stem}.json"

    raw_iter = iter(iio.imiter(raw_path, plugin="FFMPEG"))
    writer = imageio.get_writer(target, fps=FPS, codec="libx264", quality=8, macro_block_size=None)
    last_frame = None
    last_live_row = rows[-1]
    expanded_rows = []
    try:
        for frame_index in range(video_steps):
            use_frozen = terminated_step is not None and frame_index >= terminated_step
            if not use_frozen:
                try:
                    frame = next(raw_iter)
                    last_frame = frame
                except StopIteration:
                    use_frozen = True
            if use_frozen:
                if last_frame is None:
                    try:
                        last_frame = next(raw_iter)
                    except StopIteration as exc:
                        raise RuntimeError(f"No decodable frames in {raw_path}") from exc
                frame = last_frame
                row = dict(last_live_row)
                row.update({
                    "frame": frame_index,
                    "time_s": frame_index * base_env.step_dt,
                    "push_event": False,
                    "push_visible": False,
                    "terminated": True,
                    "termination_cause": termination_cause,
                    "frozen_after_termination": True,
                })
            else:
                row = dict(rows[min(frame_index, len(rows) - 1)])
            expanded_rows.append(row)
            writer.append_data(_annotate(frame, row, scenario))
    finally:
        writer.close()

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer_csv = csv.DictWriter(handle, fieldnames=list(expanded_rows[0]))
        writer_csv.writeheader()
        writer_csv.writerows(expanded_rows)
    summary = {
        "scenario": scenario,
        "command": list(command),
        "first_episode_only": True,
        "video_frames": video_steps,
        "terminated": terminated_step is not None,
        "termination_frame": terminated_step,
        "termination_time_s": None if terminated_step is None else terminated_step * base_env.step_dt,
        "termination_cause": termination_cause or None,
        "push_frames": [row["frame"] for row in rows if row["push_event"]],
        "raw_video": str(raw_path),
        "annotated_video": str(target),
        "telemetry_csv": str(csv_path),
    }
    json_path.write_text(json.dumps({"summary": summary, "frames": expanded_rows}, indent=2), encoding="utf-8")
    return summary
