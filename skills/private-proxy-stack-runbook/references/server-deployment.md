# Server deployment guide

Read this before mutating a VPS. It is an implementation contract, not a frozen vendor manual; verify current official configuration schemas first.

## Preflight

1. Confirm explicit authorization, target host, supported Ubuntu release, recovery access, and provider firewall rules.
2. Capture a redacted baseline: OS, available disk, active listeners, firewall status, relevant installed packages, and service state.
3. Back up any existing Hysteria2, Xray, Caddy, Sub-Store, or systemd configuration with restrictive permissions.
4. Verify release provenance. Prefer official repositories or pinned releases with signatures/checksums. Inspect downloaded installer scripts before running them.
5. Ensure the administrative SSH path remains allowed before enabling or reloading a firewall.

## Host and firewall

The intended inbound allowances are TCP 22, 80, 443, and 8443 plus UDP 443. Restrict SSH by source when feasible. Do not assume the host firewall is the only firewall: inspect the VPS provider ACL as well.

After changing firewall rules, keep the current SSH session open and verify a second authorized login before closing it.

## Hysteria2 layer

- Bind UDP 443.
- Use password authentication with a long random secret stored outside chat/repositories.
- Use a valid certificate when the deployment design supports it. If the chosen design intentionally uses a self-signed certificate, clients must be configured consistently and the reduced authentication assurance must be acknowledged.
- Ensure the service account can read the private key without making it world-readable. A typical pattern is root ownership, the Hysteria2 service group, mode `0640` on the key, and `0644` on the public certificate; confirm the actual service group first.
- Validate configuration with the installed version's checker, restart, then verify service state, logs, and a UDP 443 listener.

## Xray Reality layer

- Bind TCP 8443 using VLESS + Reality with `xtls-rprx-vision` when supported by the deployed client/server versions.
- Generate a fresh UUID and X25519 pair locally on the server. Store only the private key server-side; clients receive the public key.
- Keep destination/SNI/server-name values mutually consistent and confirm the selected destination is reachable from the VPS.
- Validate the JSON with the installed Xray binary before restart. Verify TCP 8443 and recent logs afterward.

## Caddy layer

The architectural requirement is equivalent to:

```caddyfile
{
    servers {
        protocols h1 h2
    }
}

<SUBSCRIPTION_DOMAIN> {
    encode gzip
    handle_path /substore/* {
        reverse_proxy localhost:3000
    }
    header {
        Cache-Control "no-store"
    }
}
```

Confirm the syntax against the installed Caddy release. The global `h1 h2` restriction is essential because HTTP/3 would bind UDP 443. Run `caddy validate` before restart, then verify TCP 443, certificate issuance, and absence of a Caddy UDP 443 listener.

Avoid serving unrelated filesystem roots unless the user explicitly needs them. Limit the public routes to the subscription endpoints required by the design.

## Sub-Store layer

- Use a reviewed, pinned release rather than an unbounded default branch when possible.
- Run it as a dedicated unprivileged service account under systemd or another supervised process manager; avoid a long-lived root process.
- Bind to loopback port 3000, not a wildcard/public interface.
- Keep the management surface private. If remote administration is required, prefer an SSH tunnel or an authenticated access layer.
- Treat generated subscription URLs and node URIs as secrets.

Before adding live nodes, prove that loopback responds and that the Caddy path reaches it. Then add the Hysteria2 and Reality entries with placeholders replaced locally, without echoing them into logs.

## Verification and rollback

Run `scripts/check_stack.sh` for the non-secret host checks. Separately verify:

- a real Hysteria2 client handshake and egress;
- a real Reality client handshake and egress;
- HTTPS certificate/hostname validation for the subscription endpoint;
- subscription parsing by each intended client;
- failover by temporarily selecting each outbound, not by disrupting production traffic without approval.

On failure, stop at the affected layer. Restore the backed-up configuration, validate it, restart only that service, and confirm the old path before proceeding.
