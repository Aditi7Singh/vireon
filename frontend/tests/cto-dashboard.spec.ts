import { test, expect } from '@playwright/test';

test.describe('CTO Dashboard Page', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/dashboard/cto');
        await page.waitForLoadState('networkidle');
    });

    // ── Page Structure ────────────────────────────────────────────────
    test('renders CTO Dashboard heading', async ({ page }) => {
        await expect(page.locator('text=CTO Dashboard')).toBeVisible();
    });

    // ── Export Buttons ────────────────────────────────────────────────
    test('has Export CSV button', async ({ page }) => {
        const csvBtn = page.locator('button:has-text("Export CSV")');
        await expect(csvBtn).toBeVisible();
    });

    test('has Export PDF button', async ({ page }) => {
        const pdfBtn = page.locator('button:has-text("Export PDF")');
        await expect(pdfBtn).toBeVisible();
    });

    // ── Tech Spend KPI Cards ──────────────────────────────────────────
    test('displays Total Tech Spend card', async ({ page }) => {
        await expect(page.locator('text=Total Tech Spend')).toBeVisible();
    });

    test('displays AWS Cost card', async ({ page }) => {
        // Use first() to avoid strict mode when "AWS Cost" appears in both KPI and breakdown
        await expect(page.locator('text=AWS Cost').first()).toBeVisible();
    });

    test('displays Software Licenses card', async ({ page }) => {
        await expect(page.locator('text=Software Licenses')).toBeVisible();
    });

    test('displays Tech % of Burn card', async ({ page }) => {
        await expect(page.locator('text=Tech % of Burn')).toBeVisible();
    });

    // ── Tech Cost Trend Chart ─────────────────────────────────────────
    test('renders Tech Cost Trend chart section', async ({ page }) => {
        await expect(page.locator('text=Tech Cost Trend')).toBeVisible();
    });

    test('tech cost trend shows Last 6 months label', async ({ page }) => {
        await expect(page.locator('text=Last 6 months')).toBeVisible();
    });

    test('tech cost trend chart has recharts container', async ({ page }) => {
        const chart = page.locator('.recharts-responsive-container');
        await expect(chart).toBeVisible();
    });

    // ── AWS Cost Breakdown ────────────────────────────────────────────
    test('renders AWS Cost Breakdown by Product section', async ({ page }) => {
        await expect(page.locator('text=AWS Cost Breakdown by Product')).toBeVisible();
    });

    test('AWS breakdown shows data or empty state', async ({ page }) => {
        const hasData = await page.locator('text=Total AWS Cost').isVisible().catch(() => false);
        const hasEmpty = await page.locator('text=No AWS cost data available').isVisible().catch(() => false);
        expect(hasData || hasEmpty).toBeTruthy();
    });

    // ── Quick Entry - Tech Cost Form ──────────────────────────────────
    test('renders Quick Entry - Tech Cost section', async ({ page }) => {
        await expect(page.locator('text=Quick Entry - Tech Cost')).toBeVisible();
    });

    test('has cost type dropdown with options', async ({ page }) => {
        const select = page.locator('select').first();
        await expect(select).toBeVisible();
        const options = select.locator('option');
        await expect(options).toHaveCount(5);
    });

    test('has vendor name input field', async ({ page }) => {
        const vendorInput = page.locator('input[placeholder*="Vendor"]');
        await expect(vendorInput).toBeVisible();
    });

    test('has amount input field', async ({ page }) => {
        const amountInput = page.locator('input[placeholder="Amount INR"]');
        await expect(amountInput).toBeVisible();
    });

    test('has description input field', async ({ page }) => {
        const descInput = page.locator('input[placeholder="Description"]');
        await expect(descInput).toBeVisible();
    });

    test('has Submit Tech Cost button', async ({ page }) => {
        const submitBtn = page.locator('button:has-text("Submit Tech Cost")');
        await expect(submitBtn).toBeVisible();
    });

    test('can fill in tech cost form fields', async ({ page }) => {
        const select = page.locator('select').first();
        await select.selectOption('aws');

        const vendorInput = page.locator('input[placeholder*="Vendor"]');
        await vendorInput.fill('Amazon Web Services');

        const amountInput = page.locator('input[placeholder="Amount INR"]');
        await amountInput.fill('50000');

        const descInput = page.locator('input[placeholder="Description"]');
        await descInput.fill('EC2 instances for ML training');

        await expect(select).toHaveValue('aws');
        await expect(vendorInput).toHaveValue('Amazon Web Services');
        await expect(amountInput).toHaveValue('50000');
        await expect(descInput).toHaveValue('EC2 instances for ML training');
    });

    // ── Recent Entries Table ──────────────────────────────────────────
    test('renders Recent Entries table header', async ({ page }) => {
        await expect(page.locator('th:has-text("Recent Entries")')).toBeVisible();
    });

    test('recent entries table has Amount column', async ({ page }) => {
        await expect(page.locator('th:has-text("Amount")')).toBeVisible();
    });

    // ── Hiring Impact Calculator ──────────────────────────────────────
    test('renders Hiring Impact Calculator section', async ({ page }) => {
        await expect(page.locator('text=Hiring Impact Calculator')).toBeVisible();
    });

    test('shows hiring impact description', async ({ page }) => {
        await expect(page.locator('text=Estimate runway impact of adding a new hire')).toBeVisible();
    });

    test('has Annual CTC label', async ({ page }) => {
        await expect(page.locator('text=Annual CTC')).toBeVisible();
    });

    test('has Calculate Impact button', async ({ page }) => {
        const calcBtn = page.locator('button:has-text("Calculate Impact")');
        await expect(calcBtn).toBeVisible();
    });

    test('CTC input has default value', async ({ page }) => {
        const ctcInput = page.locator('input[placeholder="e.g., 1200000"]');
        await expect(ctcInput).toHaveValue('1800000');
    });

    // ── Responsive Layout ─────────────────────────────────────────────
    test('CTO dashboard renders on mobile viewport', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 812 });
        await expect(page.locator('text=CTO Dashboard')).toBeVisible({ timeout: 10000 });
    });
});
