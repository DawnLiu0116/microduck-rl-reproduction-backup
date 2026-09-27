"""Decode and validate the six matched final-policy comparison videos."""

from __future__ import annotations

import json
from pathlib import Path

import imageio.v3 as iio


ROOT = Path("/mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction")
VIDEO_DIR = ROOT / "comparison_videos"
OUTPUT = VIDEO_DIR / "validation.json"
EXPECTED = {
    f"microduck_{model}_{scenario}-step-0.mp4"
    for model in ("seed42", "seed123")
    for scenario in ("forward", "turning", "stress")
}


def main() -> None:
    found = {path.name for path in VIDEO_DIR.glob("*.mp4")}
    if found != EXPECTED:
        raise RuntimeError(f"Video set mismatch; missing={EXPECTED-found}, extra={found-EXPECTED}")
    rows = []
    for name in sorted(EXPECTED):
        path = VIDEO_DIR / name
        count = 0
        first_shape = None
        for frame in iio.imiter(path, plugin="FFMPEG"):
            if first_shape is None:
                first_shape = tuple(frame.shape)
            count += 1
        valid = count == 500 and first_shape is not None and first_shape[:2] == (480, 640)
        row = {
            "file": name,
            "bytes": path.stat().st_size,
            "frames": count,
            "width": first_shape[1] if first_shape else None,
            "height": first_shape[0] if first_shape else None,
            "duration_seconds_at_50fps": count / 50,
            "decode_ok": valid,
        }
        rows.append(row)
        print(json.dumps(row), flush=True)
        if not valid:
            raise RuntimeError(f"Invalid video: {row}")
    OUTPUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
