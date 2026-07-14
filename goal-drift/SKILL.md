---
name: goal-drift
description: Use when running long tasks (10+ steps) to prevent goal drift. Injects active goal reminders via hook. Auto-triggers via goal-guard hook.
---

# Goal Drift Prevention

This skill works with the `goal-guard.ts` hook to keep agents focused during long tasks.

## How It Works

The `goal-guard` hook automatically injects the active goal and next step into every LLM turn. This prevents the common problem of forgetting the original task after 50+ tool calls.

## The Discipline

1. **Read the goal reminder** at the start of each turn
2. **Stay on task** — implement ONLY what the current task covers
3. **Don't gold-plate** — minimal implementation, not "while I'm here" improvements
4. **If you drift**, the goal reminder will catch it on the next turn

## Disabling Per-Session

Set environment variable: `MIMOCODE_GOAL_GUARD=0`

## Configuration

The hook reads from your checkpoint's §1 (Active Intent) and §2 (Next Action). Keep these sections updated for best results.
