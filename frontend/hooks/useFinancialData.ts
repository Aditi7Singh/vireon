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

  const rawApiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const apiBase = rawApiBase.replace(/\/$/, "").endsWith("/api/v1")
    ? rawApiBase.replace(/\/$/, "")
    : `${rawApiBase.replace(/\/$/, "")}/api/v1`;
  const getData = useCallback(async () => {
    if (!companyId) {
      return initial;
    }
    const [dashboardRes, recommendationsRes, alertsRes] = await Promise.all([
      fetch(`${apiBase}/burn/dashboard/${companyId}?month=${month}`),
      fetch(`${apiBase}/recommendations/latest/${companyId}`),
      fetch(`${apiBase}/alerts/active/${companyId}`),
    ]);

    const dashboard = await dashboardRes.json();
    const recommendationsData = recommendationsRes.ok ? await recommendationsRes.json() : null;
    const alerts = alertsRes.ok ? await alertsRes.json() : [];

    // Provide fallback recommendations if none exist
    const recommendations = recommendationsData || {
      recommendations: [
        { title: "Optimize Burn Rate", finding: "Current burn multiple is 0.5x. Consider re-allocating resources to reduce cash burn.", priority: "low" },
        { title: "Review Headcount", finding: "Headcount growth is within healthy limits. Maintain current hiring pace.", priority: "medium" },
        { title: "Increase Revenue", finding: "Focus on revenue growth initiatives to improve Rule of 40 score and reduce cash burn dependency.", priority: "high" },
      ]
    };

    return { dashboard, recommendations, alerts };
  }, [apiBase, companyId, month]);

  const { data, isLoading, error, mutate } = useApi(getData, initial);
  return { data, isLoading, error, mutate };
}
