# Rename getUserData to fetchUserProfile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the exported function `getUserData` to `fetchUserProfile` everywhere it is defined, exported, imported, and called across the codebase.

**Architecture:** Find the definition site, update the function name and its export, then update every import and call site. Verify with the compiler and test suite that nothing is broken.

**Tech Stack:** TypeScript

---

## File Structure

- **Definition file:** The source file where `getUserData` is defined and exported. This is the primary change site.
- **Import sites:** Every file that imports `getUserData`, whether via named import, re-export, or dynamic import.
- **Call sites:** Every file that calls `getUserData`, including any that reference it by string name (e.g., in configuration objects or mapped lookups).
- **Test files:** Any tests that reference `getUserData` directly in assertions, mocks, or setup.

## Tasks

### Task 1: Locate all references to getUserData

- [ ] Search the entire codebase for every occurrence of `getUserData` in all file types (TypeScript, config files, documentation, tests) so that nothing is missed.
- [ ] Record the full list of files and line numbers that reference the function.

**Goal:** Build a complete inventory of every place the name appears, because missing even one reference will cause a build or runtime failure.

**Files:** All files in the repository.

**Constraints:** Search must cover string literals, comments, and documentation in addition to code references. Re-exports or barrel files are easy to overlook.

**Acceptance criteria:** A complete list of every file containing `getUserData` is identified. No occurrences are missed.

**Risks:** The function name could appear in generated files, lockfiles, or build artifacts that should not be manually edited. Exclude those from the change set.

### Task 2: Rename the definition and update all references

- [ ] Rename the function at its definition site from `getUserData` to `fetchUserProfile`.
- [ ] Update the export statement to use the new name.
- [ ] Update every import statement across the codebase to use `fetchUserProfile`.
- [ ] Update every call site to use the new name.
- [ ] Update any string-literal references (e.g., in test descriptions, logging, or documentation comments) to reflect the new name.

**Goal:** Perform the actual rename so that every reference in the codebase is consistent, because a partial rename will cause compile errors or broken runtime behavior.

**Files:** The definition file and every file identified in Task 1.

**Constraints:** If any file re-exports the function under an alias, the alias may or may not need updating depending on the project's public API contract. Preserve existing aliases unless they directly expose the old name. Note that barrel/index files often re-export symbols and are easy to miss.

**Acceptance criteria:** No remaining occurrences of `getUserData` exist anywhere in the source code or test files (confirmed via codebase-wide search).

**Risks:** If `getUserData` is part of a public API consumed by external packages or plugins, renaming it is a breaking change. Verify whether a deprecation alias is needed.

### Task 3: Verify the rename with the compiler and tests

- [ ] Run the TypeScript compiler to confirm there are no type errors.
- [ ] Run the full test suite to confirm all tests pass.
- [ ] Run the linter to confirm no lint violations were introduced.

**Goal:** Prove the rename is complete and correct, because a green build is the only reliable signal that no references were missed.

**Files:** No file changes expected in this task.

**Acceptance criteria:** TypeScript compilation succeeds with zero errors, all tests pass, and the linter reports no new violations.

**Risks:** If tests were mocking `getUserData` by string name (e.g., in spy setup), the compiler won't catch the mismatch but tests will fail at runtime. If this happens, go back and fix the mock references.

### Task 4: Commit the rename

- [ ] Stage all changed files and commit with a message describing the rename and the reason for it.

**Goal:** Capture the rename as a single atomic commit so that it can be cleanly reverted or reviewed.

**Files:** All files modified in Task 2.

**Acceptance criteria:** A single commit contains all rename changes and nothing else. The commit message clearly states the old and new function names.

**Risks:** None expected at this stage.
