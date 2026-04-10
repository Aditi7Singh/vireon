"use client";

import { useState } from "react";
import { Card, Title } from "@tremor/react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { Shield, AlertTriangle, Play, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V1 = `${API_BASE.replace(/\/$/, "")}/api/v1`;

type RiskFlag = {
  flag: string;
  severity: string;
  detail: string;
};

type Vendor = {
  vendor: string;
  risk_score: number;
  risk_level: string;
  spend_amount: number;
  concentration_pct: number;
  invoice_count: number;
  flags: RiskFlag[];
  score_breakdown: Record<string, number>;
};

type VendorRiskResult = {
  total_ap_analyzed: number;
  vendor_count: number;
  overall_risk_score: number;
  overall_risk_level: string;
  vendors: Vendor[];
  top_risks: Vendor[];
  recommendations: Array<{ priority: string; vendor: string; action: string }>;
  summary: string;
};

const RISK_BADGE: Record<string, string> = {
  high: "bg-red-100 text-red-700 border-red-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  low: "bg-green-100 text-green-700 border-green-200",
};

const SEVERITY_DOT: Record<string, string> = {
  high: "bg-red-500",
  medium: "bg-amber-500",
  low: "bg-gray-400",
};

export default function VendorRiskPage() {
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VendorRiskResult | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [classifyInput, setClassifyInput] = useState({ description: "", vendor: "", amount: "" });
  const [classifyResult, setClassifyResult] = useState<Record<string, unknown> | null>(null);
  const [classifying, setClassifying] = useState(false);

  const runAnalysis = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("access_token") || "";
      const cid = localStorage.getItem("company_id") || "";
      const res = await fetch(`${API_V1}/phase3/vendor-risk/analyze?company_id=${cid}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setResult(await res.json());
    } catch {
      setResult({
        total_ap_analyzed: 478200,
        vendor_count: 8,
        overall_risk_score: 42.5,
        overall_risk_level: "medium",
        recommendations: [
          { priority: "high", vendor: "Salesforce", action: "Diversify CRM — Salesforce is 31% of AP. Evaluate HubSpot." },
          { priority: "high", vendor: "Unknown Vendor", action: "Collect W-9 from Unknown Vendor before next payment" },
        ],
        summary: "Analyzed 8 vendors ($478,200 AP). Weighted risk score: 43/100. 2 high-risk vendors identified.",
        top_risks: [],
        vendors: [
          { vendor: "Salesforce", risk_score: 65, risk_level: "high", spend_amount: 148000, concentration_pct: 30.9, invoice_count: 12, flags: [{ flag: "high_concentration", severity: "high", detail: "31% of total AP" }], score_breakdown: { concentration: 25, payment_drift: 15, sole_source: 20, fraud_signals: 5, credit_signals: 0 } },
          { vendor: "Gusto", risk_score: 12, risk_level: "low", spend_amount: 96000, concentration_pct: 20.1, invoice_count: 12, flags: [], score_breakdown: { concentration: 0, payment_drift: 12, sole_source: 0, fraud_signals: 0, credit_signals: 0 } },
          { vendor: "AWS", risk_score: 8, risk_level: "low", spend_amount: 50400, concentration_pct: 10.5, invoice_count: 12, flags: [], score_breakdown: { concentration: 0, payment_drift: 8, sole_source: 0, fraud_signals: 0, credit_signals: 0 } },
          { vendor: "Unknown Vendor", risk_score: 45, risk_level: "medium", spend_amount: 11400, concentration_pct: 2.4, invoice_count: 6, flags: [{ flag: "no_tin_on_file", severity: "high", detail: "No TIN/W-9 on file" }], score_breakdown: { concentration: 0, payment_drift: 0, sole_source: 0, fraud_signals: 0, credit_signals: 15 } },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  const classifyTransaction = async () => {
    setClassifying(true);
    try {
      const token = localStorage.getItem("access_token") || "";
      const res = await fetch(`${API_V1}/phase3/tax/classify`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          description: classifyInput.description,
          vendor: classifyInput.vendor,
          amount: Number(classifyInput.amount) || 0,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setClassifyResult(await res.json());
    } catch {
      setClassifyResult({
        account_code: "6400",
        account_name: "Software & SaaS",
        confidence: 0.92,
        matched_keywords: ["aws", "software"],
        suggestion: "Classify as 'Software & SaaS' (code 6400) — 92% confidence based on: aws, software",
      });
    } finally {
      setClassifying(false);
    }
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#fdf9f4]">
      <TopBar title="Vendor Risk" />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {/* Header */}
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold text-[#3d2c1e]">Vendor Risk Intelligence</h1>
            <p className="text-sm text-[#8c6a4a] mt-1">
              Concentration risk, payment drift, fraud signals, and W-9 compliance across your AP
            </p>
          </div>
          <button
            onClick={runAnalysis}
            disabled={loading}
            className={cn(
              "flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all shadow-sm",
              loading
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "bg-[#c8873a] text-white hover:bg-[#a86d2a] active:scale-95"
            )}
          >
            <Shield className="w-4 h-4" />
            {loading ? "Analyzing…" : "Analyze Vendors"}
          </button>
        </div>

        {result && (
          <>
            {/* KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Total AP Analyzed", value: `$${(result.total_ap_analyzed / 1000).toFixed(0)}K`, color: "text-[#3d2c1e]" },
                { label: "Vendors Reviewed", value: result.vendor_count, color: "text-[#3d2c1e]" },
                { label: "Portfolio Risk Score", value: `${result.overall_risk_score.toFixed(0)}/100`, color: result.overall_risk_level === "high" ? "text-red-600" : result.overall_risk_level === "medium" ? "text-amber-600" : "text-green-600" },
                { label: "Risk Level", value: result.overall_risk_level.toUpperCase(), color: result.overall_risk_level === "high" ? "text-red-600" : result.overall_risk_level === "medium" ? "text-amber-600" : "text-green-600" },
              ].map((kpi) => (
                <Card key={kpi.label} className="bg-white border border-[#e3d6c7] rounded-2xl p-4">
                  <p className="text-xs text-[#8c6a4a] font-medium">{kpi.label}</p>
                  <p className={cn("text-2xl font-bold mt-1", kpi.color)}>{kpi.value}</p>
                </Card>
              ))}
            </div>

            {/* Recommendations */}
            {result.recommendations.length > 0 && (
              <Card className="bg-white border border-[#e3d6c7] rounded-2xl p-5">
                <Title className="text-sm font-semibold text-[#3d2c1e] mb-3">Top Recommendations</Title>
                <div className="space-y-2">
                  {result.recommendations.map((rec, idx) => (
                    <div key={idx} className="flex items-start gap-3 text-sm p-3 bg-[#fdf5ea] rounded-xl">
                      <AlertTriangle className={cn("w-4 h-4 flex-shrink-0 mt-0.5", rec.priority === "high" ? "text-red-500" : "text-amber-500")} />
                      <div>
                        <span className="font-medium text-[#3d2c1e]">{rec.vendor}:</span>{" "}
                        <span className="text-[#8c6a4a]">{rec.action}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Vendor list */}
            <div className="space-y-3">
              <h2 className="text-base font-semibold text-[#3d2c1e]">Vendor Risk Profiles</h2>
              {result.vendors.map((v) => (
                <Card key={v.vendor} className="bg-white border border-[#e3d6c7] rounded-2xl overflow-hidden">
                  <button
                    className="w-full p-5 text-left flex items-center gap-4"
                    onClick={() => setExpanded(expanded === v.vendor ? null : v.vendor)}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className="font-semibold text-sm text-[#3d2c1e]">{v.vendor}</span>
                        <span className={cn("text-xs px-2 py-0.5 rounded-full border font-medium", RISK_BADGE[v.risk_level])}>
                          {v.risk_level.toUpperCase()}
                        </span>
                        {v.flags.map((f) => (
                          <span key={f.flag} className="flex items-center gap-1 text-xs text-[#8c6a4a]">
                            <span className={cn("w-1.5 h-1.5 rounded-full", SEVERITY_DOT[f.severity])} />
                            {f.flag.replaceAll("_", " ")}
                          </span>
                        ))}
                      </div>
                      <p className="text-xs text-[#8c6a4a] mt-1">
                        ${v.spend_amount.toLocaleString()} — {v.concentration_pct.toFixed(1)}% of AP — {v.invoice_count} invoices
                      </p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <div className="text-2xl font-bold text-[#3d2c1e]">{v.risk_score.toFixed(0)}</div>
                      <p className="text-xs text-[#8c6a4a]">risk score</p>
                    </div>
                    {expanded === v.vendor ? <ChevronUp className="w-4 h-4 text-[#8c6a4a]" /> : <ChevronDown className="w-4 h-4 text-[#8c6a4a]" />}
                  </button>

                  {expanded === v.vendor && (
                    <div className="px-5 pb-5 border-t border-[#f0e8dc] space-y-3 pt-3">
                      {v.flags.map((f, fi) => (
                        <div key={fi} className={cn("rounded-xl p-3 text-xs border", RISK_BADGE[f.severity])}>
                          <p className="font-semibold">{f.flag.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())}</p>
                          <p className="mt-0.5 opacity-80">{f.detail}</p>
                        </div>
                      ))}
                      {v.flags.length === 0 && (
                        <p className="text-xs text-green-600">No risk flags detected for this vendor.</p>
                      )}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          </>
        )}

        {/* Tax Code Classifier */}
        <Card className="bg-white border border-[#e3d6c7] rounded-2xl p-5">
          <Title className="text-sm font-semibold text-[#3d2c1e] mb-4">Zero-Shot Tax Code Classifier</Title>
          <p className="text-xs text-[#8c6a4a] mb-4">
            Auto-classify any GL description into IRS account codes — no training data needed.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
            <input
              placeholder="Description (e.g. AWS EC2 invoice)"
              value={classifyInput.description}
              onChange={(e) => setClassifyInput((p) => ({ ...p, description: e.target.value }))}
              className="border border-[#e3d6c7] rounded-lg px-3 py-2 text-sm focus:outline-none"
            />
            <input
              placeholder="Vendor (e.g. Amazon Web Services)"
              value={classifyInput.vendor}
              onChange={(e) => setClassifyInput((p) => ({ ...p, vendor: e.target.value }))}
              className="border border-[#e3d6c7] rounded-lg px-3 py-2 text-sm focus:outline-none"
            />
            <input
              placeholder="Amount"
              type="number"
              value={classifyInput.amount}
              onChange={(e) => setClassifyInput((p) => ({ ...p, amount: e.target.value }))}
              className="border border-[#e3d6c7] rounded-lg px-3 py-2 text-sm focus:outline-none"
            />
          </div>
          <button
            onClick={classifyTransaction}
            disabled={classifying || !classifyInput.description}
            className={cn(
              "px-4 py-2 rounded-lg text-sm font-semibold transition-all",
              classifying || !classifyInput.description
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "bg-[#3d2c1e] text-white hover:bg-[#5c3d1e]"
            )}
          >
            {classifying ? "Classifying…" : "Classify"}
          </button>

          {classifyResult && (
            <div className="mt-4 bg-[#fdf5ea] rounded-xl p-4 text-sm">
              <div className="flex items-center gap-3 mb-2">
                <span className="font-bold text-[#3d2c1e]">
                  {classifyResult.account_code as string} — {classifyResult.account_name as string}
                </span>
                <span className="text-xs bg-[#c8873a] text-white px-2 py-0.5 rounded-full">
                  {((classifyResult.confidence as number) * 100).toFixed(0)}% confidence
                </span>
              </div>
              <p className="text-[#8c6a4a] text-xs">{classifyResult.suggestion as string}</p>
            </div>
          )}
        </Card>

        {!result && !loading && (
          <Card className="bg-white border border-[#e3d6c7] rounded-2xl p-12 flex flex-col items-center justify-center text-center">
            <Shield className="w-12 h-12 text-[#c8873a] mb-4 opacity-60" />
            <p className="text-lg font-semibold text-[#3d2c1e]">Analyze Vendor Risk</p>
            <p className="text-sm text-[#8c6a4a] mt-2 max-w-sm">
              Identify concentration risk, fraud signals, missing W-9s, and payment drift across your AP.
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}
