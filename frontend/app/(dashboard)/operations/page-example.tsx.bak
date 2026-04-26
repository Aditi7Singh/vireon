/**
 * ================================================================
 * VIREON OPERATIONS PAGE - ERROR HANDLING EXAMPLE
 * ================================================================
 * 
 * This file demonstrates best practices for integrating the 
 * enhanced API client with proper error handling, loading states,
 * and user feedback in React components.
 * 
 * Key Concepts:
 * 1. Use the new useFinancialDataWithErrorHandling hook
 * 2. Display loading states while data is fetching
 * 3. Show clear error messages on failures
 * 4. Provide reload buttons for user recovery
 * 5. Gracefully degrade to default/empty states
 */

'use client';

import React from 'react';
import { useFinancialDataAll } from '@/hooks/useFinancialDataWithErrorHandling';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface OperationsPageProps {
  companyId: string;
}

export default function OperationsPage({ companyId }: OperationsPageProps) {
  // Use the enhanced hook that loads all financial data with error handling
  const {
    forecast,
    collections,
    invoiceQueue,
    invoiceDso,
    fxRates,
    monitor,
    isLoading,
    errors,
    reload,
  } = useFinancialDataAll(companyId);

  // ================================================================
  // ERROR DISPLAY COMPONENT
  // ================================================================
  const ErrorAlert = ({ error, onDismiss }: { error: string; onDismiss: () => void }) => (
    <Alert variant="destructive" className="mb-4">
      <AlertCircle className="h-4 w-4" />
      <AlertDescription className="ml-2">
        <div className="flex justify-between items-center">
          <span>{error}</span>
          <Button
            variant="outline"
            size="sm"
            onClick={onDismiss}
            className="ml-4"
          >
            Dismiss
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  );

  // ================================================================
  // LOADING SKELETON COMPONENT
  // ================================================================
  const LoadingSkeleton = () => (
    <div className="space-y-4">
      {[1, 2, 3].map(i => (
        <div
          key={i}
          className="h-24 bg-gray-200 rounded animate-pulse"
        />
      ))}
    </div>
  );

  // ================================================================
  // RENDER LOADING STATE
  // ================================================================
  if (isLoading) {
    return (
      <div className="p-8 space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold">Operations Center</h1>
          <Button variant="outline" disabled>
            <RefreshCw className="h-4 w-4 mr-2" />
            Loading...
          </Button>
        </div>
        <LoadingSkeleton />
      </div>
    );
  }

  // ================================================================
  // RENDER ERRORS
  // ================================================================
  const hasErrors = errors.length > 0;

  // ================================================================
  // MAIN CONTENT
  // ================================================================
  return (
    <div className="p-8 space-y-6">
      {/* Header with reload button */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Operations Center</h1>
        <Button
          variant="outline"
          onClick={reload}
          disabled={isLoading}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Reload All Data
        </Button>
      </div>

      {/* Error alerts */}
      {hasErrors && (
        <div className="space-y-2">
          {errors.map((error, idx) => (
            <ErrorAlert
              key={idx}
              error={error}
              onDismiss={() => {
                // Could clear individual errors here
              }}
            />
          ))}
        </div>
      )}

      {/* Forecast Ensemble Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-bold">Cash Runway Forecast</h2>
            {forecast.error && (
              <p className="text-sm text-red-600 mt-1">{forecast.error}</p>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={forecast.reload}
            disabled={forecast.isLoading}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        {forecast.isLoading ? (
          <div className="h-20 bg-gray-200 rounded animate-pulse" />
        ) : (
          <div className="grid grid-cols-2 gap-4">
            <MetricCard
              label="Current Cash (INR)"
              value={forecast.data.current_cash_inr}
              format="currency"
            />
            <MetricCard
              label="Runway"
              value={forecast.data.runway_months}
              format="months"
              unit="months"
            />
            <MetricCard
              label="Model"
              value={forecast.data.model_used}
              format="text"
            />
            <MetricCard
              label="Last Updated"
              value={forecast.data.last_updated}
              format="date"
            />
          </div>
        )}
      </div>

      {/* Collections Aging Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-bold">Collections & Payables</h2>
            {collections.error && (
              <p className="text-sm text-red-600 mt-1">{collections.error}</p>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={collections.reload}
            disabled={collections.isLoading}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        {collections.isLoading ? (
          <div className="h-20 bg-gray-200 rounded animate-pulse" />
        ) : (
          <div className="grid grid-cols-2 gap-4">
            <MetricCard
              label="AR Total Open"
              value={collections.data.ar.total_open}
              format="currency"
            />
            <MetricCard
              label="AP Total Open"
              value={collections.data.ap.total_open}
              format="currency"
            />
            <MetricCard
              label="Overdue AR Items"
              value={collections.data.overdue_receivables.length}
              format="number"
            />
            <MetricCard
              label="As Of"
              value={collections.data.as_of}
              format="date"
            />
          </div>
        )}
      </div>

      {/* Invoice Queue Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-bold">Invoice Queue</h2>
            {invoiceQueue.error && (
              <p className="text-sm text-red-600 mt-1">{invoiceQueue.error}</p>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={invoiceQueue.reload}
            disabled={invoiceQueue.isLoading}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        {invoiceQueue.isLoading ? (
          <div className="h-20 bg-gray-200 rounded animate-pulse" />
        ) : (
          <div className="grid grid-cols-2 gap-4">
            <MetricCard
              label="Queue Count"
              value={invoiceQueue.data.count}
              format="number"
            />
            <MetricCard
              label="As Of"
              value={invoiceQueue.data.as_of}
              format="date"
            />
          </div>
        )}
      </div>

      {/* DSO Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-bold">Days Sales Outstanding (DSO)</h2>
            {invoiceDso.error && (
              <p className="text-sm text-red-600 mt-1">{invoiceDso.error}</p>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={invoiceDso.reload}
            disabled={invoiceDso.isLoading}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        {invoiceDso.isLoading ? (
          <div className="h-20 bg-gray-200 rounded animate-pulse" />
        ) : (
          <div className="grid grid-cols-3 gap-4">
            <MetricCard
              label="DSO (Days)"
              value={invoiceDso.data.dso_days}
              format="number"
              unit="days"
            />
            <MetricCard
              label="Open AR"
              value={invoiceDso.data.open_ar}
              format="currency"
            />
            <MetricCard
              label="Daily Sales Avg"
              value={invoiceDso.data.average_daily_sales}
              format="currency"
            />
          </div>
        )}
      </div>

      {/* FX Rates Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-bold">FX Rates</h2>
            {fxRates.error && (
              <p className="text-sm text-red-600 mt-1">{fxRates.error}</p>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={fxRates.reload}
            disabled={fxRates.isLoading}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        {fxRates.isLoading ? (
          <div className="h-20 bg-gray-200 rounded animate-pulse" />
        ) : (
          <div>
            <p className="text-sm text-gray-600 mb-4">
              {fxRates.data.count} exchange rates available
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">From</th>
                    <th className="text-left py-2">To</th>
                    <th className="text-right py-2">Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {fxRates.data.rates.slice(0, 5).map((rate, idx) => (
                    <tr key={idx} className="border-b">
                      <td className="py-2">{rate.base_currency}</td>
                      <td className="py-2">{rate.target_currency}</td>
                      <td className="text-right py-2">
                        {rate.exchange_rate.toFixed(4)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Forecast Monitor Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-bold">Forecast Quality Monitor</h2>
            {monitor.error && (
              <p className="text-sm text-red-600 mt-1">{monitor.error}</p>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={monitor.reload}
            disabled={monitor.isLoading}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        {monitor.isLoading ? (
          <div className="h-20 bg-gray-200 rounded animate-pulse" />
        ) : (
          <div className="grid grid-cols-2 gap-4">
            <MetricCard
              label="Samples"
              value={monitor.data.samples}
              format="number"
            />
            <MetricCard
              label="MAE (Cash)"
              value={monitor.data.mae_cash}
              format="currency"
            />
            <MetricCard
              label="MAPE (%)"
              value={monitor.data.mape_cash}
              format="percent"
            />
            <MetricCard
              label="Health"
              value={monitor.data.health}
              format="badge"
            />
          </div>
        )}
      </div>
    </div>
  );
}

// ================================================================
// GENERIC METRIC CARD COMPONENT
// ================================================================
function MetricCard({
  label,
  value,
  format = 'text',
  unit = '',
}: {
  label: string;
  value: any;
  format?: 'text' | 'number' | 'currency' | 'percent' | 'date' | 'months' | 'badge';
  unit?: string;
}) {
  const formatValue = () => {
    if (value === null || value === undefined) {
      return 'N/A';
    }

    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-IN', {
          style: 'currency',
          currency: 'INR',
        }).format(Number(value));
      case 'number':
        return new Intl.NumberFormat('en-IN').format(Number(value));
      case 'percent':
        return Number(value).toFixed(2) + '%';
      case 'date':
        return new Date(value).toLocaleDateString('en-IN');
      case 'months':
        return Number(value).toFixed(1) + ' ' + unit;
      case 'badge':
        return (
          <span className="inline-block px-2 py-1 rounded text-sm font-medium bg-blue-100 text-blue-800">
            {String(value).toUpperCase()}
          </span>
        );
      default:
        return String(value);
    }
  };

  return (
    <div className="border rounded p-4 bg-gray-50">
      <p className="text-sm text-gray-600 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{formatValue()}</p>
    </div>
  );
}
