"""Extract factual TensorBoard metrics and render MicroDuck training curves."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator


EVENT = Path(
    "/home/deuler/microduck_rl/logs/rsl_rl/velocity/"
    "2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2/"
    "events.out.tfevents.1789999035.songchxi.802.0"
)
OUT = Path(
    "/mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/"
    "outputs/microduck_reproduction"
)
PLOTS = OUT / "plots"

TAGS = [
    "Train/mean_reward",
    "Train/mean_episode_length",
    "Episode_Termination/nan_state",
    "Episode_Termination/fell_over",
    "Episode_Termination/time_out",
    "Metrics/twist/error_vel_xy",
    "Metrics/twist/error_vel_yaw",
    "Episode_Metrics/mean_action_acc",
    "Metrics/slip_velocity_mean",
    "Metrics/peak_height_mean",
    "Metrics/air_time_mean",
    "Policy/mean_std",
    "Loss/value",
    "Loss/surrogate",
    "Loss/entropy",
    "Loss/learning_rate",
    "Perf/total_fps",
    "Curriculum/action_rate_weight",
    "Curriculum/standing_envs",
    "Curriculum/head_pose_range",
    "Curriculum/body_pose_range",
    "Curriculum/com_range",
    "Curriculum/head_com_range",
    "Curriculum/head_pose_bias_weight",
]


def series(acc: EventAccumulator, tag: str) -> tuple[list[int], list[float]]:
    events = acc.Scalars(tag)
    return [event.step for event in events], [float(event.value) for event in events]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    acc = EventAccumulator(str(EVENT))
    acc.Reload()
    available = set(acc.Tags().get("scalars", []))
    tags = [tag for tag in TAGS if tag in available]

    by_tag = {}
    for tag in tags:
        steps, values = series(acc, tag)
        by_tag[tag] = dict(zip(steps, values, strict=True))

    reward_events = acc.Scalars("Train/mean_reward")
    all_steps = [event.step for event in reward_events]
    rows = []
    for step in all_steps:
        row = {"iteration": step}
        for tag in tags:
            row[tag] = by_tag[tag].get(step, "")
        rows.append(row)

    with (OUT / "metrics_history.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["iteration", *tags])
        writer.writeheader()
        writer.writerows(rows)

    final_step = reward_events[-1].step
    final = {tag: by_tag[tag].get(final_step) for tag in tags}
    reward_values = [float(event.value) for event in reward_events]
    best_index = max(range(len(reward_values)), key=reward_values.__getitem__)
    elapsed_events = acc.Scalars("Train/mean_reward/time")
    summary = {
        "final_iteration": final_step,
        "iterations_logged": len(reward_events),
        "num_envs": 4096,
        "steps_per_env_per_iteration": 24,
        "total_transitions": (final_step + 1) * 4096 * 24,
        "elapsed_training_seconds_logged": elapsed_events[-1].step,
        "best_mean_reward": reward_values[best_index],
        "best_mean_reward_iteration": reward_events[best_index].step,
        "max_nan_state": max(by_tag["Episode_Termination/nan_state"].values()),
        "final": final,
    }
    (OUT / "metrics_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    s, v = series(acc, "Train/mean_reward")
    axes[0].plot(s, v, linewidth=1.1, color="#2c7fb8")
    axes[0].set_ylabel("Mean reward")
    axes[0].set_title("MicroDuck PPO training: reward and episode length")
    s, v = series(acc, "Train/mean_episode_length")
    axes[1].plot(s, v, linewidth=1.1, color="#31a354")
    axes[1].set_ylabel("Mean episode length")
    axes[1].set_xlabel("PPO iteration")
    fig.tight_layout()
    fig.savefig(PLOTS / "training_reward_episode.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    for tag, label, color in [
        ("Metrics/twist/error_vel_xy", "Linear velocity error", "#d95f0e"),
        ("Metrics/twist/error_vel_yaw", "Yaw velocity error", "#756bb1"),
    ]:
        s, v = series(acc, tag)
        ax.plot(s, v, linewidth=1.1, label=label, color=color)
    ax.set_title("Command tracking errors")
    ax.set_xlabel("PPO iteration")
    ax.set_ylabel("Logged error")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS / "command_tracking_errors.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
    for ax, tag, label, color in [
        (axes[0], "Episode_Metrics/mean_action_acc", "Mean action acceleration", "#e6550d"),
        (axes[1], "Metrics/slip_velocity_mean", "Mean slip velocity", "#3182bd"),
        (axes[2], "Policy/mean_std", "Policy mean standard deviation", "#31a354"),
    ]:
        s, v = series(acc, tag)
        ax.plot(s, v, linewidth=1.1, color=color)
        ax.set_ylabel(label)
    axes[0].set_title("Action smoothness, foot slip, and policy exploration")
    axes[2].set_xlabel("PPO iteration")
    fig.tight_layout()
    fig.savefig(PLOTS / "safety_and_policy_metrics.png", dpi=180)
    plt.close(fig)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
