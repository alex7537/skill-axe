---
name: private-proxy-stack-runbook
description: Plan, deploy, verify, or troubleshoot an authorized private VPS proxy stack using Hysteria2, Xray Reality, Caddy, Sub-Store, Clash/Mihomo, or sing-box. Use for requests mentioning VPS proxy setup, UDP 443 versus TCP 443 conflicts, Reality fallback, private subscription hosting, or this exact stack. Do not use for bypassing access controls, hiding malicious traffic, or operating infrastructure the user is not authorized to administer.
---

# Private Proxy Stack Runbook

Build or diagnose a small, authorized private proxy service while preserving the protocol/port contract and keeping credentials out of chat, logs, repositories, screenshots, and generated reports.

This skill is distilled from the Feishu page “私有代理系统部署手册：VPS + Hysteria2 + Reality + Caddy + Sub-Store”, revision 19. Treat the page as the design baseline, not as proof that third-party install commands or configuration schemas are still current.

## Route the request

- For architecture, prerequisites, or a deployment plan, read [references/architecture.md](references/architecture.md).
- Before changing a server, read [references/server-deployment.md](references/server-deployment.md).
- For client setup or a failure report, read [references/clients-and-troubleshooting.md](references/clients-and-troubleshooting.md).
- For a read-only server health check, run `scripts/check_stack.sh` locally on the VPS or through an already authorized remote shell.

## Authorization and secret boundary

- Require an explicit request before changing a VPS, DNS record, firewall, systemd unit, Caddy configuration, Sub-Store data, or client configuration. A request for a plan or explanation is read-only.
- Operate only infrastructure the user says they own or administer. Do not help conceal malicious activity, evade organizational controls, or access services without authorization.
- Ask for secret *names or local locations*, not secret values in chat. Use placeholders such as `<HY2_PASSWORD>`, `<REALITY_UUID>`, `<REALITY_PRIVATE_KEY>`, `<REALITY_PUBLIC_KEY>`, and `<REALITY_SHORT_ID>` in all displayed commands.
- Never print private keys, passwords, full node URIs, full subscription URLs, access tokens, or SSH credentials. Redact them from diagnostics.
- Do not commit generated secrets or live configurations. Prefer root-readable files or a secret manager, and set the narrowest permissions supported by each service.

## Operating contract

Preserve these invariants unless the user explicitly changes the architecture:

- Hysteria2 is the primary path on UDP 443.
- Xray Reality is the fallback on TCP 8443.
- Caddy serves the subscription endpoint on TCP 443 and must not bind UDP 443; disable HTTP/3 for this listener.
- Sub-Store listens only on loopback port 3000 and is reached through Caddy or an SSH tunnel. Never expose port 3000 publicly as a convenience.
- A domain is optional for the proxy nodes but recommended for an HTTPS subscription endpoint.
- Validate UDP and TCP independently. A failed TCP probe to port 443 says nothing about Hysteria2 on UDP 443.

## Execution shape

1. Establish the desired mode: plan, deploy, client setup, health check, or diagnosis. Inventory OS/version, provider/firewall layer, domain/DNS status, current listeners, installed services, and rollback access.
2. Produce a redacted change plan with exact files/services affected and the expected port ownership. Back up any existing configuration before editing it.
3. Check current official documentation and release notes for Hysteria2, Xray, Caddy, Sub-Store, sing-box, and the chosen client before executing install commands or writing version-sensitive schemas. Do not execute a remote `curl | bash` blindly; download and inspect the installer or use a pinned, verified package when practical.
4. Apply one layer at a time: host/firewall, Hysteria2, Reality, Caddy, Sub-Store, subscription, then clients. Validate each layer before continuing.
5. Run configuration validators before restarting services. After a restart, confirm service state, protocol-specific listeners, recent logs, and a real client request.
6. Report what changed, what was verified, remaining risks, and rollback instructions without revealing secrets.

Stop before a mutation when the target, authorization, secret-handling method, or rollback path is unclear.

## Gotchas

- Caddy HTTP/3 can seize UDP 443 and conflict with Hysteria2 even though HTTPS itself uses TCP 443.
- `nc -zv HOST 443` normally probes TCP; use `ss` on the server and an appropriate UDP-aware/client test for Hysteria2.
- Hysteria2 may fail because its service user cannot read the TLS private key; fix group ownership and permissions without making the key world-readable.
- Reality timeouts commonly come from mismatched UUID, public/private key pair, short ID, SNI/server name, flow, or client fingerprint.
- sing-box configuration schemas change. Do not reintroduce deprecated legacy DNS/outbound fields based solely on an old example.
- The source page's exported Linux shell example contains Feishu formula-rendering corruption around shell `${...}` expansions. Never copy those `<equation>` fragments; reconstruct and validate the script from the intended variables.
- An HTTP subscription leaks node credentials in transit. Use it only as a clearly acknowledged temporary fallback; prefer HTTPS or direct, securely delivered node configuration.
