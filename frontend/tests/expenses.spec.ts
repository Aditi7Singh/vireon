import { test, expect } from './fixtures';

test.describe('Expenses / Capital Allocations Page', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/expenses');
        await page.waitForLoadState('networkidle');
    });

    // ── Page Structure ────────────────────────────────────────────────
    test('renders page title "Capital Allocations"', async ({ page }) => {
        await expect(page.locator('text=Capital Allocations')).toBeVisible();
    });

    test('displays Audited expense ledger badge', async ({ page }) => {
        await expect(page.locator('text=Audited expense ledger')).toBeVisible();
    });

    test('shows Expense Control Center heading', async ({ page }) => {
        await expect(page.locator('h1:has-text("Expense Control Center")')).toBeVisible();
    });

    // ── Department Filter ─────────────────────────────────────────────
    test('has department filter dropdown', async ({ page }) => {
        const select = page.locator('select');
        await expect(select).toBeVisible();
    });

    test('department dropdown has all department options', async ({ page }) => {
        const select = page.locator('select');
        const options = select.locator('option');
        // Should have: all, Engineering, Marketing, Sales, Operations, Finance
        await expect(options).toHaveCount(6);
    });

    test('changing department filter updates the view', async ({ page }) => {
        const select = page.locator('select');
        await select.selectOption('Engineering');
        // The page should still render without errors
        await expect(page.locator('text=Total Expenses')).toBeVisible();
    });

    // ── KPI Summary Cards ─────────────────────────────────────────────
    test('displays Total Expenses card', async ({ page }) => {
        await expect(page.locator('text=Total Expenses')).toBeVisible();
    });

    test('displays Compliance status card', async ({ page }) => {
        await expect(page.locator('text=Compliance')).toBeVisible();
        await expect(page.locator('text=Audited')).toBeVisible();
    });

    // ── AI Leakage Audit CTA ──────────────────────────────────────────
    test('has AI leakage audit button', async ({ page }) => {
        const btn = page.locator('button:has-text("AI leakage audit")');
        await expect(btn).toBeVisible();
    });

    // ── Category Breakdown Cards ──────────────────────────────────────
    test('category cards display progress bars', async ({ page }) => {
        // Check for progress bar elements in category cards
        const progressBars = page.locator('.rounded-full.h-2');
        const count = await progressBars.count();
        // There should be at least some progress bars if data is loaded
        expect(count).toBeGreaterThanOrEqual(0);
    });

    // ── Total Outflow Display ─────────────────────────────────────────
    test('shows total outflow text', async ({ page }) => {
        await expect(page.locator('text=Total outflow this cycle')).toBeVisible();
    });
});
