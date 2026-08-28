# Knowledge-to-Presentation Content Contract

Use this reference when the deck explains a technical mechanism, includes mathematics, or needs timed speaker notes.

## 1. Communication job

Write one sentence before slide planning:

```text
By the end, <audience> should understand/decide/do <outcome> because <central takeaway>.
```

Match depth to the audience without changing the truth. A general audience needs fewer symbols, not vague claims.

## 2. Universal technical coordinates

For robot learning and ML, a compact comparison table can use:

| Coordinate | Question |
|---|---|
| Conditions | What does the model know? |
| Prediction | What must it output? |
| Representation | How is information encoded and combined? |
| Objective | What scalar pressure changes parameters? |
| Data stage | Where does capability come from? |
| Inference | How does the trained model generate a result? |
| Evaluation | What observation could reject the claim? |

Use only coordinates that advance the current presentation.

## 3. Accessible-math contract

For each formula:

1. define every symbol and shape;
2. state what is fixed, learned, sampled, or integrated;
3. identify the prediction target;
4. say which parameters receive gradients;
5. give one edge case or tiny example;
6. state what lower loss guarantees and what it does not;
7. distinguish training from inference.

### Example: why a point estimate can fail

If left and right actions are equally valid, encode them as `-1` and `+1`. A model forced to output one number `y` under squared error has:

```text
L(y) = 1/2[(y-1)^2 + (y+1)^2] = y^2 + 1
```

The minimum is `y=0`. The arithmetic is correct, but straight ahead may be physically invalid. This motivates a conditional distribution or random latent. Preserve the boundary: squared loss itself is not the problem when noise/time conditioning lets the model represent a distribution.

## 4. Slide compression contract

For each slide, record privately:

```text
Narrative job:
Primary claim:
Minimum evidence:
Audience takeaway:
What moves to speaker notes:
```

Prefer one claim plus one visual structure. Remove repeated definitions, inventories of model names, and claims that do not affect the conclusion.

## 5. Speaker-notes template

Use only relevant sections; do not fill headings mechanically.

```text
[本页一句话]
<one-sentence mechanism>

[给爷爷奶奶的一句话]
<everyday analogy that preserves causality>

[符号账本]
<symbol: meaning, type/shape, fixed/learned/random, units>

[最小数学]
<minimum equation and definitions>

[公式怎样推动学习]
<target → loss → gradient → parameter change → observable behavior>

[5分钟基础稿｜本页约N秒]
<complete short-talk segment>

[10分钟扩展｜在基础稿后追加约M秒]
<derivation, caveat, experiment, or train/inference detail>

[理解检查]
<prediction or falsifiable question>

[Sources]
- <source>: <specific contribution>
```

## 6. Timing budgets

For a five-slide deck, starting allocations are:

| Slide role | 5-minute base | 10-minute extension |
|---|---:|---:|
| Opening thesis | 35–45 s | +30–45 s |
| Core tension/example | 55–70 s | +50–70 s |
| Main mechanism | 65–85 s | +70–95 s |
| Implementation/contract | 50–65 s | +45–65 s |
| Evaluation/closure | 50–65 s | +45–65 s |

Adjust for the topic, but verify the sum. The extended mode should reuse the base talk and add depth, not create a conflicting second story.

## 7. Source annotation

Good:

```text
- <Obsidian knowledge note>: defines the unified model and current decision boundary.
- <implementation Skill>: supplies the exact rollout funnel and failure taxonomy.
- <primary paper>: supports the public architecture claim; local behavior remains unverified.
```

Weak:

```text
- /path/to/file.md
- https://example.com/paper
```

If a source supports only a hypothesis, label it as such. Do not promote a personal note to primary-paper evidence.

## 8. Final checks

- Can a non-expert explain the main idea using the analogy?
- Can a technical listener reconstruct the variables and objective?
- Does each formula predict a failure mode or experiment?
- Are train-time and inference-time procedures separated?
- Do source annotations identify contributions?
- Are scripts timed across the whole deck?
- Did the exported PPTX retain the notes and preserve the visible design?

