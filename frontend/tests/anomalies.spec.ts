import { test, expect } from '@playwright/test';

test.describe('Anomalies & Financial Risk Page', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/anomalies');
        // Wait for either content to load or loading state to finish
        await page.waitForLoadState('networkidle');
        // Wait for the page to render past loading state
        await page.waitForTimeout(2000);
    });

    // ── Page Structure ────────────────────────────────────────────────
    test('renders Financial Risk Dashboard heading', async ({ page }) => {
        await expect(page.locator('h1:has-text("Financial Risk Dashboard")')).toBeVisible({ timeout: 15000 });
    });

    test('shows Real-time monitoring badge', async ({ page }) => {
        await expect(page.locator('text=Real-time monitoring')).toBeVisible({ timeout: 15000 });
    });

    test('shows anomaly detection description', async ({ page }) => {
        await expect(page.locator('text=Anomaly detection')).toBeVisible({ timeout: 15000 });
    });

    // ── Action Buttons ────────────────────────────────────────────────
    test('has Test Email button', async ({ page }) => {
        await expect(page.locator('button:has-text("Test Email")')).toBeVisible({ timeout: 15000 });
    });

    test('has Send Alerts Now button', async ({ page }) => {
        await expect(page.locator('button:has-text("Send Alerts Now")')).toBeVisible({ timeout: 15000 });
    });

    test('has Configure button', async ({ page }) => {
        await expect(page.locator('button:has-text("Configure")')).toBeVisible({ timeout: 15000 });
    });

    // ── Risk Score Cards ──────────────────────────────────────────────
    test('displays Risk Score card', async ({ page }) => {
        await expect(page.locator('text=Risk Score')).toBeVisible({ timeout: 15000 });
    });

    test('displays Anomalies count card', async ({ page }) => {
        // Use more specific locator to avoid ambiguity with page title
        const card = page.locator('p:has-text("Anomalies")').first();
        await expect(card).toBeVisible({ timeout: 15000 });
    });

    test('displays Runway card in risk section', async ({ page }) => {
        await expect(page.locator('p:has-text("Runway")').first()).toBeVisible({ timeout: 15000 });
    });

    test('displays Alerts Sent card', async ({ page }) => {
        await expect(page.locator('text=Alerts Sent')).toBeVisible({ timeout: 15000 });
    });

    // ── Detected Anomalies List ───────────────────────────────────────
    test('renders Detected Anomalies section', async ({ page }) => {
        await expect(page.locator('text=Detected Anomalies')).toBeVisible({ timeout: 15000 });
    });

    // ── Filter Buttons ────────────────────────────────────────────────
    test('has severity filter buttons', async ({ page }) => {
        const filters = ['all', 'critical', 'warning', 'info'];
        for (const f of filters) {
            await expect(page.locator(`button:has-text("${f}")`).first()).toBeVisible({ timeout: 15000 });
        }
    });

    test('clicking filter button updates active state', async ({ page }) => {
        const criticalBtn = page.locator('button:has-text("critical")').first();
        await criticalBtn.click();
        await expect(criticalBtn).toHaveClass(/bg-\[#f5e7cf\]/);
    });

    // ── Search ────────────────────────────────────────────────────────
    test('has anomaly search input', async ({ page }) => {
        const searchInput = page.locator('input[placeholder="Search anomalies"]');
        await expect(searchInput).toBeVisible({ timeout: 15000 });
    });

    test('typing in search field works', async ({ page }) => {
        const searchInput = page.locator('input[placeholder="Search anomalies"]');
        await searchInput.fill('test search');
        await expect(searchInput).toHaveValue('test search');
    });

    // ── Configure Alert Panel ─────────────────────────────────────────
    test('clicking Configure opens email alert configuration panel', async ({ page }) => {
        await page.locator('button:has-text("Configure")').click();
        await expect(page.locator('text=Configure Email Alerts')).toBeVisible({ timeout: 10000 });
    });

    test('configuration panel has CEO Email input', async ({ page }) => {
        await page.locator('button:has-text("Configure")').click();
        await expect(page.locator('text=CEO Email')).toBeVisible({ timeout: 10000 });
    });

    test('configuration panel has Finance Team textarea', async ({ page }) => {
        await page.locator('button:has-text("Configure")').click();
        await expect(page.locator('text=Finance Team')).toBeVisible({ timeout: 10000 });
    });

    test('configuration panel has Save and Cancel buttons', async ({ page }) => {
        await page.locator('button:has-text("Configure")').click();
        await expect(page.locator('button:has-text("Save Configuration")')).toBeVisible({ timeout: 10000 });
        await expect(page.locator('button:has-text("Cancel")')).toBeVisible({ timeout: 10000 });
    });

    test('clicking Cancel closes configuration panel', async ({ page }) => {
        await page.locator('button:has-text("Configure")').click();
        await expect(page.locator('text=Configure Email Alerts')).toBeVisible({ timeout: 10000 });
        await page.locator('button:has-text("Cancel")').click();
        await expect(page.locator('text=Configure Email Alerts')).not.toBeVisible();
    });

    test('shows Currently Configured section within config panel', async ({ page }) => {
        await page.locator('button:has-text("Configure")').click();
        await expect(page.locator('text=Currently Configured')).toBeVisible({ timeout: 10000 });
    });
});
