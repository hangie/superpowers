# Checkout Flow End-to-End Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add comprehensive end-to-end Playwright tests covering the 5-step checkout flow (cart review, address, shipping method, payment, confirmation), including a strategy for the third-party payment iframe that cannot be automated directly.

**Architecture:** Tests will be organized as a dedicated test suite with shared fixtures for cart seeding, address generation, and payment stubbing. The payment step requires a mock/intercept approach because the third-party iframe cannot be driven through Playwright directly — we will intercept the iframe's network requests and simulate successful payment responses at the network level. Each checkout step gets its own focused test file, plus an integration file that exercises the full flow end-to-end.

**Tech Stack:** Playwright (existing setup), Playwright route interception for payment mocking

---

## File Structure

- **tests/e2e/checkout/cart-review.spec.ts** — Tests for step 1: viewing cart contents, modifying quantities, removing items, proceeding to address
- **tests/e2e/checkout/address.spec.ts** — Tests for step 2: entering shipping address, validation errors, saved address selection
- **tests/e2e/checkout/shipping-method.spec.ts** — Tests for step 3: selecting shipping options, price updates
- **tests/e2e/checkout/payment.spec.ts** — Tests for step 4: payment iframe loading, mocked payment completion, error handling
- **tests/e2e/checkout/confirmation.spec.ts** — Tests for step 5: order confirmation display, order number generation
- **tests/e2e/checkout/full-flow.spec.ts** — End-to-end test walking through all 5 steps in sequence
- **tests/e2e/checkout/fixtures.ts** — Shared test fixtures: cart seeding, test address data, payment route interception helpers
- **tests/e2e/checkout/helpers.ts** — Page object helpers or utility functions for common checkout interactions (filling address forms, selecting shipping, etc.)

## Phase 1: Foundation — Fixtures and Cart Review

### Task 1.1: Create shared fixtures and helpers

- [ ] **Goal:** Establish the reusable test infrastructure so that all subsequent checkout tests can seed a cart and share common setup, because duplicating this across every test file would create maintenance burden and slow iteration.
- [ ] **Files:** Create `tests/e2e/checkout/fixtures.ts` and `tests/e2e/checkout/helpers.ts`
- [ ] **Constraints:** The fixtures must work with the existing Playwright configuration — check the existing Playwright config file for base URL, browser settings, and any existing fixture patterns before designing new ones. Cart seeding should use the application's actual API or UI flow rather than direct database manipulation, so the tests reflect real user behavior.
- [ ] **Acceptance criteria:** Fixtures file exports a cart-seeding fixture that adds at least one product to the cart and navigates to the checkout entry point. Helpers file exports reusable functions for common form interactions. Both files import cleanly and cause no type errors.
- [ ] **Risks:** The existing Playwright setup may use a custom fixture extension pattern — if so, the new fixtures must extend from the same base rather than creating a parallel setup.

### Task 1.2: Write cart review step tests

- [ ] **Goal:** Verify the cart review page displays correct items, allows quantity changes, and enables proceeding to the address step, because this is the entry point to checkout and failures here block all subsequent steps.
- [ ] **Files:** Create `tests/e2e/checkout/cart-review.spec.ts`
- [ ] **Constraints:** Tests should use the cart-seeding fixture from Task 1.1. Test at least: displaying correct item names and prices, changing item quantity and seeing an updated total, removing an item, and clicking through to the address step.
- [ ] **Acceptance criteria:** All cart review tests pass. Tests use the shared fixtures. At least 4 distinct test cases covering the scenarios listed above.
- [ ] **Risks:** Cart state may be stored in cookies, local storage, or server-side sessions — the fixture needs to handle whichever mechanism the application uses, and tests should not leak state between runs.

### Task 1.3: Run cart review tests and commit

- [ ] **Goal:** Validate that the cart review tests execute correctly against the running application and commit the working foundation.
- [ ] **Acceptance criteria:** All cart review tests pass. Commit includes fixtures, helpers, and cart review spec.

## Phase 2: Address and Shipping Steps

### Task 2.1: Write address step tests

- [ ] **Goal:** Cover the address entry form including validation behavior, because address validation errors are a common source of user drop-off and must work correctly.
- [ ] **Files:** Create `tests/e2e/checkout/address.spec.ts`
- [ ] **Constraints:** Start from a seeded cart that has already passed cart review. Test at least: submitting a valid address and proceeding, triggering validation errors on required fields (empty name, invalid zip), and if the application supports saved addresses, selecting one. Use the helpers file for form-filling utilities.
- [ ] **Acceptance criteria:** All address tests pass. Validation error scenarios confirm that the UI displays appropriate messages and blocks progression. Successful address entry navigates to the shipping method step.
- [ ] **Risks:** Address validation may involve an external API call (address verification service) — if so, consider whether to mock it or rely on known-good test addresses.

### Task 2.2: Write shipping method step tests

- [ ] **Goal:** Verify that shipping method selection works and updates the order total, because incorrect shipping cost calculation is a revenue-impacting bug.
- [ ] **Files:** Create `tests/e2e/checkout/shipping-method.spec.ts`
- [ ] **Constraints:** Start from a state where cart review and address are complete. Test at least: displaying available shipping options with prices, selecting different options and verifying the total updates, and proceeding to the payment step.
- [ ] **Acceptance criteria:** All shipping method tests pass. At least one test confirms that changing the shipping method visibly changes the displayed total. Proceeding navigates to the payment step.

### Task 2.3: Run address and shipping tests and commit

- [ ] **Goal:** Validate the address and shipping tests work and commit them as a stable checkpoint.
- [ ] **Acceptance criteria:** All tests from Phase 1 and Phase 2 pass together. Commit includes both new spec files and any helper updates.

## Phase 3: Payment Step — Iframe Mocking Strategy

### Task 3.1: Implement payment iframe intercept fixture

- [ ] **Goal:** Create the network-level mock for the third-party payment iframe, because the iframe cannot be automated directly through Playwright and this is the critical technical challenge of the entire test suite.
- [ ] **Files:** Update `tests/e2e/checkout/fixtures.ts` with payment interception logic
- [ ] **Constraints:** Use Playwright's route interception to catch requests to the payment provider's domain. The mock should simulate a successful payment callback — investigate the application's payment integration to understand what message or redirect the iframe sends back to the parent page on success. Important: also create an interception variant that simulates payment failure, so error paths can be tested. Do not attempt to interact with the iframe's internal DOM — only intercept network traffic and simulate the response the parent page expects.
- [ ] **Acceptance criteria:** The payment intercept fixture is available for use in tests. It supports both success and failure simulation modes. It does not require the actual payment provider to be reachable.
- [ ] **Risks:** This is the highest-risk task. The mocking approach depends on understanding exactly how the payment iframe communicates completion to the parent page (postMessage, redirect, callback URL, webhook). If the mechanism is unclear, investigation is needed before implementation — check the payment integration code in the application source. If the payment provider uses a redirect-based flow rather than postMessage, the interception approach will differ significantly.

### Task 3.2: Write payment step tests

- [ ] **Goal:** Test the payment step including successful payment, failed payment, and iframe loading behavior, because payment is where checkout most commonly fails in production.
- [ ] **Files:** Create `tests/e2e/checkout/payment.spec.ts`
- [ ] **Constraints:** Use the payment intercept fixture from Task 3.1. Test at least: the payment iframe loading (or its container being visible), successful payment proceeding to confirmation, and failed payment displaying an error message without navigating away. All tests must work without the real payment provider being available.
- [ ] **Acceptance criteria:** All payment tests pass using the mocked payment flow. Both success and failure paths are covered. Tests do not make real requests to the payment provider.
- [ ] **Risks:** If the application has client-side payment provider SDK initialization that fails when the provider is unreachable, route interception for the SDK script itself may also be needed.

### Task 3.3: Run payment tests and commit

- [ ] **Goal:** Validate payment tests work in isolation and alongside earlier tests.
- [ ] **Acceptance criteria:** All checkout tests (cart, address, shipping, payment) pass together. Commit includes the payment fixture updates and payment spec.

## Phase 4: Confirmation and Full Flow

### Task 4.1: Write confirmation step tests

- [ ] **Goal:** Verify the order confirmation page displays expected information after a successful checkout, because this is the final proof that the entire flow completed correctly.
- [ ] **Files:** Create `tests/e2e/checkout/confirmation.spec.ts`
- [ ] **Constraints:** Start from a fully completed checkout (using all previous fixtures including payment mock). Test at least: order confirmation page is displayed, an order number or confirmation identifier is shown, and order summary matches what was in the cart. Careful: this test depends on all previous steps completing successfully, so it effectively validates the whole chain.
- [ ] **Acceptance criteria:** Confirmation tests pass. The test verifies at least one piece of order-specific data (order number, item list, or total) is displayed on the confirmation page.

### Task 4.2: Write full end-to-end flow test

- [ ] **Goal:** Create a single test that walks through all 5 checkout steps in sequence, because while individual step tests catch regressions in isolation, a full-flow test catches integration issues between steps (state not carrying forward, redirects breaking, etc.).
- [ ] **Files:** Create `tests/e2e/checkout/full-flow.spec.ts`
- [ ] **Constraints:** This test should exercise the happy path only — edge cases are covered in the individual step tests. Use shared helpers for form interactions but do not abstract away the flow itself, so the test reads as a clear narrative of the user journey. The test should assert at each step boundary that the correct page/step is active before proceeding, so failures pinpoint which transition broke.
- [ ] **Acceptance criteria:** The full-flow test passes end-to-end from cart review through confirmation. Each step transition includes an assertion that the next step loaded. The test completes in a reasonable time (under 30 seconds as a guideline).
- [ ] **Risks:** Full-flow tests are inherently more fragile than isolated step tests. If this test becomes flaky, the fix should be in the application or fixtures, not in adding retries or waits to the test itself.

### Task 4.3: Run complete test suite and commit

- [ ] **Goal:** Final validation that all checkout tests pass together without conflicts or state leakage.
- [ ] **Acceptance criteria:** Every checkout test file passes when run together. No test depends on execution order. Commit includes confirmation spec, full-flow spec, and any final helper updates.

## Phase 5: CI and Documentation

### Task 5.1: Verify CI compatibility

- [ ] **Goal:** Ensure the new checkout tests run correctly in whatever CI environment is configured, because tests that only pass locally provide false confidence.
- [ ] **Constraints:** Check the existing Playwright CI configuration. The payment mocking approach must not require network access to the payment provider. If the existing CI setup runs Playwright tests, verify the new tests are picked up automatically by the test discovery pattern. If there is a separate e2e test command or CI job, confirm the new tests are included.
- [ ] **Acceptance criteria:** Checkout tests are included in the CI test run. No additional CI configuration is needed, or necessary configuration changes are committed.
- [ ] **Risks:** CI environments may have stricter network policies that affect route interception behavior — verify the payment mock works identically in CI.

### Task 5.2: Final commit and cleanup

- [ ] **Goal:** Ensure all files are committed, no temporary debugging code remains, and the test suite is in a clean, maintainable state.
- [ ] **Acceptance criteria:** All checkout test files are committed. No skipped tests or debug-only code. The full suite passes.
