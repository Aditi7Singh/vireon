const RAW_API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_BASE = RAW_API_BASE.replace(/\/$/, "").endsWith("/api/v1")
  ? RAW_API_BASE.replace(/\/$/, "")
  : `${RAW_API_BASE.replace(/\/$/, "")}/api/v1`;

interface FetchOptions extends RequestInit {
  params?: Record<string, string | number | boolean>;
}

async function fetchAPI<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { params, ...fetchOptions } = options;

  let url = `${API_BASE}${path}`;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      searchParams.append(key, String(value));
    });
    url += `?${searchParams.toString()}`;
  }

  const response = await fetch(url, {
    ...fetchOptions,
    headers: {
      "Content-Type": "application/json",
      ...fetchOptions.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

// Types
export interface CashBalance {
  cash: number;
  ar: number;
  ap: number;
  net_cash: number;
}

export interface BurnRate {
  monthly_burn: number;
  breakdown_by_category: Record<string, number>;
  trend: number;
}

export interface Runway {
  runway_months: number;
  zero_date: string;
  confidence_interval: string;
}

export interface Revenue {
  mrr: number;
  arr: number;
  growth_pct: number;
  churn_rate: number;
  nrr: number;
}

export interface Scorecard {
  total_cash: number;
  monthly_revenue: number;
  monthly_gross_burn: number;
  monthly_net_burn: number;
  runway_months: number;
  arr: number;
  as_of: string;
}

export interface Alert {
  id: string;
  severity: "critical" | "warning" | "info";
  alert_type: string;
  category: string;
  description: string;
  amount: number;
  baseline: number;
  delta_pct: number;
  runway_impact: number;
  suggested_owner: string;
  created_at: string;
  status: "active" | "dismissed" | "resolved";
}

export interface AlertsResponse {
  alerts: Alert[];
  total: number;
  critical_count: number;
  warning_count: number;
  last_scan_at: string;
}

export interface Expense {
  category: string;
  amount: number;
  trend: number;
}

export interface ExpenseBreakdown {
  breakdown: Record<string, number>;
  trend: Expense[];
  movers: Expense[];
}

export interface AgentMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface AgentChatResponse {
  response: string;
  session_id: string;
  query_type: string;
  timestamp: string;
}

export interface StartupHealth {
  status: "ok" | "warning";
  default_company_id?: string | null;
  checks: {
    companies: number;
    monthly_metrics: number;
    ledger_entries: number;
    exchange_rates: number;
    fx_revaluation_snapshots?: number;
    documents?: number;
    ocr_pipeline: string;
  };
  table_readiness?: Record<string, boolean>;
  issues: string[];
  actions?: string[];
}

// API Functions
export const api = {
  // Cash & Financials
  getCashBalance: () => fetchAPI<CashBalance>("/cash-balance"),
  getBurnRate: (period: number = 30) => fetchAPI<BurnRate>("/burn-rate", { params: { period } }),
  getRunway: () => fetchAPI<Runway>("/runway"),
  getRevenue: () => fetchAPI<Revenue>("/revenue"),
  getScorecard: () => fetchAPI<Scorecard>("/scorecard"),

  // Expenses
  getExpenses: (months: number = 3) => fetchAPI<ExpenseBreakdown>("/expenses", { params: { months } }),

  // Alerts
  getAlerts: (params?: { severity?: string; category?: string; limit?: number }) =>
    fetchAPI<AlertsResponse>("/alerts", { params: params as Record<string, string | number> }),
  dismissAlert: (alertId: string) =>
    fetchAPI<{ status: string }>(`/alerts/${alertId}/dismiss`, { method: "PATCH" }),
  triggerScan: () =>
    fetchAPI<{ task_id: string }>("/alerts/scan-now", { method: "POST" }),

  // Agent
  chat: (message: string, sessionId?: string) =>
    fetchAPI<AgentChatResponse>("/agent/chat", {
      method: "POST",
      body: JSON.stringify({ message, session_id: sessionId })
    }),
  getHistory: (sessionId: string) =>
    fetchAPI<{ session_id: string; messages: AgentMessage[] }>(`/agent/history/${sessionId}`),
  
  // Benchmarks
  getBenchmarks: () => fetchAPI<any>("/benchmarks/sass-health"),
  getMe: () => fetchAPI<any>("/users/me/"),
  getStartupHealth: () => fetchAPI<StartupHealth>("/system/startup-health"),
};

export default api;
