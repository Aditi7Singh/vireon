'use client';

import React from 'react';
import { useFinancialDataAll } from '@/hooks/useFinancialDataWithErrorHandling';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface OperationsPageProps {
  companyId: string;
}

export default function OperationsPage({ companyId }: OperationsPageProps) {
  const {
    forecast, collections, invoiceQueue, invoiceDso,
    fxRates, monitor, isLoading, errors, reload,
  } = useFinancialDataAll(companyId);

  const ErrorAlert = ({ error }: { error: string }) => (
    <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 flex items-center gap-2">
      <AlertCircle className="h-4 w-4 text-red-600 shrink-0" />
      <span className="text-sm text-red-700">{error}</span>
    </div>
  );

  const LoadingSkeleton = () => (
    <div className="space-y-4">
      {[1, 2, 3].map(i => <div key={i} className="h-24 bg-gray-200 rounded animate-pulse" />)}
    </div>
  );

  if (isLoading) {
    return (
      <div className="p-8 space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold">Operations Center</h1>
          <button disabled className="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm opacity-50">
            <RefreshCw className="h-4 w-4" /> Loading...
          </button>
        </div>
        <LoadingSkeleton />
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Operations Center</h1>
        <button onClick={reload} disabled={isLoading} className="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm hover:bg-gray-50 disabled:opacity-50">
          <RefreshCw className="h-4 w-4" /> Reload All Data
        </button>
      </div>

      {errors.length > 0 && (
        <div className="space-y-2">
          {errors.map((error, idx) => <ErrorAlert key={idx} error={error} />)}
        </div>
      )}

      {[
        { title: "Cash Runway Forecast", section: forecast, metrics: [
          { label: "Current Cash (INR)", value: forecast.data?.current_cash_inr, format: "currency" as const },
          { label: "Runway", value: forecast.data?.runway_months, format: "months" as const },
        ]},
        { title: "Collections & Payables", section: collections, metrics: [
          { label: "AR Total Open", value: collections.data?.ar?.total_open, format: "currency" as const },
          { label: "AP Total Open", value: collections.data?.ap?.total_open, format: "currency" as const },
        ]},
        { title: "Invoice Queue", section: invoiceQueue, metrics: [
          { label: "Queue Count", value: invoiceQueue.data?.count, format: "number" as const },
        ]},
        { title: "DSO", section: invoiceDso, metrics: [
          { label: "DSO (Days)", value: invoiceDso.data?.dso_days, format: "number" as const },
          { label: "Open AR", value: invoiceDso.data?.open_ar, format: "currency" as const },
        ]},
        { title: "Forecast Monitor", section: monitor, metrics: [
          { label: "Samples", value: monitor.data?.samples, format: "number" as const },
          { label: "MAPE (%)", value: monitor.data?.mape_cash, format: "percent" as const },
        ]},
      ].map(({ title, section, metrics }) => (
        <div key={title} className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-xl font-bold">{title}</h2>
              {section.error && <p className="text-sm text-red-600 mt-1">{section.error}</p>}
            </div>
            <button onClick={section.reload} disabled={section.isLoading} className="rounded-lg border p-1.5 hover:bg-gray-50 disabled:opacity-50">
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
          {section.isLoading ? (
            <div className="h-20 bg-gray-200 rounded animate-pulse" />
          ) : (
            <div className="grid grid-cols-2 gap-4">
              {metrics.map(m => <MetricCard key={m.label} label={m.label} value={m.value} format={m.format} />)}
            </div>
          )}
        </div>
      ))}

      {/* FX Rates */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-bold">FX Rates</h2>
            {fxRates.error && <p className="text-sm text-red-600 mt-1">{fxRates.error}</p>}
          </div>
          <button onClick={fxRates.reload} disabled={fxRates.isLoading} className="rounded-lg border p-1.5 hover:bg-gray-50 disabled:opacity-50">
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
        {fxRates.isLoading ? (
          <div className="h-20 bg-gray-200 rounded animate-pulse" />
        ) : (
          <table className="w-full text-sm">
            <thead><tr className="border-b"><th className="text-left py-2">From</th><th className="text-left py-2">To</th><th className="text-right py-2">Rate</th></tr></thead>
            <tbody>
              {fxRates.data?.rates?.slice(0, 5).map((rate: any, idx: number) => (
                <tr key={idx} className="border-b">
                  <td className="py-2">{rate.base_currency}</td>
                  <td className="py-2">{rate.target_currency}</td>
                  <td className="text-right py-2">{rate.exchange_rate?.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function MetricCard({ label, value, format = 'text', unit = '' }: {
  label: string; value: any;
  format?: 'text' | 'number' | 'currency' | 'percent' | 'date' | 'months';
  unit?: string;
}) {
  const fmt = () => {
    if (value == null) return 'N/A';
    switch (format) {
      case 'currency': return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(Number(value));
      case 'number':   return new Intl.NumberFormat('en-IN').format(Number(value));
      case 'percent':  return Number(value).toFixed(2) + '%';
      case 'date':     return new Date(value).toLocaleDateString('en-IN');
      case 'months':   return Number(value).toFixed(1) + ' ' + unit;
      default:         return String(value);
    }
  };
  return (
    <div className="border rounded p-4 bg-gray-50">
      <p className="text-sm text-gray-600 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{fmt()}</p>
    </div>
  );
}
