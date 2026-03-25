## Iteration 1 — 2026-03-23
**Assertion targeted:** All "fail if present" code/command assertions (fenced code blocks, git commit -m, Expected: PASS/FAIL, git add, Run:, test function definitions, import syntax, variable declarations, commit messages, expected output predictions) — these fail across all 5 evals
**Diagnosis:** SKILL.md's "Task Structure" section (lines 63-104) is a template that explicitly prescribes fenced code blocks with language names, `git commit -m` commands, `git add` commands, `Run:` commands with CLI flags, test function definitions, import syntax, variable declarations, `Expected: PASS/FAIL` predictions, and conventional commit messages. The "Remember" section reinforces with "Complete code in plan" and "Exact commands with expected output." The "Overview" also says to document "code".
**Change:** Replaced the entire "Task Structure" template and "Remember" section with intent-based guidance: tasks describe what/why, not how. Added explicit "What plans must NOT contain" list. Added "Proportionality" guidance. Added "What makes a good plan" section covering why-reasoning, risks, success criteria, completion criteria. Updated Overview to describe intent-based planning.
**Result:** 44.6% → TBD (re-running)
**Regressions:** TBD
**Status:** TBD
