import { test, expect } from './fixtures';

test.describe('CEO Dashboard Page', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/dashboard/ceo');
        await page.waitForLoadState('networkidle');
    });

    // ── Page Structure ────────────────────────────────────────────────
    test('renders CEO Dashboard heading', async ({ page }) => {
        await expect(page.locator('h1:has-text("CEO Dashboard")')).toBeVisible();
    });

    test('shows financial health subtitle with month', async ({ page }) => {
        await expect(page.locator('text=Financial health')).toBeVisible();
    });

    // ── Month Selector ────────────────────────────────────────────────
    test('has month selector input', async ({ page }) => {
        const monthInput = page.locator('input[type="month"]');
        await expect(monthInput).toBeVisible();
    });

    test('month selector has a value', async ({ page }) => {
        const monthInput = page.locator('input[type="month"]');
        const currentValue = await monthInput.inputValue();
        expect(currentValue.length).toBeGreaterThan(0);
    });

    // ── Export Buttons ────────────────────────────────────────────────
    test('has CSV export button', async ({ page }) => {
        const csvBtn = page.locator('button:has-text("CSV")');
        await expect(csvBtn).toBeVisible();
    });

    test('has PDF export button', async ({ page }) => {
        const pdfBtn = page.locator('button:has-text("PDF")');
        await expect(pdfBtn).toBeVisible();
    });

    // ── KPI Cards ─────────────────────────────────────────────────────
    test('displays Net Burn KPI card', async ({ page }) => {
        await expect(page.locator('p:has-text("Net Burn")').first()).toBeVisible();
    });

    test('displays Burn Multiple KPI card', async ({ page }) => {
        await expect(page.locator('p:has-text("Burn Multiple")').first()).toBeVisible();
    });

    test('displays Cash Balance KPI card', async ({ page }) => {
        await expect(page.locator('p:has-text("Cash Balance")')).toBeVisible();
    });

    test('displays Headcount KPI card', async ({ page }) => {
        // Use specific selector since "Headcount" appears in multiple places
        await expect(page.locator('p.text-xs:has-text("Headcount")').first()).toBeVisible();
    });

    test('displays GM Avg KPI card', async ({ page }) => {
        await expect(page.locator('text=GM Avg')).toBeVisible();
    });

    test('Burn Multiple shows industry target reference', async ({ page }) => {
        await expect(page.locator('text=Target: 1.5x')).toBeVisible();
    });

    test('Net Burn shows month-over-month change', async ({ page }) => {
        await expect(page.locator('text=vs last month')).toBeVisible();
    });

    // ── Charts ────────────────────────────────────────────────────────
    test('renders 6-Month Burn & Cash Trajectory chart', async ({ page }) => {
        await expect(page.locator('text=6-Month Burn & Cash Trajectory')).toBeVisible();
    });

    test('renders Cost Breakdown chart', async ({ page }) => {
        await expect(page.locator('text=Cost Breakdown')).toBeVisible();
    });

    // ── Financial Health Section ──────────────────────────────────────
    test('renders Top Cost Drivers section', async ({ page }) => {
        await expect(page.locator('text=Top Cost Drivers')).toBeVisible();
    });

    test('renders Key Metrics & Ratios section', async ({ page }) => {
        await expect(page.locator('text=Key Metrics & Ratios')).toBeVisible();
    });

    test('shows Revenue per Employee metric', async ({ page }) => {
        await expect(page.locator('text=Revenue per Employee')).toBeVisible();
    });

    test('shows Avg Cost per Employee metric', async ({ page }) => {
        await expect(page.locator('text=Avg Cost per Employee')).toBeVisible();
    });

    test('shows Headcount Ratio metric', async ({ page }) => {
        await expect(page.locator('span:has-text("Headcount Ratio")')).toBeVisible();
    });

    test('shows Cash Position metric', async ({ page }) => {
        await expect(page.locator('span:has-text("Cash Position")')).toBeVisible();
    });

    // ── Product Performance Table ─────────────────────────────────────
    test('renders Product Performance & Profitability table', async ({ page }) => {
        await expect(page.locator('text=Product Performance & Profitability')).toBeVisible();
    });

    test('product table has correct headers', async ({ page }) => {
        const headers = ['Product', 'Revenue', 'Cost', 'Gross Margin', 'Margin %', 'Status'];
        for (const header of headers) {
            await expect(page.locator(`th:has-text("${header}")`)).toBeVisible();
        }
    });

    // ── AI Recommendations ────────────────────────────────────────────
    test('renders AI-Powered Recommendations section', async ({ page }) => {
        await expect(page.locator('text=AI-Powered Recommendations')).toBeVisible();
    });

    // ── Responsive Layout ─────────────────────────────────────────────
    test('CEO dashboard renders on mobile viewport', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 812 });
        await expect(page.locator('h1:has-text("CEO Dashboard")')).toBeVisible();
    });
});
