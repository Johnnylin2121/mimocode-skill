---
name: active-notes
description: Use when running multi-step tasks to proactively capture findings, decisions, and knowledge in notes.md. Works with notes-reminder hook.
---

# Active Notes System

Transforms notes.md from an empty scratchpad into a structured knowledge capture system.

## When to Write to notes.md

Write to notes.md when you:
- Discover something non-obvious about the codebase
- Make an architectural or design decision
- Encounter an error pattern worth remembering
- Learn a fact that should survive session boundaries
- Complete a significant milestone in a multi-step task

## Structure

Use these sections in notes.md:

```markdown
## [turn N · timestamp]

### Findings
- `src/file.ts:42` — key insight about how X works

### Decisions
- Chose Y over Z because [rationale]

### Errors to Remember
- Error X happens when Y → fix: do Z

### Cross-Session Knowledge
- [fact worth promoting to MEMORY.md via dream]
```

## Size Guidance

- Keep entries concise (1-2 lines each)
- Aim for 5-10 entries per session, not 50
- Focus on NON-OBvious knowledge (things you wouldn't guess from code alone)
- Use file:line references so you can find things later

## How This Connects to Memory

1. **notes.md** → captured during session
2. **checkpoint.md** → writer merges notes at checkpoint events
3. **MEMORY.md** → dream promotes durable knowledge from checkpoints
4. **Search** → BM25 finds notes across sessions

## Anti-Patterns

- Don't dump entire code blocks (reference file:line instead)
- Don't narrate what you're doing ("now I'm editing X") — capture WHAT you learned
- Don't duplicate info already in MEMORY.md — search first
