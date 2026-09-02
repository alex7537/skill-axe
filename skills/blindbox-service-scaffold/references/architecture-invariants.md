# Architecture invariants

## Ownership

The blind-box service owns:

- immutable published pool versions and configuration hashes;
- available allocation per pool item;
- draw requests and idempotency results;
- inventory movements and audit evidence;
- outbox events for downstream order and fulfillment work.

An external commerce system may remain authoritative for the merchant's master catalog, payment, customer order, and fulfillment status. Persist stable external IDs at the adapter boundary.

## Atomic draw boundary

In production, one database transaction must:

1. verify the pool version is published;
2. verify an authenticated entitlement or paid order;
3. resolve an existing idempotency result before creating anything new;
4. lock the relevant pool/allocation rows;
5. compute the active weight total from in-stock items;
6. select with a cryptographically secure server RNG;
7. decrement inventory and append its movement;
8. write the draw record, previous hash, and current audit hash;
9. write an outbox event;
10. commit before returning the item to the client.

Put a unique constraint on the merchant-scoped idempotency key. Do not rely only on a preflight lookup: concurrent requests must collide safely at the database boundary.

## Minimum entities

```text
merchant
product_variant (merchant_id, external_id, sku, value)
pool (merchant_id)
pool_version (pool_id, version, status, price, config_hash)
pool_item (pool_version_id, variant_id, weight, initial_qty, remaining_qty)
draw_record (pool_version_id, variant_id, customer/order, idempotency_key, audit hashes)
inventory_movement (pool item, draw/refund reason, delta)
outbox_event (topic, aggregate, payload, publication state)
```

The pool version referenced by a historical draw must remain readable after a new version is published or the pool is paused.

## Probability semantics

For fixed weights while stock remains:

```text
P(item i) = weight_i / sum(weight_j for every j with remaining_j > 0)
```

When an item reaches zero, remove it from the active denominator. If product quantity itself should define probability, model each unit explicitly or define a documented derived-weight rule; do not silently mix the two models.

## Audit limits

A hash chain makes later alteration detectable when a trusted checkpoint exists; it does not by itself prove the operator never biased the RNG. If public verification is required, add a reviewed commitment/reveal or external randomness design without moving selection to the browser.

## State transitions

Use explicit states instead of deleting evidence:

```text
pool version: draft -> published -> paused/exhausted
draw: requested -> committed -> fulfillment_pending -> fulfilled
                   \-> compensating/refunded
```

Compensation appends inventory and audit movements. It does not erase the original draw.
