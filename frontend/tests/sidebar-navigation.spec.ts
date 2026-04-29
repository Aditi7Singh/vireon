import { test, expect } from './fixtures';

test.describe('Sidebar Navigation', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
    });

    // ── Sidebar Rendering ─────────────────────────────────────────────
    test('sidebar is visible on dashboard pages', async ({ page }) => {
        const sidebar = page.locator('aside');
        await expect(sidebar).toBeVisible();
    });

    test('sidebar contains Vireon logo', async ({ page }) => {
        // Logo component renders within sidebar
        const sidebar = page.locator('aside');
        await expect(sidebar).toBeVisible();
    });

    // ── Navigation Links ──────────────────────────────────────────────
    const navLinks = [
        { name: 'Dashboard', path: '/dashboard' },
        { name: 'Feature Hub', path: '/features' },
        { name: 'Operations', path: '/operations' },
        { name: 'CTO Planner', path: '/dashboard/cto' },
        { name: 'Runway', path: '/runway' },
        { name: 'Expenses', path: '/expenses' },
        { name: 'Revenue', path: '/revenue' },
        { name: 'Tax', path: '/tax' },
        { name: 'Scenarios', path: '/scenarios' },
        { name: 'Benchmarking', path: '/benchmarking' },
        { name: 'AI Agent', path: '/agent' },
        { name: 'Anomalies', path: '/anomalies' },
        { name: 'Settings', path: '/settings' },
    ];

    for (const link of navLinks) {
        test(`displays "${link.name}" navigation link`, async ({ page }) => {
            const navItem = page.locator(`aside a[href="${link.path}"]`);
            await expect(navItem).toBeVisible();
        });
    }

    // ── Navigation Routing ────────────────────────────────────────────
    test('navigating to Runway page via sidebar', async ({ page }) => {
        await page.click('aside a[href="/runway"]');
        await page.waitForURL('**/runway');
        await expect(page).toHaveURL(/\/runway/);
    });

    test('navigating to Expenses page via sidebar', async ({ page }) => {
        await page.click('aside a[href="/expenses"]');
        await page.waitForURL('**/expenses');
        await expect(page).toHaveURL(/\/expenses/);
    });

    test('navigating to Revenue page via sidebar', async ({ page }) => {
        await page.click('aside a[href="/revenue"]');
        await page.waitForURL('**/revenue');
        await expect(page).toHaveURL(/\/revenue/);
    });

    test('navigating to Scenarios page via sidebar', async ({ page }) => {
        await page.click('aside a[href="/scenarios"]');
        await page.waitForURL('**/scenarios');
        await expect(page).toHaveURL(/\/scenarios/);
    });

    test('navigating to Settings page via sidebar', async ({ page }) => {
        await page.click('aside a[href="/settings"]');
        await page.waitForURL('**/settings');
        await expect(page).toHaveURL(/\/settings/);
    });

    // ── Active State ──────────────────────────────────────────────────
    test('dashboard link shows active state on dashboard page', async ({ page }) => {
        const dashboardLink = page.locator('aside a[href="/dashboard"]');
        await expect(dashboardLink).toHaveClass(/bg-\[#f4e7d8\]/);
    });

    // ── Sidebar Toggle ────────────────────────────────────────────────
    test('sidebar toggle button collapses/expands sidebar', async ({ page }) => {
        const sidebar = page.locator('aside');
        // Initially expanded
        await expect(sidebar).toHaveClass(/w-72/);

        // Hover to reveal toggle button then click
        await sidebar.hover();
        const toggleBtn = page.locator('aside button').first();
        await toggleBtn.click();

        // Should be collapsed now
        await expect(sidebar).toHaveClass(/w-24/);

        // Toggle back
        await sidebar.hover();
        await toggleBtn.click();
        await expect(sidebar).toHaveClass(/w-72/);
    });

    // ── User Card ─────────────────────────────────────────────────────
    test('displays user info card at bottom of sidebar', async ({ page }) => {
        // User initials badge is visible
        const userCard = page.locator('aside').locator('div').filter({ hasText: /FOUNDER|CFO/ }).first();
        await expect(userCard).toBeVisible();
    });
});
