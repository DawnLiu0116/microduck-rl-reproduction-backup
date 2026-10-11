# MicroDuck safety experiment code

This directory is the public-code subset of the local MicroDuck reproduction and safety study. It contains reusable simulation scripts, frozen protocols, and environment metadata. Raw episode data, model binaries, videos, progress ledgers, and unpublished research reports remain local and are intentionally not published here.

## Scope

- official/local-policy comparison and ONNX validation;
- fixed-command task evaluation;
- sensor delay, freeze, spike, and noise evaluation;
- adaptive-defense pilot analysis;
- temporal-order (OrderTrap) Gate-1 evaluation;
- matched video recording and command-sensitivity diagnostics.
- independent-seed confirmation and sensor pulse decomposition;
- full-width supervised actor order/common-clean-tail controls (not native PPO);
- checkpoint provenance, normalization, cloning and simulation signal checks.

See [SYNC_SCOPE.md](SYNC_SCOPE.md) for the synchronized subset, dependency requirements,
and the distinction between the local artifact backup and this public code release.

All work is simulation-only. No physical robot is controlled and no real-world exploitability claim is made.

## Environment

Use the official `microduck_rl` environment. Set paths when the repository and artifacts are not the current directory:

```bash
export MICRODUCK_REPO_ROOT=/path/to/microduck_rl
export MICRODUCK_ARTIFACT_ROOT=/path/to/artifacts
```

Historical run-directory names are retained for traceability. Model checkpoints and ONNX files are not included; supply locally owned artifacts at the documented paths.

## Protocols

- `task_protocol_v2/PROTOCOL.md`
- `sensor_fault_benchmark/PROTOCOL.md`
- `sensor_fault_benchmark/CONFIRMATORY_PROTOCOL.md`
- `unified_evaluation/UNIFIED_EVAL_PROTOCOL.md`

`CODE_FILE_MANIFEST.csv` records the relative path, byte count, and SHA-256 of every published file except the manifest itself.
