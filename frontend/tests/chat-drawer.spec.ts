import { test, expect } from './fixtures';

test.describe('Chat Drawer Component', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
    });

    test('chat drawer is hidden initially', async ({ page }) => {
        const drawer = page.locator('text=AI Financial Assistant');
        await expect(drawer).not.toBeVisible();
    });

    test('clicking AI-related button on dashboard opens chat drawer', async ({ page }) => {
        // Navigate to runway page which has a Forecast analysis button
        await page.goto('/runway');
        await page.waitForLoadState('networkidle');
        const btn = page.locator('button:has-text("Forecast analysis")');
        await btn.click();
        await expect(page.locator('text=AI Financial Assistant')).toBeVisible();
    });

    test('chat drawer has close button', async ({ page }) => {
        await page.goto('/runway');
        await page.waitForLoadState('networkidle');
        await page.click('button:has-text("Forecast analysis")');
        await expect(page.locator('text=AI Financial Assistant')).toBeVisible();
        // Close button (X icon)
        const closeBtn = page.locator('text=AI Financial Assistant').locator('..').locator('..').locator('button').last();
        await expect(closeBtn).toBeVisible();
    });

    test('chat drawer shows Smart Financial Manager subtitle', async ({ page }) => {
        await page.goto('/runway');
        await page.waitForLoadState('networkidle');
        await page.click('button:has-text("Forecast analysis")');
        await expect(page.locator('text=Smart Financial Manager')).toBeVisible();
    });

    test('chat drawer has message input area', async ({ page }) => {
        await page.goto('/runway');
        await page.waitForLoadState('networkidle');
        await page.click('button:has-text("Forecast analysis")');
        const input = page.locator('textarea[placeholder="Query financial state..."]');
        await expect(input).toBeVisible();
    });

    test('chat drawer shows quick prompt suggestions initially', async ({ page }) => {
        await page.goto('/runway');
        await page.waitForLoadState('networkidle');
        await page.click('button:has-text("Forecast analysis")');
        await expect(page.locator('text=Suggested Intelligence Queries')).toBeVisible();
    });

    test('chat drawer has send button', async ({ page }) => {
        await page.goto('/runway');
        await page.waitForLoadState('networkidle');
        await page.click('button:has-text("Forecast analysis")');
        const sendBtn = page.locator('button[type="submit"]');
        await expect(sendBtn).toBeVisible();
    });

    test('chat drawer shows Enter keyboard shortcut hint', async ({ page }) => {
        await page.goto('/runway');
        await page.waitForLoadState('networkidle');
        await page.click('button:has-text("Forecast analysis")');
        await expect(page.locator('text=Enter')).toBeVisible();
    });

    test('chat drawer shows powered by text', async ({ page }) => {
        await page.goto('/runway');
        await page.waitForLoadState('networkidle');
        await page.click('button:has-text("Forecast analysis")');
        await expect(page.locator('text=Powered by Agentic Intelligence')).toBeVisible();
    });
});
