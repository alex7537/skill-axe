---
name: feishu-cli-multi-account-auth
description: "Set up, repair, and verify separate Feishu/Lark CLI user authorizations for company and personal accounts. Use for 第二个账号授权、多账号 CLI、公司到个人备份前接入、personal profile, or '没有应用使用权限' during login. Covers app/tenant mismatch and persisted OAuth login; does not itself authorize document migration, sharing, or permission changes."
---

# Feishu CLI Multi-account Auth

Runbook for keeping two independently verified user identities in `lark-cli`. Read the installed `lark-cli skills read lark-shared` and relevant command `--help`; CLI behavior and available flags vary by version.

## Establish the identity map

Use `profile list`, `auth list`, and explicit-profile `auth status --json --verify` to distinguish:

| Evidence | What it proves |
| --- | --- |
| Profile name | Local routing label only; `personal` does not prove personal tenancy |
| App ID and app name | Which application receives the OAuth grant; names can be identical |
| Developer console organization, app ID, owner, publication state | Whether the application belongs to the intended organization and who controls it |
| `identities.bot.verified` | Application credentials work; not proof of user login |
| `identities.user.available`, `verified`, `openId`, scope set | User authorization exists and was verified for this profile |

Record a concise source/target map with organization, profile, app ID, and API-returned user identity. UI display names can differ from API names. Open IDs are app-scoped; use organization evidence too. Do not infer tenancy from a matching name or from the currently selected desktop identity. Desktop and CLI identity selection are independent.

Check the full actual grant, but report only materially relevant permissions. `auth scopes` lists app-available scopes; it is not evidence of an effective user grant. Top-level `verified: true` can refer only to bot verification when user login is missing.

## Diagnose before requesting more scopes

- **“没有应用使用权限”, personal identity unavailable, company identity selectable:** this is an application availability/organization problem before document-scope consent. Do not select the company identity to finish a personal-account login. Inspect the exact target App ID in the developer console under the intended organization. A company-only app may have been created because the browser was using the company identity during initialization.
- **Application configured, user `missing`:** credentials were saved but user OAuth was not completed. A ready bot does not solve this.
- **User grant missing a scope:** request only the missing task-relevant scope after authorization to expand access.
- **Specific document denied despite scopes:** resource ACL or organization policy is separate. Do not change identity to evade denial.
- **Keychain not initialized inside sandbox:** try the same authorized operation with permitted access to the OS keychain. Do not automatically downgrade keychain storage, erase configuration, or reinitialize credentials.

## Bind the correct application without losing the first account

Inventory existing profiles and preserve their app IDs and user identities. Leave the default profile unchanged unless the user asks to change it. Use explicit `--profile` on every subsequent command.

Prefer an existing suitable application owned by the user in the intended organization. Verify its exact App ID, owner and published/enabled state before binding. If none exists, prepare the official creation flow and have the user select the correct organization; do not assume creation implies user consent was completed.

Current supported setup patterns (check help first):

```bash
# Named configuration appends/updates this profile instead of replacing the default.
lark-cli config init --new --name personal

# Bind an existing application; supply the secret securely through stdin.
lark-cli config init --name personal --app-id <verified-app-id> --app-secret-stdin --brand feishu
```

Do not put secrets in command arguments, echoed terminal input, committed files, skills, or reports. Prefer a no-echo prompt feeding subprocess stdin. Do not broadly extract browser cookies or credential stores. If a secret appeared in a screenshot/tool result, do not repeat or persist it; recommend rotation without rotating it unasked.

Do not silently widen app availability, publish a new app version, or grant users access. Prepare the exact change and follow the applicable confirmation requirements. Local profile repair alone need not modify cloud permissions.

## Complete user OAuth and persist it

For ordinary Docx backup preparation, the narrow initial set verified in this workflow was:

```bash
lark-cli --profile personal auth login \
  --scope 'docx:document:readonly docx:document:create docx:document:write_only offline_access' \
  --no-wait --json
```

This is a starting set, not a universal migration contract. Images, attachments, folder placement, native copy, import/export, Sheets or Base may require more. Do not request all business domains merely because the eventual goal is backup.

Send the freshly returned verification URL unchanged, generate and display its QR code with `auth qrcode`, and ask the user to select the intended organization. Let the user complete consent. On their reply, finish the same flow:

```bash
lark-cli --profile personal auth login --device-code <current-flow-device-code>
```

The no-wait initiation alone does not persist a user token. Do not end the process at browser success: the agent must exchange the device code and verify storage. Do not reuse expired links/codes, store them in durable artifacts, or restart an active flow repeatedly. For expiration, issue a new flow with the same intended scopes.

## Acceptance checks

```bash
lark-cli --profile personal auth status --json --verify
lark-cli --profile personal auth check \
  --scope 'docx:document:readonly docx:document:create docx:document:write_only offline_access' --json
lark-cli --profile <source-profile> auth status --json --verify
lark-cli profile list
```

Require user-level verification, the intended API user, no missing required scopes, both saved profiles, and preservation of the source login/default selection. A pre-refresh `needs_refresh` label accompanied by successful server verification after refresh is not an authentication failure.

Inspect the full post-login scope list: cumulative grants may exceed this request, including document deletion or permission management. Report that fact rather than claiming the account has only the newly requested minimal set. Do not automatically revoke existing scopes.

No probe writes are needed to verify OAuth. Report precisely: two user authorizations verified; document migration remains untested. Cross-account copy is not guaranteed by two valid logins: a target-side native copy still needs source visibility, and source-read/target-create may require content reconstruction and media handling. Check actual resources when the user supplies a migration task.

Before document writes, follow the user's current Feishu rules: exact target, owner and effective permission checks for existing resources; explicit creation authorization for new resources; separate confirmation where required for non-owned targets, sharing, ownership transfer or bulk operations; fresh readback after writes. Account setup is not blanket authorization to transfer company documents.

## Verified boundary

This runbook was exercised through dual-profile persistence, correct personal-organization app binding, device-code completion, server verification of both users, and required-scope checks. It does not claim a successful cross-account document copy, preservation of formatting/media, or migration of comments/history.
