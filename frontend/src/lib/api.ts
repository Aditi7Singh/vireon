/**
 * API Client - Typed fetcher for all backend endpoints
 * Base URL: http://localhost:8000
 * All endpoints return typed responses or null on error
 */

const API_BASE =
  typeof window !== 'undefined'
    ? process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    : 'http://localhost:8000';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface CashBalance {
  cash: number;
  ar: number;
  ap: number;
  net_cash: number;
  currency: string;
  last_updated: string;
}

export interface BurnRate {
  monthly_burn: number;
  breakdown_by_category: Record<string, number>;
  trend: {
    period_days: number;
    comparison_percent: number; // vs previous period
  };
  last_updated: string;
}

export interface Runway {
  runway_months: number;
  zero_date: string;
  confidence_interval: {
    low: number;
    high: number;
  };
  cash_available: number;
  monthly_burn: number;
  last_updated: string;
}

export interface Revenue {
  mrr: number;
  arr: number;
  growth_pct: number;
  churn_rate: number;
  nrr: number;
  trend_12m: number[];
  last_updated: string;
}

export interface ExpenseBreakdown {
  breakdown: Record<string, number>;
  trend: Record<string, number[]>;
  movers: Array<{
    category: string;
    pct_change: number;
    amount: number;
  }>;
  total: number;
  period_months: number;
  last_updated: string;
}

export interface Scorecard {
  cash_balance: number;
  monthly_burn: number;
  runway_months: number;
  mrr: number;
  churn_rate: number;
  burn_multiple: number;
  magic_number: number;
  cac_payback_months: number;
  gross_margin_pct: number;
  last_updated: string;
}

export interface Alert {
  id: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  alert_type: 'spike' | 'trend' | 'duplicate' | 'new_vendor';
  category: string;
  description: string;
  amount: number | null;
  baseline: number | null;
  delta_pct: number | null;
  runway_impact: number | null;
  suggested_owner: string | null;
  status: 'active' | 'dismissed' | 'resolved';
  created_at: string;
  updated_at: string;
}

export interface AlertsResponse {
  alerts: Alert[];
  total: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  last_scan_at: string | null;
  filtered: {
    severity: string | null;
    category: string | null;
    limit: number;
  };
}

export interface ScanNowResponse {
  task_id: string;
  status: 'queued' | 'running';
  message: string;
}

export interface ScanStatusResponse {
  task_id: string;
  status: 'pending' | 'running' | 'success' | 'failure';
  alerts_found: number;
  run_at: string;
  completed_at: string | null;
  error: string | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatHistory {
  session_id: string;
  messages: ChatMessage[];
  company: string;
  created_at: string;
  updated_at: string;
}

export interface ChatRequest {
  query: string;
  session_id?: string;
  company?: string;
}

export interface ChatResponse {
  session_id: string;
  response: string;
  tool_calls: Array<{
    tool: string;
    args: Record<string, unknown>;
  }>;
  thinking_time_ms: number;
}

// ============================================================================
// FETCHER FUNCTION
// ============================================================================

export async function fetchAPI<T>(
  path: string,
  options?: RequestInit
): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!res.ok) {
      console.error(`API Error: ${res.status} ${res.statusText}`);
      return null;
    }

    return (await res.json()) as T;
  } catch (error) {
    console.error(`Fetch error: ${path}`, error);
    return null;
  }
}

// ============================================================================
// API ENDPOINTS
// ============================================================================

export const API = {
  // Financial metrics
  getCashBalance: () => fetchAPI<CashBalance>('/cash-balance'),
  getBurnRate: (periodDays = 30) =>
    fetchAPI<BurnRate>(`/burn-rate?period=${periodDays}`),
  getRunway: () => fetchAPI<Runway>('/runway'),
  getRevenue: () => fetchAPI<Revenue>('/revenue'),
  getExpenses: (months = 3) =>
    fetchAPI<ExpenseBreakdown>(`/expenses?months=${months}`),
  getScorecard: () => fetchAPI<Scorecard>('/scorecard'),

  // Alerts
  getAlerts: (severity?: string, category?: string, limit = 20) => {
    const params = new URLSearchParams();
    if (severity) params.append('severity', severity);
    if (category) params.append('category', category);
    params.append('limit', limit.toString());
    return fetchAPI<AlertsResponse>(`/alerts?${params.toString()}`);
  },
  scanNow: () => fetchAPI<ScanNowResponse>('/alerts/scan-now', { method: 'POST' }),
  getScanStatus: (taskId: string) =>
    fetchAPI<ScanStatusResponse>(`/alerts/scan-status/${taskId}`),
  dismissAlert: (alertId: string) =>
    fetchAPI<{ status: string }>(`/alerts/${alertId}/dismiss`, { method: 'PATCH' }),

  // Agent chat
  getHistory: (sessionId: string) =>
    fetchAPI<ChatHistory>(`/agent/history/${sessionId}`),
};

// ============================================================================
// STREAMING CHAT
// ============================================================================

export async function* streamChat(
  query: string,
  sessionId?: string
): AsyncGenerator<string, void, unknown> {
  const params = new URLSearchParams({ query });
  if (sessionId) params.append('session_id', sessionId);

  try {
    const res = await fetch(`${API_BASE}/agent/chat/stream?${params.toString()}`);

    if (!res.ok) {
      throw new Error(`Stream error: ${res.status}`);
    }

    const reader = res.body?.getReader();
    if (!reader) throw new Error('No reader available');

    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          try {
            const json = JSON.parse(data);
            if (json.done) {
              return;
            }
            if (json.text) {
              yield json.text;
            }
          } catch {
            // Skip invalid JSON
          }
        }
      }
    }
  } catch (error) {
    console.error('Stream error:', error);
    throw error;
  }
}
