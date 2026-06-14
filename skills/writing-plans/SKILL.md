---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Writing Plans

## Overview

Write implementation plans that transfer **decisions**, not **work**. A decision is a choice you have already made: the behavior a test must enforce, the signature another task depends on, a constraint that cannot be violated. The work is producing the implementation that satisfies those decisions. Pin every decision precisely; leave the work to the implementing agent, who is skilled and will write the actual implementation against the contracts you set.

The line matters because of *how* each kind of detail ages. A decision — a test's assertions, an interface's types, an exact version floor — does not rot: it constrains reality rather than predicting it, and if it is wrong it fails loudly and immediately. A prediction — a line number, an expected output string, a pre-guessed implementation body — rots the moment the code moves, and a wrong one silently anchors the implementer into reproducing your mistake. Capture the first. Never write the second.

Plans should be proportionate to the task. A simple rename gets a short plan. A complex migration gets phased grouping. A bug fix that needs investigation front-loads diagnosis before prescribing solutions.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** If working in an isolated worktree, it should have been created via the `superpowers:using-git-worktrees` skill at execution time.

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

Each task pins the **decisions** an implementer must honor and leaves them the **work** of satisfying those decisions. Capture the contract — what must be true when the task is done — precisely enough that a fresh agent with no other context cannot drift from it. Do not pre-solve the implementation for them.

### What each task should contain

- **Goal:** What this task accomplishes and why it matters in the larger plan
- **Files:** Which files to create or modify (exact paths where known — omit line-number ranges, they drift)
- **Interfaces:** The exact signatures this task consumes from earlier tasks and produces for later ones — function/method names, parameter and return types. A subagent sees only its own task; this block is how it learns the names and types neighboring tasks rely on. Copy them verbatim — they are decisions, not prose.
- **Tests:** Pre-write the tests. A test encodes the *decision* about what correct behavior is, so show the assertions that define "right" for this task. Tests are the one form of code a plan should contain (see below).
- **Constraints:** Non-obvious requirements, edge cases, gotchas, and any project-wide values the task must honor (version floors, flag defaults, naming rules) — copy exact values verbatim from the spec.
- **Acceptance criteria:** Observable outcomes that prove the task is done (e.g. "tests pass", "no remaining references to X", "verified working with Y")
- **Risks:** Anything that could go wrong or require a change of approach

### What plans must NOT contain

A plan pins decisions and then stops. It does not do the implementer's work for them, and it does not record details that rot. Do not include:

- **Pre-written implementation bodies** — function internals, the algorithm, the actual fix. That is the work. Writing it ahead of time does the agent's job for them (often wrong), and a wrong body anchors them into reproducing your mistake. Specify the *contract* through tests and interfaces; let them write the body to satisfy it.
- **Line-number ranges** (`file.py:123-145`) — they drift the instant anything above them changes.
- **Expected terminal output** (`Expected: PASS`, "you should see…") — a prediction about a run you have not done.
- **Pre-written commit messages** — written before the work that justifies them exists.

What a plan SHOULD carry precisely and verbatim: the **tests** that define correct behavior, the **interface signatures** tasks share, and any **exact constraint values**. Those are decisions — pin them. Everything else is intent, expressed in prose: say "Commit the test and implementation together," not a `git commit` line; say "Implement the minimal code to satisfy the test," not the function body.

### Proportionality

Match plan complexity to task complexity. A simple rename needs 2-4 tasks. A migration of 47 components needs phased grouping, not 47 individual tasks. If the task requires investigation before a fix can be designed, front-load investigation tasks and acknowledge that later tasks may change depending on findings.

## What makes a good plan

- Every decision an implementer could otherwise re-derive differently — test assertions, shared interface signatures, exact constraint values — is pinned verbatim and unambiguously
- Every task explains *why* it matters (use "because", "in order to", "so that")
- Risks, constraints, and non-obvious concerns are called out explicitly (use "risk", "constraint", "important", "note that", "caveat", "careful")
- The plan describes what success looks like as an observable outcome, not just a list of steps to perform
- Completion criteria are concrete and verifiable ("passes", "verified", "no remaining", "confirmed", "complete when")
- The plan starts with a clear statement of the goal, intent, or purpose of the work

## Self-Review

After writing the complete plan, look at the spec with fresh eyes and check the plan against it. This is a checklist you run yourself — not a subagent dispatch.

**1. Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? List any gaps.

**2. Decisions-vs-work scan:** Two checks. (a) Did you *pin* every decision an implementer could otherwise re-derive differently — test assertions, shared interface signatures, exact constraint values? Add any that are missing. (b) Did you *leak* any of the "must NOT contain" patterns — pre-written implementation bodies, line-number ranges, expected output, commit messages? Strip them back to intent.

**3. Interface consistency:** Do the signatures, types, and property names in each task's Interfaces block match across tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug — and the kind a context-isolated subagent will faithfully reproduce.

If you find issues, fix them inline. No need to re-review — just fix and move on. If you find a spec requirement with no task, add the task.

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
