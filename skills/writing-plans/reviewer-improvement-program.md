# Plan Document Reviewer Improvement Loop

## What you are doing

You are improving `skills/writing-plans/plan-document-reviewer-prompt.md` so that
the reviewer catches implementation flaws — assumptions in the plan that contradict
what the actual source files contain.

The existing reviewer already checks plan quality against the spec. That is working
and must not regress. The gap is codebase alignment: a plan can be well-formed,
spec-compliant, and completely wrong about what an existing function returns, what
parameters it accepts, or whether the abstraction it proposes already exists.

You will close this gap by running a tight loop:
dispatch reviewer with flawed plan + source files → grade output → change one
thing → repeat.

**Announce at start:** "I'm using the reviewer-improvement-program to improve
plan-document-reviewer-prompt.md."

---

## Execution environment

You are in Claude Code. Use native tools only:

- Read files with the Read tool
- Edit files with the Edit tool
- Spawn subagents with the Task tool

Do NOT:
- Run any shell commands
- Create directories or workspace folders
- Write or run Python or shell scripts

The only file you write to is `skills/writing-plans/plan-document-reviewer-prompt.md`.
Everything else happens in subagent context or your own context.

---

## Assertion polarity

Assertions are of two types:

**Fail if present** — describes something the reviewer output should NOT contain.
The reviewer SCORES A POINT if the bad thing is ABSENT.
These typically describe incorrect behavior: approving a flawed plan, missing
a specific concern, using vague non-actionable language.

**Fail if absent** — describes something the reviewer output SHOULD contain.
The reviewer SCORES A POINT if the good thing is PRESENT.
These typically describe correct behavior: flagging the flaw, naming the
specific file or function, producing "Status: Issues Found."

When in doubt: a point is scored when the reviewer behaves correctly on that
assertion.

The most important assertion in every eval:

> "The output contains 'Status: Approved'"

This is always **fail if present**. A flawed plan that receives approval is
the core failure mode being tested. Every eval must include this assertion.

---

## The loop

### Step 1 — Read the current reviewer prompt

Read `skills/writing-plans/plan-document-reviewer-prompt.md` using the Read tool.
Hold its contents in mind throughout this iteration.

Also read `skills/writing-plans/evals/reviewer-evals.json` to load all eval inputs.

---

### Step 2 — Dispatch reviewer subagents

For each eval in `reviewer-evals.json`, dispatch a reviewer subagent whose only
job is to review the plan in that eval.

The reviewer subagent:
- Receives the eval's `spec`, `plan`, and `source_files` as formatted text
- Uses the current reviewer prompt as its operating instructions
- Is told: "You are reviewing a plan document. Here are the inputs:"
  - Spec: [spec text]
  - Plan: [plan text]
  - Source files: [each file formatted as "File: path\n\n[content]"]
- Returns its complete reviewer output including Status, Issues, and Recommendations

Do NOT tell the reviewer subagent what flaw to look for.
Do NOT tell it which assertion it is being evaluated against.
Do NOT tell it it is being used in an improvement loop.
It reviews the plan on its own merits using the reviewer prompt as instructions.

Collect all reviewer outputs. Label each with its eval ID.

---

### Step 3 — Grade each output (grader subagent)

For each reviewer output, dispatch a separate grader subagent whose only job
is to grade that output.

The grader subagent:
- Receives only: the reviewer output text and the assertions for that eval
- Does NOT receive: the reviewer prompt, the plan, the source files, the known
  flaw description, or any context about what is being tested
- Works through every assertion and answers: does this reviewer output score a
  point on this assertion?
- Returns results as a list with ✓ or ✗ per assertion and a total score

```
Eval 1 — array vs dict
  ✓ The output does not contain 'Status: Approved'
  ✗ The output contains the word 'array'
  ✓ The output contains 'list_modules'
  ✓ The output contains 'Issues Found'
Score: 3/4
```

Collect scores from all grader subagents.

---

### Step 4 — Compute iteration score

Sum all points across all evals.
Record: **Iteration N score — X / [total possible]**

Identify the single assertion with the lowest pass rate across evals
(failing in the most evals).

---

### Step 5 — Diagnose

Read the current reviewer prompt again.
Find the specific instruction, phrase, or absence of guidance most likely
causing the lowest-scoring assertion to fail.

State your diagnosis explicitly:

> "Assertion X is failing because the reviewer prompt [contains / lacks] Y."

The most common root causes:
- The reviewer has no instruction to read source files at all
- The reviewer has a source file instruction but no guidance on what to check
- The reviewer checks for the right thing but the calibration says "approve unless
  serious" and it is treating codebase mismatches as non-serious
- The reviewer prompt has no structured category for codebase alignment issues

---

### Step 6 — Change one thing

Make the smallest possible edit to the reviewer prompt that addresses the
diagnosis. Change, add, or remove a single instruction or phrase.
Do not restructure sections. Do not rewrite paragraphs.

Record the change:

```
Iteration N
Assertion targeted: [text]
Diagnosis: [what in the prompt caused the failure]
Change: [what was removed or added, verbatim]
Hypothesis: [why this should fix it]
```

---

### Step 7 — Check for regression

Re-run Steps 2 and 3 for the evals most likely affected by this change.

Compare against the previous iteration's scores for those evals.

If the targeted assertion improved AND no previously passing assertions
regressed → keep the change, go to Step 1 for the next iteration.

If a regression occurred → revert the change using the Edit tool, log it
as a dead end, pick the next lowest-scoring assertion, go to Step 5.

---

## Change log

Maintain a running log in your context (do not write to a file).
Each entry:

```
Iteration N
Assertion targeted: [text]
Diagnosis: [cause in reviewer prompt]
Change: [exact edit made]
Score before: X/Y
Score after: X/Y
Regressions: none / [list affected evals and assertions]
Status: kept / reverted
```

---

## Stop conditions

Stop and report when any of the following are true:

1. Overall score >= 90% across all evals
2. Score has not improved for 3 consecutive iterations
3. The same assertion has resisted 3 targeted fix attempts — flag it, the
   assertion wording may need redesigning rather than the reviewer prompt

---

## Baseline run

Before making any changes, run Steps 2 and 3 once with the current unmodified
reviewer prompt. This establishes the red baseline — proving each eval currently
fails before you attempt to fix it.

Record: **Baseline score — X / [total possible]**

If any eval already passes at baseline, note it. That eval may be testing
something the reviewer already handles, and should be redesigned to target
a genuine gap.

---

## Final report

When stopping, produce:

```
Final score: X/Y
Baseline score: X/Y
Improvement: +N points

Per-eval scores:
  Eval 1 (array vs dict):             baseline X/4 → final X/4
  Eval 2 (duplicate implementation):  baseline X/4 → final X/4
  Eval 3 (wrong parameter name):      baseline X/4 → final X/4
  Eval 4 (phase dependency gap):      baseline X/4 → final X/4

Changes that improved the score most:
  [top 2-3 from the change log with points gained]

Assertions still failing:
  [list any that never passed across all iterations]

Assertions that may need redesigning:
  [any that resisted 3+ targeted fix attempts]

Recommended next evals to add:
  [flaw categories not yet covered that emerged during testing]
```
