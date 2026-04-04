import { test, expect } from '@playwright/test';

test.describe('Performance & Load Time Tests', () => {

    // ── Page Load Performance ─────────────────────────────────────────
    test.describe('Page Load Times', () => {

        const criticalPages = [
            { name: 'Landing', url: '/' },
            { name: 'Dashboard', url: '/dashboard' },
            { name: 'CEO Dashboard', url: '/dashboard/ceo' },
            { name: 'CTO Dashboard', url: '/dashboard/cto' },
            { name: 'Finance Dashboard', url: '/dashboard/finance' },
            { name: 'Runway', url: '/runway' },
            { name: 'Expenses', url: '/expenses' },
            { name: 'Revenue', url: '/revenue' },
            { name: 'Scenarios', url: '/scenarios' },
            { name: 'Tax', url: '/tax' },
            { name: 'Anomalies', url: '/anomalies' },
            { name: 'Benchmarking', url: '/benchmarking' },
            { name: 'AI Agent', url: '/agent' },
            { name: 'Features Hub', url: '/features' },
            { name: 'Operations', url: '/operations' },
            { name: 'Settings', url: '/settings' },
        ];

        for (const p of criticalPages) {
            test(`${p.name} page loads within acceptable time`, async ({ page }) => {
                const start = Date.now();
                await page.goto(p.url);
                await page.waitForLoadState('domcontentloaded');
                const loadTime = Date.now() - start;
                expect(loadTime).toBeLessThan(10000);
            });
        }
    });

    // ── No Console Errors ─────────────────────────────────────────────
    test.describe('Console Error Checks', () => {

        const pages = [
            { name: 'Landing', url: '/' },
            { name: 'Dashboard', url: '/dashboard' },
            { name: 'Runway', url: '/runway' },
            { name: 'Expenses', url: '/expenses' },
            { name: 'Revenue', url: '/revenue' },
            { name: 'Scenarios', url: '/scenarios' },
            { name: 'Tax', url: '/tax' },
        ];

        for (const p of pages) {
            test(`${p.name} page has no critical JS errors`, async ({ page }) => {
                const errors: string[] = [];
                page.on('pageerror', (err) => {
                    errors.push(err.message);
                });
                await page.goto(p.url);
                await page.waitForLoadState('networkidle');
                const criticalErrors = errors.filter(
                    (e) => !e.includes('fetch') && !e.includes('Failed to fetch') && !e.includes('NetworkError')
                );
                expect(criticalErrors).toHaveLength(0);
            });
        }
    });

    // ── No 404 Resources ──────────────────────────────────────────────
    test.describe('Resource Loading', () => {

        test('landing page has no 404 resource errors', async ({ page }) => {
            const failedRequests: string[] = [];
            page.on('response', (response) => {
                if (response.status() === 404 && !response.url().includes('/api/')) {
                    failedRequests.push(response.url());
                }
            });
            await page.goto('/');
            await page.waitForLoadState('networkidle');
            expect(failedRequests).toHaveLength(0);
        });

        test('dashboard has no 404 resource errors', async ({ page }) => {
            const failedRequests: string[] = [];
            page.on('response', (response) => {
                if (response.status() === 404 && !response.url().includes('/api/')) {
                    failedRequests.push(response.url());
                }
            });
            await page.goto('/dashboard');
            await page.waitForLoadState('networkidle');
            expect(failedRequests).toHaveLength(0);
        });
    });

    // ── Viewport Rendering Stability ──────────────────────────────────
    test.describe('Viewport Stability', () => {

        test('no horizontal overflow on mobile viewport', async ({ page }) => {
            await page.setViewportSize({ width: 375, height: 812 });
            await page.goto('/');
            const body = page.locator('body');
            const bodyBox = await body.boundingBox();
            expect(bodyBox).toBeTruthy();
            if (bodyBox) {
                expect(bodyBox.width).toBeLessThanOrEqual(375 + 20);
            }
        });

        test('dashboard content area fills available space', async ({ page }) => {
            await page.setViewportSize({ width: 1920, height: 1080 });
            await page.goto('/dashboard');
            await page.waitForLoadState('networkidle');
            // Use first() since there may be multiple main elements
            const main = page.locator('main').first();
            await expect(main).toBeVisible();
            const mainBox = await main.boundingBox();
            expect(mainBox).toBeTruthy();
            if (mainBox) {
                expect(mainBox.width).toBeGreaterThan(500);
            }
        });
    });
});
