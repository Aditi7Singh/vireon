'use client';

import { useMemo, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Runway } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface ChartData {
  month: string;
  actual: number;
  projected: number;
}

type Period = '6M' | '12M' | '24M';

interface Props {
  data: Runway | null;
}

export function RunwayAreaChart({ data }: Props) {
  const [period, setPeriod] = useState<Period>('12M');

  const chartData = useMemo(() => {
    if (!data) return [];

    const now = new Date();
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    const months: ChartData[] = [];
    const historicalMonths = period === '6M' ? 6 : period === '12M' ? 12 : 24;
    const projectedMonths = period === '6M' ? 6 : 6; // Always show 6 months projected

    // Generate historical data (simulated)
    const currentCash = data.cash_available;
    const monthlyBurn = data.monthly_burn;

    for (let i = -historicalMonths; i <= projectedMonths; i++) {
      const date = new Date(now);
      date.setMonth(date.getMonth() + i);
      const monthIdx = date.getMonth();
      const monthLabel = monthNames[monthIdx];

      // Historical data: simulated backwards from current cash
      const actualCash = i <= 0 ? currentCash + (Math.abs(i) * monthlyBurn) : null;
      
      // Projected data: forward from current cash with burn
      const projectedCash = i >= 0 ? currentCash - (i * monthlyBurn) : null;

      months.push({
        month: monthLabel,
        actual: actualCash ?? 0,
        projected: projectedCash ?? 0,
      });
    }

    return months;
  }, [data, period]);

  if (!data) {
    return (
      <div className="p-6 rounded-lg border border-cfo-border bg-cfo-surface h-96 animate-pulse">
        <div className="h-full bg-cfo-surface2 rounded" />
      </div>
    );
  }

  const todayMonth = new Date().toLocaleString('default', { month: 'short' });

  return (
    <div className="p-6 rounded-lg border border-cfo-border bg-cfo-surface">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-white">Cash Runway — 12 Month View</h2>
        <div className="flex gap-2">
          {(['6M', '12M', '24M'] as const).map((p) => (
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

      {/* Chart */}
      <div style={{ width: '100%', height: 360 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4ade80" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#4ade80" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorProjected" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#808080" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#808080" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
            <XAxis dataKey="month" stroke="#718096" />
            <YAxis 
              stroke="#718096"
              tickFormatter={(value) => {
                if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
                if (value >= 1000) return `$${(value / 1000).toFixed(0)}k`;
                return `$${value}`;
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1a202c',
                border: '1px solid #2d3748',
                borderRadius: '0.5rem',
              }}
              formatter={(value: number) => formatCurrency(value)}
            />
            <Legend />
            <ReferenceLine 
              y={0} 
              stroke="#ff4d4f" 
              strokeWidth={2}
              label={{ value: 'Cash Out', position: 'right', fill: '#ff4d4f' }}
            />
            <ReferenceLine 
              x={todayMonth}
              stroke="white"
              strokeDasharray="5 5"
              strokeWidth={1}
              label={{ value: 'Today', position: 'top', fill: 'white' }}
            />
            <Area 
              type="monotone" 
              dataKey="actual" 
              stroke="#4ade80" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorActual)"
              name="Actual Cash"
            />
            <Area 
              type="monotone" 
              dataKey="projected" 
              stroke="#808080" 
              strokeWidth={2}
              strokeDasharray="5 5"
              fillOpacity={1} 
              fill="url(#colorProjected)"
              name="Projected Cash"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

