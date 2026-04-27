import { test, expect } from './fixtures';

test.describe('Benchmarking / Performance Intelligence Page', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/benchmarking');
        await page.waitForLoadState('networkidle');
        // Wait for benchmarks to load (page has a loading state)
        await page.waitForTimeout(3000);
    });

    // ── Page Structure ────────────────────────────────────────────────
    test('renders Operational Benchmarking heading', async ({ page }) => {
        await expect(page.locator('h1:has-text("Operational Benchmarking")')).toBeVisible({ timeout: 15000 });
    });

    test('shows Live benchmark feed badge', async ({ page }) => {
        await expect(page.locator('text=Live benchmark feed')).toBeVisible({ timeout: 15000 });
    });

    test('has Consult AI advisor button', async ({ page }) => {
        await expect(page.locator('button:has-text("Consult AI advisor")')).toBeVisible({ timeout: 15000 });
    });

    // ── Benchmark Metric Cards ────────────────────────────────────────
    test('displays benchmark metric cards', async ({ page }) => {
        // Benchmarks always render (even with fallback data)
        const cards = page.locator('article');
        const count = await cards.count();
        expect(count).toBeGreaterThanOrEqual(3);
    });

    test('shows Rule of 40 metric', async ({ page }) => {
        await expect(page.locator('text=Rule of 40')).toBeVisible();
    });

    test('shows Burn Multiple metric', async ({ page }) => {
        await expect(page.locator('p:has-text("Burn Multiple")')).toBeVisible();
    });

    test('shows Net Revenue Retention metric', async ({ page }) => {
        await expect(page.locator('text=Net Revenue Retention')).toBeVisible();
    });

    test('each metric card has a Target label', async ({ page }) => {
        const targets = page.locator('span:has-text("Target:")');
        const count = await targets.count();
        expect(count).toBeGreaterThanOrEqual(3);
    });

    test('each metric card has a status badge', async ({ page }) => {
        // Status badges show the current status
        const cards = page.locator('article');
        const count = await cards.count();
        expect(count).toBeGreaterThanOrEqual(3);
        // Each card has a status span
        for (let i = 0; i < count; i++) {
            const badge = cards.nth(i).locator('span.font-bold.rounded-full');
            await expect(badge).toBeVisible();
        }
    });

    test('each metric card has Get advice button', async ({ page }) => {
        const adviceButtons = page.locator('button:has-text("Get advice")');
        const count = await adviceButtons.count();
        expect(count).toBeGreaterThanOrEqual(3);
    });

    test('metric cards have description text', async ({ page }) => {
        await expect(page.locator('text=Growth Rate + Profit Margin')).toBeVisible();
        await expect(page.locator('text=Efficiency of burning capital')).toBeVisible();
    });
});
