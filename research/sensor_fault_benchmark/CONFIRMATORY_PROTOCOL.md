# MicroDuck confirmatory sensor-fault protocol

## Purpose

Confirm the screening experiment's two strongest findings without changing the
policy, task, command, observation layout, or metric definitions:

1. locate the failure transition between 20 ms and 60 ms synchronous sensor delay;
2. refine the transition between 100 ms and 300 ms periodic sensor freeze;
3. test whether Seed 123's structured-spike weakness repeats across evaluation seeds.

## Fixed controls

- Task: `Mjlab-Velocity-Flat-MicroDuck`
- Scenario: Forward, fixed command `(0.3, 0.0, 0.0)`
- Models: official `alpha_walking.onnx`, local Seed 42 iteration 3999,
  local Seed 123 iteration 3999
- Evaluation seeds: 1001, 2002, 3003
- Episodes: 128 per model/fault/seed job
- External pushes: disabled
- Policy frequency: 50 Hz
- Sensor slice: actor observation `[0:34]`
- Action history `[34:48]` and command/pose `[48:61]`: unchanged and asserted

## Conditions

| Condition | Meaning |
|---|---|
| clean | no injected sensor fault |
| delay_2 | synchronous 2-policy-step delay, 40 ms |
| freeze_8 | freeze all sensor fields for 160 ms every 3.6 s |
| freeze_10 | freeze all sensor fields for 200 ms every 3.6 s |
| freeze_12 | freeze all sensor fields for 240 ms every 3.6 s |
| spike_100 | screening experiment's full structured pulse, 100 ms every 4 s |

This remains a simulation stress test. The injected magnitudes are not claims
about measured MicroDuck hardware sensor failure distributions.
