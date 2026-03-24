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
  AlertCircle,
  Clock,
  TrendingUp,
  FileText,
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

      const currentYear = new Date().getFullYear();
      const currentQuarter = Math.floor(new Date().getMonth() / 3) + 1;
      const prevQuarter = currentQuarter === 1 ? 4 : currentQuarter - 1;
      const prevYear = currentQuarter === 1 ? currentYear - 1 : currentYear;

      let [taxSummary, taxSchedule, taxRules] = await Promise.all([
        api.getTaxSummary(resolvedCompanyId, currentYear, currentQuarter),
        api.getTaxSchedule(resolvedCompanyId),
        api.getTaxRules(resolvedCompanyId)
      ]);

      const currentTotal = Number(taxSummary?.total_tax_liability || 0);
      if (currentTotal <= 0) {
        const prevSummary = await api.getTaxSummary(resolvedCompanyId, prevYear, prevQuarter);
        if (Number(prevSummary?.total_tax_liability || 0) > 0) {
          taxSummary = prevSummary;
        }
      }

      if ((taxSchedule || []).length === 0 && Number(taxSummary?.total_tax_liability || 0) > 0) {
        await api.createQuarterlyLiability(resolvedCompanyId, Number(taxSummary.year), Number(taxSummary.quarter));
        taxSchedule = await api.getTaxSchedule(resolvedCompanyId);
      }

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
    const currentYear = new Date().getFullYear();
    const currentQuarter = Math.floor(new Date().getMonth() / 3) + 1;
    setError(null);
    setIsGeneratingLiability(true);
    try {
      await api.createQuarterlyLiability(companyId, currentYear, currentQuarter);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate liability.");
    } finally {
      setIsGeneratingLiability(false);
    }
  };

  const gstLiability = Number(summary?.total_gst_collected_payable ?? summary?.gst_liability ?? 0);
  const tdsLiability = Number(summary?.total_tds_on_salary_payable ?? summary?.tds_liability ?? 0);
  const outstanding = schedule.reduce((acc, item) => acc + Number(item.remaining_balance ?? item.total_liability ?? 0), 0);
  const openItems = schedule.filter((item) => item.status !== "paid").length;
  const currentQuarter = Math.floor(new Date().getMonth() / 3) + 1;

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
          <h1 className="text-4xl font-black tracking-tight text-[#1d1b19]">Tax Compliance Hub</h1>
          <p className="mt-2 text-[#6b6257] font-medium">Track GST, TDS, and compliance deadlines for {new Date().getFullYear()}</p>
        </div>
        <button
          onClick={() => void fetchData()}
          className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-white border border-[#e5e0d8] text-sm font-bold text-[#4a443f] hover:bg-[#faf9f6] transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-2xl border border-[#ebc1b8] bg-[#fff1ee] px-4 py-3 text-sm text-[#9f3f30]">
          <AlertCircle className="w-4 h-4 inline mr-2" />
          {error}
        </div>
      )}

      {/* Key Tax Metadata */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-[#e5e0d8] bg-white px-5 py-4">
          <p className="text-xs font-black uppercase tracking-[0.12em] text-[#9a9187]">GST Status</p>
          <p className="mt-2 text-lg font-black text-[#1d1b19]">Registered</p>
          <p className="text-xs text-[#7b6f5e] mt-1">GST/18% applies</p>
        </div>
        <div className="rounded-2xl border border-[#e5e0d8] bg-white px-5 py-4">
          <p className="text-xs font-black uppercase tracking-[0.12em] text-[#9a9187]">TDS Filing</p>
          <p className="mt-2 text-lg font-black text-[#1d1b19]">Quarterly</p>
          <p className="text-xs text-[#7b6f5e] mt-1">10% on salary/vendor</p>
        </div>
        <div className="rounded-2xl border border-[#e5e0d8] bg-white px-5 py-4">
          <p className="text-xs font-black uppercase tracking-[0.12em] text-[#9a9187]">Q{currentQuarter} Filing</p>
          <p className="mt-2 text-lg font-black text-[#1d1b19]">Due In</p>
          <p className="text-xs text-[#7b6f5e] mt-1">15 days</p>
        </div>
        <div className="rounded-2xl border border-[#e5e0d8] bg-white px-5 py-4">
          <p className="text-xs font-black uppercase tracking-[0.12em] text-[#9a9187]">Outstanding</p>
          <p className="mt-2 text-lg font-black text-[#1d1b19]">₹{outstanding.toLocaleString()}</p>
          <p className="text-xs text-[#c97b59] mt-1">{openItems} pending</p>
        </div>
      </div>

      {/* Current Quarter Liability Snapshot */}
      <div className="rounded-2xl border border-[#e5e0d8] bg-white p-6">
        <h2 className="text-xl font-black text-[#1d1b19] flex items-center gap-2 mb-4">
          <FileText className="w-5 h-5" />
          Current Quarter Liability (FY {new Date().getFullYear()})
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="border-r border-[#e5e0d8] pr-6">
            <p className="text-xs font-black uppercase tracking-[0.12em] text-[#9a9187]">GST Liability</p>
            <p className="text-3xl font-black mt-2 text-[#1d1b19]">₹{gstLiability.toLocaleString()}</p>
            <p className="text-xs text-[#7b6f5e] mt-2">18% on sales</p>
          </div>
          <div className="border-r border-[#e5e0d8] pr-6">
            <p className="text-xs font-black uppercase tracking-[0.12em] text-[#9a9187]">TDS Payable</p>
            <p className="text-3xl font-black mt-2 text-[#1d1b19]">₹{tdsLiability.toLocaleString()}</p>
            <p className="text-xs text-[#7b6f5e] mt-2">10% TDS collected</p>
          </div>
          <div>
            <p className="text-xs font-black uppercase tracking-[0.12em] text-[#9a9187]">Total Due</p>
            <p className="text-3xl font-black mt-2 text-[#c97b59]">₹{(gstLiability + tdsLiability).toLocaleString()}</p>
            <p className="text-xs text-[#7b6f5e] mt-2">Payment schedule below</p>
          </div>
        </div>
      </div>

      {/* Upcoming Payment Schedule */}
      <div className="rounded-2xl border border-[#e5e0d8] bg-white p-6">
        <h2 className="text-xl font-black text-[#1d1b19] flex items-center gap-2 mb-4">
          <Calendar className="w-5 h-5" />
          Tax Payment Schedule
        </h2>
        <div className="space-y-3">
          {schedule.length > 0 ? schedule.slice(0, 5).map((item, i) => {
            const isOverdue = new Date(item.due_date) < new Date() && item.status !== 'paid';
            const isDueSoon = new Date(item.due_date) <= new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) && item.status !== 'paid';
            return (
              <div key={i} className={`p-4 rounded-xl border ${
                item.status === 'paid' ? 'bg-emerald-50 border-emerald-100' :
                isOverdue ? 'bg-rose-50 border-rose-100' :
                isDueSoon ? 'bg-amber-50 border-amber-100' : 'bg-blue-50 border-blue-100'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${
                      item.status === 'paid' ? 'bg-emerald-100 text-emerald-600' :
                      isOverdue ? 'bg-rose-100 text-rose-600' :
                      isDueSoon ? 'bg-amber-100 text-amber-600' : 'bg-blue-100 text-blue-600'
                    }`}>
                      {item.status === 'paid' ? <CheckCircle2 className="w-4 h-4" /> : <Clock className="w-4 h-4" />}
                    </div>
                    <div>
                      <p className="font-bold text-[#1d1b19]">Q{item.quarter} {item.year}</p>
                      <p className="text-sm text-[#6b6257]">{new Date(item.due_date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' })}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-black text-[#1d1b19]">₹{Number(item.total_liability || 0).toLocaleString()}</p>
                    <p className={`text-xs font-bold uppercase ${
                      item.status === 'paid' ? 'text-emerald-600' :
                      isOverdue ? 'text-rose-600' :
                      isDueSoon ? 'text-amber-600' : 'text-blue-600'
                    }`}>{item.status === 'overdue' ? 'OVERDUE' : item.status.toUpperCase()}</p>
                  </div>
                </div>
              </div>
            );
          }) : (
            <div className="text-center py-8 text-[#9a9187]">No payments scheduled. Create quarterly liability to get started.</div>
          )}
        </div>
      </div>

      {/* Tax Filing Compliance Checklist */}
      <div className="rounded-2xl border border-[#e5e0d8] bg-white p-6">
        <h2 className="text-xl font-black text-[#1d1b19] flex items-center gap-2 mb-4">
          <CheckCircle2 className="w-5 h-5" />
          Q{currentQuarter} Tax Filing Checklist
        </h2>
        <div className="space-y-3">
          {[
            { item: "Collect all invoices and GST returns", done: false },
            { item: "Reconcile AR payments received from customers", done: false },
            { item: "Calculate TDS liability (10% on salary/vendor payments)", done: false },
            { item: "Generate monthly tax summary report", done: false },
            { item: "File GST return with tax authority", done: false },
            { item: "Reconcile payments and update status", done: false },
          ].map((check, i) => (
            <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-[#f9f7f3] hover:bg-[#f3eee5] transition-colors">
              <input type="checkbox" defaultChecked={check.done} className="w-4 h-4" />
              <span className={`text-sm ${check.done ? 'text-[#9a9187] line-through' : 'text-[#4f463c]'}`}>{check.item}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Tax Reference Guide */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-[#e5e0d8] bg-white p-6">
          <h3 className="text-lg font-black text-[#1d1b19] mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            GST on Sales
          </h3>
          <div className="space-y-2 text-sm text-[#4f463c]">
            <p><strong>Rate:</strong> 18% on most services</p>
            <p><strong>Filing:</strong> Monthly (via GST portal)</p>
            <p><strong>Payment:</strong> Quarterly (Q1: Apr 15, Q2: Jul 15, Q3: Oct 15, Q4: Jan 15)</p>
            <p><strong>Note:</strong> Input credits reduce liability</p>
          </div>
        </div>
        <div className="rounded-2xl border border-[#e5e0d8] bg-white p-6">
          <h3 className="text-lg font-black text-[#1d1b19] mb-4 flex items-center gap-2">
            <IndianRupee className="w-5 h-5" />
            TDS on Salary & Vendors
          </h3>
          <div className="space-y-2 text-sm text-[#4f463c]">
            <p><strong>Rate:</strong> 10% on salaries (>₹50k/month)</p>
            <p><strong>Rate:</strong> 10% on vendor payments (>₹50k/vendor)</p>
            <p><strong>Filing:</strong> Quarterly (Form 24Q/26AS)</p>
            <p><strong>Note:</strong> Must reconcile with employee PF records</p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={handleGenerateLiability}
          disabled={isGeneratingLiability}
          className="px-6 py-2.5 rounded-xl border border-[#d2c1a7] bg-[#fff2de] text-[#654621] text-sm font-bold hover:bg-[#f6e2c3] transition-all disabled:opacity-60 inline-flex items-center gap-2"
        >
          <Calculator className="w-4 h-4" />
          {isGeneratingLiability ? "Generating..." : "Generate Quarterly Liability"}
        </button>
        <button
          onClick={handleReconcile}
          disabled={isReconciling}
          className="px-6 py-2.5 rounded-xl bg-[#1d1b19] text-white text-sm font-bold hover:bg-[#33302c] transition-all shadow-lg shadow-[#1d1b19]/10 disabled:opacity-60 inline-flex items-center gap-2"
        >
          <CheckCircle2 className="w-4 h-4" />
          {isReconciling ? "Reconciling..." : "Mark Payment as Received"}
        </button>
      </div>
    </div>
  );
}
