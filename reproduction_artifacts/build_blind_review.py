"""Build a deterministic, model-blinded review set from nine comparison videos."""

from __future__ import annotations

import csv
import hashlib
import random
import shutil
from pathlib import Path


BASE = Path(__file__).resolve().parent
SOURCE = BASE / "comparison_videos"
OUT = BASE / "blind_review"
VIDEO_OUT = OUT / "videos"
MODELS = ("official", "seed42", "seed123")
SCENARIOS = ("forward", "turning", "stress")
RANDOMIZATION_SEED = 20260927


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    pairs = [(m, s) for m in MODELS for s in SCENARIOS]
    random.Random(RANDOMIZATION_SEED).shuffle(pairs)
    VIDEO_OUT.mkdir(parents=True, exist_ok=True)
    key_rows = []
    score_rows = []
    for index, (model, scenario) in enumerate(pairs):
        code = chr(ord("A") + index)
        source = SOURCE / f"microduck_{model}_{scenario}-step-0.mp4"
        if not source.is_file() or source.stat().st_size == 0:
            raise FileNotFoundError(source)
        target = VIDEO_OUT / f"{code}.mp4"
        shutil.copy2(source, target)
        key_rows.append({
            "code": code,
            "model": model,
            "scenario": scenario,
            "source_file": source.name,
            "sha256": sha256(target),
            "bytes": target.stat().st_size,
        })
        score_rows.append({
            "code": code,
            "scenario": scenario,
            "task_completion_1_to_5": "",
            "stability_1_to_5": "",
            "motion_naturalness_1_to_5": "",
            "recovery_1_to_5": "" if scenario == "stress" else "N/A",
            "visible_failure_or_anomaly": "",
            "notes": "",
        })

    with (OUT / "answer_key.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(key_rows[0]))
        writer.writeheader()
        writer.writerows(key_rows)
    with (OUT / "scoring_sheet.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(score_rows[0]))
        writer.writeheader()
        writer.writerows(score_rows)
    (OUT / "README.md").write_text(
        "# MicroDuck anonymous video review\n\n"
        "1. Do not open `answer_key.csv` before scoring.\n"
        "2. Watch A-I in order, preferably twice.\n"
        "3. Fill `scoring_sheet.csv`; 1 is worst and 5 is best.\n"
        "4. Judge task completion separately from merely staying upright.\n"
        "5. Open the answer key only after all scores are saved.\n\n"
        f"Randomization seed: `{RANDOMIZATION_SEED}`.\n",
        encoding="utf-8",
    )
    print(OUT)


if __name__ == "__main__":
    main()
