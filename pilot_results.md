# Pilot Coding Results

**Date completed:** 2026-04-23
**Sample:** 40 posts from `pilot_coding.csv` (20 Reddit + 20 WildChat, seed=7)
**Codebook:** `coding_scheme.md` — 2 binary dimensions (Personal, Emotional) + 4 rules

## Headline

| | N | % Personal | % Emotional |
|---|---|---|---|
| **Reddit (all 4 subs)** | 20 | **70%** | **25%** |
| **WildChat** | 20 | **0%** | **0%** |

Restricting to the 3 advice subs (excluding LifeProTips):

> **Reddit advice: 14/15 = 93% Personal, 5/15 = 33% Emotional**
> **WildChat: 0/20 = 0% Personal, 0/20 = 0% Emotional**

## Reddit broken down by subreddit

| Subreddit | N | P=1 | E=1 | %P | %E |
|---|---|---|---|---|---|
| relationship_advice | 5 | 5 | 2 | **100%** | 40% |
| socialskills | 5 | 5 | 2 | **100%** | 40% |
| personalfinance | 5 | 4 | 1 | 80% | 20% |
| LifeProTips | 5 | 0 | 0 | 0% | 0% |

**LifeProTips behaves completely differently from the other three** — it's a tips-sharing sub, not an advice-seeking sub. This is a real structural point worth naming in the writeup.

## P × E combination matrix

|  | 0/0 (neither) | 1/0 (personal, not emotional) | 0/1 (emotional, not personal) | 1/1 (both) |
|---|---|---|---|---|
| **Reddit** | 6 | **9** | 0 | 5 |
| **WildChat** | 20 | 0 | 0 | 0 |

## Three findings worth remembering

### 1. "Personal but not emotional" (1/0) is the dominant Reddit pattern

Nine of 20 Reddit posts — nearly half — are personal but measured in tone. This is the pattern that a single combined "emotional/personal" label would have destroyed. Splitting P and E was the key methodological decision.

Examples: the 25k-to-invest finance post, the "I'm going to Omegle to practice talking" post, the "how do I mingle at events" post, the sexual-inexperience post written analytically.

### 2. Zero (0/1) posts across both sources

Nobody was emotional without also being personal. "Emotional" is **nested inside** "Personal" in practice — if you express your own feelings, you're almost by definition making the message about yourself.

This is an internal consistency check that the codebook is coherent, and a minor finding worth mentioning in the writeup.

### 3. WildChat is strikingly impersonal

Across 20 random draws covering creative writing, agent configuration, code help, summarization, math, puzzles, factual questions, and one parking request — **not a single genuinely personal or emotional message**. The closest was the parking question (#22), which Rule 1b pushed back to P=0 because self-involvement in logistics ≠ personal.

The real 1,500 WildChat run will almost certainly find *some* personal messages (probably 1–5%), but the pilot suggests the proportion will be very small.

## What this means for the research question

**Original question:** *"Do people bring more emotional/personal problems to AI than to human-advice communities, or vice versa?"*

**If pilot rates generalize:** The hypothesis is **reversed in this data**. Reddit advice forums are overwhelmingly personal (≈93%) and often emotional (≈33%). WildChat first turns are essentially never personal or emotional. People bring vastly *less* emotional/personal content to a general-purpose chatbot than to Reddit advice subs.

**Interpretation caveat for the writeup:** This is about *what users typed in the first turn*, not about *what users felt*. A person could feel lonely and ask ChatGPT to write a cover letter — the emotional need is real but doesn't surface in the text. The finding is about observable message content, not inner state.

## Caveats

- **Small n.** 40 posts total. A few coding flips could shift percentages noticeably. The full 3,000-post run will give a much tighter estimate.
- **Temporal mismatch.** Reddit sample is 2009–2013; WildChat is 2023–2024. Era could partly explain differences (also noted in `data_notes.md`).
- **Only 4 subreddits.** Results may be sensitive to the subreddit choice. LifeProTips vs. the three advice subs shows how much within-Reddit variation exists.
- **WildChat is a general-purpose chatbot dataset.** Users came to ChatGPT for many reasons; this is not a representative sample of "people seeking emotional support from AI." A chatbot explicitly marketed for companionship (Replika, Character.AI) would likely look very different.

## Outcome (added 2026-04-25, after the full run)

These next steps were all carried out. Recording the results here, since this
document is the one the README points readers to for the pilot:

1. **Classifier prompt drafted** from `coding_scheme.md` — it is the system prompt in `classify.py`.
2. **Validated on these 40 gold labels: 40/40 agreement on both P and E**, against the ≥85% target. Two things qualify that figure. It came *after* Rule 2 was tightened to resolve a disagreement on `rd_a20ea`, one of these same 40 posts (see the `coding_scheme.md` change log), so it is in-sample rather than held-out. And the 20 WildChat rows are all gold-labeled 0/0, most of them unambiguous task text, making the set easier than the score suggests. Reproduce with `python3 classify.py`.
3. **Full run completed** on 2,997 unique messages; 2,993 usable labels. See `results.md`.
4. **Spot check done** on 24 rows: 22/24 agreement, producing two manual corrections. The per-row labels were never committed to the repo, so this figure is documented but not independently checkable — see the warning in `results.md` § Spot-check validation.
5. **Final headline table and chi-square** produced by `analyze.py`; see `results.md`.
6. **Findings written up** in `research_article.md`. Note that the write-up does not in fact cite Ho et al. (2018) or the infertility-Reddit paper — no literature citations made it into the final article, which is a gap flagged in its caveats.

Pilot estimates held up well: Reddit advice %P moved 93% → 90.8% and WildChat %P
moved 0% → 0.7% at full N.

## Next steps (as planned at pilot stage, 2026-04-23)

1. **Draft LLM-classifier prompt** from `coding_scheme.md`.
2. **Validate on these 40 gold labels.** Target: ≥85% agreement on both P and E.
3. **Run on full 3,000.** ~$1–3 in API costs.
4. **Spot-check ~50 LLM labels manually** to catch systematic errors.
5. **Produce final headline table** (same format as above but with N=3,000) plus chi-square test for distribution difference.
6. **Write up findings**, citing Ho et al. (2018) and the infertility-Reddit NLP paper for methodological precedent.

## Files referenced

- `pilot_coding.csv` — all 40 posts with final P, E, notes
- `coding_scheme.md` — the locked codebook (4 rules, worked examples)
- `data_notes.md` — dataset provenance, time ranges, schema
