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
            <h2 className="mb-4 text-lg font-semibold text-[#2a2017]">MRR Momentum</h2>
            <div className="h-[250px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={mrrHistory}>
                  <defs>
                    <linearGradient id="mrrFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2e7b62" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#2e7b62" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 12 }} />
                  <YAxis tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 12 }} tickFormatter={(v) => `$${v / 1000}k`} />
                  <Tooltip contentStyle={{ border: "1px solid #dbcdb9", borderRadius: 12, background: "#fff8ea" }} />
                  <Area type="monotone" dataKey="value" stroke="#2e7b62" strokeWidth={2.2} fill="url(#mrrFill)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 sm:p-6">
            <h2 className="mb-4 text-lg font-semibold text-[#2a2017]">Product Allocation</h2>
            <div className="flex h-[250px] items-center justify-center">
              <div className="h-full w-full max-w-[200px]">
                {/* Simplified Donut via SVG or Placeholder for now if no Tremor here */}
                <div className="flex items-center justify-center h-full text-[#7b6d5b] text-sm">
                  <div className="space-y-2">
                    <p className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-[#2e7b62]" /> Orchard (65%)</p>
                    <p className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-[#ac4e23]" /> Vineyard (25%)</p>
                    <p className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-[#8a6b3f]" /> Others (10%)</p>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </section>

        <section className="rounded-2xl border border-[#ddd2c2] bg-rose-50/20 p-5 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[#211b15]">Retention & Churn Health</h2>
            <span className="text-xs font-medium text-rose-600 bg-rose-100 px-2 py-0.5 rounded-full">Caution: Retaining 92%</span>
          </div>
          <div className="h-48 w-full flex items-end gap-2 px-2">
            {[4.2, 3.8, 5.1, 4.5, 4.1, 4.8].map((v, i) => (
              <div key={i} className="flex-1 bg-rose-500/10 rounded-t-lg group hover:bg-rose-500/20 transition-colors relative">
                <div className="absolute bottom-0 left-0 right-0 bg-rose-400 rounded-t-lg transition-all" style={{ height: `${v * 15}%` }} />
                <span className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-bold text-rose-700 opacity-0 group-hover:opacity-100">{v}%</span>
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-2 text-[10px] text-[#716556] font-medium px-2">
            <span>Oct</span><span>Nov</span><span>Dec</span><span>Jan</span><span>Feb</span><span>Mar</span>
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
