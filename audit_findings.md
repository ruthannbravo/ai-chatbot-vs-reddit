# Project Audit — Findings

**Audit date:** 2026-05-06
**Scope:** Python scripts, codebook, data files, results documentation.

## Summary

The pipeline is functionally correct. `analyze.py` reproduces the headline numbers in `results.md` exactly when run against `predictions.csv`. The 40-row pilot validation in `validation_results.csv` shows 40/40 agreement on both P and E. No data bugs, no arithmetic errors, no failing scripts. Issues below are documentation/consistency, not correctness.

## Verified clean

| Check | Result |
|---|---|
| `analyze.py` runs | OK — output matches `results.md` headline, P×E matrix, χ² values |
| Reddit sample composition | 1,500 rows, 375 per subreddit × 4 subs, 0 dup IDs, 0 empty texts |
| WildChat sample composition | 1,500 rows, 1,497 unique IDs (3 dups confirmed, as documented), 0 empty texts |
| `predictions.csv` | 2,993 rows (1,500 Reddit + 1,493 WildChat) — matches results.md |
| Pilot validation | 40/40 P-match, 40/40 E-match, 40/40 both — consistent with results.md |
| χ² inputs | Expected frequencies all ≫ 5; no low-cell-count concern |

## Issues found

### 1. Rule count drift between codebook and prompt — `coding_scheme.md:27`

Header reads `## The three rules`, but the section defines **four** rules: Rule 1, Rule 1b, Rule 2, Rule 3. Every other reference says "4 rules":

- `classify.py:40`: `# The four rules`
- `results.md:5`: `2 binary dimensions ... + 4 rules`
- `pilot_results.md:5, 84`: `+ 4 rules` and `(4 rules, worked examples)`

**Fix:** change the codebook header to `## The four rules` so all artifacts agree.

### 2. Spot-check script doesn't match the spot-check that was reported — `spot_check.py` vs `results.md`

`spot_check.py` SAMPLE_PLAN is hardcoded to 10 random draws per common cell, which generates **52 rows** (verified by re-running the sampler). The actual file `spot_check_sample.csv` has 52 rows but **0 human labels filled in**. Yet `results.md` reports a **24-row review** with the breakdown: 1 Reddit-0/1 + 10 WildChat-1/0 + 1 WildChat-1/1 (rare cells) + 3 from each of 4 common cells = 24.

The reported review must have been completed outside the committed CSV, with a different sampling plan (3 random per common cell rather than 10).

**Fix options:**
- Update `SAMPLE_PLAN` in `spot_check.py` to use `3` for common cells so it matches what was actually reviewed, OR
- Re-run the 52-row sample as the committed artifact and update `results.md`'s "Spot-check validation" section with the new counts.

This is the most consequential audit finding — the QA reported in `results.md` is not reproducible from the code in this directory.

### 3. Stale schema mismatch flagged but not resolved — `data_notes.md:50`

Reddit uses `created_utc` + `created_datetime`; WildChat uses `timestamp`. The note says "Unify before running side-by-side time-based analysis." No time-based analysis is in scope, so this hasn't bitten anything, but the warning has been outstanding since 2026-04-23.

**Fix:** either resolve (add a unified column) or strike the warning if time-based analysis is out of scope.

### 4. `data_notes.md` file inventory is stale — `data_notes.md:19-23`

The "File inventory" section lists three files (`reddit_sample.csv`, `wildchat_sample.csv`, `data_notes.md`). The project now contains 16 files. `results.md` has a complete and correct `## Files` section, so no information is lost — but the `data_notes.md` inventory is misleading.

**Fix:** remove the inventory from `data_notes.md` (it duplicates `results.md`) or update it.

### 5. No pinned environment

Scripts depend on `anthropic` and `scipy` but there is no `requirements.txt` / `pyproject.toml`. Reproducibility depends on whatever versions happen to be installed.

**Fix:** add a `requirements.txt` pinning `anthropic` and `scipy` (and noting the Python version used).

## Non-issues (looked, fine)

- **χ² with low cell counts** — chi2_contingency expected-frequency check passes; the smallest expected count is ~238, well above the rule-of-thumb 5.
- **`p ≈ 0` reporting** — for the Personal-source test the p-value underflows to 0.0 in scipy. `analyze.py` formats it as `0.00e+00`; `results.md` softens to "p ≈ 0". Both are honest.
- **"Human-corrected" row in P×E matrix** — `results.md:42` shows a corrected row, but `predictions.csv` still holds the LLM's original labels. This is fine: the row is clearly labeled, aggregate %P/%E are unchanged, and the correction is documented in the spot-check section.
- **Duplicate WildChat IDs** — 3 dropped at submit time by `classify_batch.py:67-76`, exactly as documented in `data_notes.md:72`.
- **4 WildChat refusals** — accounted for in `results.md:103`; sensitivity analysis in the same line shows the conclusion is robust to all 4 being maximally personal.

## Verdict

Ship-ready *for the headline finding*. Address Issue #2 (spot-check reproducibility) before any external write-up, since it touches the validation claim. Issues #1, #3, #4, #5 are cosmetic/operational.
