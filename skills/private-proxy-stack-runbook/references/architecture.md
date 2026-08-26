# Architecture and planning contract

Read this reference when planning the stack or collecting prerequisites.

## Topology

```text
Desktop/mobile/Linux client
  -> Clash/Mihomo, Hiddify, Stash, or sing-box
  -> private subscription endpoint (optional)
     -> Caddy TCP 443
        -> Sub-Store localhost:3000
  -> VPS node
     -> Hysteria2 UDP 443 (primary)
     -> Xray Reality TCP 8443 (fallback)
  -> Internet
```

## Required inputs

Collect these without asking the user to paste live secrets:

| Input | Purpose |
|---|---|
| VPS address, OS, and SSH user | Host targeting and package choices |
| Provider and provider-firewall state | Distinguish cloud ACLs from host firewall |
| Authorized SSH access method | Execution boundary; never request a private key in chat |
| Domain and DNS control, if used | HTTPS subscription endpoint |
| Secret storage/generation method | Hysteria2 password and Reality credentials |
| Existing services/listeners | Avoid overwriting or port collisions |
| Client types | Choose Mihomo/Clash or sing-box output |

Recommended secret placeholders:

```text
<YOUR_VPS_IP>
<SUBSCRIPTION_DOMAIN>
<HY2_PASSWORD>
<REALITY_UUID>
<REALITY_PRIVATE_KEY>
<REALITY_PUBLIC_KEY>
<REALITY_SHORT_ID>
```

Generate the Hysteria2 password as a long random value. Generate Reality UUID and X25519 keys with the currently installed, verified Xray binary. A short ID is typically a hexadecimal value, but confirm the accepted format against the deployed Xray version.

## Port ownership

| Port | Protocol | Owner | Exposure |
|---|---|---|---|
| 22 | TCP | SSH | Restrict to administrative sources where practical |
| 80 | TCP | Caddy | Certificate challenge/redirect, if needed |
| 443 | TCP | Caddy | HTTPS subscription endpoint |
| 443 | UDP | Hysteria2 | Primary proxy path |
| 8443 | TCP | Xray Reality | Fallback proxy path |
| 3000 | TCP | Sub-Store | Loopback only (`localhost`) |

TCP and UDP port numbers are separate namespaces. Caddy can own TCP 443 while Hysteria2 owns UDP 443, provided Caddy HTTP/3 is disabled.

## Domain decision

- With a domain: point an A/AAAA record to the VPS only after confirming address-family reachability; use Caddy for HTTPS and proxy only the intended Sub-Store path.
- Without a domain: securely distribute direct node configuration, or use an SSH tunnel to reach loopback Sub-Store administration.
- Avoid long-lived IP + plaintext HTTP subscriptions because the subscription contains credentials.

## Planned-change output

Before execution, name:

- configuration files and systemd services to be created or changed;
- firewall/provider ACL rules;
- port owners before and after;
- DNS records, if any;
- backup and rollback locations;
- validation commands and expected results.
