# MicroDuck task measurement protocol v2.1

This protocol fixes only the experimental conditions: commands, push schedule, evaluation seeds, episode count, deterministic inference, and metric definitions. It deliberately does **not** freeze binary task thresholds or produce task pass/fail labels.

All continuous metrics are retained per episode and reported as distributions. Survival is reported separately so that “did not fall” cannot be confused with task quality.

| Scenario | Command | Reported measurements |
|---|---|---|
| Forward | `[0.3, 0, 0]` | survival, absolute vx error, absolute vy, lateral displacement, planar displacement |
| Turning | `[0, 0, 0.6]` | survival, yaw error, planar speed, lateral displacement, planar displacement |
| Standing | `[0, 0, 0]` | survival, planar speed, absolute yaw speed, planar displacement |
| Stress-forward | `[0.3, 0, 0]`, pushes every 0.5-1.0 s | survival, XY velocity error, push count, recovered-push fraction, recovery time |

For descriptive recovery timing only, a push is marked recovered when XY velocity error remains <= 0.20 m/s for five consecutive 50 Hz control steps before the next push. This is an operational event definition, not a model success threshold.

Fall recovery remains excluded. Automatic simulator reset is not autonomous stand-up.
