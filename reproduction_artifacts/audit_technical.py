"""Read-only integrity audit for MicroDuck milestone checkpoints and ONNX."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import torch


ROOT = Path("/mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction")
ITERATIONS = (0, 500, 1000, 2000, 3000, 3999)


def visit_tensors(value, prefix=""):
    if torch.is_tensor(value):
        yield prefix, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from visit_tensors(item, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            yield from visit_tensors(item, f"{prefix}[{index}]")


def main() -> None:
    checkpoint_results = []
    for iteration in ITERATIONS:
        path = ROOT / "checkpoints" / f"model_{iteration}.pt"
        payload = torch.load(path, map_location="cpu", weights_only=False)
        tensors = list(visit_tensors(payload))
        floating = [(name, tensor) for name, tensor in tensors if tensor.is_floating_point()]
        nonfinite = [name for name, tensor in floating if not torch.isfinite(tensor).all()]
        checkpoint_results.append(
            {
                "iteration": iteration,
                "stored_iteration": payload.get("iter") if isinstance(payload, dict) else None,
                "bytes": path.stat().st_size,
                "top_level_keys": sorted(payload.keys()) if isinstance(payload, dict) else [],
                "tensor_count": len(tensors),
                "floating_tensor_count": len(floating),
                "nonfinite_tensor_count": len(nonfinite),
                "all_floating_tensors_finite": not nonfinite,
            }
        )

    onnx_path = ROOT / "microduck_velocity_flat_seed42_iter3999.onnx"
    model = onnx.load(onnx_path)
    onnx.checker.check_model(model)
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    input_meta = session.get_inputs()[0]
    output_meta = session.get_outputs()[0]
    rng = np.random.default_rng(20260922)
    samples = np.vstack(
        [np.zeros((1, 61), dtype=np.float32), rng.standard_normal((32, 61)).astype(np.float32)]
    )
    output = np.concatenate(
        [session.run([output_meta.name], {input_meta.name: sample[None, :]})[0] for sample in samples],
        axis=0,
    )
    result = {
        "checkpoints": checkpoint_results,
        "onnx": {
            "checker_passed": True,
            "providers": session.get_providers(),
            "input_name": input_meta.name,
            "input_shape": input_meta.shape,
            "input_type": input_meta.type,
            "output_name": output_meta.name,
            "output_shape": output_meta.shape,
            "output_type": output_meta.type,
            "test_batch_shape": list(samples.shape),
            "result_shape": list(output.shape),
            "all_outputs_finite": bool(np.isfinite(output).all()),
            "output_min": float(output.min()),
            "output_max": float(output.max()),
        },
    }
    out_path = ROOT / "technical_audit.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
