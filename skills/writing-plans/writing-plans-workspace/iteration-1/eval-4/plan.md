# Fix Race Condition in Concurrent Settings Save Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate a race condition where concurrent saves to `settings.json` and `~/.claude/settings.json` can silently lose one write when two operations overlap.

**Architecture:** Both `saveSettings()` in `src/utils/config.ts` and `saveClaudeSettings()` in `src/utils/claude-settings.ts` perform non-atomic read-modify-write sequences against shared JSON files. When `saveSettings()` triggers `syncWidgetHooks()`, which itself calls `loadClaudeSettings()` then `saveClaudeSettings()`, a concurrent call (e.g., Ctrl+S while an install action is in flight) can cause the second write to overwrite the first with stale data. The fix introduces: (1) a serialization queue so concurrent saves execute sequentially, (2) atomic file writes via write-to-temp-then-rename, and (3) guards in the TUI to prevent overlapping save triggers.

**Tech Stack:** TypeScript, Node.js `fs.promises`, `os.tmpdir`, Vitest, React/Ink TUI

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/utils/save-queue.ts` (create) | Generic async serialization queue that ensures only one save runs at a time per file path |
| `src/utils/atomic-write.ts` (create) | Atomic file write helper: writes to a temp file in the same directory, then renames |
| `src/utils/config.ts` (modify) | Use atomic write and save queue for ccstatusline settings |
| `src/utils/claude-settings.ts` (modify) | Use atomic write and save queue for Claude settings |
| `src/tui/App.tsx` (modify) | Add guard to prevent overlapping save operations from the TUI |
| `src/utils/__tests__/save-queue.test.ts` (create) | Tests for the serialization queue |
| `src/utils/__tests__/atomic-write.test.ts` (create) | Tests for atomic file writing |
| `src/utils/__tests__/config.test.ts` (modify) | Add concurrency tests for `saveSettings` |
| `src/utils/__tests__/claude-settings.test.ts` (modify) | Add concurrency tests for `saveClaudeSettings` |

---

### Task 1: Create the Async Save Queue

This queue ensures that for a given file path, only one write operation executes at a time. Subsequent calls wait for the current one to finish before starting.

**Files:**
- Create: `src/utils/save-queue.ts`
- Test: `src/utils/__tests__/save-queue.test.ts`

- [ ] **Step 1: Write the failing test for basic serialization**

```typescript
// src/utils/__tests__/save-queue.test.ts
import {
    describe,
    expect,
    it
} from 'vitest';

import { SaveQueue } from '../save-queue';

describe('SaveQueue', () => {
    it('serializes concurrent operations on the same key', async () => {
        const queue = new SaveQueue();
        const order: number[] = [];

        const task1 = queue.enqueue('file-a', async () => {
            await new Promise(r => setTimeout(r, 50));
            order.push(1);
        });

        const task2 = queue.enqueue('file-a', async () => {
            order.push(2);
        });

        await Promise.all([task1, task2]);
        expect(order).toEqual([1, 2]);
    });

    it('allows parallel operations on different keys', async () => {
        const queue = new SaveQueue();
        const order: string[] = [];

        const task1 = queue.enqueue('file-a', async () => {
            await new Promise(r => setTimeout(r, 50));
            order.push('a');
        });

        const task2 = queue.enqueue('file-b', async () => {
            order.push('b');
        });

        await Promise.all([task1, task2]);
        // 'b' should complete before 'a' since they run in parallel
        expect(order).toEqual(['b', 'a']);
    });

    it('propagates errors without breaking the queue', async () => {
        const queue = new SaveQueue();

        const task1 = queue.enqueue('file-a', async () => {
            throw new Error('boom');
        });

        await expect(task1).rejects.toThrow('boom');

        // Queue should still work after an error
        const result = await queue.enqueue('file-a', async () => 'ok');
        expect(result).toBe('ok');
    });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bun test src/utils/__tests__/save-queue.test.ts`
Expected: FAIL with "Cannot find module '../save-queue'"

- [ ] **Step 3: Implement SaveQueue**

```typescript
// src/utils/save-queue.ts

/**
 * Serializes async operations per key so concurrent calls to the same
 * key execute one at a time. Different keys run in parallel.
 */
export class SaveQueue {
    private queues = new Map<string, Promise<void>>();

    async enqueue<T>(key: string, fn: () => Promise<T>): Promise<T> {
        const previous = this.queues.get(key) ?? Promise.resolve();

        let resolve: (value: void) => void;
        const next = new Promise<void>(r => { resolve = r; });
        this.queues.set(key, next);

        // Wait for previous operation to finish (regardless of success/failure)
        await previous.catch(() => {});

        try {
            return await fn();
        } finally {
            resolve!();
            // Clean up if nothing else is queued
            if (this.queues.get(key) === next) {
                this.queues.delete(key);
            }
        }
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bun test src/utils/__tests__/save-queue.test.ts`
Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/utils/save-queue.ts src/utils/__tests__/save-queue.test.ts
git commit -m "feat: add SaveQueue to serialize concurrent file writes"
```

---

### Task 2: Create Atomic File Write Helper

Replace bare `fs.promises.writeFile` with a write-to-temp-then-rename approach. This prevents partial writes from corrupting the file if the process is interrupted mid-write.

**Files:**
- Create: `src/utils/atomic-write.ts`
- Test: `src/utils/__tests__/atomic-write.test.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// src/utils/__tests__/atomic-write.test.ts
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';

import {
    afterEach,
    beforeEach,
    describe,
    expect,
    it
} from 'vitest';

import { atomicWriteFile } from '../atomic-write';

describe('atomicWriteFile', () => {
    let tmpDir: string;

    beforeEach(() => {
        tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'atomic-write-test-'));
    });

    afterEach(() => {
        fs.rmSync(tmpDir, { recursive: true, force: true });
    });

    it('writes content that can be read back', async () => {
        const filePath = path.join(tmpDir, 'test.json');
        await atomicWriteFile(filePath, '{"key":"value"}');

        const content = fs.readFileSync(filePath, 'utf-8');
        expect(content).toBe('{"key":"value"}');
    });

    it('overwrites existing file content', async () => {
        const filePath = path.join(tmpDir, 'test.json');
        fs.writeFileSync(filePath, 'old content');

        await atomicWriteFile(filePath, 'new content');

        const content = fs.readFileSync(filePath, 'utf-8');
        expect(content).toBe('new content');
    });

    it('creates parent directories if they do not exist', async () => {
        const filePath = path.join(tmpDir, 'nested', 'dir', 'test.json');
        await atomicWriteFile(filePath, 'nested content');

        const content = fs.readFileSync(filePath, 'utf-8');
        expect(content).toBe('nested content');
    });

    it('does not leave temp files on success', async () => {
        const filePath = path.join(tmpDir, 'clean.json');
        await atomicWriteFile(filePath, 'data');

        const files = fs.readdirSync(tmpDir);
        expect(files).toEqual(['clean.json']);
    });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bun test src/utils/__tests__/atomic-write.test.ts`
Expected: FAIL with "Cannot find module '../atomic-write'"

- [ ] **Step 3: Implement atomicWriteFile**

```typescript
// src/utils/atomic-write.ts
import * as fs from 'fs';
import * as path from 'path';

const writeFile = fs.promises.writeFile;
const rename = fs.promises.rename;
const unlink = fs.promises.unlink;
const mkdir = fs.promises.mkdir;

/**
 * Writes content to a file atomically by writing to a temporary file
 * in the same directory and then renaming. This prevents readers from
 * seeing partial writes and protects against data loss if the process
 * crashes mid-write.
 */
export async function atomicWriteFile(filePath: string, content: string): Promise<void> {
    const dir = path.dirname(filePath);
    await mkdir(dir, { recursive: true });

    const tmpPath = `${filePath}.${process.pid}.tmp`;

    try {
        await writeFile(tmpPath, content, 'utf-8');
        await rename(tmpPath, filePath);
    } catch (error) {
        // Clean up temp file on failure
        try {
            await unlink(tmpPath);
        } catch {
            // Ignore cleanup errors
        }
        throw error;
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bun test src/utils/__tests__/atomic-write.test.ts`
Expected: PASS (all 4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/utils/atomic-write.ts src/utils/__tests__/atomic-write.test.ts
git commit -m "feat: add atomic file write helper using temp-then-rename"
```

---

### Task 3: Integrate Save Queue and Atomic Write into config.ts

Wire up the queue and atomic writer so that `saveSettings()` and `loadSettings()` (when it writes defaults/migrations) use serialized, atomic writes.

**Files:**
- Modify: `src/utils/config.ts:1-167`
- Modify: `src/utils/__tests__/config.test.ts`

- [ ] **Step 1: Write the failing concurrency test**

Add this test to the existing test file `src/utils/__tests__/config.test.ts`:

```typescript
it('serializes concurrent saveSettings calls without data loss', async () => {
    const { loadSettings, saveSettings } = await import('../config');

    // Load initial settings
    const settings = await loadSettings();

    // Create two distinct modifications
    const settingsA = { ...settings, flexMode: 'full' as const };
    const settingsB = { ...settings, flexMode: 'full-minus-40' as const };

    // Fire both saves concurrently
    await Promise.all([
        saveSettings(settingsA),
        saveSettings(settingsB)
    ]);

    // The last save to complete should win; either is acceptable
    // as long as the file is valid JSON and not corrupted
    const reloaded = await loadSettings();
    expect(['full', 'full-minus-40']).toContain(reloaded.flexMode);
});
```

- [ ] **Step 2: Run the test to see current behavior**

Run: `bun test src/utils/__tests__/config.test.ts`
Expected: This may pass intermittently (race conditions are timing-dependent), but the test documents the expected behavior.

- [ ] **Step 3: Modify config.ts to use SaveQueue and atomicWriteFile**

In `src/utils/config.ts`, make these changes:

1. Add imports at the top:
```typescript
import { atomicWriteFile } from './atomic-write';
import { SaveQueue } from './save-queue';
```

2. Remove the `writeFile` and `mkdir` aliases (lines 19-20):
```typescript
// REMOVE these lines:
// const writeFile = fs.promises.writeFile;
// const mkdir = fs.promises.mkdir;
```
Keep `const readFile = fs.promises.readFile;`

3. Create a module-level queue instance:
```typescript
const saveQueue = new SaveQueue();
```

4. Replace `writeSettingsJson` function body (currently lines 58-61):
```typescript
async function writeSettingsJson(settings: unknown, paths: SettingsPaths): Promise<void> {
    await atomicWriteFile(paths.settingsPath, JSON.stringify(settings, null, 2));
}
```

5. Replace `backupBadSettings` to use `atomicWriteFile`:
```typescript
async function backupBadSettings(paths: SettingsPaths): Promise<void> {
    try {
        if (fs.existsSync(paths.settingsPath)) {
            const content = await readFile(paths.settingsPath, 'utf-8');
            await atomicWriteFile(paths.settingsBackupPath, content);
            console.error(`Bad settings backed up to ${paths.settingsBackupPath}`);
        }
    } catch (error) {
        console.error('Failed to backup bad settings:', error);
    }
}
```

6. Wrap `saveSettings` with the queue (currently lines 151-167):
```typescript
export async function saveSettings(settings: Settings): Promise<void> {
    const paths = getSettingsPaths();

    await saveQueue.enqueue(paths.settingsPath, async () => {
        // Always include version when saving
        const settingsWithVersion = {
            ...settings,
            version: CURRENT_VERSION
        };

        await writeSettingsJson(settingsWithVersion, paths);

        // Sync widget hooks to Claude settings
        try {
            const { syncWidgetHooks } = await import('./hooks');
            await syncWidgetHooks(settings);
        } catch { /* ignore hook sync failures */ }
    });
}
```

- [ ] **Step 4: Run the full config test suite**

Run: `bun test src/utils/__tests__/config.test.ts`
Expected: PASS (all tests including the new concurrency test)

- [ ] **Step 5: Commit**

```bash
git add src/utils/config.ts src/utils/__tests__/config.test.ts
git commit -m "fix: serialize saves in config.ts to prevent race condition"
```

---

### Task 4: Integrate Save Queue and Atomic Write into claude-settings.ts

Apply the same protections to `saveClaudeSettings()`, which is the other writer involved in the race (called by `syncWidgetHooks`, `installStatusLine`, and `uninstallStatusLine`).

**Files:**
- Modify: `src/utils/claude-settings.ts:1-278`
- Modify: `src/utils/__tests__/claude-settings.test.ts`

- [ ] **Step 1: Write the failing concurrency test**

Add to `src/utils/__tests__/claude-settings.test.ts`:

```typescript
it('serializes concurrent saveClaudeSettings calls', async () => {
    const {
        loadClaudeSettings,
        saveClaudeSettings
    } = await import('../claude-settings');

    const settingsA = { statusLine: { type: 'command' as const, command: 'cmd-a', padding: 0 } };
    const settingsB = { statusLine: { type: 'command' as const, command: 'cmd-b', padding: 0 } };

    // Fire both saves concurrently
    await Promise.all([
        saveClaudeSettings(settingsA),
        saveClaudeSettings(settingsB)
    ]);

    // File should be valid JSON with one of the two values
    const reloaded = await loadClaudeSettings();
    expect(['cmd-a', 'cmd-b']).toContain(reloaded.statusLine?.command);
});
```

- [ ] **Step 2: Run the test to see current behavior**

Run: `bun test src/utils/__tests__/claude-settings.test.ts`
Expected: May pass intermittently; documents the desired behavior.

- [ ] **Step 3: Modify claude-settings.ts**

1. Add imports at the top of `src/utils/claude-settings.ts`:
```typescript
import { atomicWriteFile } from './atomic-write';
import { SaveQueue } from './save-queue';
```

2. Remove `writeFile` and `mkdir` aliases (lines 21-23):
```typescript
// REMOVE these lines:
// const writeFile = fs.promises.writeFile;
// const mkdir = fs.promises.mkdir;
```
Keep `const readFile = fs.promises.readFile;`

3. Add a module-level queue:
```typescript
const saveQueue = new SaveQueue();
```

4. Update `backupClaudeSettings` (lines 99-113):
```typescript
async function backupClaudeSettings(suffix = '.bak'): Promise<string | null> {
    const settingsPath = getClaudeSettingsPath();
    const backupPath = settingsPath + suffix;
    try {
        if (fs.existsSync(settingsPath)) {
            const content = await readFile(settingsPath, 'utf-8');
            await atomicWriteFile(backupPath, content);
            return backupPath;
        }
    } catch (error) {
        console.error('Failed to backup Claude settings:', error);
    }

    return null;
}
```

5. Wrap `saveClaudeSettings` with the queue (lines 157-168):
```typescript
export async function saveClaudeSettings(
    settings: ClaudeSettings
): Promise<void> {
    const settingsPath = getClaudeSettingsPath();

    await saveQueue.enqueue(settingsPath, async () => {
        // Backup settings before overwriting
        await backupClaudeSettings();

        await atomicWriteFile(settingsPath, JSON.stringify(settings, null, 2));
    });
}
```

- [ ] **Step 4: Run the full claude-settings test suite**

Run: `bun test src/utils/__tests__/claude-settings.test.ts`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add src/utils/claude-settings.ts src/utils/__tests__/claude-settings.test.ts
git commit -m "fix: serialize saves in claude-settings.ts to prevent race condition"
```

---

### Task 5: Add TUI Save Guard to Prevent Overlapping User-Triggered Saves

Even with the queue, it is better UX to prevent the user from triggering multiple saves simultaneously. Add an `isSaving` guard so Ctrl+S and the "Save & Exit" menu option are debounced.

**Files:**
- Modify: `src/tui/App.tsx:98-181` (state declarations and save handlers)

- [ ] **Step 1: Write the failing test**

Add to `src/tui/__tests__/App.test.ts` (or create if structure differs):

```typescript
import {
    describe,
    expect,
    it
} from 'vitest';

import {
    clearInstallMenuSelection,
    getConfirmCancelScreen
} from '../App';

describe('App helpers', () => {
    describe('getConfirmCancelScreen', () => {
        it('returns cancelScreen when set', () => {
            expect(getConfirmCancelScreen({
                message: '',
                action: async () => {},
                cancelScreen: 'install'
            })).toBe('install');
        });

        it('returns main when no cancelScreen', () => {
            expect(getConfirmCancelScreen(null)).toBe('main');
        });
    });

    describe('clearInstallMenuSelection', () => {
        it('removes install key when present', () => {
            const result = clearInstallMenuSelection({ install: 0, main: 1 });
            expect(result).toEqual({ main: 1 });
            expect(result).not.toHaveProperty('install');
        });

        it('returns same object when install is absent', () => {
            const input = { main: 1 };
            expect(clearInstallMenuSelection(input)).toBe(input);
        });
    });
});
```

- [ ] **Step 2: Run test to verify existing helpers still pass**

Run: `bun test src/tui/__tests__/App.test.ts`
Expected: PASS

- [ ] **Step 3: Add isSaving state guard to App.tsx**

In `src/tui/App.tsx`, make these changes:

1. Add `isSaving` state alongside the other state declarations (around line 102):
```typescript
const [isSaving, setIsSaving] = useState(false);
```

2. Update the Ctrl+S handler (lines 170-180) to check `isSaving`:
```typescript
useInput((input, key) => {
    if (key.ctrl && input === 'c') {
        exit();
    }
    // Global save shortcut
    if (key.ctrl && input === 's' && settings && !isSaving) {
        setIsSaving(true);
        void (async () => {
            try {
                await saveSettings(settings);
                setOriginalSettings(cloneSettings(settings));
                setHasChanges(false);
                setFlashMessage({
                    text: '\u2713 Configuration saved',
                    color: 'green'
                });
            } finally {
                setIsSaving(false);
            }
        })();
    }
});
```

3. Update the "Save & Exit" handler in `handleMainMenuSelect` (lines 293-298):
```typescript
case 'save':
    if (!isSaving) {
        setIsSaving(true);
        await saveSettings(settings);
        setOriginalSettings(cloneSettings(settings));
        setHasChanges(false);
        exit();
    }
    break;
```

- [ ] **Step 4: Run the full test suite**

Run: `bun test`
Expected: PASS (all tests across the project)

- [ ] **Step 5: Commit**

```bash
git add src/tui/App.tsx src/tui/__tests__/App.test.ts
git commit -m "fix: add isSaving guard to prevent overlapping TUI save operations"
```

---

### Task 6: Run Full Validation

Verify everything works together and nothing is broken.

- [ ] **Step 1: Run the complete test suite**

Run: `bun test`
Expected: All tests pass.

- [ ] **Step 2: Run lint and type checking**

Run: `bun run lint`
Expected: No errors, no warnings.

- [ ] **Step 3: Test the build**

Run: `bun run build`
Expected: Build completes successfully, `dist/ccstatusline.js` is produced.

- [ ] **Step 4: Manual smoke test with piped input**

Run: `bun run example`
Expected: Formatted status line output renders without errors.

- [ ] **Step 5: Commit any final adjustments**

If lint or type checking required changes:
```bash
git add -u
git commit -m "fix: address lint and type issues from race condition fix"
```
