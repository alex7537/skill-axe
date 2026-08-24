# Method Comparison Contract

Use this before claiming that one policy family is better than another.

## Match the experimental contract

Hold constant or report:

- dataset trajectories, success/failure composition, and train/eval split;
- observation encoder, image history, state/action semantics, horizon, and normalization;
- parameter count and pretrained initialization;
- optimizer steps, batch size, sampling candidates, and total training compute;
- inference hardware, batch, warmup, sampling/integration steps, and latency definition;
- seed count and uncertainty;
- rollout environment, initial-state distribution, task success criteria, and retry policy.

Do not compare a paper's best tuned number with a local baseline's first run.

## Separate the claims

| Claim | Minimum evidence |
|---|---|
| Mode coverage | Conditional distribution plots plus per-mode recall/frequency and rollout validity |
| Sample efficiency | Learning curve versus unique demonstrations under matched optimization |
| Inference speed | End-to-end latency and throughput on the same hardware, including encoders and sampling |
| Action accuracy | Per-block/timestep metrics plus rollout behavior |
| RL compatibility | Correct log-probability/gradient path or a verified alternative objective |
| World-model usefulness | Action intervention, future-prediction quality, and downstream control/planning gain |
| Value/reward quality | Success/failure ranking, temporal consistency, reversal tests, and calibration |
| Recovery robustness | Failure injection, recovery rate, correction rate, retries, and final task success |

## Paper-note numbers

The Feishu record includes illustrative success-rate and frequency claims for IMLE, Diffusion, and Flow Matching. Preserve their source as `Feishu paper note` until the original table establishes:

- exact task and demonstration count;
- evaluation episode count;
- seed/error bars;
- network and candidate-sampling budget;
- latency measurement boundary;
- whether success is task completion, coverage, or trajectory validity.

## Implementation equivalence

Before naming a local method after a paper, verify:

1. objective equation and sign;
2. candidate sampling and nearest-neighbor direction;
3. conditioning and target variables;
4. detach/gradient ownership;
5. training versus inference procedure;
6. hyperparameters that change the method rather than only tuning it;
7. official invariants covered by tests.

Generated or simplified pseudo-code is useful for teaching, not proof of equivalence.

## Decision output

A valid comparison ends with one of:

- evidence favors method A under the frozen contract;
- methods trade quality, coverage, latency, or compute differently;
- result is inconclusive because coverage, uncertainty, or protocol differs;
- the local implementation is not yet faithful enough to compare.

