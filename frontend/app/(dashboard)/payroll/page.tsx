"use client";

import { useEffect, useMemo, useState } from "react";
import TopBar from "@/components/TopBar";
import api, { APIError, PayrollEntryItem } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { formatCurrency } from "@/lib/utils";
import { Briefcase, Calculator, RefreshCw, Sparkles, TrendingUp, Users } from "lucide-react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const FALLBACK_EMPLOYEES = [
  { department: "Engineering", salary: 182000 },
  { department: "Engineering", salary: 168000 },
  { department: "Finance", salary: 122000 },
  { department: "Sales", salary: 134000 },
  { department: "Operations", salary: 96000 },
];

const FALLBACK_ENTRIES: PayrollEntryItem[] = [
  { id: "demo-pay-1", pay_date: "2026-04-30", department: "Engineering", status: "posted", gross_pay: 350000, net_pay: 315000 },
  { id: "demo-pay-2", pay_date: "2026-04-30", department: "Sales", status: "posted", gross_pay: 210000, net_pay: 189000 },
  { id: "demo-pay-3", pay_date: "2026-04-30", department: "Finance", status: "posted", gross_pay: 110000, net_pay: 99000 },
];

function isAuthorizationError(error: unknown) {
  return error instanceof APIError && (error.status === 401 || error.status === 403);
}

export default function PayrollPage() {
  const { openChat } = useAppStore();
  const [employees, setEmployees] = useState<any[]>([]);
  const [entries, setEntries] = useState<PayrollEntryItem[]>([]);
  const [monthlyCost, setMonthlyCost] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [employeeRows, entryRows, costRows] = await Promise.all([
          api.getEmployees(),
          api.getPayrollEntries(),
          api.getMonthlyPayrollCost(),
        ]);
        setEmployees(employeeRows || []);
        setEntries(entryRows || []);
        setMonthlyCost(costRows || null);
      } catch (e) {
        if (isAuthorizationError(e)) {
          setEmployees([]);
          setEntries([]);
          setMonthlyCost(null);
          setError("Payroll data is protected. Sign in with a valid account to load live payroll records.");
          return;
        }

        const fallbackMonthly = FALLBACK_ENTRIES.reduce((sum, row) => sum + Number(row.gross_pay || 0), 0);
        setEmployees(FALLBACK_EMPLOYEES);
        setEntries(FALLBACK_ENTRIES);
        setMonthlyCost({ monthly_cost: fallbackMonthly });
        setError("Live payroll API unavailable right now. Showing demo payroll snapshot.");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const departmentData = useMemo(() => {
    const byDepartment = new Map<string, number>();
    employees.forEach((employee) => {
      const department = employee.department || "unassigned";
      byDepartment.set(department, (byDepartment.get(department) || 0) + Number(employee.salary || 0));
    });
    return Array.from(byDepartment.entries()).map(([department, value]) => ({ department, value }));
  }, [employees]);

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Payroll" />
      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Users className="h-3.5 w-3.5" />
                Headcount and compensation analytics
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">Payroll planning</h1>
              <p className="mt-2 text-sm text-[#5f5344]">Monitor compensation cost, department concentration, and recent payroll activity.</p>
            </div>
            <button
              onClick={() => openChat("Analyze our payroll structure and recommend optimization opportunities.")}
              className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
            >
              <Sparkles className="h-4 w-4" />
              Ask Finley
            </button>
          </div>
        </section>

        {error && <div className="rounded-2xl border border-[#ebc1b8] bg-[#fff1ee] px-4 py-3 text-sm text-[#9f3f30]">{error}</div>}

        <section className="grid gap-4 md:grid-cols-4">
          {[
            { label: "Headcount", value: employees.length, icon: Users },
            { label: "Payroll runs", value: entries.length, icon: Briefcase },
            { label: "Monthly payroll", value: formatCurrency(monthlyCost?.monthly_cost || monthlyCost?.total_payroll || 0), icon: Calculator },
            { label: "Annual run rate", value: formatCurrency((monthlyCost?.monthly_cost || monthlyCost?.total_payroll || 0) * 12), icon: TrendingUp },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <article key={item.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{item.label}</p>
                  <Icon className="h-4 w-4 text-[#87602a]" />
                </div>
                <p className="mt-2 text-2xl font-semibold text-[#2a2017]">{item.value}</p>
              </article>
            );
          })}
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
            <h2 className="text-lg font-semibold text-[#2a2017]">Department payroll mix</h2>
            <div className="mt-4 h-[280px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={departmentData}>
                  <XAxis dataKey="department" tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 12 }} />
                  <YAxis tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 12 }} tickFormatter={(value) => `$${Math.round(Number(value) / 1000)}k`} />
                  <Tooltip contentStyle={{ border: "1px solid #dbcdb9", borderRadius: 12, background: "#fff8ea" }} formatter={(value: number) => formatCurrency(value)} />
                  <Bar dataKey="value" fill="#a96a14" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </article>

          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
            <h2 className="text-lg font-semibold text-[#2a2017]">Recent payroll entries</h2>
            <div className="mt-4 space-y-2">
              {entries.slice(0, 8).map((entry) => (
                <div key={entry.id} className="rounded-xl border border-[#e8dcc9] bg-[#fff8ec] px-4 py-3 text-sm">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-[#2a2017]">{entry.pay_date}</p>
                      <p className="text-xs text-[#7b6d5b]">{entry.department || "unassigned"} • {entry.status}</p>
                    </div>
                    <span className="font-semibold text-[#9a461f]">{formatCurrency(entry.gross_pay)}</span>
                  </div>
                </div>
              ))}
              {entries.length === 0 && <p className="text-sm text-[#6f5f4b]">No payroll entries available.</p>}
            </div>
          </article>
        </section>

        {loading && (
          <div className="flex items-center gap-2 rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-4 text-sm text-[#6f5f4b]">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Loading payroll data...
          </div>
        )}
      </div>
    </div>
  );
}
