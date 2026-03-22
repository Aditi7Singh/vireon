"use client";

import { useState, useRef, useEffect } from "react";
import { useAppStore } from "@/lib/store";
import { cn, formatRelativeTime } from "@/lib/utils";
import { X, Send, Bot, User, MessageSquare, Sparkles, Loader2, Zap, ArrowRight, CornerDownLeft } from "lucide-react";

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

import { AlertTriangle, Users, BarChart3 } from "lucide-react";

import api, { AgentMessage } from "@/lib/api";

export function ChatDrawer() {
  const { chatOpen, closeChat, chatSessionId, setChatSessionId, chatContext } = useAppStore();
  const normalizedChatContext = typeof chatContext === "string" ? chatContext : "";
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Load history when session changes or chat opens
  useEffect(() => {
    if (chatOpen && chatSessionId) {
      loadHistory();
    }
  }, [chatOpen, chatSessionId]);

  const lastTriggeredContext = useRef<string | null>(null);

  // Handle proactive messages when context changes specifically
  useEffect(() => {
    if (chatOpen && normalizedChatContext && normalizedChatContext !== lastTriggeredContext.current) {
      triggerProactiveMessage();
      lastTriggeredContext.current = normalizedChatContext;
    }
  }, [normalizedChatContext, chatOpen]);

  const triggerProactiveMessage = () => {
    // Only trigger if history is empty (optional but safer)
    if (messages.length > 5) return; 

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
    }
  };

  const loadHistory = async () => {
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
          ? `Hello! I'm your AI CFO. I've analyzed the financial data for this ${normalizedChatContext} view. How can I help you?`
          : "Hello! I'm your AI CFO. I've analyzed your financial data and I'm ready to help you understand your runway, detect anomalies, and answer questions about your business finances.";
        
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
  };

  useEffect(() => {
    if (chatOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [chatOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text?: string) => {
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
      setMessages((prev: Message[]) =>
        prev.map((msg: Message) =>
          msg.isLoading
            ? {
                ...msg,
                content: "I encountered an error connecting to the intelligence engine. Please try again.",
                isLoading: false,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  if (!chatOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-[480px] bg-white/80 dark:bg-slate-950/80 backdrop-blur-2xl border-l border-slate-200/50 dark:border-slate-800/50 shadow-[-20px_0_50px_rgba(0,0,0,0.1)] dark:shadow-[-20px_0_50px_rgba(0,0,0,0.3)] z-[100] flex flex-col transition-all duration-500 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between h-24 px-8 border-b border-slate-200/50 dark:border-slate-800/50 shrink-0 bg-slate-50/50 dark:bg-slate-900/50">
        <div className="flex items-center gap-4">
          <div className="relative">
             <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl shadow-lg ring-4 ring-white dark:ring-slate-950">
               <Sparkles className="w-5 h-5 text-white" />
             </div>
             <div className="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-emerald-500 border-2 border-white dark:border-slate-950 rounded-full animate-pulse" />
          </div>
          <div>
            <h2 className="text-lg font-black text-slate-900 dark:text-white font-outfit tracking-tight">
              AI Financial Assistant
            </h2>
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Connected to Financial Intelligence</p>
          </div>
        </div>
        <button
          onClick={closeChat}
          className="p-2.5 text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-2xl transition-all"
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
               <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                  {msg.role === "assistant" ? "AI CFO" : "You"}
               </span>
               <span className="text-[10px] text-slate-400 font-medium">
                  {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
               </span>
            </div>
            
            <div
              className={cn(
                "relative p-5 text-sm font-medium leading-relaxed transition-all duration-300",
                msg.role === "user"
                  ? "bg-indigo-600 text-white rounded-3xl rounded-tr-sm shadow-xl shadow-indigo-500/10"
                  : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl rounded-tl-sm whitespace-pre-wrap dark:text-slate-200 shadow-sm"
              )}
            >
              {msg.isLoading ? (
                <div className="flex items-center gap-2 py-1 px-4">
                  <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce"></div>
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
            <p className="text-[10px] font-black uppercase tracking-tighter text-slate-400 mb-4 ml-1">Suggested Intelligence Queries</p>
            <div className="grid grid-cols-2 gap-3">
              {QUICK_PROMPTS.map((prompt) => (
                <button
                  key={prompt.text}
                  onClick={() => handleSend(prompt.text)}
                  className="flex items-center gap-3 p-3.5 rounded-2xl text-xs font-bold bg-white dark:bg-slate-900 border border-slate-200/50 dark:border-slate-800/50 text-slate-700 dark:text-slate-300 hover:border-indigo-500/50 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all text-left shadow-sm group"
                >
                  <prompt.icon className="w-4 h-4 text-indigo-500 group-hover:scale-110 transition-transform" />
                  <span className="truncate">{prompt.text}</span>
                  <ArrowRight className="w-3 h-3 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="relative group">
          <div className="absolute inset-x-0 -bottom-1 h-px bg-gradient-to-r from-transparent via-indigo-500 to-transparent opacity-0 group-focus-within:opacity-100 transition-opacity duration-700" />
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
              className="w-full pl-6 pr-24 py-5 bg-slate-100/50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-800/50 rounded-[28px] text-sm focus:outline-none focus:bg-white dark:focus:bg-slate-900 focus:ring-4 focus:ring-indigo-500/5 transition-all text-slate-900 dark:text-white placeholder-slate-400 font-bold resize-none min-h-[64px]"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
               <div className="hidden sm:flex items-center gap-1.5 px-2 py-1 rounded-lg bg-slate-200/50 dark:bg-slate-800/50 border border-slate-300/50 dark:border-slate-700/50">
                  <span className="text-[10px] font-black text-slate-500">Enter</span>
                  <CornerDownLeft className="w-3 h-3 text-slate-500" />
               </div>
               <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="p-3 rounded-2xl bg-indigo-600 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:bg-indigo-500 active:scale-90 shadow-lg shadow-indigo-600/20"
               >
                  <Send className="w-4 h-4" />
               </button>
            </div>
          </form>
        </div>
        <p className="mt-4 text-[10px] text-center font-bold text-slate-400 uppercase tracking-tighter">Powered by Agentic Intelligence (V0 Alpha)</p>
      </div>
    </div>
  );
}

export default ChatDrawer;
