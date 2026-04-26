import { test, expect } from '@playwright/test';

test.describe('Tax Compliance Hub Page', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/tax');
        await page.waitForLoadState('networkidle');
    });

    // ── Page Structure ────────────────────────────────────────────────
    test('renders Tax Compliance Hub heading', async ({ page }) => {
        await expect(page.locator('h1:has-text("Tax Compliance Hub")')).toBeVisible();
    });

    test('shows current year in subtitle', async ({ page }) => {
        const currentYear = new Date().getFullYear().toString();
        await expect(page.locator(`text=Track GST, TDS, and compliance deadlines for ${currentYear}`)).toBeVisible();
    });

    test('has Refresh button', async ({ page }) => {
        const refreshBtn = page.locator('button:has-text("Refresh")');
        await expect(refreshBtn).toBeVisible();
    });

    // ── Tax Metadata Cards ────────────────────────────────────────────
    test('displays GST Status card', async ({ page }) => {
        await expect(page.locator('text=GST Status')).toBeVisible();
        await expect(page.locator('text=Registered')).toBeVisible();
    });

    test('displays TDS Filing card', async ({ page }) => {
        await expect(page.locator('text=TDS Filing')).toBeVisible();
        await expect(page.locator('text=Quarterly')).toBeVisible();
    });

    test('displays Quarter Filing card', async ({ page }) => {
        const currentQuarter = Math.floor(new Date().getMonth() / 3) + 1;
        await expect(page.locator(`text=Q${currentQuarter} Filing`)).toBeVisible();
    });

    test('displays Outstanding card', async ({ page }) => {
        await expect(page.locator('text=Outstanding')).toBeVisible();
    });

    // ── Current Quarter Liability ──────────────────────────────────────
    test('renders Current Quarter Liability section', async ({ page }) => {
        await expect(page.locator('text=Current Quarter Liability')).toBeVisible();
    });

    test('shows GST Liability value', async ({ page }) => {
        await expect(page.locator('text=GST Liability')).toBeVisible();
    });

    test('shows TDS Payable value', async ({ page }) => {
        await expect(page.locator('text=TDS Payable')).toBeVisible();
    });

    test('shows Total Due value', async ({ page }) => {
        await expect(page.locator('text=Total Due')).toBeVisible();
    });

    // ── Tax Payment Schedule ──────────────────────────────────────────
    test('renders Tax Payment Schedule section', async ({ page }) => {
        await expect(page.locator('text=Tax Payment Schedule')).toBeVisible();
    });

    // ── Tax Filing Checklist ──────────────────────────────────────────
    test('renders Tax Filing Checklist section', async ({ page }) => {
        await expect(page.locator('text=Tax Filing Checklist')).toBeVisible();
    });

    test('checklist has 6 items', async ({ page }) => {
        const checklistItems = [
            'Collect all invoices and GST returns',
            'Reconcile AR payments received',
            'Calculate TDS liability',
            'Generate monthly tax summary report',
            'File GST return with tax authority',
            'Reconcile payments and update status',
        ];
        for (const item of checklistItems) {
            await expect(page.locator(`text=${item}`)).toBeVisible();
        }
    });

    test('checklist items have checkboxes', async ({ page }) => {
        const checkboxes = page.locator('input[type="checkbox"]');
        await expect(checkboxes).toHaveCount(6);
    });

    // ── Tax Reference Guide ───────────────────────────────────────────
    test('renders GST on Sales reference card', async ({ page }) => {
        await expect(page.locator('text=GST on Sales')).toBeVisible();
    });

    test('renders TDS on Salary & Vendors reference card', async ({ page }) => {
        await expect(page.locator('text=TDS on Salary & Vendors')).toBeVisible();
    });

    // ── Action Buttons ────────────────────────────────────────────────
    test('has Generate Quarterly Liability button', async ({ page }) => {
        const btn = page.locator('button:has-text("Generate Quarterly Liability")');
        await expect(btn).toBeVisible();
    });

    test('has Mark Payment as Received button', async ({ page }) => {
        const btn = page.locator('button:has-text("Mark Payment as Received")');
        await expect(btn).toBeVisible();
    });
});
