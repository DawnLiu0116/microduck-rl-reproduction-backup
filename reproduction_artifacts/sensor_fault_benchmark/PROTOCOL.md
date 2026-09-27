# MicroDuck sensor-fault sensitivity scan v0.1

This screening protocol modifies only the first 34 dimensions of the 61-D actor
observation. Action history `[34:48]`, velocity command `[48:51]`, head command
`[51:55]`, and body command `[55:61]` are asserted unchanged at every policy step.

All jobs use the fixed Forward command `(0.3, 0.0, 0.0)`, no external push,
evaluation seed 5005, and 64 parallel episodes.

## Faults

- Gaussian noise: base angular velocity, projected gravity, joint position, and
  joint velocity receive channel-appropriate zero-mean noise at three scales.
- IMU bias: constant offsets are applied to base angular velocity and projected
  gravity at scales 1, 3, and 8.
- Delay: all sensor fields `[0:34]` are delayed by 1, 3, or 5 policy steps
  (20, 60, or 100 ms at 50 Hz).
- Freeze: every 180 policy steps, all sensor fields are held for 5, 15, or 30
  steps (100, 300, or 600 ms).
- Spike: every 200 steps, a five-step structured pulse is added to IMU and joint
  velocity channels at 0.25, 0.5, or 1.0 scale. The full-scale pulse is
  deliberately severe and is a stress condition, not a realistic sensor-noise
  claim.

## Metrics

Survival success, falls, episode duration, return, XY/yaw tracking error, action
delta, action-jump rate, maximum action magnitude, maximum physical tilt, input
perturbation magnitude, NaN-state rate, and terrain-boundary rate are recorded.

This is a screening experiment. Conditions showing a meaningful degradation will
later be repeated with at least three evaluation seeds and 128 episodes per seed.
