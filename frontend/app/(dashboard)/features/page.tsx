"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import TopBar from "@/components/TopBar";
import { api, StartupHealth } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Cpu,
  DollarSign,
  Loader2,
  Mail,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  WandSparkles,
} from "lucide-react";

export default function FeaturesPage() {
  const { openChat } = useAppStore();

  const [health, setHealth] = useState<StartupHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);

  const [emailRecipients, setEmailRecipients] = useState<string>("sysswork@gmail.com");
  const [hiringCtc, setHiringCtc] = useState<number>(1800000);
  const [hiringMonth, setHiringMonth] = useState<string>(new Date().toISOString().slice(0, 7));
  const [hiringImpact, setHiringImpact] = useState<any | null>(null);
  const [claudeMonthlyCost, setClaudeMonthlyCost] = useState<number>(18000);
  const [claudeProductTag, setClaudeProductTag] = useState<"ai_lab" | "shared" | "orchard" | "sprouts">("ai_lab");

  const defaultCompanyId = health?.default_company_id || null;
  const smtpMissingKeys = (health?.credential_readiness?.missing_keys || []).filter((key: string) =>
    ["SMTP_HOST", "SMTP_USER", "SMTP_PASS"].includes(key)
  );

  const healthTone = useMemo(() => {
    if (!health) return "neutral";
    return health.status === "ok" ? "ok" : "warning";
  }, [health]);

  const loadAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const startup = await api.getStartupHealth();
      setHealth(startup);

      if (startup.default_company_id) {
        const contacts = await api.getNotificationContacts(startup.default_company_id);
        setEmailRecipients((contacts.email_recipients || ["sysswork@gmail.com"]).join(", "));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load feature controls.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadAll();
  }, []);

  const withAction = async (key: string, fn: () => Promise<void>, successMessage: string) => {
    setBusyAction(key);
    setActionError(null);
    setActionMessage(null);
    try {
      await fn();
      setActionMessage(successMessage);
      await loadAll();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusyAction(null);
    }
  };

  const runSeedAlerts = async () => {
    await withAction(
      "seed-alerts",
      async () => {
        await api.seedDemoAlerts();
      },
      "Demo anomalies seeded. Open Anomalies page to review them."
    );
  };

  const runAnomalyScan = async () => {
    await withAction(
      "scan-alerts",
      async () => {
        await api.triggerScan();
      },
      "Anomaly scan triggered successfully."
    );
  };

  const runGenerateQuarterlyLiability = async () => {
    if (!defaultCompanyId) {
      setActionError("No default company configured yet.");
      return;
    }
    const year = new Date().getFullYear();
    const quarter = Math.floor(new Date().getMonth() / 3) + 1;
    await withAction(
      "generate-tax",
      async () => {
        await api.createQuarterlyLiability(defaultCompanyId, year, quarter);
      },
      `Quarterly liability generated for Q${quarter} ${year}.`
    );
  };

  const runSaveEmailRecipients = async () => {
    if (!defaultCompanyId) {
      setActionError("No default company configured yet.");
      return;
    }
    const recipients = emailRecipients
      .split(",")
      .map((x: string) => x.trim())
      .filter(Boolean);
    if (!recipients.length) {
      setActionError("Add at least one email recipient.");
      return;
    }

    await withAction(
      "save-email",
      async () => {
        await api.updateNotificationContacts(defaultCompanyId, { email_recipients: recipients });
      },
      "Email recipients updated successfully."
    );
  };

  const runTestEmail = async () => {
    if (!defaultCompanyId) {
      setActionError("No default company configured yet.");
      return;
    }
    setBusyAction("test-email");
    setActionError(null);
    setActionMessage(null);
    try {
      const result = await api.sendTestNotification(defaultCompanyId);
      setActionMessage(result.message || "Test notification processed.");
      await loadAll();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusyAction(null);
    }
  };

  const runHiringImpact = async () => {
    if (!defaultCompanyId) {
      setActionError("No default company configured yet.");
      return;
    }

    await withAction(
      "hiring-impact",
      async () => {
        const payload = await api.getHiringImpact({
          company_id: defaultCompanyId,
          annual_ctc_inr: hiringCtc,
          join_month: hiringMonth,
        });
        setHiringImpact(payload);
      },
      "Hiring impact calculated."
    );
  };

  const runCaptureClaudeSubscription = async () => {
    if (!defaultCompanyId) {
      setActionError("No default company configured yet.");
      return;
    }
    if (!claudeMonthlyCost || claudeMonthlyCost <= 0) {
      setActionError("Enter a valid Claude monthly cost.");
      return;
    }

    const billingPeriod = new Date().toISOString().slice(0, 7);
    await withAction(
      "capture-claude",
      async () => {
        await api.createTechCost({
          company_id: defaultCompanyId,
          cost_type: "saas_tool",
          product_tag: claudeProductTag,
          amount_inr: claudeMonthlyCost,
          billing_period: billingPeriod,
          vendor_name: "Anthropic Claude",
          description: `Claude subscription ${billingPeriod}`,
          is_recurring: true,
        });
      },
      "Claude subscription captured to ledger. It will now flow into expense and burn analysis."
    );
  };

  const runLeadershipDrill = async () => {
    if (!defaultCompanyId) {
      setActionError("No default company configured yet.");
      return;
    }

    const year = new Date().getFullYear();
    const quarter = Math.floor(new Date().getMonth() / 3) + 1;

    await withAction(
      "leadership-drill",
      async () => {
        await api.seedDemoAlerts();
        await api.createQuarterlyLiability(defaultCompanyId, year, quarter);
        await api.sendTestNotification(defaultCompanyId);
        openChat("Create a CFO leadership brief combining anomaly risk, tax liability, and runway actions for the next 30 days.");
      },
      "Leadership drill completed: anomalies seeded, tax liability generated, notification sent, and CFO brief opened in chat."
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#f6f4ef] to-[#ece6db] text-[#1d1b17]">
      <TopBar title="Action Hub" />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6">
        <section className="rounded-2xl border border-[#d8cebb] bg-[#fffaf0] p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#7a6a4f]">Action Hub</p>
              <h1 className="mt-2 text-2xl font-semibold text-[#2f2618]">Operate The Smart CFO Features</h1>

            </div>
            <button
              onClick={() => void loadAll()}
              className="inline-flex items-center gap-2 rounded-lg border border-[#c9b693] bg-white px-4 py-2 text-sm font-medium text-[#4b3d2a] hover:bg-[#f8f1e4]"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        </section>

        {actionMessage && (
          <section className="rounded-xl border border-[#b8ddbf] bg-[#edf8ef] p-3 text-sm text-[#2f6a45]">{actionMessage}</section>
        )}
        {actionError && (
          <section className="rounded-xl border border-[#ebc1b8] bg-[#fff2ef] p-3 text-sm text-[#9f3f30]">{actionError}</section>
        )}
        {error && (
          <section className="rounded-xl border border-[#ebc1b8] bg-[#fff2ef] p-3 text-sm text-[#9f3f30]">{error}</section>
        )}

        <section className="rounded-2xl border border-[#d8cebb] bg-[#fffdf8] p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between gap-4">
            <h2 className="text-lg font-semibold text-[#3a2f1f]">Platform Health</h2>
            {healthTone === "ok" ? (
              <span className="inline-flex items-center gap-1 rounded-full border border-[#94b79a] bg-[#edf8ef] px-3 py-1 text-xs font-semibold text-[#2f5a34]">
                <CheckCircle2 className="h-3.5 w-3.5" /> Healthy
              </span>
            ) : healthTone === "warning" ? (
              <span className="inline-flex items-center gap-1 rounded-full border border-[#d8b184] bg-[#fff3e4] px-3 py-1 text-xs font-semibold text-[#7d4f1c]">
                <TriangleAlert className="h-3.5 w-3.5" /> Attention needed
              </span>
            ) : null}
          </div>
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-[#6c5b41]"><Loader2 className="h-4 w-4 animate-spin" />Loading...</div>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-4 text-sm">
              <div className="rounded-xl border border-[#eadfcd] bg-white p-3">
                <p className="text-xs uppercase tracking-wide text-[#7a6a4f]">Default Company</p>
                <p className="mt-1 font-semibold text-[#2f2618] break-all">{defaultCompanyId || "Not configured"}</p>
              </div>
              <div className="rounded-xl border border-[#eadfcd] bg-white p-3">
                <p className="text-xs uppercase tracking-wide text-[#7a6a4f]">Issues</p>
                <p className="mt-1 text-xl font-semibold text-[#2f2618]">{health?.issues?.length ?? 0}</p>
              </div>
              <div className="rounded-xl border border-[#eadfcd] bg-white p-3">
                <p className="text-xs uppercase tracking-wide text-[#7a6a4f]">Actionable Fixes</p>
                <p className="mt-1 text-xl font-semibold text-[#2f2618]">{health?.actions?.length ?? 0}</p>
              </div>
              <div className="rounded-xl border border-[#eadfcd] bg-white p-3">
                <p className="text-xs uppercase tracking-wide text-[#7a6a4f]">Missing Credentials</p>
                <p className="mt-1 text-xl font-semibold text-[#2f2618]">{health?.credential_readiness?.missing_keys?.length ?? 0}</p>
              </div>
            </div>
          )}
        </section>

        <section className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <article className="rounded-2xl border border-[#d8cebb] bg-[#fffdf8] p-5 shadow-sm">
            <h3 className="text-base font-semibold text-[#3a2f1f]">Anomaly Operations</h3>
            <p className="mt-1 text-sm text-[#5f513c]">Populate and scan anomalies so the Anomalies page has immediate, useful data.</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <button onClick={() => void runSeedAlerts()} disabled={busyAction === "seed-alerts"} className="rounded-lg border border-[#ceb89a] bg-[#f9f1e2] px-3 py-1.5 text-xs font-semibold text-[#513f27] hover:bg-[#f2e6d2] disabled:opacity-70">
                {busyAction === "seed-alerts" ? "Seeding..." : "Seed demo anomalies"}
              </button>
              <button onClick={() => void runAnomalyScan()} disabled={busyAction === "scan-alerts"} className="rounded-lg border border-[#ceb89a] bg-[#f9f1e2] px-3 py-1.5 text-xs font-semibold text-[#513f27] hover:bg-[#f2e6d2] disabled:opacity-70">
                {busyAction === "scan-alerts" ? "Scanning..." : "Run anomaly scan"}
              </button>
              <Link href="/anomalies" className="inline-flex items-center gap-1 rounded-lg border border-[#d4c7b3] bg-white px-3 py-1.5 text-xs font-semibold text-[#5e4d36] hover:bg-[#f9f3e8]">
                Open anomalies <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </article>

          <article className="rounded-2xl border border-[#d8cebb] bg-[#fffdf8] p-5 shadow-sm">
            <h3 className="text-base font-semibold text-[#3a2f1f]">Tax Operations</h3>
            <p className="mt-1 text-sm text-[#5f513c]">Generate current quarter liability so Tax page stops showing zeros for empty datasets.</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <button onClick={() => void runGenerateQuarterlyLiability()} disabled={busyAction === "generate-tax"} className="rounded-lg border border-[#ceb89a] bg-[#f9f1e2] px-3 py-1.5 text-xs font-semibold text-[#513f27] hover:bg-[#f2e6d2] disabled:opacity-70">
                {busyAction === "generate-tax" ? "Generating..." : "Generate quarterly liability"}
              </button>
              <Link href="/tax" className="inline-flex items-center gap-1 rounded-lg border border-[#d4c7b3] bg-white px-3 py-1.5 text-xs font-semibold text-[#5e4d36] hover:bg-[#f9f3e8]">
                Open tax page <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </article>
        </section>

        <section className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <article className="rounded-2xl border border-[#d8cebb] bg-[#fffdf8] p-5 shadow-sm">
            <h3 className="inline-flex items-center gap-2 text-base font-semibold text-[#3a2f1f]"><Cpu className="h-4 w-4" />AI Stack Cost Capture</h3>

            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-[#7a6a4f]">
                Claude monthly cost (INR)
                <input
                  type="number"
                  value={claudeMonthlyCost}
                  onChange={(e) => setClaudeMonthlyCost(Number(e.target.value || 0))}
                  className="mt-1 w-full rounded-xl border border-[#d6c8b4] bg-[#fffaf2] px-3 py-2 text-sm text-[#2a2017]"
                />
              </label>
              <label className="text-xs font-semibold uppercase tracking-wide text-[#7a6a4f]">
                Product allocation
                <select
                  value={claudeProductTag}
                  onChange={(e) => setClaudeProductTag(e.target.value as "ai_lab" | "shared" | "orchard" | "sprouts")}
                  className="mt-1 w-full rounded-xl border border-[#d6c8b4] bg-[#fffaf2] px-3 py-2 text-sm text-[#2a2017]"
                >
                  <option value="ai_lab">AI Lab</option>
                  <option value="shared">Shared</option>
                  <option value="orchard">Orchard</option>
                  <option value="sprouts">Sprouts</option>
                </select>
              </label>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <button onClick={() => void runCaptureClaudeSubscription()} disabled={busyAction === "capture-claude"} className="rounded-lg border border-[#ceb89a] bg-[#f9f1e2] px-3 py-1.5 text-xs font-semibold text-[#513f27] hover:bg-[#f2e6d2] disabled:opacity-70">
                {busyAction === "capture-claude" ? "Capturing..." : "Capture Claude subscription"}
              </button>
              <Link href="/expenses" className="inline-flex items-center gap-1 rounded-lg border border-[#d4c7b3] bg-white px-3 py-1.5 text-xs font-semibold text-[#5e4d36] hover:bg-[#f9f3e8]">
                Open expenses <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </article>



          <article className="rounded-2xl border border-[#d8cebb] bg-[#fffdf8] p-5 shadow-sm">
            <h3 className="inline-flex items-center gap-2 text-base font-semibold text-[#3a2f1f]"><WandSparkles className="h-4 w-4" />Hiring Impact Calculator</h3>
            <p className="mt-1 text-sm text-[#5f513c]">Leadership planning tool: compute runway effect of adding a hire package.</p>

            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-[#7a6a4f]">
                Annual CTC (INR)
                <input
                  type="number"
                  value={hiringCtc}
                  onChange={(e) => setHiringCtc(Number(e.target.value || 0))}
                  className="mt-1 w-full rounded-xl border border-[#d6c8b4] bg-[#fffaf2] px-3 py-2 text-sm text-[#2a2017]"
                />
              </label>
              <label className="text-xs font-semibold uppercase tracking-wide text-[#7a6a4f]">
                Join month
                <input
                  type="month"
                  value={hiringMonth}
                  onChange={(e) => setHiringMonth(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-[#d6c8b4] bg-[#fffaf2] px-3 py-2 text-sm text-[#2a2017]"
                />
              </label>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              <button onClick={() => void runHiringImpact()} disabled={busyAction === "hiring-impact"} className="rounded-lg border border-[#ceb89a] bg-[#f9f1e2] px-3 py-1.5 text-xs font-semibold text-[#513f27] hover:bg-[#f2e6d2] disabled:opacity-70">
                {busyAction === "hiring-impact" ? "Calculating..." : "Calculate impact"}
              </button>
              <Link href="/dashboard/cto" className="inline-flex items-center gap-1 rounded-lg border border-[#d4c7b3] bg-white px-3 py-1.5 text-xs font-semibold text-[#5e4d36] hover:bg-[#f9f3e8]">
                Open CTO planner <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            {hiringImpact && (
              <div className="mt-4 rounded-xl border border-[#e5d7c2] bg-[#fff8ec] p-3 text-sm text-[#4f3f2b]">
                <p>Baseline runway: <strong>{hiringImpact.baseline_runway_months}</strong> months</p>
                <p>New runway: <strong>{hiringImpact.new_runway_months}</strong> months</p>
                <p>Impact: <strong>{hiringImpact.runway_impact_days}</strong> days</p>
              </div>
            )}
          </article>
        </section>

        <section className="rounded-2xl border border-[#d8cebb] bg-[#fffdf8] p-5 shadow-sm">
          <h2 className="inline-flex items-center gap-2 text-base font-semibold text-[#3a2f1f]"><Sparkles className="h-4 w-4" />Smart CFO Agent For Leadership</h2>

          <div className="mt-3 flex flex-wrap gap-2">
            <button onClick={() => openChat("Create a CEO brief with top 5 financial risks and recommended actions")}
              className="rounded-lg border border-[#ceb89a] bg-[#f9f1e2] px-3 py-1.5 text-xs font-semibold text-[#513f27] hover:bg-[#f2e6d2]">
              CEO risk brief
            </button>
            <button onClick={() => openChat("Build a board meeting narrative: burn trend, runway guardrails, and what changed this month")}
              className="rounded-lg border border-[#ceb89a] bg-[#f9f1e2] px-3 py-1.5 text-xs font-semibold text-[#513f27] hover:bg-[#f2e6d2]">
              Board narrative
            </button>
            <button onClick={() => openChat("Analyze runway sensitivity if hiring 2 engineers and 1 sales lead this quarter")}
              className="rounded-lg border border-[#ceb89a] bg-[#f9f1e2] px-3 py-1.5 text-xs font-semibold text-[#513f27] hover:bg-[#f2e6d2]">
              Hiring trade-off analysis
            </button>
            <button onClick={() => openChat("Where can we cut 12% opex in 45 days without affecting product velocity? Give concrete levers.")}
              className="rounded-lg border border-[#ceb89a] bg-[#f9f1e2] px-3 py-1.5 text-xs font-semibold text-[#513f27] hover:bg-[#f2e6d2]">
              Cost-cutting plan
            </button>
            <button onClick={() => openChat("Summarize anomalies, tax exposure, and cash runway for leadership meeting")}
              className="rounded-lg border border-[#ceb89a] bg-[#f9f1e2] px-3 py-1.5 text-xs font-semibold text-[#513f27] hover:bg-[#f2e6d2]">
              Leadership summary
            </button>
            <button onClick={() => void runLeadershipDrill()} disabled={busyAction === "leadership-drill"}
              className="rounded-lg border border-[#ceb89a] bg-[#f6e8cf] px-3 py-1.5 text-xs font-semibold text-[#513f27] hover:bg-[#efdcb8] disabled:opacity-70">
              {busyAction === "leadership-drill" ? "Running..." : "Run full leadership drill"}
            </button>
            <Link href="/agent" className="inline-flex items-center gap-1 rounded-lg border border-[#d4c7b3] bg-white px-3 py-1.5 text-xs font-semibold text-[#5e4d36] hover:bg-[#f9f3e8]">
              Open full AI agent <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </section>

        <section className="rounded-2xl border border-[#d8cebb] bg-[#fffdf8] p-4 text-xs text-[#6f624f]">
          <p className="inline-flex items-center gap-1"><ShieldCheck className="h-3.5 w-3.5" />This hub intentionally excludes Dashboard, Runway, Expenses, Revenue, Tax, Scenarios, and Benchmarking module summaries from the sidebar.</p>
          <p className="mt-2 inline-flex items-center gap-1"><DollarSign className="h-3.5 w-3.5" />Use this hub for showcase actions: create data, trigger workflows, and demonstrate decision support in live demos.</p>
          {health?.credential_readiness?.missing_keys?.length ? (
            <p className="mt-2 inline-flex items-center gap-1 text-[#8d3f30]"><AlertCircle className="h-3.5 w-3.5" />Missing credentials can limit connectors and notifications: {health.credential_readiness.missing_keys.join(", ")}</p>
          ) : null}
        </section>
      </main>
    </div>
  );
}
