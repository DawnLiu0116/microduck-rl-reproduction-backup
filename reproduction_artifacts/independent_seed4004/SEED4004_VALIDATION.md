# Independent seed 4004 validation

This is a fresh-process check and is not merged into the frozen three-seed primary table.
Each entry contains 128 episodes under the same scenario definition.

| Scenario | Model | Seed 4004 | Prior 3-seed aggregate | Delta (pp) |
|---|---|---:|---:|---:|
| Nominal | official_alpha_walking | 100.00% | 100.00% | +0.00 |
| Nominal | seed42_iter3999 | 100.00% | 100.00% | +0.00 |
| Nominal | seed123_iter3999 | 100.00% | 100.00% | +0.00 |
| Train-like | official_alpha_walking | 98.44% | 92.97% | +5.47 |
| Train-like | seed42_iter3999 | 95.31% | 95.05% | +0.26 |
| Train-like | seed123_iter3999 | 93.75% | 97.14% | -3.39 |
| Stress | official_alpha_walking | 76.56% | 76.30% | +0.26 |
| Stress | seed42_iter3999 | 74.22% | 74.74% | -0.52 |
| Stress | seed123_iter3999 | 73.44% | 71.88% | +1.56 |
| Forward | official_alpha_walking | 100.00% | 100.00% | +0.00 |
| Forward | seed42_iter3999 | 100.00% | 100.00% | +0.00 |
| Forward | seed123_iter3999 | 100.00% | 100.00% | +0.00 |
| Turning | official_alpha_walking | 100.00% | 100.00% | +0.00 |
| Turning | seed42_iter3999 | 100.00% | 100.00% | +0.00 |
| Turning | seed123_iter3999 | 100.00% | 100.00% | +0.00 |
| Standing | official_alpha_walking | 100.00% | 100.00% | +0.00 |
| Standing | seed42_iter3999 | 100.00% | 100.00% | +0.00 |
| Standing | seed123_iter3999 | 100.00% | 100.00% | +0.00 |

Interpretation rule: this extra seed checks whether the broad ordering is reproducible; it does not replace confidence intervals or make a four-seed table retroactively primary.
