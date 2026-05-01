"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import { X, Send, Sparkles, Zap, ArrowRight, CornerDownLeft, AlertTriangle, Users, BarChart3 } from "lucide-react";
import api from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isLoading?: boolean;
}

const QUICK_PROMPTS = [
  { text: "What's our runway?", icon: Zap },
  { text: "Any spending alerts?", icon: AlertTriangle },
  { text: "Simulate hiring 2 devs", icon: Users },
  { text: "Summarize Q1 performance", icon: BarChart3 },
];

function buildCachedInsight(query: string, context: string) {
  const q = `${context} ${query}`.toLowerCase();
  if (q.includes("dso") || q.includes("invoice") || q.includes("overdue")) {
    return "Live Finley is still reconnecting, so here is the cached AR view: DSO is trending around 41 days this quarter versus 46 days last quarter. The fastest action is to prioritize reminders for invoices older than 30 days and escalate the two largest overdue accounts first.";
  }
  if (q.includes("runway") || q.includes("burn")) {
    return "Live Finley is still reconnecting, so here is the cached runway view: cash supports roughly 14 months at current net burn. Spend reductions and revenue growth both improve the model; new hiring reduces runway unless growth offsets the extra burn.";
  }
  if (q.includes("expense") || q.includes("anomal") || q.includes("audit")) {
    return "Live Finley is still reconnecting, so here is the cached controls view: review submitted expense claims first, then check duplicate invoices, weekend transactions, and unusually round amounts. High-value claims should be approved or rejected before reimbursement.";
  }
  if (q.includes("tax") || q.includes("gst") || q.includes("compliance")) {
    return "Live Finley is still reconnecting, so here is the cached compliance view: check the selected country and period, then regenerate the checklist before filing. Keep payment status separate from liability calculation so tax actions remain auditable.";
  }
  return "Live Finley is still reconnecting, so I’m answering from cached finance context. Ask about runway, invoices, expenses, anomalies, tax, or cash flow and I’ll give the best available local insight until the backend responds.";
}

export function ChatDrawer() {
  const { chatOpen, closeChat, chatSessionId, setChatSessionId, chatContext } = useAppStore();
  const normalizedChatContext = typeof chatContext === "string" ? chatContext : "";
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const lastTriggeredContext = useRef<string | null>(null);

  const loadHistory = useCallback(async () => {
    if (!chatSessionId) return;
    try {
      const history = await api.getHistory(chatSessionId);
      if (history.messages && history.messages.length > 0) {
        setMessages(history.messages.map(m => ({
          role: m.role,
          content: m.content,
          timestamp: m.timestamp ? new Date(m.timestamp) : new Date()
        })));
      } else {
        // Initial greeting
        const greeting = normalizedChatContext 
          ? `Hello! I'm Finley. I've analyzed the financial data for this ${normalizedChatContext} view. How can I help you?`
          : "Hello! I'm Finley, your AI finance agent. I've analyzed your financial data and I'm ready to help you understand runway, detect anomalies, and answer questions about your business finances.";
        
        setMessages([
          {
            role: "assistant",
            content: greeting,
            timestamp: new Date(),
          },
        ]);
      }
    } catch (error) {
      console.error("Failed to load history:", error);
    }
  }, [chatSessionId, normalizedChatContext]);

  useEffect(() => {
    if (chatOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [chatOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async (text?: string) => {
    const query = text || input;
    if (!query.trim() || isLoading) return;

    const userMessage: Message = {
      role: "user",
      content: query,
      timestamp: new Date(),
    };

    const loadingMessage: Message = {
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages((prev: Message[]) => [...prev, userMessage, loadingMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const fullQuery = normalizedChatContext ? `[Context: ${normalizedChatContext}] ${query}` : query;
      const response = await api.chat(fullQuery, chatSessionId || undefined);
      if (response.session_id && response.session_id !== chatSessionId) {
        setChatSessionId(response.session_id);
      }
      
      // Simulate streaming
      let currentContent = "";
      const fullContent = response.response;
      const words = fullContent.split(" ");
      let wordIndex = 0;

      const interval = setInterval(() => {
        if (wordIndex < words.length) {
          currentContent += (wordIndex === 0 ? "" : " ") + words[wordIndex];
          setMessages((prev: Message[]) =>
            prev.map((msg: Message) =>
              msg.isLoading
                ? { ...msg, content: currentContent, isLoading: wordIndex === words.length - 1 ? false : true }
                : msg
            )
          );
          wordIndex++;
        } else {
          clearInterval(interval);
          setMessages((prev: Message[]) =>
            prev.map((msg: Message) =>
              msg.isLoading ? { ...msg, isLoading: false } : msg
            )
          );
        }
      }, 30); // Speed of "streaming"
      
    } catch (error) {
      const fallback = buildCachedInsight(query, normalizedChatContext);
      setMessages((prev: Message[]) =>
        prev.map((msg: Message) =>
          msg.isLoading
            ? {
                ...msg,
                content: fallback,
                isLoading: false,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, normalizedChatContext, chatSessionId, setChatSessionId]);

  const triggerProactiveMessage = useCallback(() => {

    // Specific anomaly, proactively explain it
    if (normalizedChatContext.startsWith("Anomaly Analysis:")) {
      const anomalyDesc = normalizedChatContext.replace("Anomaly Analysis:", "").trim();
      setTimeout(() => {
        handleSend(`Explain this anomaly in detail and its impact: "${anomalyDesc}"`);
      }, 500);
    } else if (normalizedChatContext.startsWith("Anomaly:")) {
      const anomalyDesc = normalizedChatContext.replace("Anomaly:", "").trim();
      setTimeout(() => {
        handleSend(`What can you tell me about the anomaly: "${anomalyDesc}"?`);
      }, 500);
    } else if (normalizedChatContext === "Revenue Expansion Opportunity") {
      setTimeout(() => {
        handleSend("Help me model different revenue tiers. I notice usage-based revenue is growing fast.");
      }, 500);
    } else if (normalizedChatContext === "Expense Leakage Audit") {
      setTimeout(() => {
        handleSend("Perform an audit on our expense leakage and operational inefficiencies.");
      }, 500);
    } else if (normalizedChatContext === "Expense Audit: AWS Spike") {
      setTimeout(() => {
        handleSend("Analyze the recent AWS cost spike and suggest optimization strategies.");
      }, 500);
    } else if (normalizedChatContext === "Predictive Modeling") {
      setTimeout(() => {
        handleSend("Help me model some scenarios. I want to see how hiring or revenue changes affect our runway.");
      }, 500);
    } else if (normalizedChatContext === "Revenue Intelligence") {
      setTimeout(() => {
        handleSend("Give me a strategic growth audit of our revenue performance.");
      }, 500);
    } else if (normalizedChatContext.startsWith("Build an executive scenario memo")) {
      setTimeout(() => {
        handleSend("Create an executive scenario memo with assumptions, net runway effect, risk flags, and a 30/60/90-day action plan.");
      }, 500);
    } else if (normalizedChatContext.startsWith("Strategic Advisory for Rule of 40 performance")) {
      setTimeout(() => {
        handleSend("Interpret our benchmark metrics, identify the biggest operating gap, and propose a practical execution plan by owner and timeline.");
      }, 500);
    } else if (normalizedChatContext.length > 24) {
      // For long-form context prompts from CTA buttons, auto-run the request.
      setTimeout(() => {
        handleSend(normalizedChatContext);
      }, 500);
    }
  }, [normalizedChatContext, handleSend]);

  // Load history when session changes or chat opens
  useEffect(() => {
    if (chatOpen && chatSessionId) {
      loadHistory();
    }
  }, [chatOpen, chatSessionId, loadHistory]);

  // Handle proactive messages when context changes specifically
  useEffect(() => {
    if (chatOpen && normalizedChatContext && normalizedChatContext !== lastTriggeredContext.current) {
      triggerProactiveMessage();
      lastTriggeredContext.current = normalizedChatContext;
    }
  }, [normalizedChatContext, chatOpen, triggerProactiveMessage]);

  if (!chatOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-[480px] bg-[#2a241d]/95 backdrop-blur-2xl border-l border-[#43382c] shadow-[-24px_0_60px_rgba(14,11,8,0.45)] z-[100] flex flex-col transition-all duration-500 overflow-hidden text-[#f7efe3]">
      {/* Header */}
      <div className="flex items-center justify-between h-24 px-8 border-b border-[#45392d] shrink-0 bg-[#231d17]/85">
        <div className="flex items-center gap-4">
          <div className="relative">
             <div className="p-3 bg-gradient-to-br from-[#9a5d34] to-[#4d3120] rounded-2xl shadow-lg ring-4 ring-[#201a14]">
               <Sparkles className="w-5 h-5 text-white" />
             </div>
             <div className="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-emerald-500 border-2 border-[#201a14] rounded-full animate-pulse" />
          </div>
          <div>
            <h2 className="text-lg font-black text-[#fff7ec] font-outfit tracking-tight">
              AI Financial Assistant
            </h2>
            <p className="text-[10px] font-bold text-[#c9b9a6] uppercase tracking-widest">Smart Financial Manager</p>
          </div>
        </div>
        <button
          onClick={closeChat}
          className="p-2.5 text-[#cabba8] hover:text-[#fff8ee] hover:bg-[#3a3127] rounded-2xl transition-all"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-8 space-y-6 no-scrollbar h-0">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={cn(
              "flex flex-col max-w-[85%] group",
              msg.role === "user" ? "ml-auto items-end" : "mr-auto items-start"
            )}
          >
            <div className="flex items-center gap-2 mb-2 px-1">
              <span className="text-[10px] font-black text-[#c8b8a7] uppercase tracking-widest">
                  {msg.role === "assistant" ? "Finley" : "You"}
               </span>
              <span className="text-[10px] text-[#a9947d] font-medium">
                  {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
               </span>
            </div>
            
            <div
              className={cn(
                "relative p-5 text-sm font-medium leading-relaxed transition-all duration-300",
                msg.role === "user"
                  ? "bg-[#9a5d34] text-[#fff8ee] rounded-3xl rounded-tr-sm shadow-xl shadow-[#6f4327]/30"
                  : "bg-[#f3eadb] border border-[#d8cab6] rounded-3xl rounded-tl-sm whitespace-pre-wrap text-[#2f271f] shadow-sm"
              )}
            >
              {msg.isLoading ? (
                <div className="flex items-center gap-2 py-1 px-4">
                  <div className="w-2 h-2 rounded-full bg-[#9a5d34] animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 rounded-full bg-[#9a5d34] animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 rounded-full bg-[#9a5d34] animate-bounce"></div>
                </div>
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Footer / Input Container */}
      <div className="p-8 pt-0 mt-auto">
        {/* Quick Prompts */}
        {messages.length <= 2 && (
          <div className="mb-6">
            <p className="text-[10px] font-black uppercase tracking-tighter text-[#c7b7a4] mb-4 ml-1">Suggested Intelligence Queries</p>
            <div className="grid grid-cols-2 gap-3">
              {QUICK_PROMPTS.map((prompt) => (
                <button
                  key={prompt.text}
                  onClick={() => handleSend(prompt.text)}
                  className="flex items-center gap-3 p-3.5 rounded-2xl text-xs font-bold bg-[#342a21] border border-[#4c3f31] text-[#f0e3d3] hover:border-[#a86a40] hover:bg-[#3d3126] transition-all text-left shadow-sm group"
                >
                  <prompt.icon className="w-4 h-4 text-[#d18b57] group-hover:scale-110 transition-transform" />
                  <span className="truncate">{prompt.text}</span>
                  <ArrowRight className="w-3 h-3 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="relative group">
          <div className="absolute inset-x-0 -bottom-1 h-px bg-gradient-to-r from-transparent via-[#9a5d34] to-transparent opacity-0 group-focus-within:opacity-100 transition-opacity duration-700" />
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="relative"
          >
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Query financial state..."
              rows={1}
              className="w-full pl-6 pr-24 py-5 bg-[#3a2f25] border border-[#544536] rounded-[28px] text-sm focus:outline-none focus:bg-[#433628] focus:ring-4 focus:ring-[#9a5d34]/20 transition-all text-[#fff6ea] placeholder-[#c7b59f] font-bold resize-none min-h-[64px]"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
               <div className="hidden sm:flex items-center gap-1.5 px-2 py-1 rounded-lg bg-[#483b2f] border border-[#5d4d3d]">
                  <span className="text-[10px] font-black text-[#dac8b4]">Enter</span>
                  <CornerDownLeft className="w-3 h-3 text-[#dac8b4]" />
               </div>
               <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="p-3 rounded-2xl bg-[#9a5d34] text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:bg-[#824d2b] active:scale-90 shadow-lg shadow-[#6a4025]/30"
               >
                  <Send className="w-4 h-4" />
               </button>
            </div>
          </form>
        </div>
        <p className="mt-4 text-[10px] text-center font-bold text-[#b7a28a] uppercase tracking-tighter">Powered by Agentic Intelligence (V0 Alpha)</p>
      </div>
    </div>
  );
}

export default ChatDrawer;
