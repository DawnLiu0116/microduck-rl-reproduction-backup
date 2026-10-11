# Zero-update original-PPO clone gate

This is an implementation baseline, not a poisoning experiment or a new defense.
Sources: seed 42 and 2026 final model_3999.pt. Never overwrite source checkpoints.
Clone the entire checkpoint byte-for-byte (actor, critic, optimizer, iteration,
environment metadata). Load both through the installed official runner. Also
serialize/reload a deep-copied full-width inference actor to test independent
module reconstruction rather than merely copying a file.

Predeclared checks:
- Original and copied checkpoint SHA256 equal before and after evaluation.
- Original, copied-checkpoint actor and serialized actor agree exactly on
  every live observation; finite 61-to-14 deterministic inference.
- Actor state, including normalizer buffers/count, unchanged throughout inference.
- Fixed Forward (vx=0.3) and Turning (yaw=0.5), evaluation seed 11011,
  64 first episodes per case, maximum 20 s. Two models x two tasks x two
  checkpoint variants = 512 episodes. No push or actor additive noise/IMU
  misalignment; native sensor/actuator delays retained. Head/body commands zero.
- Identical initial observations and compare full live observation/action/
  reward/done traces and first-episode rows between each original/clone pair.
  Report any simulator nondeterminism rather than changing tolerances post hoc.
  Bitwise trajectory identity is the strict gate for this bounded run.
- Survival means timeout without fall/NaN/terrain exit. It is not tracking success.
  Turning may fail for both identical policies: do not conflate existing skill
  limitations with a clone implementation bug. Save per-episode tracking errors.

No optimizer steps or normalizer updates. No ONNX re-export, retraining, hardware,
or modification of historical reports. Only after this gate passes should a
controlled training pilot begin; preserving capacity alone does not prove any
training-time poisoning mechanism.
