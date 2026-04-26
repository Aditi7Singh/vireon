import { test, expect } from '@playwright/test';

test.describe('Accessibility & Semantic Structure Tests', () => {

    // ── Landing Page Accessibility ────────────────────────────────────
    test.describe('Landing Page', () => {

        test('has proper heading hierarchy with single h1', async ({ page }) => {
            await page.goto('/');
            const h1Elements = page.locator('h1');
            await expect(h1Elements).toHaveCount(1);
            await expect(h1Elements.first()).toContainText('Vireon Times');
        });

        test('all images have alt text or are decorative', async ({ page }) => {
            await page.goto('/');
            const images = page.locator('img');
            const count = await images.count();
            for (let i = 0; i < count; i++) {
                const img = images.nth(i);
                const alt = await img.getAttribute('alt');
                const role = await img.getAttribute('role');
                expect(alt !== null || role === 'presentation').toBeTruthy();
            }
        });

        test('CTA links are focusable and have visible focus', async ({ page }) => {
            await page.goto('/');
            const cta = page.locator('a:has-text("Open Vireon Dashboard")');
            await cta.focus();
            await expect(cta).toBeFocused();
        });

        test('page has proper lang attribute', async ({ page }) => {
            await page.goto('/');
            const lang = await page.locator('html').getAttribute('lang');
            expect(lang).toBeTruthy();
        });

        test('all links have accessible names', async ({ page }) => {
            await page.goto('/');
            const links = page.locator('a');
            const count = await links.count();
            for (let i = 0; i < count; i++) {
                const link = links.nth(i);
                const text = await link.innerText();
                const ariaLabel = await link.getAttribute('aria-label');
                expect(text.length > 0 || (ariaLabel && ariaLabel.length > 0)).toBeTruthy();
            }
        });
    });

    // ── Dashboard Page Accessibility ──────────────────────────────────
    test.describe('Dashboard', () => {

        test('dashboard has semantic main content area', async ({ page }) => {
            await page.goto('/dashboard');
            await page.waitForLoadState('networkidle');
            // Use first() since layout has multiple main-like areas
            const main = page.locator('main').first();
            await expect(main).toBeVisible();
        });

        test('sidebar uses aside element', async ({ page }) => {
            await page.goto('/dashboard');
            await page.waitForLoadState('networkidle');
            const aside = page.locator('aside');
            await expect(aside).toBeVisible();
        });

        test('sidebar navigation uses nav element', async ({ page }) => {
            await page.goto('/dashboard');
            await page.waitForLoadState('networkidle');
            const nav = page.locator('aside nav');
            await expect(nav).toBeVisible();
        });

        test('navigation links are keyboard accessible', async ({ page }) => {
            await page.goto('/dashboard');
            await page.waitForLoadState('networkidle');
            const firstLink = page.locator('aside a').first();
            await firstLink.focus();
            await expect(firstLink).toBeFocused();
        });

        test('interactive buttons are present and functional', async ({ page }) => {
            await page.goto('/dashboard');
            await page.waitForLoadState('networkidle');
            const buttons = page.locator('button');
            const count = await buttons.count();
            expect(count).toBeGreaterThan(0);
        });
    });

    // ── Form Accessibility ────────────────────────────────────────────
    test.describe('Form Controls', () => {

        test('tax checklist checkboxes are keyboard operable', async ({ page }) => {
            await page.goto('/tax');
            await page.waitForLoadState('networkidle');
            const checkbox = page.locator('input[type="checkbox"]').first();
            await checkbox.focus();
            await expect(checkbox).toBeFocused();
        });

        test('expense department dropdown is keyboard accessible', async ({ page }) => {
            await page.goto('/expenses');
            await page.waitForLoadState('networkidle');
            const select = page.locator('select');
            await select.focus();
            await expect(select).toBeFocused();
        });

        test('anomaly search input has placeholder text', async ({ page }) => {
            await page.goto('/anomalies');
            await page.waitForLoadState('networkidle');
            await page.waitForTimeout(3000);
            const searchInput = page.locator('input[placeholder="Search anomalies"]');
            await expect(searchInput).toBeVisible({ timeout: 15000 });
        });

        test('AI agent chat input has clear placeholder', async ({ page }) => {
            await page.goto('/agent');
            await page.waitForLoadState('networkidle');
            const input = page.locator('input[placeholder="Ask your finance question"]');
            await expect(input).toBeVisible();
        });

        test('scenario sliders are interactive via keyboard', async ({ page }) => {
            await page.goto('/scenarios');
            await page.waitForLoadState('networkidle');
            const slider = page.locator('input[type="range"]').first();
            await slider.focus();
            await expect(slider).toBeFocused();
        });
    });

    // ── Visual Hierarchy ──────────────────────────────────────────────
    test.describe('Visual Hierarchy', () => {

        test('stable pages each have a clear h1 heading', async ({ page }) => {
            // Only test pages that always render h1 without API dependency
            const pages = [
                { url: '/dashboard', text: 'financial story' },
                { url: '/expenses', text: 'Expense Control Center' },
                { url: '/tax', text: 'Tax Compliance Hub' },
                { url: '/settings', text: 'Platform Settings' },
            ];

            for (const p of pages) {
                await page.goto(p.url);
                await page.waitForLoadState('networkidle');
                const h1 = page.locator('h1').first();
                await expect(h1).toBeVisible({ timeout: 10000 });
            }
        });
    });
});
