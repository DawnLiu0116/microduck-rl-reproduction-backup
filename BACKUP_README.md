# MicroDuck RL research repository

This repository tracks the official `pollen-robotics/microduck_rl` source base at commit `cb70b792312d559a4da09064d92009079671815f` together with a curated, simulation-only safety experiment code release.

## Current research release

Start at [`research/README.md`](research/README.md).

The current tree contains reusable experiment code, frozen protocols, environment metadata, and integrity utilities. Raw episode data, result reports, videos, model binaries, and unpublished research material remain local and are deliberately not published in this branch.

## Excluded from the current branch

- the retired `Walker2d-v5` project;
- model checkpoints, ONNX binaries, TensorBoard events, and videos;
- caches, progress files, previews, smoke tests, and withdrawn threshold trials;
- superseded random-command Stress results and OrderTrap v1 development outputs.
- raw evaluation data and unpublished research reports.

The original mixed backup remains recoverable at Git tag `legacy-backup-2026-09-27`. Removing it from the current tree does not erase it from repository history. Complete local artifacts remain outside this Git checkout.

## Evidence boundary

All reported experiments are from MuJoCo/MjLab simulation. No physical robot was controlled, and no real-world exploitability claim is made.
