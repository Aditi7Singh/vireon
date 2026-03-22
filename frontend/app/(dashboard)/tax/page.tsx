"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { 
  ShieldCheck, 
  Calendar, 
  IndianRupee, 
  RefreshCw,
  CheckCircle2,
  AlertCircle
} from "lucide-react";

export default function TaxDashboard() {
  const { user } = useAppStore();
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<any>(null);
  const [schedule, setSchedule] = useState<any[]>([]);
  const [rules, setRules] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const health = await api.getStartupHealth();
        const companyId = health.default_company_id;
        if (!companyId) return;

        const year = new Date().getFullYear();
        const quarter = Math.floor(new Date().getMonth() / 3) + 1;

        const [taxSummary, taxSchedule, taxRules] = await Promise.all([
          api.getTaxSummary(companyId, year, quarter),
          api.getTaxSchedule(companyId),
          api.getTaxRules(companyId)
        ]);

        setSummary(taxSummary);
        setSchedule(taxSchedule);
        setRules(taxRules);
      } catch (error) {
        console.error("Failed to fetch tax data:", error);
      } finally {
        setLoading(setLoading(false) as any);
      }
    };
    fetchData();
  }, []);

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
          <p className="mt-2 text-[#6b6257] font-medium">Quarterly liabilities and payment schedule for {new Date().getFullYear()}</p>
        </div>
        <div className="flex gap-4">
          <button className="px-6 py-2.5 rounded-xl bg-white border border-[#e5e0d8] text-sm font-bold text-[#4a443f] hover:bg-[#faf9f6] transition-all">
            Download Report
          </button>
          <button className="px-6 py-2.5 rounded-xl bg-[#1d1b19] text-white text-sm font-bold hover:bg-[#33302c] transition-all shadow-lg shadow-[#1d1b19]/10">
            Reconcile Payment
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { label: "GST Liability", value: summary?.gst_liability || 0, icon: ShieldCheck, color: "bg-blue-50 text-blue-600" },
          { label: "TDS Payable", value: summary?.tds_liability || 0, icon: IndianRupee, color: "bg-amber-50 text-amber-600" },
          { label: "Advance Tax", value: summary?.advance_tax_estimate || 0, icon: Calendar, color: "bg-emerald-50 text-emerald-600" },
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
                    <td className="px-6 py-5 font-black text-[#1d1b19]">₹{item.total_liability.toLocaleString()}</td>
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
          </div>
        </div>
      </div>
    </div>
  );
}
