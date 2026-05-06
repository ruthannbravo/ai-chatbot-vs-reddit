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

## File inventory

- `reddit_sample.csv` — 1,500 Reddit advice-forum opening posts
- `wildchat_sample.csv` — 1,500 WildChat first user turns
- `data_notes.md` — this file

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

> ⚠ **Schema mismatch to resolve:** Reddit uses `created_utc` + `created_datetime`; WildChat uses `timestamp`. Unify before running side-by-side time-based analysis.

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
- **Deduplication (2026-04-25):** WildChat sample contained 3 exact-duplicate rows (same `id`, identical text — likely an upstream sampling glitch). The source CSV is left unmodified; classification and analysis dedupe to the first occurrence. Effective N for analysis: 1,497 WildChat + 1,500 Reddit = **2,997 messages**.

## Limitations & caveats

- **Temporal mismatch is the biggest threat to the research question.** Reddit is 2009–2013; WildChat is 2023–2024. Any difference in "emotional/personal" proportion could reflect *era* (life in 2012 vs. 2024) rather than *venue* (Reddit vs. AI). Worth discussing explicitly in any writeup.
- **Neither sample is population-representative.** WildChat users and these four subreddits' posters are self-selected subgroups. Findings describe those subgroups, not "people in general" or even "all AI users" / "all Reddit users."
- **Subreddit substitution.** r/AskReddit and r/Advice were not available in the upstream dataset, so four advice-adjacent subreddits were used. The proportion of emotional/personal content may be sensitive to this choice — repeating the analysis with different subreddit picks would test robustness.
- **"Emotional/personal" is not yet operationally defined.** The research question depends on a classification scheme (human-coded, keyword-based, or model-scored). Document the definition and method here once chosen, since the headline result rises or falls with it.

## Reproducibility

- **Random seed:** `42` (both samples)
- **Collection date:** 2026-04-23
- Upstream datasets are public and versioned on Hugging Face. Dataset revision hashes are not recorded here — add them if exact reproducibility becomes important.
