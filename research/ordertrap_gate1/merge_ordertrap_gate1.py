"""Merge isolated OrderTrap Gate-1 model outputs into the canonical result."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCES = [
    ROOT / "official_v2.json",
    ROOT / "seed42_v2.json",
    ROOT / "seed123_v2.json",
    ROOT / "seed2026_v2.json",
]
EXPECTED_MODELS = {
    "official_alpha_walking",
    "seed42_iter3999",
    "seed123_iter3999",
    "seed2026_iter3999",
}


def main() -> None:
    payloads = [json.loads(path.read_text(encoding="utf-8")) for path in SOURCES]
    rows = []
    for payload in payloads:
        if not payload.get("complete"):
            raise RuntimeError("A per-model source is incomplete")
        rows.extend(payload["results"])

    keys = [(r["model_label"], r["fault_name"], int(r["seed"])) for r in rows]
    if len(rows) != 32 or len(keys) != len(set(keys)):
        raise RuntimeError(f"Expected 32 unique rows, got rows={len(rows)} unique={len(set(keys))}")
    if {r["model_label"] for r in rows} != EXPECTED_MODELS:
        raise RuntimeError("Unexpected model set")
    if any(float(r["nan_state_rate"]) != 0.0 or float(r["out_of_terrain_rate"]) != 0.0 for r in rows):
        raise RuntimeError("Invalid termination evidence")

    merged = dict(payloads[0])
    merged["models"] = sorted(EXPECTED_MODELS)
    merged["complete"] = True
    merged["results"] = sorted(rows, key=lambda r: (r["model_label"], r["fault_name"]))
    target = ROOT / "ordertrap_gate1.json"
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    temp.replace(target)
    print(f"merged={target} rows={len(rows)} unique={len(set(keys))}")


if __name__ == "__main__":
    main()
