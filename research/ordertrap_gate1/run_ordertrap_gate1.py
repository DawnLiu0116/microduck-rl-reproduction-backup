"""OrderTrap Gate-1 paired temporal-order screening for MicroDuck.

For every pair, IID and correlated schedules contain exactly the same scalar
perturbation multiset for each environment.  Only temporal order differs.
This is a simulation robustness screen, not evidence of a physical attack.
"""

from __future__ import annotations

import argparse
import json
import zlib
from pathlib import Path

import torch


BASE = Path(__file__).resolve().parent.parent
FAULT_DIR = BASE / "sensor_fault_benchmark"
ROOT = BASE / "ordertrap_gate1"
RESULT = ROOT / "ordertrap_gate1.json"

import sys

sys.path.insert(0, str(FAULT_DIR))
import run_sensor_fault_scan as scan  # noqa: E402


EPISODES = 64
SEED = 6006
# The fixed Forward protocol lasts exactly 20 s at 50 Hz.  Matching the
# schedule horizon to the consumed 1000 policy steps is required for the two
# orderings to expose the exact same multiset during evaluation.
HORIZON = 1000
PHI = 0.98


def make_faults() -> list[dict]:
    faults = []
    for channel in ("imu", "joint_velocity"):
        for scale in (1.0, 2.0):
            pair_id = f"{channel}_scale{scale:g}"
            for ordering in ("iid", "correlated"):
                faults.append(
                    {
                        "name": f"{pair_id}_{ordering}",
                        "type": "ordertrap",
                        "severity": "gate1-screening",
                        "pair_id": pair_id,
                        "channel": channel,
                        "scale": scale,
                        "ordering": ordering,
                        "horizon": HORIZON,
                        "phi": PHI,
                    }
                )
    return faults


FAULTS = make_faults()


class PairedTemporalInjector:
    """Inject paired equal-multiset schedules with different temporal order."""

    def __init__(self, spec: dict, seed: int, device: torch.device):
        self.spec = spec
        self.seed = int(seed)
        self.device = device
        self.step = 0
        self.schedule: torch.Tensor | None = None

    def _build_schedule(self, num_envs: int, dtype: torch.dtype) -> torch.Tensor:
        horizon = int(self.spec["horizon"])
        pair_offset = zlib.crc32(self.spec["pair_id"].encode("utf-8"))
        generator = torch.Generator(device="cpu")
        generator.manual_seed(self.seed + pair_offset)

        # Every environment receives the same symmetric multiset but an
        # independently generated order.  Endpoints are excluded to avoid
        # making the screen depend on one exact maximum-amplitude sample.
        base = torch.linspace(-1.0, 1.0, horizon + 2, dtype=torch.float64)[1:-1]
        schedules = []
        for _ in range(num_envs):
            if self.spec["ordering"] == "iid":
                order = torch.randperm(horizon, generator=generator)
                sequence = base[order]
            elif self.spec["ordering"] == "correlated":
                noise = torch.randn(horizon, generator=generator, dtype=torch.float64)
                latent = torch.empty(horizon, dtype=torch.float64)
                latent[0] = noise[0]
                phi = float(self.spec["phi"])
                innovation = (1.0 - phi * phi) ** 0.5
                for index in range(1, horizon):
                    latent[index] = phi * latent[index - 1] + innovation * noise[index]
                # Rank matching preserves the exact multiset while transferring
                # the AR(1) temporal dependence into the perturbation sequence.
                ranks = torch.argsort(torch.argsort(latent))
                sequence = base[ranks]
            else:
                raise ValueError(f"Unknown ordering: {self.spec['ordering']}")
            schedules.append(sequence)
        return torch.stack(schedules).to(device=self.device, dtype=dtype)

    def apply(self, observations):
        output = observations.clone()
        clean = observations["actor"]
        if clean.shape[-1] != 61:
            raise RuntimeError(f"Expected 61 actor observations, got {clean.shape}")
        if self.schedule is None:
            self.schedule = self._build_schedule(clean.shape[0], clean.dtype)

        actor = clean.clone()
        scalar = self.schedule[:, self.step % self.schedule.shape[1]]
        scale = float(self.spec["scale"])
        if self.spec["channel"] == "imu":
            gyro_pattern = actor.new_tensor([0.050, -0.040, 0.030]) * scale
            gravity_pattern = actor.new_tensor([0.005, -0.004, 0.000]) * scale
            actor[:, 0:3] += scalar[:, None] * gyro_pattern
            actor[:, 3:6] += scalar[:, None] * gravity_pattern
        elif self.spec["channel"] == "joint_velocity":
            pattern = actor.new_tensor(
                [1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1]
            )
            actor[:, 20:34] += scalar[:, None] * pattern * (0.10 * scale)
        else:
            raise ValueError(f"Unknown channel: {self.spec['channel']}")

        if not torch.equal(actor[:, scan.ACTION_HISTORY_SLICE], clean[:, scan.ACTION_HISTORY_SLICE]):
            raise RuntimeError("Injector modified action-history fields")
        if not torch.equal(actor[:, scan.COMMAND_AND_POSE_SLICE], clean[:, scan.COMMAND_AND_POSE_SLICE]):
            raise RuntimeError("Injector modified command/pose fields")

        output["actor"] = actor
        self.step += 1
        perturbation = torch.linalg.vector_norm(
            actor[:, scan.SENSOR_SLICE] - clean[:, scan.SENSOR_SLICE], dim=-1
        )
        return output, perturbation


def save(path: Path, rows: list[dict], complete: bool, args) -> None:
    payload = {
        "protocol_version": "ordertrap-gate1-v2-exact-consumed-multiset",
        "task": scan.TASK_ID,
        "scenario": scan.SCENARIO,
        "hypothesis": "Equal marginal perturbation multisets can have different closed-loop effects when temporally reordered.",
        "episodes_per_job": args.episodes,
        "seeds": [args.seed],
        "models": args.models,
        "faults": FAULTS,
        "complete": complete,
        "results": rows,
    }
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=EPISODES)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--models", nargs="+", choices=list(scan.MODELS), default=list(scan.MODELS))
    parser.add_argument("--output", type=Path, default=RESULT)
    args = parser.parse_args()

    ROOT.mkdir(parents=True, exist_ok=True)
    progress = args.output.with_name(args.output.stem + "_progress.json")
    rows: list[dict] = []
    if progress.is_file():
        previous = json.loads(progress.read_text(encoding="utf-8"))
        if int(previous["episodes_per_job"]) != args.episodes:
            raise RuntimeError("Existing progress uses a different episode count")
        rows = previous["results"]

    completed = {
        (row["model_label"], row["fault_name"], int(row["seed"])) for row in rows
    }
    total = len(args.models) * len(FAULTS)
    scan.FaultInjector = PairedTemporalInjector
    scan.configure_torch_backends()

    for model_label in args.models:
        for fault in FAULTS:
            key = (model_label, fault["name"], args.seed)
            if key in completed:
                continue
            print(f"START {model_label}/{fault['name']} ({len(rows)+1}/{total})", flush=True)
            row = scan.evaluate(model_label, fault, args.episodes, args.seed)
            rows.append(row)
            completed.add(key)
            save(progress, rows, False, args)
            print(
                f"DONE {model_label}/{fault['name']} success={row['success_count']}/{args.episodes} "
                f"xy={row['mean_xy_velocity_error_mps']:.5f} tilt={row['mean_max_tilt_deg']:.3f}",
                flush=True,
            )

    if len(rows) != total:
        raise RuntimeError(f"Expected {total} results, found {len(rows)}")
    save(args.output, rows, True, args)
    print(f"RESULT={args.output}", flush=True)


if __name__ == "__main__":
    main()
