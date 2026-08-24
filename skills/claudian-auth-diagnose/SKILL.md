---
name: claudian-auth-diagnose
description: Diagnose recurring Obsidian Claudian and Claude Code authentication failures on macOS, especially `authentication_failed`, 401 expired OAuth tokens, misleading `claude auth status`, failures after VPN or network switching, hanging `claude auth login`, or cases where Terminal works but Claudian does not. Use for diagnosis and safe recovery guidance; do not use for unrelated Claudian UI or model-quality problems.
---

# Claudian Auth Diagnose

Treat this as a runbook. Establish which layer fails before recommending another login.

## Evidence first

1. Capture the exact Claudian error and whether the request hangs, fails immediately, or only fails after a network/VPN change.
2. Run the bundled read-only diagnostic:

   ```bash
   python3 scripts/diagnose.py --vault "/path/to/Obsidian Vault"
   ```

3. When the user asked to diagnose actual authentication, add `--probe`. It sends only `Reply only OK` to Claude and imposes a 45-second timeout:

   ```bash
   python3 scripts/diagnose.py --vault "/path/to/Obsidian Vault" --probe
   ```

The script deliberately excludes emails, organization IDs, tokens, and Keychain passwords.

## Decision points

- `auth status` is logged out: authentication was never completed or was explicitly cleared.
- `auth status` says logged in but the probe returns 401/expired token: local status is stale; OAuth refresh failed. Check a hanging `claude auth login`, credential modification time, concurrent Claude/Claudian sessions, and whether VPN/network changed during refresh.
- The probe works but Claudian fails: inspect the executable path, `HOME`, `CLAUDE_CONFIG_DIR`, macOS Keychain access, Obsidian restart state, and the Claudian/Agent SDK version. This is a plugin or non-interactive child-process problem, not a general login failure.
- Anthropic endpoints fail DNS/TLS/connectivity checks: stabilize the network path before touching credentials. Browser, Terminal, and Obsidian must reach the same expected network route during OAuth.

An OAuth access token expiring is normal; repeatedly requiring interactive login is not. A valid refresh token should renew it automatically. VPN switching is usually a trigger only when it interrupts refresh/callback traffic or changes browser and CLI routing; do not present it as proof by itself.

## Recovery boundary

Diagnosis is read-only. Do not run `claude auth logout`, kill processes, edit Keychain entries, change VPN/proxy settings, or modify Claudian configuration unless the user explicitly requests the corresponding fix.

For an authorized clean recovery:

1. Stop active Claudian requests and fully quit Obsidian so no child session rotates credentials concurrently.
2. End any hanging `claude auth login`; prefer `Ctrl+C` in its original terminal.
3. Keep the network route stable, then run `claude auth logout` followed by `claude auth login`.
4. The browser success page is insufficient: confirm the login command returns to the shell prompt.
5. Run `claude -p "Reply only OK"` in the same Terminal.
6. Restart Obsidian and verify a new Claudian message.

Authentication entry, OAuth approval, passwords, and security prompts must be completed by the user. Never extract or print Keychain secret values.

## Success criteria

- CLI layer: the real probe returns `OK`, not merely `loggedIn: true`.
- Claudian layer: a newly spawned Claudian request succeeds after Obsidian restart.
- If CLI succeeds but Claudian fails, report the split explicitly and continue only with plugin/child-environment diagnosis.

## Gotchas

- `claude auth status` validates local credential presence and can remain positive while the server rejects an expired access token.
- A browser OAuth page can look successful while `claude auth login` is still waiting and has not updated Keychain.
- On macOS, credentials normally live in the `Claude Code-credentials` Keychain item; inspect metadata only. Never use `security ... -w` or `-g` in diagnostics because those can reveal the password payload.
- Obsidian can stay open for days and keep stale Claude child processes. Restart it only after the CLI probe succeeds.
- macOS does not ship GNU `timeout`; the bundled Python probe supplies its own timeout.
- Concurrent refresh/login sessions can rotate or invalidate refresh state. Eliminate concurrency during clean recovery.
