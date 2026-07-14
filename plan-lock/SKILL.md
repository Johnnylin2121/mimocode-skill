---
name: plan-lock
description: Use when creating or executing implementation plans to ensure plan integrity via SHA-256 attestation. Prevents mid-execution plan drift.
---

# Plan Attestation

Ensures implementation plans are not modified during execution without detection.

## Workflow

### 1. After Creating a Plan

```bash
# Compute hash of plan file
Get-FileHash -Algorithm SHA256 plans/your-plan.md | Select-Object -ExpandProperty Hash
```

Store the hash in your notes.md or the plan file header:

```markdown
<!-- ATTESTATION: sha256=<hash> -->
```

### 2. Before Each Task Execution

Re-compute the hash and compare:

```bash
$hash = (Get-FileHash -Algorithm SHA256 plans/your-plan.md).Hash
$attested = "<stored-hash>"
if ($hash -ne $attested) {
  Write-Warning "Plan hash mismatch! Plan may have been modified."
  # Pause and verify with user
}
```

### 3. If Mismatch Detected

- Warn the user immediately
- Show what changed (git diff if in git repo)
- Do NOT proceed until user confirms the changes are intentional

## When to Use

- Plans longer than 5 tasks
- Multi-day implementation projects
- Any plan where integrity matters

## Quick Commands

- **Attest**: `Get-FileHash -Algorithm SHA256 <plan-file>`
- **Verify**: Compare stored hash with current hash
- **Log**: Record hash + timestamp in notes.md

## Limitations

- This is a soft lock (skill-based, not enforced by hook)
- Agent must follow the workflow — it's a discipline, not a hard gate
- For hard enforcement, use the completion-gate hook instead
