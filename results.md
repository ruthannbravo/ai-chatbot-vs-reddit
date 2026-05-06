# Final Classification Results

**Date completed:** 2026-04-25
**Sample:** 2,997 messages — 1,500 Reddit advice posts + 1,497 WildChat first turns (3 WildChat duplicates dropped; 4 WildChat refusals returned no usable label, so analysis N = 2,993)
**Codebook:** `coding_scheme.md` — 2 binary dimensions (Personal, Emotional) + 4 rules
**Classifier:** Claude Sonnet 4.6 via Anthropic Batch API; system prompt mirrors `coding_scheme.md` (see `classify.py`)
**Validation:** 100% agreement (40/40) on the pilot gold labels after one codebook tightening (Rule 2 — see `coding_scheme.md` change log 2026-04-25). 91.7% agreement (22/24) on a stratified spot check of full-run predictions (see "Spot-check validation" below).

## Headline

| | N | % Personal | % Emotional |
|---|---|---|---|
| **Reddit (all 4 subs)** | 1,500 | **71.3%** | **31.8%** |
| **Reddit advice (3 subs, excl. LifeProTips)** | 1,125 | **90.8%** | **41.3%** |
| **WildChat** | 1,493 | **0.7%** | **0.1%** |

> Reddit advice forums are overwhelmingly personal (~91%) and frequently emotional (~41%). WildChat first turns are essentially never personal (0.7%) or emotional (0.1%). The hypothesis is **reversed** in this data; the effect on Personal is roughly **130-fold**.

The pilot's prediction held: WildChat first turns are dominated by tasks, creative writing, code help, and factual questions — not personal disclosure.

## Reddit broken down by subreddit

| Subreddit | N | %P | %E |
|---|---|---|---|
| relationship_advice | 375 | **93.6%** | **64.5%** |
| socialskills | 375 | 90.7% | 47.2% |
| personalfinance | 375 | 88.0% | 12.3% |
| LifeProTips | 375 | 13.1% | 3.2% |

**LifeProTips is a structural outlier** — confirmed at full N. It is a tips-sharing sub, not an advice-seeking sub. Excluding it raises the Reddit Personal rate from 71.3% to 90.8%. This is a real methodological point, not noise.

**personalfinance vs the other two advice subs** is the cleanest illustration of the "personal but measured" pattern: same Personal rate (~90%), but a quarter of the Emotional rate (12% vs ~50%). Money posts are personal-but-deliberative.

**relationship_advice has the highest Emotional rate** (64.5%) — relationship problems trigger more affective language than career or money problems do.

## P × E combination matrix

|  | 0/0 (neither) | 1/0 (personal, not emotional) | 0/1 (emotional, not personal) | 1/1 (both) |
|---|---|---|---|---|
| **Reddit** (LLM) | 429 | **594** | 1 | 476 |
| **Reddit** (human-corrected) | 430 | 593 | **0** | 477 |
| **WildChat** | 1,482 | 10 | 0 | 1 |

> The "human-corrected" row reflects two manual flips identified in the spot check (see below). Aggregate %P and %E are unchanged; the 0/1 cell becomes empty across both sources.

## Statistical significance

Chi-square tests of independence between source (Reddit vs WildChat) and each binary code:

| Comparison | Personal | Emotional |
|---|---|---|
| Reddit (all 4 subs) vs WildChat | χ² = 1,613, p ≈ 0 | χ² = 559, p = 1.3 × 10⁻¹²³ |
| Reddit advice (3 subs) vs WildChat | χ² = 2,173, p ≈ 0 | χ² = 744, p = 8.6 × 10⁻¹⁶⁴ |

Both effects are massively significant. With effect sizes this large, statistical significance is largely a formality — the chi-square confirms the difference is not a sampling artifact.

## Spot-check validation

A 24-row stratified manual review of full-run predictions (12 from rare cells: 1 Reddit 0/1 + 10 WildChat 1/0 + 1 WildChat 1/1; 12 from common cells: 3 random per cell from R-0/0, R-1/0, R-1/1, WC-0/0). Rare cells were oversampled because errors there move the headline most.

**Result: 22/24 agreement (91.7%).** Both disagreements were on Emotional, in opposite directions:

| Case | Predicted | Human | Why the model erred |
|---|---|---|---|
| rd_a3wjd | 0/1 | 0/0 | "Caught me off guard" / "I'm terrible at dealing with serious situations" — under tightened Rule 2, behavioral and chronic-trait descriptions don't qualify as named affect. |
| rd_a1im9 | 1/0 | 1/1 | "I was actually revolted" — explicit emotion word naming the author's own state. The model over-applied Rule 3 (heavy topic, neutral language) when in fact the language was not neutral. |

**Implications:**

- **No systematic bias.** One over-codes E, one under-codes — errors are at codebook edges (behavioral descriptions and the Rule 3 borderline), not in any consistent direction.
- **Aggregate %P and %E are unchanged** — the two corrections cancel each other on the Reddit side (one Emotional flips up, one flips down).
- **The 0/1 cell goes from 1 case to 0** across both sources. Finding #2 below is now stronger: emotional-without-personal is *literally* absent in this corpus, not just rare.
- 91.7% agreement is consistent with the 100% pilot rate (40 rows, post-tightening) and well above the 85% target from `pilot_results.md`.

## Three findings worth remembering

### 1. "Personal but not emotional" (1/0) is the dominant Reddit pattern

594 of 1,500 Reddit posts (~40%) are personal but measured in tone. Splitting Personal and Emotional into two independent dimensions was the methodological choice that made this visible — a single combined "emotional/personal" label would have collapsed it. The pattern is clearest in personalfinance, where the topic is by definition personal but the language stays deliberative.

### 2. The (0/1) cell is empty across both sources

Zero cases after human correction (1 LLM-flagged Reddit case, rd_a3wjd, was reviewed and reclassified to 0/0 — see Spot-check validation). **Emotional language without personal framing is empirically absent** in this corpus. If you express your own feelings, you are almost by definition making the message about yourself. This is both an internal consistency check that the codebook is coherent, and a small finding in its own right.

### 3. WildChat is strikingly impersonal at scale

Across 1,493 random first turns, only 11 were personal (0.7%) and only 1 was emotional (0.1%). Users came to ChatGPT for tasks: code help, summarization, math, role-play, factual questions. The pilot's small-N estimate (0%) was almost spot-on.

## What this means for the research question

**Original question:** *Do people bring more emotional/personal problems to AI than to human-advice communities, or vice versa?*

**Answer in this data:** The hypothesis is **reversed**, and the effect is large. People bring vastly *less* emotional/personal content to a general-purpose chatbot than to Reddit advice subs.

**Important framing caveat (from the pilot, still applies):** This is about *what users typed in the first turn*, not about *what users felt*. A person could feel lonely and ask ChatGPT to write a cover letter — the emotional need is real but doesn't surface in the text. The finding describes observable message content, not inner state.

## Caveats

- **Temporal mismatch.** Reddit sample is 2009–2013; WildChat is 2023–2024. Era could partly account for differences, but a ~130-fold gap is too large to be all era. Worth naming explicitly in any further writeup.
- **The AI side is already dated.** WildChat closed in 2024. By 2025–2026, more users visibly bring advice-seeking, self-reflection, and personal-life prompts to general-purpose chatbots — the behavior that was rare in the 2023–2024 sample is plausibly far more common now. The 0.7% / 0.1% WildChat headline should be read as a **2023–2024 baseline**, not a stable estimate. A re-run on 2025–2026 logs would likely show a higher Personal rate on the AI side and a narrower gap.
- **Subreddit choice.** Four advice-adjacent subs, not all of Reddit. The LifeProTips/advice split shows how much within-Reddit variation exists.
- **WildChat is general-purpose.** ChatGPT users came for many reasons — this is not a sample of "people seeking emotional support from AI." A companionship-marketed product (Replika, Character.AI) would likely look very different.
- **Self-selected populations.** Findings describe these subgroups, not "people in general" or "all Reddit/AI users."
- **4 WildChat refusals.** 4 of 1,497 (0.27%) returned no usable label, likely because Sonnet 4.6 refused on edgy content. Even if all four were 1/1, WildChat Personal goes from 0.7% to 1.0%. Doesn't move the conclusion.
- **Classifier validation.** 100% agreement (40/40) on the pilot gold labels post-tightening; 91.7% agreement (22/24) on a stratified spot check of the full-run predictions. The two disagreements were on Emotional and in opposite directions (one over-coded, one under-coded), implying no systematic bias.
- **Operational definition.** "Emotional/personal" depends on the codebook in `coding_scheme.md`. A different codebook (e.g., one that counts behavioral descriptions as E=1) would give different numbers.

## Connection to the pilot

| | Pilot (N = 40) | Full run (N = 2,993) |
|---|---|---|
| Reddit advice %P | 93% | 90.8% |
| Reddit advice %E | 33% | 41.3% |
| WildChat %P | 0% | 0.7% |
| WildChat %E | 0% | 0.1% |

Pilot estimates held within 3 points on Personal and within 8 points on Emotional. The codebook generalized cleanly. The slightly higher Emotional rate at full N (41% vs 33%) is well within sampling variance for N = 15 advice posts vs N = 1,125.

## Files

- `predictions.csv` — 2,993 rows: id, source, subreddit, word_count, personal, emotional, reasoning
- `analyze.py` — produces this report's tables and chi-square results
- `classify.py` — single-message classifier; codebook is the system prompt
- `classify_batch.py` — batch driver for all 2,997 unique messages
- `spot_check.py` — generates the 50-row stratified QA sample
- `coding_scheme.md` — locked codebook (Rule 2 tightened 2026-04-25)
- `pilot_results.md` — pilot-stage results (N = 40, 2026-04-23)
- `data_notes.md` — dataset provenance, schema, processing
- `validation_results.csv` — 40-row pilot validation output
- `batch_state.json` — batch ID + row metadata; created at submit time, used for resumable polling
