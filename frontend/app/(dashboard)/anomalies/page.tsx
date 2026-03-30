"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, Badge, Title } from "@tremor/react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import api from "@/lib/api";
import { cn } from "@/lib/utils";
import { AlertTriangle, Mail, Search, Zap } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V1 = API_BASE.replace(/\/$/, "").endsWith("/api/v1")
  ? API_BASE.replace(/\/$/, "")
  : `${API_BASE.replace(/\/$/, "")}/api/v1`;

type AnomalySeverity = "critical" | "warning" | "info";

type FinancialAnomaly = {
  severity?: AnomalySeverity;
  message?: string;
  type?: string;
  runway_months?: number;
  pct_change?: number;
  action?: string;
};

type FinancialHealth = {
  risk_score?: number;
  health_status?: string;
  critical_anomalies?: number;
  runway_months?: number;
  burn_multiple?: number;
  anomalies?: FinancialAnomaly[];
};

type AlertContacts = {
  ceo?: string;
  finance?: string[];
  email_recipients?: string[];
};

export default function AnomaliesPage() {
  const { openChat } = useAppStore();
  const [companyId, setCompanyId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState<FinancialHealth | null>(null);
  const [anomalies, setAnomalies] = useState<FinancialAnomaly[]>([]);
  const [filter, setFilter] = useState<"all" | "critical" | "warning" | "info">("all");
  const [query, setQuery] = useState("");
  const [showConfig, setShowConfig] = useState(false);
  const [configError, setConfigError] = useState<string | null>(null);
  const [ceoEmail, setCeoEmail] = useState("");
  const [financeEmails, setFinanceEmails] = useState<string[]>([]);
  const [genericEmails, setGenericEmails] = useState<string[]>([]);
  const [lastAlert, setLastAlert] = useState<string | null>(null);

  useEffect(() => {
    const loadCompany = async () => {
      const health = await api.getStartupHealth();
      setCompanyId(health.default_company_id || "");
    };
    loadCompany();
  }, []);

  useEffect(() => {
    const loadHealth = async () => {
      if (!companyId) return;
      setLoading(true);
      try {
        const res = await fetch(`${API_V1}/financial-alerts/financial-health/${companyId}`);
        if (res.ok) {
          const data = await res.json();
          setHealth(data);
          setAnomalies(data.anomalies || []);
        }
      } catch (err) {
        console.error("Failed to load health:", err);
      } finally {
        setLoading(false);
      }
    };
    loadHealth();
  }, [companyId]);

  useEffect(() => {
    const loadContacts = async () => {
      if (!companyId) return;
      try {
        const res = await fetch(`${API_V1}/notifications/contacts/${companyId}`);
        if (res.ok) {
          const data: AlertContacts = await res.json();
          setCeoEmail(data.ceo || "");
          setFinanceEmails(data.finance || []);
          setGenericEmails(data.email_recipients || []);
        }
      } catch (err) {
        console.error("Failed to load contacts:", err);
      }
    };
    loadContacts();
  }, [companyId]);

  const filteredAnomalies = useMemo(() => {
    return anomalies.filter((a: FinancialAnomaly) => {
      const matchesSeverity = filter === "all" || a.severity === filter;
      const normalized = `${a.message} ${a.type}`.toLowerCase();
      const matchesQuery = !query.trim() || normalized.includes(query.trim().toLowerCase());
      return matchesSeverity && matchesQuery;
    });
  }, [anomalies, filter, query]);

  const handleSendAlerts = async () => {
    if (!companyId) return;
    try {
      setLastAlert("Sending...");
      const res = await fetch(`${API_V1}/financial-alerts/send-alerts/${companyId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-User-Role": "finance" },
      });
      if (res.ok) {
        const data = await res.json();
        setLastAlert(`✅ Alerts sent to ${data.recipients?.length || 0} recipients`);
        setTimeout(() => setLastAlert(null), 5000);
      } else {
        setLastAlert("❌ Failed to send alerts");
        setTimeout(() => setLastAlert(null), 5000);
      }
    } catch (err) {
      setLastAlert("❌ Error sending alerts");
      setTimeout(() => setLastAlert(null), 5000);
    }
  };

  const handleTestAlert = async () => {
    if (!companyId) return;
    try {
      const res = await fetch(`${API_V1}/financial-alerts/test-alert/${companyId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (res.ok) {
        setLastAlert("✅ Test alert sent!");
        setTimeout(() => setLastAlert(null), 5000);
      } else {
        setLastAlert("❌ Test alert failed");
        setTimeout(() => setLastAlert(null), 5000);
      }
    } catch (err) {
      setLastAlert("❌ Test alert failed");
      setTimeout(() => setLastAlert(null), 5000);
    }
  };

  const handleSaveAlertConfig = async () => {
    if (!companyId) return;
    setConfigError(null);
    
    // Validate at least one email is configured
    const allEmails = [ceoEmail, ...financeEmails, ...genericEmails]
      .filter((e) => e && e.trim().includes("@"))
      .map(e => e.trim());
    
    if (allEmails.length === 0) {
      setConfigError("Please add at least one valid email address");
      return;
    }
    
    try {
      const payload = {
        ceo: ceoEmail.trim() || null,
        finance: financeEmails.map(e => e.trim()).filter(e => e && e.includes("@")),
        email_recipients: genericEmails.map(e => e.trim()).filter(e => e && e.includes("@")),
      };
      
      const res = await fetch(`${API_V1}/financial-alerts/configure-alerts/${companyId}`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Failed to save (${res.status})`);
      }
      
      const resultData = await res.json();
      setShowConfig(false);
      setLastAlert(`✅ Alerts configured for ${resultData.recipients_count || allEmails.length} recipients!`);
      
      // Reload contacts to reflect saved state
      const contactRes = await fetch(`${API_V1}/notifications/contacts/${companyId}`);
      if (contactRes.ok) {
        const contactData = await contactRes.json();
        setCeoEmail(contactData.ceo || "");
        setFinanceEmails(contactData.finance || []);
        setGenericEmails(contactData.email_recipients || []);
      }
      
      setTimeout(() => setLastAlert(null), 5000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to save configuration";
      setConfigError(msg);
      console.error("Config error:", err);
    }
  };

  if (loading) {
    return <div className="min-h-screen bg-[#f6f3ee]" />;
  }

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Financial Risk & Anomalies" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">
        {/* Header */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Zap className="h-3.5 w-3.5" />
                Real-time monitoring
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">Financial Risk Dashboard</h1>
              <p className="mt-2 text-sm text-[#5f5344]">Anomaly detection & email alerts for CEO & Finance team</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={handleTestAlert}
                className="inline-flex items-center gap-2 rounded-xl border border-[#d4c2a5] bg-[#fff3df] px-4 py-2.5 text-sm font-medium text-[#6a4d26] hover:bg-[#f6e5c8]"
              >
                <Mail className="h-4 w-4" />
                Test Email
              </button>
              <button
                onClick={handleSendAlerts}
                className="inline-flex items-center gap-2 rounded-xl bg-red-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-red-700"
              >
                <AlertTriangle className="h-4 w-4" />
                Send Alerts Now
              </button>
              <button
                onClick={() => setShowConfig(!showConfig)}
                className="inline-flex items-center gap-2 rounded-xl border border-[#ccb89a] bg-[#fff9ee] px-4 py-2.5 text-sm font-medium text-[#5f4828] hover:bg-[#f8ebd7]"
              >
                ⚙️ Configure
              </button>
            </div>
          </div>
        </section>

        {lastAlert && (
          <div className={cn("rounded-xl border px-4 py-3 text-sm font-medium", 
            lastAlert.includes("✅") 
              ? "border-green-300 bg-green-50 text-green-700"
              : "border-amber-300 bg-amber-50 text-amber-700"
          )}>
            {lastAlert}
          </div>
        )}

        {/* Alert Configuration */}
        {showConfig && (
          <Card className="bg-white border-[#e4d8cb] p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <Title className="text-[#2a231d]">Configure Email Alerts</Title>
                <p className="text-xs text-[#7b6f5e] mt-1">Choose who receives financial anomaly alerts</p>
              </div>
              <button
                onClick={async () => {
                  await new Promise(r => setTimeout(r, 300));
                  try {
                    const res = await fetch(`${API_V1}/notifications/contacts/${companyId}`);
                    if (res.ok) {
                      const data: AlertContacts = await res.json();
                      setCeoEmail(data.ceo || "");
                      setFinanceEmails(data.finance || []);
                      setGenericEmails(data.email_recipients || []);
                    }
                  } catch (err) {
                    console.error("Failed to reload:", err);
                  }
                }}
                className="text-xs px-3 py-1 rounded-full bg-[#f3ede2] text-[#5f5344] hover:bg-[#e8dfd5] transition-colors"
              >
                ↻ Reload saved
              </button>
            </div>

            {/* Currently Configured Display */}
            <div className="mb-6 p-4 rounded-lg bg-[#f9f7f3] border border-[#e8dfd5]">
              <p className="text-xs font-semibold text-[#6f655a] uppercase mb-3">✓ Currently Configured</p>
              <div className="space-y-2">
                <div className="flex items-start gap-2">
                  <span className="text-xs font-bold text-[#5f5344] min-w-fit">CEO:</span>
                  <span className="text-sm text-[#4a443f]">{ceoEmail ? <span className="inline-block px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">{ceoEmail}</span> : <span className="text-[#9a9187] italic">Not set</span>}</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-xs font-bold text-[#5f5344] min-w-fit">Finance:</span>
                  <div className="flex flex-wrap gap-1">
                    {financeEmails.length > 0 ? (
                      financeEmails.map((e, i) => <span key={i} className="inline-block px-2 py-1 bg-amber-100 text-amber-700 rounded text-xs">{e}</span>)
                    ) : (
                      <span className="text-[#9a9187] italic text-sm">Not set</span>
                    )}
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-xs font-bold text-[#5f5344] min-w-fit\">Other:</span>
                  <div className="flex flex-wrap gap-1">
                    {genericEmails.length > 0 ? (
                      genericEmails.map((e, i) => <span key={i} className="inline-block px-2 py-1 bg-green-100 text-green-700 rounded text-xs">{e}</span>)
                    ) : (
                      <span className="text-[#9a9187] italic text-sm">Not set</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 space-y-4 border-t border-[#e8dfd5] pt-4">
              <div>
                <label className="block text-sm font-medium text-[#5f5344] mb-1">👤 CEO Email</label>
                <input
                  type="email"
                  value={ceoEmail}
                  onChange={(e: any) => setCeoEmail(e.target.value)}
                  className="w-full rounded-lg border border-[#d7cdbc] px-3 py-2 text-sm focus:outline-none focus:border-[#5f5344] focus:ring-1 focus:ring-[#5f5344]"
                  placeholder="outlandishaditi11@gmail.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[#5f5344] mb-1">💼 Finance Team (comma-separated)</label>
                <textarea
                  value={financeEmails.join(", ")}
                  onChange={(e: any) => setFinanceEmails(e.target.value.split(",").map((v: string) => v.trim()).filter((v: string) => v))}
                  className="w-full rounded-lg border border-[#d7cdbc] px-3 py-2 text-sm focus:outline-none focus:border-[#5f5344] focus:ring-1 focus:ring-[#5f5344]"
                  placeholder="sysswork@gmail.com, other@company.com"
                  rows={2}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[#5f5344] mb-1">📧 Additional Recipients (comma-separated)</label>
                <textarea
                  value={genericEmails.join(", ")}
                  onChange={(e: any) => setGenericEmails(e.target.value.split(",").map((v: string) => v.trim()).filter((v: string) => v))}
                  className="w-full rounded-lg border border-[#d7cdbc] px-3 py-2 text-sm focus:outline-none focus:border-[#5f5344] focus:ring-1 focus:ring-[#5f5344]"
                  placeholder="extra@company.com"
                  rows={2}
                />
              </div>
              {configError && <p className="text-sm text-red-600">{configError}</p>}
              <div className="flex gap-2 pt-2">
                <button
                  onClick={handleSaveAlertConfig}
                  className="rounded-lg bg-[#1f1a16] px-4 py-2 text-sm font-medium text-white hover:bg-[#282219]"
                >
                  Save Configuration
                </button>
                <button
                  onClick={() => setShowConfig(false)}
                  className="rounded-lg border border-[#d7cdbc] px-4 py-2 text-sm font-medium text-[#5f5344] hover:bg-[#f9f6f2]"
                >
                  Cancel
                </button>
              </div>
            </div>
          </Card>
        )}

        {/* Risk Score Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card className="bg-gradient-to-br from-red-50 to-red-100/50 border-red-200">
            <p className="text-xs font-semibold uppercase text-[#6f655a]">Risk Score</p>
            <p className="mt-2 text-3xl font-bold text-[#9b3a1f]">{health?.risk_score || 0}/100</p>
            <p className="mt-1 text-xs text-red-700">
              Status: <span className="font-semibold">{health?.health_status?.toUpperCase()}</span>
            </p>
          </Card>

          <Card className="bg-gradient-to-br from-amber-50 to-amber-100/50 border-amber-200">
            <p className="text-xs font-semibold uppercase text-[#6f655a]">Anomalies</p>
            <p className="mt-2 text-3xl font-bold text-amber-900">{anomalies.length}</p>
            <p className="mt-1 text-xs text-amber-700">
              {health?.critical_anomalies || 0} critical
            </p>
          </Card>

          <Card className="bg-gradient-to-br from-blue-50 to-blue-100/50 border-blue-200">
            <p className="text-xs font-semibold uppercase text-[#6f655a]">Runway</p>
            <p className="mt-2 text-3xl font-bold text-blue-900">{health?.runway_months?.toFixed(1) || "0"}mo</p>
            <p className="mt-1 text-xs text-blue-700">
              Burn: {health?.burn_multiple?.toFixed(2) || "0"}x
            </p>
          </Card>

          <Card className="bg-gradient-to-br from-purple-50 to-purple-100/50 border-purple-200">
            <p className="text-xs font-semibold uppercase text-[#6f655a]">Alerts Sent</p>
            <p className="mt-2 text-3xl font-bold text-purple-900">
              {[ceoEmail, ...financeEmails, ...genericEmails].filter((e) => e && e.includes("@")).length}
            </p>
            <p className="mt-1 text-xs text-purple-700">Recipients configured</p>
          </Card>
        </div>

        {/* Anomalies List */}
        <Card className="bg-white border-[#e4d8cb]">
          <Title className="text-[#2a231d]">Detected Anomalies</Title>

          <div className="mt-6 flex flex-wrap gap-2">
            {(["all", "critical", "warning", "info"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`rounded-full border px-3 py-1.5 text-xs font-medium ${
                  filter === f ? "border-[#b99561] bg-[#f5e7cf] text-[#6b4a1e]" : "border-[#dbcdb9] bg-[#fffdf8] text-[#7a6a57]"
                }`}
              >
                {f}
              </button>
            ))}
            <div className="relative ml-auto w-full sm:w-64">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8a7b68]" />
              <input
                value={query}
                onChange={(e: any) => setQuery(e.target.value)}
                className="w-full rounded-xl border border-[#dbcdb9] bg-[#fffdf8] py-2 pl-10 pr-3 text-sm"
                placeholder="Search anomalies"
              />
            </div>
          </div>

          <div className="mt-6 space-y-4">
            {filteredAnomalies.length === 0 ? (
              <p className="py-8 text-center text-sm text-[#7a6f62]">✅ No anomalies detected. Your finances are looking good!</p>
            ) : (
              filteredAnomalies.map((anomaly: FinancialAnomaly, idx: number) => (
                <div
                  key={idx}
                  className={`rounded-lg border p-4 ${
                    anomaly.severity === "critical"
                      ? "border-red-300 bg-red-50"
                      : anomaly.severity === "warning"
                        ? "border-amber-300 bg-amber-50"
                        : "border-green-300 bg-green-50"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Badge
                          color={anomaly.severity === "critical" ? "red" : anomaly.severity === "warning" ? "amber" : "green"}
                        >
                          {anomaly.severity?.toUpperCase()}
                        </Badge>
                        <span className="font-semibold">{anomaly.type?.replace(/_/g, " ")}</span>
                      </div>
                      <p className="mt-2 text-sm font-medium text-[#2a231d]">{anomaly.message}</p>
                      <div className="mt-2 flex flex-wrap gap-4 text-xs text-[#6f655a]">
                        {anomaly.runway_months && <span>Runway Impact: -{anomaly.runway_months.toFixed(1)}mo</span>}
                        {anomaly.pct_change && <span>Change: {anomaly.pct_change.toFixed(1)}%</span>}
                        {anomaly.action && <span className="italic text-red-700">Action: {anomaly.action}</span>}
                      </div>
                    </div>
                    <button
                      onClick={() => openChat(`Analysis: ${anomaly.message}`)}
                      className="ml-4 rounded-lg bg-[#1f1a16] px-3 py-1 text-xs font-medium text-white hover:bg-[#282219]"
                    >
                      Analyze
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
