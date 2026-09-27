# Additional independent validation and visual-review package

## Scope

This work adds a fresh evaluation seed, official-policy videos, a blinded review set,
and a final integrity audit. Existing primary results were not overwritten.

## Fresh evaluation seed 4004

All three policies were evaluated in a new process on all six frozen scenarios, with
128 episodes per policy/scenario (18 jobs, 2304 episodes total).

| Scenario | Official | Seed 42 | Seed 123 |
|---|---:|---:|---:|
| Nominal | 100.00% | 100.00% | 100.00% |
| Train-like | **98.44%** | 95.31% | 93.75% |
| Stress | **76.56%** | 74.22% | 73.44% |
| Forward | 100.00% | 100.00% | 100.00% |
| Turning | 100.00% | 100.00% | 100.00% |
| Standing | 100.00% | 100.00% | 100.00% |

The extra seed supports the earlier Stress ordering: official first, seed 42 second,
seed 123 third. It does **not** reproduce the earlier Train-like ordering: the official
policy is first on seed 4004. Therefore Train-like differences are seed-sensitive and
must not be presented as a stable superiority claim.

The command-tracking conclusion does reproduce cleanly. On Turning, mean yaw error was:

- Official: `0.5800 rad/s`
- Seed 42: `0.5219 rad/s`
- Seed 123: `0.1974 rad/s`

Thus seed 123 remains much better at executing the fixed yaw command, even though all
three policies have 100% survival success. All 18 new jobs have zero NaN-state and
zero out-of-terrain rates.

## Matched official videos

Official Forward, Turning, and Stress videos were recorded with the same evaluation
seed (`1001`), camera, `640x480` resolution, 500 frames, and scenario configuration
as the two reproduced models. The final set contains nine videos.

Every video was fully decoded and verified to contain exactly 500 frames at 640x480.
The unusually small official and seed-42 Turning files are valid videos; their low
motion is consistent with the measured poor yaw tracking and should be judged in the
blinded review.

## Blinded human review

The `blind_review` directory contains videos A-I, a blank scoring sheet, and a separate
answer key. Do not open the answer key before finishing the scores. Score task completion
separately from stability so that “did not fall” cannot be mistaken for “followed the command.”

## Integrity audit

`FINAL_INTEGRITY_AUDIT.json` reports:

- seed-4004 evaluation set complete: yes;
- 18 unique policy/scenario records: yes;
- nine matched videos fully decodable: yes;
- all expected videos 500 frames at 640x480: yes;
- overall audit: pass.

`SHA256SUMS_FINAL.txt` records hashes for the three ONNX policies, primary evaluation
JSON files, seed-4004 results, and all nine videos.

## Evidence boundary

The frozen three-seed table remains the primary result. Seed 4004 is an independent
consistency check and was deliberately not merged after seeing its outcome. Physical
robot performance remains untested, and the human visual scores are still pending.
