---
name: masterarbeit-search
description: Find and triage current Masterarbeit opportunities for this LUH Mechatronik und Robotik student. Use when the user says “查看今天的大论文机会”, asks for a Masterarbeit search sprint, wants thesis openings, or needs application priorities; do not use for generic job hunting or CAD/geometry-only topics.
---

# Masterarbeit Search

Maintain a small, current opportunity pipeline for the user’s Masterarbeit. The primary technical profile is Robot Learning, Embodied AI, robotic manipulation, VLA, imitation/reinforcement learning, Flow Matching/Diffusion Policy, Isaac/Sim2Real, and robot-policy deployment/evaluation. Treat CAD/Geometry as a possible side route only—not a search theme.

## Search and rank

1. First verify that each listed opening is live on its official employer, research-institute, or LUH page. Do not recycle expired roles or report an old listing as current.
2. Search in this order:
   - South-Germany companies: Stuttgart, München, Augsburg, Ulm, Karlsruhe and nearby R&D sites.
   - Applied research: Fraunhofer (especially IPA), ARENA2036, IPH and comparable robotics/manufacturing institutes.
   - LUH-internal opportunities as the deliberate fallback.
3. Prefer a problem with a scientific core and a plausible six-month experimental loop over a generic software task. Score evidence of data/hardware access, research fit, supervision feasibility, technical fit, and realistic scope.
4. For an external opportunity, make the LUH-supervision question explicit early: a named company supervisor, alignment with the LUH institute, a jointly agreed scientific question, and LUH examination must be feasible before a company agreement is treated as secure.

## Feedback-driven refinement

Before a new batch, read the user’s `Masterarbeit_Action_Board.md` in `20_Research/研究机会/`, especially **“你的偏好与搜索反馈”**, and the latest daily notes’ **“我的评论 / 注释”** sections. Treat actual user-entered feedback as the current ranking evidence:

- cities, start windows, language limits, and role type can be hard filters;
- stated interests, liked technical ingredients, and willingness to apply should increase priority;
- stated dislikes or concerns should down-rank or exclude similar roles;
- empty template fields are not evidence—do not invent preferences from them.

When a meaningful preference changed the ranking, state the adjustment in one concise sentence. Give every new opportunity the same short `我的评论 / 注释` block so the next batch can improve.

## Daily output contract

- Return 3–5 highest-priority, non-duplicate opportunities in chat; if fewer are verified, say so rather than padding the list. Every daily search must also create or update the Obsidian daily note in the same turn, including when there are no new opportunities.
- For each item give: organization/location, live source link, technical fit, why it ranks here, pipeline state, and one concrete next action formatted as `- [ ] ...`.
- Follow the action with a compact user-feedback block: `喜欢度（1–5）`, `最吸引我的点`, `担忧 / 不想做的部分`, and `我愿意的下一步`.
- Keep the wording compact enough to act on today. Do not dump a broad directory or repeat settled background.
- Preserve evidence-backed states, including existing `Candidate`, `Review/Apply 优先`, and `Candidate/Review` labels. Use `Submitted` for a user-confirmed completed application; application priority or prepared materials alone are not submission evidence. Do not downgrade a submitted role to Found/Review or infer a submission date.
- Flag an item as `Needs LUH supervision check` until the academic arrangement is confirmed. A company offer alone is not a registered thesis.

## Required Obsidian daily record

- Fixed directory: `/Users/<user>/Documents/Obsidian Vault/20_Research/研究机会/`.
- Filename: `YYYY-MM-DD_Masterarbeit_Search_Daily.md`, using the user's local calendar date (or the explicit requested date).
- Before writing, read the existing daily note, action board, and relevant earlier entries. Match openings by official URL/job ID plus employer and topic; distinguish IGCV VLA manipulation from IGCV LLM manipulation.
- Create or update one note per date in the same operation as the chat output. Preserve user comments, checked actions, and unrelated content; merge repeated runs without duplicate opportunity blocks.
- Include `今日重点`, an ordered opportunity list, and `今日完成情况`. Every opportunity needs type, city, title, current official link and verification date, fit to all three project repositories, state, and one concrete unchecked `- [ ]` next step. Keep the compact user-feedback block above.
- Include `已投递状态更新`: update matching existing overview/action-board/daily entries in place when the user confirms submission, preserve `Submitted`, and link back rather than create another candidate. Record no change when there is no new submission evidence; never invent dates or completed actions.
- If there are no high-priority new opportunities, still write a short note saying **“无高优先级新机会”**, with focus, any state updates, and completion summary. Do not repeat old openings to fill the quota; link an existing candidate only if needed for a follow-up action.
- Read back the saved note and status changes before reporting success; return the actual daily-note and skill paths when relevant. If writing is blocked, report the blocker rather than claiming the note was saved.
- This is a per-invocation persistence rule, not a scheduled job. Do not create an automation unless separately requested.

## User-specific evidence to reuse

Frame relevant applications with three repositories, without exposing confidential material:

- `<github-owner>/flow-matching-test-a2d-v2`: robot-learning training, Flow Matching / policy modeling.
- `<github-owner>/fk-issac-logistics`: Isaac, deployment and closed-loop / Sim2Real-oriented work.
- `<github-owner>/a2d-eval`: policy evaluation, rollout evidence and failure analysis.

The durable plan and checklist live in `20_Research/研究机会/2026-09-21_Masterarbeit_Search_Sprint.md` in the user’s Obsidian Vault. Update it when the user asks to record progress.

## Boundaries and gotchas

- Do not create a fixed-duration automation unless the user explicitly asks for one; use the user-maintained daily action board instead.
- Current openings and university rules are time-sensitive: verify official sources before presenting them as facts.
- Do not promise that FEI, BauGeo, or any institute can serve as examiner merely because the program is interdisciplinary. Check the applicable PO, the examination office, and the prospective institute for the individual thesis.
