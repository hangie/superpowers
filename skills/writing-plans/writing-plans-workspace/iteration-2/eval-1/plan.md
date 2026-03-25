# Split Feature Branch Into Two PRs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split an existing feature branch that contains two unrelated features into two separate PRs — one for the urgent feature that can be reviewed and merged quickly, and one for the slower, more complex feature that can proceed on its own timeline.

**Architecture:** Use interactive git rebase and cherry-pick to isolate commits belonging to each feature onto their own clean branches forked from main. The urgent-feature branch gets its PR created first. The second branch carries only the non-urgent commits and gets its own independent PR against main.

**Tech Stack:** Git (branching, cherry-pick, interactive rebase), GitHub CLI (gh) for PR creation

---

## Phase 1: Audit and Classify Commits

### Task 1.1 — Identify the current state of the mixed branch

- [ ] **Goal:** Establish a complete inventory of every commit on the feature branch that is not on main, so that each commit can be classified as belonging to the urgent feature or the non-urgent feature. This is the foundation for all subsequent work — misclassifying a commit here will cause problems downstream.
- **Files:** None modified. This is a read-only investigation step.
- **Constraints:** Inspect both commit messages and diffs. Commit messages alone may be misleading if commits touch files for both features. If any single commit contains changes for both features (a "mixed commit"), flag it — it will need to be split in a later task.
- **Acceptance criteria:** A written list mapping every commit hash to exactly one of three categories: "urgent", "non-urgent", or "mixed (needs splitting)". The list accounts for every commit between main and the feature branch HEAD.
- **Risks:** If the branch has been rebased or has merge commits from main, the commit topology may be non-linear. Use the merge-base between main and the feature branch as the starting point rather than assuming a simple linear history.

### Task 1.2 — Handle any mixed commits that touch both features

- [ ] **Goal:** If any commits were flagged as "mixed" in the previous task, split them so that each resulting commit belongs cleanly to one feature. This is necessary because cherry-picking a mixed commit onto the urgent branch would bring non-urgent changes along with it.
- **Files:** Whatever files the mixed commits touch. The split will produce new commits with narrower diffs.
- **Constraints:** Use a soft reset or interactive rebase edit to break the mixed commit into two commits — one with only the urgent-feature hunks staged, one with only the non-urgent hunks. Preserve the original commit's authorship metadata on both resulting commits.
- **Acceptance criteria:** After this task, every commit on the branch classifies cleanly as either "urgent" or "non-urgent" with no overlap. Re-running the audit from Task 1.1 confirms no mixed commits remain.
- **Risks:** If a mixed commit has interleaved changes in the same file (not just different files), hunk-level staging is required. This is error-prone — verify the resulting commits each compile and pass tests independently before proceeding.

## Phase 2: Create the Urgent-Feature Branch and PR

### Task 2.1 — Create a clean branch for the urgent feature

- [ ] **Goal:** Create a new branch off of main that contains only the commits classified as "urgent," so the urgent feature has a clean, minimal diff for reviewers. Branching from main (not from the mixed branch) ensures no non-urgent changes leak in.
- **Files:** Only the files touched by urgent-feature commits will appear in the diff.
- **Constraints:** Cherry-pick the urgent commits in their original chronological order to preserve logical progression. If any urgent commit depends on a non-urgent commit (e.g., imports a module introduced by the non-urgent feature), this dependency must be resolved — either by inlining the needed change or by rewriting the urgent commit to be self-contained.
- **Acceptance criteria:** The new branch diverges from main and contains exactly the urgent-feature commits. A diff against main shows only urgent-feature changes. No non-urgent files or hunks are present.
- **Risks:** Cherry-pick conflicts are likely if urgent and non-urgent commits modified the same files. Resolve conflicts by keeping only the urgent-feature intent — do not pull in non-urgent changes to "fix" conflicts.

### Task 2.2 — Verify the urgent-feature branch is healthy

- [ ] **Goal:** Confirm the urgent-feature branch builds, passes lint, and passes all tests, so the PR is ready for review without caveats. A broken PR undermines the goal of fast review and merge.
- **Files:** None modified unless fixes are needed.
- **Constraints:** Run the full validation suite: type checking, linting, and tests. If any check fails, fix it on this branch with a small corrective commit and document what was fixed and why.
- **Acceptance criteria:** All of the following pass on the urgent-feature branch: type checking, linting, and the full test suite. No regressions compared to main.
- **Risks:** If the urgent feature depended on shared infrastructure introduced by the non-urgent feature, tests may fail. This signals a real dependency that needs to be addressed — either by including the shared infrastructure in the urgent branch or by refactoring the urgent feature to not need it.

### Task 2.3 — Push the urgent-feature branch and open a PR

- [ ] **Goal:** Open a pull request for the urgent feature against main so that review can begin immediately. The PR description should make clear this was extracted from a larger branch and is intentionally scoped to the urgent feature only.
- **Files:** None. This is a git and GitHub CLI operation.
- **Constraints:** The PR title should be concise and reflect only the urgent feature's purpose. The PR body should note that a companion PR for the non-urgent feature will follow, so reviewers understand the intentional scoping. Set the base branch to main.
- **Acceptance criteria:** A PR exists on GitHub targeting main, containing only the urgent-feature commits. The PR passes CI checks. The PR description mentions the companion PR.
- **Risks:** If the repository has branch protection rules requiring linear history or specific merge strategies, confirm the branch is compatible before opening the PR.

## Phase 3: Create the Non-Urgent Feature Branch and PR

### Task 3.1 — Create a clean branch for the non-urgent feature

- [ ] **Goal:** Create a new branch off of main that contains only the non-urgent commits, so the non-urgent feature has its own independent review lifecycle. This branch must not depend on the urgent-feature branch — both PRs target main independently.
- **Files:** Only the files touched by non-urgent-feature commits will appear in the diff.
- **Constraints:** Cherry-pick the non-urgent commits in their original order onto a new branch from main. If the non-urgent feature depends on changes from the urgent feature, there are two options: (a) base this branch on the urgent-feature branch instead of main, or (b) duplicate the needed changes. Option (a) is simpler but creates a merge dependency — document whichever choice is made.
- **Acceptance criteria:** The new branch contains exactly the non-urgent-feature commits. A diff against its base branch shows only non-urgent changes.
- **Risks:** If the non-urgent feature is the more complex one, cherry-pick conflicts are more likely to require careful resolution. Take extra care to verify the branch after all cherry-picks are applied.

### Task 3.2 — Verify the non-urgent feature branch is healthy

- [ ] **Goal:** Confirm the non-urgent feature branch builds, passes lint, and passes all tests. Even though this PR is not urgent, sending a broken PR for review wastes reviewer time.
- **Files:** None modified unless fixes are needed.
- **Constraints:** Run the same full validation suite as Task 2.2. If this branch was based on the urgent-feature branch (option (a) from Task 3.1), the tests must also pass with the urgent-feature changes present.
- **Acceptance criteria:** Type checking, linting, and full test suite all pass on the non-urgent feature branch.
- **Risks:** If this branch was based on main but the non-urgent feature actually depends on urgent-feature changes, tests will fail here. This is the correct place to discover that dependency — resolve it before opening the PR.

### Task 3.3 — Push the non-urgent feature branch and open a PR

- [ ] **Goal:** Open a pull request for the non-urgent feature so it can proceed through review on its own timeline. Cross-reference the urgent-feature PR so reviewers understand the relationship.
- **Files:** None. Git and GitHub CLI operation.
- **Constraints:** The PR body should cross-reference the urgent-feature PR by number. If this branch is based on the urgent-feature branch rather than main, note that in the PR description and set the base branch accordingly — it will need to be retargeted to main after the urgent PR merges.
- **Acceptance criteria:** A PR exists on GitHub with the correct base branch, containing only the non-urgent feature commits. The PR description cross-references the urgent-feature PR. CI checks pass.
- **Risks:** If this PR targets the urgent-feature branch and that branch is force-pushed or rebased during review, this PR's diff may become stale. Keep the two branches in sync if changes occur.

## Phase 4: Clean Up

### Task 4.1 — Archive or delete the original mixed branch

- [ ] **Goal:** Remove the original mixed feature branch to avoid confusion, because having three branches for two features creates ambiguity about which branch is canonical.
- **Files:** None. Git operation only.
- **Constraints:** Before deleting, verify that every commit from the original branch is accounted for on one of the two new branches. Do not delete a remote branch if other collaborators may have work based on it — coordinate first.
- **Acceptance criteria:** The original mixed branch no longer exists locally. If it was pushed to the remote, it has been deleted there as well (or renamed with an "archived-" prefix if deletion is too disruptive). Both new PRs are confirmed open and passing CI.
- **Risks:** If any commit was missed during classification, deleting the original branch loses it. The verification step (confirming all commits are accounted for) is the safeguard against this.
