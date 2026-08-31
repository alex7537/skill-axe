---
name: zerotier-diagnose
description: Inspect, explain, and troubleshoot ZeroTier installation, version, service health, network membership, assigned virtual IPs, routes, and direct-versus-relayed peer paths on macOS or Linux. Use when the user asks 检查 ZeroTier、ZeroTier 是否安装完整、服务是否在线、虚拟 IP 是什么、为什么显示 OFFLINE/RELAY/TUNNELED, or wants the current overlay-network packet path explained. Do not join or leave networks, change controller membership, or alter routes unless the user explicitly requests that mutation.
---

# ZeroTier Diagnose

Treat diagnosis as a read-only evidence funnel. Distinguish installation artifacts, the privileged service, local control API reachability, virtual-network authorization, and peer transport quality; one passing layer does not prove the next.

## Diagnostic workflow

1. Run `scripts/check_zerotier.sh` and preserve its section labels in the assessment.
2. Establish the platform and installation evidence:
   - macOS: application or package receipt, CLI symlink, service home, and `com.zerotier.one` LaunchDaemon;
   - Linux: CLI/binary, package evidence when available, and `zerotier-one.service`.
3. Read the CLI version independently of service health. `zerotier-cli -v` can succeed while the daemon is unusable.
4. Compare service-manager state with `zerotier-cli info`:
   - `ONLINE` proves contact with the ZeroTier root infrastructure;
   - `OFFLINE` means roots are currently unreachable;
   - `TUNNELED` means TCP fallback is active.
5. Use `listnetworks` to verify at least one `OK` membership, its virtual interface, assigned IPs, and managed routes. An installed and online node may still belong to no network.
6. Use `peers` to classify current paths. `DIRECT` is peer-to-peer; `RELAY` is an encrypted relayed path. Report mixed results per peer rather than labeling the entire node direct or relayed.
7. Read `references/mental-model.md` when explaining Controller, Root/Planet, Node ID, Network ID, virtual IP, routes, encryption, or packet flow.

## Repair boundary

Keep checks read-only unless the user asked to repair. Before restarting or reinstalling, resolve the exact service and show why repair is needed.

- If installation artifacts are missing, prefer the platform's official ZeroTier installer/package workflow; do not infer that a missing GUI means the service is absent.
- If the service is stopped, start or restart the resolved LaunchDaemon/systemd unit, then repeat `info`, `listnetworks`, and `peers`.
- Do not join an unknown Network ID, authorize a member, enable a default route, or change controller rules without an explicit request naming the intended network or change.
- Never print or copy `identity.secret`, `authtoken.secret`, controller credentials, or private keys. Checking their existence and permissions is sufficient.

## Reporting contract

Lead with one of: `完整且在线`, `已安装但服务异常`, `服务在线但未加入网络`, `网络已加入但路径退化`, or `未完整安装`.

Include:

- executable/application evidence and version;
- service state and node status;
- each joined network's name/ID, authorization status, interface, virtual IP, and route scope;
- direct/relay/TCP-fallback observations;
- repairs performed and post-repair verification;
- the difference between observed facts, likely causes, and unknowns.

## Gotchas

- A restricted Codex sandbox can block loopback access to the daemon's local API on `<loopback-address>:9993`. This produces `Error connecting to the ZeroTier service` even while `launchctl` shows a healthy daemon. Retry the read-only CLI check outside the restricted sandbox before restarting or reinstalling anything.
- `pgrep` and local socket probes can also be denied by macOS sandboxing. Prefer the service manager plus an authorized CLI query over treating these denials as process failure.
- A physical LAN address, another VPN's `utun` address, and a ZeroTier-assigned address can coexist. Attribute the virtual IP from `listnetworks`, not from the first private-looking address in `ifconfig`.
- Controller and Root are different roles: the Controller authorizes/configures a virtual network; Roots help peers discover each other and may relay encrypted packets.
- `allowDefault=false` means ordinary Internet traffic is not routed through ZeroTier. Report the actual managed route instead of calling the setup a full-tunnel VPN.
