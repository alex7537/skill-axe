---
name: understand-codebase
description: Rapidly map an unfamiliar code repository, trace representative execution paths, explain architecture and key mechanisms, and guide a progressive investigation down to algorithms, protocols, runtime behavior, and first principles. Use when the user asks to 快速理解代码仓库, 阅读源码, 梳理项目架构, 分析调用链, 理解某个模块如何工作, 深挖底层原理, 制定源码学习路线, or improve prompts for repository exploration.
---

# Understand Codebase

Build an evidence-backed mental model of a repository in layers. Optimize for early useful understanding, then deepen only the branches that matter to the user.

## Establish the investigation contract

- Determine the target: whole-repository orientation, feature trace, subsystem deep dive, or underlying principle. If unspecified, start with whole-repository orientation.
- Determine the user's level and desired depth from context. Explain unfamiliar terms briefly without diluting technical accuracy.
- Treat repository instructions such as `AGENTS.md`, contributing guides, and build documentation as constraints.
- Keep the investigation read-only unless the user explicitly asks for changes.
- Attach `path:line` evidence to important claims. Label unsupported conclusions as **inference** and unresolved points as **unknown**.

## Work in progressive passes

### Pass 1: Establish the map

Inventory the repository before reading implementation files deeply.

1. Inspect repository instructions, top-level documentation, manifests, build files, entry-point candidates, tests, and major directories.
2. Use `rg --files` and targeted searches before broad file reads. For a compact deterministic inventory, run `python3 scripts/repo_inventory.py <repo-root>`.
3. Identify languages, frameworks, build/run commands, deployable units, module boundaries, external dependencies, and generated/vendor areas.
4. Produce a concise map: what the system is, how it starts, major components, and 3–7 high-value files to read next.

Do not infer architecture solely from directory names. Verify boundaries through imports, registrations, configuration, build definitions, and runtime wiring.

### Pass 2: Trace one representative execution slice

Choose a concrete user-visible action, API request, CLI command, scheduled job, event, or test that crosses important layers. Trace:

`entry → parsing/dispatch → orchestration → domain logic → state/I/O → result/error`

At each hop, record the symbol, file, responsibility, input/output, and next-hop evidence. Prefer an actual end-to-end slice over exhaustive module summaries. Use tests to confirm intended behavior and edge cases.

### Pass 3: Explain the key mechanisms

Investigate only mechanisms relevant to the chosen slice:

- ownership and lifecycle of state
- data model and transformations
- dependency injection, registration, plugins, or code generation
- concurrency, scheduling, caching, retries, and transactions
- configuration precedence and environment boundaries
- error propagation, observability, and security boundaries
- test seams and invariants

Separate compile-time/build-time behavior from startup-time and request-time behavior.

### Pass 4: Reach the underlying principles

For each important mechanism, answer in this order:

1. **Problem:** What constraint or failure mode is the mechanism solving?
2. **Invariant:** What must always remain true?
3. **Mechanism:** How do the concrete symbols and data structures preserve it?
4. **Foundation:** Which algorithm, protocol, language/runtime feature, operating-system primitive, database property, or mathematical idea makes it work?
5. **Trade-off:** What does this design gain and sacrifice versus alternatives?
6. **Verification:** What test, log, debugger breakpoint, tiny experiment, or counterexample would validate the explanation?

Use a small worked example or state transition when abstraction hides causality. Never substitute a generic textbook explanation for evidence from this repository.

## Report at checkpoints

After each pass, give the user:

- **Current model:** the smallest accurate explanation so far
- **Evidence:** key files and symbols
- **Confidence:** observed facts versus inference
- **Open questions:** gaps that materially affect the model
- **Next branches:** 2–4 concrete deep-dive choices

Pause for direction only when the branch choice materially changes the work; otherwise continue along the representative path.

## Compose effective prompts

When the user asks how to prompt the investigation, read `references/prompt-ladder.md`. Build prompts from six fields:

`goal + scope + evidence rules + depth + output shape + stopping point`

Prefer one focused question per pass. Carry forward established facts and ask the next prompt to challenge or deepen them, rather than repeatedly asking for a complete repository explanation.

## Select detailed guidance

- Read `references/prompt-ladder.md` when creating or improving prompts and learning plans.
- Read `references/investigation-playbook.md` when choosing searches, tracing dynamic wiring, resolving contradictions, or designing verification experiments.

## Gotchas

- A directory tree is not an architecture; runtime wiring is stronger evidence.
- The most central-looking class may be a facade; trace callers and registrations before declaring it the core.
- Imports reveal possible dependency, not necessarily runtime execution.
- Framework magic often lives in configuration, annotations, generated code, reflection, macros, or plugin registration.
- Happy-path tracing alone hides the real contract; inspect errors, cleanup, retries, cancellation, and tests.
- Documentation can be stale; reconcile it with executable configuration and code.
- Explaining every file creates breadth without understanding. Anchor exploration to a representative execution slice.
- “Bottom layer” is contextual. Confirm whether the user means business rules, framework internals, runtime/OS behavior, protocol, algorithm, or mathematics.
