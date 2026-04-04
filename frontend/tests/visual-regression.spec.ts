import { test, expect } from '@playwright/test';

test.describe('Visual Regression & Screenshot Tests', () => {

    // ── Landing Page Snapshots ────────────────────────────────────────
    test('landing page visual snapshot - desktop', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto('/');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('landing-desktop.png', {
            fullPage: true,
            maxDiffPixelRatio: 0.05,
        });
    });

    test('landing page visual snapshot - mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 812 });
        await page.goto('/');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('landing-mobile.png', {
            fullPage: true,
            maxDiffPixelRatio: 0.05,
        });
    });

    // ── Dashboard Snapshots ───────────────────────────────────────────
    test('dashboard page visual snapshot', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('dashboard-desktop.png', {
            fullPage: true,
            maxDiffPixelRatio: 0.1,
        });
    });

    // ── Individual Module Snapshots ───────────────────────────────────
    test('runway page visual snapshot', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto('/runway');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('runway-desktop.png', {
            fullPage: true,
            maxDiffPixelRatio: 0.1,
        });
    });

    test('expenses page visual snapshot', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto('/expenses');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('expenses-desktop.png', {
            fullPage: true,
            maxDiffPixelRatio: 0.1,
        });
    });

    test('revenue page visual snapshot', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto('/revenue');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('revenue-desktop.png', {
            fullPage: true,
            maxDiffPixelRatio: 0.1,
        });
    });

    test('scenarios page visual snapshot', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto('/scenarios');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('scenarios-desktop.png', {
            fullPage: true,
            maxDiffPixelRatio: 0.1,
        });
    });

    test('tax page visual snapshot', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto('/tax');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('tax-desktop.png', {
            fullPage: true,
            maxDiffPixelRatio: 0.1,
        });
    });

    test('anomalies page visual snapshot', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto('/anomalies');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('anomalies-desktop.png', {
            fullPage: true,
            maxDiffPixelRatio: 0.1,
        });
    });

    test('benchmarking page visual snapshot', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto('/benchmarking');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('benchmarking-desktop.png', {
            fullPage: true,
            maxDiffPixelRatio: 0.1,
        });
    });

    test('settings page visual snapshot', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto('/settings');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('settings-desktop.png', {
            fullPage: true,
            maxDiffPixelRatio: 0.1,
        });
    });

    test('CEO dashboard visual snapshot', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto('/dashboard/ceo');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('ceo-dashboard.png', {
            fullPage: true,
            maxDiffPixelRatio: 0.1,
        });
    });

    test('CTO dashboard visual snapshot', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto('/dashboard/cto');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('cto-dashboard.png', {
            fullPage: true,
            maxDiffPixelRatio: 0.1,
        });
    });

    test('Finance dashboard visual snapshot', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto('/dashboard/finance');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('finance-dashboard.png', {
            fullPage: true,
            maxDiffPixelRatio: 0.1,
        });
    });
});
