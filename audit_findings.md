# Project Audit — Findings

**First audit:** 2026-05-06 (scripts, codebook, data files, results documentation)
**Second audit:** 2026-07-30 (multi-reviewer pass; statistics independently recomputed, findings adversarially verified)

## Summary

The analysis pipeline is correct and independently verifiable. `analyze.py`, run against the committed `predictions.csv`, reproduces every table and χ² value in `results.md` exactly; `tests/test_headline.py` now asserts this in CI. The 40-row pilot validation in `validation_results.csv` shows 40/40 agreement on both P and E.

The second audit found three problems the first had missed or waved through — a four-cell table in the README that did not sum to N, a headline multiplier derived from pre-rounded values, and a validation badge with no supporting data — plus confirmed that all five issues from the first audit were still open. All are now addressed or explicitly scoped, below.

## Verified clean

| Check | Result |
|---|---|
| `analyze.py` runs | OK — output matches `results.md` headline, P×E matrix, χ² values |
| Every published number vs. the data | OK — recomputed independently; `tests/test_headline.py` locks all of them |
| Reddit sample composition | 1,500 rows, 375 per subreddit × 4 subs, 0 dup IDs, 0 empty texts |
| WildChat sample composition | 1,500 rows, 1,497 unique IDs (3 dups confirmed, as documented), 0 empty texts |
| `predictions.csv` | 2,993 rows (1,500 Reddit + 1,493 WildChat), no blank labels |
| Refusal accounting | `batch_state.json` held 2,997 submitted IDs; exactly 4 WildChat IDs absent from `predictions.csv` — the documented refusals |
| Pilot validation | 40/40 P-match, 40/40 E-match, 40/40 both — consistent with `results.md` |
| χ² inputs | Expected frequencies all ≫ 5; smallest ≈ 200, no low-cell-count concern |
| Anthropic API usage | Results joined by `custom_id` not position; current `output_config.format` structured-output form; codebook cached as a stable system prefix; `classify_batch.py` imports the codebook and schema from `classify.py`, so pilot and full run provably share them |
| Seeded QA sampler | `spot_check.py` (seed 42) regenerates the committed 52-row sample exactly |

## Issues found in the second audit

### 1. README P×E matrix did not sum to N — **FIXED**

`README.md` gave the Reddit row as `429 | 594 | 0 | 476`, which sums to **1,499** against a stated N of 1,500. It mixed three raw-classifier counts with the corrected value for the 0/1 cell, making it internally impossible under any correction set, and it contradicted both `results.md` (which correctly shows raw and corrected rows separately) and the embedded figure. The README also said "one manual correction" where two are documented.

**Fixed:** README now publishes the human-corrected row (`430 | 593 | 0 | 477`), states that the raw output was 429/594/1/476, and says "two manual corrections". Prose counts updated 594 → 593. `research_article.md` §4.3 now shows both rows and names both flips. `tests/test_headline.py` asserts every published matrix row sums to its N.

### 2. Headline "~130-fold" gap was wrong — **FIXED**

The Reddit-advice-vs-WildChat Personal ratio is **123.2×** (90.756% / 0.7368%). The published 130 came from dividing pre-rounded display values (91 / 0.7 = 130.0). No subset pairing in the data yields 130: all four subs give 96.8×, the three advice subs 123.2×, `relationship_advice` alone 127.0×. The string was hardcoded in `make_figure.py` and baked into the committed PNG.

**Fixed:** corrected to ~123-fold in all eight locations; `make_figure.py` now computes the ratio from the loaded rates so it cannot drift again; figure regenerated. Docs now also note the ratio rests on 11 WildChat events (95% CI ≈ 68×–222×), so "two orders of magnitude" is the robust claim.

### 3. The 22/24 spot check has no committed evidence — **PARTIALLY ADDRESSED, ACTION STILL REQUIRED**

Carried over from first-audit issue #2 and made worse by being promoted to a README badge. `spot_check_sample.csv` has 52 rows with `human_p`, `human_e`, `agree`, and `notes` **blank in all 52**. The labels are not in `validation_results.csv` or `pilot_coding.csv` either. `spot_check.py` draws 10 per common cell (→ 52 rows), while `results.md` describes a 24-row, 3-per-cell design.

**Done:** the badge is removed; `README.md`, `results.md`, and `research_article.md` §3.3 now state plainly that the review's per-row labels were never captured and that 22/24 is a documented note rather than evidence; `spot_check.py`'s docstring records the discrepancy.

**Still required — this cannot be fixed by editing docs.** Re-run the review against the committed 52-row sample, fill in the human columns, commit it, and replace the 22/24 figure with what that review finds. Until then this validation claim is unsupported by anything in the repo.

### 4. `classify_batch.py` could destroy `predictions.csv` — **FIXED**

`collect_results()` opened `predictions.csv` in `"w"` mode and wrote the header *before* the first fallible network call, so any failure left a header-only file. This was reachable on every fresh clone: `batch_state.json` was committed and `main()` took the resume branch whenever it existed, with no flag — and batch results expire 29 days after creation, so that batch was long dead. Labels were also written unvalidated (`parsed.get(...)` could emit blank cells that every downstream `int()` would reject), non-object JSON would raise an uncaught `AttributeError` mid-write, and the error log was printed but never persisted.

**Fixed:** writes now go to a temp file and `os.replace()` onto `predictions.csv` only after the run yields ≥1 usable row; labels are validated to be 0 or 1 before writing; the exception clause covers the non-dict-JSON path; failures are persisted to `errors.csv` with `stop_reason`; resume is an explicit `--resume` flag that refuses to run without state, and a fresh run refuses to clobber existing state; polling has a 6-hour bound and reports expired batches with instructions; `batch_state.json` is now gitignored and untracked.

### 5. Framing overreach in the abstract and TL;DR — **ADDRESSED**

The design compares subreddits chosen *because* people post personal problems there against unconditioned ChatGPT traffic, then opened by declaring the popular narrative "reversed" — importing a population-level frame onto a venue-conditioned result. Mitigating context, confirmed during verification: the Conclusion (§9) already stated the properly scoped version, every instance of "reversed" was hedged with "in this data", and the gap survives the whole observed range (LifeProTips at 13.1% Personal is still ~18× WildChat, χ² = 143). So this was rhetoric in the two most-read locations, not a design defect.

**Addressed:** README TL;DR and article abstract now state what is being compared and that the multiplier is an upper bound; §6.1 discusses the asymmetry directly; both caveat lists note that a random all-Reddit sample was never drawn.

### 6. Classifier validation is circular and single-rater — **DISCLOSED**

Rule 2 was tightened specifically to resolve a disagreement on `rd_a20ea`, one of the 40 pilot items, after which the same 40 were rescored and reported as 40/40. Half the pilot set is WildChat rows all gold-labeled 0/0, mostly unambiguous task text. One person wrote the codebook and produced every human label; there is no second coder and no Cohen's κ anywhere in the project.

**Disclosed** in `README.md` § Method, `results.md` caveats, `research_article.md` §3.3 and §7, `pilot_results.md`, and in `classify.py`'s own output. The substantive fix — an independent coder on a held-out set — remains open and is named as the first priority for further work.

### 7. Over-claimed secondary finding: the empty (0/1) cell — **DISCLOSED**

"Emotional but not personal is empirically absent" is close to true by construction: Rule 2 requires a named internal state belonging to the author, which is hard to satisfy without the author being the subject. The single observed counterexample is also the one removed by manual correction. Now framed as a codebook-coherence property rather than a discovery, in both `results.md` and `research_article.md` §5.2.

### 8. Spot check measures precision, not recall — **DISCLOSED**

Because it reviews positive predictions, the design cannot detect false negatives — a WildChat message wrongly coded 0/0 never enters the sample. Since the 0.7% headline rests on only 11 positives, that is the error direction it is most sensitive to. Noted in `results.md`, `research_article.md` §3.3, and `spot_check.py`'s docstring. Also corrected: "no systematic bias" was concluded from n = 2 disagreements, which the text no longer claims.

## First-audit issues (2026-05-06) — all now closed

| # | Issue | Status |
|---|---|---|
| 1 | `coding_scheme.md` header said "three rules" for four | **FIXED** — header corrected |
| 2 | Spot-check script doesn't match the reported spot check | **See issue 3 above** — documented; re-review still required |
| 3 | Stale schema-mismatch warning in `data_notes.md:50` | **FIXED** — rewritten as a scoping note (no time-based analysis is in scope; no script reads either timestamp column) |
| 4 | Stale file inventory in `data_notes.md` | **FIXED** — replaced with a scope note pointing at `results.md` § Files |
| 5 | No pinned environment | **FIXED** — `requirements.txt` added with pinned `anthropic`, `scipy`, `matplotlib`, `datasets` and the tested Python range; `matplotlib` was also missing from the README install line, now corrected |

## Also fixed in the second pass

- **`data_notes.md` said the study's central construct "is not yet operationally defined"** — a leftover to-do contradicting the whole project. Now points at `coding_scheme.md`.
- **`data_notes.md` labelled 2,997 as "Effective N for analysis"** — 2,997 was submitted, 2,993 analyzed. Both numbers now stated and distinguished.
- **`results.md` called the QA sample "50-row"**; it is 52.
- **`classify.py` swallowed per-row exceptions silently**, so a run with failures could print "100%" over a shrunken denominator. Failures are now collected and reported loudly, and the agreement line shows `n of 40`.
- **`spot_check.py` opened the uncommitted raw CSVs unguarded**, dying on a bare `FileNotFoundError`. Now exits with an explanation.
- **`coding_scheme.md` described itself as "open for refinement"** while other docs called it locked. Reframed as judgment calls recorded as locked, with the vague "significant personal problem" clause explained.
- **No CI, tests, or citation metadata.** Added `tests/test_headline.py` (asserts every published figure against `predictions.csv`, including that each matrix row sums to N), `.github/workflows/ci.yml`, and `CITATION.cff`.
- **`make_figure.py` was absent from the documented pipeline.** Now step 7 in the README.
- **`pilot_results.md` never reported the 40/40 outcome** the README pointed readers to it for. Added, with its qualifications.

## Non-issues (looked, fine)

- **χ² with low cell counts** — expected-frequency check passes; smallest expected count ≈ 200, well above the rule-of-thumb 5.
- **`p ≈ 0` reporting** — for the Personal-source test the p-value underflows to 0.0 in scipy. `analyze.py` prints `0.00e+00`; `results.md` softens to "p ≈ 0". Both are honest.
- **`predictions.csv` holds raw labels while the figure shows corrected ones** — deliberate and clearly labeled. `results.md` publishes both rows, the figure panel is titled "human-corrected", `analyze.py` reproduces exactly the raw row it claims to, and both corrections are documented by ID with rationale. Aggregate %P and %E are bit-identical either way because the two flips cancel; `tests/test_headline.py` asserts that.
- **Duplicate WildChat IDs** — 3 dropped at submit time by `classify_batch.py`, exactly as documented in `data_notes.md`.
- **4 WildChat refusals** — the count is reproducible by diffing submitted IDs against `predictions.csv`; sensitivity analysis in `results.md` shows the conclusion survives all four being maximally personal. Only the attribution to *refusal* specifically is unverifiable, and `results.md` already hedges it with "likely".

## Verdict

The headline finding is sound and now fully reproducible from committed files, with CI to keep it that way. One substantive gap remains open by necessity rather than oversight: **the 22/24 spot check needs to be re-done and committed** (issue 3), since no amount of editing can manufacture labels that were never saved. The deeper methodological limitation — single-rater validation with no inter-rater reliability — is now disclosed everywhere it is relevant, but closing it requires a second coder.
