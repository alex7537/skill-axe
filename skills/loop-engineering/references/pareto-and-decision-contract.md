# Pareto and experiment-decision contract

## Minimal scorecard

Freeze one row per candidate before comparing it:

| Field | Meaning |
|---|---|
| Candidate ID | Immutable configuration or experiment identity |
| Hypothesis | What causal claim the test probes |
| Fixed contract | Code, data/split, evaluator, seeds, and comparison policy |
| Primary KPI | Main outcome to maximize or minimize |
| Guardrails | Safety, validity, generalization, or reliability thresholds |
| Resource vector | Tokens, GPU-hours, money, wall time, and human interventions |
| Validity | Qualified, partial, invalid, or diagnostic-only |
| Evidence | Metric manifest, logs, hashes, and artifacts |
| Decision | Frontier, dominated, retry-eval, new-cycle, promote, stop |

Do not compare candidates with incompatible data splits, evaluation criteria, checkpoint selection rules, or incomplete coverage as though they were scientific alternatives.

## Dominance

For objectives such as maximize success and minimize cost:

```text
A dominates B when:
  success(A) >= success(B)
  cost(A)    <= cost(B)
  latency(A) <= latency(B)
  ... and all guardrails pass for A

and at least one inequality is strict.
```

A candidate that fails a frozen guardrail is not a Pareto solution; classify it separately even if it has an attractive primary KPI.

## Choosing the next experiment

Prefer candidates that are expected to yield high information per unit of scarce resource:

1. resolve an uncertainty that can invalidate many downstream trials;
2. test one controllable factor near the current frontier;
3. use a cheap smoke or diagnostic before a full training/evaluation run;
4. make the outcome decisive: state what would cause promotion, rejection, or a return to an earlier phase.

Avoid broad hyperparameter sweeps by default. Use one only when the search range, comparable budget, parallelism limit, selection rule, and total cost are frozen.

## Robot-policy example

Objective: retain baseline grasp success while reducing inference cost.

```text
Fixed: checkpoint, simulator build, layouts, seeds, execute horizon,
       success profile, preprocessing, control frequency.
Variable: inference steps and timestep schedule only.
Guardrails: valid episode coverage; retention >= baseline - 1 percentage point.
Objectives: maximize retention; minimize median inference latency and GPU cost.
Stop: all allowed schedules tested, two equivalent infrastructure failures,
      or the allocated GPU-hour cap is reached.
```

This produces a frontier such as: highest retention, lowest-latency qualifying candidate, and lowest-cost qualifying candidate. A human chooses among those only when the product/research priority is not already frozen.
