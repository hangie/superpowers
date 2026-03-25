---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Writing Plans

## Overview

Write implementation plans that capture intent, constraints, and risks — not implementation details. The implementing agent is skilled and will write the actual code, commands, and tests. Your job is to give them the strategic picture: what to build, why, what could go wrong, and what "done" looks like.

Plans should be proportionate to the task. A simple rename gets a short plan. A complex migration gets phased grouping. A bug fix that needs investigation front-loads diagnosis before prescribing solutions.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** This should be run in a dedicated worktree (created by brainstorming skill).

**Save plans to:** `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

## Task Structure

Each task describes **what** to accomplish and **why**, not **how**. The implementing agent will write the actual code, commands, and tests — your job is to set them up for success by capturing intent, constraints, and risks they might not see.

### What each task should contain

- **Goal:** What this task accomplishes and why it matters in the larger plan
- **Files:** Which files to create or modify (use exact paths where known)
- **Constraints:** Non-obvious requirements, edge cases, or gotchas the implementer needs to know
- **Acceptance criteria:** Observable outcomes that prove the task is done (e.g. "tests pass", "no remaining references to X", "verified working with Y")
- **Risks:** Anything that could go wrong or require a change of approach

### What plans must NOT contain

Plans capture intent — they do not prescribe implementation. The implementing agent needs freedom to adapt when reality diverges from the plan. Do not include:

- Code blocks or inline code with implementation logic (no function definitions, no variable declarations, no imports)
- Exact shell commands, CLI invocations, or run instructions (no `Run:`, no `git commit -m`, no `npm run`)
- Pre-written test code or test function signatures
- Expected terminal output predictions (no `Expected: PASS` or `You should see:`)
- Pre-written commit messages

Instead, describe the *intent* behind each step in plain prose. For example, instead of writing a test function, say "Write a test that verifies [specific behavior] when [specific condition]." Instead of a git command, say "Commit the test and implementation together."

### Proportionality

Match plan complexity to task complexity. A simple rename needs 2-4 tasks. A migration of 47 components needs phased grouping, not 47 individual tasks. If the task requires investigation before a fix can be designed, front-load investigation tasks and acknowledge that later tasks may change depending on findings.

## What makes a good plan

- Every task explains *why* it matters (use "because", "in order to", "so that")
- Risks, constraints, and non-obvious concerns are called out explicitly (use "risk", "constraint", "important", "note that", "caveat", "careful")
- The plan describes what success looks like as an observable outcome, not just a list of steps to perform
- Completion criteria are concrete and verifiable ("passes", "verified", "no remaining", "confirmed", "complete when")
- The plan starts with a clear statement of the goal, intent, or purpose of the work

## Plan Review Loop

After writing the complete plan:

1. Dispatch a single plan-document-reviewer subagent (see plan-document-reviewer-prompt.md) with precisely crafted review context — never your session history. This keeps the reviewer focused on the plan, not your thought process.
   - Provide: path to the plan document, path to spec document
2. If ❌ Issues Found: fix the issues, re-dispatch reviewer for the whole plan
3. If ✅ Approved: proceed to execution handoff

**Review loop guidance:**
- Same agent that wrote the plan fixes it (preserves context)
- If loop exceeds 3 iterations, surface to human for guidance
- Reviewers are advisory — explain disagreements if you believe feedback is incorrect

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `docs/superpowers/plans/<filename>.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development
- Fresh subagent per task + two-stage review

**If Inline Execution chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:executing-plans
- Batch execution with checkpoints for review
