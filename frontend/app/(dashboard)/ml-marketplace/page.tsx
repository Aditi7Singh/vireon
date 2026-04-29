"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import {
  Brain, Zap, TrendingUp, Shield, Search, ChevronRight,
  CheckCircle2, Clock, BarChart3, AlertTriangle, RefreshCw,
  Package, Star, Cpu, Play, Trash2, Activity,
} from "lucide-react";

type Category = "all" | "forecasting" | "anomaly_detection" | "risk" | "tax";
type Complexity = "low" | "medium" | "high";

interface CatalogModel {
  id: string;
  name: string;
  category: string;
  description: string;
  accuracy_benchmark: number;
  training_time_minutes: number;
  framework: string;
  version: string;
  tags: string[];
  complexity: Complexity;
  output: string;
}

const CATALOG: CatalogModel[] = [
  { id: "rev-forecast-sarima", name: "Revenue Forecasting (SARIMA)", category: "forecasting", description: "Seasonal ARIMA model trained on monthly revenue patterns with 12-month lookahead.", accuracy_benchmark: 91.2, training_time_minutes: 4, framework: "statsmodels", version: "2.1.0", tags: ["forecasting", "revenue", "saas"], complexity: "medium", output: "30/60/90-day revenue forecast" },
  { id: "burn-forecast-prophet", name: "Cash Burn Forecasting (Prophet)", category: "forecasting", description: "Facebook Prophet model for cash burn and runway prediction. Handles holidays and funding events.", accuracy_benchmark: 88.7, training_time_minutes: 6, framework: "prophet", version: "1.4.0", tags: ["forecasting", "burn", "runway"], complexity: "low", output: "Runway months + burn rate trend" },
  { id: "anomaly-isolation-forest", name: "GL Anomaly Detector (Isolation Forest)", category: "anomaly_detection", description: "Unsupervised ML detecting unusual transactions, split invoices, and duplicate payments.", accuracy_benchmark: 93.5, training_time_minutes: 2, framework: "scikit-learn", version: "3.0.1", tags: ["anomaly", "fraud", "gl"], complexity: "low", output: "Anomaly score + severity" },
  { id: "churn-risk-xgboost", name: "Customer Churn Risk (XGBoost)", category: "risk", description: "Gradient-boosted trees predicting customer churn probability using payment and usage signals.", accuracy_benchmark: 87.3, training_time_minutes: 8, framework: "xgboost", version: "1.2.0", tags: ["churn", "customers", "risk"], complexity: "medium", output: "Churn probability + risk tier" },
  { id: "vendor-risk-classifier", name: "Vendor Risk Classifier", category: "risk", description: "Classifies vendors into LOW/MEDIUM/HIGH risk based on payment patterns and concentration.", accuracy_benchmark: 85.9, training_time_minutes: 5, framework: "scikit-learn", version: "1.1.0", tags: ["vendor", "risk", "procurement"], complexity: "medium", output: "Risk tier + factors" },
  { id: "dso-lstm", name: "DSO Prediction (LSTM)", category: "forecasting", description: "Long Short-Term Memory network predicting Days Sales Outstanding and payment probability.", accuracy_benchmark: 89.1, training_time_minutes: 15, framework: "tensorflow", version: "1.0.0", tags: ["dso", "collections", "ar"], complexity: "high", output: "Expected DSO + payment probability" },
  { id: "tax-optimization-nlp", name: "Tax Deduction Classifier (NLP)", category: "tax", description: "NLP classifier that auto-categorizes expenses for maximum tax deduction eligibility.", accuracy_benchmark: 90.4, training_time_minutes: 10, framework: "transformers", version: "2.0.0", tags: ["tax", "optimization", "nlp"], complexity: "high", output: "Deduction category + savings estimate" },
  { id: "cash-flow-ensemble", name: "Cash Flow Ensemble", category: "forecasting", description: "Ensemble model averaging SARIMA and Prophet for robust 90-day cash flow prediction.", accuracy_benchmark: 94.1, training_time_minutes: 12, framework: "ensemble", version: "3.2.0", tags: ["cash-flow", "ensemble"], complexity: "high", output: "90-day forecast + confidence bands" },
];

const categoryIcons: Record<string, React.ElementType> = {
  forecasting: TrendingUp,
  anomaly_detection: AlertTriangle,
  risk: Shield,
  tax: BarChart3,
};

const complexityColor: Record<Complexity, string> = {
  low: "text-emerald-700 bg-emerald-50 border-emerald-200",
  medium: "text-amber-700 bg-amber-50 border-amber-200",
  high: "text-rose-700 bg-rose-50 border-rose-200",
};

const frameworkColor: Record<string, string> = {
  "scikit-learn": "bg-blue-100 text-blue-700",
  "statsmodels": "bg-purple-100 text-purple-700",
  "prophet": "bg-indigo-100 text-indigo-700",
  "xgboost": "bg-orange-100 text-orange-700",
  "tensorflow": "bg-red-100 text-red-700",
  "transformers": "bg-pink-100 text-pink-700",
  "ensemble": "bg-teal-100 text-teal-700",
};

export default function MLMarketplacePage() {
  const { openChat } = useAppStore();
  const [category, setCategory] = useState<Category>("all");
  const [search, setSearch] = useState("");
  const [deployed, setDeployed] = useState<Set<string>>(
    new Set(["rev-forecast-sarima", "anomaly-isolation-forest"])
  );
  const [retraining, setRetraining] = useState<Set<string>>(new Set());
  const [selected, setSelected] = useState<CatalogModel | null>(null);

  const filtered = CATALOG.filter(m => {
    const matchCat = category === "all" || m.category === category;
    const matchSearch = !search || m.name.toLowerCase().includes(search.toLowerCase()) || m.tags.some(t => t.includes(search.toLowerCase()));
    return matchCat && matchSearch;
  });

  const handleDeploy = (id: string) => {
    setDeployed(prev => new Set([...prev, id]));
  };

  const handleRetire = (id: string) => {
    setDeployed(prev => { const n = new Set(prev); n.delete(id); return n; });
  };

  const handleRetrain = (id: string) => {
    setRetraining(prev => new Set([...prev, id]));
    setTimeout(() => setRetraining(prev => { const n = new Set(prev); n.delete(id); return n; }), 3000);
  };

  const deployedModels = CATALOG.filter(m => deployed.has(m.id));

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="ML Model Marketplace" />
      <div className="max-w-7xl mx-auto px-6 pt-6 space-y-6">

        {/* Header Stats */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: "Models Available", value: CATALOG.length, icon: Package, color: "text-violet-600" },
            { label: "Deployed", value: deployed.size, icon: CheckCircle2, color: "text-emerald-600" },
            { label: "Avg Accuracy", value: `${(CATALOG.reduce((s, m) => s + m.accuracy_benchmark, 0) / CATALOG.length).toFixed(1)}%`, icon: Star, color: "text-amber-600" },
            { label: "Frameworks", value: new Set(CATALOG.map(m => m.framework)).size, icon: Cpu, color: "text-blue-600" },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="bg-white border border-[#e8ddd4] rounded-2xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-[#8a7e74] uppercase tracking-wide">{label}</span>
                <Icon className={cn("w-4 h-4", color)} />
              </div>
              <div className="text-2xl font-black text-[#1d1b17]">{value}</div>
            </div>
          ))}
        </div>

        {/* Deployed Models Banner */}
        {deployedModels.length > 0 && (
          <div className="bg-white border border-[#e8ddd4] rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Activity className="w-4 h-4 text-emerald-600" />
              <h3 className="font-bold text-sm text-[#1d1b17]">Active Deployments</h3>
            </div>
            <div className="flex flex-wrap gap-3">
              {deployedModels.map(m => (
                <div key={m.id} className="flex items-center gap-2.5 bg-emerald-50 border border-emerald-200 rounded-xl px-3 py-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-xs font-semibold text-emerald-700">{m.name}</span>
                  <span className="text-[10px] text-emerald-500">{m.accuracy_benchmark}% acc</span>
                  <button
                    onClick={() => handleRetrain(m.id)}
                    className="p-0.5 rounded hover:bg-emerald-100"
                    title="Retrain"
                  >
                    <RefreshCw className={cn("w-3 h-3 text-emerald-600", retraining.has(m.id) && "animate-spin")} />
                  </button>
                  <button onClick={() => handleRetire(m.id)} className="p-0.5 rounded hover:bg-red-50">
                    <Trash2 className="w-3 h-3 text-red-400" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative flex-1 min-w-[200px] max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#b0a499]" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search models or tags..."
              className="w-full pl-9 pr-3 py-2 bg-white border border-[#e8ddd4] rounded-xl text-sm focus:outline-none focus:border-[#b3622d]"
            />
          </div>
          {(["all", "forecasting", "anomaly_detection", "risk", "tax"] as Category[]).map(cat => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={cn(
                "px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all",
                category === cat
                  ? "bg-[#b3622d] text-white border-[#b3622d]"
                  : "bg-white text-[#6a6054] border-[#e8ddd4] hover:border-[#b3622d]"
              )}
            >
              {cat === "all" ? "All Models" : cat.replace("_", " ").replace(/\b\w/g, c => c.toUpperCase())}
            </button>
          ))}
        </div>

        {/* Model Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(model => {
            const CategoryIcon = categoryIcons[model.category] || Brain;
            const isDeployed = deployed.has(model.id);
            return (
              <div
                key={model.id}
                className={cn(
                  "bg-white border rounded-2xl p-5 hover:shadow-md transition-all cursor-pointer",
                  isDeployed ? "border-emerald-300 ring-1 ring-emerald-200" : "border-[#e8ddd4]"
                )}
                onClick={() => setSelected(model)}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-xl bg-[#f6f3ee] flex items-center justify-center">
                      <CategoryIcon className="w-4 h-4 text-[#b3622d]" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-[#1d1b17] leading-tight">{model.name}</div>
                      <div className="text-[10px] text-[#8a7e74]">v{model.version}</div>
                    </div>
                  </div>
                  {isDeployed && (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-600 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                      Live
                    </span>
                  )}
                </div>

                <p className="text-xs text-[#6a6054] mb-3 line-clamp-2">{model.description}</p>

                <div className="flex items-center gap-2 mb-3 flex-wrap">
                  <span className={cn("text-[10px] font-semibold border rounded-full px-2 py-0.5", complexityColor[model.complexity])}>
                    {model.complexity}
                  </span>
                  <span className={cn("text-[10px] font-semibold rounded-full px-2 py-0.5", frameworkColor[model.framework] || "bg-gray-100 text-gray-600")}>
                    {model.framework}
                  </span>
                  {model.tags.slice(0, 2).map(t => (
                    <span key={t} className="text-[10px] bg-[#f6f3ee] text-[#6a6054] rounded-full px-2 py-0.5">{t}</span>
                  ))}
                </div>

                <div className="flex items-center justify-between border-t border-[#f0e8e0] pt-3">
                  <div className="flex items-center gap-3">
                    <div className="text-center">
                      <div className="text-sm font-black text-emerald-600">{model.accuracy_benchmark}%</div>
                      <div className="text-[9px] text-[#8a7e74] uppercase">Accuracy</div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm font-black text-blue-600">{model.training_time_minutes}m</div>
                      <div className="text-[9px] text-[#8a7e74] uppercase">Train Time</div>
                    </div>
                  </div>
                  {isDeployed ? (
                    <button
                      onClick={e => { e.stopPropagation(); handleRetire(model.id); }}
                      className="text-[11px] font-semibold text-red-500 hover:bg-red-50 border border-red-200 px-3 py-1.5 rounded-xl transition-all"
                    >
                      Retire
                    </button>
                  ) : (
                    <button
                      onClick={e => { e.stopPropagation(); handleDeploy(model.id); }}
                      className="flex items-center gap-1 text-[11px] font-semibold text-white bg-[#b3622d] hover:bg-[#9d4f22] px-3 py-1.5 rounded-xl transition-all"
                    >
                      <Play className="w-3 h-3" /> Deploy
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Model Detail Modal */}
        {selected && (
          <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-6" onClick={() => setSelected(null)}>
            <div className="bg-white rounded-2xl p-6 max-w-lg w-full shadow-2xl" onClick={e => e.stopPropagation()}>
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="font-black text-lg text-[#1d1b17]">{selected.name}</h2>
                  <p className="text-xs text-[#8a7e74]">v{selected.version} · {selected.framework}</p>
                </div>
                <button onClick={() => setSelected(null)} className="text-[#8a7e74] hover:text-[#1d1b17] text-xl font-bold">×</button>
              </div>
              <p className="text-sm text-[#6a6054] mb-4">{selected.description}</p>
              <div className="bg-[#f6f3ee] rounded-xl p-4 mb-4">
                <div className="text-xs font-bold text-[#1d1b17] mb-1">Output</div>
                <div className="text-sm text-[#6a6054]">{selected.output}</div>
              </div>
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="text-center bg-emerald-50 rounded-xl p-3">
                  <div className="text-lg font-black text-emerald-600">{selected.accuracy_benchmark}%</div>
                  <div className="text-[10px] text-emerald-700">Benchmark Accuracy</div>
                </div>
                <div className="text-center bg-blue-50 rounded-xl p-3">
                  <div className="text-lg font-black text-blue-600">{selected.training_time_minutes}m</div>
                  <div className="text-[10px] text-blue-700">Training Time</div>
                </div>
                <div className="text-center bg-[#f6f3ee] rounded-xl p-3">
                  <div className={cn("text-lg font-black capitalize", complexityColor[selected.complexity].split(" ")[0])}>{selected.complexity}</div>
                  <div className="text-[10px] text-[#8a7e74]">Complexity</div>
                </div>
              </div>
              <div className="flex gap-3">
                {deployed.has(selected.id) ? (
                  <>
                    <button
                      onClick={() => handleRetrain(selected.id)}
                      className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold transition-all"
                    >
                      <RefreshCw className={cn("w-4 h-4", retraining.has(selected.id) && "animate-spin")} />
                      Retrain
                    </button>
                    <button
                      onClick={() => { handleRetire(selected.id); setSelected(null); }}
                      className="flex-1 py-2.5 border border-red-300 text-red-500 hover:bg-red-50 rounded-xl text-sm font-semibold transition-all"
                    >
                      Retire Model
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => { handleDeploy(selected.id); setSelected(null); }}
                    className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-[#b3622d] hover:bg-[#9d4f22] text-white rounded-xl text-sm font-semibold transition-all"
                  >
                    <Play className="w-4 h-4" /> Deploy Model
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
