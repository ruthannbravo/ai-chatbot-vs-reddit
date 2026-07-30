# Personal but Not Emotional: What Reddit Advice Posts and ChatGPT First Turns Reveal About How People Address Human and AI Listeners

**Author:** Ruth-Ann Bravo
**Date:** May 2026

## Abstract

The popular narrative around general-purpose AI chatbots is that users are increasingly bringing emotional and personal problems to them — sometimes treating them as confidants. We tested a bounded version of this against observable text by comparing 1,500 random first-turn user messages from WildChat (a public log of ChatGPT conversations, 2023–2024) with 1,500 opening posts from four Reddit advice-adjacent subreddits (2009–2013). Each message was scored on two independent binary dimensions, **Personal** (the author is the subject and the topic is in a life domain) and **Emotional** (the author's language names an internal state), using a four-rule codebook that reached 40/40 agreement on a 40-post hand-labeled pilot — in-sample, after one rule was tightened to resolve a disagreement within that set. Reddit advice posts (excluding a tips-sharing subreddit, LifeProTips) were 90.8% Personal and 41.3% Emotional. WildChat first turns were 0.7% Personal and 0.1% Emotional — a roughly 123-fold gap on Personal, resting on only 11 Personal WildChat messages. In these venues the expected direction is reversed: people brought vastly *less* observable personal/emotional content to a general-purpose chatbot than to public Reddit advice forums. The comparison is deliberately asymmetric — advice-seeking venues against unconditioned chatbot traffic — so it bounds rather than estimates any population-level gap, and it speaks to what users typed, not to what they felt.

## 1. Question

> Among first-turn user messages to a general-purpose chatbot versus opening posts on public Reddit advice forums, what proportion of each are personal and emotional, and do the distributions differ?

The question is **about the surface text of the first message**, not about what the user feels. A person could feel lonely and ask ChatGPT to write a cover letter; the emotional need is real but does not surface in the text. The finding here describes observable message content, not inner state.

## 2. Data

| Source | N | Range | Filter |
|---|---:|---|---|
| WildChat (`allenai/WildChat-1M`) — first user turn | 1,500 | 2023–2024 | English, 10–1000 words, random seed 42 |
| Reddit (`HuggingFaceGECLM/REDDIT_submissions`) — opening post | 1,500 | 2009–2013 | non-deleted, non-empty, 10–1000 words; 375 per subreddit; seed 42 |
| Subreddits | 4 | — | `relationship_advice`, `socialskills`, `personalfinance`, `LifeProTips` |

Three duplicate-ID rows in WildChat were dropped at classification time, leaving 1,497 unique WildChat messages. Four WildChat messages returned no usable label (the classifier refused on edgy content), giving N = 2,993 for analysis.

The Reddit dataset was used because Reddit's late-2025 Responsible Builder Policy restricts new live-API access. r/AskReddit and r/Advice were not in the upstream dataset, so four advice-adjacent subreddits were used.

## 3. Method

### 3.1 Codebook (two independent dimensions, four rules)

Each message receives two binary codes:

- **Personal (P) = 1** if the author is the subject **and** the topic is in a life domain (relationships, body/health, finances, feelings, decisions, identity, work/career, or a significant personal problem).
- **Emotional (E) = 1** if the message contains an explicit emotion word naming the author's own state ("frustrated," "plagued," "overwhelmed") or clear affective phrasing that names an internal state ("can't stop worrying," "losing my mind"). Neutral, deliberative, or task-oriented language is E = 0 even when the topic is heavy.

Four rules disambiguate edge cases:

- **Rule 1 (framing over topic):** an intimate-topic question with impersonal framing — e.g., a creative-writing prompt about a fictional character's medical issue — is P = 0.
- **Rule 1b (self-involvement is not enough):** "Where should I park?" is self-involved but logistical — P = 0.
- **Rule 2 (strict threshold for emotional language):** polite closings, casual interjections, and playful tone do not count as emotional.
- **Rule 3 (content ≠ affect, the most important rule):** do not code E = 1 just because the topic *feels* heavy. A measured, analytical post about grief or sexual inexperience is E = 0 if the language is neutral.

Behavioral and physical descriptions ("my face went red," "I avoided eye contact") describe observable behavior, not a named internal state, and were finalized as E = 0 after a pilot disagreement on 2026-04-25.

### 3.2 Classification

Claude Sonnet 4.6 (`claude-sonnet-4-6`) was used as the classifier. The system prompt is the codebook itself, with prompt caching enabled (cache_control: ephemeral). The user message contains only the message to classify, wrapped in `<message>` tags. Output is a JSON object — `{personal, emotional, reasoning}` — constrained by a JSON schema. All 2,997 unique messages were submitted via the Anthropic Message Batches API in a single batch.

### 3.3 Validation

**Pilot (N = 40):** 40 hand-labeled posts (20 Reddit, 20 WildChat). After one Rule 2 tightening on behavioral descriptions, the classifier reached **40/40 agreement** on both Personal and Emotional. This is an in-sample figure: the tightening was prompted by a disagreement on `rd_a20ea`, one of the 40, and agreement was then measured on the same unchanged set. The 20 WildChat items are all gold-labeled 0/0 and most are unambiguous task text, so the set is easier than 40/40 implies. Reproducible via `classify.py` against the committed `pilot_coding.csv`.

**Spot check (N = 24, full-run predictions):** A stratified sample weighted toward rare cells (1 Reddit-0/1, 10 WildChat-1/0, 1 WildChat-1/1, plus 3 random draws per common cell) was reviewed manually. Result: **22/24 (91.7%)** agreement, with both disagreements on Emotional and in opposite directions. Three limits on how much weight this carries: the per-row labels were never committed to the repo (the committed `spot_check_sample.csv` is a 52-row sample with the human columns blank), so only the two corrections are traceable; rare-cell stratification means this is not an estimate of overall accuracy; and because it reviews positive *predictions*, it measures precision, not recall — a WildChat message wrongly coded 0/0 could never appear in it, which is precisely the error direction the 0.7% headline is sensitive to.

**A structural limitation of both.** One person wrote the codebook and produced every human label in this study. There is no second coder and therefore no inter-rater reliability statistic (Cohen's κ or otherwise). Agreement here means *model vs. that one coder*, never *coder vs. coder*, so it measures whether the model applied the codebook consistently — not whether the codebook is intersubjectively reliable.

## 4. Results

### 4.1 Headline

| Group | N | % Personal | % Emotional |
|---|---:|---:|---:|
| Reddit (all 4 subs) | 1,500 | **71.3%** | **31.8%** |
| Reddit advice (3 subs, excl. LifeProTips) | 1,125 | **90.8%** | **41.3%** |
| WildChat | 1,493 | **0.7%** | **0.1%** |

The gap on Personal is roughly **123-fold** between Reddit advice forums and ChatGPT first turns (90.76% / 0.737%). Because the WildChat numerator is 11 messages, the interval around that ratio is wide (roughly 68×–222×); "two orders of magnitude" is the claim the data support robustly.

### 4.2 By subreddit

| Subreddit | N | % Personal | % Emotional |
|---|---:|---:|---:|
| relationship_advice | 375 | 93.6% | **64.5%** |
| socialskills | 375 | 90.7% | 47.2% |
| personalfinance | 375 | 88.0% | 12.3% |
| LifeProTips | 375 | 13.1% | 3.2% |

**LifeProTips behaves nothing like the other three.** It is a tips-sharing subreddit, not an advice-seeking one. Including it pulls the headline Reddit-Personal rate from 91% down to 71%. Excluding it gives the cleaner advice-forum estimate.

**personalfinance is the canonical "personal but measured" venue.** Same Personal rate as the relationship and social subs (~90%), but a quarter of the Emotional rate (12% vs 47–65%). Money posts are personal-but-deliberative.

### 4.3 P × E combination matrix

| | 0/0 (neither) | 1/0 (personal, not emotional) | 0/1 (emotional, not personal) | 1/1 (both) |
|---|---:|---:|---:|---:|
| Reddit (classifier output) | 429 | **594** | 1 | 476 |
| Reddit (human-corrected) | 430 | **593** | 0 | 477 |
| WildChat | 1,482 | 10 | 0 | 1 |

The spot check produced two manual flips, both Reddit rows and both on Emotional: `rd_a3wjd` from 0/1 to 0/0 (the model read behavioral phrasing as named affect), and `rd_a1im9` from 1/0 to 1/1 (the model treated "I was actually revolted" as neutral under Rule 3). They move in opposite directions, so aggregate %P and %E are unchanged; only the cell counts shift. After correction, **the (0/1) cell is empty across both sources** — though see §5.2 on how much that is worth. The first row is what `analyze.py` prints from `predictions.csv`, which stores the classifier's original labels; the corrections are applied in `make_figure.py` and documented in `results.md`.

### 4.4 Statistical significance

Chi-square tests of independence between source and each binary code:

| Comparison | Personal | Emotional |
|---|---|---|
| Reddit (all) vs WildChat | χ²(1) = 1,613, p ≈ 0 | χ²(1) = 559, p = 1.3 × 10⁻¹²³ |
| Reddit advice (3 subs) vs WildChat | χ²(1) = 2,173, p ≈ 0 | χ²(1) = 744, p = 8.6 × 10⁻¹⁶⁴ |

With effects this large, statistical significance is largely a formality — the χ² confirms the difference is not a sampling artifact.

## 5. Three findings

### 5.1 "Personal but not emotional" is the dominant Reddit pattern

593 of 1,500 Reddit posts — roughly **40%** — are personal but measured in tone. A single combined "emotional/personal" label would have collapsed this. Splitting Personal and Emotional into two independent binary dimensions was the methodological decision that made the pattern visible. It is most pronounced in personalfinance, where the topic is by definition personal but the language stays deliberative.

### 5.2 The (0/1) cell is empty across both sources

Zero cases of "emotional but not personal" after manual correction. Empirically, **expressing your own feelings makes the message about yourself**.

This should be read as a coherence check on the codebook rather than as a discovery about language. Rule 2 requires a named internal state belonging to the author, which is hard to satisfy while the author is not the subject — so an empty (0/1) cell is close to true by construction. The single observed counterexample is also the one removed by manual correction, which means the cell is empty partly by decision. It shows the two dimensions are not orthogonal in practice; it is not evidence that emotion-without-self-reference does not occur in human writing.

### 5.3 ChatGPT first turns are strikingly impersonal at scale

Across 1,493 random first turns, only 11 were Personal (0.7%) and 1 was Emotional (0.1%). Users came to ChatGPT for tasks: code help, summarization, math, role-play, factual questions, creative writing. The pilot's small-N estimate (0%) was almost spot-on at full N.

## 6. Discussion

### 6.1 What the gap means

In *this* data, and between *these* venues, the expected direction is reversed. Public Reddit advice forums are a venue where people deliberately disclose personal situations and frequently, though not always, name how they feel about them. A general-purpose chatbot is not. Most ChatGPT first turns look more like the kinds of things you would type into a search engine or paste into a productivity tool than the kinds of things you would post on r/relationship_advice.

One asymmetry deserves to be stated rather than buried in the caveats, because it bounds how far the result generalizes. The Reddit arm was drawn from subreddits selected *because* people bring personal problems there; the WildChat arm is an unconditioned random draw from all ChatGPT traffic. The comparison is therefore between a venue optimized for disclosure and a venue used for everything, which is the right design for the question as posed in §1 but the wrong design for testing a claim about chatbot users in general. Two things keep this from hollowing out the finding: the gap holds across the entire observed range of the Reddit side, with even LifeProTips at 13.1% Personal running ~18× above WildChat (χ² = 143, p = 7 × 10⁻³³), and the unfiltered all-four-subreddit row is still ~97×. But LifeProTips is itself advice-adjacent, so it is not a stand-in for an unconditioned Reddit base rate. A random draw across all of Reddit was never taken, and until one is, the honest statement is that this study measures a venue difference of at least two orders of magnitude, not a population difference of any specific size.

This does not contradict reports of intense emotional reliance on AI chatbots — it constrains where to look for it. **A general-purpose model used by a general population is not the same dataset as a companionship-marketed product (Replika, Character.AI) used by a self-selected one.** The gap also does not say anything about what users *felt* before they typed; it says only what they typed in the first turn.

### 6.2 Why "personal but not emotional" matters methodologically

Treating "emotional/personal" as one construct would have produced a substantially weaker, blurrier finding. By coding the dimensions independently, the analysis surfaces a third pattern that an aggregated label would have hidden: users in personalfinance are doing something genuinely different from users in relationship_advice, even though both sets of posts are squarely "about themselves." Future work on disclosure should probably default to splitting these.

### 6.3 What "personal but not emotional" implies about how people seek advice

The most psychologically interesting result in this study is not the headline gap between Reddit and ChatGPT — it is the internal composition of the Reddit side.

Forty percent of Reddit posts in this sample are personal but measured in tone. Someone describing a debt-to-income ratio, laying out a relationship timeline in structured paragraphs, or working through a career decision with explicit pros and cons is doing something that looks much more like *deliberative reasoning* than emotional release. This challenges a common assumption: that online advice-seeking is primarily emotionally driven — that people post publicly because they need to vent, and the advice is almost incidental.

The data do not support that for a large fraction of Reddit advice posts. Many users appear to be using advice forums as a **thinking tool**: articulating a situation precisely, structuring a decision, and soliciting outside judgment. The emotional charge may be real and present internally, but it does not surface in the text. And the pattern is not confined to r/personalfinance, where a financial framing makes deliberation expected. Even in r/relationship_advice — a venue associated with raw emotional disclosures — roughly 29% of posts are personal but non-emotional (93.6% Personal, 64.5% Emotional; since the 0/1 cell is empty, all Emotional posts are also Personal). In r/socialskills, the personal-but-measured fraction is approximately 43%.

The distinction has practical implications. Deliberative advice-seeking and emotionally-driven disclosure are probably best served by different kinds of responses. A post asking whether to consolidate student loans may benefit from calculations; the same post from someone who opens with "I'm overwhelmed and spiraling" may benefit from acknowledgment before analysis. The present study cannot say whether advice-givers on Reddit recognize this distinction — but it establishes that the distinction exists at scale in the observable text, and that it is the *modal* pattern, not an edge case.

**The AI caveat.** In the 2023–2024 WildChat data, deliberative, personal first turns were almost absent — 10 out of 1,493 messages. But chatbot use has shifted noticeably since then. By 2025–2026, users are visibly bringing "help me think through whether to take this job," "here is my situation, what am I missing?", and "talk me through this decision" prompts to general-purpose chatbots — the same deliberative-cognitive mode that has long been the dominant pattern on Reddit advice forums. Whether this shift shows up in measurable rates, and how large the remaining gap is, is an open empirical question. But if a re-run on 2025–2026 chatbot logs were to show a substantial rise in the personal-but-measured cell on the AI side, it would suggest that general-purpose AI is absorbing a function that Reddit advice forums have served for over a decade: not a confessional, but a structured thinking partner.

### 6.4 The 2023–2024 snapshot is already dated

WildChat's collection window closed in 2024. Between then and the time of writing (mid-2026), how people use general-purpose chatbots has shifted noticeably. Press coverage, model cards, and informal reporting all point in the same direction: more users now bring **advice-seeking, self-reflection, and personal-life questions** to ChatGPT and Claude — relationship dilemmas, career decisions, mental-health check-ins, "help me understand why I reacted this way" prompts. The behavior that was rare in 2023 first turns is plausibly much more common in 2025–2026 first turns.

That means the 0.7% / 0.1% headline should be read as a **2023–2024 baseline**, not a stable estimate. A re-run on a 2025–2026 sample (when one becomes publicly available) would very likely show a higher Personal rate on the AI side, and the gap to Reddit would narrow. Whether it narrows by 2× or by 50× is the empirical question that follow-up work should answer. The methodology in this repo is designed to be re-runnable on a fresh sample with no changes to the codebook.

## 7. Caveats

- **Temporal mismatch.** Reddit is 2009–2013; WildChat is 2023–2024. Era could account for some of the gap, but a ~123-fold difference is too large to be entirely era.
- **Asymmetric conditioning.** Advice-seeking subreddits versus unconditioned chatbot traffic. See §6.1 — the result bounds a venue gap rather than estimating a population one.
- **The headline ratio rests on 11 events.** Only 11 of 1,493 WildChat messages were Personal, giving the ~123× estimate a 95% interval of roughly 68×–222×. The order of magnitude is solid; the multiplier is not precise.
- **Validation is single-rater and partly in-sample.** See §3.3. One coder, no Cohen's κ, a 40/40 figure measured after tuning a rule on the same 40 items, and a spot check whose per-row labels are not committed. An independent coder on a held-out set is the first thing further work should add.
- **No literature citations.** This article frames itself against a "popular narrative" and against disclosure research that collapses personal and emotional into one construct, but cites no specific sources for either. Those claims should be read as the author's characterization of the field, not as documented positions.
- **The AI side is already a snapshot in time.** Chatbot use shifted between 2024 and 2026 — anecdotal and journalistic evidence suggests more users now bring relationship questions, career reflections, and self-understanding prompts to general-purpose chatbots. A 2025–2026 WildChat-equivalent sample would almost certainly show a higher Personal rate on the AI side. See §6.4.
- **Subreddit selection.** Four advice-adjacent subreddits are not all of Reddit. The within-Reddit variation (LifeProTips at 13% Personal vs relationship_advice at 94%) shows how sensitive the answer is to which corners of Reddit you pick.
- **WildChat is general-purpose.** Users came to ChatGPT for many reasons. This is not a sample of "people seeking emotional support from AI."
- **Self-selected populations.** Findings describe these subgroups, not "people in general."
- **First-turn only.** A neutral first turn ("write me a cover letter") can be followed by intensely personal turns later. This study does not address conversational drift.
- **Operational definition.** Different codebooks would give different numbers. A codebook that counted behavioral descriptions as Emotional would push the Reddit Emotional rate higher; one that required acute affect rather than chronic traits would push it lower.

## 8. Reproducibility

All code, data references, and intermediate artifacts live alongside this article:

- `data_notes.md` — sources, sampling, processing, schema
- `coding_scheme.md` — the locked codebook
- `pilot_coding.csv` / `pilot_results.md` — N = 40 pilot
- `classify.py` / `classify_batch.py` — classification scripts
- `predictions.csv` — full-run model outputs
- `analyze.py` — produces the headline table, P × E matrix, and χ² in §4
- `make_figure.py` — produces the headline figure
- `spot_check.py` / `spot_check_sample.csv` — QA sampler (human columns blank; see §3.3)
- `requirements.txt` — pinned dependencies and tested Python version

§4 is verifiable from this repo alone: `analyze.py` reads the committed `predictions.csv` and needs no API key or raw data. §3.3's pilot figure is likewise reproducible from the committed `pilot_coding.csv`.

Two gaps remain, both known and unclosed. The script that drew the upstream samples was never committed — only its outputs — so although the seeds are recorded (42 for sampling, 7 for the pilot draw), the sampling step cannot be re-executed as written. And upstream dataset revision hashes were not pinned, so a fresh Hugging Face pull is not guaranteed to reproduce the same rows. Regenerating `predictions.csv` from scratch is therefore approximate; verifying the published analysis is exact.

## 9. Conclusion

In 2023–2024 data, people brought vastly less observable personal and emotional content to ChatGPT first turns than to Reddit advice posts. The dominant Reddit pattern is "personal but measured" — a finding that depends on coding Personal and Emotional as independent dimensions rather than collapsing them.

This conclusion is **bounded to its time window**. Chatbot use is changing fast. By 2025–2026, more users are visibly turning to general-purpose AI for advice, self-reflection, and personal understanding — the kinds of prompts that were rare in the 2023–2024 sample. A re-run on a fresh AI-side sample is the natural next step, and would likely tell a meaningfully different story. Whether the same patterns hold in *companionship-marketed* AI products, in *later* turns of conversations, in *2025–2026 chatbot logs*, or in *Reddit data from 2024*, are all open questions and good next steps.
