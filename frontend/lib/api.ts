const RAW_API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_BASE = RAW_API_BASE.replace(/\/$/, "").endsWith("/api/v1")
  ? RAW_API_BASE.replace(/\/$/, "")
  : `${RAW_API_BASE.replace(/\/$/, "")}/api/v1`;

// API Error class for better error handling
export class APIError extends Error {
  constructor(
    public status: number,
    public path: string,
    public detail: string,
    public originalError?: any
  ) {
    super(detail);
    this.name = "APIError";
  }
}

interface FetchOptions extends RequestInit {
  params?: Record<string, string | number | boolean>;
  timeout?: number;
  retries?: number;
}

// Request logging helper
function logRequest(method: string, url: string, options?: any) {
  if (typeof window !== "undefined" && window.location.hostname !== "localhost") {
    // Only log in development or when explicitly enabled
    if (process.env.NEXT_PUBLIC_DEBUG_API !== "false") {
      console.debug(`[API] ${method} ${url}`, options?.body ? `(body: ${options.body.substring(0, 100)}...)` : "");
    }
  }
}

// Response logging helper
function logResponse(status: number, url: string, duration: number) {
  if (typeof window !== "undefined" && window.location.hostname !== "localhost") {
    if (process.env.NEXT_PUBLIC_DEBUG_API !== "false") {
      console.debug(`[API] ${status} ${url} (${duration}ms)`);
    }
  }
}

// Error logging helper
function logError(error: Error, context: string) {
  console.error(`[API Error] ${context}:`, error.message);
  if (process.env.NODE_ENV === "development") {
    console.error(error);
  }
}

async function fetchAPI<T>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const { params, timeout = 30000, retries = 1, ...fetchOptions } = options;

  let url = `${API_BASE}${path}`;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        searchParams.append(key, String(value));
      }
    });
    url += `?${searchParams.toString()}`;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  let lastError: Error | null = null;
  let attempt = 0;

  while (attempt <= retries) {
    try {
      attempt++;
      logRequest(fetchOptions.method || "GET", url, fetchOptions);

      const startTime = performance.now();

      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("access_token") || localStorage.getItem("auth_token")
          : null;

      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          "Content-Type": "application/json",
          ...fetchOptions.headers,
        },
      });

      const duration = performance.now() - startTime;
      logResponse(response.status, url, duration);

      if (!response.ok) {
        const rawText = await response.text().catch(() => "");
        let errorDetail = `HTTP ${response.status}`;
        let errorData: any = {};

        try {
          if (rawText) {
            errorData = JSON.parse(rawText);
            errorDetail = errorData.detail || errorData.message || errorData.error || errorDetail;
          }
        } catch {
          // If JSON parsing fails, use raw text
          if (rawText) {
            errorDetail = rawText.substring(0, 200);
          }
        }

        const apiError = new APIError(response.status, path, errorDetail, errorData);
        logError(apiError, `API request failed: ${fetchOptions.method || "GET"} ${url}`);

        // Retry on certain status codes (5xx errors, 429 rate limit)
        if ((response.status >= 500 || response.status === 429) && attempt <= retries) {
          const backoffMs = Math.pow(2, attempt - 1) * 1000;
          console.warn(`[API] Retry attempt ${attempt}/${retries} after ${backoffMs}ms...`);
          await new Promise(resolve => setTimeout(resolve, backoffMs));
          continue;
        }

        throw apiError;
      }

      const data = await response.json().catch((err) => {
        const parseError = new Error(`Failed to parse API response as JSON: ${err.message}`);
        logError(parseError, `JSON parsing failed for ${url}`);
        throw parseError;
      });

      return data as T;
    } catch (error) {
      lastError = error as Error;

      if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
        const networkError = new Error(
          "Network error: Unable to reach the API server. Check your connection and try again."
        );
        logError(networkError, `Network error for ${url}`);
        throw networkError;
      }

      if (error instanceof DOMException && error.name === "AbortError") {
        const timeoutError = new Error(
          `Request timeout: API call exceeded ${timeout}ms. The server may be experiencing high load.`
        );
        logError(timeoutError, `Timeout for ${url}`);
        throw timeoutError;
      }

      if (error instanceof APIError) {
        throw error;
      }

      // Unexpected error, don't retry
      const unexpectedError = new Error(`Unexpected error: ${(error as Error).message}`);
      logError(unexpectedError, `Unexpected error for ${url}`);
      throw unexpectedError;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // If we get here, all retries failed
  throw lastError || new Error("API request failed after retries");
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

export interface ForecastPoint {
  forecast_date: string;
  mrr_predicted: number;
  cash_predicted: number;
  confidence_lower: number;
  confidence_upper: number;
}

export interface BudgetVarianceItem {
  category: string;
  budget: number;
  actual: number;
  variance: number;
  variance_pct: number;
  is_zero_based?: boolean;
}

export interface BudgetVarianceResponse {
  budget_name: string;
  month: string;
  department_filter?: string | null;
  variances: BudgetVarianceItem[];
}

export interface PayrollEntryItem {
  id: string;
  pay_date: string;
  gross_pay: number;
  net_pay: number;
  status: string;
  department?: string | null;
}

export interface AssetLifecycleItem {
  asset_id: string;
  asset_name: string;
  category?: string | null;
  age_years: number;
  remaining_life_years: number;
  book_value: number;
  recommendation: string;
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

export interface FinancialConceptResponse {
  status: string;
  concept_name: string;
  definition: string;
  interpretation: string;
  good_range: string;
  red_flags: string[];
  related_concepts: string[];
}

export interface FinancialConceptListResponse {
  status: string;
  total_concepts: number;
  concepts: string[];
}

export interface FinancialRecommendationsResponse {
  status: string;
  company_id: string;
  company_stage: string;
  recommendation_count: number;
  recommendations: Array<Record<string, unknown>>;
  summary: {
    critical: number;
    high: number;
    medium: number;
  };
}

export interface ComprehensiveFinancialAnalysisResponse {
  status: string;
  analysis_date: string;
  company_id: string;
  company_stage: string;
  income_statement: Record<string, unknown>;
  key_metrics: Record<string, unknown>;
  cash_flow: Record<string, unknown>;
  financial_health: Record<string, unknown>;
  recommendations: Array<Record<string, unknown>>;
  recommendation_summary: {
    total: number;
    critical: number;
    high: number;
    medium: number;
  };
}

export interface CashFlowAnalysisInput {
  operating_cash_flow: number;
  investing_cash_flow: number;
  financing_cash_flow: number;
  capex?: number;
  net_income: number;
}

export interface ProfitabilityAnalysisInput {
  revenue: number;
  cogs: number;
  operating_expenses: number;
  interest_expense?: number;
  tax_expense?: number;
}

export interface LiquidityAnalysisInput {
  current_assets: number;
  current_liabilities: number;
  inventory?: number;
}

export interface LeverageAnalysisInput {
  total_debt: number;
  total_equity: number;
  operating_profit: number;
  interest_expense: number;
}

export interface RunwayAnalysisResponse {
  status: string;
  months_of_runway?: number;
  runway_months?: number;
  zero_date?: string;
  confidence_interval?: string;
  [key: string]: unknown;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
}

// Safe wrapper for API calls with error handling and logging
export async function safeAPICall<T>(
  callFn: () => Promise<T>,
  defaultValue: T,
  context: string
): Promise<T> {
  try {
    return await callFn();
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    console.error(`[API Safe Call] ${context} failed: ${errorMsg}`);
    
    // Return default value to prevent UI crashes
    return defaultValue;
  }
}

// ─── Market-ready API types ──────────────────────────────────────────────────

export interface ContactRecord {
  id: string;
  name: string;
  type: string;
  email?: string | null;
  phone?: string | null;
  status?: string;
  payment_terms?: string | null;
  currency?: string;
  tax_number?: string | null;
  billing_address?: Record<string, unknown> | null;
  created_at?: string | null;
}

export interface InvoiceRecord {
  id: string;
  invoice_number: string;
  contact_id?: string | null;
  contact_name?: string | null;
  issue_date: string;
  due_date: string;
  payment_date?: string | null;
  status: string;
  type: string;
  sub_total: number;
  tax_amount: number;
  total_amount: number;
  amount_paid: number;
  amount_due: number;
  currency: string;
  memo?: string | null;
  created_at?: string | null;
}

export interface InvoicesListResponse {
  count: number;
  invoices: InvoiceRecord[];
  aging: { current: number; "1_30": number; "31_60": number; "61_90": number; over_90: number };
  total_outstanding: number;
}

export interface CreateInvoicePayload {
  invoice_number?: string;
  contact_id?: string;
  issue_date: string;
  due_date: string;
  type: string;
  sub_total: number;
  tax_amount?: number;
  currency?: string;
  memo?: string;
}

export interface SaasSummary {
  mrr: number;
  arr: number;
  mrr_growth_pct: number;
  nrr: number;
  gross_margin_pct: number;
  ltv: number;
  cac: number;
  ltv_cac_ratio: number;
  cac_payback_months: number;
  churn_rate_pct: number;
  rule_of_40: number;
  burn_rate: number;
  runway_months: number;
}

export interface MrrWaterfallMonth {
  month: string;
  mrr: number;
  new: number;
  expansion: number;
  contraction: number;
  churn: number;
}

export interface CohortData {
  cohort: string;
  cohort_value: string;
  customer_count: number;
  mrr_total: number;
  nrr: number;
  ltv: number;
  cac: number;
  churn_rate: number;
  payback_months: number;
  retention_curve: number[];
}

export interface MetricTrendMonth {
  month: string;
  mrr: number;
  expenses: number;
  burn_rate: number;
  runway_months: number;
  ending_cash: number;
  net_cash_flow: number;
}

export interface IncomeStatement {
  period: { start: string; end: string };
  revenue: { lines: { account: string; code: string; amount: number }[]; total: number };
  cogs: { lines: { account: string; code: string; amount: number }[]; total: number };
  gross_profit: number;
  gross_margin_pct: number;
  opex: { lines: { account: string; code: string; amount: number }[]; total: number };
  ebitda: number;
  ebit: number;
  net_income: number;
  net_margin_pct: number;
}

export interface BalanceSheet {
  as_of: string;
  assets: { lines: { account: string; code: string; amount: number }[]; total: number };
  liabilities: { lines: { account: string; code: string; amount: number }[]; total: number };
  equity: { lines: { account: string; code: string; amount: number }[]; retained_earnings: number; total: number };
  liabilities_and_equity: number;
  balanced: boolean;
}

export interface CashFlowStatement {
  period: { start: string; end: string };
  operating: { net_income: number; add_depreciation: number; change_in_ar: number; change_in_ap: number; net_operating: number };
  investing: { capex: number; net_investing: number };
  financing: { net_debt_change: number; net_financing: number };
  summary: { beginning_cash: number; net_change: number; ending_cash: number };
}

// API Functions
export const api = {
  // Cash & Financials
  getCashBalance: () => fetchAPI<CashBalance>("/cash-balance"),
  getBurnRate: (period: number = 30) => fetchAPI<BurnRate>("/burn-rate", { params: { period } }),
  getRunway: () => fetchAPI<Runway>("/runway"),
  getRevenue: () => fetchAPI<Revenue>("/revenue"),
  getScorecard: () => fetchAPI<Scorecard>("/scorecard"),
  analyzeFinancialCashFlow: (payload: CashFlowAnalysisInput) =>
    fetchAPI<Record<string, unknown>>("/financial/analyze/cash-flow", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  analyzeFinancialProfitability: (payload: ProfitabilityAnalysisInput) =>
    fetchAPI<Record<string, unknown>>("/financial/analyze/profitability", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  analyzeFinancialLiquidity: (payload: LiquidityAnalysisInput) =>
    fetchAPI<Record<string, unknown>>("/financial/analyze/working-capital", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  analyzeFinancialLeverage: (payload: LeverageAnalysisInput) =>
    fetchAPI<Record<string, unknown>>("/financial/analyze/leverage", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  analyzeFinancialComprehensive: (payload: Record<string, unknown>) =>
    fetchAPI<ComprehensiveFinancialAnalysisResponse>("/financial/analyze/comprehensive", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getFinancialConcept: (conceptName: string) =>
    fetchAPI<FinancialConceptResponse>(`/financial/concepts/${conceptName}`),
  listFinancialConcepts: () =>
    fetchAPI<FinancialConceptListResponse>("/financial/concepts"),
  getFinancialRecommendations: (payload: Record<string, unknown>) =>
    fetchAPI<FinancialRecommendationsResponse>("/financial/recommendations", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  calculateFinancialRunway: (params: { cash_balance: number; monthly_burn: number; monthly_revenue?: number; growth_rate?: number }) =>
    fetchAPI<RunwayAnalysisResponse>("/financial/calculate/runway", {
      method: "POST",
      params,
    }),
  getForecasts: (companyId: string, months: number = 6) =>
    fetchAPI<ForecastPoint[]>("/planning/forecasts", { params: { company_id: companyId, months } }),
  getBudgets: () => fetchAPI<any[]>("/planning/budgets"),
  getBudgetVariance: (budgetId: string, params?: { month?: string; department?: string }) =>
    fetchAPI<BudgetVarianceResponse>(`/planning/budgets/${budgetId}/variance`, { params: params as Record<string, string | number> }),

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
  getPayrollEntries: (params?: { start_date?: string; end_date?: string }) =>
    fetchAPI<PayrollEntryItem[]>("/payroll/payroll-entries", { params: params as Record<string, string | number> }),
  getMonthlyPayrollCost: (month?: string) =>
    fetchAPI<any>("/payroll/monthly-cost", { params: month ? { month } : undefined }),
  getEmployees: () => fetchAPI<any[]>("/payroll/employees"),
  getAssets: (companyId: string) => fetchAPI<any[]>("/depreciation/assets", { params: { company_id: companyId } }),
  getDepreciationEntries: (companyId: string) => fetchAPI<any[]>("/depreciation/entries", { params: { company_id: companyId } }),
  getDepreciationExpense: (companyId: string, month: string) =>
    fetchAPI<any>("/depreciation/monthly-expense", { params: { company_id: companyId, month } }),
  getMe: () => fetchAPI<any>("/users/me/"),
  login: (usernameOrEmail: string, password: string) =>
    fetchAPI<AuthTokenResponse>("/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username: usernameOrEmail, password }).toString(),
    }),
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

  // Contacts (vendors + customers)
  getContacts: (companyId: string, params?: { type?: string; status?: string; search?: string }) =>
    fetchAPI<{ count: number; contacts: ContactRecord[] }>("/contacts", {
      params: { company_id: companyId, ...params } as Record<string, string | number | boolean>,
    }),
  getContact: (contactId: string) => fetchAPI<ContactRecord>(`/contacts/${contactId}`),
  createContact: (companyId: string, payload: Omit<ContactRecord, "id" | "created_at">) =>
    fetchAPI<ContactRecord>(`/contacts?company_id=${companyId}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateContact: (contactId: string, payload: Partial<ContactRecord>) =>
    fetchAPI<ContactRecord>(`/contacts/${contactId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  // Invoices list (AR + AP)
  getInvoicesList: (companyId: string, params?: { type?: string; status?: string; contact_id?: string }) =>
    fetchAPI<InvoicesListResponse>("/invoices-list", {
      params: { company_id: companyId, ...params } as Record<string, string | number | boolean>,
    }),
  getInvoiceDetail: (invoiceId: string) => fetchAPI<InvoiceRecord>(`/invoices-list/${invoiceId}`),
  createInvoiceRecord: (companyId: string, payload: CreateInvoicePayload) =>
    fetchAPI<InvoiceRecord>(`/invoices-list?company_id=${companyId}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateInvoiceStatus: (invoiceId: string, payload: { status: string; payment_amount?: number; payment_date?: string }) =>
    fetchAPI<InvoiceRecord>(`/invoices-list/${invoiceId}/status`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  // SaaS metrics
  getSaasSummary: (companyId: string) =>
    fetchAPI<SaasSummary>("/saas-metrics/summary", { params: { company_id: companyId } }),
  getMrrWaterfall: (companyId: string, months = 12) =>
    fetchAPI<{ months: MrrWaterfallMonth[] }>("/saas-metrics/waterfall", { params: { company_id: companyId, months } }),
  getCohortRetention: (companyId: string) =>
    fetchAPI<{ cohorts: CohortData[]; count: number }>("/saas-metrics/cohorts", { params: { company_id: companyId } }),
  getMetricTrend: (companyId: string, months = 12) =>
    fetchAPI<{ months: MetricTrendMonth[] }>("/saas-metrics/trend", { params: { company_id: companyId, months } }),

  // Financial reports
  getIncomeStatement: (companyId: string, periodStart: string, periodEnd: string) =>
    fetchAPI<IncomeStatement>("/financial-reports/income-statement", {
      params: { company_id: companyId, period_start: periodStart, period_end: periodEnd },
    }),
  getBalanceSheet: (companyId: string, asOf: string) =>
    fetchAPI<BalanceSheet>("/financial-reports/balance-sheet", {
      params: { company_id: companyId, as_of: asOf },
    }),
  getCashFlowStatement: (companyId: string, periodStart: string, periodEnd: string) =>
    fetchAPI<CashFlowStatement>("/financial-reports/cash-flow", {
      params: { company_id: companyId, period_start: periodStart, period_end: periodEnd },
    }),
  getDepartmentBreakdown: (companyId: string, periodStart: string, periodEnd: string) =>
    fetchAPI<any>("/financial-reports/department-breakdown", {
      params: { company_id: companyId, period_start: periodStart, period_end: periodEnd },
    }),

  // Voice Commands
  processVoiceCommand: (companyId: string, command: string) =>
    fetchAPI<{ answer: string; intent: string; data: Record<string, unknown>; success: boolean }>(
      "/voice/command",
      { method: "POST", body: JSON.stringify({ company_id: companyId, command, source: "text" }) }
    ),
  getVoiceHistory: (companyId: string, limit = 50) =>
    fetchAPI<any>(`/voice/commands/history/${companyId}`, { params: { limit } }),

  // Realtime Sync
  triggerSync: (companyId: string) =>
    fetchAPI<any>(`/realtime-sync/trigger/${companyId}`, { method: "POST", body: JSON.stringify({}) }),
  getSyncStatus: (companyId: string) =>
    fetchAPI<any>(`/realtime-sync/status/${companyId}`),
  getSyncHistory: (companyId: string, limit = 50) =>
    fetchAPI<any>(`/realtime-sync/history/${companyId}`, { params: { limit } }),

  // ML Marketplace
  getDeployedModels: (companyId: string) =>
    fetchAPI<any>(`/ml-marketplace/models/${companyId}`),
  deployModel: (companyId: string, catalogId: string) =>
    fetchAPI<any>(`/ml-marketplace/models/${companyId}/deploy`, {
      method: "POST", body: JSON.stringify({ catalog_id: catalogId }),
    }),

  // Blockchain Audit
  getBlockchainReport: (companyId: string, period: string) =>
    fetchAPI<any>(`/blockchain-audit/report/${companyId}`, { params: { period } }),
  verifyAuditChain: (companyId: string) =>
    fetchAPI<any>(`/blockchain-audit/verify/${companyId}`),

  // Regulatory Compliance
  getSoxControls: (companyId: string) =>
    fetchAPI<any>(`/regulatory/sox/controls/${companyId}`),
  getRegulatoryDashboard: (companyId: string) =>
    fetchAPI<any>(`/regulatory/dashboard/${companyId}`),

  // White-Label
  getTenantBranding: (companyId: string) =>
    fetchAPI<any>(`/white-label/tenants/${companyId}/branding`),
  getTenantFeatures: (companyId: string) =>
    fetchAPI<any>(`/white-label/tenants/${companyId}/features`),
  getTenantUsage: (companyId: string) =>
    fetchAPI<any>(`/white-label/tenants/${companyId}/usage`),
};

export default api;
