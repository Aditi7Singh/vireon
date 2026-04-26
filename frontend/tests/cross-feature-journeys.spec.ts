import { test, expect } from '@playwright/test';

test.describe('Cross-Feature Integration & User Journey Tests', () => {

    // Increase timeout for journey tests that navigate multiple pages
    test.setTimeout(60000);

    // ── Complete CEO User Journey ─────────────────────────────────────
    test('CEO full journey: landing → dashboard → CEO view', async ({ page }) => {
        await page.goto('/');
        await expect(page.locator('h1')).toContainText('Vireon Times');

        await page.click('a:has-text("Open Vireon Dashboard")');
        await page.waitForURL('**/dashboard');
        await expect(page.locator('text=Executive Control Center')).toBeVisible();

        await page.click('a:has-text("CEO View")');
        await page.waitForURL('**/dashboard/ceo');
        await expect(page.locator('h1:has-text("CEO Dashboard")')).toBeVisible();

        // Verify KPIs load
        await expect(page.locator('text=Net Burn').first()).toBeVisible();
        await expect(page.locator('text=Cash Balance')).toBeVisible();
    });

    // ── CTO User Journey ──────────────────────────────────────────────
    test('CTO journey: dashboard → CTO planner → tech cost form', async ({ page }) => {
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');

        await page.click('aside a[href="/dashboard/cto"]');
        await page.waitForURL('**/dashboard/cto');
        await expect(page.locator('text=CTO Dashboard')).toBeVisible();

        await expect(page.locator('text=Quick Entry - Tech Cost')).toBeVisible();
    });

    // ── Finance Team Journey ──────────────────────────────────────────
    test('Finance journey: dashboard → finance view → tax', async ({ page }) => {
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');

        await page.click('a:has-text("Finance View")');
        await page.waitForURL('**/dashboard/finance');
        await expect(page.locator('h1:has-text("Finance Control")')).toBeVisible();

        await page.click('aside a[href="/tax"]');
        await page.waitForURL('**/tax');
        await expect(page.locator('h1:has-text("Tax Compliance Hub")')).toBeVisible();
    });

    // ── Anomaly Investigation Journey ─────────────────────────────────
    test('anomaly workflow: features → view anomalies page', async ({ page }) => {
        await page.goto('/features');
        await page.waitForLoadState('networkidle');

        await expect(page.locator('text=Anomaly Operations')).toBeVisible();
        await expect(page.locator('button:has-text("Seed demo anomalies")')).toBeVisible();

        await page.click('a:has-text("Open anomalies")');
        await page.waitForURL('**/anomalies');
        // Wait for loading to complete
        await page.waitForTimeout(3000);
        await expect(page.locator('h1:has-text("Financial Risk Dashboard")')).toBeVisible({ timeout: 15000 });
    });

    // ── Tax Compliance Journey ────────────────────────────────────────
    test('tax compliance: features → tax page with checklist', async ({ page }) => {
        await page.goto('/features');
        await page.waitForLoadState('networkidle');

        await expect(page.locator('text=Tax Operations')).toBeVisible();

        await page.click('a:has-text("Open tax page")');
        await page.waitForURL('**/tax');
        await expect(page.locator('h1:has-text("Tax Compliance Hub")')).toBeVisible();
        await expect(page.locator('text=Tax Filing Checklist')).toBeVisible();
    });

    // ── Scenario Planning Full Flow ───────────────────────────────────
    test('scenario planning: mode toggle → slider → decision signal', async ({ page }) => {
        await page.goto('/scenarios');
        await page.waitForLoadState('networkidle');

        await expect(page.locator('button:has-text("Balanced")')).toBeVisible();

        await page.click('button:has-text("Aggressive")');
        await expect(page.locator('text=Push expansion')).toBeVisible();

        await page.click('button:has-text("Growth Push")');
        await expect(page.locator('text=Policy changes sensitivity')).toBeVisible();

        const slider = page.locator('input[type="range"]').first();
        await slider.fill('25');

        await expect(page.locator('text=Finance Decision Signal')).toBeVisible();
    });

    // ── AI Agent Quick Actions ────────────────────────────────────────
    test('AI agent: navigate and verify quick actions', async ({ page }) => {
        await page.goto('/agent');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);

        // The agent page renders with TopBar + intelligence core badge
        await expect(page.locator('text=Financial intelligence core')).toBeVisible({ timeout: 15000 });

        await expect(page.locator('button:has-text("Survival path audit")')).toBeVisible();
        await expect(page.locator('button:has-text("Growth vector analysis")')).toBeVisible();
    });

    // ── Operations Center Full Workflow ────────────────────────────────
    test('operations center: all sections and interactive elements', async ({ page }) => {
        await page.goto('/operations');
        await page.waitForLoadState('networkidle');

        await expect(page.locator('h2:has-text("Live FX")')).toBeVisible();
        await expect(page.locator('h2:has-text("Forecast Governance")')).toBeVisible();
        await expect(page.locator('h2:has-text("Collections")')).toBeVisible();
        await expect(page.locator('h2:has-text("Invoice Queue Priority")')).toBeVisible();
        await expect(page.locator('h2:has-text("Document Workflow Actions")')).toBeVisible();

        await expect(page.locator('button:has-text("Sync live FX")')).toBeVisible();
        await expect(page.locator('button:has-text("Retrain now")')).toBeVisible();
    });

    // ── Revenue to Benchmarking ───────────────────────────────────────
    test('revenue to benchmarking via sidebar', async ({ page }) => {
        await page.goto('/revenue');
        await page.waitForLoadState('networkidle');
        await expect(page.locator('body')).toContainText('Revenue');

        await page.click('aside a[href="/benchmarking"]');
        await page.waitForURL('**/benchmarking');
        await page.waitForTimeout(2000);
        await expect(page.locator('body')).toContainText('Benchmark', { timeout: 15000 });
    });

    // ── Runway to Expenses Deep Dive ──────────────────────────────────
    test('runway to expenses via sidebar', async ({ page }) => {
        await page.goto('/runway');
        await page.waitForLoadState('networkidle');
        await expect(page.locator('body')).toContainText('Runway', { timeout: 15000 });

        await page.click('aside a[href="/expenses"]');
        await page.waitForURL('**/expenses');
        await expect(page.locator('body')).toContainText('Expense', { timeout: 15000 });
    });

    // ── Settings Configuration ────────────────────────────────────────
    test('settings page: readiness + team access', async ({ page }) => {
        await page.goto('/settings');
        await page.waitForLoadState('networkidle');

        await expect(page.locator('text=Startup Readiness')).toBeVisible();
        await expect(page.locator('text=Team Access')).toBeVisible();
        await expect(page.locator('text=VIREON AI')).toBeVisible();
    });
});
