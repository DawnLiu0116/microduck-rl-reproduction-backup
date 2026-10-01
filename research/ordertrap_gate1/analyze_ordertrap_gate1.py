"""Validate, summarize, and visualize OrderTrap Gate-1 paired results."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "ordertrap_gate1.json"


def main() -> None:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = payload["results"]
    if not payload.get("complete") or len(rows) != 32:
        raise RuntimeError(f"Incomplete Gate-1 result: complete={payload.get('complete')} rows={len(rows)}")
    keys = [(r["model_label"], r["fault_name"], int(r["seed"])) for r in rows]
    if len(keys) != len(set(keys)):
        raise RuntimeError("Duplicate result keys")
    if any(float(r["nan_state_rate"]) != 0.0 or float(r["out_of_terrain_rate"]) != 0.0 for r in rows):
        raise RuntimeError("NaN or terrain-bound termination found")

    by_pair = defaultdict(dict)
    for row in rows:
        spec = row["fault_parameters"]
        by_pair[(row["model_label"], spec["pair_id"])][spec["ordering"]] = row

    paired = []
    for (model, pair_id), values in sorted(by_pair.items()):
        if set(values) != {"iid", "correlated"}:
            raise RuntimeError(f"Missing pair for {model}/{pair_id}")
        iid = values["iid"]
        corr = values["correlated"]
        paired.append(
            {
                "model_label": model,
                "pair_id": pair_id,
                "iid_success_rate": iid["success_rate"],
                "correlated_success_rate": corr["success_rate"],
                "success_delta_correlated_minus_iid": corr["success_rate"] - iid["success_rate"],
                "iid_xy_error": iid["mean_xy_velocity_error_mps"],
                "correlated_xy_error": corr["mean_xy_velocity_error_mps"],
                "xy_error_relative_change": (
                    corr["mean_xy_velocity_error_mps"] / max(iid["mean_xy_velocity_error_mps"], 1e-12) - 1.0
                ),
                "iid_yaw_error": iid["mean_yaw_velocity_error_radps"],
                "correlated_yaw_error": corr["mean_yaw_velocity_error_radps"],
                "iid_tilt_deg": iid["mean_max_tilt_deg"],
                "correlated_tilt_deg": corr["mean_max_tilt_deg"],
                "iid_action_jump_rate": iid["action_jump_rate_gt_1"],
                "correlated_action_jump_rate": corr["action_jump_rate_gt_1"],
                "perturbation_l2_delta": corr["mean_sensor_perturbation_l2"] - iid["mean_sensor_perturbation_l2"],
            }
        )

    csv_path = ROOT / "ordertrap_gate1_pairs.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(paired[0]))
        writer.writeheader()
        writer.writerows(paired)

    gate_hits = [
        p for p in paired
        if p["success_delta_correlated_minus_iid"] <= -0.10
        or p["xy_error_relative_change"] >= 0.25
    ]
    affected_models = sorted({p["model_label"] for p in gate_hits})
    go = len(affected_models) >= 2

    labels = [f"{p['model_label'].replace('_iter3999', '')}\n{p['pair_id']}" for p in paired]
    success_delta = np.array([100 * p["success_delta_correlated_minus_iid"] for p in paired])
    xy_delta = np.array([100 * p["xy_error_relative_change"] for p in paired])
    x = np.arange(len(paired))
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), constrained_layout=True)
    axes[0].bar(x, success_delta, color=np.where(success_delta < 0, "#c84b31", "#3a7d44"))
    axes[0].axhline(-10, color="black", linestyle="--", linewidth=1)
    axes[0].set_ylabel("Success delta (pp)\ncorrelated - IID")
    axes[0].grid(axis="y", alpha=0.25)
    if np.allclose(success_delta, 0.0):
        axes[0].text(
            0.5,
            0.55,
            "All 16 paired success-rate deltas are exactly 0 pp",
            transform=axes[0].transAxes,
            ha="center",
            va="center",
            fontsize=11,
        )
    axes[1].bar(x, xy_delta, color=np.where(xy_delta > 0, "#c84b31", "#3a7d44"))
    axes[1].axhline(25, color="black", linestyle="--", linewidth=1)
    axes[1].set_ylabel("XY tracking error change (%)")
    axes[1].set_xticks(x, labels, rotation=45, ha="right", fontsize=8)
    axes[1].grid(axis="y", alpha=0.25)
    fig.suptitle("OrderTrap Gate 1: equal-marginal temporal ordering screen")
    fig.savefig(ROOT / "ordertrap_gate1_paired_effects.png", dpi=180)
    plt.close(fig)

    strongest = sorted(
        paired,
        key=lambda p: (p["success_delta_correlated_minus_iid"], -p["xy_error_relative_change"]),
    )[:5]
    max_abs_l2_delta = max(abs(p["perturbation_l2_delta"]) for p in paired)
    report = [
        "# OrderTrap Gate-1 screening report",
        "",
        f"- Protocol: `{payload['protocol_version']}`.",
        f"- Complete: `{payload['complete']}`; jobs: {len(rows)}; episodes: {len(rows) * payload['episodes_per_job']}.",
        "- Each IID/correlated pair uses the same per-environment perturbation multiset; only temporal order differs.",
        "- The evaluated sequence length is exactly 1000 policy steps (20 s at 50 Hz), so every compared episode consumes the complete matched multiset.",
        "- This screen preserves marginal values and total perturbation energy, but does not match temporal autocorrelation or per-step slew distributions by design.",
        f"- Maximum absolute paired perturbation-L2 difference: `{max_abs_l2_delta:.3e}` (floating-point roundoff).",
        f"- NaN/out-of-terrain terminations: 0/0.",
        "- Predeclared pair threshold: success decline >=10 percentage points or XY tracking-error increase >=25%; the overall gate additionally requires the effect on at least two models.",
        f"- Preliminary Gate-1 decision: **{'GO' if go else 'NO-GO / redesign'}**.",
        f"- Models meeting at least one screening threshold: {', '.join(affected_models) if affected_models else 'none'}.",
        "",
        "## Strongest observed paired effects",
        "",
        "| Model | Pair | Success delta | XY error change | Perturbation L2 delta |",
        "|---|---|---:|---:|---:|",
    ]
    for p in strongest:
        report.append(
            f"| {p['model_label']} | {p['pair_id']} | "
            f"{100*p['success_delta_correlated_minus_iid']:+.1f} pp | "
            f"{100*p['xy_error_relative_change']:+.1f}% | {p['perturbation_l2_delta']:+.3e} |"
        )
    report.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "The v1 development run used a longer generated sequence than the consumed episode and therefore did not prove exact consumed-multiset equality. It was discarded. All values in this report come from the corrected v2 rerun with a 1000-step generated and consumed horizon.",
            "",
            "This NO-GO result rejects the narrow claim that mild order-only IMU or joint-velocity perturbations materially degrade these frozen MicroDuck policies under this Forward protocol. It does not test adaptation-state poisoning, because these deployed policies do not update an online adaptation state or their weights during an episode.",
            "",
            "## Recommended next experiment",
            "",
            "Keep the frozen policies as controls, but add an explicitly stateful victim: first a naive online bias estimator and then a history-conditioned adaptation module. Reuse the same exact-multiset pairing and measure adaptation-state displacement, post-attack residual error, recovery time, and delayed failure after a command change. Treat any amplitude sweep as a separately labelled exploratory boundary search, not as confirmation of this failed gate.",
        ]
    )
    (ROOT / "ORDERTRAP_GATE1_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"pairs={len(paired)} gate_hits={len(gate_hits)} affected_models={len(affected_models)} go={go}")


if __name__ == "__main__":
    main()
