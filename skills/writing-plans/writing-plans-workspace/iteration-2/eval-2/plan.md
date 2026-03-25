# CSS Modules to Tailwind Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate a 47-component React component library from CSS modules to Tailwind CSS, including design token mapping and dynamic class logic conversion.

**Architecture:** The migration proceeds in four phases: foundation (Tailwind config and token mapping), pilot batch (a small group of simple components to validate the approach), bulk migration (remaining simple components in batches), and complex component migration (components with dynamic class logic that require rethinking). Each phase produces working, testable output before the next begins. CSS module files are removed only after their replacement is verified.

**Tech Stack:** React, Tailwind CSS, PostCSS, existing CSS Modules (to be removed)

---

## Phase 1: Foundation — Tailwind Configuration and Design Token Mapping

### Task 1.1: Audit existing design tokens

- [ ] Catalog all CSS custom properties (variables) used across the component library — colors, spacing, typography, shadows, breakpoints, and any other tokens.
- [ ] Identify which tokens map directly to Tailwind defaults, which need custom values in the Tailwind config, and which represent concepts Tailwind handles differently (e.g., composite tokens that combine multiple properties).

**Files:** All CSS module files across the 47 components.

**Constraints:** Some tokens may be defined in multiple places or overridden at different levels. The audit must capture the full inheritance chain, not just top-level definitions. Pay attention to tokens that are computed or derived from other tokens, because Tailwind config values are static.

**Acceptance criteria:** A complete mapping document (or structured comment block in the Tailwind config) that accounts for every CSS variable currently in use, with a clear decision for each: direct Tailwind equivalent, custom config entry, or needs special handling.

**Risks:** Tokens that use CSS calc() or are context-dependent (e.g., dark mode overrides via variable reassignment) will not translate to simple Tailwind config entries. These must be flagged for resolution before proceeding.

### Task 1.2: Set up Tailwind configuration with custom theme

- [ ] Install Tailwind CSS and its PostCSS dependencies.
- [ ] Create the Tailwind config file, extending the default theme with all custom tokens identified in the audit.
- [ ] Configure the content paths so Tailwind scans the component source files for class usage.

**Files:** tailwind.config.js (or .ts), postcss.config.js, package.json

**Constraints:** The config must preserve the exact design token values currently in use, so that migrated components are visually identical. Do not rename tokens unless the CSS variable name directly conflicts with a Tailwind convention. Preserving names reduces cognitive overhead during the bulk migration.

**Acceptance criteria:** Tailwind builds successfully. A simple test file using the custom theme values produces the expected CSS output. All custom tokens are accessible via Tailwind utility classes.

**Risks:** If the project uses CSS variable theming for runtime theme switching (e.g., light/dark via CSS variable reassignment on a parent element), Tailwind's static config approach will require a different strategy. Investigate whether Tailwind's dark mode or CSS variable mode can replicate the existing behavior before committing to the config shape.

### Task 1.3: Create a utility mapping reference for the team

- [ ] Document the most common CSS module patterns in this codebase alongside their Tailwind equivalents — not as a translation table for every property, but as a guide covering the recurring patterns.
- [ ] Specifically document how dynamic class patterns (conditional classes, computed styles) should be handled in the Tailwind world, because these cannot be simple find-and-replace.

**Files:** A reference document or comments in the Tailwind config.

**Constraints:** This reference must address the dynamic class patterns identified during the audit, not just static mappings. The implementing agents will rely on this reference during bulk migration.

**Acceptance criteria:** The reference covers static class replacement patterns, conditional/dynamic class strategies (e.g., clsx/classnames with Tailwind classes), responsive patterns, and pseudo-state handling. It is accurate against the actual Tailwind config created in Task 1.2.

---

## Phase 2: Pilot Batch — Validate the Migration Approach

### Task 2.1: Classify components by migration complexity

- [ ] Sort all 47 components into three tiers:
  - **Simple** — static classes only, no conditional logic, no computed styles (~60-70% of components typically).
  - **Moderate** — some conditional classes (e.g., active/disabled states toggled via props) but predictable patterns.
  - **Complex** — dynamic class construction, style objects, runtime-computed values, or heavy use of CSS variable overrides.

**Files:** All 47 component source files and their associated CSS module files.

**Constraints:** Classification must be based on actual code inspection, not assumptions. A component that looks simple might have a CSS module that uses :global, composes, or other advanced CSS module features that complicate migration.

**Acceptance criteria:** Every component is classified into one of the three tiers. Complex components each have a brief note explaining what makes them complex, because this informs how they are handled in Phase 4.

**Risks:** Misclassifying a complex component as simple will cause problems during bulk migration. Err on the side of classifying upward — it is cheaper to discover a component is simpler than expected than to hit unexpected complexity mid-migration.

### Task 2.2: Migrate 3-5 pilot components from the "simple" tier

- [ ] Select 3-5 simple components that collectively exercise a variety of token types (color, spacing, typography, layout).
- [ ] For each pilot component, replace the CSS module import with Tailwind utility classes applied directly in JSX.
- [ ] Remove the CSS module file for each migrated component.
- [ ] Verify that each component renders identically to its pre-migration state.

**Files:** The selected component files (JSX/TSX) and their CSS module files (.module.css).

**Constraints:** Do not introduce any new visual behavior. The goal is pixel-parity with the existing implementation. If a component's CSS module uses animations or transitions, those must be replicated in Tailwind (using Tailwind's transition/animation utilities or an inline @keyframes definition in the global styles).

**Acceptance criteria:** All pilot components render identically to their CSS module versions. Existing tests pass without modification (or with only import-related changes). The CSS module files for these components are deleted and no longer referenced.

**Risks:** If visual parity cannot be achieved for a pilot component, stop and investigate before proceeding to bulk migration. The pilot exists specifically to surface these issues early.

### Task 2.3: Migrate 1-2 pilot components from the "moderate" tier

- [ ] Select 1-2 moderate-complexity components that use conditional class application (e.g., different styles based on props like variant, size, or disabled state).
- [ ] Replace the CSS module class toggling with a Tailwind-compatible pattern — likely using a utility like clsx or classnames to conditionally apply Tailwind classes.
- [ ] Remove the CSS module files.
- [ ] Verify visual and behavioral parity.

**Files:** The selected component files and their CSS module files.

**Constraints:** The pattern chosen for conditional classes here becomes the standard for all moderate components in Phase 3. Choose a pattern that is readable and maintainable, not just the most concise. If the codebase does not already depend on clsx or classnames, decide whether to add one — Tailwind's class strings can become unwieldy without a helper.

**Acceptance criteria:** Conditional styling works identically to before (e.g., a Button with variant="primary" vs variant="secondary" renders the correct styles). Tests pass. Pattern is documented in the reference from Task 1.3.

---

## Phase 3: Bulk Migration — Simple and Moderate Components

### Task 3.1: Migrate remaining simple components in batches of 8-10

- [ ] Work through the remaining simple-tier components in batches. Each batch should be committed independently so that any regression is easy to isolate.
- [ ] For each component: replace CSS module imports with Tailwind classes, delete the CSS module file, verify rendering.
- [ ] Run the full test suite after each batch.

**Files:** All simple-tier component files and their CSS module files (exact list determined by Task 2.1 classification).

**Constraints:** Maintain the same patterns established in the pilot. Do not introduce new patterns or shortcuts during bulk migration — consistency matters more than cleverness when migrating at scale. If a component turns out to be more complex than its classification suggested, move it to the moderate or complex tier rather than forcing a simple migration.

**Acceptance criteria:** All simple-tier components are migrated. No CSS module files remain for these components. Full test suite passes after each batch. No visual regressions.

**Risks:** Batch size of 8-10 is a guideline. If regressions start appearing, reduce batch size to isolate problems faster. If migration is going smoothly, batches can grow slightly, but never migrate all remaining components in one batch.

### Task 3.2: Migrate remaining moderate components in batches of 4-6

- [ ] Work through the remaining moderate-tier components using the conditional class pattern validated in the pilot.
- [ ] Each batch committed independently.
- [ ] Run the full test suite after each batch.

**Files:** All moderate-tier component files and their CSS module files.

**Constraints:** Moderate components may have more varied conditional patterns than the pilot covered. When encountering a new pattern, document the Tailwind approach before applying it across multiple components. Careful: components that share CSS module files (via composes or shared stylesheets) must be migrated together, not split across batches.

**Acceptance criteria:** All moderate-tier components are migrated. No CSS module files remain for these components. Full test suite passes. Conditional styling behaves identically to before.

---

## Phase 4: Complex Component Migration

### Task 4.1: Design migration strategy for each complex component

- [ ] For each complex-tier component, analyze the dynamic class logic and determine the appropriate Tailwind approach. This is not find-and-replace — each complex component may need a different strategy.
- [ ] Common patterns to address:
  - Runtime style computation (e.g., inline styles derived from props) — may need to remain as inline styles or use CSS variables with Tailwind.
  - Highly dynamic class construction (e.g., building class names from string interpolation) — needs restructuring into explicit conditional mappings.
  - CSS module composition (composes) used for component variants — needs replacement with Tailwind variant patterns or component-level abstractions.
  - Animation/keyframe definitions scoped to the module — need global keyframe definitions or Tailwind animation config.

**Files:** All complex-tier component files.

**Constraints:** Do not force every complex component into pure Tailwind utilities. Some components may legitimately need a small amount of custom CSS (defined in a global stylesheet or via Tailwind's @layer). The goal is to eliminate CSS modules, not to eliminate all CSS. Pragmatism over purity.

**Acceptance criteria:** Each complex component has a documented migration strategy before implementation begins. Strategies are reviewed for feasibility.

**Risks:** This is the highest-risk phase. Complex components may reveal assumptions baked into the CSS module architecture that do not translate cleanly. If a component's migration strategy would require significant refactoring of the component's logic (not just its styling), flag this for discussion before proceeding.

### Task 4.2: Migrate complex components one at a time

- [ ] Migrate each complex component individually, following its documented strategy from Task 4.1.
- [ ] Commit each complex component migration separately.
- [ ] Verify visual and behavioral parity for each component in isolation, including all its variants and states.

**Files:** Each complex-tier component file and its CSS module file, migrated one at a time.

**Constraints:** Complex components get individual attention because they are the most likely to break. Do not batch these. If a component's pre-planned strategy does not work in practice, revise the strategy rather than forcing a broken approach.

**Acceptance criteria:** Each complex component is migrated, tested, and committed individually. All dynamic styling works as before. No CSS module files remain.

---

## Phase 5: Cleanup and Verification

### Task 5.1: Remove CSS module infrastructure

- [ ] Remove all CSS module configuration from the build toolchain (webpack/vite CSS module loaders, PostCSS plugins that were only needed for CSS modules, etc.).
- [ ] Remove any CSS module-related dev dependencies from package.json.
- [ ] Verify the build still succeeds.

**Files:** Build config files (webpack.config / vite.config), postcss.config, package.json.

**Constraints:** Be careful not to remove PostCSS plugins that Tailwind still needs. Only remove tooling that was exclusively serving CSS modules.

**Acceptance criteria:** Build succeeds with no CSS module configuration. No references to CSS modules remain in build config. No unused CSS module dependencies remain in package.json.

**Risks:** Some PostCSS plugins may serve dual purposes (CSS modules and general CSS processing). Verify each removal does not break Tailwind's PostCSS pipeline.

### Task 5.2: Full regression verification

- [ ] Run the complete test suite.
- [ ] Perform a visual review of all 47 components, comparing against pre-migration screenshots or Storybook snapshots if available.
- [ ] Verify that no CSS module files (.module.css) remain anywhere in the source tree.
- [ ] Verify that no CSS module imports remain in any component file.
- [ ] Confirm the production build output size is reasonable — Tailwind with purging should produce a smaller CSS bundle than 47 individual CSS modules.

**Files:** Entire component source tree.

**Acceptance criteria:** All tests pass. No CSS module files or imports remain. Production build succeeds and the CSS bundle size is equal to or smaller than before. No visual regressions across all 47 components.

### Task 5.3: Commit and document the completed migration

- [ ] Commit any remaining cleanup changes.
- [ ] Update the project's contributing guidelines or developer documentation to reflect that components now use Tailwind instead of CSS modules, so future contributors follow the new pattern.

**Files:** Contributing docs, developer setup docs, or README sections related to styling.

**Acceptance criteria:** Documentation reflects the current styling approach. A new contributor reading the docs would know to use Tailwind, not CSS modules.
