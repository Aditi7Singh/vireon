import { test, expect } from '@playwright/test';

test.describe('Operations Center Page', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/operations');
        await page.waitForLoadState('networkidle');
    });

    test('renders Operations Center page title', async ({ page }) => {
        await expect(page.locator('text=Operations Center')).toBeVisible();
    });

    test('displays Finance Operations Controls heading', async ({ page }) => {
        await expect(page.locator('h1:has-text("Finance Operations Controls")')).toBeVisible();
    });

    test('shows Ops Coverage badge', async ({ page }) => {
        await expect(page.locator('text=Ops Coverage')).toBeVisible();
    });

    test('has Refresh button', async ({ page }) => {
        await expect(page.locator('button:has-text("Refresh")')).toBeVisible();
    });

    test('renders Live FX section', async ({ page }) => {
        await expect(page.locator('h2:has-text("Live FX")')).toBeVisible();
    });

    test('has Sync live FX button', async ({ page }) => {
        await expect(page.locator('button:has-text("Sync live FX")')).toBeVisible();
    });

    test('renders Forecast Governance section', async ({ page }) => {
        await expect(page.locator('h2:has-text("Forecast Governance")')).toBeVisible();
    });

    test('has Retrain now button', async ({ page }) => {
        await expect(page.locator('button:has-text("Retrain now")')).toBeVisible();
    });

    test('shows forecast MAPE and MAE metrics', async ({ page }) => {
        await expect(page.locator('text=MAPE')).toBeVisible();
        await expect(page.locator('text=MAE')).toBeVisible();
    });

    test('renders Collections & DSO section', async ({ page }) => {
        await expect(page.locator('h2:has-text("Collections & DSO")')).toBeVisible();
    });

    test('shows Open AR, Open AP, DSO, Overdue AR', async ({ page }) => {
        await expect(page.locator('text=Open AR')).toBeVisible();
        await expect(page.locator('text=Open AP')).toBeVisible();
        await expect(page.locator('text=DSO')).toBeVisible();
        await expect(page.locator('text=Overdue AR')).toBeVisible();
    });

    test('renders Invoice Queue Priority section', async ({ page }) => {
        await expect(page.locator('h2:has-text("Invoice Queue Priority")')).toBeVisible();
    });

    test('renders Document Workflow Actions section', async ({ page }) => {
        await expect(page.locator('h2:has-text("Document Workflow Actions")')).toBeVisible();
    });

    test('has Document ID and Workflow note inputs', async ({ page }) => {
        await expect(page.locator('input[placeholder="Document ID"]')).toBeVisible();
        await expect(page.locator('input[placeholder*="Workflow note"]')).toBeVisible();
    });

    test('has Classify, Approve, Reject, Post to ledger buttons', async ({ page }) => {
        await expect(page.locator('button:has-text("Classify document")')).toBeVisible();
        await expect(page.locator('button:has-text("Approve")')).toBeVisible();
        await expect(page.locator('button:has-text("Reject")')).toBeVisible();
        await expect(page.locator('button:has-text("Post to ledger")')).toBeVisible();
    });
});
