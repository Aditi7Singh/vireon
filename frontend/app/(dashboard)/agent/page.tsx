"use client";

import { useState, useRef, useEffect } from "react";
import { Card, TextInput, Button, Text, Divider, Flex, Icon, Badge } from "@tremor/react";
import {
    Send,
    Bot,
    User,
    Sparkles,
    History,
    Lightbulb,
    MessageSquare,
    ChevronRight,
    Search,
    Wallet,
    TrendingUp,
    AlertTriangle,
    Hexagon,
    Shield,
    ShieldCheck,
    Target,
    RefreshCw,
} from "lucide-react";

import { useAppStore } from "@/lib/store";
import api, { AgentMessage } from "@/lib/api";
import { cn } from "@/lib/utils";

import TopBar from "@/components/TopBar";

export default function AgentPage() {
    const { chatSessionId, setChatSessionId, openChat } = useAppStore();
    const [messages, setMessages] = useState<any[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Initialize session if needed
    useEffect(() => {
        if (!chatSessionId) {
            setChatSessionId(`session_${Math.random().toString(36).substring(7)}`);
        }
    }, [chatSessionId, setChatSessionId]);

    // Load history
    useEffect(() => {
        if (chatSessionId) {
            loadHistory();
        }
    }, [chatSessionId]);

    const loadHistory = async () => {
        try {
            const history = await api.getHistory(chatSessionId!);
            if (history.messages && history.messages.length > 0) {
                setMessages(history.messages.map(m => ({
                    role: m.role,
                    content: m.content,
                    timestamp: new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                })));
            } else {
                setMessages([
                    {
                        role: "assistant",
                        content: "Hello! I'm your Vireon AI CFO. I've mapped your institutional data feeds and I'm ready to conduct a deep survival audit or growth projection. \n\nWhat high-level vector should we analyze today?",
                        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    }
                ]);
            }
        } catch (error) {
            console.error("Failed to load history:", error);
        }
    };

    const suggestions = [
        { text: "Survival Path Audit", icon: Wallet },
        { text: "Growth Vector Analysis", icon: TrendingUp },
        { text: "GL Anomaly Detection", icon: AlertTriangle },
        { text: "Capital Scenario Modeling", icon: Sparkles }
    ];

    const handleSend = async (text?: string) => {
        const query = text || input;
        if (!query.trim() || isLoading) return;

        const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const userMessage = { role: "user", content: query, timestamp: now };
        setMessages(prev => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        try {
            const response = await api.chat(query, chatSessionId || undefined);

            const assistantNow = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            setMessages(prev => [...prev, {
                role: "assistant",
                content: response.response,
                timestamp: assistantNow
            }]);
        } catch (error) {
            setMessages(prev => [...prev, {
                role: "assistant",
                content: "I encountered a protocol error. Ensure the intelligence node is online and try again.",
                timestamp: now
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 flex flex-col">
            <TopBar title="Vireon AI Assistant" />

            <div className="flex-1 p-6 flex flex-col max-w-[1400px] mx-auto w-full overflow-hidden">
                {/* Header Section */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10">
                    <div className="space-y-4">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-bold uppercase tracking-wider">
                            <Bot className="w-3.5 h-3.5" />
                            Financial Intelligence Core
                        </div>
                        <h1 className="text-4xl font-black text-white tracking-tight font-outfit">
                            Vireon <span className="text-slate-500">Assistant</span>
                        </h1>
                    </div>
                </div>

                <div className="flex-1 flex gap-8 min-h-0">
                    {/* Main Chat Interface */}
                    <div className="flex-1 flex flex-col bg-slate-900 border border-white/10 rounded-3xl overflow-hidden relative shadow-2xl">
                        {/* Messages Area */}
                        <div className="flex-1 overflow-y-auto p-8 space-y-10 no-scrollbar scroll-smooth">
                            {messages.map((msg, idx) => (
                                <div key={idx} className={cn("flex w-full", msg.role === "user" ? "justify-end" : "justify-start")}>
                                    <div className={cn("flex gap-4 max-w-[85%]", msg.role === "user" ? "flex-row-reverse" : "flex-row")}>
                                        <div className={cn(
                                            "w-10 h-10 rounded-xl shrink-0 flex items-center justify-center shadow-lg transition-transform",
                                            msg.role === "user"
                                                ? "bg-slate-800 border border-white/10 text-white"
                                                : "bg-indigo-600 text-white"
                                        )}>
                                            {msg.role === "user" ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                                        </div>
                                        <div className={cn("flex flex-col space-y-2", msg.role === "user" ? "items-end" : "items-start")}>
                                            <div className={cn(
                                                "px-6 py-4 rounded-2xl text-sm leading-relaxed",
                                                msg.role === "user"
                                                    ? "bg-indigo-600 text-white rounded-tr-none"
                                                    : "bg-slate-800 border border-white/5 text-slate-200 rounded-tl-none"
                                            )}>
                                                <p className="whitespace-pre-wrap">{msg.content}</p>
                                            </div>
                                            <span className="text-[10px] font-bold text-slate-600 uppercase tracking-wider">{msg.timestamp}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input Area */}
                        <div className="p-8 bg-slate-950/50 border-t border-white/5">
                            {/* suggestions */}
                            <div className="flex flex-wrap gap-3 mb-6">
                                {suggestions.map((s, i) => (
                                    <button
                                        key={i}
                                        onClick={() => handleSend(s.text)}
                                        className="btn-secondary text-[11px]"
                                    >
                                        <s.icon className="w-4 h-4 text-indigo-500 shrink-0" />
                                        {s.text}
                                    </button>
                                ))}
                            </div>

                            <form
                                onSubmit={(e) => { e.preventDefault(); handleSend(); }}
                                className="relative flex items-center gap-4"
                            >
                                <div className="relative flex-1 group/input">
                                    <MessageSquare className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500 group-focus-within/input:text-indigo-400" />
                                    <input
                                        className="w-full pl-14 pr-6 py-4 bg-slate-800 border border-white/10 rounded-2xl text-sm focus:outline-none focus:border-indigo-500/50 transition-all text-white placeholder-slate-500 shadow-inner"
                                        placeholder="Type your financial query..."
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        disabled={isLoading}
                                    />
                                </div>
                                <button
                                    type="submit"
                                    disabled={isLoading || !input.trim()}
                                    className="btn-primary p-4 shrink-0 flex items-center justify-center"
                                >
                                    {isLoading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                                </button>
                            </form>
                        </div>
                    </div>

                    {/* Sidebar Strategic Intel */}
                    <div className="hidden lg:flex w-80 flex-col gap-8">
                        <div className="bg-slate-900 border border-white/10 rounded-3xl p-8 shadow-xl">
                            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-6">Capacities</h3>
                            <div className="space-y-4">
                                {[
                                    { title: "Forensic Audit", desc: "Institutional GL Anomaly Detection", icon: Shield },
                                    { title: "Vector Modeling", desc: "Scenario-based Runway Projection", icon: Target },
                                    { title: "Compliance Core", desc: "Automated Tax Matrix Optimization", icon: ShieldCheck }
                                ].map((cap, i) => (
                                    <div key={i} className="p-4 bg-white/[0.03] border border-white/5 rounded-xl hover:border-white/10 transition-colors">
                                        <p className="text-[10px] font-bold uppercase tracking-widest text-indigo-400 mb-1 flex items-center gap-2">
                                            {cap.icon && <cap.icon className="w-3.5 h-3.5" />}
                                            {cap.title}
                                        </p>
                                        <p className="text-xs text-slate-400 leading-snug">{cap.desc}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="bg-slate-900 border border-white/10 rounded-3xl p-8 shadow-xl">
                            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-6 flex items-center gap-2">
                                <History className="w-4 h-4" />
                                Recent Analysis
                            </h3>
                            <div className="space-y-4">
                                {[
                                    "Stripe Volatility Alert: MAR 18",
                                    "Infrastructure Nodes Synced",
                                    "Runway Matrix Overhaul Complete"
                                ].map((insight, i) => (
                                    <div key={i} className="flex items-start gap-3 group cursor-pointer">
                                        <div className="w-1.5 h-1.5 rounded-full bg-slate-700 group-hover:bg-indigo-500 transition-colors mt-1.5" />
                                        <span className="text-[11px] font-medium text-slate-500 group-hover:text-slate-300 transition-colors">{insight}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
