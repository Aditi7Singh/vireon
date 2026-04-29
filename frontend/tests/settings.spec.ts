import { test, expect } from './fixtures';

test.describe('Settings Page', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/settings');
        await page.waitForLoadState('networkidle');
    });

    // ── Page Structure ────────────────────────────────────────────────
    test('renders Settings page title', async ({ page }) => {
        await expect(page.locator('text=Settings')).toBeVisible();
    });

    test('displays Platform Settings heading', async ({ page }) => {
        await expect(page.locator('h1:has-text("Platform Settings")')).toBeVisible();
    });

    test('shows System configuration badge', async ({ page }) => {
        await expect(page.locator('text=System configuration')).toBeVisible();
    });

    test('has Refresh button', async ({ page }) => {
        const refreshBtn = page.locator('button:has-text("Refresh")');
        await expect(refreshBtn).toBeVisible();
    });

    // ── Startup Readiness Section ─────────────────────────────────────
    test('shows Startup Readiness section', async ({ page }) => {
        await expect(page.locator('text=Startup Readiness')).toBeVisible();
    });

    test('displays Status field', async ({ page }) => {
        await expect(page.locator('text=Status:')).toBeVisible();
    });

    test('displays Companies count', async ({ page }) => {
        await expect(page.locator('text=Companies:')).toBeVisible();
    });

    test('displays Ledger rows count', async ({ page }) => {
        await expect(page.locator('text=Ledger rows:')).toBeVisible();
    });

    test('displays Missing keys count', async ({ page }) => {
        await expect(page.locator('text=Missing keys:')).toBeVisible();
    });

    // ── Connector Conflict Policy ─────────────────────────────────────
    test('renders Connector Conflict Policy section', async ({ page }) => {
        await expect(page.locator('text=Connector Conflict Policy')).toBeVisible();
    });

    test('has merge, plaid, and cloud costs dropdowns', async ({ page }) => {
        const selects = page.locator('select');
        const count = await selects.count();
        expect(count).toBeGreaterThanOrEqual(3);
    });

    test('policy dropdowns have correct options', async ({ page }) => {
        const firstSelect = page.locator('select').first();
        const options = firstSelect.locator('option');
        await expect(options).toHaveCount(3); // source_of_truth, latest_timestamp_wins, manual_review
    });

    test('changing policy dropdown works', async ({ page }) => {
        const firstSelect = page.locator('select').first();
        await firstSelect.selectOption('manual_review');
        await expect(firstSelect).toHaveValue('manual_review');
    });

    test('has Save policy button', async ({ page }) => {
        const saveBtn = page.locator('button:has-text("Save policy")');
        await expect(saveBtn).toBeVisible();
    });

    // ── Team Access Section ───────────────────────────────────────────
    test('renders Team Access section', async ({ page }) => {
        await expect(page.locator('text=Team Access')).toBeVisible();
    });

    test('displays team members', async ({ page }) => {
        await expect(page.locator('text=VIREON AI')).toBeVisible();
        await expect(page.locator('text=Aditi Singh')).toBeVisible();
        await expect(page.locator('text=yagnasri')).toBeVisible();
    });

    test('shows team member roles', async ({ page }) => {
        await expect(page.locator('text=CFO')).toBeVisible();
        await expect(page.locator('text=Founder')).toBeVisible();
        await expect(page.locator('text=Finance Ops')).toBeVisible();
    });

    test('shows team member emails', async ({ page }) => {
        await expect(page.locator('text=ai@vireon.finance')).toBeVisible();
        await expect(page.locator('text=aditi@vireon.ai')).toBeVisible();
        await expect(page.locator('text=yagnasri@vireon.ai')).toBeVisible();
    });

    test('shows VIREON AI configured as CFO note', async ({ page }) => {
        await expect(page.locator('text=VIREON AI is configured as CFO')).toBeVisible();
    });
});
