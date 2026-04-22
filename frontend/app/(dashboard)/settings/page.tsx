"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import api from "@/lib/api";
import { AlertCircle, Building2, CheckCircle2, RefreshCw, Save, Shield, Users } from "lucide-react";

type Policy = {
  merge: string;
  plaid: string;
  cloud_costs: string;
};

const POLICY_OPTIONS = ["source_of_truth", "latest_timestamp_wins", "manual_review"];

const team = [
  { name: "Finley", role: "CFO", email: "finley@vireon.ai" },
  { name: "Aditi Singh", role: "Founder", email: "aditi@vireon.ai" },
  { name: "yagnasri", role: "Finance Ops", email: "yagnasri@vireon.ai" },
];

export default function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [policy, setPolicy] = useState<Policy>({
    merge: "source_of_truth",
    plaid: "source_of_truth",
    cloud_costs: "latest_timestamp_wins",
  });
  const [health, setHealth] = useState<any>(null);

  const loadSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const [startup, policyResult] = await Promise.all([
        api.getStartupHealth(),
        api.getConnectorConflictPolicy(),
      ]);
      setHealth(startup);
      const p = policyResult.policy || {};
      setPolicy({
        merge: p.merge || "source_of_truth",
        plaid: p.plaid || "source_of_truth",
        cloud_costs: p.cloud_costs || "latest_timestamp_wins",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadSettings();
  }, []);

  const savePolicy = async () => {
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const result = await api.updateConnectorConflictPolicy(policy);
      if (!result.success) {
        setError(result.message || "Failed to update connector policy");
        return;
      }
      setMessage("Connector conflict policy updated successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save policy");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Settings" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d3c2a8] bg-[#fff5e6] px-3 py-1 text-xs font-semibold text-[#7b5727]">
                <Shield className="h-3.5 w-3.5" />
                System configuration
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">Platform Settings</h1>
              <p className="mt-2 text-sm text-[#5f5344]">Operational controls, readiness checks, and connector conflict policy.</p>
            </div>
            <button
              onClick={() => void loadSettings()}
              className="inline-flex items-center gap-2 rounded-xl border border-[#ccb89a] bg-[#fff9ee] px-4 py-2.5 text-sm font-medium text-[#5f4828] hover:bg-[#f8ebd7]"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        </section>

        {error && (
          <section className="rounded-xl border border-[#ebc1b8] bg-[#fff2ef] p-3 text-sm text-[#9f3f30]">{error}</section>
        )}
        {message && (
          <section className="rounded-xl border border-[#b8ddbf] bg-[#edf8ef] p-3 text-sm text-[#2f6a45]">{message}</section>
        )}

        <section className="grid gap-6 lg:grid-cols-3">
          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-[#2a2017]"><Building2 className="h-4 w-4" />Startup Readiness</h2>
            {loading ? (
              <p className="mt-3 text-sm text-[#6f6252]">Loading...</p>
            ) : (
              <div className="mt-3 space-y-2 text-sm text-[#5f5243]">
                <p>Status: <strong>{health?.status || "unknown"}</strong></p>
                <p>Companies: <strong>{health?.checks?.companies ?? 0}</strong></p>
                <p>Ledger rows: <strong>{health?.checks?.ledger_entries ?? 0}</strong></p>
                <p>Missing keys: <strong>{health?.credential_readiness?.missing_keys?.length ?? 0}</strong></p>
              </div>
            )}
          </article>

          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 lg:col-span-2">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-[#2a2017]"><Save className="h-4 w-4" />Connector Conflict Policy</h2>
            <p className="mt-1 text-sm text-[#6f6252]">Control source precedence when Merge, Plaid, or cloud providers send overlapping data.</p>
            <div className="mt-4 grid gap-4 sm:grid-cols-3">
              {(["merge", "plaid", "cloud_costs"] as const).map((key) => (
                <label key={key} className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-[#76624a]">{key.replace("_", " ")}</span>
                  <select
                    value={policy[key]}
                    onChange={(e) => setPolicy((prev) => ({ ...prev, [key]: e.target.value }))}
                    className="w-full rounded-xl border border-[#d6c8b4] bg-[#fffaf2] px-3 py-2 text-sm text-[#2a2017]"
                  >
                    {POLICY_OPTIONS.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
            <button
              onClick={savePolicy}
              disabled={saving}
              className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d] disabled:opacity-60"
            >
              {saving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              {saving ? "Saving" : "Save policy"}
            </button>
          </article>
        </section>

        <section className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-[#2a2017]"><Users className="h-4 w-4" />Team Access</h2>
          <div className="mt-4 space-y-3">
            {team.map((member) => (
              <div key={member.email} className="flex items-center justify-between rounded-xl border border-[#e5dacb] bg-[#fff9ef] px-4 py-3">
                <div>
                  <p className="font-semibold text-[#2f241a]">{member.name}</p>
                  <p className="text-xs text-[#76624a]">{member.email}</p>
                </div>
                <span className="rounded-full border border-[#cdb48d] bg-[#f5e8d1] px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-[#6f4d21]">
                  {member.role}
                </span>
              </div>
            ))}
          </div>
          <p className="mt-3 inline-flex items-center gap-1 text-xs text-[#5f5344]"><CheckCircle2 className="h-3.5 w-3.5 text-[#2f6a45]" />Finley is configured as CFO.</p>
        </section>

        {health?.issues?.length > 0 && (
          <section className="rounded-2xl border border-[#ebd0bc] bg-[#fff7ee] p-5">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-[#7b5727]"><AlertCircle className="h-4 w-4" />Open startup issues</h3>
            <ul className="mt-3 space-y-1 text-sm text-[#6f5432]">
              {health.issues.map((issue: string, index: number) => (
                <li key={`${issue}-${index}`}>- {issue}</li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </div>
  );
}
