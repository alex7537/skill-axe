---
name: blindbox-service-scaffold
description: Design, scaffold, or review a merchant-configurable blind-box or random-product service with server-authoritative draws, inventory safety, idempotency, auditable rules, and reveal UI. Use when users ask to build 盲盒平台、随机商品服务、开箱 SaaS、gacha storefront, or turn a merchant catalog into a weighted product pool. Do not use for an ordinary store without randomness, a game-only gacha simulator, or a paid raffle where some buyers receive nothing.
---

# Blindbox Service Scaffold

Build the smallest credible vertical slice around one invariant: the server commits the item and inventory change before the client reveals it.

## Frame the commercial model

Confirm or infer whether every valid purchase receives a real item from a disclosed pool. Keep that must-win blind-box model as the default MVP. If participants can pay and receive nothing, stop treating it as the same product: surface the legal and platform-risk difference before designing or implementing it.

Separate four layers:

- merchant catalog and pool configuration;
- draw, inventory, idempotency, and audit;
- payment/order/fulfillment adapters;
- themeable reveal UI.

Read [references/architecture-invariants.md](references/architecture-invariants.md) before choosing the data model or draw transaction. Read [references/milestone-contract.md](references/milestone-contract.md) when creating a new repository or planning the first implementation milestone.

## Choose a bounded architecture

Prefer a headless blind-box domain service over rebuilding a full commerce platform. Reuse an appropriately licensed commerce foundation for catalog, payment, orders, and fulfillment; own pool versions, draw records, inventory allocations, audit evidence, and reveal contracts locally.

Treat public source without an explicit license as design reference only. Do not copy it into a commercial scaffold.

For a new repository:

- resolve the exact local and remote target first;
- create a remote only when the user explicitly requests it;
- when remote visibility is unspecified, use private and report that assumption;
- keep the first milestone runnable without real payment credentials;
- document production boundaries when the runnable adapter is intentionally in-memory.

Do not add blockchain, marketplace settlement, coupons, referrals, or elaborate theming unless they are acceptance criteria.

## Deliver the first vertical slice

Produce observable artifacts rather than architecture prose alone:

1. Product scope with explicit non-goals and the must-win versus raffle boundary.
2. Context and draw sequence diagrams.
3. Versioned pool, pool item, draw record, inventory movement, and outbox data contracts.
4. An API that requires an idempotency key and returns the committed result.
5. A framework-independent weighted-selection core using a cryptographically secure server RNG.
6. A reveal page that animates only after the API returns the result.
7. Tests for weight boundaries, exhausted inventory, invalid weights, and repeated requests.

Use an integer weight domain. Exclude zero-inventory items before calculating the active total. The browser may animate decoys, but it must never submit, choose, or override the awarded item ID.

## Verify

Run the project's tests, type checks, production builds, dependency audit, API contract validation, and a live duplicate-request smoke test. When browser control is available, exercise the full reveal flow and inspect responsive layout; otherwise report visual verification as unperformed instead of substituting unrelated automation.

Run the bundled structural guard after implementation:

```bash
python3 scripts/check_scaffold.py <project-root>
```

Treat a clean guard as supporting evidence, not proof of transactional correctness. A production claim additionally requires a real database transaction/concurrency test.

## Gotchas

- A polished wheel is not the source of truth; the backend result must predate the animation.
- In-memory mutation can validate domain flow but cannot prove multi-process inventory safety.
- Redis is useful for limits and caching, but not the final source of inventory or draw truth.
- A published pool must be immutable; create a new version instead of editing historical rules.
- Weight-based probability and inventory quantity are different concepts. State whether weights stay fixed until an item reaches zero or derive from remaining units.
- An OpenAPI document can compile while leaving authentication intent ambiguous; mark anonymous prototype operations explicitly and document production entitlement binding.
- TypeScript/Vite scaffolds need `vite/client` types, and generated `*.tsbuildinfo` files should not be committed.
- Do not claim visual QA merely because the frontend builds.
