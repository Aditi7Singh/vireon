import { test, expect } from '@playwright/test';

test.describe('Vireon E2E Tests', () => {
    test('Dashboard loads correctly', async ({ page }) => {
        // Navigate to the dashboard
        await page.goto('/');

        // Check if the title is correct (adjust based on actual app title)
        // await expect(page).toHaveTitle(/Vireon|SeedlingLabs/i);

        // Check if the main heading is visible or a specific text exists
        // This is a generic check, adjust the text "Vireon" or "Dashboard" to match your UI
        await expect(page.locator('body')).toBeVisible();

        // We expect the app to render some content and not be empty
        const bodyText = await page.locator('body').innerText();
        expect(bodyText.length).toBeGreaterThan(0);
    });
});
