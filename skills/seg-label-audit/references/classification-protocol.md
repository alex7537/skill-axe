# Label classification protocol

| Classification | Evidence standard | Default action |
|---|---|---|
| `valid_nonempty` | Target identity and spatial annotation are trusted | Eligible positive |
| `true_empty` | Scene legitimately contains no target under the label contract | Eligible negative; score separately |
| `confirmed_missing` | Target is visible under the contract but annotation is absent | Quarantine; relabel |
| `partial_annotation_hole` | Only a known interval lacks otherwise valid labels | Exclude interval; keep valid frames |
| `boundary_ambiguous` | Target identity or propagated label is unreliable near a task/clip boundary | Diagnostic or quarantine |
| `multi_instance_ambiguous` | Multiple IDs conflict with single-target semantics | Resolve contract before binarizing |
| `corrupt_or_unreadable` | RGB/mask is unreadable, misaligned, or out of bounds | Quarantine and repair source |

## Evidence bundle

Include stable sample/frame identity, RGB, raw GT, binary GT, overlay, preceding/following frames, and the rule version. Add probability/prediction only as secondary evidence.

For zero runs, ask:

1. Does the target remain visible under the task definition?
2. Does the zero run align with a clip, merge, or propagation boundary?
3. Do trusted labels exist immediately before and after the run?
4. Is target identity already established at this point in the task?
5. Is there a legal no-target state in deployment?

Use explicit confidence such as `confirmed`, `probable`, or `ambiguous`. Do not collapse probable and confirmed decisions merely to increase training data.

## Valid-frame rule

Version the rule that converts frame decisions into an allowlist. Record valid and invalid ranges with reasons. Training samplers and evaluation loaders must consume the frozen allowlist instead of rediscovering validity independently.
