# Literature-discovery prompt patterns

Use these patterns to turn a topic into a reproducible search request. Keep the variables explicit; do not hide scope decisions inside vague phrases such as “核心论文” or “最新高被引”.

## What a complete prompt must specify

1. **Topic and mechanism:** the material/system plus the physical mechanism or research question.
2. **Exact time window:** concrete years, not only “近几年”.
3. **Included evidence:** primary research, accepted/preprint policy, language, experiment/theory balance, and required access level.
4. **Exclusions:** reviews, unrelated applications, composites, patents, theses, or weakly related mechanisms as appropriate.
5. **Verification:** primary metadata source, DOI/arXiv, version status, and retrieval date.
6. **Screening:** target count, explicit inclusion/exclusion reason, deduplication, and coverage clusters.
7. **Metrics:** source and date for any citation signal; metrics must not be the sole selection rule.
8. **Output:** query log, candidate matrix, selected set, limitations, and downstream handoff.

## Recommended staged prompts

### Stage 1 — Freeze scope

```text
使用 $literature-discovery。围绕“<topic>”先冻结检索协议，不开始筛选。
时间范围：<start-year>–<end-year>。
请定义核心概念、同义词、纳入/排除标准、预印本规则、语言范围、
实验/理论覆盖目标，以及“核心论文”的判定维度。把仍需用户确认的歧义单列出来。
```

### Stage 2 — Retrieve and verify candidates

```text
按已冻结协议执行广检索。至少使用两个互补学术来源，并从强种子论文做前向/后向追踪。
记录每条原始检索式、来源、过滤条件、检索日期和结果数；来源不提供结果数时写 unknown。
每个候选先核验题名、作者、年份、期刊/会议、出版状态和 DOI/arXiv。
搜索结果摘要只能发现候选，不能作为最终元数据证据。禁止虚构缺失字段。
```

### Stage 3 — Screen, deduplicate, and select

```text
对候选按 DOI、题名和版本关系去重。逐条给出 include/exclude/maybe/unavailable
以及具体理由。按主题相关性、机制覆盖、证据质量和领域影响筛选最多 <N> 篇，
不要为了凑数纳入弱相关论文。引用次数必须注明数据库和查询日期。
```

### Stage 4 — Produce the handoff

```text
输出检索范围、query log、候选矩阵、最终核心集、机制聚类、排除项和检索局限。
候选矩阵使用 literature-candidate-matrix.csv 字段；为后续 $paper-deep-analysis
保留稳定标识符、落地页、全文链接、screen_decision 和 version_of。
```

## One-shot prompt

Use this only when the scope is already sufficiently clear:

```text
使用 $literature-discovery，围绕“<topic>”检索 <start-year>–<end-year> 的核心文献。
范围包括：<included mechanisms / evidence>；排除：<exclusions>。
至少检索两个互补学术来源，并对强种子论文做前向/后向追踪。
逐篇从出版社、会议、DOI 注册机构或官方预印本记录核验题名、作者、年份、
出版状态和 DOI/arXiv；禁止根据搜索摘要补造信息。
先输出完整 query log 和去重后的候选矩阵，再按主题相关性、方法覆盖、证据质量
和注明来源/日期的影响信号筛选最多 <N> 篇。每篇给出一句纳入理由；所有排除项
给出具体理由。若合格论文不足 <N> 篇，报告缺口而不是补齐。
最后说明数据库覆盖、语言、全文访问、版本和 citation signal 的局限，并生成可交给
$paper-deep-analysis 的 literature-candidate-matrix.csv。
```

## Prompt-quality check

Reject or repair a prompt when it:

- asks for “最权威/最高引用” without naming a metric source and date;
- requests an exact paper count but forbids reporting a shortfall;
- mixes discovery, full-text analysis, gap claims, and final prose into one untraceable step;
- asks the model to fill missing metadata from memory;
- uses “近 3–5 年” without converting it to exact calendar years;
- treats a review, search snippet, or citation-manager record as proof of a primary-study claim.
