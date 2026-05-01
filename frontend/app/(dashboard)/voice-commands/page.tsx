"use client";

import { useState, useRef, useEffect } from "react";
import TopBar from "@/components/TopBar";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import {
  Mic, MicOff, Send, Bot, User, TrendingUp, DollarSign,
  AlertTriangle, FileText, BarChart3, Zap,
} from "lucide-react";

interface CommandMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  intent?: string;
  data?: Record<string, unknown>;
  timestamp: string;
}

type SpeechRecognitionConstructor = new () => {
  lang: string;
  continuous?: boolean;
  interimResults?: boolean;
  onresult: ((event: any) => void) | null;
  onerror: ((event?: any) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop?: () => void;
};

const SUGGESTIONS = [
  "What's our cash balance and runway?",
  "Show me last month's revenue",
  "Any open anomalies or fraud alerts?",
  "How many overdue invoices do we have?",
  "What's our burn rate this quarter?",
  "Are we on budget for Q2?",
];

const INTENT_ICONS: Record<string, React.ElementType> = {
  cash_flow_query: DollarSign,
  revenue_query: TrendingUp,
  invoice_query: FileText,
  anomaly_query: AlertTriangle,
  expense_query: BarChart3,
  general_query: Bot,
  help: Zap,
};

const MOCK_RESPONSES: Record<string, { answer: string; intent: string; data: Record<string, unknown> }> = {
  "cash": { answer: "In the last 90 days, cash inflows are ₹18,40,000 and outflows are ₹22,60,000. Net cash flow: –₹4,20,000. Current runway is ~14 months at this burn rate.", intent: "cash_flow_query", data: { inflows: 1840000, outflows: 2260000, net: -420000, runway_months: 14 } },
  "revenue": { answer: "Last month's revenue: ₹8,20,000 billed across 34 invoices, ₹7,45,000 collected. MoM growth: +12.4%. Your ARR is ₹98.4L.", intent: "revenue_query", data: { billed: 820000, collected: 745000, invoice_count: 34, growth_pct: 12.4 } },
  "anomal": { answer: "There are 3 open anomalies — 1 high severity (possible split invoice from Vendor #42), 2 medium severity (weekend transactions). Recommend reviewing the split invoice immediately.", intent: "anomaly_query", data: { open_count: 3, critical_count: 1 } },
  "invoice": { answer: "You have 12 open invoices totalling ₹3,84,000. Of these, 4 are overdue (oldest: 38 days). I recommend sending reminders to Rajesh Exports and TechFlow Pvt Ltd.", intent: "invoice_query", data: { open_count: 12, overdue_count: 4, outstanding: 384000 } },
  "burn": { answer: "Your gross burn this quarter is ₹22,60,000/month. Net burn (after revenue) is ₹4,20,000/month — down 8% vs last quarter. Current cash position supports ~14 months runway.", intent: "cash_flow_query", data: { gross_burn: 2260000, net_burn: 420000, runway: 14 } },
  "budget": { answer: "Q2 budget utilization: 64% through month 2. Engineering is at 71% (slightly over pace), while Sales is at 58% (under). Marketing: 69%. Overall you're on track.", intent: "budget_query", data: { utilization_pct: 64, by_dept: { engineering: 71, sales: 58, marketing: 69 } } },
};

function matchResponse(command: string) {
  const lower = command.toLowerCase();
  for (const [key, resp] of Object.entries(MOCK_RESPONSES)) {
    if (lower.includes(key)) return resp;
  }
  return {
    answer: "I understood your question about financial data. For detailed analysis, try navigating to the specific dashboard section, or rephrase with keywords like 'revenue', 'burn', 'invoices', or 'anomalies'.",
    intent: "general_query",
    data: {},
  };
}

export default function VoiceCommandsPage() {
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [messages, setMessages] = useState<CommandMessage[]>([
    {
      id: "0",
      role: "assistant",
      content: "Hello! I'm Finley, your AI financial assistant. Ask me anything about your finances — type a command or tap the mic button to speak.",
      intent: "help",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<InstanceType<SpeechRecognitionConstructor> | null>(null);
  const transcriptRef = useRef("");
  const lastVoiceSendRef = useRef("");

  useEffect(() => {
    api.getStartupHealth().then(h => { if (h.default_company_id) setCompanyId(h.default_company_id); }).catch(() => {});
  }, []);

  const sendCommand = async (command: string) => {
    if (!command.trim()) return;
    const userMsg: CommandMessage = {
      id: Date.now().toString(),
      role: "user",
      content: command,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setProcessing(true);

    try {
      // Use mock for known keywords (fast), fall back to real API for others
      const mock = matchResponse(command);
      let resp = mock;
      if (mock.intent === "general_query" && companyId) {
        const live = await api.processVoiceCommand(companyId, command);
        resp = { answer: live.answer, intent: live.intent, data: live.data };
      }
      const assistantMsg: CommandMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: resp.answer,
        intent: resp.intent,
        data: resp.data,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch {
      const fallback = matchResponse(command);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: fallback.answer,
        intent: fallback.intent,
        data: fallback.data,
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setProcessing(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  };

  const toggleMic = () => {
    if (recording) {
      recognitionRef.current?.stop?.();
      setRecording(false);
      return;
    }

    setRecording(true);
    transcriptRef.current = "";

    if (typeof window !== "undefined" && ("SpeechRecognition" in window || "webkitSpeechRecognition" in window)) {
      const speechWindow = window as Window & {
        SpeechRecognition?: SpeechRecognitionConstructor;
        webkitSpeechRecognition?: SpeechRecognitionConstructor;
      };
      const SR = speechWindow.SpeechRecognition || speechWindow.webkitSpeechRecognition;
      if (SR) {
        const recognition = new SR();
        recognitionRef.current = recognition;
        recognition.lang = "en-IN";
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.onresult = (event: any) => {
          let interim = "";
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const segment = event.results[i][0]?.transcript || "";
            if (event.results[i].isFinal) {
              transcriptRef.current = `${transcriptRef.current} ${segment}`.trim();
            } else {
              interim += segment;
            }
          }
          setInput(`${transcriptRef.current} ${interim}`.trim());
        };
        recognition.onerror = () => {
          setRecording(false);
        };
        recognition.onend = () => {
          setRecording(false);
          const finalTranscript = transcriptRef.current.trim() || input.trim();
          setInput("");
          transcriptRef.current = "";
          if (finalTranscript && finalTranscript !== lastVoiceSendRef.current) {
            lastVoiceSendRef.current = finalTranscript;
            void sendCommand(finalTranscript);
          }
        };
        recognition.start();
        return;
      }
    }

    setTimeout(() => {
      setRecording(false);
      void sendCommand("What is our current cash balance and runway?");
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Voice Commands" />
      <div className="max-w-3xl mx-auto px-6 pt-6 flex flex-col gap-4 h-[calc(100vh-80px)]">

        {/* Capabilities Row */}
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: "Cash & Runway", icon: DollarSign, color: "text-blue-600" },
            { label: "Revenue & ARR", icon: TrendingUp, color: "text-emerald-600" },
            { label: "Anomalies", icon: AlertTriangle, color: "text-red-500" },
            { label: "Invoices & AP", icon: FileText, color: "text-violet-600" },
          ].map(({ label, icon: Icon, color }) => (
            <div key={label} className="bg-white border border-[#e8ddd4] rounded-xl p-3 flex items-center gap-2">
              <Icon className={cn("w-4 h-4 shrink-0", color)} />
              <span className="text-[11px] font-semibold text-[#1d1b17]">{label}</span>
            </div>
          ))}
        </div>

        {/* Conversation */}
        <div className="flex-1 bg-white border border-[#e8ddd4] rounded-2xl p-4 overflow-y-auto space-y-4 min-h-0">
          {messages.map(msg => {
            const IntentIcon = msg.intent ? (INTENT_ICONS[msg.intent] || Bot) : Bot;
            return (
              <div key={msg.id} className={cn("flex gap-3", msg.role === "user" ? "justify-end" : "justify-start")}>
                {msg.role === "assistant" && (
                  <div className="w-8 h-8 rounded-xl bg-[#b3622d] flex items-center justify-center shrink-0 mt-0.5">
                    <IntentIcon className="w-4 h-4 text-white" />
                  </div>
                )}
                <div className={cn(
                  "max-w-[75%] rounded-2xl px-4 py-3",
                  msg.role === "user"
                    ? "bg-[#b3622d] text-white rounded-tr-sm"
                    : "bg-[#f6f3ee] text-[#1d1b17] border border-[#e8ddd4] rounded-tl-sm"
                )}>
                  <p className="text-sm leading-relaxed">{msg.content}</p>
                  {msg.data && Object.keys(msg.data).length > 0 && (
                    <div className="mt-2 pt-2 border-t border-white/20 grid grid-cols-2 gap-1">
                      {Object.entries(msg.data).slice(0, 4).map(([k, v]) => (
                        <div key={k} className="text-[10px]">
                          <span className="opacity-70 capitalize">{k.replace(/_/g, " ")}: </span>
                          <span className="font-semibold">
                            {typeof v === "number"
                              ? v > 1000 ? `₹${(v as number).toLocaleString()}` : v.toString()
                              : String(v)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className={cn("text-[9px] mt-1", msg.role === "user" ? "text-white/60 text-right" : "text-[#b0a499]")}>
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                </div>
                {msg.role === "user" && (
                  <div className="w-8 h-8 rounded-xl bg-[#1d1b17] flex items-center justify-center shrink-0 mt-0.5">
                    <User className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>
            );
          })}
          {processing && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-xl bg-[#b3622d] flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-[#f6f3ee] border border-[#e8ddd4] rounded-2xl rounded-tl-sm px-4 py-3">
                <div className="flex gap-1">
                  {[0, 1, 2].map(i => (
                    <div key={i} className="w-2 h-2 rounded-full bg-[#b3622d] animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                  ))}
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Suggestions */}
        <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
          {SUGGESTIONS.map(s => (
            <button
              key={s}
              onClick={() => sendCommand(s)}
              className="shrink-0 text-[11px] font-semibold text-[#6a6054] bg-white border border-[#e8ddd4] hover:border-[#b3622d] hover:text-[#b3622d] px-3 py-1.5 rounded-full transition-all"
            >
              {s}
            </button>
          ))}
        </div>

        {/* Input */}
        <div className="flex items-center gap-3 bg-white border border-[#e8ddd4] rounded-2xl px-4 py-3">
          <button
            onClick={toggleMic}
            className={cn(
              "w-10 h-10 rounded-xl flex items-center justify-center transition-all shrink-0",
              recording ? "bg-red-500 text-white animate-pulse" : "bg-[#f6f3ee] text-[#6a6054] hover:bg-[#b3622d] hover:text-white"
            )}
          >
            {recording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>
          {recording && (
            <div className="flex items-center gap-1 shrink-0">
              {[0, 1, 2, 3, 4].map(i => (
                <div
                  key={i}
                  className="w-1 bg-red-500 rounded-full animate-pulse"
                  style={{ height: `${8 + Math.random() * 16}px`, animationDelay: `${i * 0.1}s` }}
                />
              ))}
            </div>
          )}
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && sendCommand(input)}
            placeholder={recording ? "Listening..." : "Ask about revenue, burn, invoices, anomalies..."}
            className="flex-1 text-sm bg-transparent outline-none text-[#1d1b17] placeholder-[#b0a499]"
            disabled={recording || processing}
          />
          <button
            onClick={() => sendCommand(input)}
            disabled={!input.trim() || processing}
            className="w-10 h-10 rounded-xl bg-[#b3622d] hover:bg-[#9d4f22] text-white flex items-center justify-center transition-all disabled:opacity-40 shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
