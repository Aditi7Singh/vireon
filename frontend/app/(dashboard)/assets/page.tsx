"use client";

import { useEffect, useMemo, useState } from "react";
import TopBar from "@/components/TopBar";
import api from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { formatCurrency } from "@/lib/utils";
import { Box, RefreshCw, Sparkles, Wrench, ArrowRight, Archive } from "lucide-react";

export default function AssetsPage() {
  const { openChat } = useAppStore();
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [assets, setAssets] = useState<any[]>([]);
  const [depreciation, setDepreciation] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const health = await api.getStartupHealth();
        const resolvedCompanyId = health.default_company_id || null;
        setCompanyId(resolvedCompanyId);
        if (!resolvedCompanyId) {
          setError("No default company is configured yet.");
          return;
        }
        const [assetRows, depRows] = await Promise.all([
          api.getAssets(resolvedCompanyId),
          api.getDepreciationExpense(resolvedCompanyId, new Date().toISOString().slice(0, 7)),
        ]);
        setAssets(assetRows || []);
        setDepreciation(depRows || null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load assets.");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const assetSummary = useMemo(() => ({
    count: assets.length,
    totalBookValue: assets.reduce((sum, asset) => sum + Number(asset.book_value || asset.purchase_cost || 0), 0),
  }), [assets]);

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Assets" />
      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Archive className="h-3.5 w-3.5" />
                Fixed asset lifecycle and depreciation
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">Asset management</h1>
              <p className="mt-2 text-sm text-[#5f5344]">Track book value, aging, and replacement recommendations.
              </p>
            </div>
            <button
              onClick={() => openChat("Review our fixed assets and recommend what to retire, replace, or keep.")}
              className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
            >
              <Sparkles className="h-4 w-4" />
              Ask Finley
            </button>
          </div>
        </section>

        {error && <div className="rounded-2xl border border-[#ebc1b8] bg-[#fff1ee] px-4 py-3 text-sm text-[#9f3f30]">{error}</div>}

        <section className="grid gap-4 md:grid-cols-3">
          {[
            { label: "Asset count", value: assetSummary.count, icon: Box },
            { label: "Total book value", value: formatCurrency(assetSummary.totalBookValue), icon: ArrowRight },
            { label: "Monthly depreciation", value: formatCurrency(depreciation?.monthly_depreciation || 0), icon: Wrench },
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
            <h2 className="text-lg font-semibold text-[#2a2017]">Lifecycle recommendations</h2>
            <div className="mt-4 space-y-2">
              {assets.slice(0, 10).map((asset) => {
                const ageYears = asset.age_years ?? 0;
                const usefulLifeYears = asset.useful_life_years ?? 0;
                const remaining = Math.max(0, usefulLifeYears - ageYears);
                return (
                  <div key={asset.id || asset.asset_name} className="rounded-xl border border-[#e8dcc9] bg-[#fff8ec] px-4 py-3 text-sm">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="font-medium text-[#2a2017]">{asset.asset_name}</p>
                        <p className="text-xs text-[#7b6d5b]">{asset.asset_category || "Uncategorized"} • {remaining.toFixed(1)} years remaining</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-[#9a461f]">{formatCurrency(asset.book_value || asset.purchase_cost || 0)}</p>
                        <p className="text-xs uppercase text-[#7b6d5b]">{asset.status || asset.recommendation || "hold"}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
              {assets.length === 0 && <p className="text-sm text-[#6f5f4b]">No asset records found.</p>}
            </div>
          </article>

          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
            <h2 className="text-lg font-semibold text-[#2a2017]">Depreciation snapshot</h2>
            <div className="mt-4 space-y-3 text-sm text-[#5f5344]">
              <p>Accumulated depreciation: <span className="font-semibold text-[#2a2017]">{formatCurrency(depreciation?.accumulated_depreciation || 0)}</span></p>
              <p>Asset count: <span className="font-semibold text-[#2a2017]">{depreciation?.asset_count || assets.length}</span></p>
              <p>The asset lifecycle tool uses useful life and current book value to recommend retire, replace, or hold actions.</p>
            </div>
          </article>
        </section>

        {loading && (
          <div className="flex items-center gap-2 rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-4 text-sm text-[#6f5f4b]">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Loading asset data...
          </div>
        )}
      </div>
    </div>
  );
}
