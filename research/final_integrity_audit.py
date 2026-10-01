"""Validate the final evaluation files and all nine matched comparison videos."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import imageio.v3 as iio


ROOT = Path(__file__).resolve().parent
SCENARIOS = {"Nominal", "Train-like", "Stress", "Forward", "Turning", "Standing"}
MODELS = {"seed42_iter3999", "seed123_iter3999", "official_alpha_walking"}
VIDEO_MODELS = {"seed42", "seed123", "official"}
VIDEO_SCENARIOS = {"forward", "turning", "stress"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    seed4004_path = ROOT / "independent_seed4004" / "seed4004_results.json"
    seed4004 = json.loads(seed4004_path.read_text(encoding="utf-8"))
    rows = seed4004["results"]
    keys = {(r["model_label"], r["scenario"], int(r["seed"])) for r in rows}
    expected_keys = {(m, s, 4004) for m in MODELS for s in SCENARIOS}
    evaluation_ok = (
        seed4004.get("complete") is True
        and len(rows) == 18
        and keys == expected_keys
        and all(int(r["episodes"]) == 128 for r in rows)
        and all(float(r["nan_state_rate"]) == 0.0 for r in rows)
        and all(float(r["out_of_terrain_rate"]) == 0.0 for r in rows)
    )

    video_rows = []
    expected_videos = {
        f"microduck_{m}_{s}-step-0.mp4" for m in VIDEO_MODELS for s in VIDEO_SCENARIOS
    }
    for name in sorted(expected_videos):
        path = ROOT / "comparison_videos" / name
        count = 0
        shape = None
        for frame in iio.imiter(path, plugin="FFMPEG"):
            if shape is None:
                shape = tuple(frame.shape)
            count += 1
        row = {
            "file": name,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "frames": count,
            "width": shape[1] if shape else None,
            "height": shape[0] if shape else None,
            "decode_ok": count == 500 and shape is not None and shape[:2] == (480, 640),
        }
        video_rows.append(row)
    videos_ok = len(video_rows) == 9 and all(r["decode_ok"] for r in video_rows)

    artifact_paths = [
        ROOT / "microduck_velocity_flat_seed42_iter3999.onnx",
        ROOT / "microduck_velocity_flat_seed123_iter3999.onnx",
        ROOT / "official_comparison" / "alpha_walking_official.onnx",
        ROOT / "unified_evaluation" / "multi_seed" / "multi_seed_evaluation.json",
        ROOT / "official_comparison" / "official_multi_seed_evaluation.json",
        seed4004_path,
    ]
    artifacts = [
        {"file": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in artifact_paths
    ]
    result = {
        "evaluation_seed4004_ok": evaluation_ok,
        "video_set_ok": videos_ok,
        "overall_ok": evaluation_ok and videos_ok,
        "seed4004_result_count": len(rows),
        "videos": video_rows,
        "artifacts": artifacts,
    }
    (ROOT / "FINAL_INTEGRITY_AUDIT.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    lines = [f"{item['sha256']}  {item['file']}" for item in artifacts]
    lines.extend(f"{item['sha256']}  comparison_videos/{item['file']}" for item in video_rows)
    (ROOT / "SHA256SUMS_FINAL.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["overall_ok"]:
        raise RuntimeError("Final integrity audit failed")


if __name__ == "__main__":
    main()
