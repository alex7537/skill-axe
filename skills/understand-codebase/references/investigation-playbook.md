# Repository Investigation Playbook

Use this reference when the obvious file tree does not explain actual behavior.

## Evidence hierarchy

Prefer stronger evidence when sources conflict:

1. Reproducible runtime observation or focused test
2. Executable build/startup configuration
3. Implementations plus callers and registrations
4. Tests and fixtures as intended contracts
5. Current documentation and examples
6. Names, comments, and directory layout

Record documentation/code conflicts instead of silently choosing one.

## Search sequence

Start narrow and widen deliberately:

1. List files with `rg --files`; identify instructions, manifests, entry candidates, tests, and generated/vendor directories.
2. Search exact symbols with `rg -n '\bSymbolName\b'`.
3. Search registrations and construction sites: factories, dependency containers, router tables, plugin registries, annotations, macros, service loaders, or module exports.
4. Search configuration keys across code, example configs, deployment files, and tests.
5. Trace both callers and callees. Imports alone show only a possible edge.
6. Inspect the nearest focused tests before general test suites.

Avoid dumping huge files. Find relevant line ranges, then read enough surrounding context to understand the branch and state changes.

## Trace dynamic behavior

When static control flow disappears, inspect:

- framework lifecycle hooks and generated sources
- decorators/annotations, reflection, or metadata scanning
- dependency-injection bindings and factory selection
- callbacks, event buses, queues, signals, observers, and middleware
- plugin discovery and environment-dependent loading
- templates, schemas, IDLs, code generators, macros, and build steps
- configuration precedence and feature flags

State which edge is proven statically and which requires runtime confirmation.

## Build a causal explanation

For each hop in an execution trace, capture:

| Field | Question |
|---|---|
| Trigger | What causes this code to run? |
| Contract | What input and preconditions does it accept? |
| Transformation | What value or state changes? |
| Ownership | Who owns and releases the state/resource? |
| Dispatch | How is the next implementation selected? |
| Failure | How do errors, cancellation, or retries propagate? |
| Evidence | Which file, symbol, test, or observation proves it? |

## Descend to first principles

Use “why” recursively, but stop only at a named foundation:

- **Language/runtime:** allocation, dispatch, type erasure, GC, async executor, memory model
- **Operating system:** process/thread, file descriptor, socket, syscall, virtual memory, scheduling
- **Data/storage:** index, WAL, isolation, consistency, serialization, cache coherence
- **Distributed systems:** ordering, idempotency, retry, consensus, backpressure, partial failure
- **Protocol:** framing, handshake, state machine, flow control, compatibility
- **Algorithm/math:** complexity, invariant, graph traversal, probability, numerical stability, optimization

Tie the foundation back to a concrete code decision. If the repository delegates the behavior entirely to a dependency, inspect the boundary and cite upstream documentation or source only when needed.

## Verification techniques

Choose the smallest technique that can falsify the current model:

- run a focused existing test
- add temporary logging only with user authorization
- place breakpoints at registration, entry, and state-transition points
- construct a minimal input that selects a disputed branch
- compare configuration with and without one override
- inspect generated output after the relevant build step
- measure or trace one operation rather than benchmarking the entire system
- write a tiny state table or hand-simulate an algorithm

Before running commands that mutate state, build artifacts, install dependencies, or contact external systems, explain the impact and remain within the user's authorization.

## Completion criteria

A repository model is useful when the user can answer:

- What starts the system and what are its external boundaries?
- Which path implements one important behavior end to end?
- Where is state owned, transformed, persisted, and released?
- Which invariants and failure semantics govern the path?
- Which parts are framework/runtime magic rather than application code?
- What underlying principle explains the design?
- What evidence could disprove the model?
