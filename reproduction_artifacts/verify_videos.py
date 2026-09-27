"""Validate milestone MP4s and build a mid-frame contact sheet."""

from __future__ import annotations

import json
from pathlib import Path

import imageio.v3 as iio
from PIL import Image, ImageDraw


ROOT = Path("/mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction")
VIDEO_DIR = ROOT / "videos"
ITERATIONS = (0, 500, 1000, 2000, 3000, 3999)
EXPECTED_FRAMES = 500
EXPECTED_SIZE = (640, 480)


def main() -> None:
    results = []
    thumbnails = []
    for iteration in ITERATIONS:
        path = VIDEO_DIR / f"microduck_iter_{iteration:04d}-step-0.mp4"
        if not path.is_file() or path.stat().st_size <= 0:
            raise RuntimeError(f"Missing or empty video: {path}")

        count = 0
        first_shape = None
        middle = None
        for frame in iio.imiter(path, plugin="FFMPEG"):
            if first_shape is None:
                first_shape = tuple(frame.shape)
            if count == EXPECTED_FRAMES // 2:
                middle = frame.copy()
            count += 1

        if count != EXPECTED_FRAMES:
            raise RuntimeError(f"{path.name}: expected {EXPECTED_FRAMES} frames, got {count}")
        if first_shape is None or (first_shape[1], first_shape[0]) != EXPECTED_SIZE:
            raise RuntimeError(f"{path.name}: unexpected frame shape {first_shape}")
        if middle is None:
            raise RuntimeError(f"{path.name}: no middle frame")

        image = Image.fromarray(middle).resize((320, 240))
        thumbnails.append((iteration, image))
        results.append(
            {
                "iteration": iteration,
                "file": path.name,
                "bytes": path.stat().st_size,
                "frames": count,
                "width": first_shape[1],
                "height": first_shape[0],
                "expected_fps": 50,
                "expected_duration_seconds": 10.0,
                "decode_ok": True,
            }
        )

    sheet = Image.new("RGB", (960, 540), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (iteration, image) in enumerate(thumbnails):
        col = index % 3
        row = index // 3
        x = col * 320
        y = row * 270
        sheet.paste(image, (x, y + 30))
        draw.text((x + 10, y + 8), f"checkpoint iteration {iteration}", fill="black")

    sheet_path = ROOT / "plots" / "milestone_video_contact_sheet.png"
    sheet.save(sheet_path)
    (ROOT / "video_validation.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    print(json.dumps(results, indent=2))
    print(f"CONTACT_SHEET={sheet_path}")


if __name__ == "__main__":
    main()
