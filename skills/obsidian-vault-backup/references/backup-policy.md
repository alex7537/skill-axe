# Obsidian backup policy

## What “current” means

| Mode | Trigger | Trade-off |
|---|---|---|
| Reviewed checkpoint | Invoke the skill after meaningful work | Safest history; not automatic |
| End-of-session | One backup when a work session closes | Good default for research notes |
| Periodic archive | `launchd` checks every 15–30 minutes | More current, but can capture half-written notes |
| Real-time file sync | Obsidian Sync or a file-sync product | Fast propagation, not semantic Git history |

Git should normally own reviewed history; use a sync product when the requirement is second-by-second device synchronization.

## Default content policy

Eligible by default:

- Markdown and other configured text knowledge artifacts;
- modifications/deletions of already tracked attachments below the size limit;
- new text notes after high-confidence secret scanning.

Require explicit opt-in:

- stable `.obsidian` preferences;
- new binary attachments;
- files near provider size limits;
- branch changes or reconciliation after another device pushed.

Always deny:

- `.obsidian/workspace*.json`;
- `.obsidian/plugins/` and plugin-local data;
- `.claudian/`, `.trash/`, `.backup_*/`, `.git/`;
- `.env`, `.netrc`, private keys, auth-bearing URLs, and detected credentials.

## Periodic automation gate

Do not install a scheduler until the user approves:

1. exact Vault and remote branch;
2. cadence and off-hours behavior;
3. text/binary and `.obsidian` inclusion policy;
4. commit-message format;
5. behavior when dirty changes fail scanning;
6. notification and pause/removal procedure.

An automated job must preview with the same script, acquire a single local lock, skip when the branch is behind/diverged, and fail closed on sensitive or oversized files. It must never auto-rebase, resolve conflicts, force-push, or change remote visibility.

## Recovery boundary

Verify recovery separately by cloning the remote into a temporary directory and checking Markdown count, critical indexes, attachments, and Git history. A successful push proves transport, not complete recovery of ignored Obsidian/plugin state.
