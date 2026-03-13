---
name: reflection-organizer
description: Organize a user's diary entry, thought memo, or emotional note into structured reflection fields with simple mood and energy scores. Use when the user wants to structure, rewrite, or clean up personal reflection notes, journaling fragments, anxious thoughts, or messy emotional memos into DATE, MOOD_SCORE, ENERGY_SCORE, EVENT, FEELINGS, THOUGHTS, ACTION, and NEXT_SMALL_STEP without adding interpretation or psychological analysis.
---

# Reflection Organizer

Organize the user's diary or memo into a short reflection format while preserving the user's original wording as much as possible.

## Output Format

Always return the memo in this exact structure:

```text
DATE
- ...

MOOD_SCORE
- ...

ENERGY_SCORE
- ...

EVENT
- ...

FEELINGS
- ...

THOUGHTS
- ...

ACTION
- ...

NEXT_SMALL_STEP
- ...
```

## Instructions

- Read the user's memo closely before organizing it.
- Extract only what is explicitly present in the memo.
- Keep the user's wording whenever possible.
- Rewrite for clarity and brevity, but do not add new meaning.
- If the date is not stated, use today's date in the user's local context.
- Set `MOOD_SCORE` to a simple 1-10 score based on the user's stated mood or the overall tone of the memo.
- Set `ENERGY_SCORE` to a simple 1-10 score based on the user's stated energy, fatigue, motivation, or activity level.
- Keep score reasoning minimal and do not explain it unless the user asks.
- If `ACTION` is not present, keep it brief and indicate that no clear action was stated.
- Provide exactly one concrete action in `NEXT_SMALL_STEP`.
- Keep the result concise and easy to scan.

## Rules

- Do not add interpretation.
- Do not do psychological analysis.
- Do not explain causes, diagnoses, or hidden motives.
- Do not moralize or give long advice.
- Do not expand beyond the content the user gave.
- Do not let the scores turn into a long evaluation.

## Style

- Use simple, calm language.
- Prefer short bullet points.
- Preserve emotionally important phrases from the user when possible.
- Keep scores compact, such as `7/10`.
- Avoid sounding clinical or overly polished.
