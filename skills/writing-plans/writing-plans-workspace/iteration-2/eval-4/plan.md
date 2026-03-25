# Race Condition Fix: Concurrent Settings Save Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate the race condition where concurrent saves to settings files cause one write to silently overwrite the other, losing data.

**Architecture:** The root cause is a read-modify-write pattern in two settings files (`settings.json` for ccstatusline config and Claude's `settings.json` for hooks/statusLine) with no concurrency control. The `saveSettings` function in `config.ts` writes the ccstatusline config and then calls `syncWidgetHooks`, which itself performs a separate read-modify-write cycle on Claude's settings file. When two save operations overlap (e.g., Ctrl+S while a previous save is still flushing, or the TUI "Save & Exit" firing alongside the Ctrl+S handler), the second read can load stale data before the first write completes, causing the first write's changes to be silently discarded. The fix introduces atomic file writes (write-to-temp-then-rename) and a per-file async mutex to serialize concurrent save operations.

**Tech Stack:** Node.js fs.promises, os.tmpdir/path utilities for atomic writes, a lightweight async mutex (no new dependencies needed -- a simple promise-chain lock suffices)

---

## Phase 1: Investigate and Confirm the Race Condition

### Task 1.1: Write a test that demonstrates the concurrent save race condition

- **Goal:** Prove the bug exists before fixing it, so we have a regression test that validates the fix.
- **Files:** Create a new test file at `src/utils/__tests__/config-race.test.ts`
- **Constraints:** The test must use the real `saveSettings`/`loadSettings` functions pointed at a temp directory (use `initConfigPath` to redirect). Do not mock the filesystem -- the race is in real async I/O ordering.
- **Acceptance criteria:** A test that fires two concurrent `saveSettings` calls with different data and asserts both changes are reflected in the final file. This test should fail on the current codebase (demonstrating the race). Mark it with a comment explaining it is expected to fail until the fix lands.
- **Risks:** Timing-dependent tests can be flaky. Use `Promise.all` with two distinct setting mutations rather than relying on precise timing.

### Task 1.2: Run the test and confirm it fails

- **Goal:** Validate that the test from 1.1 demonstrates the race condition.
- **Files:** None modified
- **Acceptance criteria:** The test fails, confirming the race exists.

## Phase 2: Introduce Atomic File Writes

### Task 2.1: Create an atomic write utility

- **Goal:** Replace bare `writeFile` calls with a write-to-temp-then-rename pattern, because `rename` is atomic on the same filesystem, preventing partial/corrupt writes.
- **Files:** Create `src/utils/atomic-write.ts`
- **Constraints:** Write to a temp file in the same directory as the target (not `/tmp`), because `rename` only works atomically within the same filesystem/mount. Use a unique suffix (e.g., `.tmp.<pid>.<timestamp>`) to avoid collisions. Clean up the temp file in a `finally` block if rename fails. The function signature should match `fs.promises.writeFile` closely so call sites need minimal changes.
- **Acceptance criteria:** A standalone utility function that writes content atomically. Unit tests in `src/utils/__tests__/atomic-write.test.ts` verify: (a) the file appears with correct content, (b) an incomplete write does not corrupt the target, (c) temp files are cleaned up on error.
- **Risks:** On Windows, `rename` over an existing file may fail depending on Node.js version. Since the project targets Node.js 14+ and modern Bun, verify behavior. A fallback of `unlink + rename` may be needed for Windows, but this codebase's primary targets are macOS/Linux (Powerline font install, `which` command usage confirm this).

### Task 2.2: Run the atomic write tests

- **Goal:** Confirm the atomic write utility works correctly.
- **Files:** None modified
- **Acceptance criteria:** All tests pass.

### Task 2.3: Wire atomic writes into config.ts

- **Goal:** Replace the direct `writeFile` call in `writeSettingsJson` with the atomic write utility, so that ccstatusline's own settings file is written atomically.
- **Files:** Modify `src/utils/config.ts`
- **Constraints:** Only change the `writeSettingsJson` function. The `mkdir` call for the config directory must remain. Do not change the function signature or any callers.
- **Acceptance criteria:** `saveSettings` and `loadSettings` continue to pass all existing tests. The `writeSettingsJson` function now uses the atomic write utility.

### Task 2.4: Wire atomic writes into claude-settings.ts

- **Goal:** Replace the direct `writeFile` call in `saveClaudeSettings` with the atomic write utility, so that Claude's settings file is also written atomically.
- **Files:** Modify `src/utils/claude-settings.ts`
- **Constraints:** The backup logic (`backupClaudeSettings`) should remain unchanged -- it is a safety copy, not the primary write path. Only change the final `writeFile` in `saveClaudeSettings`.
- **Acceptance criteria:** `installStatusLine`, `uninstallStatusLine`, and `syncWidgetHooks` continue to work correctly. Existing tests pass.

### Task 2.5: Run all existing tests

- **Goal:** Confirm atomic writes do not break anything.
- **Files:** None
- **Acceptance criteria:** Full test suite passes.

## Phase 3: Add Async Mutex for Save Serialization

### Task 3.1: Create an async mutex utility

- **Goal:** Prevent two concurrent save operations from interleaving their read-modify-write cycles, because atomic writes alone do not prevent the "stale read" half of the race (process A reads, process B reads, A writes, B writes stale data over A's).
- **Files:** Create `src/utils/async-mutex.ts`
- **Constraints:** Implement a simple promise-chain mutex (no external dependencies). The API should be a function like `withLock(key: string, fn: () => Promise<T>): Promise<T>` that serializes calls sharing the same key string. Important: the lock must be per-key so that locking ccstatusline's settings file does not block writes to Claude's settings file. Keep it simple -- this is single-process concurrency, not cross-process.
- **Acceptance criteria:** Unit tests in `src/utils/__tests__/async-mutex.test.ts` verify: (a) two concurrent calls to the same key run sequentially, (b) calls to different keys run concurrently, (c) if the locked function throws, the lock is released for the next caller.
- **Risks:** This only protects against in-process concurrency (two React event handlers firing save). Cross-process races (two separate ccstatusline processes) remain possible but are outside the scope of this bug report -- the TUI is single-instance.

### Task 3.2: Run the mutex tests

- **Goal:** Confirm the mutex works correctly.
- **Files:** None
- **Acceptance criteria:** All tests pass.

### Task 3.3: Wrap saveSettings with the mutex

- **Goal:** Serialize all calls to `saveSettings` in `config.ts` so that overlapping Ctrl+S and "Save & Exit" actions do not race.
- **Files:** Modify `src/utils/config.ts`
- **Constraints:** Wrap the body of `saveSettings` (including the `syncWidgetHooks` call) inside `withLock('ccstatusline-settings', ...)`. Do not change the function's external signature or return type. Note that `loadSettings` does not need locking because it only runs once at startup.
- **Acceptance criteria:** Two rapid calls to `saveSettings` with different data both persist correctly. The race condition test from Task 1.1 now passes.

### Task 3.4: Wrap saveClaudeSettings with the mutex

- **Goal:** Serialize writes to Claude's settings file, because `syncWidgetHooks`, `installStatusLine`, and `uninstallStatusLine` all independently load-modify-save this file.
- **Files:** Modify `src/utils/claude-settings.ts`
- **Constraints:** Use a different lock key (e.g., `'claude-settings'`) so that saves to ccstatusline's own config and Claude's config can proceed independently. Wrap `saveClaudeSettings` only -- the callers (`syncWidgetHooks`, `installStatusLine`, `uninstallStatusLine`) each call `loadClaudeSettings` then `saveClaudeSettings`, and the load must also be inside the lock to prevent stale reads. This means the lock should be applied at the caller level (`syncWidgetHooks`, `installStatusLine`, `uninstallStatusLine`) rather than inside `saveClaudeSettings` alone. Carefully consider which functions need the lock boundary to include their read step.
- **Acceptance criteria:** Concurrent calls to `syncWidgetHooks` do not lose each other's changes. Existing tests pass.

### Task 3.5: Run the race condition test from Task 1.1

- **Goal:** Confirm the race condition is fixed.
- **Files:** None
- **Acceptance criteria:** The previously-failing test now passes. Remove any "expected to fail" annotations.

## Phase 4: Final Validation

### Task 4.1: Run the full test suite

- **Goal:** Confirm nothing is broken by the changes.
- **Files:** None
- **Acceptance criteria:** All tests pass, including the new race condition, atomic write, and mutex tests.

### Task 4.2: Run lint and type checks

- **Goal:** Ensure all new code passes the project's quality checks.
- **Files:** None
- **Acceptance criteria:** `bun run lint` passes with no errors.

### Task 4.3: Commit the fix

- **Goal:** Commit all changes as a single coherent unit.
- **Files:** All new and modified files from this plan
- **Acceptance criteria:** Clean commit with a message describing the race condition fix.
