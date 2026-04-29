import { test, expect } from './fixtures';

test.describe('Revenue Intelligence Page', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/revenue');
        await page.waitForLoadState('networkidle');
    });

    // ── Page Structure ────────────────────────────────────────────────
    test('renders page title "Revenue Intelligence"', async ({ page }) => {
        await expect(page.locator('text=Revenue Intelligence')).toBeVisible();
    });

    test('displays Revenue performance badge', async ({ page }) => {
        await expect(page.locator('text=Revenue performance')).toBeVisible();
    });

    test('shows Growth and Retention heading', async ({ page }) => {
        await expect(page.locator('h1:has-text("Growth and Retention")')).toBeVisible();
    });

    test('shows description about MRR, ARR, NRR, and churn', async ({ page }) => {
        await expect(page.locator('text=Track MRR, ARR, NRR, and churn')).toBeVisible();
    });

    // ── Revenue KPI Cards ─────────────────────────────────────────────
    test('displays Current MRR card', async ({ page }) => {
        await expect(page.locator('text=Current MRR')).toBeVisible();
    });

    test('displays Projected ARR card', async ({ page }) => {
        await expect(page.locator('text=Projected ARR')).toBeVisible();
    });

    test('displays Net Retention card', async ({ page }) => {
        await expect(page.locator('text=Net Retention')).toBeVisible();
    });

    test('displays Churn card', async ({ page }) => {
        await expect(page.locator('text=Churn').first()).toBeVisible();
    });

    // ── MRR Momentum Chart ────────────────────────────────────────────
    test('renders MRR Momentum chart section', async ({ page }) => {
        await expect(page.locator('text=MRR Momentum')).toBeVisible();
    });

    test('MRR chart shows YoY growth badge', async ({ page }) => {
        await expect(page.locator('text=18.4% YoY')).toBeVisible();
    });

    test('MRR chart has recharts container', async ({ page }) => {
        const chart = page.locator('.recharts-responsive-container').first();
        await expect(chart).toBeVisible();
    });

    test('MRR chart shows Last 6 months label', async ({ page }) => {
        await expect(page.locator('text=Last 6 months')).toBeVisible();
    });

    // ── Revenue by Segment ────────────────────────────────────────────
    test('renders Revenue by Segment section', async ({ page }) => {
        await expect(page.locator('text=Revenue by Segment')).toBeVisible();
    });

    test('shows segment breakdown (Orchard, Vineyard, Others)', async ({ page }) => {
        await expect(page.locator('text=Orchard')).toBeVisible();
        await expect(page.locator('text=Vineyard')).toBeVisible();
        await expect(page.locator('text=Others')).toBeVisible();
    });

    test('segment percentages are displayed', async ({ page }) => {
        await expect(page.locator('text=65%')).toBeVisible();
        await expect(page.locator('text=25%')).toBeVisible();
        await expect(page.locator('text=10%')).toBeVisible();
    });

    test('shows Total Monthly value', async ({ page }) => {
        await expect(page.locator('text=Total Monthly')).toBeVisible();
        await expect(page.locator('text=$45,000')).toBeVisible();
    });

    // ── Retention & Churn Health ───────────────────────────────────────
    test('renders Retention & Churn Health section', async ({ page }) => {
        await expect(page.locator('text=Retention & Churn Health')).toBeVisible();
    });

    test('shows NRR value', async ({ page }) => {
        await expect(page.locator('text=/NRR:/')).toBeVisible();
    });

    test('shows Target > 110% label', async ({ page }) => {
        await expect(page.locator('text=/Target/')).toBeVisible();
    });

    // ── AI Strategy CTA ───────────────────────────────────────────────
    test('has Run strategy audit button', async ({ page }) => {
        const btn = page.locator('button:has-text("Run strategy audit")');
        await expect(btn).toBeVisible();
    });
});
