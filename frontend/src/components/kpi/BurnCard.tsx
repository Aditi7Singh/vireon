'use client';

import { BurnRate } from '@/lib/api';
import { formatCurrency, formatPercent } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Flame } from 'lucide-react';

interface Props {
  data: BurnRate | null;
  loading: boolean;
}

export function BurnCard({ data, loading }: Props) {
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

  const trendPercentage = data.trend.comparison_percent;
  const isBurning = trendPercentage > 0;

  return (
    <div className="p-6 rounded-lg border border-cfo-border bg-cfo-surface">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs font-medium text-cfo-muted uppercase tracking-wide">
          Monthly Burn
        </p>
        <Flame className={cn(
          'w-4 h-4',
          isBurning ? 'text-red-400' : 'text-green-400'
        )} />
      </div>

      {/* Main Value */}
      <div className="mb-4">
        <p className="text-3xl font-bold text-white">
          {formatCurrency(data.monthly_burn)}
        </p>
      </div>

      {/* Breakdown */}
      <div className="space-y-2 text-xs text-cfo-muted mb-4 pb-4 border-b border-cfo-border">
        <div className="flex justify-between">
          <span>Trend</span>
          <span className={cn(
            'font-medium',
            isBurning ? 'text-red-400' : 'text-green-400'
          )}>
            {isBurning ? '+' : ''}{formatPercent(trendPercentage)}
          </span>
        </div>
      </div>

      {/* Trend Indicator */}
      <div className="flex items-center gap-2">
        {isBurning ? (
          <TrendingUp className="w-4 h-4 text-red-400" />
        ) : (
          <TrendingDown className="w-4 h-4 text-green-400" />
        )}
        <span className={cn(
          'text-xs font-medium',
          isBurning ? 'text-red-400' : 'text-green-400'
        )}>
          {isBurning ? 'Increasing' : 'Decreasing'} vs last month
        </span>
      </div>
    </div>
  );
}
