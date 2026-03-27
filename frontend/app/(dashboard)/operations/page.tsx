"use client";

import { useEffect, useMemo, useState } from "react";
import TopBar from "@/components/TopBar";
import {
  api,
  CollectionsAging,
  ForecastEnsemble,
  ForecastMonitor,
  FxRatesResponse,
  InvoiceDsoResponse,
  InvoiceQueueResponse,
  StartupHealth,
} from "@/lib/api";
import { Loader2, RefreshCw } from "lucide-react";

export default function OperationsPage() {
  const [health, setHealth] = useState<StartupHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [fxRates, setFxRates] = useState<FxRatesResponse | null>(null);
  const [forecastMonitor, setForecastMonitor] = useState<ForecastMonitor | null>(null);
  const [forecastEnsemble, setForecastEnsemble] = useState<ForecastEnsemble | null>(null);
  const [collections, setCollections] = useState<CollectionsAging | null>(null);
  const [queue, setQueue] = useState<InvoiceQueueResponse | null>(null);
  const [dso, setDso] = useState<InvoiceDsoResponse | null>(null);

  const [documentId, setDocumentId] = useState("");
  const [workflowNote, setWorkflowNote] = useState("");

  const companyId = health?.default_company_id || null;

  const prioritySummary = useMemo(() => {
    const items = queue?.queue || [];
    const counters = { critical: 0, high: 0, medium: 0, normal: 0 };
    items.forEach((item) => {
      if (item.priority === "critical") counters.critical += 1;
      else if (item.priority === "high") counters.high += 1;
      else if (item.priority === "medium") counters.medium += 1;
      else counters.normal += 1;
    });
    return counters;
  }, [queue]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const startup = await api.getStartupHealth();
      setHealth(startup);

      if (!startup.default_company_id) {
        setLoading(false);
        return;
      }

      const cid = startup.default_company_id;
      const [rates, monitor, ensemble, aging, invoiceQueue, invoiceDso] = await Promise.all([
        api.getFxRates(),
        api.getForecastMonitor(cid),
        api.getForecastEnsemble(cid),
        api.getCollectionsAging(cid),
        api.getInvoiceQueue(cid),
        api.getInvoiceDso(cid),
      ]);

      setFxRates(rates);
      setForecastMonitor(monitor);
      setForecastEnsemble(ensemble);
      setCollections(aging);
      setQueue(invoiceQueue);
      setDso(invoiceDso);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load operations data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  const withAction = async (key: string, action: () => Promise<void>, success: string) => {
    setBusy(key);
    setError(null);
    setMessage(null);
    try {
      await action();
      setMessage(success);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusy(null);
    }
  };

  const runFxSync = async () => {
    await withAction(
      "fx-sync",
      async () => {
        await api.syncLiveFx(["USD", "EUR", "GBP"]);
      },
      "FX sync completed."
    );
  };

  const runForecastRetrain = async () => {
    if (!companyId) {
      setError("No default company configured");
      return;
    }
    await withAction(
      "forecast-retrain",
      async () => {
        await api.retrainForecast(companyId);
      },
      "Forecast retraining completed."
    );
  };

  const runClassifyDocument = async () => {
    const id = documentId.trim();
    if (!id) {
      setError("Enter a valid document ID");
      return;
    }
    await withAction(
      "doc-classify",
      async () => {
        await api.classifyDocument(id);
      },
      "Document classified successfully."
    );
  };

  const runWorkflow = async (action: "approve" | "reject" | "post_ledger") => {
    const id = documentId.trim();
    if (!id) {
      setError("Enter a valid document ID");
      return;
    }
    await withAction(
      `doc-${action}`,
      async () => {
        await api.workflowDocument(id, action, workflowNote || undefined);
      },
      `Document workflow action '${action}' executed.`
    );
  };

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Operations Center" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#7a6a4f]">Ops Coverage</p>
              <h1 className="mt-2 text-2xl font-semibold text-[#2f2618]">Finance Operations Controls</h1>
              <p className="mt-1 text-sm text-[#5f5344]">Live FX sync, forecast governance, collections, and document workflow actions.</p>
            </div>
            <button
              onClick={() => void loadData()}
              className="inline-flex items-center gap-2 rounded-xl border border-[#ccb89a] bg-[#fff9ee] px-4 py-2.5 text-sm font-medium text-[#5f4828] hover:bg-[#f8ebd7]"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        </section>

        {error && <section className="rounded-xl border border-[#ebc1b8] bg-[#fff2ef] p-3 text-sm text-[#9f3f30]">{error}</section>}
        {message && <section className="rounded-xl border border-[#b8ddbf] bg-[#edf8ef] p-3 text-sm text-[#2f6a45]">{message}</section>}

        {!companyId && !loading && (
          <section className="rounded-xl border border-[#ebc1b8] bg-[#fff2ef] p-3 text-sm text-[#9f3f30]">
            No default company configured. Set up company data first to use the Operations Center.
          </section>
        )}

        {loading ? (
          <section className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-6 text-sm text-[#6f6252]">
            <div className="inline-flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading operations data...
            </div>
          </section>
        ) : (
          <>
            <section className="grid gap-6 lg:grid-cols-2">
              <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
                <h2 className="text-lg font-semibold text-[#2a2017]">Live FX</h2>
                <p className="mt-1 text-sm text-[#6f6252]">Sync latest rates and review persisted FX rows.</p>
                <button
                  onClick={() => void runFxSync()}
                  disabled={busy === "fx-sync"}
                  className="mt-4 rounded-lg border border-[#ceb89a] bg-[#f9f1e2] px-3 py-1.5 text-xs font-semibold text-[#513f27] hover:bg-[#f2e6d2] disabled:opacity-70"
                >
                  {busy === "fx-sync" ? "Syncing..." : "Sync live FX"}
                </button>
                <div className="mt-4 space-y-2 text-sm text-[#5f5243]">
                  {(fxRates?.rates || []).slice(0, 6).map((row) => (
                    <div key={`${row.base_currency}-${row.effective_date}`} className="flex items-center justify-between rounded-lg border border-[#eadfcd] bg-white px-3 py-2">
                      <span>{row.base_currency} -> {row.target_currency}</span>
                      <strong>{row.exchange_rate.toFixed(4)}</strong>
                    </div>
                  ))}
                </div>
              </article>

              <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
                <h2 className="text-lg font-semibold text-[#2a2017]">Forecast Governance</h2>
                <p className="mt-1 text-sm text-[#6f6252]">Monitor forecast error and retrain ensemble projections.</p>
                <button
                  onClick={() => void runForecastRetrain()}
                  disabled={busy === "forecast-retrain"}
                  className="mt-4 rounded-lg border border-[#ceb89a] bg-[#f9f1e2] px-3 py-1.5 text-xs font-semibold text-[#513f27] hover:bg-[#f2e6d2] disabled:opacity-70"
                >
                  {busy === "forecast-retrain" ? "Retraining..." : "Retrain now"}
                </button>
                <div className="mt-4 grid grid-cols-3 gap-2 text-sm">
                  <div className="rounded-lg border border-[#eadfcd] bg-white p-2">
                    <p className="text-xs text-[#7a6a4f]">MAPE</p>
                    <p className="font-semibold">{forecastMonitor?.mape_cash?.toFixed(2) ?? "-"}%</p>
                  </div>
                  <div className="rounded-lg border border-[#eadfcd] bg-white p-2">
                    <p className="text-xs text-[#7a6a4f]">MAE</p>
                    <p className="font-semibold">{forecastMonitor?.mae_cash?.toFixed(2) ?? "-"}</p>
                  </div>
                  <div className="rounded-lg border border-[#eadfcd] bg-white p-2">
                    <p className="text-xs text-[#7a6a4f]">Runway</p>
                    <p className="font-semibold">{forecastEnsemble?.runway_months?.toFixed(1) ?? "-"} mo</p>
                  </div>
                </div>
              </article>
            </section>

            <section className="grid gap-6 lg:grid-cols-2">
              <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
                <h2 className="text-lg font-semibold text-[#2a2017]">Collections & DSO</h2>
                <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                  <div className="rounded-lg border border-[#eadfcd] bg-white p-3">
                    <p className="text-xs text-[#7a6a4f]">Open AR</p>
                    <p className="font-semibold">{collections?.ar.total_open?.toLocaleString() ?? "-"}</p>
                  </div>
                  <div className="rounded-lg border border-[#eadfcd] bg-white p-3">
                    <p className="text-xs text-[#7a6a4f]">Open AP</p>
                    <p className="font-semibold">{collections?.ap.total_open?.toLocaleString() ?? "-"}</p>
                  </div>
                  <div className="rounded-lg border border-[#eadfcd] bg-white p-3">
                    <p className="text-xs text-[#7a6a4f]">DSO</p>
                    <p className="font-semibold">{dso?.dso_days?.toFixed(1) ?? "-"} days</p>
                  </div>
                  <div className="rounded-lg border border-[#eadfcd] bg-white p-3">
                    <p className="text-xs text-[#7a6a4f]">Overdue AR</p>
                    <p className="font-semibold">{collections?.overdue_receivables?.length ?? 0}</p>
                  </div>
                </div>
              </article>

              <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
                <h2 className="text-lg font-semibold text-[#2a2017]">Invoice Queue Priority</h2>
                <div className="mt-3 grid grid-cols-4 gap-2 text-sm">
                  <div className="rounded-lg border border-[#eadfcd] bg-white p-2 text-center"><p className="text-xs">Critical</p><p className="font-semibold">{prioritySummary.critical}</p></div>
                  <div className="rounded-lg border border-[#eadfcd] bg-white p-2 text-center"><p className="text-xs">High</p><p className="font-semibold">{prioritySummary.high}</p></div>
                  <div className="rounded-lg border border-[#eadfcd] bg-white p-2 text-center"><p className="text-xs">Medium</p><p className="font-semibold">{prioritySummary.medium}</p></div>
                  <div className="rounded-lg border border-[#eadfcd] bg-white p-2 text-center"><p className="text-xs">Normal</p><p className="font-semibold">{prioritySummary.normal}</p></div>
                </div>
                <div className="mt-3 max-h-48 space-y-2 overflow-y-auto">
                  {(queue?.queue || []).slice(0, 12).map((item) => (
                    <div key={item.invoice_id} className="rounded-lg border border-[#eadfcd] bg-white px-3 py-2 text-sm">
                      <div className="flex items-center justify-between">
                        <strong>{item.invoice_number}</strong>
                        <span className="text-xs uppercase">{item.priority}</span>
                      </div>
                      <p className="text-xs text-[#76624a]">Due {item.due_date || "N/A"} | Overdue {item.days_overdue}d | {item.amount_due.toLocaleString()}</p>
                    </div>
                  ))}
                </div>
              </article>
            </section>

            <section className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
              <h2 className="text-lg font-semibold text-[#2a2017]">Document Workflow Actions</h2>
              <p className="mt-1 text-sm text-[#6f6252]">Enter a document ID to classify or trigger approval/rejection/posting workflow actions.</p>
              <div className="mt-4 grid gap-3 lg:grid-cols-3">
                <input
                  value={documentId}
                  onChange={(e) => setDocumentId(e.target.value)}
                  className="rounded-xl border border-[#d6c8b4] bg-[#fffaf2] px-3 py-2 text-sm text-[#2a2017]"
                  placeholder="Document ID"
                />
                <input
                  value={workflowNote}
                  onChange={(e) => setWorkflowNote(e.target.value)}
                  className="rounded-xl border border-[#d6c8b4] bg-[#fffaf2] px-3 py-2 text-sm text-[#2a2017]"
                  placeholder="Workflow note (optional)"
                />
                <button
                  onClick={() => void runClassifyDocument()}
                  disabled={busy === "doc-classify"}
                  className="rounded-xl border border-[#ccb89a] bg-[#fff9ee] px-4 py-2.5 text-sm font-medium text-[#5f4828] hover:bg-[#f8ebd7] disabled:opacity-70"
                >
                  {busy === "doc-classify" ? "Classifying..." : "Classify document"}
                </button>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <button onClick={() => void runWorkflow("approve")} disabled={busy === "doc-approve"} className="rounded-lg border border-[#ceb89a] bg-[#f9f1e2] px-3 py-1.5 text-xs font-semibold text-[#513f27] hover:bg-[#f2e6d2] disabled:opacity-70">{busy === "doc-approve" ? "Working..." : "Approve"}</button>
                <button onClick={() => void runWorkflow("reject")} disabled={busy === "doc-reject"} className="rounded-lg border border-[#ceb89a] bg-[#f9f1e2] px-3 py-1.5 text-xs font-semibold text-[#513f27] hover:bg-[#f2e6d2] disabled:opacity-70">{busy === "doc-reject" ? "Working..." : "Reject"}</button>
                <button onClick={() => void runWorkflow("post_ledger")} disabled={busy === "doc-post_ledger"} className="rounded-lg border border-[#ceb89a] bg-[#f9f1e2] px-3 py-1.5 text-xs font-semibold text-[#513f27] hover:bg-[#f2e6d2] disabled:opacity-70">{busy === "doc-post_ledger" ? "Working..." : "Post to ledger"}</button>
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
