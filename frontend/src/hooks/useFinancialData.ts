/**
 * Custom SWR Hooks for Financial Data
 * Auto-refresh with configurable intervals, sync with Zustand
 */

import { useEffect } from 'react';
import useSWR, { SWRConfiguration } from 'swr';
import { API } from '@/lib/api';
import { useAppStore } from '@/lib/store';
import type {
  CashBalance,
  BurnRate,
  Runway,
  Revenue,
  ExpenseBreakdown,
  Scorecard,
  AlertsResponse,
} from '@/lib/api';

const swrConfigFast: SWRConfiguration = {
  revalidateOnFocus: false,
  revalidateOnReconnect: true,
  dedupingInterval: 30000,
  focusThrottleInterval: 30000,
  refreshInterval: 30000, // 30s for financial data
};

const swrConfigSlow: SWRConfiguration = {
  revalidateOnFocus: false,
  revalidateOnReconnect: true,
  dedupingInterval: 60000,
  focusThrottleInterval: 60000,
  refreshInterval: 60000, // 60s for alerts/expenses
};

/**
 * Fetch cash balance (30s refresh)
 */
export function useCashBalance() {
  const { data, error, isLoading, mutate } = useSWR(
    'cash-balance',
    API.getCashBalance,
    swrConfigFast
  );

  return {
    data: data || {
      cash: 0,
      ar: 0,
      ap: 0,
      net_cash: 0,
      currency: 'USD',
      last_updated: new Date().toISOString(),
    },
    isLoading: isLoading && !data,
    error,
    mutate,
  };
}

/**
 * Fetch burn rate (30s refresh)
 */
export function useBurnRate(periodDays = 30) {
  const { data, error, isLoading, mutate } = useSWR(
    `burn-rate-${periodDays}`,
    () => API.getBurnRate(periodDays),
    swrConfigFast
  );

  return {
    data: data || {
      monthly_burn: 0,
      breakdown_by_category: {},
      trend: { period_days: periodDays, comparison_percent: 0 },
      last_updated: new Date().toISOString(),
    },
    isLoading: isLoading && !data,
    error,
    mutate,
  };
}

/**
 * Fetch cash runway (30s refresh)
 */
export function useRunway() {
  const { data, error, isLoading, mutate } = useSWR(
    'runway',
    API.getRunway,
    swrConfigFast
  );

  return {
    data: data || {
      runway_months: 0,
      zero_date: new Date().toISOString(),
      confidence_interval: { low: 0, high: 0 },
      cash_available: 0,
      monthly_burn: 0,
      last_updated: new Date().toISOString(),
    },
    isLoading: isLoading && !data,
    error,
    mutate,
  };
}

/**
 * Fetch revenue metrics (60s refresh)
 */
export function useRevenue() {
  const { data, error, isLoading, mutate } = useSWR(
    'revenue',
    API.getRevenue,
    swrConfigSlow
  );

  return {
    data: data || {
      mrr: 0,
      arr: 0,
      growth_pct: 0,
      churn_rate: 0,
      nrr: 0,
      trend_12m: [],
      last_updated: new Date().toISOString(),
    },
    isLoading: isLoading && !data,
    error,
    mutate,
  };
}

/**
 * Fetch expense breakdown (60s refresh)
 */
export function useExpenses(months = 3) {
  const { data, error, isLoading, mutate } = useSWR(
    `expenses-${months}`,
    () => API.getExpenses(months),
    swrConfigSlow
  );

  return {
    data: data || {
      breakdown: {},
      trend: {},
      movers: [],
      total: 0,
      period_months: months,
      last_updated: new Date().toISOString(),
    },
    isLoading: isLoading && !data,
    error,
    mutate,
  };
}

/**
 * Fetch financial scorecard (30s refresh)
 */
export function useScorecard() {
  const { data, error, isLoading, mutate } = useSWR(
    'scorecard',
    API.getScorecard,
    swrConfigFast
  );

  return {
    data: data || {
      cash_balance: 0,
      monthly_burn: 0,
      runway_months: 0,
      mrr: 0,
      churn_rate: 0,
      burn_multiple: 0,
      magic_number: 0,
      cac_payback_months: 0,
      gross_margin_pct: 0,
      last_updated: new Date().toISOString(),
    },
    isLoading: isLoading && !data,
    error,
    mutate,
  };
}

/**
 * Fetch active alerts (60s refresh) and sync to Zustand
 */
export function useAlerts(severity?: string, category?: string, limit = 20) {
  const setAlertCount = useAppStore((state) => state.setAlertCount);
  const { setAlerts } = useAppStore((state) => ({
    setAlerts: state.setAlerts,
  }));

  const { data, error, isLoading, mutate } = useSWR(
    `alerts-${severity || 'all'}-${category || 'all'}-${limit}`,
    () => API.getAlerts(severity, category, limit),
    swrConfigSlow
  );

  // Sync alert count to Zustand whenever data changes
  useEffect(() => {
    if (data && data.alerts) {
      setAlerts(data.alerts);
      setAlertCount(data.total || 0);
    }
  }, [data, setAlerts, setAlertCount]);

  return {
    data: data || {
      alerts: [],
      total: 0,
      critical_count: 0,
      warning_count: 0,
      info_count: 0,
      last_scan_at: null,
      filtered: { severity, category, limit },
    },
    isLoading: isLoading && !data,
    error,
    mutate,
  };
}

/**
 * Trigger anomaly scan and poll for results
 */
export async function triggerAnomalyScan() {
  const response = await API.scanNow();
  if (!response) return null;

  // Poll for status
  const taskId = response.task_id;
  let attempts = 0;
  const maxAttempts = 60; // 30 seconds at 500ms intervals

  while (attempts < maxAttempts) {
    await new Promise((r) => setTimeout(r, 500));
    const status = await API.getScanStatus(taskId);

    if (!status) continue;

    if (status.status === 'success' || status.status === 'failure') {
      return status;
    }

    attempts++;
  }

  return null;
}
