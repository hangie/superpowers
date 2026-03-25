# Rename `getUserData` to `fetchUserProfile` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the exported function `getUserData` to `fetchUserProfile` across the entire codebase so all definitions, call sites, re-exports, tests, and documentation reference the new name.

**Architecture:** This is a mechanical rename refactor. We locate the definition, update it, then update every import and call site. We rely on TypeScript's compiler (`tsc --noEmit`) and the existing test suite (`vitest`) as our safety net to catch any missed references.

**Tech Stack:** TypeScript, Vitest, Bun, ESLint

---

## File Structure

This is a rename-only change. No new files are created. The files affected are:

1. **Definition file** -- the source file where `getUserData` is defined and exported.
2. **Re-export barrel files** -- any `index.ts` that re-exports `getUserData`.
3. **Consumer files** -- every file that imports or calls `getUserData`.
4. **Test files** -- every test that imports, calls, or asserts on `getUserData`.
5. **Documentation / comments** -- any JSDoc, inline comments, or markdown referencing `getUserData`.

Because `getUserData` does not currently exist in this codebase (confirmed via codebase-wide search), the tasks below describe the **systematic process** an engineer must follow. If the function is added before this plan is executed, or if this plan is applied to a different codebase where it does exist, follow these steps exactly.

---

### Task 1: Locate All References

**Files:**
- Search scope: entire repository

- [ ] **Step 1: Search for all occurrences of `getUserData`**

```bash
grep -rn "getUserData" --include="*.ts" --include="*.tsx" --include="*.md" --include="*.json" .
```

Record every file path and line number. Group them into:
- **Definition** (where `export function getUserData` or `export const getUserData` lives)
- **Re-exports** (barrel `index.ts` files with `export { getUserData }`)
- **Imports** (files with `import { getUserData }`)
- **Call sites** (files that call `getUserData(...)`)
- **Tests** (test files referencing `getUserData`)
- **Docs/comments** (markdown, JSDoc, or inline comments)

- [ ] **Step 2: Verify the search is exhaustive**

```bash
grep -rn "getUserData" .
```

This broader search (no file-type filter) catches references in config files, scripts, or other unexpected locations. If new files appear, add them to the list.

- [ ] **Step 3: Commit -- no code changes yet, just record findings**

No commit needed here. Proceed to Task 2.

---

### Task 2: Update the Definition File

**Files:**
- Modify: the file where `getUserData` is defined (e.g., `src/utils/user.ts` -- substitute the real path)

- [ ] **Step 1: Run the full test suite to confirm green baseline**

```bash
bun vitest run
```

Expected: all tests PASS. If any fail, stop and fix them before proceeding.

- [ ] **Step 2: Run the TypeScript compiler to confirm no type errors**

```bash
bun tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Rename the function at its definition**

In the definition file, change:

```typescript
// Before
export function getUserData(/* params */) {
  // ...
}
```

to:

```typescript
// After
export function fetchUserProfile(/* params */) {
  // ...
}
```

If the function is an arrow function or const, apply the same rename:

```typescript
// Before
export const getUserData = (/* params */) => { /* ... */ };

// After
export const fetchUserProfile = (/* params */) => { /* ... */ };
```

- [ ] **Step 4: Run `tsc --noEmit` to see all broken imports**

```bash
bun tsc --noEmit
```

Expected: FAIL with errors like `Module '"./user"' has no exported member 'getUserData'` in every consuming file. This confirms the rename broke dependents as expected and gives you the full list of files to update.

- [ ] **Step 5: Commit the definition-only rename**

```bash
git add <definition-file-path>
git commit -m "refactor: rename getUserData to fetchUserProfile at definition"
```

---

### Task 3: Update All Re-Export Barrel Files

**Files:**
- Modify: every `index.ts` (or similar barrel file) that re-exports the function

- [ ] **Step 1: Update each barrel re-export**

In each barrel file, change:

```typescript
// Before
export { getUserData } from './user.ts';

// After
export { fetchUserProfile } from './user.ts';
```

- [ ] **Step 2: Run `tsc --noEmit` to verify barrel files compile**

```bash
bun tsc --noEmit
```

Expected: still FAIL, but barrel-file-specific errors should be resolved. Remaining errors come from consumer files.

- [ ] **Step 3: Commit barrel file updates**

```bash
git add <barrel-file-paths>
git commit -m "refactor: update barrel re-exports for fetchUserProfile rename"
```

---

### Task 4: Update All Consumer (Non-Test) Files

**Files:**
- Modify: every non-test file that imports or calls `getUserData`

- [ ] **Step 1: Update import statements in each consumer file**

In each file, change:

```typescript
// Before
import { getUserData } from '../utils/user.ts';

// After
import { fetchUserProfile } from '../utils/user.ts';
```

- [ ] **Step 2: Update all call sites in each consumer file**

In each file, change every usage:

```typescript
// Before
const data = getUserData(userId);

// After
const data = fetchUserProfile(userId);
```

- [ ] **Step 3: Update any JSDoc or inline comments referencing `getUserData`**

```typescript
// Before
/** Calls getUserData to fetch the profile */

// After
/** Calls fetchUserProfile to fetch the profile */
```

- [ ] **Step 4: Run `tsc --noEmit` to verify consumer files compile**

```bash
bun tsc --noEmit
```

Expected: remaining errors should only be in test files now (if any).

- [ ] **Step 5: Commit consumer file updates**

```bash
git add <consumer-file-paths>
git commit -m "refactor: update all imports and call sites to fetchUserProfile"
```

---

### Task 5: Update All Test Files

**Files:**
- Modify: every test file that references `getUserData`

- [ ] **Step 1: Update imports in test files**

```typescript
// Before
import { getUserData } from '../../utils/user.ts';

// After
import { fetchUserProfile } from '../../utils/user.ts';
```

- [ ] **Step 2: Update call sites in test files**

```typescript
// Before
const result = getUserData(mockId);

// After
const result = fetchUserProfile(mockId);
```

- [ ] **Step 3: Update test descriptions and assertion messages**

```typescript
// Before
describe('getUserData', () => {
  it('should return user data for a valid ID', () => {

// After
describe('fetchUserProfile', () => {
  it('should return user profile for a valid ID', () => {
```

- [ ] **Step 4: Run the full test suite**

```bash
bun vitest run
```

Expected: all tests PASS.

- [ ] **Step 5: Commit test file updates**

```bash
git add <test-file-paths>
git commit -m "refactor: update tests for fetchUserProfile rename"
```

---

### Task 6: Update Documentation and Run Final Validation

**Files:**
- Modify: any `.md` files, `README.md`, JSDoc comments, or config files referencing `getUserData`

- [ ] **Step 1: Search for any remaining references**

```bash
grep -rn "getUserData" .
```

Expected: zero matches. If any remain, update them now.

- [ ] **Step 2: Update any markdown documentation**

Change all occurrences in `.md` files:

```markdown
<!-- Before -->
Call `getUserData(id)` to retrieve...

<!-- After -->
Call `fetchUserProfile(id)` to retrieve...
```

- [ ] **Step 3: Run TypeScript compiler -- final check**

```bash
bun tsc --noEmit
```

Expected: PASS with zero errors.

- [ ] **Step 4: Run full test suite -- final check**

```bash
bun vitest run
```

Expected: all tests PASS.

- [ ] **Step 5: Run linter -- final check**

```bash
bun run lint
```

Expected: PASS with zero warnings (the project enforces `--max-warnings=0`).

- [ ] **Step 6: Final grep to confirm zero remaining references**

```bash
grep -rn "getUserData" .
```

Expected: zero matches.

- [ ] **Step 7: Commit any documentation updates**

```bash
git add <doc-file-paths>
git commit -m "refactor: update docs for fetchUserProfile rename"
```

- [ ] **Step 8: Verify clean git status**

```bash
git status
```

Expected: working tree clean, nothing unstaged.
