# Checkout Flow E2E Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add end-to-end Playwright tests covering all 5 steps of the checkout flow (cart review, address, shipping method, payment, confirmation), including a strategy for the third-party payment iframe that cannot be automated directly.

**Architecture:** Tests are organized as a single Playwright test suite with one spec file per checkout step, plus shared fixtures and helpers. The payment step uses a mock intercept strategy: we stub the third-party iframe's network requests and simulate a successful payment response at the network level, bypassing the need to interact with the iframe DOM. A page object model (POM) encapsulates each checkout page's selectors and actions.

**Tech Stack:** Playwright (existing setup), TypeScript, Page Object Model pattern

---

## File Structure

| File | Responsibility |
|------|---------------|
| `e2e/fixtures/checkout.fixture.ts` | Shared test fixture that seeds a cart with products and provides authenticated page context |
| `e2e/pages/CartPage.ts` | Page object for cart review step — selectors, actions (update qty, remove item, proceed) |
| `e2e/pages/AddressPage.ts` | Page object for address step — fill form, select saved address, proceed |
| `e2e/pages/ShippingPage.ts` | Page object for shipping method step — select method, verify costs, proceed |
| `e2e/pages/PaymentPage.ts` | Page object for payment step — mock iframe interaction, verify total, proceed |
| `e2e/pages/ConfirmationPage.ts` | Page object for confirmation step — verify order number, summary |
| `e2e/helpers/payment-mock.ts` | Network-level mock for the third-party payment iframe (route interception) |
| `e2e/helpers/test-data.ts` | Test data constants: addresses, card tokens, product SKUs |
| `e2e/tests/checkout-cart.spec.ts` | Cart review E2E tests |
| `e2e/tests/checkout-address.spec.ts` | Address step E2E tests |
| `e2e/tests/checkout-shipping.spec.ts` | Shipping method E2E tests |
| `e2e/tests/checkout-payment.spec.ts` | Payment step E2E tests (with mocked iframe) |
| `e2e/tests/checkout-confirmation.spec.ts` | Confirmation step E2E tests |
| `e2e/tests/checkout-full-flow.spec.ts` | Happy-path test covering all 5 steps end-to-end |
| `playwright.config.ts` | Modify: add checkout project config if needed |

---

### Task 1: Create Test Data Constants and Shared Helpers

**Files:**
- Create: `e2e/helpers/test-data.ts`

- [ ] **Step 1: Create the test data file with address, product, and payment constants**

```typescript
// e2e/helpers/test-data.ts

export const TEST_PRODUCTS = {
  basic: { sku: "WIDGET-001", name: "Basic Widget", qty: 2 },
  premium: { sku: "WIDGET-PRO", name: "Premium Widget", qty: 1 },
} as const;

export const TEST_ADDRESS = {
  firstName: "Jane",
  lastName: "Tester",
  street: "123 Test Lane",
  city: "Testville",
  state: "CA",
  zip: "90210",
  country: "US",
  phone: "555-000-1234",
} as const;

export const TEST_ADDRESS_SECONDARY = {
  firstName: "John",
  lastName: "Backup",
  street: "456 QA Blvd",
  city: "Checktown",
  state: "NY",
  zip: "10001",
  country: "US",
  phone: "555-000-5678",
} as const;

export const PAYMENT_TOKEN = {
  /** Simulated successful tokenization response from the payment provider */
  nonce: "fake-valid-nonce-for-testing",
  lastFour: "4242",
  cardType: "visa",
} as const;

export const SHIPPING_METHODS = {
  standard: { label: "Standard Shipping", minDays: 5, maxDays: 7 },
  express: { label: "Express Shipping", minDays: 2, maxDays: 3 },
} as const;
```

- [ ] **Step 2: Verify the file compiles**

Run: `npx tsc --noEmit e2e/helpers/test-data.ts`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add e2e/helpers/test-data.ts
git commit -m "test: add checkout e2e test data constants"
```

---

### Task 2: Create Payment Iframe Mock Helper

**Files:**
- Create: `e2e/helpers/payment-mock.ts`

This is the critical piece that solves the third-party iframe problem. Instead of trying to interact with the iframe DOM (which Playwright cannot do for cross-origin third-party iframes), we intercept the network requests the iframe makes and return canned responses.

- [ ] **Step 1: Write the payment mock helper**

```typescript
// e2e/helpers/payment-mock.ts
import { Page, Route } from "@playwright/test";
import { PAYMENT_TOKEN } from "./test-data";

/**
 * Intercepts requests to the third-party payment provider's iframe and API.
 * This avoids needing to automate the iframe DOM directly.
 *
 * Strategy:
 * 1. Intercept the iframe HTML load and inject a minimal page that
 *    auto-posts a success message to the parent window.
 * 2. Intercept the tokenization API call and return a fake valid token.
 */
export async function mockPaymentProvider(page: Page): Promise<void> {
  // Intercept the iframe HTML — replace with a stub that auto-submits
  await page.route("**/payment-provider.example.com/iframe**", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/html",
      body: `
        <!DOCTYPE html>
        <html>
        <body>
          <script>
            // Simulate the payment provider posting a tokenization result
            // back to the parent window, matching the real provider's message format
            window.parent.postMessage({
              type: "payment-provider-token",
              token: "${PAYMENT_TOKEN.nonce}",
              lastFour: "${PAYMENT_TOKEN.lastFour}",
              cardType: "${PAYMENT_TOKEN.cardType}"
            }, "*");
          </script>
        </body>
        </html>
      `,
    });
  });

  // Intercept tokenization API calls from the parent page
  await page.route("**/payment-provider.example.com/api/tokenize**", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        nonce: PAYMENT_TOKEN.nonce,
        last_four: PAYMENT_TOKEN.lastFour,
        card_type: PAYMENT_TOKEN.cardType,
      }),
    });
  });
}

/**
 * Variant that simulates a payment provider failure (declined card).
 */
export async function mockPaymentProviderDeclined(page: Page): Promise<void> {
  await page.route("**/payment-provider.example.com/iframe**", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/html",
      body: `
        <!DOCTYPE html>
        <html>
        <body>
          <script>
            window.parent.postMessage({
              type: "payment-provider-error",
              error: "card_declined",
              message: "Your card was declined."
            }, "*");
          </script>
        </body>
        </html>
      `,
    });
  });

  await page.route("**/payment-provider.example.com/api/tokenize**", async (route: Route) => {
    await route.fulfill({
      status: 422,
      contentType: "application/json",
      body: JSON.stringify({
        success: false,
        error: "card_declined",
        message: "Your card was declined.",
      }),
    });
  });
}
```

- [ ] **Step 2: Verify the file compiles**

Run: `npx tsc --noEmit e2e/helpers/payment-mock.ts`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add e2e/helpers/payment-mock.ts
git commit -m "test: add payment provider network mock for checkout e2e"
```

---

### Task 3: Create Checkout Test Fixture

**Files:**
- Create: `e2e/fixtures/checkout.fixture.ts`

The fixture handles repetitive setup: seeding the cart with products so each test starts at a known state.

- [ ] **Step 1: Write the checkout fixture**

```typescript
// e2e/fixtures/checkout.fixture.ts
import { test as base, Page } from "@playwright/test";
import { TEST_PRODUCTS } from "../helpers/test-data";
import { mockPaymentProvider } from "../helpers/payment-mock";

type CheckoutFixtures = {
  /** A page with items already added to cart, ready to start checkout */
  checkoutPage: Page;
  /** A page with payment provider mocked, items in cart, ready for full flow */
  checkoutPageWithPaymentMock: Page;
};

export const test = base.extend<CheckoutFixtures>({
  checkoutPage: async ({ page }, use) => {
    // Seed cart via API to avoid slow UI interactions for setup
    await page.request.post("/api/cart", {
      data: {
        items: [
          { sku: TEST_PRODUCTS.basic.sku, quantity: TEST_PRODUCTS.basic.qty },
          { sku: TEST_PRODUCTS.premium.sku, quantity: TEST_PRODUCTS.premium.qty },
        ],
      },
    });

    await page.goto("/checkout");
    await use(page);
  },

  checkoutPageWithPaymentMock: async ({ page }, use) => {
    await mockPaymentProvider(page);

    await page.request.post("/api/cart", {
      data: {
        items: [
          { sku: TEST_PRODUCTS.basic.sku, quantity: TEST_PRODUCTS.basic.qty },
        ],
      },
    });

    await page.goto("/checkout");
    await use(page);
  },
});

export { expect } from "@playwright/test";
```

- [ ] **Step 2: Verify the file compiles**

Run: `npx tsc --noEmit e2e/fixtures/checkout.fixture.ts`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add e2e/fixtures/checkout.fixture.ts
git commit -m "test: add checkout Playwright fixture with cart seeding"
```

---

### Task 4: Create Page Objects for Each Checkout Step

**Files:**
- Create: `e2e/pages/CartPage.ts`
- Create: `e2e/pages/AddressPage.ts`
- Create: `e2e/pages/ShippingPage.ts`
- Create: `e2e/pages/PaymentPage.ts`
- Create: `e2e/pages/ConfirmationPage.ts`

All page objects follow the same pattern: locators as properties, user actions as methods, no assertions (assertions belong in tests).

- [ ] **Step 1: Write CartPage page object**

```typescript
// e2e/pages/CartPage.ts
import { Page, Locator } from "@playwright/test";

export class CartPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly cartItems: Locator;
  readonly subtotal: Locator;
  readonly proceedButton: Locator;
  readonly emptyCartMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { name: /cart/i });
    this.cartItems = page.getByTestId("cart-item");
    this.subtotal = page.getByTestId("cart-subtotal");
    this.proceedButton = page.getByRole("button", { name: /proceed to address/i });
    this.emptyCartMessage = page.getByText(/your cart is empty/i);
  }

  async updateQuantity(sku: string, quantity: number): Promise<void> {
    const item = this.page.getByTestId(`cart-item-${sku}`);
    await item.getByRole("spinbutton").fill(String(quantity));
    await item.getByRole("button", { name: /update/i }).click();
  }

  async removeItem(sku: string): Promise<void> {
    const item = this.page.getByTestId(`cart-item-${sku}`);
    await item.getByRole("button", { name: /remove/i }).click();
  }

  async proceedToAddress(): Promise<void> {
    await this.proceedButton.click();
  }
}
```

- [ ] **Step 2: Write AddressPage page object**

```typescript
// e2e/pages/AddressPage.ts
import { Page, Locator } from "@playwright/test";

type AddressData = {
  firstName: string;
  lastName: string;
  street: string;
  city: string;
  state: string;
  zip: string;
  country: string;
  phone: string;
};

export class AddressPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly firstNameInput: Locator;
  readonly lastNameInput: Locator;
  readonly streetInput: Locator;
  readonly cityInput: Locator;
  readonly stateSelect: Locator;
  readonly zipInput: Locator;
  readonly countrySelect: Locator;
  readonly phoneInput: Locator;
  readonly proceedButton: Locator;
  readonly backButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { name: /address/i });
    this.firstNameInput = page.getByLabel(/first name/i);
    this.lastNameInput = page.getByLabel(/last name/i);
    this.streetInput = page.getByLabel(/street|address line/i);
    this.cityInput = page.getByLabel(/city/i);
    this.stateSelect = page.getByLabel(/state|province/i);
    this.zipInput = page.getByLabel(/zip|postal/i);
    this.countrySelect = page.getByLabel(/country/i);
    this.phoneInput = page.getByLabel(/phone/i);
    this.proceedButton = page.getByRole("button", { name: /proceed to shipping/i });
    this.backButton = page.getByRole("button", { name: /back/i });
  }

  async fillAddress(address: AddressData): Promise<void> {
    await this.firstNameInput.fill(address.firstName);
    await this.lastNameInput.fill(address.lastName);
    await this.streetInput.fill(address.street);
    await this.cityInput.fill(address.city);
    await this.stateSelect.selectOption(address.state);
    await this.zipInput.fill(address.zip);
    await this.countrySelect.selectOption(address.country);
    await this.phoneInput.fill(address.phone);
  }

  async proceedToShipping(): Promise<void> {
    await this.proceedButton.click();
  }
}
```

- [ ] **Step 3: Write ShippingPage page object**

```typescript
// e2e/pages/ShippingPage.ts
import { Page, Locator } from "@playwright/test";

export class ShippingPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly shippingOptions: Locator;
  readonly selectedCost: Locator;
  readonly proceedButton: Locator;
  readonly backButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { name: /shipping/i });
    this.shippingOptions = page.getByRole("radio");
    this.selectedCost = page.getByTestId("shipping-cost");
    this.proceedButton = page.getByRole("button", { name: /proceed to payment/i });
    this.backButton = page.getByRole("button", { name: /back/i });
  }

  async selectShippingMethod(label: string): Promise<void> {
    await this.page.getByLabel(label).check();
  }

  async proceedToPayment(): Promise<void> {
    await this.proceedButton.click();
  }
}
```

- [ ] **Step 4: Write PaymentPage page object**

```typescript
// e2e/pages/PaymentPage.ts
import { Page, Locator } from "@playwright/test";

export class PaymentPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly orderTotal: Locator;
  readonly paymentFrame: Locator;
  readonly placeOrderButton: Locator;
  readonly errorMessage: Locator;
  readonly backButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { name: /payment/i });
    this.orderTotal = page.getByTestId("order-total");
    this.paymentFrame = page.locator("iframe[data-testid='payment-iframe']");
    this.placeOrderButton = page.getByRole("button", { name: /place order/i });
    this.errorMessage = page.getByTestId("payment-error");
    this.backButton = page.getByRole("button", { name: /back/i });
  }

  /**
   * Wait for the mocked payment provider to post its token message.
   * The mock auto-posts on iframe load, so we just need to wait for the
   * Place Order button to become enabled (indicating the app received the token).
   */
  async waitForPaymentReady(): Promise<void> {
    await this.placeOrderButton.waitFor({ state: "visible" });
    // Button should become enabled once token is received from mock
    await this.page.waitForFunction(
      () => {
        const btn = document.querySelector("[data-testid='place-order-btn']") as HTMLButtonElement | null;
        return btn !== null && !btn.disabled;
      },
      { timeout: 5000 }
    );
  }

  async placeOrder(): Promise<void> {
    await this.placeOrderButton.click();
  }
}
```

- [ ] **Step 5: Write ConfirmationPage page object**

```typescript
// e2e/pages/ConfirmationPage.ts
import { Page, Locator } from "@playwright/test";

export class ConfirmationPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly orderNumber: Locator;
  readonly orderSummaryItems: Locator;
  readonly shippingAddress: Locator;
  readonly orderTotal: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { name: /confirmation|thank you/i });
    this.orderNumber = page.getByTestId("order-number");
    this.orderSummaryItems = page.getByTestId("confirmation-item");
    this.shippingAddress = page.getByTestId("confirmation-address");
    this.orderTotal = page.getByTestId("confirmation-total");
  }

  async getOrderNumber(): Promise<string> {
    return (await this.orderNumber.textContent()) ?? "";
  }
}
```

- [ ] **Step 6: Verify all page objects compile**

Run: `npx tsc --noEmit e2e/pages/CartPage.ts e2e/pages/AddressPage.ts e2e/pages/ShippingPage.ts e2e/pages/PaymentPage.ts e2e/pages/ConfirmationPage.ts`
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add e2e/pages/
git commit -m "test: add page objects for all 5 checkout steps"
```

---

### Task 5: Write Cart Review Step Tests

**Files:**
- Create: `e2e/tests/checkout-cart.spec.ts`
- Test: `e2e/tests/checkout-cart.spec.ts`

- [ ] **Step 1: Write the cart review tests**

```typescript
// e2e/tests/checkout-cart.spec.ts
import { test, expect } from "../fixtures/checkout.fixture";
import { CartPage } from "../pages/CartPage";
import { TEST_PRODUCTS } from "../helpers/test-data";

test.describe("Checkout - Cart Review", () => {
  test("displays cart items with correct quantities", async ({ checkoutPage }) => {
    const cart = new CartPage(checkoutPage);

    await expect(cart.heading).toBeVisible();
    await expect(cart.cartItems).toHaveCount(2);
    await expect(cart.subtotal).toBeVisible();
    await expect(cart.subtotal).not.toHaveText("$0.00");
  });

  test("can update item quantity", async ({ checkoutPage }) => {
    const cart = new CartPage(checkoutPage);

    const initialSubtotal = await cart.subtotal.textContent();
    await cart.updateQuantity(TEST_PRODUCTS.basic.sku, 5);
    await expect(cart.subtotal).not.toHaveText(initialSubtotal!);
  });

  test("can remove an item from cart", async ({ checkoutPage }) => {
    const cart = new CartPage(checkoutPage);

    await cart.removeItem(TEST_PRODUCTS.basic.sku);
    await expect(cart.cartItems).toHaveCount(1);
  });

  test("proceed button advances to address step", async ({ checkoutPage }) => {
    const cart = new CartPage(checkoutPage);

    await cart.proceedToAddress();
    await expect(checkoutPage).toHaveURL(/\/checkout\/address/);
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail (no app running / no implementation)**

Run: `npx playwright test e2e/tests/checkout-cart.spec.ts --reporter=list`
Expected: FAIL (tests cannot reach the app or page elements do not exist yet)

- [ ] **Step 3: Commit**

```bash
git add e2e/tests/checkout-cart.spec.ts
git commit -m "test: add cart review e2e tests"
```

---

### Task 6: Write Address Step Tests

**Files:**
- Create: `e2e/tests/checkout-address.spec.ts`
- Test: `e2e/tests/checkout-address.spec.ts`

- [ ] **Step 1: Write the address step tests**

```typescript
// e2e/tests/checkout-address.spec.ts
import { test, expect } from "../fixtures/checkout.fixture";
import { CartPage } from "../pages/CartPage";
import { AddressPage } from "../pages/AddressPage";
import { TEST_ADDRESS } from "../helpers/test-data";

test.describe("Checkout - Address", () => {
  test.beforeEach(async ({ checkoutPage }) => {
    // Navigate past cart review to address step
    const cart = new CartPage(checkoutPage);
    await cart.proceedToAddress();
  });

  test("displays address form with required fields", async ({ checkoutPage }) => {
    const address = new AddressPage(checkoutPage);

    await expect(address.heading).toBeVisible();
    await expect(address.firstNameInput).toBeVisible();
    await expect(address.lastNameInput).toBeVisible();
    await expect(address.streetInput).toBeVisible();
    await expect(address.cityInput).toBeVisible();
    await expect(address.zipInput).toBeVisible();
  });

  test("validates required fields before proceeding", async ({ checkoutPage }) => {
    const address = new AddressPage(checkoutPage);

    // Try to proceed without filling in any fields
    await address.proceedToShipping();

    // Should still be on address page with validation errors
    await expect(checkoutPage).toHaveURL(/\/checkout\/address/);
    await expect(checkoutPage.getByText(/required/i)).toBeVisible();
  });

  test("can fill address and proceed to shipping", async ({ checkoutPage }) => {
    const address = new AddressPage(checkoutPage);

    await address.fillAddress(TEST_ADDRESS);
    await address.proceedToShipping();

    await expect(checkoutPage).toHaveURL(/\/checkout\/shipping/);
  });

  test("back button returns to cart review", async ({ checkoutPage }) => {
    const address = new AddressPage(checkoutPage);

    await address.backButton.click();
    await expect(checkoutPage).toHaveURL(/\/checkout/);
    await expect(checkoutPage).not.toHaveURL(/\/checkout\/address/);
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npx playwright test e2e/tests/checkout-address.spec.ts --reporter=list`
Expected: FAIL

- [ ] **Step 3: Commit**

```bash
git add e2e/tests/checkout-address.spec.ts
git commit -m "test: add address step e2e tests"
```

---

### Task 7: Write Shipping Method Step Tests

**Files:**
- Create: `e2e/tests/checkout-shipping.spec.ts`
- Test: `e2e/tests/checkout-shipping.spec.ts`

- [ ] **Step 1: Write the shipping method tests**

```typescript
// e2e/tests/checkout-shipping.spec.ts
import { test, expect } from "../fixtures/checkout.fixture";
import { CartPage } from "../pages/CartPage";
import { AddressPage } from "../pages/AddressPage";
import { ShippingPage } from "../pages/ShippingPage";
import { TEST_ADDRESS, SHIPPING_METHODS } from "../helpers/test-data";

test.describe("Checkout - Shipping Method", () => {
  test.beforeEach(async ({ checkoutPage }) => {
    const cart = new CartPage(checkoutPage);
    await cart.proceedToAddress();

    const address = new AddressPage(checkoutPage);
    await address.fillAddress(TEST_ADDRESS);
    await address.proceedToShipping();
  });

  test("displays available shipping options", async ({ checkoutPage }) => {
    const shipping = new ShippingPage(checkoutPage);

    await expect(shipping.heading).toBeVisible();
    await expect(shipping.shippingOptions).toHaveCount(2);
    await expect(
      checkoutPage.getByLabel(SHIPPING_METHODS.standard.label)
    ).toBeVisible();
    await expect(
      checkoutPage.getByLabel(SHIPPING_METHODS.express.label)
    ).toBeVisible();
  });

  test("selecting a method updates the displayed cost", async ({ checkoutPage }) => {
    const shipping = new ShippingPage(checkoutPage);

    await shipping.selectShippingMethod(SHIPPING_METHODS.express.label);
    await expect(shipping.selectedCost).toBeVisible();
    await expect(shipping.selectedCost).not.toHaveText("$0.00");
  });

  test("can proceed to payment after selecting a method", async ({ checkoutPage }) => {
    const shipping = new ShippingPage(checkoutPage);

    await shipping.selectShippingMethod(SHIPPING_METHODS.standard.label);
    await shipping.proceedToPayment();

    await expect(checkoutPage).toHaveURL(/\/checkout\/payment/);
  });

  test("back button returns to address step", async ({ checkoutPage }) => {
    const shipping = new ShippingPage(checkoutPage);

    await shipping.backButton.click();
    await expect(checkoutPage).toHaveURL(/\/checkout\/address/);
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npx playwright test e2e/tests/checkout-shipping.spec.ts --reporter=list`
Expected: FAIL

- [ ] **Step 3: Commit**

```bash
git add e2e/tests/checkout-shipping.spec.ts
git commit -m "test: add shipping method step e2e tests"
```

---

### Task 8: Write Payment Step Tests (with Mocked Iframe)

**Files:**
- Create: `e2e/tests/checkout-payment.spec.ts`
- Test: `e2e/tests/checkout-payment.spec.ts`

This is the most nuanced task. The third-party payment iframe cannot be automated directly, so all tests in this file rely on the mocked payment provider fixture.

- [ ] **Step 1: Write the payment step tests**

```typescript
// e2e/tests/checkout-payment.spec.ts
import { test, expect } from "../fixtures/checkout.fixture";
import { CartPage } from "../pages/CartPage";
import { AddressPage } from "../pages/AddressPage";
import { ShippingPage } from "../pages/ShippingPage";
import { PaymentPage } from "../pages/PaymentPage";
import { mockPaymentProviderDeclined } from "../helpers/payment-mock";
import { TEST_ADDRESS, SHIPPING_METHODS, PAYMENT_TOKEN } from "../helpers/test-data";

test.describe("Checkout - Payment", () => {
  test.beforeEach(async ({ checkoutPageWithPaymentMock: page }) => {
    // Navigate through cart -> address -> shipping to reach payment
    const cart = new CartPage(page);
    await cart.proceedToAddress();

    const address = new AddressPage(page);
    await address.fillAddress(TEST_ADDRESS);
    await address.proceedToShipping();

    const shipping = new ShippingPage(page);
    await shipping.selectShippingMethod(SHIPPING_METHODS.standard.label);
    await shipping.proceedToPayment();
  });

  test("displays payment page with order total", async ({ checkoutPageWithPaymentMock: page }) => {
    const payment = new PaymentPage(page);

    await expect(payment.heading).toBeVisible();
    await expect(payment.orderTotal).toBeVisible();
    await expect(payment.orderTotal).not.toHaveText("$0.00");
  });

  test("payment iframe loads (mocked) and enables place order", async ({
    checkoutPageWithPaymentMock: page,
  }) => {
    const payment = new PaymentPage(page);

    await payment.waitForPaymentReady();
    await expect(payment.placeOrderButton).toBeEnabled();
  });

  test("successful payment proceeds to confirmation", async ({
    checkoutPageWithPaymentMock: page,
  }) => {
    const payment = new PaymentPage(page);

    await payment.waitForPaymentReady();
    await payment.placeOrder();

    await expect(page).toHaveURL(/\/checkout\/confirmation/);
  });

  test("back button returns to shipping step", async ({
    checkoutPageWithPaymentMock: page,
  }) => {
    const payment = new PaymentPage(page);

    await payment.backButton.click();
    await expect(page).toHaveURL(/\/checkout\/shipping/);
  });
});

test.describe("Checkout - Payment Declined", () => {
  test("shows error message when payment is declined", async ({ page }) => {
    // Use the declined mock instead of the success mock
    await mockPaymentProviderDeclined(page);

    // Seed cart and navigate to payment
    await page.request.post("/api/cart", {
      data: { items: [{ sku: "WIDGET-001", quantity: 1 }] },
    });
    await page.goto("/checkout");

    const cart = new CartPage(page);
    await cart.proceedToAddress();

    const address = new AddressPage(page);
    await address.fillAddress(TEST_ADDRESS);
    await address.proceedToShipping();

    const shipping = new ShippingPage(page);
    await shipping.selectShippingMethod(SHIPPING_METHODS.standard.label);
    await shipping.proceedToPayment();

    const payment = new PaymentPage(page);
    await expect(payment.errorMessage).toBeVisible();
    await expect(payment.errorMessage).toContainText(/declined/i);
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npx playwright test e2e/tests/checkout-payment.spec.ts --reporter=list`
Expected: FAIL

- [ ] **Step 3: Commit**

```bash
git add e2e/tests/checkout-payment.spec.ts
git commit -m "test: add payment step e2e tests with mocked iframe"
```

---

### Task 9: Write Confirmation Step Tests

**Files:**
- Create: `e2e/tests/checkout-confirmation.spec.ts`
- Test: `e2e/tests/checkout-confirmation.spec.ts`

- [ ] **Step 1: Write the confirmation step tests**

```typescript
// e2e/tests/checkout-confirmation.spec.ts
import { test, expect } from "../fixtures/checkout.fixture";
import { CartPage } from "../pages/CartPage";
import { AddressPage } from "../pages/AddressPage";
import { ShippingPage } from "../pages/ShippingPage";
import { PaymentPage } from "../pages/PaymentPage";
import { ConfirmationPage } from "../pages/ConfirmationPage";
import { TEST_ADDRESS, TEST_PRODUCTS, SHIPPING_METHODS } from "../helpers/test-data";

test.describe("Checkout - Confirmation", () => {
  test.beforeEach(async ({ checkoutPageWithPaymentMock: page }) => {
    const cart = new CartPage(page);
    await cart.proceedToAddress();

    const address = new AddressPage(page);
    await address.fillAddress(TEST_ADDRESS);
    await address.proceedToShipping();

    const shipping = new ShippingPage(page);
    await shipping.selectShippingMethod(SHIPPING_METHODS.standard.label);
    await shipping.proceedToPayment();

    const payment = new PaymentPage(page);
    await payment.waitForPaymentReady();
    await payment.placeOrder();
  });

  test("displays order number", async ({ checkoutPageWithPaymentMock: page }) => {
    const confirmation = new ConfirmationPage(page);

    await expect(confirmation.heading).toBeVisible();
    const orderNumber = await confirmation.getOrderNumber();
    expect(orderNumber).toBeTruthy();
    expect(orderNumber.length).toBeGreaterThan(0);
  });

  test("displays correct order summary", async ({ checkoutPageWithPaymentMock: page }) => {
    const confirmation = new ConfirmationPage(page);

    await expect(confirmation.orderSummaryItems).toHaveCount(1); // fixture seeds 1 item
    await expect(confirmation.orderTotal).toBeVisible();
  });

  test("displays shipping address", async ({ checkoutPageWithPaymentMock: page }) => {
    const confirmation = new ConfirmationPage(page);

    await expect(confirmation.shippingAddress).toContainText(TEST_ADDRESS.street);
    await expect(confirmation.shippingAddress).toContainText(TEST_ADDRESS.city);
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npx playwright test e2e/tests/checkout-confirmation.spec.ts --reporter=list`
Expected: FAIL

- [ ] **Step 3: Commit**

```bash
git add e2e/tests/checkout-confirmation.spec.ts
git commit -m "test: add confirmation step e2e tests"
```

---

### Task 10: Write Full Happy-Path Flow Test

**Files:**
- Create: `e2e/tests/checkout-full-flow.spec.ts`
- Test: `e2e/tests/checkout-full-flow.spec.ts`

A single test that exercises every step end-to-end. This catches integration issues between steps that step-level tests miss.

- [ ] **Step 1: Write the full flow test**

```typescript
// e2e/tests/checkout-full-flow.spec.ts
import { test, expect } from "../fixtures/checkout.fixture";
import { CartPage } from "../pages/CartPage";
import { AddressPage } from "../pages/AddressPage";
import { ShippingPage } from "../pages/ShippingPage";
import { PaymentPage } from "../pages/PaymentPage";
import { ConfirmationPage } from "../pages/ConfirmationPage";
import { TEST_ADDRESS, SHIPPING_METHODS } from "../helpers/test-data";

test.describe("Checkout - Full Happy Path", () => {
  test("completes checkout from cart through confirmation", async ({
    checkoutPageWithPaymentMock: page,
  }) => {
    // Step 1: Cart Review
    const cart = new CartPage(page);
    await expect(cart.heading).toBeVisible();
    await expect(cart.cartItems).toHaveCount(1);
    await cart.proceedToAddress();

    // Step 2: Address
    const address = new AddressPage(page);
    await expect(address.heading).toBeVisible();
    await address.fillAddress(TEST_ADDRESS);
    await address.proceedToShipping();

    // Step 3: Shipping Method
    const shipping = new ShippingPage(page);
    await expect(shipping.heading).toBeVisible();
    await shipping.selectShippingMethod(SHIPPING_METHODS.standard.label);
    await shipping.proceedToPayment();

    // Step 4: Payment (mocked iframe)
    const payment = new PaymentPage(page);
    await expect(payment.heading).toBeVisible();
    await payment.waitForPaymentReady();
    await payment.placeOrder();

    // Step 5: Confirmation
    const confirmation = new ConfirmationPage(page);
    await expect(confirmation.heading).toBeVisible();
    const orderNumber = await confirmation.getOrderNumber();
    expect(orderNumber).toBeTruthy();
    await expect(confirmation.orderTotal).toBeVisible();
    await expect(confirmation.shippingAddress).toContainText(TEST_ADDRESS.street);
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npx playwright test e2e/tests/checkout-full-flow.spec.ts --reporter=list`
Expected: FAIL

- [ ] **Step 3: Commit**

```bash
git add e2e/tests/checkout-full-flow.spec.ts
git commit -m "test: add full checkout happy-path e2e test"
```

---

### Task 11: Update Playwright Config (if needed)

**Files:**
- Modify: `playwright.config.ts`

- [ ] **Step 1: Check existing playwright config**

Run: `cat playwright.config.ts`
Determine if `e2e/` directory is already included in `testDir` or `testMatch`.

- [ ] **Step 2: Add checkout test configuration if not already covered**

If `testDir` does not include `e2e/`, add a project entry:

```typescript
// Add to the projects array in playwright.config.ts:
{
  name: "checkout",
  testDir: "./e2e/tests",
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:3000",
  },
},
```

- [ ] **Step 3: Run all checkout tests together**

Run: `npx playwright test --project=checkout --reporter=list`
Expected: All tests are discovered (they will fail until the app exists, but Playwright should find and attempt to run them all)

- [ ] **Step 4: Commit**

```bash
git add playwright.config.ts
git commit -m "chore: add checkout e2e project to Playwright config"
```

---

## Key Design Decisions

### Payment Iframe Strategy

The third-party payment iframe cannot be automated directly because:
1. It is cross-origin, so Playwright cannot access its DOM
2. The provider likely has bot detection that would block automation

**Solution:** Network-level mocking via `page.route()`. We intercept:
- The iframe HTML request: replaced with a stub that auto-posts a `postMessage` token to the parent window
- The tokenization API: returns a canned success/failure response

This approach tests that our application correctly handles the payment provider's message protocol without needing to interact with the provider's UI. The mock lives in `e2e/helpers/payment-mock.ts` and has both success and declined variants.

### What This Does NOT Test

- The actual payment provider's UI and tokenization flow (requires manual QA or the provider's own sandbox)
- Browser-specific payment method integrations (Apple Pay, Google Pay)
- Real payment processing and settlement

These gaps should be covered by:
1. Manual QA in a staging environment with the provider's sandbox/test mode
2. Contract tests against the payment provider's documented API responses
