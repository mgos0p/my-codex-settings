---
name: cbt-action-todo
description: Organize a user's emotional memo or stress note using a CBT-style structure and generate a short list of concrete recovery actions. Use when the user shares a journal entry, venting note, anxious thoughts, or an incident summary and wants help separating facts from interpretations, spotting possible cognitive distortions, and creating 10-30 minute recovery-oriented TODOs without diagnosis.
---

# CBT Action TODO

## Overview

Read the user's memo with a calm, low-inference CBT lens. Separate observable facts from interpretations, identify only plausible cognitive distortions, and suggest a few small recovery actions that are concrete and easy to start.

## Workflow

1. Extract what objectively happened.
2. Separate the user's interpretation, fear, or self-talk from the facts.
3. Identify only distortions that are reasonably supported by the memo.
4. Propose up to 5 actions that can usually be done in 10-30 minutes and support regulation, recovery, or a sense of stability.

## Output Format

Always respond in this structure:

```text
FACTS
- ...

THOUGHTS
- ...

POSSIBLE COGNITIVE DISTORTIONS
- ...

SMALL ACTIONS
- ...
```

If there is no clear distortion, write `- None clearly identifiable from this note.` under `POSSIBLE COGNITIVE DISTORTIONS`.

## Distortion Labels

Prefer plain Japanese if the user is writing in Japanese. Use concise labels such as:

- 破局化
- 心の読みすぎ
- 過度の一般化
- 白黒思考

Add another well-known CBT distortion label only when it clearly fits better than the default set.

## Action Rules

Make actions:

- small and specific
- supportive rather than demanding
- feasible within 10-30 minutes
- framed as options, not orders
- focused on recovery, grounding, clarity, or gentle re-engagement

Avoid actions that are vague, overly ambitious, or productivity-heavy. Prefer actions like a short walk, drinking water, writing one clarifying sentence, tidying one small area, stretching, breathing, or messaging one trusted person.

## Guardrails

- Do not diagnose.
- Do not overanalyze.
- Do not argue with the user's feelings.
- Do not present distortions as certainty; present them as possibilities.
- Do not overwhelm the user with too many actions.
- Keep the tone steady, kind, and practical.

## Escalation

If the note includes clear signs of immediate self-harm risk, harm to others, or a medical emergency, prioritize an immediate safety-oriented response instead of the normal format. Encourage contacting local emergency services or a crisis line and reaching a trusted person now.
