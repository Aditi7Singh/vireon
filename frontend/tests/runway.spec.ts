import { test, expect } from '@playwright/test';

test.describe('Runway & Survival Page', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/runway');
        await page.waitForLoadState('networkidle');
    });

    // ── Page Structure ────────────────────────────────────────────────
    test('renders the page title "Runway & Survival"', async ({ page }) => {
        await expect(page.locator('text=Runway & Survival')).toBeVisible();
    });

    test('shows runway status badge (Critical/Watch/Healthy)', async ({ page }) => {
        const badge = page.locator('text=/runway profile/i');
        await expect(badge).toBeVisible();
    });

    test('displays runway months in header', async ({ page }) => {
        const heading = page.locator('h1');
        await expect(heading).toContainText('months of runway');
    });

    test('shows current cash and monthly burn info', async ({ page }) => {
        await expect(page.locator('text=Current cash')).toBeVisible();
    });

    // ── Forecast Analysis CTA ─────────────────────────────────────────
    test('has Forecast analysis button', async ({ page }) => {
        const btn = page.locator('button:has-text("Forecast analysis")');
        await expect(btn).toBeVisible();
    });

    // ── Scenario Planner ──────────────────────────────────────────────
    test('renders Scenario Planner section', async ({ page }) => {
        await expect(page.locator('text=Scenario Planner')).toBeVisible();
    });

    test('has Reduce Spend slider', async ({ page }) => {
        await expect(page.locator('text=Reduce Spend')).toBeVisible();
        const slider = page.locator('input[type="range"]').first();
        await expect(slider).toBeVisible();
    });

    test('has Add Headcount slider', async ({ page }) => {
        await expect(page.locator('text=Add Headcount')).toBeVisible();
    });

    test('has Revenue Growth slider', async ({ page }) => {
        await expect(page.locator('text=Revenue Growth')).toBeVisible();
    });

    test('adjusting Reduce Spend slider updates scenario results', async ({ page }) => {
        const slider = page.locator('input[type="range"]').first();
        await slider.fill('25');
        // After adjusting, the "New Runway" should display
        await expect(page.locator('text=New Runway')).toBeVisible();
    });

    test('scenario results show Base and Scenario Monthly Burn', async ({ page }) => {
        await expect(page.locator('text=Base Monthly Burn')).toBeVisible();
        await expect(page.locator('text=Scenario Monthly Burn')).toBeVisible();
    });

    // ── KPI Cards ─────────────────────────────────────────────────────
    test('displays Terminal Date card', async ({ page }) => {
        await expect(page.locator('text=Terminal Date')).toBeVisible();
    });

    test('displays Monthly Net Burn card', async ({ page }) => {
        await expect(page.locator('text=Monthly Net Burn')).toBeVisible();
    });

    test('displays Safety Buffer card', async ({ page }) => {
        await expect(page.locator('text=Safety Buffer')).toBeVisible();
    });

    // ── Liquidity Trajectory Chart ────────────────────────────────────
    test('renders Liquidity Trajectory chart section', async ({ page }) => {
        await expect(page.locator('text=Liquidity Trajectory')).toBeVisible();
    });

    test('chart has 6-month projection label', async ({ page }) => {
        await expect(page.locator('text=6-month projection')).toBeVisible();
    });

    test('recharts SVG is rendered in chart container', async ({ page }) => {
        const chart = page.locator('.recharts-responsive-container');
        await expect(chart).toBeVisible();
    });
});
