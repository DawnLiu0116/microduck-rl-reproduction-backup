"""Merge the preserved confirmation with the seed-2026 protocol extension."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import analyze_confirmatory_faults as analysis


ROOT = Path(__file__).resolve().parent
OLD = ROOT / "confirmatory_faults.json"
EXT = ROOT / "seed2026_extension/confirmatory_faults_seed2026.json"
OUT = ROOT / "four_model_confirmatory"
MERGED = OUT / "confirmatory_faults_four_models.json"
MODEL = "seed2026_iter3999"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    old = json.loads(OLD.read_text(encoding="utf-8"))
    ext = json.loads(EXT.read_text(encoding="utf-8"))
    if not old.get("complete") or len(old["results"]) != 54:
        raise RuntimeError("Original three-model confirmation is incomplete")
    if not ext.get("complete") or len(ext["results"]) != 18:
        raise RuntimeError("Seed-2026 extension is incomplete")
    rows = old["results"] + ext["results"]
    models = ["official_alpha_walking", "seed42_iter3999", "seed123_iter3999", MODEL]
    expected = {
        (model, fault, seed)
        for model in models
        for fault in analysis.FAULTS
        for seed in analysis.SEEDS
    }
    keys = {(row["model_label"], row["fault_name"], int(row["seed"])) for row in rows}
    if keys != expected or len(rows) != 72:
        raise RuntimeError(f"Four-model key mismatch: expected 72, found {len(rows)} rows/{len(keys)} keys")
    for row in rows:
        if int(row["episodes"]) != 128:
            raise RuntimeError("Unexpected episode count")
        if float(row["nan_state_rate"]) != 0.0 or float(row["out_of_terrain_rate"]) != 0.0:
            raise RuntimeError(f"Invalid termination evidence in {row['model_label']}/{row['fault_name']}/{row['seed']}")

    OUT.mkdir(parents=True, exist_ok=True)
    payload = dict(old)
    payload.update({
        "protocol_version": "0.3-four-model-confirmatory",
        "complete": True,
        "models": models,
        "results": rows,
        "job_count": 72,
        "total_episodes": 72 * 128,
        "nan_job_count": 0,
        "out_of_terrain_job_count": 0,
    })
    MERGED.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    analysis.MODELS = models
    analysis.MODEL_NAMES[MODEL] = "Seed 2026"
    aggregated = analysis.aggregate(rows)
    analysis.write_jobs(rows, OUT / "confirmatory_jobs_four_models.csv")
    analysis.write_csv(aggregated, OUT / "confirmatory_aggregate_four_models.csv")
    analysis.plot_summary(aggregated, OUT / "confirmatory_summary_four_models.png", True)
    analysis.write_report(aggregated, OUT / "CONFIRMATORY_FAULT_REPORT_FOUR_MODELS.md", True)
    artifacts = [
        EXT,
        MERGED,
        OUT / "confirmatory_jobs_four_models.csv",
        OUT / "confirmatory_aggregate_four_models.csv",
        OUT / "confirmatory_summary_four_models.png",
        OUT / "CONFIRMATORY_FAULT_REPORT_FOUR_MODELS.md",
    ]
    manifest = {
        "complete": True,
        "job_count": 72,
        "total_episodes": 72 * 128,
        "unique_job_count": len(keys),
        "nan_job_count": 0,
        "out_of_terrain_job_count": 0,
        "artifacts": [
            {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in artifacts
        ],
    }
    (OUT / "four_model_fault_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "complete": True,
        "jobs": len(rows),
        "episodes": 72 * 128,
        "aggregate_rows": len(aggregated),
        "output": str(OUT),
    }, indent=2))


if __name__ == "__main__":
    main()
