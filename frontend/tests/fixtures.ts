import { test as baseTest } from '@playwright/test';

export const test = baseTest.extend({
  page: async ({ page }, use) => {
    // Set test auth markers before any page script executes.
    await page.addInitScript(() => {
      (window as any).__PLAYWRIGHT_TESTING__ = true;
      localStorage.setItem('access_token', 'test_token_e2e_bypass');
      localStorage.setItem('auth_token', 'test_token_e2e_bypass');
    });
    await use(page);
  },
});

export { expect } from '@playwright/test';
