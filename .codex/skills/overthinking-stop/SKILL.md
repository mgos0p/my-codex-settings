---
name: overthinking-stop
description: Help the user stop overthinking by compressing a situation into one sentence, separating real unknowns from imagined ones, and offering one grounding action they can do immediately. Use when the user is looping on a decision, replaying possibilities, asking for repeated analysis of the same situation, or showing signs of rumination and wants to regain traction quickly.
---

# Overthinking Stop

## Overview

Interrupt analysis spirals quickly.
Reduce the situation to a short, stabilizing response that helps the user move from rumination to action.

## Response Flow

Follow this sequence:

1. Summarize the situation in one sentence.
2. List only what is actually unknown.
3. Suggest one grounding action the user can do now.

## Rules

- Do not extend the analysis.
- Do not add new branches, frameworks, pros/cons lists, or hypotheticals.
- Do not speculate about the future.
- Keep the response short and calm.
- Prefer plain language over therapeutic jargon.
- If the user asks for more analysis, first offer the same compression pattern again before expanding.

## What Counts As Unknown

- Include missing facts, decisions not yet made, and information the user cannot currently verify.
- Exclude imagined outcomes, mind-reading, and recursive "what if" branches.

## Output Shape

Use a compact format like:

Situation: ...
Unknowns:
- ...
- ...
Next step: ...

If there are no real unknowns, say so directly and move to the next step.

## Example

Situation: You are trying to decide whether to send the message now or wait because you keep replaying how it might land.
Unknowns:
- Whether the person is available right now
- Whether you want this resolved today or later
Next step: Put the message in one draft, then step away for five minutes before deciding send or wait.

Keep examples short. The skill exists to stop looping, not to produce a deeper interpretation.
