import { test, expect } from './fixtures';

test.describe('Landing Page (Home)', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    // ── Structure & Branding ──────────────────────────────────────────
    test('renders the Vireon Times masthead', async ({ page }) => {
        const heading = page.locator('h1');
        await expect(heading).toBeVisible();
        await expect(heading).toContainText('Vireon Times');
    });

    test('displays the hero tagline — AI CFO Takes The Helm', async ({ page }) => {
        const tagline = page.locator('text=AI CFO Takes The Helm');
        await expect(tagline).toBeVisible();
    });

    test('shows the meta subtitle with ERP transformation message', async ({ page }) => {
        await expect(page.locator('text=Transforming Financial Management')).toBeVisible();
    });

    test('renders the header metadata strip (Vol, Copilot, Price)', async ({ page }) => {
        await expect(page.locator('text=Vol 1, No 1')).toBeVisible();
        await expect(page.locator('text=AI Financial Copilot for ERP Systems')).toBeVisible();
        await expect(page.locator('text=Price: Productive Decisions')).toBeVisible();
    });

    // ── Highlight Cards ───────────────────────────────────────────────
    test('renders all 3 highlight cards with titles', async ({ page }) => {
        const highlights = ['ERP Integration', 'What-If Simulations', 'Anomaly Detection'];
        for (const title of highlights) {
            await expect(page.locator(`h2:has-text("${title}")`)).toBeVisible();
        }
    });

    test('each highlight card has a subtitle and blurb', async ({ page }) => {
        await expect(page.locator('text=Real-time data. Real decisions.')).toBeVisible();
        await expect(page.locator('text=Test before you commit.')).toBeVisible();
        await expect(page.locator('text=Spot risk before it compounds.')).toBeVisible();
    });

    // ── CTA Buttons ───────────────────────────────────────────────────
    test('has "Open Vireon Dashboard" CTA that links to /dashboard', async ({ page }) => {
        const cta = page.locator('a:has-text("Open Vireon Dashboard")');
        await expect(cta).toBeVisible();
        await expect(cta).toHaveAttribute('href', '/dashboard');
    });

    test('clicking "Open Vireon Dashboard" navigates to dashboard', async ({ page }) => {
        await page.click('a:has-text("Open Vireon Dashboard")');
        await page.waitForURL('**/dashboard');
        await expect(page).toHaveURL(/\/dashboard/);
    });

    test('has "Go to Vireon" secondary CTA', async ({ page }) => {
        const secondaryCTA = page.locator('a:has-text("Go to Vireon")');
        await expect(secondaryCTA).toBeVisible();
        await expect(secondaryCTA).toHaveAttribute('href', '/dashboard');
    });

    // ── Anomaly Spotlight Section ─────────────────────────────────────
    test('renders anomaly alert section with 45% spike', async ({ page }) => {
        await expect(page.locator('text=Anomaly Detected')).toBeVisible();
        await expect(page.locator('text=45%')).toBeVisible();
        await expect(page.locator('text=vs average baseline')).toBeVisible();
    });

    test('shows AI Chat Insight snippet', async ({ page }) => {
        await expect(page.locator('text=AI Chat Insight')).toBeVisible();
        await expect(page.locator('text=Why did expenses spike last month?')).toBeVisible();
    });

    // ── Runway Forecast Section ───────────────────────────────────────
    test('shows runway forecast with cash and months', async ({ page }) => {
        await expect(page.locator('text=Runway Forecast')).toBeVisible();
        await expect(page.locator('text=$790K')).toBeVisible();
        await expect(page.locator('text=5.2')).toBeVisible();
    });

    // ── Bar Chart / Visual Elements ───────────────────────────────────
    test('renders the expense bar chart (12 bars)', async ({ page }) => {
        const bars = page.locator('.bg-\\[\\#465a72\\]');
        await expect(bars).toHaveCount(12);
    });

    // ── Footer Strip ──────────────────────────────────────────────────
    test('displays footer capability strip with all 4 items', async ({ page }) => {
        const footerItems = [
            'Loan & Depreciation Calculations',
            'Multi-Currency Support in Progress',
            'PDF Reports Available',
            'Cloud Deployment with AWS + Ollama',
        ];
        for (const item of footerItems) {
            await expect(page.locator(`text=${item}`)).toBeVisible();
        }
    });

    // ── Responsive layout check (basic) ───────────────────────────────
    test('page renders content correctly on mobile viewport', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 812 });
        await expect(page.locator('h1')).toBeVisible();
        await expect(page.locator('a:has-text("Open Vireon Dashboard")')).toBeVisible();
    });
});
