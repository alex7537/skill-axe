# Supervised Loop

Use this mode for multi-stage work that should be resumable across turns but must remain under the current agent and authorization boundary.

## Runtime files

The runtime lives under `<project>/.codex/skill-chef/`:

- `mise.json` — objective, authorization mode, current runtime status, and recent history;
- `orders-next.json` — proposed orders written by the agent;
- `orders.json` — validated, promoted orders and stage lifecycle state.

Runtime files are project state, not permission. Do not initialize them for a read-only request unless the user asked for persistent tracking.

## Lifecycle

1. Initialize once:

   ```powershell
   ./scripts/chef_runtime.ps1 -Action Init -ProjectRoot <project> -Objective <goal> -Mode read-only
   ```

2. Write `orders-next.json` using the schema below. Never write `orders.json` directly.
3. Validate, then promote:

   ```powershell
   ./scripts/chef_runtime.ps1 -Action Validate -ProjectRoot <project>
   ./scripts/chef_runtime.ps1 -Action Promote -ProjectRoot <project>
   ```

4. Read the next stage, start it, perform the work with the selected Skill and tool, then record completion or failure:

   ```powershell
   ./scripts/chef_runtime.ps1 -Action Next -ProjectRoot <project>
   ./scripts/chef_runtime.ps1 -Action Start -ProjectRoot <project>
   ./scripts/chef_runtime.ps1 -Action Complete -ProjectRoot <project> -Result <evidence-summary>
   ```

5. Inspect status whenever resuming:

   ```powershell
   ./scripts/chef_runtime.ps1 -Action Status -ProjectRoot <project>
   ```

## Proposal schema

```json
{
  "orders": [
    {
      "id": "inspect-and-fix",
      "title": "Inspect, change, and verify the target",
      "rationale": "The verified dependency path requires these stages",
      "stages": [
        {
          "id": "inspect",
          "skill": "code-understanding-coach",
          "deliverable": "Verified cause and affected path",
          "evidence": "Source trace and focused reproduction",
          "mutation": "none",
          "group": 0
        }
      ]
    }
  ]
}
```

Valid mutations are `none`, `local`, and `external`. The runtime rejects local mutation in `read-only` mode and external mutation unless the mode is `external-mutation`. Groups are recorded for dependency planning but do not cause parallel execution.

## Boundaries

- This is a state machine and validation layer, not an autonomous scheduler.
- The agent still chooses tools, performs each stage, and supplies real evidence.
- No background process, automatic retry, worktree creation, merge, subagent, commit, push, or external action is implied.
- On failure, record the reason. Do not retry more than once without new evidence; split or reschedule the stage instead.

This adapts Noodle's `mise → orders-next → validate/promote → lifecycle` separation while keeping execution supervised and Windows-local.
