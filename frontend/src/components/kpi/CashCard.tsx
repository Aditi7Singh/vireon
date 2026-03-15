'use client';

import { CashBalance } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';

interface Props {
  data: CashBalance | null;
  loading: boolean;
  trend?: { value: number; label: string };
}

export function CashCard({ data, loading, trend }: Props) {
  if (loading) {
    return (
      <div className="p-6 rounded-lg bg-cfo-surface border border-cfo-border animate-pulse">
        <div className="h-24 bg-cfo-surface2 rounded" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6 rounded-lg bg-cfo-surface border border-cfo-border">
        <p className="text-sm text-cfo-muted">—</p>
      </div>
    );
  }

  return (
    <div className="p-6 rounded-lg bg-cfo-surface border border-cfo-border">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs font-medium text-cfo-muted uppercase tracking-wide">
          Net Cash
        </p>
        <DollarSign className="w-4 h-4 text-cfo-accent" />
      </div>

      {/* Main Value */}
      <div className="mb-4">
        <p className="text-3xl font-bold text-white">
          {formatCurrency(data.net_cash)}
        </p>
      </div>

      {/* Breakdown */}
      <div className="space-y-2 text-xs text-cfo-muted mb-4 pb-4 border-b border-cfo-border">
        <div className="flex justify-between">
          <span>AR</span>
          <span className="text-white font-medium">{formatCurrency(data.ar)}</span>
        </div>
        <div className="flex justify-between">
          <span>AP</span>
          <span className="text-white font-medium">{formatCurrency(data.ap)}</span>
        </div>
      </div>

      {/* Trend Indicator */}
      {trend && (
        <div className="flex items-center gap-2">
          {trend.value >= 0 ? (
            <TrendingUp className="w-4 h-4 text-green-400" />
          ) : (
            <TrendingDown className="w-4 h-4 text-red-400" />
          )}
          <span
            className={cn(
              'text-xs font-medium',
              trend.value >= 0 ? 'text-green-400' : 'text-red-400'
            )}
          >
            {trend.value >= 0 ? '+' : ''}{trend.value}% {trend.label}
          </span>
        </div>
      )}
    </div>
  );
}
