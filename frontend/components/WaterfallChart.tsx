"use client";

/**
 * WaterfallChart
 * ==============
 * Month-over-month Burn Analysis Waterfall.
 * Each month shows: start balance → +revenue → −burn → end balance
 * Clicking on a bar triggers onBarClick with the category name.
 */

import React, { useState } from "react";
import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface WaterfallRow {
  month: string;
  starting_cash: number;
  revenue: number;
  burn: number;
  net_change: number;
  ending_cash: number;
}

interface WaterfallChartProps {
  data: WaterfallRow[];
  onBarClick?: (month: string, type: "revenue" | "burn") => void;
  height?: number;
}

function formatShort(v: number): string {
  const abs = Math.abs(v);
  const sign = v < 0 ? "-" : "";
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(0)}K`;
  return `${sign}$${abs.toFixed(0)}`;
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "#fffdf7",
        border: "1px solid #ddd2c2",
        borderRadius: 12,
        padding: "10px 14px",
        fontSize: 12,
        boxShadow: "0 4px 16px rgba(60,45,24,0.12)",
      }}
    >
      <p style={{ fontWeight: 600, marginBottom: 6, color: "#2a2018" }}>{label}</p>
      {payload.map((p, i) => (
        <div key={i} style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
          <span style={{ color: "#7a6252" }}>{p.name}</span>
          <span style={{ fontWeight: 600, color: p.color }}>{formatShort(p.value)}</span>
        </div>
      ))}
    </div>
  );
};

export default function WaterfallChart({
  data,
  onBarClick,
  height = 320,
}: WaterfallChartProps) {
  const [activeMonth, setActiveMonth] = useState<string | null>(null);

  // Recharts waterfall trick: transparent "base" bar + colored delta bars
  const chartData = data.map((row) => {
    const revenueBase = row.starting_cash;
    const burnBase = row.starting_cash + row.revenue;
    return {
      month: row.month,
      // invisible bases
      revenueBase,
      burnBase,
      // visible segments
      revenue: row.revenue,
      burn: row.burn,
      ending_cash: row.ending_cash,
      net_change: row.net_change,
    };
  });

  const minCash = Math.min(...data.map((d) => Math.min(d.starting_cash, d.ending_cash)));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart
        data={chartData}
        margin={{ top: 12, right: 20, left: 10, bottom: 0 }}
        barGap={2}
      >
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="#ede8df"
          vertical={false}
        />
        <XAxis
          dataKey="month"
          tickLine={false}
          axisLine={{ stroke: "#e2d9cc" }}
          tick={{ fill: "#7a6252", fontSize: 12, fontWeight: 500 }}
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          tick={{ fill: "#7a6252", fontSize: 12 }}
          tickFormatter={formatShort}
          domain={[Math.max(0, minCash * 0.85), "auto"]}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 12, color: "#7a6252", paddingTop: 8 }}
        />
        <ReferenceLine y={0} stroke="#c2b5a4" strokeDasharray="4 2" />

        {/* Invisible base for revenue bars */}
        <Bar
          dataKey="revenueBase"
          stackId="waterfall"
          fill="transparent"
          legendType="none"
          isAnimationActive={false}
        />

        {/* Revenue bar (green) */}
        <Bar
          dataKey="revenue"
          stackId="waterfall"
          name="Revenue"
          radius={[3, 3, 0, 0]}
          cursor="pointer"
          onClick={(entry) => {
            setActiveMonth(entry.month);
            onBarClick?.(entry.month, "revenue");
          }}
        >
          {chartData.map((entry, i) => (
            <Cell
              key={i}
              fill={activeMonth === entry.month ? "#059669" : "#34d399"}
              opacity={activeMonth && activeMonth !== entry.month ? 0.5 : 1}
            />
          ))}
        </Bar>

        {/* Gap between revenue and burn (transparent) */}
        <Bar
          dataKey="burnBase"
          stackId="waterfall2"
          fill="transparent"
          legendType="none"
          isAnimationActive={false}
        />

        {/* Burn bar (red) */}
        <Bar
          dataKey="burn"
          stackId="waterfall2"
          name="Burn"
          radius={[3, 3, 0, 0]}
          cursor="pointer"
          onClick={(entry) => {
            setActiveMonth(entry.month);
            onBarClick?.(entry.month, "burn");
          }}
        >
          {chartData.map((entry, i) => (
            <Cell
              key={i}
              fill={activeMonth === entry.month ? "#dc2626" : "#f87171"}
              opacity={activeMonth && activeMonth !== entry.month ? 0.5 : 1}
            />
          ))}
        </Bar>
      </ComposedChart>
    </ResponsiveContainer>
  );
}
