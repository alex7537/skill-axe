# Clients and troubleshooting

Read this for Clash/Mihomo, sing-box, subscription delivery, or incident diagnosis.

## Desktop clients

For Clash Verge Rev or another Mihomo-compatible client:

- Import the HTTPS subscription URL without pasting it into chat or logs.
- Keep rules and proxy-group customization separate from the generated node subscription so node rotation does not erase policy.
- Use a `url-test` group for the Hysteria2 and Reality nodes when automatic selection is desired.
- Validate both individual nodes before relying on automatic selection.
- Enable system proxy or TUN only as needed; TUN changes routing more broadly and may conflict with VPNs or corporate controls.

An HTTP 401 JSON response from an authenticated API can demonstrate network reachability, but it does not prove credentials or API authorization. Do not send a live API key merely to test routing.

## Linux clients

The intended path is:

```text
application -> HTTP_PROXY/HTTPS_PROXY -> localhost:7890 -> sing-box -> VPS
```

Requirements:

- Bind the mixed inbound to loopback unless LAN sharing is explicitly requested and secured.
- Build the configuration from the schema of the installed sing-box version. Validate it with `sing-box check -c <CONFIG_PATH>` before restart.
- Keep Hysteria2 and Reality as distinct outbounds, then place them behind `urltest` and `selector` outbounds if supported by the installed version.
- Put proxy environment variables in the narrowest applicable scope. A shell alias affects only that shell; systemd services need explicit environment configuration.
- `proxyoff` should unset lower- and uppercase HTTP/HTTPS proxy variables. Check `ALL_PROXY` separately if it is used.

Never copy `<equation>...` fragments from the Feishu-exported shell example. They are rendering artifacts that replaced normal shell `${VARIABLE}` expansions.

## Diagnostic funnel

Work from the server outward and record redacted evidence at each layer:

1. **Process:** Is the expected systemd unit active? Did it crash-loop?
2. **Configuration:** Does the installed binary accept the config? Are permissions correct?
3. **Listener:** Does the correct process own the correct protocol/port?
4. **Host firewall:** Are the intended TCP/UDP rules active?
5. **Provider ACL:** Does the external firewall permit the same protocol/port?
6. **DNS/TLS:** Does the name resolve to the right address, and does the certificate match?
7. **Handshake:** Can the matching client establish Hysteria2 or Reality using redacted local credentials?
8. **Routing/egress:** Does traffic exit through the expected VPS address?
9. **Application:** Does the target CLI/service inherit the intended proxy environment?

## Symptom map

| Symptom | First checks |
|---|---|
| Hysteria2 private-key permission denied | Actual service user/group; key ownership and mode; parent-directory traversal permissions |
| `nc -zv HOST 443` fails | It is a TCP probe; inspect UDP 443 locally and use a real Hysteria2 client test |
| Caddy fails after Hysteria2 starts | HTTP/3/UDP 443 collision; Caddy protocols; current socket owner |
| Reality timeout | Server/client UUID, key pair, short ID, SNI, destination, flow, fingerprint, TCP 8443 ACL |
| sing-box rejects DNS/outbound config | Installed version and schema; deprecated legacy DNS fields; configuration validator output |
| Subscription UI works locally but not publicly | Loopback bind is expected; inspect Caddy route, DNS, certificate, TCP 443, and provider ACL |
| Proxy works in shell but not a service | systemd/service environment does not inherit shell aliases or exported variables |

Prefer service logs and protocol-aware checks over repeated restarts. Redact node URIs and secrets before sharing any output.
