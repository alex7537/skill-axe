# The 9 Skill Categories

Cataloged from hundreds of skills in active use at Anthropic. The best skills fit cleanly into one category; ones that straddle several become confusing — split them.

## 1. Library & API Reference
How to correctly use a library, CLI, or SDK — internal libraries, or public ones Claude sometimes fumbles. Typically includes a folder of reference code snippets plus a gotchas list.
Examples: `billing-lib`, `internal-platform-cli`, `frontend-design`

## 2. Product Verification
How to test or verify code is actually working, usually paired with an external tool (Playwright, tmux, ...). Extremely high ROI — worth having an engineer spend a week making these excellent, since they gate the correctness of everything else the agent produces.
Examples: `signup-flow-driver`, `checkout-verifier`, `tmux-cli-driver`

## 3. Data Fetching & Analysis
Connects the agent to data and monitoring stacks: fetch libraries with credentials, specific dashboard IDs, common query workflows.
Examples: `funnel-query`, `cohort-compare`, `grafana`

## 4. Business Process & Team Automation
Repetitive workflows collapsed into one command. Simple instructions, but may depend on other skills or MCPs. Saving previous results in log files helps the model stay consistent and reflect on past executions.
Examples: `standup-post`, `create-ticket`, `weekly-recap`

## 5. Code Scaffolding & Templates
Generate framework boilerplate for a specific function in the codebase, often combined with composable scripts. Best when scaffolding has natural-language requirements code alone can't cover.
Examples: `new-workflow`, `new-migration`, `create-app`

## 6. Code Quality & Review
Enforce org code quality and assist review. Include deterministic scripts/tools for robustness; consider running automatically via hooks or GitHub Actions.
Examples: `adversarial-review`, `code-style`, `testing-practices`

## 7. CI/CD & Deployment
Fetch, push, and deploy code. May reference other skills to collect data.
Examples: `babysit-pr`, `deploy-<service>`, `cherry-pick-prod`

## 8. Runbooks
Take a symptom (Slack thread, alert, error signature), walk a multi-tool investigation, produce a structured report.
Examples: `<service>-debugging`, `oncall-runner`, `log-correlator`

## 9. Infrastructure Operations
Routine maintenance and operational procedures — some destructive, benefiting from guardrails (pair with on-demand hooks). Helps engineers follow best practices in critical operations.
Examples: `<resource>-orphans`, `dependency-management`, `cost-investigation`
