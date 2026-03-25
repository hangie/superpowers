# CSS Modules to Tailwind Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate all 47 React components from CSS modules to Tailwind CSS, including design token mapping and dynamic class logic refactoring.

**Architecture:** Three-phase approach: (1) set up Tailwind config with design token mapping, (2) migrate components in dependency order starting with leaf components, (3) remove CSS module infrastructure. Each component migration is atomic and independently testable. Dynamic class logic is refactored to use `clsx` with Tailwind classes instead of conditional CSS module lookups.

**Tech Stack:** React, Tailwind CSS v3, PostCSS, clsx, tailwind-merge

---

## Scope

This plan covers a single cohesive subsystem: the component library's styling layer. All 47 components share one set of design tokens and one CSS module setup, so they belong in one plan. The work is ordered so each task produces a working, testable build.

## File Structure

### New files
- `tailwind.config.js` — Tailwind configuration with design token mappings
- `postcss.config.js` — PostCSS config for Tailwind (if not already present)
- `src/styles/globals.css` — Tailwind directives (`@tailwind base/components/utilities`)
- `src/utils/cn.ts` — Utility combining `clsx` and `tailwind-merge` for conditional classes

### Modified files (per component, 47 total)
- `src/components/<Name>/<Name>.tsx` — Replace `styles.xxx` references with Tailwind classes
- `src/components/<Name>/<Name>.test.tsx` — Update snapshot tests and class-based assertions
- `src/components/<Name>/<Name>.module.css` — Deleted after migration

### Modified config files
- `package.json` — Add `tailwindcss`, `postcss`, `autoprefixer`, `clsx`, `tailwind-merge` deps
- `tsconfig.json` — No changes expected unless path aliases need updating

### Component categories by migration complexity

**Simple (direct class replacement, ~25 components):** Components where CSS module classes map 1:1 to static Tailwind utility classes. Examples: `Avatar`, `Badge`, `Divider`, `Spinner`, `Label`, `Tooltip`.

**Medium (conditional classes, ~15 components):** Components with props that toggle between CSS module classes (e.g., `variant`, `size`, `disabled`). Examples: `Button`, `Input`, `Select`, `Card`, `Alert`, `Tabs`.

**Complex (dynamic/computed classes, ~7 components):** Components with runtime-computed class names, CSS custom property overrides, animation states, or style objects derived from CSS variables. Examples: `Modal`, `Dropdown`, `DataTable`, `Accordion`, `ColorPicker`, `ThemeProvider`, `Layout`.

---

## Task 1: Install dependencies and configure Tailwind

**Files:**
- Modify: `package.json`
- Create: `tailwind.config.js`
- Create: `postcss.config.js`
- Create: `src/styles/globals.css`

- [ ] **Step 1: Install Tailwind and supporting packages**

```bash
npm install -D tailwindcss postcss autoprefixer
npm install clsx tailwind-merge
npx tailwindcss init -p
```

- [ ] **Step 2: Verify `tailwind.config.js` and `postcss.config.js` were created**

```bash
ls tailwind.config.js postcss.config.js
```

Expected: Both files listed without error.

- [ ] **Step 3: Write the Tailwind global stylesheet**

Create `src/styles/globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 4: Import the global stylesheet in the application entry point**

In the root entry file (e.g., `src/index.tsx` or `src/App.tsx`), add at the top:

```tsx
import './styles/globals.css';
```

- [ ] **Step 5: Verify the app builds without errors**

```bash
npm run build
```

Expected: Build succeeds. No styling changes yet (Tailwind is loaded but unused).

- [ ] **Step 6: Commit**

```bash
git add package.json package-lock.json tailwind.config.js postcss.config.js src/styles/globals.css src/index.tsx
git commit -m "chore: install Tailwind CSS and configure PostCSS pipeline"
```

---

## Task 2: Map design tokens to Tailwind config

**Files:**
- Modify: `tailwind.config.js`
- Reference: The CSS file where your CSS custom properties (design tokens) are defined (e.g., `src/styles/tokens.css` or `:root` block in a global stylesheet)

- [ ] **Step 1: Audit existing design tokens**

Open the file that defines your CSS custom properties. Identify every `--token-name: value;` declaration. Group them by category: colors, spacing, typography, shadows, border-radius, breakpoints, z-index, transitions.

Example of what you are looking for:

```css
:root {
  --color-primary: #3b82f6;
  --color-primary-hover: #2563eb;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --font-size-base: 1rem;
  --radius-md: 0.375rem;
  --shadow-card: 0 1px 3px rgba(0,0,0,0.12);
  --z-modal: 1000;
  --transition-fast: 150ms ease;
}
```

- [ ] **Step 2: Write the token mapping in `tailwind.config.js`**

Map every token into `theme.extend`. Use the same semantic names so the mapping is traceable.

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{ts,tsx,js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#3b82f6',
          hover: '#2563eb',
          // ... map every --color-* token
        },
        // secondary, danger, warning, success, neutral, etc.
      },
      spacing: {
        // Map --spacing-* tokens. Tailwind already has a spacing scale,
        // so only add custom values that don't match Tailwind defaults.
        // e.g., 'sm': '0.5rem' is already Tailwind's `2` (0.5rem).
        // Only add if your token names are used semantically.
      },
      fontSize: {
        // Map --font-size-* tokens
      },
      borderRadius: {
        // Map --radius-* tokens
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.12)',
        // Map --shadow-* tokens
      },
      zIndex: {
        modal: '1000',
        dropdown: '900',
        tooltip: '1100',
        // Map --z-* tokens
      },
      transitionDuration: {
        fast: '150ms',
        // Map --transition-* tokens
      },
    },
  },
  plugins: [],
};
```

- [ ] **Step 3: Write a test to verify token availability**

Create `src/utils/__tests__/tailwind-tokens.test.ts`:

```ts
import resolveConfig from 'tailwindcss/resolveConfig';
import tailwindConfig from '../../../tailwind.config.js';

const fullConfig = resolveConfig(tailwindConfig);

describe('Tailwind design tokens', () => {
  it('maps primary color', () => {
    expect(fullConfig.theme.colors.primary.DEFAULT).toBe('#3b82f6');
  });

  it('maps primary hover color', () => {
    expect(fullConfig.theme.colors.primary.hover).toBe('#2563eb');
  });

  it('maps card shadow', () => {
    expect(fullConfig.theme.boxShadow.card).toBe('0 1px 3px rgba(0,0,0,0.12)');
  });

  it('maps modal z-index', () => {
    expect(fullConfig.theme.zIndex.modal).toBe('1000');
  });

  // Add one assertion per token category to ensure nothing was missed
});
```

- [ ] **Step 4: Run the token tests**

```bash
npx vitest run src/utils/__tests__/tailwind-tokens.test.ts
```

Expected: All assertions pass.

- [ ] **Step 5: Commit**

```bash
git add tailwind.config.js src/utils/__tests__/tailwind-tokens.test.ts
git commit -m "feat: map design tokens from CSS variables to Tailwind config"
```

---

## Task 3: Create the `cn` utility for conditional classes

**Files:**
- Create: `src/utils/cn.ts`
- Create: `src/utils/__tests__/cn.test.ts`

- [ ] **Step 1: Write the failing test**

Create `src/utils/__tests__/cn.test.ts`:

```ts
import { cn } from '../cn';

describe('cn utility', () => {
  it('merges static classes', () => {
    expect(cn('px-4', 'py-2')).toBe('px-4 py-2');
  });

  it('handles conditional classes', () => {
    expect(cn('px-4', false && 'hidden', 'py-2')).toBe('px-4 py-2');
  });

  it('deduplicates conflicting Tailwind classes (last wins)', () => {
    expect(cn('px-4', 'px-6')).toBe('px-6');
  });

  it('handles undefined and null inputs', () => {
    expect(cn('px-4', undefined, null, 'py-2')).toBe('px-4 py-2');
  });

  it('handles array inputs', () => {
    expect(cn(['px-4', 'py-2'], 'mt-1')).toBe('px-4 py-2 mt-1');
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
npx vitest run src/utils/__tests__/cn.test.ts
```

Expected: FAIL -- cannot find module `../cn`.

- [ ] **Step 3: Implement the `cn` utility**

Create `src/utils/cn.ts`:

```ts
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combines clsx (conditional class joining) with tailwind-merge
 * (deduplication of conflicting Tailwind utilities).
 *
 * Usage:
 *   cn('px-4 py-2', isActive && 'bg-primary', className)
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
npx vitest run src/utils/__tests__/cn.test.ts
```

Expected: All 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/utils/cn.ts src/utils/__tests__/cn.test.ts
git commit -m "feat: add cn() utility for conditional Tailwind class merging"
```

---

## Task 4: Migrate simple components (batch 1 of 3 -- approx. 8 components)

> Repeat Tasks 4-6 for all ~25 simple components, in batches of 8-9. Each batch is one task. Below is the template for one batch. Adjust component names per batch.

**Files (per component in batch):**
- Modify: `src/components/<Name>/<Name>.tsx`
- Modify: `src/components/<Name>/<Name>.test.tsx`
- Delete: `src/components/<Name>/<Name>.module.css`

**Migration pattern for simple components:**

A simple component looks like this before migration:

```tsx
import styles from './Avatar.module.css';

export function Avatar({ src, alt, size = 'md' }: AvatarProps) {
  return <img className={styles.avatar} src={src} alt={alt} />;
}
```

```css
/* Avatar.module.css */
.avatar {
  border-radius: var(--radius-full);
  object-fit: cover;
  width: 2.5rem;
  height: 2.5rem;
}
```

After migration:

```tsx
export function Avatar({ src, alt, size = 'md' }: AvatarProps) {
  return <img className="rounded-full object-cover w-10 h-10" src={src} alt={alt} />;
}
```

- [ ] **Step 1: Pick the first component in this batch (e.g., `Avatar`). Read its `.module.css` file. For every CSS class, write the equivalent Tailwind classes on paper (or in a scratch comment).**

Map each CSS property to its Tailwind utility:
- `border-radius: var(--radius-full)` => `rounded-full`
- `object-fit: cover` => `object-cover`
- `width: 2.5rem` => `w-10`
- `height: 2.5rem` => `h-10`

Refer to https://tailwindcss.com/docs for utility lookups. If a CSS property has no Tailwind equivalent, use an arbitrary value: `w-[2.5rem]`.

- [ ] **Step 2: Update snapshot tests or class-based assertions**

If the test file contains snapshot tests, they will break because class names change. Update assertions to check for Tailwind classes instead of CSS module hashed classes.

Before:
```tsx
expect(container.firstChild).toHaveClass('_avatar_1a2b3');
```

After:
```tsx
expect(container.firstChild).toHaveClass('rounded-full');
expect(container.firstChild).toHaveClass('object-cover');
```

If using snapshot tests, the snapshot will need to be updated after the component change. That is fine -- just run:

```bash
npx vitest run --update src/components/Avatar/Avatar.test.tsx
```

- [ ] **Step 3: Run the tests before making changes (baseline)**

```bash
npx vitest run src/components/Avatar/Avatar.test.tsx
```

Expected: All tests pass (current CSS module version still works).

- [ ] **Step 4: Replace CSS module imports with Tailwind classes in the component**

1. Remove `import styles from './Avatar.module.css';`
2. Replace every `styles.xxx` with the mapped Tailwind classes as a string literal.
3. If the component accepts a `className` prop, use `cn()`:

```tsx
import { cn } from '../../utils/cn';

export function Avatar({ src, alt, className }: AvatarProps) {
  return <img className={cn('rounded-full object-cover w-10 h-10', className)} src={src} alt={alt} />;
}
```

- [ ] **Step 5: Delete the `.module.css` file**

```bash
rm src/components/Avatar/Avatar.module.css
```

- [ ] **Step 6: Run the updated tests**

```bash
npx vitest run src/components/Avatar/Avatar.test.tsx
```

Expected: All tests pass with the new Tailwind classes.

- [ ] **Step 7: Visually verify the component in Storybook or the dev server**

```bash
npm run storybook
```

Open the Avatar story. Confirm it looks identical to the CSS module version.

- [ ] **Step 8: Repeat steps 1-7 for the remaining components in this batch**

Components in batch 1 (adjust to your actual component list): `Avatar`, `Badge`, `Divider`, `Spinner`, `Label`, `Tooltip`, `Icon`, `VisuallyHidden`.

- [ ] **Step 9: Run the full test suite**

```bash
npx vitest run
```

Expected: All tests pass. No regressions.

- [ ] **Step 10: Commit the batch**

```bash
git add -A
git commit -m "refactor: migrate simple components batch 1 to Tailwind (Avatar, Badge, Divider, Spinner, Label, Tooltip, Icon, VisuallyHidden)"
```

---

## Task 5: Migrate simple components (batch 2 of 3 -- approx. 8 components)

Follow the exact same pattern as Task 4. Components in batch 2 (adjust to your actual list): `Heading`, `Text`, `Link`, `Image`, `Separator`, `Skeleton`, `ProgressBar`, `Tag`.

- [ ] **Step 1-10: Same as Task 4, substituting the component names for batch 2.**

- [ ] **Commit**

```bash
git add -A
git commit -m "refactor: migrate simple components batch 2 to Tailwind (Heading, Text, Link, Image, Separator, Skeleton, ProgressBar, Tag)"
```

---

## Task 6: Migrate simple components (batch 3 of 3 -- approx. 9 components)

Follow the exact same pattern as Task 4. Components in batch 3 (adjust to your actual list): `Container`, `Grid`, `Stack`, `Flex`, `Spacer`, `AspectRatio`, `Center`, `Wrap`, `Box`.

- [ ] **Step 1-10: Same as Task 4, substituting the component names for batch 3.**

- [ ] **Commit**

```bash
git add -A
git commit -m "refactor: migrate simple components batch 3 to Tailwind (Container, Grid, Stack, Flex, Spacer, AspectRatio, Center, Wrap, Box)"
```

---

## Task 7: Migrate medium-complexity components (batch 1 of 2 -- approx. 8 components)

**Files (per component):**
- Modify: `src/components/<Name>/<Name>.tsx`
- Modify: `src/components/<Name>/<Name>.test.tsx`
- Delete: `src/components/<Name>/<Name>.module.css`

**Migration pattern for medium components:**

Medium components have props that select between CSS module classes. The pattern changes from object-key lookups to `cn()` with Tailwind variant maps.

Before:

```tsx
import styles from './Button.module.css';

const sizeClasses = {
  sm: styles.sm,
  md: styles.md,
  lg: styles.lg,
};

export function Button({ variant = 'primary', size = 'md', disabled, children }: ButtonProps) {
  return (
    <button
      className={`${styles.button} ${styles[variant]} ${sizeClasses[size]} ${disabled ? styles.disabled : ''}`}
      disabled={disabled}
    >
      {children}
    </button>
  );
}
```

After:

```tsx
import { cn } from '../../utils/cn';

const variantClasses = {
  primary: 'bg-primary text-white hover:bg-primary-hover',
  secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary-hover',
  ghost: 'bg-transparent hover:bg-neutral-100',
  danger: 'bg-danger text-white hover:bg-danger-hover',
} as const;

const sizeClasses = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg',
} as const;

export function Button({ variant = 'primary', size = 'md', disabled, className, children }: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-md font-medium transition-colors duration-fast',
        variantClasses[variant],
        sizeClasses[size],
        disabled && 'opacity-50 cursor-not-allowed pointer-events-none',
        className,
      )}
      disabled={disabled}
    >
      {children}
    </button>
  );
}
```

- [ ] **Step 1: Read the component's `.module.css` and its `.tsx` file. Identify every variant/size/state class. Create a mapping table:**

| CSS Module Class | Condition | Tailwind Equivalent |
|---|---|---|
| `.button` | always | `inline-flex items-center justify-center rounded-md font-medium transition-colors` |
| `.primary` | `variant === 'primary'` | `bg-primary text-white hover:bg-primary-hover` |
| `.disabled` | `disabled === true` | `opacity-50 cursor-not-allowed pointer-events-none` |

- [ ] **Step 2: Write tests that assert correct classes for each variant/state combination**

```tsx
import { render } from '@testing-library/react';
import { Button } from '../Button';

describe('Button Tailwind classes', () => {
  it('applies primary variant classes by default', () => {
    const { getByRole } = render(<Button>Click</Button>);
    const btn = getByRole('button');
    expect(btn).toHaveClass('bg-primary');
    expect(btn).toHaveClass('text-white');
  });

  it('applies ghost variant classes', () => {
    const { getByRole } = render(<Button variant="ghost">Click</Button>);
    const btn = getByRole('button');
    expect(btn).toHaveClass('bg-transparent');
  });

  it('applies disabled classes when disabled', () => {
    const { getByRole } = render(<Button disabled>Click</Button>);
    const btn = getByRole('button');
    expect(btn).toHaveClass('opacity-50');
    expect(btn).toHaveClass('cursor-not-allowed');
  });

  it('applies size classes', () => {
    const { getByRole } = render(<Button size="lg">Click</Button>);
    const btn = getByRole('button');
    expect(btn).toHaveClass('px-6');
    expect(btn).toHaveClass('text-lg');
  });

  it('merges external className', () => {
    const { getByRole } = render(<Button className="mt-4">Click</Button>);
    const btn = getByRole('button');
    expect(btn).toHaveClass('mt-4');
  });
});
```

- [ ] **Step 3: Run tests to verify they fail (component still uses CSS modules)**

```bash
npx vitest run src/components/Button/Button.test.tsx
```

Expected: FAIL -- elements do not have Tailwind classes.

- [ ] **Step 4: Refactor the component to use `cn()` with variant/size maps (as shown in the pattern above)**

- [ ] **Step 5: Delete the `.module.css` file**

```bash
rm src/components/Button/Button.module.css
```

- [ ] **Step 6: Run the tests**

```bash
npx vitest run src/components/Button/Button.test.tsx
```

Expected: All tests pass.

- [ ] **Step 7: Visual check in Storybook for each variant/size/state combination**

- [ ] **Step 8: Repeat for remaining components in batch**

Batch 1 (~8 components, adjust to your list): `Button`, `Input`, `Select`, `Checkbox`, `Radio`, `Switch`, `Textarea`, `Alert`.

- [ ] **Step 9: Run full test suite**

```bash
npx vitest run
```

Expected: All pass.

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "refactor: migrate medium-complexity components batch 1 to Tailwind (Button, Input, Select, Checkbox, Radio, Switch, Textarea, Alert)"
```

---

## Task 8: Migrate medium-complexity components (batch 2 of 2 -- approx. 7 components)

Follow the exact same pattern as Task 7. Components: `Card`, `Tabs`, `Breadcrumb`, `Pagination`, `NavLink`, `FormField`, `Toast`.

- [ ] **Step 1-10: Same as Task 7, substituting component names.**

- [ ] **Commit**

```bash
git add -A
git commit -m "refactor: migrate medium-complexity components batch 2 to Tailwind (Card, Tabs, Breadcrumb, Pagination, NavLink, FormField, Toast)"
```

---

## Task 9: Migrate complex components -- `Modal`

**Files:**
- Modify: `src/components/Modal/Modal.tsx`
- Modify: `src/components/Modal/Modal.test.tsx`
- Delete: `src/components/Modal/Modal.module.css`

Complex components need individual attention. Each gets its own task.

**Why Modal is complex:** It typically uses CSS custom properties for overlay opacity, z-index stacking, enter/exit animations (keyframes), and body scroll locking styles. CSS modules may define `@keyframes` that must be replaced with Tailwind animation utilities or custom `@keyframes` in `tailwind.config.js`.

- [ ] **Step 1: Audit `Modal.module.css` for features that go beyond static classes**

Look for:
- `@keyframes` -- Will need to be added to `tailwind.config.js` under `theme.extend.keyframes` and `theme.extend.animation`.
- `var(--z-modal)` -- Already mapped in Task 2. Use `z-modal`.
- Backdrop styles -- Use Tailwind's `backdrop:` modifier or a dedicated overlay div.
- Transition properties -- Map to Tailwind `transition-*` utilities.

- [ ] **Step 2: Add any required keyframes to `tailwind.config.js`**

```js
// In theme.extend:
keyframes: {
  'modal-enter': {
    '0%': { opacity: '0', transform: 'scale(0.95)' },
    '100%': { opacity: '1', transform: 'scale(1)' },
  },
  'modal-exit': {
    '0%': { opacity: '1', transform: 'scale(1)' },
    '100%': { opacity: '0', transform: 'scale(0.95)' },
  },
  'overlay-enter': {
    '0%': { opacity: '0' },
    '100%': { opacity: '1' },
  },
},
animation: {
  'modal-enter': 'modal-enter 200ms ease-out',
  'modal-exit': 'modal-exit 150ms ease-in',
  'overlay-enter': 'overlay-enter 200ms ease-out',
},
```

- [ ] **Step 3: Write tests for Modal's Tailwind output**

```tsx
import { render } from '@testing-library/react';
import { Modal } from '../Modal';

describe('Modal Tailwind classes', () => {
  it('renders overlay with correct z-index and animation', () => {
    const { container } = render(<Modal isOpen onClose={() => {}}>Content</Modal>);
    const overlay = container.querySelector('[data-testid="modal-overlay"]');
    expect(overlay).toHaveClass('z-modal');
    expect(overlay).toHaveClass('animate-overlay-enter');
  });

  it('renders modal panel with enter animation', () => {
    const { container } = render(<Modal isOpen onClose={() => {}}>Content</Modal>);
    const panel = container.querySelector('[data-testid="modal-panel"]');
    expect(panel).toHaveClass('animate-modal-enter');
  });

  it('centers the modal', () => {
    const { container } = render(<Modal isOpen onClose={() => {}}>Content</Modal>);
    const overlay = container.querySelector('[data-testid="modal-overlay"]');
    expect(overlay).toHaveClass('flex');
    expect(overlay).toHaveClass('items-center');
    expect(overlay).toHaveClass('justify-center');
  });
});
```

- [ ] **Step 4: Run tests to see them fail**

```bash
npx vitest run src/components/Modal/Modal.test.tsx
```

Expected: FAIL.

- [ ] **Step 5: Rewrite Modal component with Tailwind**

Replace CSS module references. Key changes:
- Overlay: `cn('fixed inset-0 z-modal bg-black/50 flex items-center justify-center animate-overlay-enter')`
- Panel: `cn('bg-white rounded-lg shadow-xl max-w-lg w-full p-6 animate-modal-enter', className)`
- If the old code used inline `style` to set CSS variables (e.g., `style={{ '--modal-width': width }}`), replace with Tailwind arbitrary values: `max-w-[${width}]` or a size prop map.

- [ ] **Step 6: Delete the CSS module file**

```bash
rm src/components/Modal/Modal.module.css
```

- [ ] **Step 7: Run tests**

```bash
npx vitest run src/components/Modal/Modal.test.tsx
```

Expected: All pass.

- [ ] **Step 8: Visual check -- open/close animation, overlay click, escape key**

- [ ] **Step 9: Commit**

```bash
git add tailwind.config.js src/components/Modal/Modal.tsx src/components/Modal/Modal.test.tsx
git rm src/components/Modal/Modal.module.css
git commit -m "refactor: migrate Modal to Tailwind with custom keyframe animations"
```

---

## Task 10: Migrate complex components -- `Dropdown`

**Files:**
- Modify: `src/components/Dropdown/Dropdown.tsx`
- Modify: `src/components/Dropdown/Dropdown.test.tsx`
- Delete: `src/components/Dropdown/Dropdown.module.css`

**Why Dropdown is complex:** Positioning logic may use CSS custom properties for offset/placement. Open/close state drives class transitions. May use `transform-origin` dynamically based on dropdown direction.

- [ ] **Step 1: Audit `Dropdown.module.css` for dynamic positioning and transitions**

Look for:
- Placement-dependent styles (`top`, `bottom`, `left`, `right` variants)
- `transform-origin` changes based on direction
- Transition timing for open/close

- [ ] **Step 2: Create a placement class map**

```tsx
const placementClasses = {
  'bottom-start': 'top-full left-0 origin-top-left',
  'bottom-end': 'top-full right-0 origin-top-right',
  'top-start': 'bottom-full left-0 origin-bottom-left',
  'top-end': 'bottom-full right-0 origin-bottom-right',
} as const;
```

- [ ] **Step 3: Write tests covering each placement variant and open/closed states**

```tsx
describe('Dropdown Tailwind classes', () => {
  it('positions menu below trigger by default', () => {
    const { getByRole } = render(<Dropdown isOpen placement="bottom-start" />);
    const menu = getByRole('listbox');
    expect(menu).toHaveClass('top-full');
    expect(menu).toHaveClass('left-0');
  });

  it('hides menu when closed', () => {
    const { container } = render(<Dropdown isOpen={false} />);
    const menu = container.querySelector('[role="listbox"]');
    expect(menu).toHaveClass('hidden');
  });
});
```

- [ ] **Step 4: Run tests to see them fail**

```bash
npx vitest run src/components/Dropdown/Dropdown.test.tsx
```

- [ ] **Step 5: Rewrite Dropdown with Tailwind, using the placement map and `cn()`**

- [ ] **Step 6: Delete CSS module, run tests, visual check**

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor: migrate Dropdown to Tailwind with placement variant maps"
```

---

## Task 11: Migrate complex components -- `DataTable`

**Files:**
- Modify: `src/components/DataTable/DataTable.tsx`
- Modify: `src/components/DataTable/DataTable.test.tsx`
- Delete: `src/components/DataTable/DataTable.module.css`

**Why DataTable is complex:** Often has dynamic column widths via CSS variables, sticky header styles, striped rows via `:nth-child`, and responsive overflow behavior.

- [ ] **Step 1: Audit the CSS module for dynamic width and sticky behavior**

Look for:
- `style={{ '--col-width': ... }}` patterns in the TSX -- replace with inline `style={{ width }}` or Tailwind `w-[value]`
- `position: sticky` -- use Tailwind `sticky top-0`
- `:nth-child(even)` -- use Tailwind `even:bg-neutral-50` on `<tr>`
- `overflow-x: auto` -- use `overflow-x-auto` on the wrapper

- [ ] **Step 2: Write tests for table structure classes**

```tsx
describe('DataTable Tailwind classes', () => {
  it('wraps table in scrollable container', () => {
    const { container } = render(<DataTable columns={cols} data={rows} />);
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('overflow-x-auto');
  });

  it('makes header sticky', () => {
    const { container } = render(<DataTable columns={cols} data={rows} />);
    const thead = container.querySelector('thead');
    expect(thead).toHaveClass('sticky');
    expect(thead).toHaveClass('top-0');
  });

  it('applies striped row styling', () => {
    const { container } = render(<DataTable columns={cols} data={rows} />);
    const tbodyRows = container.querySelectorAll('tbody tr');
    tbodyRows.forEach(row => {
      expect(row).toHaveClass('even:bg-neutral-50');
    });
  });
});
```

- [ ] **Step 3: Run tests to see them fail**

- [ ] **Step 4: Rewrite DataTable with Tailwind**

Key replacements:
- Wrapper: `cn('overflow-x-auto rounded-lg border border-neutral-200')`
- Thead: `cn('sticky top-0 bg-white z-10')`
- Th: `cn('px-4 py-3 text-left text-sm font-semibold text-neutral-700')`
- Tr: `cn('border-b border-neutral-100 even:bg-neutral-50')`
- Td: `cn('px-4 py-3 text-sm')`
- For dynamic column widths, use inline `style={{ width }}` or `style={{ minWidth }}` since these are truly dynamic values that cannot be expressed as utility classes.

- [ ] **Step 5: Delete CSS module, run tests, visual check**

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: migrate DataTable to Tailwind with sticky headers and striped rows"
```

---

## Task 12: Migrate complex components -- `Accordion`

**Files:**
- Modify: `src/components/Accordion/Accordion.tsx`
- Modify: `src/components/Accordion/Accordion.test.tsx`
- Delete: `src/components/Accordion/Accordion.module.css`

**Why Accordion is complex:** Height animation for expand/collapse. Often uses `max-height` with CSS transitions and a ref to measure content height.

- [ ] **Step 1: Audit for height animation approach**

If using `max-height` transition, options:
1. Use Tailwind's `grid-rows` animation trick: parent toggles `grid-template-rows: 0fr` / `grid-template-rows: 1fr` with `transition-all`.
2. Keep a small inline style for measured `max-height` and use Tailwind for everything else.
3. Use the `details`/`summary` HTML elements with Tailwind styling (simplest if no animation is needed).

- [ ] **Step 2: Add grid-row animation keyframes to Tailwind config if using approach 1**

- [ ] **Step 3: Write tests, rewrite component, delete CSS module, verify**

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: migrate Accordion to Tailwind with grid-row expand animation"
```

---

## Task 13: Migrate complex components -- `ColorPicker`, `ThemeProvider`, `Layout`

**Files:** The respective component directories.

**Why these are complex:**

- **ColorPicker**: Uses CSS custom properties to dynamically set HSL values for the preview swatch. These must remain as inline styles -- Tailwind cannot handle runtime color values. Migrate all static styles to Tailwind; keep `style={{ backgroundColor: dynamicColor }}` for runtime values.

- **ThemeProvider**: This component likely sets CSS custom properties on a root element. After migration, ThemeProvider should instead swap Tailwind's `dark` class or set `data-theme` attributes and use Tailwind's dark mode / custom variants. Update `tailwind.config.js` to use `darkMode: 'class'` or a custom variant selector.

- **Layout**: Uses responsive CSS with media queries, potentially CSS Grid with named areas. Tailwind handles this well: `grid grid-cols-[250px_1fr]` with responsive prefixes like `md:grid-cols-[250px_1fr] grid-cols-1`.

- [ ] **Step 1: Migrate ColorPicker -- keep inline styles for dynamic values, Tailwind for static**

- [ ] **Step 2: Migrate ThemeProvider -- switch from CSS variable injection to Tailwind dark mode**

Add to `tailwind.config.js`:

```js
darkMode: 'class',
```

ThemeProvider becomes:

```tsx
export function ThemeProvider({ theme, children }: ThemeProviderProps) {
  return (
    <div className={cn(theme === 'dark' && 'dark')}>
      {children}
    </div>
  );
}
```

- [ ] **Step 3: Migrate Layout -- replace CSS Grid / media queries with Tailwind responsive utilities**

- [ ] **Step 4: Write/update tests for all three, run full suite**

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: migrate ColorPicker, ThemeProvider, Layout to Tailwind"
```

---

## Task 14: Remove CSS module infrastructure

**Files:**
- Delete: All remaining `.module.css` files (should be none if previous tasks were thorough)
- Modify: Build config (e.g., `vite.config.ts`, `webpack.config.js`, or `next.config.js`) to remove CSS module loader config if it was explicitly configured
- Modify: `tsconfig.json` to remove CSS module type declarations if present
- Delete: `src/types/css-modules.d.ts` or similar type declaration file (if it exists)
- Delete: `src/styles/tokens.css` (the old CSS custom property file, if all tokens are now in Tailwind config)

- [ ] **Step 1: Search for any remaining `.module.css` files**

```bash
find src -name '*.module.css' -type f
```

Expected: No results. If any remain, migrate them now.

- [ ] **Step 2: Search for any remaining `styles.` or `.module.css` imports**

```bash
grep -r "\.module\.css" src/ --include="*.tsx" --include="*.ts"
```

Expected: No results.

- [ ] **Step 3: Remove CSS module type declarations**

If `src/types/css-modules.d.ts` or a similar file exists with:

```ts
declare module '*.module.css' {
  const classes: { [key: string]: string };
  export default classes;
}
```

Delete it.

- [ ] **Step 4: Remove CSS module config from build tool**

Check your bundler config. If using Vite, CSS modules work by default so there may be nothing to remove. If using webpack with explicit `css-loader` config for modules, remove the modules-specific config but keep regular CSS loading for Tailwind.

- [ ] **Step 5: Remove the old design token CSS file**

```bash
rm src/styles/tokens.css
```

Only do this if ALL consumers of these CSS variables have been migrated. Search first:

```bash
grep -r "var(--" src/ --include="*.tsx" --include="*.ts" --include="*.css"
```

Expected: No results (except `globals.css` which has Tailwind directives, not custom properties).

- [ ] **Step 6: Run full test suite and build**

```bash
npx vitest run
npm run build
```

Expected: All tests pass, build succeeds.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: remove CSS module infrastructure, token CSS, and type declarations"
```

---

## Task 15: Final validation and cleanup

**Files:**
- Modify: `package.json` (remove unused CSS-module-related devDependencies if any)
- Modify: `tailwind.config.js` (run Tailwind's purge/content check)

- [ ] **Step 1: Check for unused CSS-related devDependencies**

Look in `package.json` for packages that were only needed for CSS modules:
- `typed-css-modules`
- `css-modules-typescript-loader`
- `postcss-modules` (if Tailwind's PostCSS replaces it)

Remove them:

```bash
npm uninstall typed-css-modules css-modules-typescript-loader
```

- [ ] **Step 2: Verify Tailwind content config catches all files**

Check that `tailwind.config.js` `content` array matches all files that use Tailwind classes:

```js
content: ['./src/**/*.{ts,tsx,js,jsx}'],
```

If there are other directories (e.g., `stories/`, `pages/`), add them.

- [ ] **Step 3: Run a production build and check bundle size**

```bash
npm run build
```

Compare the CSS bundle size to the old CSS module build. Tailwind with purging should produce a smaller CSS file.

- [ ] **Step 4: Run the full test suite one final time**

```bash
npx vitest run
```

Expected: All 47 components pass all tests.

- [ ] **Step 5: Run linting**

```bash
npm run lint
```

Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: remove unused CSS module dependencies and finalize Tailwind migration"
```

---

## Migration Decision Reference

Use this table when deciding how to handle specific CSS patterns during any task:

| CSS Module Pattern | Tailwind Approach |
|---|---|
| `.class { color: var(--token); }` | Use the mapped Tailwind token: `text-primary` |
| `.class { margin: 1rem 2rem; }` | Use utility classes: `mx-8 my-4` |
| `composes: base from './shared.module.css';` | Use `cn()` to compose base + variant classes |
| `.class:hover { ... }` | Use `hover:` prefix: `hover:bg-primary-hover` |
| `.class:focus-visible { ... }` | Use `focus-visible:` prefix: `focus-visible:ring-2` |
| `@media (min-width: 768px) { ... }` | Use `md:` prefix: `md:flex-row` |
| `@keyframes name { ... }` | Add to `tailwind.config.js` `theme.extend.keyframes` |
| `style={{ '--var': value }}` + CSS using `var(--var)` | Use inline `style` for truly dynamic values, or a prop-to-class map for known variants |
| `:nth-child(even)` | Use `even:` modifier: `even:bg-neutral-50` |
| `position: sticky` | Use `sticky` utility |
| `overflow-x: auto` | Use `overflow-x-auto` |
| `.dark .class { ... }` | Use `dark:` prefix: `dark:bg-neutral-900` |
