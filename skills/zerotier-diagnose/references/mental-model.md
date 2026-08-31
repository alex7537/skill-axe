# ZeroTier mental model

Use this reference when the request asks how ZeroTier works or when interpreting diagnostic output.

## Two coupled layers

- **VL1 transport:** an encrypted peer-to-peer network that creates virtual paths between ZeroTier node identities.
- **VL2 Ethernet:** a virtual Ethernet switch presented to the operating system as a normal network interface.

An application sends an IP packet to a managed virtual subnet. The operating system routes it into the ZeroTier interface; ZeroTier carries the virtual Ethernet frame inside an encrypted VL1 packet over the physical network, normally UDP. The destination injects the recovered frame into its own virtual interface.

## Identity and configuration

- **Node ID:** a 10-hex-digit identifier derived from the node's cryptographic identity. It is not the assigned virtual IP.
- **Network ID:** a 16-hex-digit identifier. Its first 10 digits identify the network's Controller node.
- **Controller:** admits members and issues network configuration, membership credentials, virtual IPs, routes, and rules. It is control plane, not the default data path.
- **Root/Planet:** stable infrastructure used for identity lookup, rendezvous, and initial forwarding. It can relay encrypted traffic when a direct path is unavailable.
- **Peer/Leaf:** another endpoint, server, or controller node known to the local node.

## Path establishment

1. Nodes contact Roots and learn enough information to find peers.
2. Roots provide rendezvous hints for reachable physical endpoints.
3. Both nodes send probes, often creating NAT mappings by UDP hole punching.
4. When this works, data changes to `DIRECT` peer-to-peer transport.
5. When it does not, communication may remain `RELAY`; the nodes keep retrying direct connectivity.
6. If UDP is unavailable and TCP fallback is allowed, node status may become `TUNNELED`, normally with worse performance.

Data remains end-to-end encrypted even when a Root or relay forwards it. Authorization and encryption do not mean the endpoint itself is trustworthy: access still depends on membership, distributed rules, host firewalls, and application authentication.

## Output interpretation

| Evidence | Meaning | Does not prove |
|---|---|---|
| CLI binary and version | Client artifacts exist | Daemon or network is healthy |
| Service manager says running | Daemon process is scheduled/running | Local API, roots, or membership works |
| `info ... ONLINE` | Root infrastructure is reachable | Any network has been joined |
| `listnetworks ... OK` | Membership/configuration is active | Every peer is direct |
| Assigned address + route | Traffic for that subnet can enter the overlay | Default Internet traffic uses ZeroTier |
| Peer `DIRECT` | That peer currently has a direct path | All peers are direct |
| Peer `RELAY` | That peer currently uses encrypted relaying | The whole node is offline |
| `tcpFallbackActive=false` | TCP fallback is not active | No individual peer is relayed |

## Primary references

- Protocol and VL1/VL2: <https://docs.zerotier.com/protocol/>
- Controller responsibility: <https://docs.zerotier.com/what-is-a-controller/>
- Client and virtual ports: <https://docs.zerotier.com/config/>
- CLI status and peers: <https://docs.zerotier.com/cli/>
- TCP fallback relay: <https://docs.zerotier.com/relay/>
