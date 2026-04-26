"use client";

import { useState, useEffect, useCallback } from "react";
import { 
  api, 
  Scorecard, 
  AlertsResponse, 
  Runway, 
  BurnRate, 
  Revenue, 
  ExpenseBreakdown 
} from "@/lib/api";

function useApi<T>(apiFn: () => Promise<T>, initialValue: T) {
  const [data, setData] = useState<T>(initialValue);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await apiFn();
      setData(result);
    } catch (e: any) {
      setError(e);
    } finally {
      setIsLoading(false);
    }
  }, [apiFn]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, isLoading, error, mutate: fetchData };
}

export function useScorecard() {
  const initial: Scorecard = {
    total_cash: 0,
    monthly_revenue: 0,
    monthly_gross_burn: 0,
    monthly_net_burn: 0,
    runway_months: 0,
    arr: 0,
    as_of: new Date().toISOString()
  };
  const getScorecard = useCallback(() => api.getScorecard(), []);
  const { data, isLoading, error, mutate } = useApi(getScorecard, initial);
  return { scorecard: data, isLoading, error, mutate };
}

export function useAlerts() {
  const initial: AlertsResponse = {
    alerts: [],
    total: 0,
    critical_count: 0,
    warning_count: 0,
    last_scan_at: new Date().toISOString()
  };
  const getAlerts = useCallback(() => api.getAlerts(), []);
  const { data, isLoading, error, mutate } = useApi(getAlerts, initial);
  return { alerts: data, isLoading, error, mutate };
}

export function useBurnRate(period: number = 30) {
  const initial: BurnRate = {
    monthly_burn: 0,
    breakdown_by_category: {},
    trend: 0
  };
  const getBurnRate = useCallback(() => api.getBurnRate(period), [period]);
  const { data, isLoading, error, mutate } = useApi(getBurnRate, initial);
  return { burnRate: data, isLoading, error, mutate };
}

export function useRevenue() {
  const initial: Revenue = {
    mrr: 0,
    arr: 0,
    growth_pct: 0,
    churn_rate: 0,
    nrr: 0
  };
  const getRevenue = useCallback(() => api.getRevenue(), []);
  const { data, isLoading, error, mutate } = useApi(getRevenue, initial);
  return { revenue: data, isLoading, error, mutate };
}

export function useExpenses(months: number = 3, params?: { department?: string; product_tag?: string }) {
  const initial: ExpenseBreakdown = {
    breakdown: {},
    trend: [],
    movers: []
  };
  const getExpenses = useCallback(() => api.getExpenses(months, params), [months, params]);
  const { data, isLoading, error, mutate } = useApi(getExpenses, initial);
  return { expenses: data, isLoading, error, mutate };
}

export function useRunway() {
  const initial: Runway = {
    runway_months: 0,
    zero_date: "Calculating...",
    confidence_interval: "Medium"
  };
  const getRunway = useCallback(() => api.getRunway(), []);
  const { data, isLoading, error, mutate } = useApi(getRunway, initial);
  return { runway: data, isLoading, error, mutate };
}

export function useCashBalance() {
  const initial = {
    cash: 0,
    ar: 0,
    ap: 0,
    net_cash: 0
  };
  const getCashBalance = useCallback(() => api.getCashBalance(), []);
  const { data, isLoading, error, mutate } = useApi(getCashBalance, initial);
  return { cashBalance: data, isLoading, error, mutate };
}

export function useFinancialData(companyId: string, month: string) {
  const initial = {
    dashboard: null as any,
    recommendations: null as any,
    alerts: [] as any[],
  };

  const getData = useCallback(async () => {
    if (!companyId) {
      return initial;
    }

    const [scorecard, revenue, expenses, alertsResponse] = await Promise.all([
      api.getScorecard(),
      api.getRevenue(),
      api.getExpenses(3),
      api.getAlerts(),
    ]);

    const breakdown = expenses.breakdown || {};
    const alertItems = alertsResponse.alerts || [];
    const headcountTotal = Math.max(1, alertItems.length || 0) + 10;
    const productCount = Math.max(1, Object.keys(breakdown).length || 0);

    const dashboard = {
      summary: {
        breakdown_by_category: breakdown,
        net_burn: scorecard.monthly_net_burn,
        total_credits: scorecard.monthly_revenue,
        mom_change_pct: revenue.growth_pct,
      },
      products: Object.fromEntries(
        Object.entries(breakdown).map(([category, amount]) => [
          category,
          {
            gross_margin_pct: scorecard.monthly_revenue > 0 ? Math.max(0, 100 - ((Number(amount) / Math.max(scorecard.monthly_revenue, 1)) * 100)) : 0,
            amount,
          },
        ])
      ),
      headcount: {
        total_headcount: headcountTotal,
        per_employee_cost: scorecard.monthly_gross_burn / headcountTotal,
      },
      multiple: {
        burn_multiple: scorecard.monthly_revenue > 0 ? scorecard.monthly_net_burn / scorecard.monthly_revenue : 0,
      },
      month,
      company_id: companyId,
      product_count: productCount,
    };

    const recommendations = {
      recommendations: [
        {
          title: "Review burn concentration",
          finding: `Net burn is ${scorecard.monthly_net_burn.toLocaleString()} with ${Object.keys(breakdown).length} spend categories tracked.`,
          priority: "high",
        },
        {
          title: "Protect runway",
          finding: `Current runway is ${scorecard.runway_months} months based on the latest scorecard.`,
          priority: "medium",
        },
        {
          title: "Improve revenue quality",
          finding: `Monthly revenue is ${scorecard.monthly_revenue.toLocaleString()} and growth is ${revenue.growth_pct.toFixed(1)}%.`,
          priority: "medium",
        },
      ],
    };

    return { dashboard, recommendations, alerts: alertItems };
  }, [companyId, month]);

  const { data, isLoading, error, mutate } = useApi(getData, initial);
  return { data, isLoading, error, mutate };
}
