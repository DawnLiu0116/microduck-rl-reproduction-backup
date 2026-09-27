# MicroDuck sensor-fault screening results

Screening design: Forward command, evaluation seed 5005, 64 episodes per model/fault, three policies and sixteen conditions (3072 episodes total).

This is a one-seed screening experiment. It identifies candidates for confirmatory three-seed evaluation but does not establish statistical superiority.

## Per-model worst observed conditions

| Model | Lowest survival | Largest XY error | Largest tilt | Largest action-jump rate |
|---|---|---|---|---|
| Official | delay_5 (0.0%) | delay_3 (0.372 m/s) | delay_5 (68.0 deg) | noise_severe (27.78%) |
| Seed 42 | delay_5 (0.0%) | delay_3 (0.390 m/s) | freeze_30 (68.3 deg) | delay_3 (27.70%) |
| Seed 123 | delay_5 (0.0%) | delay_3 (0.374 m/s) | freeze_30 (68.4 deg) | noise_severe (26.12%) |

## Interpretation rules

- Compare each fault with the clean row for the same model.
- A 100% survival rate does not imply successful command following; inspect XY error.
- A large action-jump or tilt increase without falls is still a safety degradation.
- Severe structured spikes are stress tests, not estimates of ordinary sensor noise.
- Only degraded and scientifically interesting conditions should advance to the 128-episode, three-evaluation-seed confirmatory stage.
