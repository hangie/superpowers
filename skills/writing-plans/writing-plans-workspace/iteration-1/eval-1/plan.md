# Split Feature Branch into Two Clean PRs - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split a feature branch containing two unrelated features into two separate PRs -- one urgent PR that can be reviewed and merged quickly against main, and one non-urgent PR for the slower, more complex feature.

**Architecture:** Use `git cherry-pick` to selectively apply commits from the mixed feature branch onto two new branches, each forked from main. The urgent feature gets its own clean branch with only its commits, enabling fast review and merge. The non-urgent feature gets a separate branch with its commits, decoupled from the urgent work.

**Tech Stack:** Git (branching, cherry-pick, interactive log analysis), GitHub CLI (`gh`) for PR creation

---

## File Structure

No new source files are created. This plan operates entirely at the git/branch level:

- **Source of truth:** The existing mixed feature branch (referred to as `feature/mixed` below -- substitute the actual branch name)
- **New branch 1:** `feature/urgent` -- forked from `main`, receives only urgent-feature commits
- **New branch 2:** `feature/non-urgent` -- forked from `main`, receives only non-urgent-feature commits

---

### Task 1: Audit the Mixed Feature Branch

**Files:**
- Read: git log output (no files modified)

- [ ] **Step 1: Identify the merge base with main**

```bash
git merge-base main feature/mixed
```

Record this commit hash. Every commit between this hash and `HEAD` of `feature/mixed` is in scope.

- [ ] **Step 2: List all commits on the feature branch since it diverged from main**

```bash
git log --oneline --reverse main..feature/mixed
```

Expected: A list of commits, each on one line with hash and message.

- [ ] **Step 3: Categorize each commit**

Go through each commit from step 2. For every commit, run:

```bash
git show --stat <commit-hash>
```

Create two lists in a scratch file or notes:
- **URGENT commits:** commits that belong to the urgent feature (list their hashes in chronological order)
- **NON-URGENT commits:** commits that belong to the non-urgent feature (list their hashes in chronological order)

If any commit touches files from both features, flag it -- it will need to be split (see Task 4).

- [ ] **Step 4: Verify no commits are missed**

Count: (number of URGENT commits) + (number of NON-URGENT commits) + (number of MIXED commits) should equal total commits from step 2. If not, re-examine.

- [ ] **Step 5: Commit your categorization notes**

Save the commit categorization to a temporary file for reference:

```bash
cat > /tmp/branch-split-plan.txt << 'EOF'
URGENT COMMITS (in order):
<hash1> <message1>
<hash2> <message2>
...

NON-URGENT COMMITS (in order):
<hash3> <message3>
<hash4> <message4>
...

MIXED COMMITS (need splitting):
<hash5> <message5> -- touches both features
EOF
```

---

### Task 2: Create the Urgent Feature Branch

**Files:**
- No source files modified directly -- git operations only

- [ ] **Step 1: Create a fresh branch from main**

```bash
git checkout main
git pull origin main
git checkout -b feature/urgent
```

Expected: You are now on `feature/urgent`, identical to `main`.

- [ ] **Step 2: Cherry-pick the urgent commits in chronological order**

For each urgent commit hash identified in Task 1, Step 3:

```bash
git cherry-pick <urgent-hash-1>
git cherry-pick <urgent-hash-2>
# ... repeat for each urgent commit in order
```

If a cherry-pick produces a conflict:
1. Run `git status` to see conflicted files
2. Open each conflicted file and resolve the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
3. Run `git add <resolved-file>`
4. Run `git cherry-pick --continue`

Expected: Each cherry-pick applies cleanly or is resolved manually.

- [ ] **Step 3: Verify the urgent branch has only urgent changes**

```bash
git diff main..feature/urgent --stat
```

Expected: Only files related to the urgent feature appear. No files belonging to the non-urgent feature should be listed.

- [ ] **Step 4: Run the test suite to verify nothing is broken**

```bash
bun test
```

Expected: All tests pass. If any fail, investigate whether the failure is due to a missing dependency on a non-urgent commit. If so, that commit was miscategorized and needs to be included.

- [ ] **Step 5: Run lint and type checks**

```bash
bun run lint
```

Expected: No errors. If there are lint/type errors, fix them and commit the fix on this branch.

---

### Task 3: Create the Non-Urgent Feature Branch

**Files:**
- No source files modified directly -- git operations only

- [ ] **Step 1: Create a fresh branch from main**

```bash
git checkout main
git checkout -b feature/non-urgent
```

Expected: You are now on `feature/non-urgent`, identical to `main`.

- [ ] **Step 2: Cherry-pick the non-urgent commits in chronological order**

For each non-urgent commit hash identified in Task 1, Step 3:

```bash
git cherry-pick <non-urgent-hash-1>
git cherry-pick <non-urgent-hash-2>
# ... repeat for each non-urgent commit in order
```

Handle conflicts the same way as Task 2, Step 2.

- [ ] **Step 3: Verify the non-urgent branch has only non-urgent changes**

```bash
git diff main..feature/non-urgent --stat
```

Expected: Only files related to the non-urgent feature appear.

- [ ] **Step 4: Run the test suite**

```bash
bun test
```

Expected: All tests pass.

- [ ] **Step 5: Run lint and type checks**

```bash
bun run lint
```

Expected: No errors.

---

### Task 4: Handle Mixed Commits (if any)

**Files:**
- Whichever source files the mixed commit touches

Skip this task entirely if no commits were flagged as MIXED in Task 1, Step 3.

- [ ] **Step 1: For each mixed commit, inspect the full diff**

```bash
git show <mixed-hash>
```

Identify which hunks belong to the urgent feature and which belong to the non-urgent feature.

- [ ] **Step 2: Apply the urgent portion to feature/urgent**

```bash
git checkout feature/urgent
git cherry-pick --no-commit <mixed-hash>
```

This stages all changes without committing. Now unstage the non-urgent parts:

```bash
git reset HEAD <non-urgent-file-1> <non-urgent-file-2>
git checkout -- <non-urgent-file-1> <non-urgent-file-2>
```

If the mixed commit changes both features within the same file, manually edit the file to keep only the urgent changes, then:

```bash
git add <file>
git commit -m "feat: <urgent portion of original message>"
```

- [ ] **Step 3: Apply the non-urgent portion to feature/non-urgent**

```bash
git checkout feature/non-urgent
git cherry-pick --no-commit <mixed-hash>
git reset HEAD <urgent-file-1> <urgent-file-2>
git checkout -- <urgent-file-1> <urgent-file-2>
git add <file>
git commit -m "feat: <non-urgent portion of original message>"
```

- [ ] **Step 4: Re-run tests on both branches**

```bash
git checkout feature/urgent
bun test
bun run lint

git checkout feature/non-urgent
bun test
bun run lint
```

Expected: All tests pass on both branches.

---

### Task 5: Validate Both Branches Against Main

**Files:**
- No files modified

- [ ] **Step 1: Verify the urgent branch diff is clean and minimal**

```bash
git diff main..feature/urgent
```

Read through the entire diff. Confirm every change is related to the urgent feature and nothing else.

- [ ] **Step 2: Verify the non-urgent branch diff is clean and minimal**

```bash
git diff main..feature/non-urgent
```

Read through the entire diff. Confirm every change is related to the non-urgent feature and nothing else.

- [ ] **Step 3: Verify the union of both branches covers all original changes**

```bash
git diff main..feature/mixed --stat > /tmp/original-changes.txt
git diff main..feature/urgent --stat > /tmp/urgent-changes.txt
git diff main..feature/non-urgent --stat > /tmp/non-urgent-changes.txt
```

Every file in `original-changes.txt` should appear in either `urgent-changes.txt` or `non-urgent-changes.txt` (or both, if a file was legitimately changed by both features). If a file is missing from both, a commit was dropped.

- [ ] **Step 4: Verify no cross-contamination**

Spot-check 2-3 files from each branch. Open them and confirm the changes make sense in isolation for that feature.

---

### Task 6: Push and Create the Urgent PR

**Files:**
- No source files modified

- [ ] **Step 1: Push the urgent branch**

```bash
git push -u origin feature/urgent
```

Expected: Branch pushed successfully.

- [ ] **Step 2: Create the urgent PR against main**

```bash
gh pr create --base main --head feature/urgent --title "feat: <urgent feature short description>" --body "$(cat <<'EOF'
## Summary
- <1-2 bullet points describing the urgent feature>
- Split from mixed feature branch for independent review

## Test plan
- [ ] All existing tests pass (`bun test`)
- [ ] Lint and type checks pass (`bun run lint`)
- [ ] Manual testing of the urgent feature works as expected

## Notes
- This PR contains only the urgent feature, split from the original branch
- The non-urgent feature will follow in a separate PR
EOF
)"
```

Expected: PR created successfully. Record the PR URL.

- [ ] **Step 3: Verify the PR diff on GitHub**

Open the PR URL in a browser or run:

```bash
gh pr diff <pr-number>
```

Confirm the diff matches what you reviewed locally in Task 5, Step 1.

---

### Task 7: Push and Create the Non-Urgent PR

**Files:**
- No source files modified

- [ ] **Step 1: Push the non-urgent branch**

```bash
git push -u origin feature/non-urgent
```

Expected: Branch pushed successfully.

- [ ] **Step 2: Create the non-urgent PR against main**

```bash
gh pr create --base main --head feature/non-urgent --title "feat: <non-urgent feature short description>" --body "$(cat <<'EOF'
## Summary
- <1-2 bullet points describing the non-urgent feature>
- Split from mixed feature branch for independent review

## Test plan
- [ ] All existing tests pass (`bun test`)
- [ ] Lint and type checks pass (`bun run lint`)
- [ ] Manual testing of the non-urgent feature works as expected

## Notes
- This PR contains only the non-urgent feature, split from the original branch
- The urgent feature was merged separately via PR #<urgent-pr-number>
- If the urgent PR merges first, rebase this branch onto main before merge:
  `git fetch origin && git rebase origin/main`
EOF
)"
```

Expected: PR created successfully. Record the PR URL.

- [ ] **Step 3: Verify the PR diff on GitHub**

```bash
gh pr diff <pr-number>
```

Confirm the diff matches what you reviewed locally in Task 5, Step 2.

---

### Task 8: Rebase Non-Urgent Branch After Urgent Merges (post-merge step)

**Files:**
- No source files modified

This task is performed after the urgent PR has been merged into main.

- [ ] **Step 1: Fetch the latest main**

```bash
git fetch origin
git checkout feature/non-urgent
```

- [ ] **Step 2: Rebase onto updated main**

```bash
git rebase origin/main
```

If conflicts arise, resolve them file by file:

```bash
# For each conflicted file:
# 1. Edit the file to resolve conflicts
# 2. git add <file>
# 3. git rebase --continue
```

- [ ] **Step 3: Run tests after rebase**

```bash
bun test
bun run lint
```

Expected: All tests pass.

- [ ] **Step 4: Force-push the rebased branch**

```bash
git push --force-with-lease origin feature/non-urgent
```

Expected: Branch updated on remote. The PR will automatically reflect the rebased changes.

---

## Troubleshooting Reference

**Cherry-pick conflict patterns in this codebase:**
- Widget files (`src/widgets/*.ts`): Usually self-contained. Conflicts are rare unless both features add widgets.
- Widget registry (`src/widgets/index.ts`): If both features register new widgets, the registry will conflict. Resolve by keeping only the widgets for the current branch's feature.
- Type files (`src/types/*.ts`): If both features add new types, keep only the types needed for the current branch's feature.
- Config/settings (`src/utils/config.ts`): If both features change default settings, take only the defaults for the current branch's feature.
- Test files: Cherry-pick only tests relevant to the current branch's feature.

**If a cherry-pick fails with "empty commit":**
This means the commit's changes are already present (e.g., from a prior cherry-pick that included the same changes). Skip it safely:

```bash
git cherry-pick --skip
```

**If you realize a commit was miscategorized after cherry-picking:**
Revert it on the wrong branch and apply it to the correct one:

```bash
git revert <hash-on-wrong-branch>
git checkout <correct-branch>
git cherry-pick <original-hash>
```
