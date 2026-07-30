# Data Collection Notes

## Overview

This project compares AI-chatbot first-turn messages (WildChat) against Reddit advice-forum opening posts.

**Research question:** Do people bring more emotional/personal problems to AI than to human-advice communities, or vice versa?

**Operationalized as:** Among first-turn messages to a general-purpose chatbot (WildChat) versus opening posts on public Reddit advice forums, what proportion of each are emotional/personal in nature, and do the distributions differ?

## Dates

- **Collection date:** 2026-04-23 (when these samples were drawn)
- **Reddit data range:** 2009-06-20 to 2013-02-25 (UTC) — when the posts were actually written
- **WildChat data range:** 2023–2024

*Collection date ≠ data date range. The first is when you pulled the sample; the second is when the content was created.*

## Scope of this file

This file documents the two **raw upstream samples** and how they were drawn. Neither is committed — both are gitignored for redistribution-licensing reasons, and must be recreated from Hugging Face using the parameters below.

- `reddit_sample.csv` — 1,500 Reddit advice-forum opening posts (not committed)
- `wildchat_sample.csv` — 1,500 WildChat first user turns (not committed)

For the full inventory of files that *are* committed, see the `## Files` section of `results.md` or the repo layout in `README.md`.

## Data dictionary

### `reddit_sample.csv` (1,500 rows)

| Column | Type | Description |
|---|---|---|
| `id` | string | Post ID (prefixed `rd_`) |
| `source` | string | Always `reddit` |
| `subreddit` | string | One of the four sampled subreddits |
| `text` | string | Submission body text |
| `word_count` | int | Number of words in `text` |
| `created_utc` | int | Post creation time, unix seconds (UTC) |
| `created_datetime` | string | Post creation time, ISO 8601 UTC (derived from `created_utc`) |

### `wildchat_sample.csv` (1,500 rows)

| Column | Type | Description |
|---|---|---|
| `id` | string | Conversation ID (prefixed `wc_`) |
| `source` | string | Always `wildchat` |
| `subreddit` | empty | N/A for WildChat; column kept for schema alignment |
| `text` | string | First user turn text |
| `word_count` | int | Number of words in `text` |
| `timestamp` | string | First-turn time, ISO 8601 UTC |

> **Note on timestamp columns:** Reddit uses `created_utc` + `created_datetime`; WildChat uses `timestamp`. These were deliberately left un-unified because no time-based analysis is in scope — the study compares proportions across sources, and neither timestamp column is read by any script in the pipeline. Anyone extending this to time-series work should unify them first.

## Sources & collection

### AI-side data
- **Source:** `allenai/WildChat-1M` on Hugging Face
- **Sample size:** 1,500 first user turns
- **Filters:** English language, 10–1000 words
- **Sampling:** random sample of 1,500 from a pool of 15,000 candidates (seed=42)

### Human-side data
- **Source:** `HuggingFaceGECLM/REDDIT_submissions` on Hugging Face
- **Reason for this dataset (not the live API):** Reddit's Responsible Builder Policy (late 2025) restricts new API access
- **Subreddits:** `relationship_advice`, `socialskills`, `personalfinance`, `LifeProTips`
- **Sample size:** 375 per subreddit = 1,500 total
- **Filters:** non-deleted, non-empty, 10–1000 words
- **Sampling:** random sample from a pool of ~1,875 candidates per subreddit (seed=42)

## Processing applied

- **Reddit:** renamed the upstream `timestamp` column (unix seconds) to `created_utc` to match Reddit's standard field name. Added a derived `created_datetime` column (ISO 8601 UTC) for readability.
- **WildChat:** no column transformations yet. `timestamp` is already an ISO 8601 UTC string from the upstream dataset.
- **Deduplication (2026-04-25):** WildChat sample contained 3 exact-duplicate rows (same `id`, identical text — likely an upstream sampling glitch). The source CSV is left unmodified; classification and analysis dedupe to the first occurrence. **N submitted to the classifier: 1,497 WildChat + 1,500 Reddit = 2,997 messages.**
- **Refusals:** 4 of the 1,497 WildChat requests returned no usable label and are absent from `predictions.csv`. **N for analysis is therefore 2,993** (1,493 WildChat + 1,500 Reddit) — this is the figure used throughout `results.md`, `research_article.md`, and the README. The two numbers are easy to confuse: 2,997 was submitted, 2,993 was analyzed.

## Limitations & caveats

- **Temporal mismatch is the biggest threat to the research question.** Reddit is 2009–2013; WildChat is 2023–2024. Any difference in "emotional/personal" proportion could reflect *era* (life in 2012 vs. 2024) rather than *venue* (Reddit vs. AI). Worth discussing explicitly in any writeup.
- **Neither sample is population-representative.** WildChat users and these four subreddits' posters are self-selected subgroups. Findings describe those subgroups, not "people in general" or even "all AI users" / "all Reddit users."
- **Subreddit substitution.** r/AskReddit and r/Advice were not available in the upstream dataset, so four advice-adjacent subreddits were used. The proportion of emotional/personal content may be sensitive to this choice — repeating the analysis with different subreddit picks would test robustness.
- **The operational definition drives the headline result.** "Emotional/personal" was ultimately split into two independent binary dimensions, Personal and Emotional, defined by a four-rule codebook — see **`coding_scheme.md`** for the locked definitions, worked examples, and change log, and `research_article.md` §3.1 for the rationale. This was resolved during the pilot (2026-04-23 to 04-25); the numbers in `results.md` rise or fall with that codebook, and a different one would give different rates. `research_article.md` §7 names the direction each plausible alternative would move them.

## Reproducibility

- **Random seed:** `42` (both samples); `7` for the 40-row pilot draw
- **Collection date:** 2026-04-23
- **Known gap — the sampling script was not committed.** Only its outputs were kept (`pilot_coding.csv`, plus the two gitignored sample CSVs). Recreating the raw samples means writing a loader against the parameters in "Sources & collection" above, and a seed alone does not pin row selection across different implementations — `random.sample` and `datasets.shuffle` seeded identically will not agree.
- **Known gap — upstream revision hashes were not pinned.** Both datasets are public and versioned on Hugging Face, but the specific revisions used were not recorded, so a fresh pull may not contain exactly the same rows.

Taken together, these mean a from-scratch rebuild of `predictions.csv` is approximate. Verification of the published analysis is exact and requires neither gap to be closed: `analyze.py` runs off the committed `predictions.csv`, and `classify.py` validates against the committed `pilot_coding.csv`.
