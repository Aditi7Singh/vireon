import { test, expect } from './fixtures';

test('uses same-origin API fallback when the upstream host is unavailable', async ({ page }) => {
  const requests: string[] = [];

  await page.route('**/api/v1/**', async (route) => {
    const requestUrl = new URL(route.request().url());
    requests.push(requestUrl.href);

    if (requestUrl.origin !== 'http://localhost:3000') {
      await route.abort();
      return;
    }

    const payload = buildPayload(requestUrl.pathname);
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(payload),
    });
  });

  await page.goto('/dashboard/finance');

  await expect(page.getByRole('heading', { name: 'Finance Control · Finley CFO' })).toBeVisible({ timeout: 20000 });

  expect(requests.some((url) => url.startsWith('http://localhost:8000/api/v1/'))).toBeTruthy();
  expect(requests.some((url) => url.startsWith('http://localhost:3000/api/v1/'))).toBeTruthy();
});

function buildPayload(pathname: string) {
  if (pathname.endsWith('/system/startup-health')) {
    return {
      default_company_id: 'demo-company',
      issues: [],
      actions: [],
    };
  }

  if (pathname.endsWith('/scorecard')) {
    return {
      total_cash: 2640000,
      monthly_revenue: 1480000,
      monthly_gross_burn: 1240000,
      monthly_net_burn: 1240000,
      runway_months: 6.8,
      arr: 17760000,
      as_of: new Date().toISOString(),
    };
  }

  if (pathname.endsWith('/revenue')) {
    return {
      mrr: 1480000,
      arr: 17760000,
      growth_pct: 12.1,
      churn_rate: 2.4,
      nrr: 108.2,
    };
  }

  if (pathname.endsWith('/expenses')) {
    return {
      breakdown: {
        engineering: 580000,
        infrastructure: 180000,
        marketing: 140000,
        operations: 120000,
        ga: 100000,
        other: 120000,
      },
      trend: [],
      movers: [],
    };
  }

  if (pathname.endsWith('/alerts')) {
    return {
      alerts: [],
      total: 0,
      critical_count: 0,
      warning_count: 0,
      last_scan_at: new Date().toISOString(),
    };
  }

  if (pathname.includes('/financial/recommendations')) {
    return { recommendations: [] };
  }

  if (pathname.includes('/metrics/history/')) {
    return [];
  }

  if (pathname.includes('/burn/expenses/')) {
    return {};
  }

  if (pathname.includes('/inputs/pending-review')) {
    return { pending_review: {} };
  }

  return {};
}