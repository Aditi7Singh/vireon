import { test, expect } from '@playwright/test';

test.describe('Responsive Layout Tests - All Pages', () => {

    const viewports = [
        { name: 'mobile', width: 375, height: 812 },
        { name: 'tablet', width: 768, height: 1024 },
        { name: 'desktop', width: 1440, height: 900 },
        { name: 'fullhd', width: 1920, height: 1080 },
    ];

    // Pages that don't depend on backend API for initial render
    const stablePages = [
        { name: 'Landing', url: '/', contentCheck: 'Vireon Times' },
        { name: 'Dashboard', url: '/dashboard', contentCheck: 'Executive Control Center' },
        { name: 'Features Hub', url: '/features', contentCheck: 'Action Hub' },
        { name: 'Operations', url: '/operations', contentCheck: 'Operations Center' },
        { name: 'Settings', url: '/settings', contentCheck: 'Settings' },
        { name: 'Tax', url: '/tax', contentCheck: 'Tax Compliance Hub' },
    ];

    // Pages that may show loading state when backend is unavailable
    const apiDependentPages = [
        { name: 'CEO Dashboard', url: '/dashboard/ceo', contentCheck: 'CEO Dashboard' },
        { name: 'CTO Dashboard', url: '/dashboard/cto', contentCheck: 'CTO Dashboard' },
        { name: 'Finance Dashboard', url: '/dashboard/finance', contentCheck: 'Finance Control' },
        { name: 'Runway', url: '/runway', contentCheck: 'Runway' },
        { name: 'Expenses', url: '/expenses', contentCheck: 'Expense' },
        { name: 'Revenue', url: '/revenue', contentCheck: 'Revenue' },
        { name: 'Scenarios', url: '/scenarios', contentCheck: 'Scenario' },
        { name: 'Anomalies', url: '/anomalies', contentCheck: 'Risk' },
        { name: 'Benchmarking', url: '/benchmarking', contentCheck: 'benchmark' },
        { name: 'AI Agent', url: '/agent', contentCheck: 'intelligence' },
    ];

    // ── Test stable pages at all viewports ────────────────────────────
    for (const vp of viewports) {
        for (const p of stablePages) {
            test(`${p.name} renders at ${vp.name} (${vp.width}x${vp.height})`, async ({ page }) => {
                await page.setViewportSize({ width: vp.width, height: vp.height });
                await page.goto(p.url);
                await page.waitForLoadState('domcontentloaded');
                await expect(page.locator(`text=${p.contentCheck}`).first()).toBeVisible({ timeout: 15000 });
            });
        }
    }

    // ── Test API-dependent pages at desktop viewport only ─────────────
    for (const p of apiDependentPages) {
        test(`${p.name} renders at desktop (1440x900)`, async ({ page }) => {
            await page.setViewportSize({ width: 1440, height: 900 });
            await page.goto(p.url);
            await page.waitForLoadState('domcontentloaded');
            // Use case-insensitive regex match for flexibility
            await expect(page.locator('body')).toContainText(new RegExp(p.contentCheck, 'i'), { timeout: 20000 });
        });
    }

    // ── Sidebar Behavior at Different Viewports ───────────────────────
    test('sidebar is visible on desktop dashboard', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
        const sidebar = page.locator('aside');
        await expect(sidebar).toBeVisible();
    });

    test('sidebar is visible on tablet dashboard', async ({ page }) => {
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
        const sidebar = page.locator('aside');
        await expect(sidebar).toBeVisible();
    });

    // ── Charts Responsive Behavior ────────────────────────────────────
    test('recharts containers resize at different viewports', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
        const chart = page.locator('.recharts-responsive-container');
        await expect(chart).toBeVisible();
        const desktopBox = await chart.boundingBox();

        await page.setViewportSize({ width: 375, height: 812 });
        await page.waitForTimeout(500);
        const mobileBox = await chart.boundingBox();

        if (desktopBox && mobileBox) {
            expect(mobileBox.width).toBeLessThanOrEqual(desktopBox.width);
        }
    });
});
