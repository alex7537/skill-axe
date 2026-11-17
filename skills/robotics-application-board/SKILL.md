---
name: robotics-application-board
description: Update the user's public GitHub Pages Masterarbeit and AI robotics application board after an application, reply, interview, rejection, offer, follow-up, or networking change. Use when the user says they submitted an application, received a status change, or asks to record or update the board. Do not use for merely discussing or discovering roles unless the user wants them recorded.
---

# Robotics Application Board

Maintain the canonical application data in `applications.json`, LUH professor/project outreach data in `luh.json`, and both local-file fallback snapshots in `index.html` in the public GitHub repository `alex7537/robotics-application-board`. The published board is `https://alex7537.github.io/robotics-application-board/`.

## Decide whether to write

- Treat statements such as “I applied to…”, “I submitted my CV”, “they invited me to interview”, “I was rejected”, or “update the board” as intent to record the event.
- When the user is only evaluating, browsing, or preparing an application, do not mutate the board. Offer a preview or ask whether they want the opportunity recorded as `Found`.
- GitHub mutations remain scoped to this repository and the requested application record. Never change repository visibility, Pages settings, or unrelated files without a separate user request.
- The repository and site are public. Never store résumé files, home addresses, phone numbers, private email addresses, application portal credentials, private message contents, or other non-public personal data. Summarize notes in public-safe language. A public job-posting URL and a contact's public professional name are acceptable when useful.

## Read before changing

Read the latest `applications.json` from the repository's default branch immediately before each update. Preserve all unrelated records and fields. Match an existing record by normalized organization and title; if the match is ambiguous, ask one concise question instead of creating a duplicate.

For LUH professor contact, thesis-topic review, or university-project updates, read and update `luh.json` instead. Preserve evidence levels: use `Discovered` for newly found material, `Reviewed` when the user has evaluated it, `Contacted` only when sending is confirmed, `Replied` only with a confirmed response, and `Follow-up` when a concrete next contact is due.

## Record an application event

For a new record, require enough information to identify the organization and role. Infer other fields conservatively from the user's message or supplied job posting.

- Default `status` to `Applied` when the user says the application was submitted. Use `Waiting` only when they explicitly describe waiting after submission or ask for that status.
- Set `applied_date` to the user-provided date; otherwise use the current client-local date for a newly submitted application.
- Set `last_contact` when the event is a reply, interview invitation, rejection, offer, or other direct contact.
- Use `record_type: "application"` for formal applications and `record_type: "networking"` for prospecting or connection activity.
- Allowed `category` values are `company`, `applied-research`, and `LUH`.
- Allowed `status` values are `Found`, `Applied`, `Waiting`, `Interview`, `Rejected`, `Offer`, and `Closed`.
- Allowed `priority` values are `High`, `Medium`, and `Low`; default to `Medium` if the user gives no useful priority signal.
- Use stable lowercase hyphenated IDs based on organization and title. If the ID already exists, add a short disambiguating suffix.
- Keep unknown scalar fields as empty strings rather than inventing names, dates, links, or locations.
- Store `technical_focus` as a JSON array of concise terms.

Every record should preserve this field set:

`id`, `organization`, `city`, `title`, `category`, `technical_focus`, `status`, `applied_date`, `last_contact`, `next_action`, `application_link`, `contact_person`, `contact_channel`, `notes`, `priority`, and `record_type`.

## Commit safely

Validate that each edited JSON file has an array root. After changing `applications.json` or `luh.json`, synchronize the corresponding `fallbackData` or `luhFallbackData` block in `index.html`. When a local checkout is available, run `scripts/sync_fallback.py <repository-directory>` from this Skill; otherwise perform the equivalent exact replacement through the GitHub tools. Do not change other HTML.

Commit both files in one change directly to the default branch with a concise message such as `Record BMW robotics application` or `Update Fraunhofer IGCV status to interview`. Verify that the commit contains `applications.json` and `index.html` and that their application arrays are identical.

The hosted page already fetches `applications.json` with `cache: "no-store"`, so a hosted copy reflects the new data on refresh. The synchronized HTML fallback is for direct local-file opening; a previously downloaded local `index.html` still needs to be downloaded or pulled again to receive the new embedded snapshot.

After a successful update, report the organization, role, new status, date used, and the published board link. GitHub Pages deploys automatically from `main`; users normally only need to refresh after the deployment finishes. If a GitHub write fails, leave local/user data intact and report the exact failed step; do not retry by overwriting the whole repository.
