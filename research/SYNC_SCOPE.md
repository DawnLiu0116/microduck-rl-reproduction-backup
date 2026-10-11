# Backup synchronization scope

This code-only release now includes independent sensor-fault confirmation,
pulse decomposition, full-width supervised actor order and common-clean-tail
controls, normalizer/provenance checks, and simulation signal/integrity utilities.

Supervised actor updates are not native PPO training. Observation fault tests
are not evidence of training poisoning, persistent backdoors, or physical exploitability.

`run_normalization_pilot.py` and `collect_long_teacher.py` are retained as
dependencies of the full-width pilot and its integrity utilities, not as extra
claims of successful methods. These scripts require local checkpoints, teacher
datasets, ledgers and environment dependencies; they are not a turnkey data release.
Some scripts retain experiment-specific paths. Review those before invoking.

No raw episode files, results, unpublished reports/dossiers, checkpoint/ONNX
binaries, videos, progress state or duplicate development outputs are added to
GitHub by this synchronization. Complete research artifacts are backed up locally
in a separate date-stamped snapshot with source/destination SHA-256 verification.

The synchronization copies files additively and preserves older backups.
`CODE_FILE_MANIFEST.csv` inventories this code release, excluding itself.
