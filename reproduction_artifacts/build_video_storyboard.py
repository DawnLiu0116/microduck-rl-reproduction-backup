"""Build a temporal storyboard for qualitative milestone-video review."""

from pathlib import Path

import imageio.v3 as iio
from PIL import Image, ImageDraw


ROOT = Path("/mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction")
ITERATIONS = (0, 500, 1000, 2000, 3000, 3999)
FRAME_IDS = (0, 100, 200, 300, 400)
CELL = (256, 192)
LABEL_H = 28


def main() -> None:
    sheet = Image.new("RGB", (CELL[0] * len(FRAME_IDS), (CELL[1] + LABEL_H) * len(ITERATIONS)), "white")
    draw = ImageDraw.Draw(sheet)
    for row, iteration in enumerate(ITERATIONS):
        path = ROOT / "videos" / f"microduck_iter_{iteration:04d}-step-0.mp4"
        frames = {index: iio.imread(path, index=index, plugin="FFMPEG") for index in FRAME_IDS}
        y = row * (CELL[1] + LABEL_H)
        for col, frame_id in enumerate(FRAME_IDS):
            x = col * CELL[0]
            image = Image.fromarray(frames[frame_id]).resize(CELL)
            sheet.paste(image, (x, y + LABEL_H))
            draw.text((x + 6, y + 7), f"iter {iteration}, t={frame_id / 50:.0f}s", fill="black")
    output = ROOT / "plots" / "milestone_video_storyboard.png"
    sheet.save(output)
    print(output)


if __name__ == "__main__":
    main()
