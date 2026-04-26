/**
 * Enhanced Hook for Financial Data Loading with Comprehensive Error Handling
 * 
 * This hook demonstrates best practices for:
 * - Using the enhanced API client with error handling
 * - Managing loading/error/success states
 * - Providing user feedback for network failures
 * - Automatic retries and fallback values
 * 
 * Usage Example:
 * ```
 * const { data, isLoading, error, reload } = useFinancialDataWithErrorHandling(
 *   () => api.getForecastEnsemble(companyId),
 *   { initial: defaultForecast, context: "Forecast Ensemble" }
 * );
 * ```
 */

import { useState, useEffect, useCallback } from "react";
import { api, APIError } from "@/lib/api";

export interface UseDataOptions<T> {
  initial: T;
  context: string;
  retryOnError?: boolean;
  retryDelayMs?: number;
}

export interface UseDataResult<T> {
  data: T;
  isLoading: boolean;
  error: string | null;
  reload: () => void;
  clearError: () => void;
}

/**
 * Generic hook for loading data with full error handling
 * 
 * @param fetchFn - Async function that fetches data
 * @param options - Configuration for data loading
 * @returns Object with data, loading state, error, and control functions
 */
export function useFinancialDataWithErrorHandling<T>(
  fetchFn: () => Promise<T>,
  options: UseDataOptions<T>
): UseDataResult<T> {
  const { initial, context, retryOnError = true, retryDelayMs = 5000 } = options;
  
  const [data, setData] = useState<T>(initial);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const handleFetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await fetchFn();
      setData(result);
      setRetryCount(0);
      console.info(`[${context}] Data loaded successfully`);
    } catch (err) {
      const errorMessage = formatErrorMessage(err, context);
      setError(errorMessage);
      console.error(`[${context}] Load failed:`, err);

      // Automatic retry on transient errors
      if (retryOnError && isTransientError(err)) {
        console.warn(`[${context}] Transient error detected, will retry in ${retryDelayMs}ms...`);
        setRetryCount(prev => prev + 1);
        
        // Don't retry more than 3 times to avoid infinite loops
        if (retryCount < 3) {
          setTimeout(() => {
            handleFetch();
          }, retryDelayMs);
        } else {
          console.error(`[${context}] Max retries exceeded (3)`);
          setError(`${errorMessage} - Max retries exceeded. Please try again.`);
        }
      }
    } finally {
      setIsLoading(false);
    }
  }, [fetchFn, context, retryOnError, retryDelayMs, retryCount]);

  // Load data on mount
  useEffect(() => {
    handleFetch();
  }, [handleFetch]);

  const reload = useCallback(async () => {
    setRetryCount(0);
    await handleFetch();
  }, [handleFetch]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    data,
    isLoading,
    error,
    reload,
    clearError,
  };
}

/**
 * Specialized hook for ForecastEnsemble data
 */
export function useForecastEnsembleData(companyId: string) {
  const defaultForecast = {
    current_cash_inr: 0,
    runway_months: 0,
    runway_date: new Date().toISOString(),
    model_used: "unknown",
    weights: {},
    monthly_projections: [],
    last_updated: new Date().toISOString(),
  };

  return useFinancialDataWithErrorHandling(
    () => api.getForecastEnsemble(companyId),
    {
      initial: defaultForecast,
      context: "Forecast Ensemble",
      retryOnError: true,
    }
  );
}

/**
 * Specialized hook for Collections Aging data
 */
export function useCollectionsAgingData(companyId: string) {
  const defaultCollections = {
    as_of: new Date().toISOString(),
    ar: { buckets: {}, total_open: 0 },
    ap: { buckets: {}, total_open: 0 },
    overdue_receivables: [],
  };

  return useFinancialDataWithErrorHandling(
    () => api.getCollectionsAging(companyId),
    {
      initial: defaultCollections,
      context: "Collections Aging",
      retryOnError: true,
    }
  );
}

/**
 * Specialized hook for Invoice Queue data
 */
export function useInvoiceQueueData(companyId: string) {
  const defaultQueue = {
    as_of: new Date().toISOString(),
    count: 0,
    queue: [],
  };

  return useFinancialDataWithErrorHandling(
    () => api.getInvoiceQueue(companyId),
    {
      initial: defaultQueue,
      context: "Invoice Queue",
      retryOnError: true,
    }
  );
}

/**
 * Specialized hook for Invoice DSO data
 */
export function useInvoiceDsoData(companyId: string) {
  const defaultDso = {
    as_of: new Date().toISOString(),
    lookback_days: 90,
    open_ar: 0,
    period_credit_sales: 0,
    average_daily_sales: 0,
    dso_days: 0,
  };

  return useFinancialDataWithErrorHandling(
    () => api.getInvoiceDso(companyId),
    {
      initial: defaultDso,
      context: "Invoice DSO",
      retryOnError: true,
    }
  );
}

/**
 * Specialized hook for FX Rates data
 */
export function useFxRatesData() {
  const defaultRates = {
    count: 0,
    rates: [],
  };

  return useFinancialDataWithErrorHandling(
    () => api.getFxRates(),
    {
      initial: defaultRates,
      context: "FX Rates",
      retryOnError: true,
    }
  );
}

/**
 * Specialized hook for Forecast Monitor data
 */
export function useForecastMonitorData(companyId: string) {
  const defaultMonitor = {
    company_id: companyId,
    samples: 0,
    mae_cash: 0,
    mape_cash: 0,
    health: "unknown",
    message: "Data not available",
  };

  return useFinancialDataWithErrorHandling(
    () => api.getForecastMonitor(companyId),
    {
      initial: defaultMonitor,
      context: "Forecast Monitor",
      retryOnError: true,
    }
  );
}

// ============================================================================
// Helper Functions for Error Handling
// ============================================================================

/**
 * Determines if an error is transient (should be retried)
 */
function isTransientError(error: unknown): boolean {
  if (error instanceof APIError) {
    // Retry on 5xx server errors and 429 rate limits
    return error.status >= 500 || error.status === 429;
  }

  if (error instanceof Error) {
    const msg = error.message.toLowerCase();
    return (
      msg.includes("network error") ||
      msg.includes("timeout") ||
      msg.includes("unable to reach")
    );
  }

  return false;
}

/**
 * Formats error messages for user display
 */
function formatErrorMessage(error: unknown, context: string): string {
  if (error instanceof APIError) {
    if (error.status === 404) {
      return `${context}: Data not found on the server.`;
    }
    if (error.status === 401 || error.status === 403) {
      return `${context}: You don't have permission to access this data.`;
    }
    if (error.status >= 500) {
      return `${context}: Server error. Please try again in a moment.`;
    }
    if (error.status === 429) {
      return `${context}: Too many requests. Please wait a moment before retrying.`;
    }
    return `${context}: ${error.detail}`;
  }

  if (error instanceof Error) {
    if (error.message.includes("timeout")) {
      return `${context}: Request timed out. The server may be slow. Please try again.`;
    }
    if (error.message.includes("Network error")) {
      return `${context}: ${error.message}`;
    }
    if (error.message.includes("Failed to parse")) {
      return `${context}: Invalid response format from server.`;
    }
    return `${context}: ${error.message}`;
  }

  return `${context}: An unknown error occurred.`;
}

// ============================================================================
// Multi-Data Loader Hook
// ============================================================================

/**
 * Load multiple data sources in parallel with combined error handling
 */
export function useFinancialDataAll(companyId: string) {
  const forecast = useForecastEnsembleData(companyId);
  const collections = useCollectionsAgingData(companyId);
  const invoiceQueue = useInvoiceQueueData(companyId);
  const invoiceDso = useInvoiceDsoData(companyId);
  const fxRates = useFxRatesData();
  const monitor = useForecastMonitorData(companyId);

  // Combine all errors
  const errors = [
    forecast.error,
    collections.error,
    invoiceQueue.error,
    invoiceDso.error,
    fxRates.error,
    monitor.error,
  ].filter(e => e !== null);

  // Consider loading only if at least one is still loading
  const isLoading =
    forecast.isLoading ||
    collections.isLoading ||
    invoiceQueue.isLoading ||
    invoiceDso.isLoading ||
    fxRates.isLoading ||
    monitor.isLoading;

  // Reload all
  const reload = useCallback(async () => {
    await Promise.all([
      forecast.reload(),
      collections.reload(),
      invoiceQueue.reload(),
      invoiceDso.reload(),
      fxRates.reload(),
      monitor.reload(),
    ]);
  }, [forecast, collections, invoiceQueue, invoiceDso, fxRates, monitor]);

  return {
    forecast,
    collections,
    invoiceQueue,
    invoiceDso,
    fxRates,
    monitor,
    isLoading,
    errors,
    reload,
  };
}
