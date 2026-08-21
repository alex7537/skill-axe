# A2D grasp evaluation methodology

## Evaluation questions

Answer separately:

1. Did the policy predict and execute a plausible grasp trajectory?
2. Which subsystem first prevented success: infrastructure, arm, hand command, hand tracking, contact, lift, or retention?
3. Is the comparison controlled enough to attribute the difference to the model or tested variable?

A final object-height value cannot answer all three.

## Diagnostic funnel

| Stage | Evidence | Interpretation when it first fails |
|---|---|---|
| Infrastructure | reset, observation, action, contact, and GT RPCs succeed | evaluator/server/runtime invalidity |
| Arm arrival | actual 7D pose reaches frozen pre-lift reference | approach or arm policy/execution |
| Hand command | commanded 6D hand target reaches frozen shape | policy hand output |
| Hand actual | measured 6D hand pose reaches frozen shape | actuation or physical response |
| Tracking | command-to-actual error at frozen lags | latency, drive strength, or contact load |
| Contact | target object has the required multi-finger contacts | closure, geometry, or alignment |
| Lift | contact and relative lift hold simultaneously | stability or lift trajectory |
| Retention | final contact/lift and maximum streak | sustained holding versus later drop |

Nearest-reference matching is diagnostic. When the reference comes from another object, seed, or episode, do not present the paired hand target as object-specific ground truth.

## Controlled comparisons

- For a model comparison, keep horizon, seeds, scene, action rate, maximum actions, sampling, and success profile fixed.
- For a horizon comparison, keep the exact bundle fixed.
- Use the same ordered seeds and alternate configurations to reduce time/order bias.
- Compare incomplete runs at equal matched counts; always show numerator and denominator.
- Treat early episodes as smoke checks for loading, schema, execution, populated metrics, and physical plausibility.
- Do not rank checkpoints until the frozen coverage and invalidity rules qualify the run.

## Execution-chain lessons

- Replay recorded target actions first when joint mapping or command execution is uncertain. Success supports the execution chain but does not validate inference inputs or policy reproduction.
- Compare policy outputs offline with dataset actions when separating prediction from execution. Verify preprocessing, observation timestamps, action frames, normalization, temporal offsets, and chunk semantics.
- Preserve zero-valued observations until their schema meaning is known; zero can be real state, padding, missing data, or an error.
- Evaluate the executed prefix separately from the unexecuted chunk tail.
- Record command and measured hand pose separately and compute lagged tracking errors.
- Separate arm arrival from hand closure before interpreting contact or lift.

## Runtime integrity

Preflight:

1. Resolve each bundle to exactly one file and record its hash and role.
2. Record evaluator revision/hash and exact arguments.
3. Confirm server readiness and required RPCs.
4. Confirm object identity, initial pose, visibility, and reset stability.
5. Inspect host-visible evaluators and established sockets for the target endpoint.
6. Confirm a versioned output namespace and compatible resume schema.

During execution:

- Use append-only per-episode records as the resume source.
- Record seed, configuration, executed steps, wall time, error type/message, funnel fields, contact fields, lift fields, and success profile.
- Verify matched configurations advance approximately evenly under alternation.
- Verify exactly one evaluator client controls a single-environment server.
- Quarantine every record produced during concurrent-control contamination.

Do not stop prior processes without explicit confirmation after resolving their exact identities. Do not stop the simulator/server when only an evaluator must be replaced.

## Success profile contract

Each profile must version:

```text
target-object identity
contact bodies/fingers and Boolean rule
force floor and units
height reference and coordinate frame
lift thresholds
sampling point and persistence length
final-retention rule
step/time limit
infrastructure-invalid policy
```

The historical `target-contact-lift-5f-v1` profile uses thumb plus two non-thumb contacts, 5 cm and 10 cm relative-lift tiers, and five consecutive sampled frames. Its original machine paths and checkpoint hashes are intentionally not retained here; rediscover current artifacts and freeze a new run manifest.

## Reporting contract

Minimum progress report:

| Configuration | Completed/requested | 5 cm sustained | 10 cm sustained | Valid contact | Errors |
|---|---:|---:|---:|---:|---:|

Diagnostic reports also include:

- funnel pass/fail counts and earliest-failure distribution;
- maximum/final lift and streak distributions;
- requested versus achieved cadence;
- bundle/evaluator hashes, scene/server identity, seeds, order, criterion version, and result schema;
- process state: active, stopped, complete, stale, crashed, or contaminated.

Lead with the earliest stage that materially separates configurations. Discuss lift only after confirming target-object contact and height signals are simultaneous and correctly identified.
