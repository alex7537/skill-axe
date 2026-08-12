---
name: claude-guided-coding
description: Behavioral guidelines to reduce common coding mistakes. Use when writing, reviewing, or refactoring code to surface assumptions, prefer the simplest implementation, keep edits surgical, and verify against explicit success criteria.
---

# Claude-Guided Coding

Use these guidelines when coding, reviewing, or refactoring.

## 1. Think Before Coding

- State assumptions explicitly.
- If multiple interpretations exist, name them instead of silently picking one.
- Prefer the simpler approach when it solves the task.
- If a risky detail is unclear, stop and ask.

## 2. Simplicity First

- Write the minimum code that solves the request.
- Do not add speculative flexibility or extra features.
- Avoid abstractions for one-off code.
- If the solution feels longer than necessary, simplify it.

## 3. Surgical Changes

- Touch only the lines needed for the task.
- Do not refactor adjacent code unless required.
- Match the existing style.
- Remove only the unused code created by your own edits.

## 4. Goal-Driven Execution

- Turn the task into concrete checks before implementing.
- For behavior changes, add or run tests that prove the new behavior.
- For multi-step work, state a short plan and how each step will be verified.
