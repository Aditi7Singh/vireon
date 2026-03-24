"use client";

import TopBar from "@/components/TopBar";
import { useRevenue, useAlerts } from "@/hooks/useFinancialData";
import { useAppStore } from "@/lib/store";
import { formatCurrency } from "@/lib/utils";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ArrowUpRight, Repeat, Sparkles, TrendingDown, TrendingUp, AlertCircle, Users } from "lucide-react";
import { 
  Card, 
  Title, 
  DonutChart, 
  BarChart, 
  Text, 
  Flex, 
  Badge, 
  List, 
  ListItem, 
  Icon 
} from "@tremor/react";

const mrrHistory = [
  { month: "Oct", value: 38000 },
  { month: "Nov", value: 39500 },
  { month: "Dec", value: 41000 },
  { month: "Jan", value: 42500 },
  { month: "Feb", value: 44000 },
  { month: "Mar", value: 45000 },
];

export default function RevenuePage() {
  const { revenue } = useRevenue();
  const { alerts } = useAlerts();

  const revenueAlerts = alerts.alerts.filter(a => 
    ["revenue_spike", "revenue_drop", "churn_spike"].includes(a.alert_type)
  );
  const { openChat } = useAppStore();

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Revenue Intelligence" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <TrendingUp className="h-3.5 w-3.5" />
                Revenue performance
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">Growth and Retention</h1>
              <p className="mt-2 text-sm text-[#5f5344]">Track MRR, ARR, NRR, and churn quality with one narrative.</p>
            </div>
            <button
              onClick={() => openChat("Revenue growth strategy")}
              className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
            >
              <Sparkles className="h-4 w-4" />
              Run strategy audit
            </button>
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Current MRR", value: formatCurrency(revenue.mrr), icon: TrendingUp },
            { label: "Projected ARR", value: formatCurrency(revenue.arr), icon: ArrowUpRight },
            { label: "Net Retention", value: `${revenue.nrr}%`, icon: Repeat },
            { label: "Churn", value: `${revenue.churn_rate}%`, icon: TrendingDown },
          ].map((item) => (
            <article key={item.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <div className="flex items-center justify-between">
                <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{item.label}</p>
                <item.icon className="h-4 w-4 text-[#87602a]" />
              </div>
              <p className="mt-2 text-2xl font-semibold text-[#2a2017]">{item.value}</p>
            </article>
          ))}
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <Card className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 sm:p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-[#2a2017]">MRR Momentum</h2>
              <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-700">↑ 18.4% YoY</span>
            </div>
            <div className="h-[250px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={mrrHistory} margin={{ top: 5, right: 15, left: 0, bottom: 5 }}>
                  <defs>
                    <linearGradient id="mrrFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.01} />
                    </linearGradient>
                    <filter id="shadowMrr">
                      <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.15" />
                    </filter>
                  </defs>
                  <XAxis 
                    dataKey="month" 
                    tickLine={false} 
                    axisLine={{ stroke: "#e0d7cf", strokeWidth: 1 }} 
                    tick={{ fill: "#7b6d5b", fontSize: 12, fontWeight: 500 }} 
                    grid={{ horizontal: false }}
                  />
                  <YAxis 
                    tickLine={false} 
                    axisLine={{ stroke: "#e0d7cf", strokeWidth: 1 }} 
                    tick={{ fill: "#7b6d5b", fontSize: 12 }} 
                    tickFormatter={(v) => `$${v / 1000}k`}
                    grid={{ vertical: true, stroke: "#f0ede8", strokeDasharray: "3 3" }}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      border: "1px solid #d9c9b8", 
                      borderRadius: 12, 
                      background: "#fffbf5",
                      boxShadow: "0 4px 12px rgba(63, 45, 24, 0.1)"
                    }}
                    formatter={(value) => [`$${Number(value).toLocaleString()}`, 'MRR']}
                    labelFormatter={(label) => `${label} 2024`}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="value" 
                    stroke="#059669" 
                    strokeWidth={2.5} 
                    fill="url(#mrrFill)"
                    filter="url(#shadowMrr)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 flex items-center justify-between pt-4 border-t border-[#ede8e0]">
              <span className="text-xs text-[#716556]">Last 6 months</span>
              <span className="text-sm font-semibold text-[#2a2017]">${mrrHistory[mrrHistory.length - 1].value.toLocaleString()}</span>
            </div>
          </Card>

          <Card className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 sm:p-6">
            <h2 className="mb-6 text-lg font-semibold text-[#2a2017]">Revenue by Segment</h2>
            <div className="space-y-4">
              {[
                { name: "Orchard", value: 65, color: "#10b981", bar: "bg-emerald-500" },
                { name: "Vineyard", value: 25, color: "#f97316", bar: "bg-orange-500" },
                { name: "Others", value: 10, color: "#8b7355", bar: "bg-amber-700/50" },
              ].map((item) => (
                <div key={item.name} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-[#2a2017]">{item.name}</span>
                    <span className="text-sm font-semibold text-[#5f5344]">{item.value}%</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2.5 bg-[#ede8e0] rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all ${item.bar}`}
                        style={{ width: `${item.value}%` }}
                      />
                    </div>
                    <span className="text-xs text-[#7b6d5b]">${Math.round(45000 * item.value / 100).toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6 pt-6 border-t border-[#ede8e0]">
              <div className="flex items-center justify-between">
                <span className="text-sm text-[#716556]">Total Monthly</span>
                <span className="text-lg font-bold text-[#2a2017]">${45000.toLocaleString()}</span>
              </div>
            </div>
          </Card>
        </section>

        <section className="rounded-2xl border border-[#ddd2c2] bg-rose-50/20 p-5 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[#211b15]">Retention & Churn Health</h2>
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
              (revenue?.nrr || 0) >= 110 ? 'text-emerald-600 bg-emerald-100' :
              (revenue?.nrr || 0) >= 100 ? 'text-amber-600 bg-amber-100' :
              'text-rose-600 bg-rose-100'
            }`}>
              {(revenue?.nrr || 0) >= 110 ? '✓ Strong Retention' : `${revenue?.churn_rate || 0}% churn`}
            </span>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-[#5f5344]">NRR: {revenue?.nrr || 0}%</span>
              <span className="text-xs text-[#7b6d5b]">Target: >110%</span>
            </div>
            <div className="w-full bg-[#ddd2c2]/20 rounded-full h-2">
              <div 
                className={`h-full rounded-full transition-all ${
                  (revenue?.nrr || 0) >= 110 ? 'bg-emerald-500' :
                  (revenue?.nrr || 0) >= 100 ? 'bg-amber-500' :
                  'bg-rose-500'
                }`}
                style={{ width: `${Math.min((revenue?.nrr || 0) / 150 * 100, 100)}%` }}
              />
            </div>
            <div className="text-xs text-[#716556] italic">
              {(revenue?.nrr || 0) >= 110 ? '✓ Excellent retention - customers expanding' :
               (revenue?.nrr || 0) >= 100 ? 'Good - maintaining existing customers' :
               'Monitor - customer contraction or churn'}
            </div>
          </div>
        </section>
      </div>

      {revenueAlerts.length > 0 && (
        <Card className="mt-8 border-[#e2d1c3] bg-[#fdfaf7]">
          <Flex className="mb-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-[#9a461f]" />
              <Title className="text-[#4a3f35]">Revenue Anomalies & Risk Alerts</Title>
            </div>
            <Badge color="orange">{revenueAlerts.length} Active</Badge>
          </Flex>
          <List className="space-y-2">
            {revenueAlerts.map((alert) => (
              <ListItem key={alert.id} className="py-3 px-4 rounded-lg bg-white/50 border border-[#eee0d5]">
                <Flex justifyContent="start" className="gap-4">
                  <Icon 
                    icon={alert.alert_type === 'churn_spike' ? Users : alert.alert_type === 'revenue_spike' ? TrendingUp : TrendingDown} 
                    color={alert.severity === 'critical' ? "red" : "orange"} 
                    variant="light" 
                  />
                  <div>
                    <Text className="font-medium text-[#4a3f35]">{alert.description}</Text>
                    <Text className="text-xs text-[#7b6d5b]">
                      Detected: {new Date(alert.created_at).toLocaleDateString()} • Impact: {alert.runway_impact}mo runway
                    </Text>
                  </div>
                </Flex>
                <Badge variant="outline" color={alert.severity === 'critical' ? "red" : "orange"}>
                  {alert.severity}
                </Badge>
              </ListItem>
            ))}
          </List>
        </Card>
      )}
    </div>
  );
}
