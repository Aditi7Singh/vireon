'use client';

import { useState, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useRevenue } from '@/hooks/useFinancialData';
import { formatCurrency, formatPercent } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface ChartData {
  month: string;
  mrr: number;
  projectedMrr: number;
}

type Period = '6M' | '12M';

export function RevenueLineChart() {
  const { data: revenueData, isLoading } = useRevenue();
  const [period, setPeriod] = useState<Period>('12M');

  const chartData = useMemo(() => {
    if (!revenueData?.trend_12m || !Array.isArray(revenueData.trend_12m)) return [];

    const now = new Date();
    const months: ChartData[] = [];

    // Generate month labels
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    // Get historical data (trend_12m contains 12 months of MRR data)
    const historyLength = period === '6M' ? 6 : 12;
    const trendData = Array.isArray(revenueData.trend_12m) ? revenueData.trend_12m.slice(-historyLength) : [];

    // Calculate growth rate for projection
    const growthRate = (revenueData.growth_pct || 0) / 100;

    // Build chart data
    for (let i = 0; i < historyLength; i++) {
      const date = new Date(now);
      date.setMonth(date.getMonth() - (historyLength - 1 - i));
      const monthIdx = date.getMonth();
      const monthLabel = monthNames[monthIdx];

      const mrrValue = trendData[i] || revenueData.mrr;
      const projectedValue = mrrValue * Math.pow(1 + growthRate, 1);

      months.push({
        month: monthLabel,
        mrr: Math.round(mrrValue),
        projectedMrr: Math.round(projectedValue),
      });
    }

    return months;
  }, [revenueData, period]);

  if (isLoading) {
    return (
      <div className="p-6 rounded-lg border border-cfo-border bg-cfo-surface h-96 animate-pulse">
        <div className="h-full bg-cfo-surface2 rounded" />
      </div>
    );
  }

  return (
    <div className="p-6 rounded-lg border border-cfo-border bg-cfo-surface">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-white">Revenue Trend</h2>
        <div className="flex gap-2">
          {(['6M', '12M'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={cn(
                'px-3 py-1 text-xs font-medium rounded transition-colors',
                period === p
                  ? 'bg-cfo-accent text-black'
                  : 'bg-cfo-surface2 text-cfo-muted hover:bg-cfo-border'
              )}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Row */}
      <div className="grid grid-cols-3 gap-4 mb-6 p-4 bg-cfo-surface2 rounded-lg">
        <div>
          <p className="text-xs text-cfo-muted mb-1">MRR</p>
          <p className="text-xl font-bold text-white">{formatCurrency(revenueData?.mrr)}</p>
        </div>
        <div>
          <p className="text-xs text-cfo-muted mb-1">ARR</p>
          <p className="text-xl font-bold text-white">{formatCurrency(revenueData?.arr)}</p>
        </div>
        <div>
          <p className="text-xs text-cfo-muted mb-1">Growth Rate</p>
          <p className={cn(
            'text-xl font-bold',
            (revenueData?.growth_pct || 0) >= 0 ? 'text-green-400' : 'text-red-400'
          )}>
            {formatPercent(revenueData?.growth_pct)}
          </p>
        </div>
      </div>

      {/* Chart */}
      <div style={{ width: '100%', height: 320 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
            <XAxis dataKey="month" stroke="#718096" />
            <YAxis stroke="#718096" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1a202c',
                border: '1px solid #2d3748',
                borderRadius: '0.5rem',
              }}
              formatter={(value: number) => formatCurrency(value)}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="mrr" 
              stroke="#4ade80" 
              strokeWidth={2}
              name="MRR (Actual)"
              dot={false}
            />
            <Line 
              type="monotone" 
              dataKey="projectedMrr" 
              stroke="#808080" 
              strokeWidth={2}
              strokeDasharray="5 5"
              name="Projected MRR"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
