---
name: tione-ssh-diagnose
description: Diagnose Tencent Cloud TI-ONE Notebook/development-machine SSH failures, especially after restart or rebuild. Use when the user provides a TI-ONE development-machine/Notebook ID, name, SSH alias, host and port, or reports 连接不上, REMOTE HOST IDENTIFICATION HAS CHANGED, Host key verification failed, SHA256 fingerprint mismatch, known_hosts conflict, or uncertainty about whether the local private key or remote authorized_keys is invalid.
---

# TI-ONE SSH Diagnose

Determine whether failure comes from endpoint discovery, network reachability, server host-key verification, or user public-key authentication. Keep those layers separate in the report.

## Workflow

1. Resolve the current trusted endpoint.
   - For a Notebook ID such as `nb-...`, use the installed `tione` skill and its `tione_api.py notebook <id>` command.
   - For a name, use `tione_api.py notebooks --name-contains '<name>' --details`, then select an exact or unambiguous match.
   - Read the current SSH host and port from `SSHConfig`. Never print `PublicKey`, auth tokens, cloud secrets, or presigned URLs.
   - If TI-ONE API authentication fails, inspect `~/.ssh/config` as a fallback, but label that endpoint as locally configured and not currently verified by TI-ONE.

2. Run the bundled read-only diagnostic:

   ```bash
   python3 scripts/diagnose_ssh.py <ssh-alias-or-host> [--port PORT]
   ```

   The script resolves `ssh -G`, checks TCP reachability, scans current server host keys, fingerprints matching `known_hosts` entries, and classifies each algorithm as matching, changed, or new. It never edits SSH files.

3. Interpret results in this order:
   - TCP failure: endpoint, port mapping, firewall, instance state, or network problem.
   - `CHANGED`: server host key differs from the local `known_hosts` entry. This is independent of the user's login key.
   - Host key matches but login fails: inspect the local identity selected by `ssh -G`, remote `authorized_keys`, username, and permissions.
   - TI-ONE restart alone does not necessarily change a host key; rebuild, replacement, regenerated OS state, or endpoint reuse can.

4. Test user-key authentication only after the endpoint has been verified through TI-ONE or explicitly confirmed by the user:

   ```bash
   python3 scripts/diagnose_ssh.py <alias> --auth-test --endpoint-verified
   ```

   The script pins the freshly scanned host keys in a temporary file and runs a harmless `true` command with `BatchMode=yes`. Do not use `StrictHostKeyChecking=no` as a routine workaround.

5. Report concise evidence: resolved endpoint, TCP result, old and current SHA256 fingerprints by algorithm, whether user-key authentication succeeds, and the recommended next action.

## Repair

Remain read-only unless the user explicitly asks to fix the connection. Before removing an entry, require both:

- current endpoint verified from TI-ONE or explicitly confirmed by the user;
- new fingerprint shown to the user or otherwise checked against a trusted source.

Then remove only the exact host-and-port entry:

```bash
ssh-keygen -R '[HOST]:PORT'
ssh <alias>
```

Never delete the entire `known_hosts` file and never suppress host-key verification permanently.

## Gotchas

- The SHA256 shown in `REMOTE HOST IDENTIFICATION HAS CHANGED` identifies the development machine's SSH host key, not the user's local private key.
- A successful authentication test proves the local private key and remote `authorized_keys` still correspond; it does not explain a stale host-key record.
- Multiple algorithms can be stored for one endpoint. Remove by exact `[host]:port`, not by line number, because line numbers drift.
- Hashed `known_hosts` entries are still discoverable with `ssh-keygen -F`; do not rely on text search alone.
- Do not claim a changed fingerprint is safe solely because the machine was restarted.
