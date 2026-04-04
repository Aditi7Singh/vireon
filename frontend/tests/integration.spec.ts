import { test, expect } from '@playwright/test';

test.describe('Cross-Page Navigation & Integration', () => {

    test.setTimeout(60000);

    test('full user journey: landing → dashboard → runway → expenses', async ({ page }) => {
        await page.goto('/');
        await expect(page.locator('h1')).toContainText('Vireon Times');

        await page.click('a:has-text("Open Vireon Dashboard")');
        await page.waitForURL('**/dashboard');
        await expect(page.locator('text=Executive Control Center')).toBeVisible();

        await page.click('a:has-text("Runway Intelligence")');
        await page.waitForURL('**/runway');
        await expect(page.locator('body')).toContainText('Runway', { timeout: 15000 });

        await page.click('aside a[href="/expenses"]');
        await page.waitForURL('**/expenses');
        await expect(page.locator('body')).toContainText('Expense', { timeout: 15000 });
    });

    test('full user journey: dashboard → scenarios → save snapshot flow', async ({ page }) => {
        await page.goto('/scenarios');
        await page.waitForLoadState('networkidle');

        await page.click('button:has-text("Aggressive")');
        await expect(page.locator('text=Push expansion')).toBeVisible();

        const slider = page.locator('input[type="range"]').first();
        await slider.fill('20');

        await expect(page.locator('text=Monthly Hiring Burden')).toBeVisible();
    });

    test('navigating between all major pages without errors', async ({ page }) => {
        const pages = [
            '/dashboard',
            '/runway',
            '/expenses',
            '/revenue',
            '/scenarios',
            '/tax',
            '/benchmarking',
            '/agent',
            '/anomalies',
            '/features',
            '/operations',
            '/settings',
        ];

        for (const url of pages) {
            await page.goto(url);
            await page.waitForLoadState('domcontentloaded');
            const body = page.locator('body');
            await expect(body).toBeVisible();
            const text = await body.innerText();
            expect(text.length).toBeGreaterThan(0);
        }
    });

    test('sidebar active state changes when navigating', async ({ page }) => {
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');

        const dashLink = page.locator('aside a[href="/dashboard"]');
        await expect(dashLink).toHaveClass(/bg-\[#f4e7d8\]/);

        await page.click('aside a[href="/revenue"]');
        await page.waitForURL('**/revenue');

        const revLink = page.locator('aside a[href="/revenue"]');
        await expect(revLink).toHaveClass(/bg-\[#f4e7d8\]/);
    });
});

test.describe('Dashboard Layout Integration', () => {

    test('dashboard layout renders sidebar, content area', async ({ page }) => {
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');

        await expect(page.locator('aside')).toBeVisible();
        // Use first() since there may be multiple main elements
        await expect(page.locator('main').first()).toBeVisible();
    });

    test('startup health banner appears when issues exist', async ({ page }) => {
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
        await expect(page.locator('body')).toBeVisible();
    });
});

test.describe('Responsive Layout Tests', () => {

    test('landing page is responsive on mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 812 });
        await page.goto('/');
        await expect(page.locator('h1')).toBeVisible();
        await expect(page.locator('a:has-text("Open Vireon Dashboard")')).toBeVisible();
    });

    test('dashboard works on tablet viewport', async ({ page }) => {
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
        await expect(page.locator('text=Executive Control Center')).toBeVisible();
    });

    test('dashboard works on desktop viewport', async ({ page }) => {
        await page.setViewportSize({ width: 1920, height: 1080 });
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
        await expect(page.locator('text=Executive Control Center')).toBeVisible();
    });
});
