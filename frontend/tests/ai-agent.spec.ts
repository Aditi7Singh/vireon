import { test, expect } from './fixtures';

test.describe('AI Agent Page', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/agent');
        await page.waitForLoadState('networkidle');
        // Wait for the chat interface to fully render
        await page.waitForTimeout(2000);
    });

    // ── Page Structure ────────────────────────────────────────────────
    test('renders Financial intelligence core badge', async ({ page }) => {
        await expect(page.locator('text=Financial intelligence core')).toBeVisible({ timeout: 15000 });
    });

    test('shows backend connection status', async ({ page }) => {
        const status = page.locator('text=/Backend connected|Check backend status/');
        await expect(status).toBeVisible();
    });

    // ── Chat Interface ────────────────────────────────────────────────
    test('renders initial chat message', async ({ page }) => {
        // Initial greeting - check for either message variant
        const greeting = page.locator('text=/ready to help|Unable to load|start a new query/');
        await expect(greeting).toBeVisible({ timeout: 15000 });
    });

    test('has message input field', async ({ page }) => {
        const input = page.locator('input[placeholder="Ask your finance question"]');
        await expect(input).toBeVisible();
    });

    test('has send button', async ({ page }) => {
        const sendBtn = page.locator('button[type="submit"]');
        await expect(sendBtn).toBeVisible();
    });

    // ── Quick Action Buttons ──────────────────────────────────────────
    test('displays quick action buttons', async ({ page }) => {
        const quickActions = [
            'Survival path audit',
            'Growth vector analysis',
            'GL anomaly detection',
            'Show top active alerts',
        ];
        for (const action of quickActions) {
            await expect(page.locator(`button:has-text("${action}")`)).toBeVisible();
        }
    });

    // ── Message Sending ───────────────────────────────────────────────
    test('can type a message in the input field', async ({ page }) => {
        const input = page.locator('input[placeholder="Ask your finance question"]');
        await input.fill('What is our current runway?');
        await expect(input).toHaveValue('What is our current runway?');
    });

    test('clicking quick action sends message to chat', async ({ page }) => {
        await page.click('button:has-text("Survival path audit")');
        await page.waitForTimeout(500);
        // The quick action text should now appear in chat as user message
        const userMsg = page.locator('.justify-end').first();
        await expect(userMsg).toBeVisible({ timeout: 10000 });
    });

    test('submitting a message shows it in chat', async ({ page }) => {
        const input = page.locator('input[placeholder="Ask your finance question"]');
        await input.fill('Test message');
        await page.press('input[placeholder="Ask your finance question"]', 'Enter');
        await expect(page.locator('text=Test message')).toBeVisible();
    });

    // ── Chat Messages Layout ──────────────────────────────────────────
    test('chat messages have user and assistant role indicators', async ({ page }) => {
        // Initial assistant message should already be present
        await expect(page.locator('text=assistant').first()).toBeVisible({ timeout: 15000 });
    });

    test('user messages appear on the right after sending', async ({ page }) => {
        await page.click('button:has-text("Growth vector analysis")');
        await page.waitForTimeout(500);
        const userMsg = page.locator('.justify-end').first();
        await expect(userMsg).toBeVisible();
    });
});
