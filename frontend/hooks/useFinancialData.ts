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

export function useExpenses(months: number = 3) {
  const initial: ExpenseBreakdown = {
    breakdown: {},
    trend: [],
    movers: []
  };
  const getExpenses = useCallback(() => api.getExpenses(months), [months]);
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
