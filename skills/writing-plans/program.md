# Writing-plans skill improvement loop

## What you are doing

You are improving `skills/writing-plans/SKILL.md` so that plans it
generates capture intent, constraints, and non-obvious risks — without
prescribing implementation details like code blocks, exact CLI commands,
or pre-written commit messages.

You will do this by running a tight loop:
invoke the skill → read the output → grade it → change one thing →
repeat.

---

## Execution environment

You are in Claude Code. Use native tools only:

- Read files with the Read tool
- Edit files with the Edit tool
- Invoke skills with the Skill tool
- Spawn subagents for generation and grading (see loop steps)

Do NOT:
- Run any shell commands
- Create any directories or workspace folders
- Write or run any Python or shell scripts
- Use `ls`, `cat`, `grep`, `cd`, or any terminal command
- Create grading files, benchmark files, or iteration folders

The only file you write to is `skills/writing-plans/SKILL.md`.
Everything else happens in subagent context or your own context.

---

## Assertion polarity

Assertions in `skills/writing-plans/evals/evals.json` are of two types:

**Fail if present** — the assertion describes something a good plan
should NOT contain. These typically start with "The output contains..."
where the thing described is bad (code blocks, commit messages, CLI
commands, hardcoded function names, etc.).
A plan SCORES A POINT if the bad thing is ABSENT.

**Fail if absent** — the assertion describes something a good plan
SHOULD contain. These typically start with "The output contains at
least one...", "The output mentions...", "The output identifies...".
A plan SCORES A POINT if the good thing is PRESENT.

When in doubt: a point is scored when the plan behaves well on that
assertion.

---

## The loop

### Step 1 — Read the current skill

Read `skills/writing-plans/SKILL.md` using the Read tool.
Hold its contents in mind throughout this iteration.

### Step 2 — Generate plans (generator subagent)

For each eval, spawn a subagent whose only job is to generate the plan.
The generator subagent:
- Receives only the eval prompt as input
- Has access to the writing-plans skill and the codebase at `../[repo-path]`
- Invokes the writing-plans skill and returns the generated plan text
- Knows nothing about the assertions or what is being tested

Do not pass the assertions, the evals.json, or any grading criteria
to the generator subagent. It must generate the plan without knowing
what it is being evaluated against.

Collect the 5 generated plans.

### Step 3 — Grade each plan (grader subagent)

For each generated plan, spawn a separate grader subagent whose only
job is to grade that plan. The grader subagent:
- Receives only: the plan text and the assertions for that eval
- Does NOT receive: SKILL.md, the eval prompt context, or any
  information about what skill version produced the plan
- Goes through every assertion and answers: does this plan score
  a point on this assertion?
- Returns results as a simple list with ✓ or ✗ per assertion and
  a total score

The grader subagent must not know it is grading a plan generated
by a skill under improvement. It grades the plan on its own merits.

Collect scores from all 5 grader subagents:
```
Eval 1 — [prompt summary]
  ✓ The output does not contain a fenced code block
  ✗ The output contains at least one sentence with 'because'
  ✓ ...
Score: 22/30
```

### Step 4 — Compute iteration score

Sum all points across all evals.
Record: Iteration N score — X / 130

Identify the single assertion with the lowest pass rate across evals
(i.e. failing in the most evals).

### Step 5 — Diagnose

Read the current SKILL.md body again.
Find the specific instruction, phrase, or absence of guidance most
likely causing the lowest-scoring assertion to fail.

State your diagnosis explicitly:
> "Assertion X is failing because SKILL.md [contains / lacks] Y."

### Step 6 — Change one thing

Make the smallest possible edit to SKILL.md that addresses the
diagnosis. Change, add, or remove a single instruction or phrase.
Do not restructure sections. Do not rewrite paragraphs.

Record the change:
```
Iteration N
Assertion targeted: [text]
Diagnosis: [what in SKILL.md caused it]
Change: [what was removed or added]
Hypothesis: [why this should fix it]
```

### Step 7 — Check for regression

Re-run Step 2 and Step 3 for the evals most likely affected by this
assertion.

If the targeted assertion improved AND no previously passing assertions
regressed → keep the change, go to Step 1 for the next iteration.

If a regression occurred → revert the change using the Edit tool,
log it as a dead end, pick the next lowest-scoring assertion, go to
Step 5.

---

## Change log

Maintain a running log in your context (do not write to a file).
Each entry:

```
Iteration N
Assertion targeted: [text]
Diagnosis: [cause in SKILL.md]
Change: [exact edit]
Score before: X/130
Score after: X/130
Regressions: none / [list]
Status: kept / reverted
```

---

## Stop conditions

Stop and report when any of the following are true:

1. Overall score >= 117/130 (90% across all evals)
2. Score has not improved for 3 consecutive iterations
3. The same assertion has resisted 3 targeted fix attempts
   (flag it — the assertion may be the problem, not the skill)

---

## Final report

When stopping, state:

```
Final score: X/130

Per-eval scores:
  Eval 1 (PR split):        X/30
  Eval 2 (Tailwind):        X/25
  Eval 3 (Checkout e2e):    X/25
  Eval 4 (Race condition):  X/25
  Eval 5 (Simple rename):   X/25

Changes that improved the score most:
  [top 2-3 from the log]

Assertions still failing:
  [list any that never passed]

Assertions that may need revisiting:
  [any that resisted 3+ fix attempts]
```
