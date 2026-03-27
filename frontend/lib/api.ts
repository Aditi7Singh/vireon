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
  credential_readiness?: {
    environment?: string;
    storage_backend?: string;
    ocr_provider?: string;
    missing_keys?: string[];
    ready?: boolean;
  };
  connector_conflict_policy?: {
    merge?: "source_of_truth" | "latest_timestamp_wins" | "manual_review";
    plaid?: "source_of_truth" | "latest_timestamp_wins" | "manual_review";
    cloud_costs?: "source_of_truth" | "latest_timestamp_wins" | "manual_review";
  };
  issues: string[];
  actions?: string[];
}

export interface StartupRemediationResult {
  success: boolean;
  action: string;
  message?: string;
  synced?: number;
  result?: unknown;
}

export interface ScenarioSnapshot {
  id: string;
  name: string;
  scenario_type: string;
  input_data: Record<string, unknown>;
  result_data: Record<string, unknown>;
  created_at: string;
}

export interface NotificationContacts {
  email_recipients: string[];
  phone_recipients?: string[];
  ceo?: string;
  founders?: string[];
  finance?: string[];
  cto?: string;
}

export interface FxRateRow {
  base_currency: string;
  target_currency: string;
  exchange_rate: number;
  effective_date: string;
}

export interface FxRatesResponse {
  count: number;
  rates: FxRateRow[];
}

export interface FxSyncResponse {
  success: boolean;
  source: string;
  synced: number;
  effective_date: string;
  warning?: string;
  rates: Record<string, number>;
}

export interface ForecastMonitor {
  company_id: string;
  samples: number;
  mae_cash: number;
  mape_cash: number;
  health?: string;
  message?: string;
}

export interface ForecastEnsemble {
  current_cash_inr: number;
  runway_months: number;
  runway_date: string;
  model_used: string;
  weights: Record<string, number>;
  monthly_projections: Array<Record<string, unknown>>;
  last_updated: string;
}

export interface CollectionsAging {
  as_of: string;
  ar: {
    buckets: Record<string, number>;
    total_open: number;
  };
  ap: {
    buckets: Record<string, number>;
    total_open: number;
  };
  overdue_receivables: Array<{
    invoice_id: string;
    invoice_number: string;
    due_date: string | null;
    days_overdue: number | null;
    amount_due: number;
  }>;
}

export interface InvoiceQueueItem {
  invoice_id: string;
  invoice_number: string;
  due_date: string | null;
  days_overdue: number;
  amount_due: number;
  priority: string;
  status: string;
}

export interface InvoiceQueueResponse {
  as_of: string;
  count: number;
  queue: InvoiceQueueItem[];
}

export interface InvoiceDsoResponse {
  as_of: string;
  lookback_days: number;
  open_ar: number;
  period_credit_sales: number;
  average_daily_sales: number;
  dso_days: number;
}

export interface DocumentWriteResponse {
  success: boolean;
  message: string;
  document_id: string;
}

export interface InvoiceTaxBreakdown {
  invoice_base: number;
  gst_amount: number;
  tds_deducted: number;
  total_invoice: number;
  net_cash_expected: number;
}

export interface PayrollTaxBreakdown {
  gross_pay: number;
  employee_pf: number;
  employee_esi: number;
  professional_tax: number;
  income_tax_tds: number;
  total_deductions: number;
  net_pay: number;
}

export interface HiringImpactResponse {
  baseline_runway_months: number;
  new_runway_months: number;
  runway_impact_days: number;
  projected_hire_costs_12m?: number;
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
  getExpenses: (months: number = 3, params?: { department?: string; product_tag?: string }) => 
    fetchAPI<ExpenseBreakdown>("/expenses", { params: { months, ...params } }),

  // Alerts
  getAlerts: (params?: { severity?: string; category?: string; limit?: number }) =>
    fetchAPI<AlertsResponse>("/alerts", { params: params as Record<string, string | number> }),
  dismissAlert: (alertId: string) =>
    fetchAPI<{ status: string }>(`/alerts/${alertId}/dismiss`, { method: "PATCH" }),
  triggerScan: () =>
    fetchAPI<{ task_id: string }>("/alerts/scan-now", { method: "POST" }),
  seedDemoAlerts: () =>
    fetchAPI<{ success: boolean; created: number }>("/alerts/seed-demo", { method: "POST" }),

  // Agent
  chat: (message: string, sessionId?: string) =>
    fetchAPI<AgentChatResponse>("/agent/chat", {
      method: "POST",
      body: JSON.stringify({ message, session_id: sessionId })
    }),
  getHistory: (sessionId: string) =>
    fetchAPI<{ session_id: string; messages: AgentMessage[] }>(`/agent/history/${sessionId}`),
  
  // Tax
  getTaxRules: (companyId: string) => fetchAPI<any[]>(`/tax/rules/${companyId}`),
  getTaxSummary: (companyId: string, year: number, quarter: number) => 
    fetchAPI<any>("/tax/quarterly-summary", { params: { company_id: companyId, year, quarter } }),
  getTaxSchedule: (companyId: string) => fetchAPI<any[]>(`/tax/payment-schedule/${companyId}`),
  reconcileTaxPayment: (liabilityId: string, amount: number, reference: string) =>
    fetchAPI<any>("/tax/reconcile-payment", {
      method: "POST",
      params: { liability_id: liabilityId, amount, reference }
    }),
  createQuarterlyLiability: (companyId: string, year: number, quarter: number) =>
    fetchAPI<any>("/tax/quarterly-liability", {
      method: "POST",
      params: { company_id: companyId, year, quarter },
    }),
  calculateInvoiceTax: (companyId: string, invoiceBaseAmount: number, isService: boolean = true) =>
    fetchAPI<InvoiceTaxBreakdown>("/tax/calculate/invoice", {
      params: { company_id: companyId, invoice_base_amount: invoiceBaseAmount, is_service: isService },
    }),
  calculatePayrollTax: (companyId: string, grossMonthly: number) =>
    fetchAPI<PayrollTaxBreakdown>("/tax/calculate/payroll", {
      params: { company_id: companyId, gross_monthly: grossMonthly },
    }),

  // Notifications
  getNotificationContacts: (companyId: string) =>
    fetchAPI<NotificationContacts>(`/notifications/contacts/${companyId}`),
  updateNotificationContacts: (companyId: string, payload: NotificationContacts) =>
    fetchAPI<{ success: boolean; notification_contacts: NotificationContacts }>(`/notifications/contacts/${companyId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  sendTestNotification: (companyId: string) =>
    fetchAPI<{ success: boolean; message: string; alert_id: string }>(`/alerts/test-notification/${companyId}`, {
      method: "POST",
    }),

  // Manual inputs
  createTechCost: (payload: {
    company_id: string;
    cost_type: "aws_compute" | "aws_storage" | "aws_other" | "software_license" | "saas_tool" | "infra_other";
    product_tag: "orchard" | "sprouts" | "ai_lab" | "shared" | "unallocated";
    amount_inr: number;
    billing_period: string;
    vendor_name: string;
    description: string;
    is_recurring?: boolean;
  }) =>
    fetchAPI<{ success: boolean; ledger_entry_id: string; message: string }>("/inputs/tech-cost", {
      method: "POST",
      headers: { "x-user-role": "cto" },
      body: JSON.stringify(payload),
    }),
  getHiringImpact: (payload: {
    company_id: string;
    annual_ctc_inr: number;
    join_month: string;
  }) =>
    fetchAPI<HiringImpactResponse>("/forecast/hiring-impact", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Ops Center (new backend endpoint wiring)
  syncLiveFx: (currencies: string[]) =>
    fetchAPI<FxSyncResponse>('/fx/sync-live', {
      method: 'POST',
      body: JSON.stringify({ currencies }),
    }),
  getFxRates: () => fetchAPI<FxRatesResponse>('/fx/rates'),
  getForecastEnsemble: (companyId: string) => fetchAPI<ForecastEnsemble>(`/forecast/ensemble/${companyId}`),
  getForecastMonitor: (companyId: string, lookbackMonths: number = 6) =>
    fetchAPI<ForecastMonitor>(`/forecast/monitor/${companyId}`, {
      params: { lookback_months: lookbackMonths },
    }),
  retrainForecast: (companyId: string) =>
    fetchAPI<{ success: boolean; company_id: string; message: string; monitoring: ForecastMonitor }>(
      `/forecast/retrain/${companyId}`,
      { method: 'POST' }
    ),
  getCollectionsAging: (companyId: string) => fetchAPI<CollectionsAging>(`/collections/aging/${companyId}`),
  getInvoiceQueue: (companyId: string) => fetchAPI<InvoiceQueueResponse>(`/invoices/queue/${companyId}`),
  getInvoiceDso: (companyId: string, lookbackDays: number = 90) =>
    fetchAPI<InvoiceDsoResponse>(`/invoices/dso/${companyId}`, {
      params: { lookback_days: lookbackDays },
    }),
  classifyDocument: (documentId: string) =>
    fetchAPI<DocumentWriteResponse>(`/documents/${documentId}/classify`, { method: 'POST' }),
  workflowDocument: (documentId: string, action: 'approve' | 'reject' | 'post_ledger', note?: string) =>
    fetchAPI<DocumentWriteResponse>(`/documents/${documentId}/workflow`, {
      method: 'POST',
      body: JSON.stringify({ action, note }),
    }),

  getBenchmarks: () => fetchAPI<any>("/benchmarks/sass-health"),
  getMe: () => fetchAPI<any>("/users/me/"),
  getStartupHealth: () => fetchAPI<StartupHealth>("/system/startup-health"),
  runStartupRemediation: (action: string, month?: string) =>
    fetchAPI<StartupRemediationResult>("/system/remediate", {
      method: "POST",
      body: JSON.stringify({ action, month }),
    }),
  getConnectorConflictPolicy: () =>
    fetchAPI<{ policy: Record<string, string> }>("/system/connectors/conflict-policy"),
  updateConnectorConflictPolicy: (policy: Record<string, string>) =>
    fetchAPI<{ success: boolean; policy?: Record<string, string>; message?: string }>(
      "/system/connectors/conflict-policy",
      {
        method: "PUT",
        body: JSON.stringify(policy),
      }
    ),
  saveScenario: (payload: {
    name: string;
    scenario_type: string;
    input_data: Record<string, unknown>;
    result_data: Record<string, unknown>;
  }) =>
    fetchAPI<{ status: string; id: string }>("/planning/scenarios/save", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getScenarioHistory: () => fetchAPI<ScenarioSnapshot[]>("/planning/scenarios/history"),
};

export default api;
