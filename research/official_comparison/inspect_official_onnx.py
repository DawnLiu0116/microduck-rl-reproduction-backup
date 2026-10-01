"""Validate and describe the official alpha_walking ONNX graph."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort


ROOT = Path(os.environ.get("MICRODUCK_OFFICIAL_ROOT", Path(__file__).resolve().parent))
PATH = ROOT / "alpha_walking_official.onnx"


def shape(value_info) -> list[int | str]:
    result = []
    for dim in value_info.type.tensor_type.shape.dim:
        result.append(dim.dim_value if dim.dim_value else dim.dim_param)
    return result


def main() -> None:
    raw = PATH.read_bytes()
    model = onnx.load(PATH)
    onnx.checker.check_model(model)
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(PATH), sess_options=options, providers=["CPUExecutionProvider"])
    input_meta = session.get_inputs()[0]
    output_meta = session.get_outputs()[0]
    smoke = session.run(
        [output_meta.name],
        {input_meta.name: np.zeros(tuple(input_meta.shape), dtype=np.float32)},
    )[0]
    payload = {
        "path": str(PATH),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "onnx_checker_passed": True,
        "input": {"name": input_meta.name, "shape": input_meta.shape, "type": input_meta.type},
        "output": {"name": output_meta.name, "shape": output_meta.shape, "type": output_meta.type},
        "cpu_smoke_finite": bool(np.isfinite(smoke).all()),
        "node_types": [node.op_type for node in model.graph.node],
        "nodes": [
            {"name": node.name, "op_type": node.op_type, "inputs": list(node.input), "outputs": list(node.output)}
            for node in model.graph.node
        ],
        "initializers": [
            {"name": item.name, "dims": list(item.dims), "data_type": item.data_type}
            for item in model.graph.initializer
        ],
        "metadata": {item.key: item.value for item in model.metadata_props},
    }
    output = ROOT / "official_onnx_inspection.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
