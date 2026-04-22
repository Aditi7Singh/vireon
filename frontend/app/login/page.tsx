"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import {
  Crown, Shield, Bot, TrendingUp, BarChart3, Zap, Lock,
  CheckCircle2, ArrowRight,
} from "lucide-react";

const DEMO_USERS = [
  {
    role: "CEO",
    icon: Crown,
    name: "Aditi Singh",
    login: "outlandishaditi11@gmail.com",
    password: "VireonCEO@2026",
    color: "#b45309",
    bg: "#fef3c7",
    border: "#fde68a",
    description: "Strategic overview, portfolio health, board-ready metrics",
    capabilities: ["Full dashboard access", "Investor portal", "Runway scenarios"],
    redirectTo: "/dashboard/ceo",
  },
  {
    role: "Admin",
    icon: Shield,
    name: "Vireon Admin",
    login: "admin@vireon.ai",
    password: "VireonAdmin@2026",
    color: "#1d4ed8",
    bg: "#dbeafe",
    border: "#bfdbfe",
    description: "Platform management, user access, audit trails",
    capabilities: ["User management", "All modules", "Audit logs"],
    redirectTo: "/dashboard",
  },
  {
    role: "CFO · Finley",
    icon: Bot,
    name: "Finley",
    login: "finley@vireon.ai",
    password: "FinleyCFO@2026",
    color: "#7c3aed",
    bg: "#ede9fe",
    border: "#ddd6fe",
    description: "AI CFO agent — full financial ops, compliance, forecasting",
    capabilities: ["AI agent tools", "Close workflow", "Tax provisioning"],
    redirectTo: "/dashboard/finance",
  },
];

const PLATFORM_STATS = [
  { icon: BarChart3,  value: "38+",    label: "Finance modules" },
  { icon: Zap,        value: "100+",   label: "AI agent tools" },
  { icon: TrendingUp, value: "3",      label: "Active projects" },
  { icon: CheckCircle2,value: "6+",   label: "Compliance regions" },
];

export default function LoginPage() {
  const router = useRouter();
  const [usernameOrEmail, setUsernameOrEmail] = useState(DEMO_USERS[0].login);
  const [password, setPassword] = useState(DEMO_USERS[0].password);
  const [selectedRole, setSelectedRole] = useState<string>(DEMO_USERS[0].role);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSelect = (user: typeof DEMO_USERS[0]) => {
    setUsernameOrEmail(user.login);
    setPassword(user.password);
    setSelectedRole(user.role);
    setError(null);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const token = await api.login(usernameOrEmail.trim(), password);
      localStorage.setItem("access_token", token.access_token);
      localStorage.setItem("auth_token", token.access_token);
      const selected = DEMO_USERS.find((u) => u.login === usernameOrEmail.trim());
      router.replace(selected?.redirectTo ?? "/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex bg-[#f6f3ee] text-[#1f1a15]">

      {/* ── Left: Branding Panel ── */}
      <div className="hidden lg:flex flex-col justify-between w-[46%] bg-[#1a1410] px-12 py-10 relative overflow-hidden">
        {/* Subtle ambient glow */}
        <div className="absolute top-0 left-0 w-80 h-80 bg-[#b45309]/20 rounded-full blur-[120px] -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-[#7c3aed]/15 rounded-full blur-[140px] translate-x-1/3 translate-y-1/3 pointer-events-none" />

        {/* Logo */}
        <div className="relative z-10">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-[#d97706] to-[#b45309] shadow-lg">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="text-lg font-black tracking-tight text-white">Vireon</p>
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#c8a95e]">Seeding Lab · AI Finance</p>
            </div>
          </div>
        </div>

        {/* Headline */}
        <div className="relative z-10 space-y-6">
          <div>
            <h1 className="text-4xl font-black leading-tight text-white">
              Your entire finance operation,
              <span className="text-[#f59e0b]"> powered by AI.</span>
            </h1>
            <p className="mt-4 text-sm leading-relaxed text-[#c8b89e]">
              Vireon unifies financial data, AI-driven insights, and autonomous workflows
              for your CFO, CEO, and finance team — in one platform built for high-growth startups.
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-3">
            {PLATFORM_STATS.map(({ icon: Icon, value, label }) => (
              <div key={label} className="rounded-2xl border border-[#2e2620] bg-[#221c18]/80 px-4 py-3">
                <div className="flex items-center gap-2 mb-1">
                  <Icon className="h-3.5 w-3.5 text-[#f59e0b]" />
                  <span className="text-xl font-black text-white">{value}</span>
                </div>
                <p className="text-[10px] text-[#9c8c7c] font-semibold uppercase tracking-wider">{label}</p>
              </div>
            ))}
          </div>

          {/* Feature highlights */}
          <div className="space-y-2">
            {[
              "Finley · Autonomous AI CFO with 100+ financial tools",
              "Sprout · Orchard · AI Lab project cost tracking",
              "India FY budget, GST, TDS & PF compliance",
              "Runway forecasting with Monte Carlo simulation",
            ].map((f) => (
              <div key={f} className="flex items-start gap-2.5">
                <CheckCircle2 className="h-3.5 w-3.5 mt-0.5 shrink-0 text-[#f59e0b]" />
                <p className="text-xs text-[#c8b89e]">{f}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom tag */}
        <p className="relative z-10 text-[10px] text-[#6b5948]">
          © 2026 Vireon Seeding Lab · Confidential demo environment
        </p>
      </div>

      {/* ── Right: Login Panel ── */}
      <div className="flex flex-1 flex-col justify-center px-6 py-10 sm:px-10 lg:px-16 bg-[#faf7f2]">
        <div className="mx-auto w-full max-w-md">

          {/* Mobile logo */}
          <div className="mb-8 flex items-center gap-2 lg:hidden">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-[#d97706] to-[#b45309]">
              <Zap className="h-4 w-4 text-white" />
            </div>
            <span className="text-base font-black text-[#1f1a15]">Vireon</span>
          </div>

          <h2 className="text-2xl font-black text-[#1f1a15]">Sign in to Vireon</h2>
          <p className="mt-1 text-sm text-[#7a6a57]">Choose a role to explore the platform</p>

          {/* Role cards */}
          <div className="mt-6 space-y-3">
            {DEMO_USERS.map((user) => {
              const Icon     = user.icon;
              const isActive = selectedRole === user.role;
              return (
                <button
                  key={user.role}
                  type="button"
                  onClick={() => handleSelect(user)}
                  className={`w-full rounded-2xl border-2 p-4 text-left transition-all duration-200 ${
                    isActive
                      ? "shadow-md scale-[1.01]"
                      : "border-[#e5d9c8] bg-white hover:border-[#d4c3ae] hover:bg-[#fdf9f4]"
                  }`}
                  style={isActive ? { borderColor: user.border, background: user.bg } : {}}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"
                      style={{ background: user.color + "20" }}>
                      <Icon className="h-4.5 w-4.5" style={{ color: user.color }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-black uppercase tracking-wider" style={{ color: user.color }}>{user.role}</span>
                        {isActive && (
                          <span className="rounded-full px-1.5 py-0.5 text-[9px] font-black uppercase tracking-wider text-white"
                            style={{ background: user.color }}>
                            Selected
                          </span>
                        )}
                      </div>
                      <p className="text-xs font-semibold text-[#1d1b17]">{user.name}</p>
                      <p className="mt-0.5 text-[11px] text-[#8b7a69]">{user.description}</p>
                      <div className="mt-1.5 flex flex-wrap gap-1.5">
                        {user.capabilities.map((cap) => (
                          <span key={cap} className="rounded-lg px-2 py-0.5 text-[9px] font-bold"
                            style={{ background: user.color + "15", color: user.color }}>
                            {cap}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <label className="block">
              <span className="text-[10px] font-black uppercase tracking-[0.15em] text-[#8b7a69]">Email or username</span>
              <input
                className="mt-1.5 w-full rounded-xl border border-[#d2bea0] bg-white px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[#b66b2f]/30 transition-all"
                value={usernameOrEmail}
                onChange={(e) => { setUsernameOrEmail(e.target.value); setSelectedRole(""); }}
                required
              />
            </label>

            <label className="block">
              <span className="text-[10px] font-black uppercase tracking-[0.15em] text-[#8b7a69]">Password</span>
              <div className="relative mt-1.5">
                <input
                  type="password"
                  className="w-full rounded-xl border border-[#d2bea0] bg-white px-3 py-2.5 pr-10 text-sm outline-none focus:ring-2 focus:ring-[#b66b2f]/30 transition-all"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <Lock className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#b08a5c]" />
              </div>
            </label>

            {error && (
              <div className="rounded-xl border border-[#fecaca] bg-[#fff1f2] px-3 py-2.5 text-sm text-[#9f1239]">
                {error}
              </div>
            )}

            <button
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#1f1a15] px-4 py-3 text-sm font-bold text-[#fff6ea] hover:bg-[#15110d] active:scale-[0.98] disabled:opacity-60 transition-all"
            >
              {loading ? (
                <span className="animate-pulse">Signing in…</span>
              ) : (
                <>
                  Sign in to Vireon
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-[10px] text-[#a0917f]">
            Presentation demo environment · Data is synthetic
          </p>
        </div>
      </div>
    </main>
  );
}
