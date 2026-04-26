"use client";

import { useEffect, useRef, useState } from "react";
import TopBar from "@/components/TopBar";
import api from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { AlertCircle, Bot, CheckCircle2, MessageSquare, RefreshCw, Send, Sparkles, User } from "lucide-react";
import { cn } from "@/lib/utils";

export default function AgentPage() {
  const { chatSessionId, setChatSessionId } = useAppStore();
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState<"ok" | "warning" | "unknown">("unknown");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chatSessionId) {
      setChatSessionId(`session_${Math.random().toString(36).substring(7)}`);
    }
  }, [chatSessionId, setChatSessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const loadHistory = async () => {
      if (!chatSessionId) return;
      try {
        const history = await api.getHistory(chatSessionId);
        if (history.messages?.length) {
          setMessages(history.messages.map((m) => ({ role: m.role, content: m.content })));
        } else {
          setMessages([{ role: "assistant", content: "I am ready to help with runway, burn, and growth decisions. What should we analyze first?" }]);
        }
      } catch {
        setMessages([{ role: "assistant", content: "Unable to load history. You can still start a new query." }]);
      }
    };
    loadHistory();
  }, [chatSessionId]);

  useEffect(() => {
    const loadHealth = async () => {
      try {
        const health = await api.getStartupHealth();
        setHealthStatus(health.status || "unknown");
      } catch {
        setHealthStatus("unknown");
      }
    };
    loadHealth();
  }, []);

  const handleSend = async (seed?: string) => {
    const query = (seed || input).trim();
    if (!query || isLoading) return;

    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setInput("");
    setIsLoading(true);
    try {
      const response = await api.chat(query, chatSessionId || undefined);
      setMessages((prev) => [...prev, { role: "assistant", content: response.response }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "I hit an error while processing that request." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#ece3d4] pb-10 text-[#1d1b17]">
      <TopBar title="Vireon AI Assistant" />

      <div className="mx-auto max-w-7xl px-4 pt-6 sm:px-6 lg:px-8">
        <section className="rounded-2xl border border-[#cfbfa9] bg-[#f8efe3] shadow-[0_16px_36px_rgba(63,45,24,0.12)]">
          <header className="border-b border-[#deceb8] p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="inline-flex items-center gap-2 rounded-full border border-[#cba880] bg-[#f5e1c8] px-3 py-1 text-xs font-semibold text-[#7a4c1c]"><Sparkles className="h-3.5 w-3.5" />Financial intelligence core</p>
              {healthStatus === "ok" ? (
                <span className="inline-flex items-center gap-1 rounded-full border border-[#b7d8bf] bg-[#edf8ef] px-2.5 py-1 text-[10px] font-semibold text-[#2f6a45]"><CheckCircle2 className="h-3 w-3" />Backend connected</span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-full border border-[#e1c4af] bg-[#fff2ee] px-2.5 py-1 text-[10px] font-semibold text-[#9f3f30]"><AlertCircle className="h-3 w-3" />Check backend status</span>
              )}
            </div>
          </header>

          <div className="max-h-[58vh] overflow-y-auto p-5 space-y-4">
            {messages.map((msg, idx) => (
              <div key={idx} className={cn("flex", msg.role === "user" ? "justify-end" : "justify-start")}>
                <div className={cn("max-w-[85%] rounded-2xl px-4 py-3 text-sm", msg.role === "user" ? "bg-[#2d241b] text-[#fff8ee]" : "border border-[#ddcfbc] bg-[#f6ecde] text-[#33291f]")}>
                  <div className="mb-1 inline-flex items-center gap-1 text-xs opacity-70">{msg.role === "user" ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}{msg.role}</div>
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="border-t border-[#e5dbc9] p-4">
            <div className="mb-3 flex flex-wrap gap-2">
              {[
                "Survival path audit",
                "Growth vector analysis",
                "GL anomaly detection",
                "Show top active alerts",
              ].map((s) => (
                <button key={s} onClick={() => handleSend(s)} className="rounded-full border border-[#ceb99d] bg-[#f7ead8] px-3 py-1.5 text-xs text-[#6f5837] hover:bg-[#efd9bf]">{s}</button>
              ))}
            </div>
            <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex items-center gap-2">
              <div className="relative flex-1">
                <MessageSquare className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8a7b68]" />
                <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask your finance question" className="w-full rounded-xl border border-[#ccb89d] bg-[#fff8ed] py-2.5 pl-10 pr-3 text-sm" />
              </div>
              <button type="submit" disabled={isLoading} className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-[#8f5632] text-[#fff8ee] disabled:opacity-60 hover:bg-[#764729]">
                {isLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </button>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
}
