'use client';

import { Revenue } from '@/lib/api';
import { formatCurrency, formatPercent } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';

interface Props {
  data: Revenue | null;
  loading: boolean;
}

export function MrrCard({ data, loading }: Props) {
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

  const isGrowing = data.growth_pct >= 0;

  return (
    <div className="p-6 rounded-lg border border-cfo-border bg-cfo-surface">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs font-medium text-cfo-muted uppercase tracking-wide">
          Monthly Recurring Revenue
        </p>
        <BarChart3 className="w-4 h-4 text-cfo-accent" />
      </div>

      {/* Main Value */}
      <div className="mb-4">
        <p className="text-3xl font-bold text-white">
          {formatCurrency(data.mrr)}
        </p>
      </div>

      {/* Breakdown */}
      <div className="space-y-2 text-xs text-cfo-muted mb-4 pb-4 border-b border-cfo-border">
        <div className="flex justify-between">
          <span>Growth</span>
          <span className={cn(
            'font-medium',
            isGrowing ? 'text-green-400' : 'text-red-400'
          )}>
            {isGrowing ? '+' : ''}{formatPercent(data.growth_pct)}
          </span>
        </div>
        <div className="flex justify-between">
          <span>Churn</span>
          <span className="text-white font-medium">{formatPercent(data.churn_rate)}</span>
        </div>
      </div>

      {/* Growth Indicator */}
      <div className="flex items-center gap-2">
        {isGrowing ? (
          <TrendingUp className="w-4 h-4 text-green-400" />
        ) : (
          <TrendingDown className="w-4 h-4 text-red-400" />
        )}
        <span className={cn(
          'text-xs font-medium',
          isGrowing ? 'text-green-400' : 'text-red-400'
        )}>
          {isGrowing ? 'Growing' : 'Declining'}
        </span>
      </div>
    </div>
  );
}
