import { test, expect } from '@playwright/test';

test.describe('Scenarios / Strategic Simulations Page', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/scenarios');
        await page.waitForLoadState('networkidle');
    });

    // ── Page Structure ────────────────────────────────────────────────
    test('renders page title "Strategic Simulations"', async ({ page }) => {
        await expect(page.locator('text=Strategic Simulations')).toBeVisible();
    });

    test('displays heading about planning decisions', async ({ page }) => {
        await expect(page.locator('h1:has-text("Plan decisions")')).toBeVisible();
    });

    test('shows Scenario engine badge', async ({ page }) => {
        await expect(page.locator('text=Scenario engine')).toBeVisible();
    });

    // ── Planning Mode Toggle ──────────────────────────────────────────
    test('has Planning Mode section with three modes', async ({ page }) => {
        await expect(page.locator('text=Planning Mode')).toBeVisible();
        await expect(page.locator('button:has-text("Defensive")')).toBeVisible();
        await expect(page.locator('button:has-text("Balanced")')).toBeVisible();
        await expect(page.locator('button:has-text("Aggressive")')).toBeVisible();
    });

    test('Balanced mode is selected by default', async ({ page }) => {
        const balancedBtn = page.locator('button:has-text("Balanced")');
        await expect(balancedBtn).toHaveClass(/bg-\[#2a2118\]/);
    });

    test('switching to Defensive mode updates note text', async ({ page }) => {
        await page.click('button:has-text("Defensive")');
        await expect(page.locator('text=Protect runway under demand softness')).toBeVisible();
    });

    test('switching to Aggressive mode updates note text', async ({ page }) => {
        await page.click('button:has-text("Aggressive")');
        await expect(page.locator('text=Push expansion and accept higher cash pressure')).toBeVisible();
    });

    // ── Cash Policy Toggle ────────────────────────────────────────────
    test('has Cash Policy section with two options', async ({ page }) => {
        await expect(page.locator('text=Cash Policy')).toBeVisible();
        await expect(page.locator('button:has-text("Preserve Runway")')).toBeVisible();
        await expect(page.locator('button:has-text("Growth Push")')).toBeVisible();
    });

    test('toggling cash policy updates sensitivity note', async ({ page }) => {
        await page.click('button:has-text("Growth Push")');
        await expect(page.locator('text=Policy changes sensitivity')).toBeVisible();
    });

    // ── Scenario KPI Cards ────────────────────────────────────────────
    test('displays Monthly Hiring Burden card', async ({ page }) => {
        await expect(page.locator('text=Monthly Hiring Burden')).toBeVisible();
    });

    test('displays Annual Hiring Cost card', async ({ page }) => {
        await expect(page.locator('text=Annual Hiring Cost')).toBeVisible();
    });

    test('displays Revenue Effect card', async ({ page }) => {
        await expect(page.locator('text=Revenue Effect')).toBeVisible();
    });

    test('displays Net Runway Effect card', async ({ page }) => {
        await expect(page.locator('text=Net Runway Effect')).toBeVisible();
    });

    // ── Hiring Simulation ─────────────────────────────────────────────
    test('renders Hiring Simulation section', async ({ page }) => {
        await expect(page.locator('text=Hiring Simulation')).toBeVisible();
    });

    test('has new hires range slider', async ({ page }) => {
        await expect(page.locator('text=/New hires:/')).toBeVisible();
    });

    test('has average salary range slider', async ({ page }) => {
        await expect(page.locator('text=/Avg salary/')).toBeVisible();
    });

    test('shows runway pressure from hiring', async ({ page }) => {
        await expect(page.locator('text=Runway pressure from hiring')).toBeVisible();
    });

    test('has Save Snapshot button for hiring', async ({ page }) => {
        const saveBtn = page.locator('button:has-text("Save Snapshot")').first();
        await expect(saveBtn).toBeVisible();
    });

    // ── Revenue Stress Test ───────────────────────────────────────────
    test('renders Revenue Stress Test section', async ({ page }) => {
        await expect(page.locator('text=Revenue Stress Test')).toBeVisible();
    });

    test('has revenue shift slider', async ({ page }) => {
        await expect(page.locator('text=/Revenue shift:/')).toBeVisible();
    });

    test('shows Potential runway contribution', async ({ page }) => {
        await expect(page.locator('text=Potential runway contribution')).toBeVisible();
    });

    // ── Finance Decision Signal ───────────────────────────────────────
    test('shows Finance Decision Signal section', async ({ page }) => {
        await expect(page.locator('text=Finance Decision Signal')).toBeVisible();
    });

    test('displays operating signal badge (healthy/caution/high-risk)', async ({ page }) => {
        const badge = page.locator('text=/healthy|caution|high-risk/');
        await expect(badge).toBeVisible();
    });

    test('has Ask finance agent for plan button', async ({ page }) => {
        const btn = page.locator('button:has-text("Ask finance agent for plan")');
        await expect(btn).toBeVisible();
    });

    // ── Generate Executive Memo CTA ───────────────────────────────────
    test('has Generate executive memo button', async ({ page }) => {
        const btn = page.locator('button:has-text("Generate executive memo")');
        await expect(btn).toBeVisible();
    });

    // ── Slider Interactions ───────────────────────────────────────────
    test('adjusting hiring count slider changes burden value', async ({ page }) => {
        const slider = page.locator('input[type="range"]').first();
        const burdenCard = page.locator('article').filter({ hasText: 'Monthly Hiring Burden' });
        const initialValue = await burdenCard.locator('p.text-xl').innerText();

        await slider.fill('30');

        const newValue = await burdenCard.locator('p.text-xl').innerText();
        // Values should be different after changing slider
        expect(newValue).not.toBe(initialValue);
    });
});
