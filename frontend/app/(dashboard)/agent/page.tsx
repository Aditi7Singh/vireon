"use client";

import { useEffect, useRef, useState } from "react";
import TopBar from "@/components/TopBar";
import api from "@/lib/api";
import { useAppStore } from "@/lib/store";
import {
  AlertCircle, Bot, CheckCircle2, MessageSquare, RefreshCw,
  Send, Sparkles, User, FileText, Receipt, BarChart3, Shield,
  TrendingUp, Users,
  Zap, ChevronDown, ChevronUp, Copy, ThumbsUp, ThumbsDown,
} from "lucide-react";
import { cn } from "@/lib/utils";

const QUICK_ACTIONS = [
  { category: "Analysis", icon: TrendingUp, color: "#059669", prompts: [
    "Show me our current runway and burn rate",
    "Analyze our cash position and flag risks",
    "What's our MRR growth trend this quarter?",
    "Compare our unit economics to SaaS benchmarks",
  ]},
  { category: "Invoices & AR", icon: FileText, color: "#2563eb", prompts: [
    "Which invoices are overdue and how much?",
    "Create an invoice for Acme Corp for $5,000 consulting",
    "What's our DSO this quarter versus last?",
    "Send payment reminders for all overdue invoices",
  ]},
  { category: "Bills & AP", icon: Receipt, color: "#d97706", prompts: [
    "List all bills pending my approval",
    "What AP is due in the next 7 days?",
    "Optimize our AP payment timing for cash flow",
    "Flag any duplicate invoices in AP",
  ]},
  { category: "Finance Reports", icon: BarChart3, color: "#7c3aed", prompts: [
    "Generate a P&L summary for Q1 2026",
    "How does our gross margin compare to budget?",
    "Show key balance sheet movements this month",
    "Prepare a board-ready cash flow summary",
  ]},
  { category: "Compliance", icon: Shield, color: "#dc2626", prompts: [
    "What tax deadlines are coming up this month?",
    "Check our SOC 2 compliance status",
    "When is our next quarterly estimated tax due?",
    "What corporate filings are due in Q2?",
  ]},
  { category: "Forecasting", icon: Sparkles, color: "#8d4f27", prompts: [
    "Forecast our 12-month runway under base case",
    "Model impact of hiring 5 engineers in June",
    "What happens to runway if we lose our top customer?",
    "Simulate raising a Series B at $200M valuation",
  ]},
  { category: "Seeding Lab", icon: Users, color: "#16a34a", prompts: [
    "Compare burn rate across Sprout, Orchard and AI Lab",
    "Which project has the highest revenue per employee?",
    "How does AI Lab GPU spend impact overall runway?",
    "Model adding 3 engineers to Orchard starting next month",
  ]},
];

const EXAMPLE_RESPONSES: Record<string, string> = {
  "Show me our current runway and burn rate": `**Runway Analysis — April 2026**

📊 **Current Position:**
• Cash & Equivalents: **$2.84M**
• Monthly Gross Burn: **$481K**
• Monthly Net Burn: **$372K** (after $109K revenue)
• **Runway: 7.6 months** at current burn rate

⚠️ **Risk Factors:**
• Cooley LLP bill of $22,500 is 15 days overdue — paying immediately reduces runway by 4 days
• AWS spend trending +12% QoQ — proactive optimization could save $1,800/month

✅ **Positive Signals:**
• MRR grew 21% last month ($89K → $108K), improving net burn monthly
• Series A capital deployed efficiently — burn multiple at 0.82x (excellent for growth stage)

**Recommendation:** At current MRR growth rate, you'll reach cash-flow positive in ~5.2 months. Maintain hiring plan but defer any non-critical opex above $10K until Q3.`,

  "Which invoices are overdue and how much?": `**Overdue Invoice Summary — April 20, 2026**

🔴 **1 Invoice Overdue:**

| Invoice | Customer | Amount | Days Past Due |
|---------|----------|--------|---------------|
| INV-2026-042 | Nexus Ventures | $7,200 | 15 days |

**Total Overdue AR: $7,200**

**Suggested Actions:**
1. Send automated payment reminder email (last sent 10 days ago)
2. Schedule a call with Nexus Ventures AP team — they've been slow payers historically (avg 42 DSO)
3. Consider adding a 1.5% monthly late fee clause to their next contract

**Upcoming Risk:** INV-2026-043 (Bloom Health · $4,800) is due in 20 days with no payment activity logged.

_Would you like me to draft a payment reminder email for Nexus Ventures?_`,
};

export default function AgentPage() {
  const { chatSessionId, setChatSessionId } = useAppStore();
  const [messages, setMessages] = useState<{ role: string; content: string; timestamp?: string }[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState<"ok" | "warning" | "unknown">("unknown");
  const [showActions, setShowActions] = useState(true);
  const [activeCategory, setActiveCategory] = useState("Analysis");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chatSessionId) setChatSessionId(`session_${Math.random().toString(36).substring(7)}`);
  }, [chatSessionId, setChatSessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const init = async () => {
      try {
        const health = await api.getStartupHealth();
        setHealthStatus(health.status || "unknown");
        const history = await api.getHistory(chatSessionId || "");
        if (history.messages?.length) {
          setMessages(history.messages.map((m: any) => ({ role: m.role, content: m.content, timestamp: new Date().toLocaleTimeString() })));
        } else {
          setMessages([{
            role: "assistant",
            content: "**Hello! I'm Finley, your Vireon AI finance agent.**\n\nI can help you with financial analysis, create invoices and bills, run scenario models, check compliance deadlines, and much more. I have access to your full financial data.\n\nWhat would you like to work on today?",
            timestamp: new Date().toLocaleTimeString(),
          }]);
        }
      } catch {
        setMessages([{ role: "assistant", content: "Ready to help — backend may be offline so I'll work with cached insights.", timestamp: new Date().toLocaleTimeString() }]);
      }
    };
    init();
  }, [chatSessionId]);

  const handleSend = async (seed?: string) => {
    const query = (seed || input).trim();
    if (!query || isLoading) return;

    const timestamp = new Date().toLocaleTimeString();
    setMessages(prev => [...prev, { role: "user", content: query, timestamp }]);
    setInput("");
    setIsLoading(true);

    try {
      let responseContent: string;
      if (EXAMPLE_RESPONSES[query]) {
        await new Promise(r => setTimeout(r, 1200));
        responseContent = EXAMPLE_RESPONSES[query];
      } else {
        const res = await api.chat(query, chatSessionId || undefined);
        responseContent = res.response;
      }
      setMessages(prev => [...prev, { role: "assistant", content: responseContent, timestamp: new Date().toLocaleTimeString() }]);
    } catch {
      setMessages(prev => [...prev, { role: "assistant", content: "I hit an error processing that. Please try again or check the backend connection.", timestamp: new Date().toLocaleTimeString() }]);
    } finally {
      setIsLoading(false);
    }
  };

  const activeGroup = QUICK_ACTIONS.find(g => g.category === activeCategory);

  function renderMessage(content: string) {
    const lines = content.split("\n");
    return (
      <div className="space-y-1">
        {lines.map((line, i) => {
          if (line.startsWith("**") && line.endsWith("**") && line.length > 4) {
            return <p key={i} className="font-bold text-[#2a2017]">{line.slice(2, -2)}</p>;
          }
          if (line.startsWith("• ") || line.startsWith("- ")) {
            const bold = line.slice(2).replace(/\*\*(.*?)\*\*/g, (_, m) => `<strong>${m}</strong>`);
            return <p key={i} className="pl-3 text-sm" dangerouslySetInnerHTML={{ __html: `• ${bold}` }} />;
          }
          if (/^\d+\./.test(line)) {
            const bold = line.replace(/\*\*(.*?)\*\*/g, (_, m) => `<strong>${m}</strong>`);
            return <p key={i} className="pl-3 text-sm" dangerouslySetInnerHTML={{ __html: bold }} />;
          }
          if (line.startsWith("⚠️") || line.startsWith("✅") || line.startsWith("📊") || line.startsWith("🔴") || line.startsWith("_")) {
            const italic = line.startsWith("_") ? `<em>${line.slice(1, -1)}</em>` : line;
            return <p key={i} className="text-sm" dangerouslySetInnerHTML={{ __html: italic.replace(/\*\*(.*?)\*\*/g, (_, m) => `<strong>${m}</strong>`) }} />;
          }
          if (line.includes("|") && line.trim().startsWith("|")) {
            return <p key={i} className="font-mono text-xs text-[#5f5344] bg-[#f0ebe3] rounded px-2 py-0.5">{line}</p>;
          }
          const bold = line.replace(/\*\*(.*?)\*\*/g, (_, m) => `<strong>${m}</strong>`);
          return line ? <p key={i} className="text-sm" dangerouslySetInnerHTML={{ __html: bold }} /> : <div key={i} className="h-1" />;
        })}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#ece3d4] pb-10 text-[#1d1b17]">
      <TopBar title="Finley AI Agent" />

      <div className="mx-auto max-w-7xl px-4 pt-6 sm:px-6 lg:px-8">
        <div className="grid gap-6 lg:grid-cols-[1fr_320px]">

          {/* Chat Panel */}
          <div className="rounded-2xl border border-[#cfbfa9] bg-[#f8efe3] shadow-[0_16px_36px_rgba(63,45,24,0.12)] overflow-hidden flex flex-col" style={{ height: "calc(100vh - 140px)" }}>

            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#deceb8] px-5 py-4 shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#2c2520] to-[#8d4f27] flex items-center justify-center shadow">
                  <Bot className="h-5 w-5 text-[#fff7ef]" />
                </div>
                <div>
                  <p className="text-sm font-bold text-[#2a2017]">Finley by Vireon</p>
                  <p className="text-xs text-[#8a7b68]">Powered by LangGraph · GPT-4o</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {healthStatus === "ok"
                  ? <span className="inline-flex items-center gap-1 rounded-full border border-[#b7d8bf] bg-[#edf8ef] px-2.5 py-1 text-[10px] font-semibold text-[#2f6a45]"><CheckCircle2 className="h-3 w-3" />Connected</span>
                  : <span className="inline-flex items-center gap-1 rounded-full border border-[#e1c4af] bg-[#fff2ee] px-2.5 py-1 text-[10px] font-semibold text-[#9f3f30]"><AlertCircle className="h-3 w-3" />Offline</span>
                }
                <button onClick={() => setMessages([{ role: "assistant", content: "Session cleared. How can I help?", timestamp: new Date().toLocaleTimeString() }])} className="rounded-lg border border-[#ddcfbc] px-2.5 py-1 text-xs font-medium text-[#776b5a] hover:bg-white/50">
                  Clear
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {messages.map((msg, idx) => (
                <div key={idx} className={cn("flex gap-3", msg.role === "user" ? "justify-end" : "justify-start")}>
                  {msg.role === "assistant" && (
                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#2c2520] to-[#8d4f27] flex items-center justify-center shrink-0 mt-0.5">
                      <Bot className="h-3.5 w-3.5 text-[#fff7ef]" />
                    </div>
                  )}
                  <div className={cn("max-w-[82%] rounded-2xl px-4 py-3", msg.role === "user" ? "bg-[#2d241b] text-[#fff8ee] rounded-tr-sm" : "border border-[#ddcfbc] bg-white/80 text-[#33291f] rounded-tl-sm shadow-sm")}>
                    {msg.role === "assistant" ? renderMessage(msg.content) : <p className="text-sm">{msg.content}</p>}
                    <p className="text-[10px] opacity-50 mt-1.5">{msg.timestamp}</p>
                    {msg.role === "assistant" && idx > 0 && (
                      <div className="flex items-center gap-2 mt-2 pt-2 border-t border-[#ede8e0]">
                        <button className="p-1 rounded hover:bg-[#f0ebe3] text-[#9a8872]"><ThumbsUp className="h-3 w-3" /></button>
                        <button className="p-1 rounded hover:bg-[#f0ebe3] text-[#9a8872]"><ThumbsDown className="h-3 w-3" /></button>
                        <button className="p-1 rounded hover:bg-[#f0ebe3] text-[#9a8872]"><Copy className="h-3 w-3" /></button>
                      </div>
                    )}
                  </div>
                  {msg.role === "user" && (
                    <div className="w-7 h-7 rounded-lg bg-[#2d241b] flex items-center justify-center shrink-0 mt-0.5">
                      <User className="h-3.5 w-3.5 text-[#fff7ef]" />
                    </div>
                  )}
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-3 justify-start">
                  <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#2c2520] to-[#8d4f27] flex items-center justify-center shrink-0">
                    <Bot className="h-3.5 w-3.5 text-[#fff7ef]" />
                  </div>
                  <div className="border border-[#ddcfbc] bg-white/80 rounded-2xl rounded-tl-sm px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      {[0, 150, 300].map(delay => (
                        <span key={delay} className="w-2 h-2 rounded-full bg-[#8d4f27] animate-bounce" style={{ animationDelay: `${delay}ms` }} />
                      ))}
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="border-t border-[#e5dbc9] p-4 bg-white/30 shrink-0">
              <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex items-end gap-2">
                <div className="relative flex-1">
                  <MessageSquare className="absolute left-3 top-3 h-4 w-4 text-[#8a7b68]" />
                  <textarea
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                    placeholder="Ask anything about your finances, or give a command like 'create an invoice'..."
                    rows={2}
                    className="w-full rounded-xl border border-[#ccb89d] bg-[#fff8ed] py-2.5 pl-10 pr-3 text-sm resize-none outline-none focus:ring-2 focus:ring-[#8d4f27]/20"
                  />
                </div>
                <button type="submit" disabled={isLoading || !input.trim()} className="h-10 w-10 rounded-xl bg-[#8f5632] text-[#fff8ee] disabled:opacity-50 hover:bg-[#764729] flex items-center justify-center shrink-0">
                  {isLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                </button>
              </form>
              <p className="text-[10px] text-[#9a8872] mt-2 text-center">Shift+Enter for new line · Enter to send</p>
            </div>
          </div>

          {/* Quick Actions Sidebar */}
          <div className="space-y-4">
            <div className="rounded-2xl border border-[#cfbfa9] bg-[#f8efe3] overflow-hidden">
              <button onClick={() => setShowActions(!showActions)} className="w-full flex items-center justify-between px-4 py-3 border-b border-[#deceb8]">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-[#8d4f27]" />
                  <span className="text-sm font-bold text-[#2a2017]">Quick Actions</span>
                </div>
                {showActions ? <ChevronUp className="h-4 w-4 text-[#776b5a]" /> : <ChevronDown className="h-4 w-4 text-[#776b5a]" />}
              </button>

              {showActions && (
                <div>
                  <div className="flex gap-1 flex-wrap p-3 border-b border-[#deceb8]">
                    {QUICK_ACTIONS.map(g => {
                      const Icon = g.icon;
                      return (
                        <button key={g.category} onClick={() => setActiveCategory(g.category)} className={cn("rounded-lg px-2.5 py-1.5 text-xs font-semibold flex items-center gap-1 transition-all", activeCategory === g.category ? "bg-[#231c15] text-white" : "bg-white/60 text-[#776b5a] hover:bg-white")}>
                          <Icon className="h-3 w-3" />{g.category}
                        </button>
                      );
                    })}
                  </div>
                  <div className="p-3 space-y-1.5">
                    {activeGroup?.prompts.map(prompt => (
                      <button key={prompt} onClick={() => handleSend(prompt)} className="w-full text-left rounded-xl border border-[#e5dbc9] bg-white/60 px-3 py-2.5 text-xs text-[#4a3f35] hover:bg-white hover:border-[#c8b49a] transition-all leading-relaxed">
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Agent Capabilities — full showcase */}
            <div className="rounded-2xl border border-[#cfbfa9] bg-[#f8efe3] p-4">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-black uppercase tracking-widest text-[#776b5a]">Finley's Capabilities</p>
                <span className="rounded-full bg-[#2c2520] px-2 py-0.5 text-[9px] font-black text-[#f6d9b0]">100+ tools</span>
              </div>
              <div className="space-y-3">
                {[
                  {
                    group: "Transactions",
                    color: "#2563eb",
                    items: ["Create & send invoices", "Enter & approve bills", "Expense categorisation", "Procurement & POs"],
                  },
                  {
                    group: "Intelligence",
                    color: "#7c3aed",
                    items: ["GL anomaly detection (ML)", "Vendor risk scoring", "Duplicate invoice detection", "Cash Flow at Risk (Monte Carlo)"],
                  },
                  {
                    group: "Planning",
                    color: "#059669",
                    items: ["12-month runway forecast", "Scenario modelling", "Hire impact simulation", "FY budget vs actual"],
                  },
                  {
                    group: "Compliance",
                    color: "#dc2626",
                    items: ["India tax calendar (TDS, PF, GST)", "Advance tax calculation", "Month-end close checklist", "SOC 2 audit trail"],
                  },
                  {
                    group: "Portfolio",
                    color: "#16a34a",
                    items: ["Sprout / Orchard / AI Lab burn", "Per-project headcount cost", "Cross-project runway impact", "ARR attainment tracking"],
                  },
                ].map(({ group, color, items }) => (
                  <div key={group}>
                    <p className="text-[9px] font-black uppercase tracking-widest mb-1.5" style={{ color }}>{group}</p>
                    <div className="grid grid-cols-2 gap-1">
                      {items.map((item) => (
                        <div key={item} className="flex items-center gap-1.5 rounded-lg px-2 py-1" style={{ background: color + "10" }}>
                          <div className="w-1 h-1 rounded-full shrink-0" style={{ background: color }} />
                          <p className="text-[9px] font-semibold text-[#3d3429] leading-tight">{item}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-3 rounded-xl bg-[#1f1a16]/90 px-3 py-2 text-center">
                <p className="text-[9px] font-black text-amber-400 uppercase tracking-wider">Powered by</p>
                <p className="text-[10px] font-bold text-white">LangGraph · GPT-4o · Deterministic Math Engine</p>
                <p className="text-[9px] text-[#c8b89e]">Zero-hallucination financial arithmetic</p>
              </div>
            </div>

            {/* Session Info */}
            <div className="rounded-2xl border border-[#cfbfa9] bg-[#f8efe3] p-4">
              <p className="text-xs font-black uppercase tracking-widest text-[#776b5a] mb-3">Session</p>
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-[#9a8872]">Messages</span>
                  <span className="font-semibold text-[#4a3f35]">{messages.length}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-[#9a8872]">Session ID</span>
                  <span className="font-mono text-[10px] text-[#6b5344]">{chatSessionId?.slice(-8) || "—"}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-[#9a8872]">Model</span>
                  <span className="font-semibold text-[#4a3f35]">GPT-4o</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-[#9a8872]">Framework</span>
                  <span className="font-semibold text-[#4a3f35]">LangGraph</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
