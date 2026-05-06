# Coding Scheme: Personal & Emotional Content

## Purpose

Binary classification of first-turn messages (WildChat) and opening posts (Reddit) on two independent dimensions, to answer:

> Among first-turn messages to a general-purpose chatbot versus opening posts on public Reddit advice forums, what proportion of each are **personal** and **emotional**, and do the distributions differ?

## The two dimensions

Each message gets two independent binary codes.

### Personal (P)
- **P = 1** if BOTH conditions hold:
  - (a) the author is the subject — describing their own life or situation, AND
  - (b) the topic falls in a **life domain**: relationships, body/health, finances, feelings, decisions, identity, work/career, or a significant personal problem.
- **P = 0** if *either*:
  - (a) the author isn't the subject — tasks, creative writing, factual questions about the world, or discussion of a third party, OR
  - (b) the author *is* the subject but the topic is **everyday logistics** — parking, directions, shopping, travel tips, quick how-tos, recommendations. Being self-involved in a logistical question ≠ personal.

### Emotional (E)
- **E = 1** if the message contains an **explicit emotion word** referring to the author's own state (*frustrated, stuck, lost, plagued, devastated, nervous, excited, overwhelmed*) OR **clear affective phrasing that names an internal state** (*"can't stop [worrying/thinking]," "don't know what to do," "losing my mind"*). Affective phrasing must signal a mental or emotional state — not merely describe an observable behavior.
- **E = 0** if the tone is neutral, deliberative, curious, or task-oriented — even when the topic is weighty.

P and E are **independent**. A message can be any combination: 0/0, 1/0, 0/1, or 1/1.

## The three rules

### Rule 1 — Framing over topic
The *framing* of the message determines P, not the topic alone. A factual or creative-writing question about an intimate topic (drugs, sex, mental health, money) is **P=0** if the author isn't the subject. Only the author's self-involvement makes it personal.

### Rule 1b — Self-involvement alone is not enough
Being the subject of your own question doesn't automatically make it personal. "Where should I park?" or "What hike should I do?" is self-involved but logistical — **P=0**. P=1 requires the message to be in a life domain (see definition above). This rule prevents "personal" from inflating with routine self-directed requests.

### Rule 2 — Strict threshold for emotional language
E=1 requires explicit emotion words or clear affective phrasing (see examples above). Polite closings (*"thanks :)"*), mild interjections (*"yay"*), and playful tone do **not** count as emotional.

### Rule 3 — Content ≠ affect (the most important rule)
Do **not** code E=1 merely because the *topic* is emotionally heavy. E=1 requires the author's *language* to express feeling, not the topic to imply it. A measured, analytical post about sexual inexperience or grief is still E=0 if the author chose neutral language.

## Worked examples from the 40-post pilot

### Clear P=0 examples (tasks, factual questions, creative writing)

| Post text (abridged) | P | E | Why |
|---|---|---|---|
| *"On OSX — Window > Extended Controls > Video Filter..."* | 0 | 0 | Technical how-to; author not subject |
| *"Does Transformers architecture feature pairwise attention..."* | 0 | 0 | Technical question about the world |
| *"Rearrange the following words: Bob / coffee / soothes"* | 0 | 0 | Puzzle task |
| *"You are an expert in strategic analysis... PESTLE factors for Amazon"* | 0 | 0 | Coursework/professional task |
| *"Caroline Hertig is a young executive... write an excerpt from her bladder diary"* | 0 | 0 | Role-play about a fictional character. **Tests Rule 1** — intimate topic, impersonal framing |
| *"Monster Hunter Gunlance player slander version..."* | 0 | 0 | Creative writing continuation |
| *"will there ever be a substance to replace cannabis..."* | 0 | 0 | Speculative question about the world |
| *"Please tell me the best places to park if I go to devil's bridge trail in sedona..."* | 0 | 0 | Self-involved but logistical (parking). **Rule 1b exemplar.** |

### Clear P=1 examples, split on E

| Post text (abridged) | P | E | Why |
|---|---|---|---|
| *"This has **plagued me** for a while; I'll be talking to someone and they have an opposing opinion..."* | 1 | 1 | "Plagued me" = explicit affective self-description |
| *"We've been on 5 dates... she never uses my name. What should I read into this?"* | 1 | 0 | Personal situation; curious/puzzled tone, no affect |
| *"I have about 25k to my name. 12k in student loans... best way to allocate my money?"* | 1 | 0 | Personal finance; purely deliberative tone |
| *"I have zero to no self-confidence, found it difficult to talk on Omegle... I still need to practice my social skills"* | 1 | 0 | Trait description ("self-confidence"), not acute affect |
| *"how do i mingle? I don't want to interrupt... Thanks :)"* | 1 | 0 | Personal networking question; casual, zero emotion words |
| *"This is from someone who's never even kissed a girl... invisible to only me"* | 1 | 0 | **Rule 3 exemplar** — emotionally freighted topic, analytical language |

## Decision checklist (when coding)

For each post, in this order:

1. **Is the author the subject of the message?** Not just "is the topic personal" — is the author describing their own life/situation/feelings?
   - If no → **P=0**. Stop on P.
   - If yes → continue to step 2.
2. **Is the topic in a life domain?** Relationships, body/health, finances, feelings, decisions, identity, work/career, or a significant personal problem?
   - If no (logistics, directions, shopping, how-tos) → **P=0**.
   - If yes → **P=1**.
3. **Does the post contain an explicit emotion word or clear affective phrasing?**
   - If yes → **E=1**.
   - If no → **E=0**, even if the topic is heavy.

## Common failure modes to watch for

- **Confusing topic with affect.** Sexual shame, financial stress, grief — these topics *feel* emotional to read, but code the language, not the feeling. (Rule 3.)
- **Role-play / creative writing about intimate topics.** The topic is personal-sounding but the author isn't the subject. (Rule 1.)
- **Chronic trait descriptions** ("low self-confidence," "I'm an introvert"). These describe stable traits, not acute feelings. Usually **E=0**.
- **Behavioral / physical descriptions.** Actions or bodily reactions that *imply* emotion ("my face went red," "I was blushing," "I couldn't remember what I said," "I avoided eye contact") describe observable behavior, not a named internal state. Per Rule 3, code the language, not the feeling the reader infers. **E=0.**
- **Polite/casual closings.** "thanks :)", "Yay", "lol" — these are social markers, not emotional disclosure. **E=0**.
- **Over-counting on Reddit.** Reddit advice posts are almost all P=1, but most are **E=0**. Don't default to E=1 just because it's an advice subreddit.

## Edge cases still open for refinement

- **Weak affective language** (*"it's frustrating," "I find this confusing"*) — currently E=0 unless the author names their own state. May tighten/loosen after more coding.
- **Implicit affect via metaphor** (*"invisible to only me," "I'm missing out"*) — currently E=0 under strict Rule 2. Revisit if many posts hinge on this.
- **Behavioral descriptions implying emotion** — *resolved 2026-04-25:* explicitly E=0 (see "Behavioral / physical descriptions" under failure modes). Trigger: the rd_a20ea blushing-and-memory-blank post, where the LLM coded E=1 on `"can't even remember if I said thanks"` and the human coded E=0 on the strict "named internal state" reading. Codebook now requires named state, not implied behavior.
