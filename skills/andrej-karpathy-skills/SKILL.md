---
name: andrej-karpathy-skills
description: Behavioral guidelines to reduce common LLM coding mistakes. Use when writing, reviewing, or refactoring code to avoid overcomplication, make surgical changes, surface assumptions, and define verifiable success criteria.
---

# Karpathy Behavioral Guidelines

Use these guidelines when writing, reviewing, or refactoring code.

## 1. Think Before Coding

Do not assume or hide confusion.

- State assumptions explicitly.
- If multiple interpretations exist, present them.
- Prefer the simpler approach when it solves the problem.
- If something is unclear and risky, stop and ask.

## 2. Simplicity First

Write the minimum code that solves the problem.

- No features beyond what was asked.
- No abstractions for single-use code.
- No speculative configurability.
- No broad error handling for impossible scenarios.
- If the code is much longer than needed, simplify it.

## 3. Surgical Changes

Touch only what the request requires.

- Do not refactor unrelated code.
- Do not improve adjacent formatting or comments.
- Match the existing style.
- Remove imports, variables, or helpers made unused by your own changes.
- Mention unrelated dead code instead of deleting it.

Every changed line should trace directly to the user request.

## 4. Goal-Driven Execution

Define success criteria and verify them.

- For fixes, reproduce the failure when practical, then make it pass.
- For validation, test invalid and valid paths when practical.
- For refactors, keep behavior unchanged and run relevant checks.
- For multi-step work, state a short plan with verification for each step.
