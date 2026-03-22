"use client";

import { useState, useEffect } from "react";

import TopBar from "@/components/TopBar";
import { useExpenses, useAlerts } from "@/hooks/useFinancialData";
import { useAppStore } from "@/lib/store";
import { cn, formatCurrency } from "@/lib/utils";
import { Receipt, ShieldCheck, Sparkles, Users, Globe, Layers, Zap, Tag, AlertTriangle, Copy, TrendingUp } from "lucide-react";
import { 
  Card, 
  Title, 
  DonutChart, 
  BarChart, 
  Select, 
  SelectItem, 
  List, 
  ListItem, 
  Flex, 
  Text, 
  Badge, 
  Icon 
} from "@tremor/react";
import type { ElementType } from "react";

const categoryMeta: Record<string, { label: string; icon: ElementType; color: string }> = {
  payroll: { label: "Payroll", icon: Users, color: "#bf7a1d" },
  aws: { label: "Infrastructure", icon: Globe, color: "#227a66" },
  saas: { label: "SaaS", icon: Layers, color: "#9d6328" },
  marketing: { label: "Marketing", icon: Zap, color: "#ac4e23" },
  office: { label: "Office", icon: Tag, color: "#5f7c2f" },
  legal: { label: "Legal", icon: ShieldCheck, color: "#85561a" },
};

export default function ExpensesPage() {
  const [department, setDepartment] = useState<string>("all");
  const { expenses } = useExpenses(3, department === "all" ? undefined : { department });
  const { alerts } = useAlerts();

  const expenseAlerts = alerts.alerts.filter(a => 
    ["spending_spike", "duplicate_invoice"].includes(a.alert_type)
  );
  const { openChat } = useAppStore();

  const totalExpenses = Object.values(expenses.breakdown as Record<string, number>).reduce((a: number, b: number) => a + b, 0);

  const departments = ["all", "Engineering", "Marketing", "Sales", "Operations", "Finance"];

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Capital Allocations" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-4">
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Receipt className="h-3.5 w-3.5" />
                Audited expense ledger
              </p>
              <h1 className="text-3xl font-semibold text-[#2c2013]">Expense Control Center</h1>
              
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-[#7a664f]">Department:</span>
                <select 
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="rounded-lg border border-[#cebda8] bg-white px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20"
                >
                  {departments.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
                </select>
              </div>

              <p className="text-sm text-[#5f5344]">Total outflow this cycle: {formatCurrency(totalExpenses)}</p>
            </div>
            <button
              onClick={() => openChat("Optimize expenditures")}
              className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
            >
              <Sparkles className="h-4 w-4" />
              AI leakage audit
            </button>
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Total Expenses", value: formatCurrency(totalExpenses) },
            { label: "Payroll Share", value: `${Math.round(((expenses.breakdown.payroll || 0) / Math.max(totalExpenses, 1)) * 100)}%` },
            { label: "Infra Share", value: `${Math.round(((expenses.breakdown.aws || 0) / Math.max(totalExpenses, 1)) * 100)}%` },
            { label: "Compliance", value: "Audited" },
          ].map((item) => (
            <article key={item.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{item.label}</p>
              <p className="mt-2 text-2xl font-semibold text-[#2a2017]">{item.value}</p>
            </article>
          ))}
        </section>

        <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Object.entries(expenses.breakdown as Record<string, number>).map(([key, amount]) => {
            const meta = categoryMeta[key] || { label: key, icon: Receipt, color: "#8a6b3f" };
            const Icon = meta.icon;
            const pct = totalExpenses > 0 ? (amount / totalExpenses) * 100 : 0;
            return (
              <article key={key} className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
                <div className="flex items-center justify-between">
                  <div className="inline-flex items-center gap-2 text-[#6f5f4b]">
                    <Icon className="h-4 w-4" />
                    <p className="text-sm font-medium">{meta.label}</p>
                  </div>
                  <span className="text-xs text-[#7f715f]">{pct.toFixed(0)}%</span>
                </div>
                <p className="mt-3 text-xl font-semibold text-[#2a2017]">{formatCurrency(amount)}</p>
                <div className="mt-3 h-1.5 rounded-full bg-[#efe6d7]">
                  <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: meta.color }} />
                </div>
              </article>
            );
          })}
        </section>
      </div>

      {expenseAlerts.length > 0 && (
        <Card className="mt-8 border-[#e2d1c3] bg-[#fdfaf7]">
          <Flex className="mb-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-[#9a461f]" />
              <Title className="text-[#4a3f35]">Expense Anomalies & Audit Flags</Title>
            </div>
          </Flex>
          <List>
            {expenseAlerts.map((alert) => (
              <ListItem key={alert.id} className="py-3">
                <Flex justifyContent="start" className="gap-4">
                  <Icon 
                    icon={alert.alert_type === 'duplicate_invoice' ? Copy : TrendingUp} 
                    color="orange" 
                    variant="light" 
                  />
                  <div>
                    <Text className="font-medium text-[#4a3f35]">{alert.description}</Text>
                    <Text className="text-xs text-[#7b6d5b]">
                      Category: {alert.category} • Method: Deterministic Audit
                    </Text>
                  </div>
                </Flex>
                <div className="text-right">
                  <Text className="font-bold text-[#9a461f]">₹{alert.amount.toLocaleString()}</Text>
                  <Badge color="orange" size="xs">
                    {alert.alert_type === 'duplicate_invoice' ? "Duplicate" : "Spike"}
                  </Badge>
                </div>
              </ListItem>
            ))}
          </List>
        </Card>
      )}
    </div>
  );
}
