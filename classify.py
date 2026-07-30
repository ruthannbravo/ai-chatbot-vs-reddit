"""
Validate the LLM classifier against the 40 gold-labeled pilot rows.

Reads pilot_coding.csv, classifies each message via Claude Sonnet 4.6, compares
predictions to gold labels (Personal, Emotional), and reports agreement.

Run: python3 classify.py
"""

import csv
import json
import os
import sys

from anthropic import Anthropic

MODEL = "claude-sonnet-4-6"
INPUT_CSV = "pilot_coding.csv"
OUTPUT_CSV = "validation_results.csv"

CODEBOOK = """\
You are a careful research coder applying a binary classification scheme to short messages (Reddit advice posts and AI chatbot first turns). For each message, output two independent binary codes — Personal (P) and Emotional (E) — plus a one-sentence reason.

# The two dimensions

## Personal (P)
- P = 1 if BOTH conditions hold:
  (a) the author is the subject — describing their own life or situation, AND
  (b) the topic falls in a life domain: relationships, body/health, finances, feelings, decisions, identity, work/career, or a significant personal problem.
- P = 0 if either:
  (a) the author isn't the subject — tasks, creative writing, factual questions about the world, discussion of a third party, OR
  (b) the author IS the subject but the topic is everyday logistics — parking, directions, shopping, travel tips, quick how-tos, recommendations.

## Emotional (E)
- E = 1 if the message contains an explicit emotion word referring to the author's own state (frustrated, stuck, lost, plagued, devastated, nervous, excited, overwhelmed) OR clear affective phrasing that NAMES AN INTERNAL STATE ("can't stop [worrying/thinking]," "don't know what to do," "losing my mind"). Affective phrasing must signal a mental or emotional state — not merely describe an observable behavior.
- E = 0 if the tone is neutral, deliberative, curious, or task-oriented — even when the topic is weighty.

P and E are independent. A message can be 0/0, 1/0, 0/1, or 1/1.

# The four rules

Rule 1 — Framing over topic. The framing of the message determines P, not the topic alone. A factual or creative-writing question about an intimate topic (drugs, sex, mental health, money) is P=0 if the author isn't the subject.

Rule 1b — Self-involvement alone is not enough. Being the subject of your own question doesn't automatically make it personal. "Where should I park?" or "What hike should I do?" is self-involved but logistical — P=0.

Rule 2 — Strict threshold for emotional language. E=1 requires explicit emotion words or clear affective phrasing. Polite closings ("thanks :)"), mild interjections ("yay"), and playful tone do NOT count.

Rule 3 — Content ≠ affect (most important). Do NOT code E=1 merely because the topic is emotionally heavy. E=1 requires the author's language to express feeling, not the topic to imply it. A measured, analytical post about sexual inexperience or grief is still E=0 if the language is neutral.

# Worked examples

P=0, E=0 (tasks / factual / creative writing / logistics):
- "On OSX — Window > Extended Controls > Video Filter..." (technical how-to)
- "Does Transformers architecture feature pairwise attention..." (factual question)
- "You are an expert in strategic analysis... PESTLE factors for Amazon" (coursework task)
- "Caroline Hertig is a young executive... write an excerpt from her bladder diary" (role-play; intimate topic but impersonal framing — Rule 1)
- "Please tell me the best places to park if I go to devil's bridge trail in sedona" (self-involved but logistical — Rule 1b)

P=1, E=0 (personal but measured tone):
- "We've been on 5 dates... she never uses my name. What should I read into this?" (personal puzzle, no affect)
- "I have about 25k to my name. 12k in student loans... best way to allocate?" (personal finance, deliberative)
- "I have zero to no self-confidence, found it difficult to talk on Omegle..." (trait description, not acute affect)
- "This is from someone who's never even kissed a girl... invisible to only me" (Rule 3 — heavy topic, analytical language)

P=1, E=1 (personal AND affective):
- "This has plagued me for a while; I'll be talking to someone and they have an opposing opinion..." ("plagued me" = explicit affect)

# Decision checklist (apply in order)

1. Is the author the subject of the message? If no → P=0.
2. Is the topic in a life domain (not logistics)? If no → P=0. If yes → P=1.
3. Does the post contain an explicit emotion word or clear affective phrasing? If yes → E=1, else E=0.

# Common failure modes to avoid

- Confusing topic with affect (Rule 3). Code the language, not the feeling.
- Role-play / creative writing about intimate topics: P=0 (Rule 1).
- Chronic trait descriptions ("low self-confidence", "I'm an introvert"): usually E=0.
- Behavioral / physical descriptions. Actions or bodily reactions that imply emotion ("my face went red," "I was blushing," "I couldn't remember what I said," "I avoided eye contact") describe observable behavior, not a named internal state. Per Rule 3, code the language, not the feeling the reader infers. E=0.
- Polite/casual closings ("thanks :)", "yay", "lol"): not emotional, E=0.
- Reddit advice posts skew P=1 but most are E=0 — don't default to E=1 just because it's an advice forum.

Output ONLY the JSON object specified by the schema. The reasoning field should be one sentence naming the rule or feature that drove the decision.
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "personal": {"type": "integer", "enum": [0, 1]},
        "emotional": {"type": "integer", "enum": [0, 1]},
        "reasoning": {"type": "string"},
    },
    "required": ["personal", "emotional", "reasoning"],
    "additionalProperties": False,
}


def classify(client: Anthropic, text: str) -> tuple[dict, object]:
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=[
            {
                "type": "text",
                "text": CODEBOOK,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"Classify this message:\n\n<message>\n{text}\n</message>",
            }
        ],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
    )
    text_block = next(b for b in response.content if b.type == "text")
    return json.loads(text_block.text), response.usage


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY not set. export ANTHROPIC_API_KEY=sk-ant-... and re-run.")

    client = Anthropic()

    with open(INPUT_CSV) as f:
        rows = list(csv.DictReader(f))

    results = []
    failures = []
    p_correct = e_correct = both_correct = 0
    cache_reads = cache_writes = input_tokens = output_tokens = 0

    print(f"Classifying {len(rows)} rows with {MODEL}...\n")
    for i, row in enumerate(rows, 1):
        gold_p = int(float(row["personal"]))
        gold_e = int(float(row["emotional"]))
        try:
            pred, usage = classify(client, row["text"])
        except Exception as exc:
            # Skipped rows leave the agreement denominator, so they are collected
            # and reported explicitly below — otherwise "40/40" could quietly be
            # 38/38 on a run where two calls failed.
            print(f"[{i}/{len(rows)}] {row['id']}: ERROR {type(exc).__name__}: {exc}")
            failures.append((row["id"], f"{type(exc).__name__}: {exc}"))
            continue

        pred_p, pred_e = pred["personal"], pred["emotional"]
        p_match = pred_p == gold_p
        e_match = pred_e == gold_e
        p_correct += p_match
        e_correct += e_match
        both_correct += p_match and e_match

        cache_reads += usage.cache_read_input_tokens or 0
        cache_writes += usage.cache_creation_input_tokens or 0
        input_tokens += usage.input_tokens or 0
        output_tokens += usage.output_tokens or 0

        mark = "OK" if p_match and e_match else "MISS"
        print(
            f"[{i:2d}/{len(rows)}] {row['id']:8s} "
            f"gold P={gold_p}/E={gold_e}  pred P={pred_p}/E={pred_e}  {mark}"
        )

        results.append(
            {
                "id": row["id"],
                "source": row["source"],
                "subreddit": row["subreddit"],
                "gold_p": gold_p,
                "gold_e": gold_e,
                "pred_p": pred_p,
                "pred_e": pred_e,
                "p_match": int(p_match),
                "e_match": int(e_match),
                "pred_reasoning": pred["reasoning"],
                "gold_notes": row.get("notes", ""),
                "text": row["text"],
            }
        )

    n = len(results)
    if n == 0:
        sys.exit("No rows classified.")

    if failures:
        print(f"\n!!! {len(failures)} of {len(rows)} rows failed to classify and are")
        print(f"!!! EXCLUDED from the agreement figures below. Any percentage quoted")
        print(f"!!! from this run is over {n} rows, not {len(rows)}. Re-run before citing it.")
        for rid, why in failures:
            print(f"      {rid}: {why}")

    print(f"\n=== Agreement (n={n} of {len(rows)} gold rows) ===")
    print(f"Personal:  {p_correct}/{n} = {p_correct/n*100:.1f}%")
    print(f"Emotional: {e_correct}/{n} = {e_correct/n*100:.1f}%")
    print(f"Both:      {both_correct}/{n} = {both_correct/n*100:.1f}%  (target ≥85%)")
    print("\nNote: this is in-sample. Rule 2 was tightened to resolve a disagreement on")
    print("rd_a20ea, one of these 40 rows (see coding_scheme.md change log), so perfect")
    print("agreement here is weaker evidence than it looks. See results.md caveats.")

    # Cache + cost
    print(f"\n=== Tokens ===")
    print(f"Cache writes: {cache_writes:,}  Cache reads: {cache_reads:,}")
    print(f"Uncached input: {input_tokens:,}  Output: {output_tokens:,}")
    # Sonnet 4.6: $3/$15 per 1M; cache write 1.25x, cache read 0.1x
    cost = (
        cache_writes * 3.75e-6
        + cache_reads * 0.30e-6
        + input_tokens * 3e-6
        + output_tokens * 15e-6
    )
    print(f"Approx cost: ${cost:.4f}")

    # Disagreements
    misses = [r for r in results if not (r["p_match"] and r["e_match"])]
    if misses:
        print(f"\n=== Disagreements ({len(misses)}) ===")
        for r in misses:
            snippet = r["text"][:120].replace("\n", " ")
            print(f"\n{r['id']} ({r['source']}{'/' + r['subreddit'] if r['subreddit'] else ''}):")
            print(f"  Text:  {snippet}{'...' if len(r['text']) > 120 else ''}")
            print(f"  Gold:  P={r['gold_p']} E={r['gold_e']}  ({r['gold_notes']})")
            print(f"  Pred:  P={r['pred_p']} E={r['pred_e']}  ({r['pred_reasoning']})")

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\nFull results written to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
