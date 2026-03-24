"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import {
  ShieldCheck,
  Calendar,
  IndianRupee,
  RefreshCw,
  CheckCircle2,
  Calculator,
  Receipt,
} from "lucide-react";

export default function TaxDashboard() {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<any>(null);
  const [schedule, setSchedule] = useState<any[]>([]);
  const [rules, setRules] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [isReconciling, setIsReconciling] = useState(false);
  const [isGeneratingLiability, setIsGeneratingLiability] = useState(false);
  const [invoiceBaseAmount, setInvoiceBaseAmount] = useState<number>(100000);
  const [invoiceIsService, setInvoiceIsService] = useState(true);
  const [invoiceBreakdown, setInvoiceBreakdown] = useState<any | null>(null);
  const [payrollGross, setPayrollGross] = useState<number>(120000);
  const [payrollBreakdown, setPayrollBreakdown] = useState<any | null>(null);
  const [calcBusy, setCalcBusy] = useState<"invoice" | "payroll" | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const health = await api.getStartupHealth();
      const resolvedCompanyId = health.default_company_id;
      setCompanyId(resolvedCompanyId || null);
      if (!resolvedCompanyId) {
        setError("No default company configured. Please complete startup setup.");
        return;
      }

      const year = new Date().getFullYear();
      const quarter = Math.floor(new Date().getMonth() / 3) + 1;

      const [taxSummary, taxSchedule, taxRules] = await Promise.all([
        api.getTaxSummary(resolvedCompanyId, year, quarter),
        api.getTaxSchedule(resolvedCompanyId),
        api.getTaxRules(resolvedCompanyId)
      ]);

      setSummary(taxSummary);
      setSchedule(taxSchedule || []);
      setRules(taxRules || []);
    } catch (err) {
      console.error("Failed to fetch tax data:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch tax data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchData();
  }, []);

  const handleReconcile = async () => {
    if (!companyId || isReconciling) return;
    const nextPending = schedule.find((item) => item.status !== "paid" && item.id);
    if (!nextPending) {
      setError("No pending liability found to reconcile.");
      return;
    }

    setError(null);
    setIsReconciling(true);
    try {
      await api.reconcileTaxPayment(
        String(nextPending.id),
        Number(nextPending.total_liability || 0),
        `UI-${new Date().toISOString()}`
      );
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reconciliation failed.");
    } finally {
      setIsReconciling(false);
    }
  };

  const handleGenerateLiability = async () => {
    if (!companyId || isGeneratingLiability) return;
    setError(null);
    setIsGeneratingLiability(true);
    try {
      const year = new Date().getFullYear();
      const quarter = Math.floor(new Date().getMonth() / 3) + 1;
      await api.createQuarterlyLiability(companyId, year, quarter);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate quarterly liability.");
    } finally {
      setIsGeneratingLiability(false);
    }
  };

  const handleInvoiceTaxCalc = async () => {
    if (!companyId || calcBusy) return;
    setError(null);
    setCalcBusy("invoice");
    try {
      const result = await api.calculateInvoiceTax(companyId, invoiceBaseAmount, invoiceIsService);
      setInvoiceBreakdown(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to calculate invoice taxes.");
    } finally {
      setCalcBusy(null);
    }
  };

  const handlePayrollTaxCalc = async () => {
    if (!companyId || calcBusy) return;
    setError(null);
    setCalcBusy("payroll");
    try {
      const result = await api.calculatePayrollTax(companyId, payrollGross);
      setPayrollBreakdown(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to calculate payroll deductions.");
    } finally {
      setCalcBusy(null);
    }
  };

  const gstLiability = Number(summary?.total_gst_collected_payable ?? summary?.gst_liability ?? 0);
  const tdsLiability = Number(summary?.total_tds_on_salary_payable ?? summary?.tds_liability ?? 0);
  const advanceTax = Number(summary?.advance_tax_estimate ?? 0);
  const outstanding = schedule.reduce((acc, item) => acc + Number(item.remaining_balance ?? item.total_liability ?? 0), 0);
  const nextDue = schedule.length ? new Date(schedule[0].due_date).toLocaleDateString() : "No due items";
  const openItems = schedule.filter((item) => item.status !== "paid").length;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <RefreshCw className="w-8 h-8 animate-spin text-[#d4a373]" />
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-4xl font-black tracking-tight text-[#1d1b19]">Tax Compliance</h1>
          <p className="mt-2 text-[#6b6257] font-medium">Quarterly liabilities, live calculators, and reconciliation workflow for {new Date().getFullYear()}</p>
        </div>
        <div className="flex gap-4">
          <button
            onClick={handleGenerateLiability}
            disabled={isGeneratingLiability}
            className="px-6 py-2.5 rounded-xl border border-[#d2c1a7] bg-[#fff2de] text-[#654621] text-sm font-bold hover:bg-[#f6e2c3] transition-all disabled:opacity-60"
          >
            {isGeneratingLiability ? "Generating..." : "Generate this quarter"}
          </button>
          <button
            onClick={() => void fetchData()}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-white border border-[#e5e0d8] text-sm font-bold text-[#4a443f] hover:bg-[#faf9f6] transition-all"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={handleReconcile}
            disabled={isReconciling}
            className="px-6 py-2.5 rounded-xl bg-[#1d1b19] text-white text-sm font-bold hover:bg-[#33302c] transition-all shadow-lg shadow-[#1d1b19]/10 disabled:opacity-60"
          >
            {isReconciling ? "Reconciling..." : "Reconcile Payment"}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl border border-[#ebc1b8] bg-[#fff1ee] px-4 py-3 text-sm text-[#9f3f30]">
          {error}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { label: "GST Liability", value: gstLiability, icon: ShieldCheck, color: "bg-blue-50 text-blue-600" },
          { label: "TDS Payable", value: tdsLiability, icon: IndianRupee, color: "bg-amber-50 text-amber-600" },
          { label: "Advance Tax", value: advanceTax, icon: Calendar, color: "bg-emerald-50 text-emerald-600" },
        ].map((item, i) => (
          <div key={i} className="bg-white/60 backdrop-blur-md border border-white/40 p-6 rounded-3xl shadow-sm hover:shadow-md transition-all group">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-2xl ${item.color} group-hover:scale-110 transition-transform`}>
                <item.icon className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs font-black uppercase tracking-[0.12em] text-[#9a9187]">{item.label}</p>
                <p className="text-2xl font-black mt-1 text-[#1d1b19]">₹{item.value.toLocaleString()}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="rounded-2xl border border-[#e5e0d8] bg-white px-5 py-4">
          <p className="text-xs font-black uppercase tracking-[0.12em] text-[#9a9187]">Outstanding Tax Balance</p>
          <p className="mt-2 text-2xl font-black text-[#1d1b19]">₹{outstanding.toLocaleString()}</p>
        </div>
        <div className="rounded-2xl border border-[#e5e0d8] bg-white px-5 py-4">
          <p className="text-xs font-black uppercase tracking-[0.12em] text-[#9a9187]">Open Payment Items</p>
          <p className="mt-2 text-2xl font-black text-[#1d1b19]">{openItems}</p>
        </div>
        <div className="rounded-2xl border border-[#e5e0d8] bg-white px-5 py-4">
          <p className="text-xs font-black uppercase tracking-[0.12em] text-[#9a9187]">Next Due Date</p>
          <p className="mt-2 text-2xl font-black text-[#1d1b19]">{nextDue}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-[#e5e0d8] bg-white p-5">
          <h2 className="inline-flex items-center gap-2 text-lg font-black text-[#1d1b19]"><Receipt className="w-5 h-5" />Invoice Tax Calculator</h2>
          <p className="mt-1 text-sm text-[#6b6257]">Preview GST and TDS for a deal before invoicing.</p>
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label className="text-xs font-black uppercase tracking-[0.12em] text-[#9a9187]">
              Invoice base (INR)
              <input
                type="number"
                value={invoiceBaseAmount}
                onChange={(e) => setInvoiceBaseAmount(Number(e.target.value || 0))}
                className="mt-1 w-full rounded-xl border border-[#d6c8b4] bg-[#fffaf2] px-3 py-2 text-sm text-[#2a2017]"
              />
            </label>
            <label className="text-xs font-black uppercase tracking-[0.12em] text-[#9a9187]">
              Type
              <select
                value={invoiceIsService ? "service" : "saas"}
                onChange={(e) => setInvoiceIsService(e.target.value === "service")}
                className="mt-1 w-full rounded-xl border border-[#d6c8b4] bg-[#fffaf2] px-3 py-2 text-sm text-[#2a2017]"
              >
                <option value="service">Service</option>
                <option value="saas">SaaS</option>
              </select>
            </label>
          </div>
          <button
            onClick={handleInvoiceTaxCalc}
            disabled={calcBusy === "invoice"}
            className="mt-4 inline-flex items-center gap-2 rounded-xl border border-[#d2c1a7] bg-[#fff2de] px-4 py-2 text-xs font-black uppercase tracking-wide text-[#654621] hover:bg-[#f6e2c3] disabled:opacity-60"
          >
            <Calculator className="w-4 h-4" />
            {calcBusy === "invoice" ? "Calculating..." : "Calculate invoice tax"}
          </button>

          {invoiceBreakdown && (
            <div className="mt-4 rounded-xl border border-[#efe4d4] bg-[#fffaf2] p-4 text-sm text-[#4f463c] space-y-1">
              <p>GST: <strong>₹{Number(invoiceBreakdown.gst_amount || 0).toLocaleString()}</strong></p>
              <p>TDS: <strong>₹{Number(invoiceBreakdown.tds_deducted || 0).toLocaleString()}</strong></p>
              <p>Total invoice: <strong>₹{Number(invoiceBreakdown.total_invoice || 0).toLocaleString()}</strong></p>
              <p>Net cash expected: <strong>₹{Number(invoiceBreakdown.net_cash_expected || 0).toLocaleString()}</strong></p>
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-[#e5e0d8] bg-white p-5">
          <h2 className="inline-flex items-center gap-2 text-lg font-black text-[#1d1b19]"><IndianRupee className="w-5 h-5" />Payroll Tax Calculator</h2>
          <p className="mt-1 text-sm text-[#6b6257]">Estimate PF, ESI, PT, and TDS impact for a monthly gross salary.</p>
          <label className="mt-4 block text-xs font-black uppercase tracking-[0.12em] text-[#9a9187]">
            Monthly gross (INR)
            <input
              type="number"
              value={payrollGross}
              onChange={(e) => setPayrollGross(Number(e.target.value || 0))}
              className="mt-1 w-full rounded-xl border border-[#d6c8b4] bg-[#fffaf2] px-3 py-2 text-sm text-[#2a2017]"
            />
          </label>
          <button
            onClick={handlePayrollTaxCalc}
            disabled={calcBusy === "payroll"}
            className="mt-4 inline-flex items-center gap-2 rounded-xl border border-[#d2c1a7] bg-[#fff2de] px-4 py-2 text-xs font-black uppercase tracking-wide text-[#654621] hover:bg-[#f6e2c3] disabled:opacity-60"
          >
            <Calculator className="w-4 h-4" />
            {calcBusy === "payroll" ? "Calculating..." : "Calculate payroll tax"}
          </button>

          {payrollBreakdown && (
            <div className="mt-4 rounded-xl border border-[#efe4d4] bg-[#fffaf2] p-4 text-sm text-[#4f463c] space-y-1">
              <p>Employee PF: <strong>₹{Number(payrollBreakdown.employee_pf || 0).toLocaleString()}</strong></p>
              <p>Employee ESI: <strong>₹{Number(payrollBreakdown.employee_esi || 0).toLocaleString()}</strong></p>
              <p>Professional Tax: <strong>₹{Number(payrollBreakdown.professional_tax || 0).toLocaleString()}</strong></p>
              <p>Income Tax TDS: <strong>₹{Number(payrollBreakdown.income_tax_tds || 0).toLocaleString()}</strong></p>
              <p>Net Pay: <strong>₹{Number(payrollBreakdown.net_pay || 0).toLocaleString()}</strong></p>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Payment Schedule */}
        <div className="lg:col-span-2 space-y-6">
          <h2 className="text-xl font-black text-[#1d1b19] flex items-center gap-2">
            Upcoming Schedule
            <span className="px-2 py-0.5 rounded-full bg-[#f0ede6] text-[10px] font-black uppercase text-[#8b8276]">Timeline</span>
          </h2>
          <div className="bg-white/80 backdrop-blur-md border border-white/40 rounded-[2rem] overflow-hidden shadow-sm">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-[#f0ede6]">
                  <th className="px-6 py-5 text-[10px] font-black uppercase tracking-widest text-[#9a9187]">Quarter/Year</th>
                  <th className="px-6 py-5 text-[10px] font-black uppercase tracking-widest text-[#9a9187]">Due Date</th>
                  <th className="px-6 py-5 text-[10px] font-black uppercase tracking-widest text-[#9a9187]">Amount</th>
                  <th className="px-6 py-5 text-[10px] font-black uppercase tracking-widest text-[#9a9187]">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f0ede6]">
                {schedule.length > 0 ? schedule.map((item, i) => (
                  <tr key={i} className="group hover:bg-[#faf9f6] transition-colors">
                    <td className="px-6 py-5">
                      <p className="font-bold text-[#1d1b19]">Q{item.quarter} {item.year}</p>
                    </td>
                    <td className="px-6 py-5 text-sm text-[#6b6257] font-medium">{new Date(item.due_date).toLocaleDateString()}</td>
                    <td className="px-6 py-5 font-black text-[#1d1b19]">₹{Number(item.total_liability || 0).toLocaleString()}</td>
                    <td className="px-6 py-5">
                      <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase ${
                        item.status === 'paid' ? 'bg-emerald-50 text-emerald-600' : 
                        item.status === 'overdue' ? 'bg-rose-50 text-rose-600' : 'bg-amber-50 text-amber-600'
                      }`}>
                        {item.status}
                      </span>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={4} className="px-6 py-12 text-center text-[#9a9187] font-medium">No upcoming payments scheduled</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Tax Rules */}
        <div className="space-y-6">
          <h2 className="text-xl font-black text-[#1d1b19]">Active Rules</h2>
          <div className="space-y-4">
            {rules.map((rule, i) => (
              <div key={i} className="p-5 bg-white border border-[#e5e0d8] rounded-2xl flex items-start gap-4">
                <div className="mt-1">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                </div>
                <div>
                  <p className="font-bold text-[#1d1b19]">{rule.tax_name}</p>
                  <p className="text-xs text-[#6b6257] mt-0.5">{rule.description}</p>
                  <p className="text-xs font-black mt-2 text-[#d4a373]">{(rule.rate * 100).toFixed(1)}% Rate</p>
                </div>
              </div>
            ))}
            {rules.length === 0 && (
              <div className="rounded-2xl border border-dashed border-[#d9cdbc] bg-[#fffdf8] p-5 text-sm text-[#7b6f5e]">
                No tax rules available for the selected company.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
