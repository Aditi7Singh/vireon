import { test, expect } from './fixtures';

test.describe('Feature Hub / Action Hub Page', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/features');
        await page.waitForLoadState('networkidle');
    });

    // ── Page Structure ────────────────────────────────────────────────
    test('renders Action Hub heading', async ({ page }) => {
        await expect(page.locator('text=Action Hub').first()).toBeVisible();
    });

    test('displays "Operate The Smart CFO Features" heading', async ({ page }) => {
        await expect(page.locator('h1:has-text("Operate The Smart CFO Features")')).toBeVisible();
    });

    test('has Refresh button', async ({ page }) => {
        const refreshBtn = page.locator('button:has-text("Refresh")');
        await expect(refreshBtn).toBeVisible();
    });

    // ── Platform Health Section ───────────────────────────────────────
    test('renders Platform Health section', async ({ page }) => {
        await expect(page.locator('text=Platform Health')).toBeVisible();
    });

    test('shows health status badge (Healthy or Attention needed)', async ({ page }) => {
        const badge = page.locator('text=/Healthy|Attention needed/');
        await expect(badge).toBeVisible();
    });

    test('displays Default Company info', async ({ page }) => {
        await expect(page.locator('text=Default Company')).toBeVisible();
    });

    test('displays Issues count', async ({ page }) => {
        await expect(page.locator('text=Issues')).toBeVisible();
    });

    test('displays Actionable Fixes count', async ({ page }) => {
        await expect(page.locator('text=Actionable Fixes')).toBeVisible();
    });

    test('displays Missing Credentials count', async ({ page }) => {
        await expect(page.locator('text=Missing Credentials')).toBeVisible();
    });

    // ── Anomaly Operations ────────────────────────────────────────────
    test('renders Anomaly Operations section', async ({ page }) => {
        await expect(page.locator('text=Anomaly Operations')).toBeVisible();
    });

    test('has Seed demo anomalies button', async ({ page }) => {
        const btn = page.locator('button:has-text("Seed demo anomalies")');
        await expect(btn).toBeVisible();
    });

    test('has Run anomaly scan button', async ({ page }) => {
        const btn = page.locator('button:has-text("Run anomaly scan")');
        await expect(btn).toBeVisible();
    });

    test('has Open anomalies link', async ({ page }) => {
        const link = page.locator('a:has-text("Open anomalies")');
        await expect(link).toBeVisible();
        await expect(link).toHaveAttribute('href', '/anomalies');
    });

    // ── Tax Operations ────────────────────────────────────────────────
    test('renders Tax Operations section', async ({ page }) => {
        await expect(page.locator('text=Tax Operations')).toBeVisible();
    });

    test('has Generate quarterly liability button', async ({ page }) => {
        const btn = page.locator('button:has-text("Generate quarterly liability")');
        await expect(btn).toBeVisible();
    });

    test('has Open tax page link', async ({ page }) => {
        const link = page.locator('a:has-text("Open tax page")');
        await expect(link).toBeVisible();
        await expect(link).toHaveAttribute('href', '/tax');
    });

    // ── AI Stack Cost Capture ─────────────────────────────────────────
    test('renders AI Stack Cost Capture section', async ({ page }) => {
        await expect(page.locator('text=AI Stack Cost Capture')).toBeVisible();
    });

    test('has Claude monthly cost input field', async ({ page }) => {
        await expect(page.locator('text=Claude monthly cost')).toBeVisible();
    });

    test('has Product allocation dropdown', async ({ page }) => {
        await expect(page.locator('text=Product allocation')).toBeVisible();
        const select = page.locator('select').filter({ hasText: /AI Lab|Shared|Orchard|Sprouts/ });
        await expect(select).toBeVisible();
    });

    test('has Capture Claude subscription button', async ({ page }) => {
        const btn = page.locator('button:has-text("Capture Claude subscription")');
        await expect(btn).toBeVisible();
    });

    // ── Hiring Impact Calculator ──────────────────────────────────────
    test('renders Hiring Impact Calculator section', async ({ page }) => {
        await expect(page.locator('text=Hiring Impact Calculator')).toBeVisible();
    });

    test('has Annual CTC input', async ({ page }) => {
        await expect(page.locator('text=Annual CTC')).toBeVisible();
    });

    test('has Join month input', async ({ page }) => {
        await expect(page.locator('text=Join month')).toBeVisible();
    });

    test('has Calculate impact button', async ({ page }) => {
        const btn = page.locator('button:has-text("Calculate impact")');
        await expect(btn).toBeVisible();
    });

    test('has Open CTO planner link', async ({ page }) => {
        const link = page.locator('a:has-text("Open CTO planner")');
        await expect(link).toBeVisible();
    });

    // ── Smart CFO Agent Section ───────────────────────────────────────
    test('renders Smart CFO Agent section', async ({ page }) => {
        await expect(page.locator('text=Smart CFO Agent For Leadership')).toBeVisible();
    });

    test('has CEO risk brief button', async ({ page }) => {
        const btn = page.locator('button:has-text("CEO risk brief")');
        await expect(btn).toBeVisible();
    });

    test('has Board narrative button', async ({ page }) => {
        const btn = page.locator('button:has-text("Board narrative")');
        await expect(btn).toBeVisible();
    });

    test('has Hiring trade-off analysis button', async ({ page }) => {
        const btn = page.locator('button:has-text("Hiring trade-off analysis")');
        await expect(btn).toBeVisible();
    });

    test('has Cost-cutting plan button', async ({ page }) => {
        const btn = page.locator('button:has-text("Cost-cutting plan")');
        await expect(btn).toBeVisible();
    });

    test('has Leadership summary button', async ({ page }) => {
        const btn = page.locator('button:has-text("Leadership summary")');
        await expect(btn).toBeVisible();
    });

    test('has Run full leadership drill button', async ({ page }) => {
        const btn = page.locator('button:has-text("Run full leadership drill")');
        await expect(btn).toBeVisible();
    });

    test('has Open full AI agent link', async ({ page }) => {
        const link = page.locator('a:has-text("Open full AI agent")');
        await expect(link).toBeVisible();
        await expect(link).toHaveAttribute('href', '/agent');
    });
});
