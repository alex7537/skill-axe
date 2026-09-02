# First milestone contract

## Done when

- A merchant-facing pool can be represented with multiple products, weights, tiers, and remaining quantities.
- A public endpoint exposes the frozen version and current active probabilities.
- A draw endpoint requires an idempotency key and a customer/order reference.
- The server selects exactly one in-stock item with secure randomness.
- Repeating the same request returns the same draw ID without another decrement.
- A second request fails after the last unit is consumed.
- The response contains a pool version, timestamp, and audit hash.
- A frontend waits for the response, then reveals that returned item.
- Product scope, diagrams, API, and production data contract are reviewable.
- Tests, type checking, build, dependency audit, and live API smoke checks pass.

## Recommended repository shape

Adapt names to the stack; preserve responsibilities.

```text
apps/
  api/          transport and demo/production repository adapters
  web/          reveal experience; no winner-selection logic
packages/
  core/         framework-independent pool and selection rules
docs/
  architecture.md
  product-scope.md
  openapi.yaml
  schema.sql or equivalent migration/model contract
  adr/
```

## Evidence to record

- exact test and build commands with exit status;
- contract-linter result;
- first draw status/result and repeated-request status/result;
- remaining inventory after the duplicate request;
- local and remote Git SHA when publishing was requested;
- whether interactive visual verification was actually performed.

## Production claims not earned by this milestone

- payment correctness;
- database isolation under concurrent workers;
- multi-tenant authorization;
- regulatory approval;
- three-year audit retention;
- fulfillment and refund correctness;
- cryptographically public proof of fairness.
