import { test, expect } from './fixtures';

test.describe('Dashboard Home Page', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
    });

    // ── Hero Section ──────────────────────────────────────────────────
    test('renders hero with Executive Control Center badge', async ({ page }) => {
        await expect(page.locator('text=Executive Control Center')).toBeVisible();
    });

    test('displays main heading about financial story', async ({ page }) => {
        const h1 = page.locator('h1');
        await expect(h1).toContainText('financial story');
    });

    test('shows subtitle about ERP, payroll, cloud, and revenue', async ({ page }) => {
        await expect(page.locator('text=Unified ERP, payroll, cloud')).toBeVisible();
    });

    // ── Role-Based Navigation CTAs ────────────────────────────────────
    test('has CEO View button linking to /dashboard/ceo', async ({ page }) => {
        const ceoLink = page.locator('a:has-text("CEO View")');
        await expect(ceoLink).toBeVisible();
        await expect(ceoLink).toHaveAttribute('href', '/dashboard/ceo');
    });

    test('has Finance View button linking to /dashboard/finance', async ({ page }) => {
        const financeLink = page.locator('a:has-text("Finance View")');
        await expect(financeLink).toBeVisible();
        await expect(financeLink).toHaveAttribute('href', '/dashboard/finance');
    });

    test('clicking CEO View navigates successfully', async ({ page }) => {
        await page.click('a:has-text("CEO View")');
        await page.waitForURL('**/dashboard/ceo');
        await expect(page).toHaveURL(/\/dashboard\/ceo/);
    });

    // ── KPI Metric Cards ──────────────────────────────────────────────
    test('displays 4 KPI metric cards', async ({ page }) => {
        const metricLabels = ['Net Burn', 'Burn Multiple', 'Runway', 'Team Cost Ratio'];
        for (const label of metricLabels) {
            await expect(page.locator(`text=${label}`)).toBeVisible();
        }
    });

    test('Net Burn metric shows formatted currency value', async ({ page }) => {
        // Check that the Net Burn card has a formatted value like ₹1.41M
        const burnCard = page.locator('article').filter({ hasText: 'Net Burn' });
        const value = burnCard.locator('p.text-2xl');
        await expect(value).toBeVisible();
        const text = await value.innerText();
        expect(text).toMatch(/₹[\d.,]+[KM]/);
    });

    test('Runway metric shows months', async ({ page }) => {
        const runwayCard = page.locator('article').filter({ hasText: 'Runway' });
        const value = runwayCard.locator('p.text-2xl');
        await expect(value).toContainText('months');
    });

    test('Burn Multiple metric shows multiplier', async ({ page }) => {
        const card = page.locator('article').filter({ hasText: 'Burn Multiple' });
        const value = card.locator('p.text-2xl');
        await expect(value).toBeVisible();
        const text = await value.innerText();
        expect(text).toMatch(/[\d.]+x/);
    });

    // ── Burn vs Revenue Chart ─────────────────────────────────────────
    test('renders Burn vs Revenue Momentum chart section', async ({ page }) => {
        await expect(page.locator('text=Burn vs Revenue Momentum')).toBeVisible();
    });

    test('chart has burn and revenue legend items', async ({ page }) => {
        await expect(page.locator('text=Monthly Burn')).toBeVisible();
        await expect(page.locator('text=Revenue')).toBeVisible();
    });

    test('chart container is visible with recharts SVG', async ({ page }) => {
        const chartContainer = page.locator('.recharts-responsive-container');
        await expect(chartContainer).toBeVisible();
    });

    test('chart has Explore runway link', async ({ page }) => {
        await expect(page.locator('text=Explore runway')).toBeVisible();
    });

    // ── Priority Actions ──────────────────────────────────────────────
    test('displays Priority Actions section', async ({ page }) => {
        await expect(page.locator('text=Priority Actions')).toBeVisible();
    });

    test('shows 3 priority action items', async ({ page }) => {
        const actions = [
            'Optimize cloud spend in ML workloads',
            'Accelerate collections for enterprise invoices',
            'Recalibrate growth hiring for Q3',
        ];
        for (const action of actions) {
            await expect(page.locator(`text=${action}`)).toBeVisible();
        }
    });

    test('priority actions have owner labels', async ({ page }) => {
        await expect(page.locator('text=Owner: CTO')).toBeVisible();
        await expect(page.locator('text=Owner: Finance')).toBeVisible();
        await expect(page.locator('text=Owner: CEO')).toBeVisible();
    });

    // ── Module Navigation Cards ───────────────────────────────────────
    test('displays module navigation cards', async ({ page }) => {
        const modules = [
            'Runway Intelligence',
            'Expense Forensics',
            'Revenue Signal',
            'Scenario Engine',
            'Feature Hub',
        ];
        for (const module of modules) {
            await expect(page.locator(`text=${module}`)).toBeVisible();
        }
    });

    test('module cards link to correct pages', async ({ page }) => {
        const moduleLinks = [
            { title: 'Runway Intelligence', href: '/runway' },
            { title: 'Expense Forensics', href: '/expenses' },
            { title: 'Revenue Signal', href: '/revenue' },
            { title: 'Scenario Engine', href: '/scenarios' },
            { title: 'Feature Hub', href: '/features' },
        ];
        for (const mod of moduleLinks) {
            const link = page.locator(`a`).filter({ hasText: mod.title });
            await expect(link).toHaveAttribute('href', mod.href);
        }
    });

    test('clicking a module card navigates to the module page', async ({ page }) => {
        await page.click('a:has-text("Runway Intelligence")');
        await page.waitForURL('**/runway');
        await expect(page).toHaveURL(/\/runway/);
    });
});
