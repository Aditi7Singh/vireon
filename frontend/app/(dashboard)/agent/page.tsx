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
    Search
} from "lucide-react";

import { useAppStore } from "@/lib/store";
import api, { AgentMessage } from "@/lib/api";

export default function AgentPage() {
    const { chatSessionId, setChatSessionId } = useAppStore();
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
                        content: "Hello! I'm Vireon, your AI CFO. I've analyzed your financial data and I'm ready to help you understanding your runway, detect anomalies, and answer questions about your business finances. \n\nHow can I help you today?",
                        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    }
                ]);
            }
        } catch (error) {
            console.error("Failed to load history:", error);
        }
    };

    const suggestions = [
        "What is our current runway?",
        "Why did cloud costs spike?",
        "Explain Net Revenue Retention",
        "How much could we save by cutting SaaS by 10%?"
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
                content: "I encountered an error while processing your financial data. Please ensure the backend is running and try again.",
                timestamp: now
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-160px)] max-w-5xl mx-auto">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-indigo-100 dark:bg-indigo-500/20 rounded-lg">
                        <Bot className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-zinc-900 dark:text-zinc-50">AI CFO Agent</h1>
                        <div className="flex items-center gap-2 mt-0.5">
                            <span className="flex h-2 w-2 rounded-full bg-emerald-500"></span>
                            <span className="text-xs text-zinc-500 font-medium font-sans">System Ready • Connected to ERPNext</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="flex-1 flex gap-6 overflow-hidden">
                <Card className="flex-1 flex flex-col p-0 overflow-hidden ring-1 ring-zinc-200 dark:ring-zinc-800 shadow-sm border-0 rounded-2xl bg-white dark:bg-zinc-950">
                    <div className="flex-1 overflow-y-auto p-8 space-y-8 scrollbar-hide">
                        {messages.map((msg, idx) => (
                            <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
                                <div className={`flex gap-4 max-w-[85%] ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                                    <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${msg.role === "user"
                                            ? "bg-zinc-100 dark:bg-zinc-800"
                                            : "bg-indigo-600 shadow-md shadow-indigo-200 dark:shadow-none"
                                        }`}>
                                        {msg.role === "user"
                                            ? <User className="w-4 h-4 text-zinc-600 dark:text-zinc-400" />
                                            : <Bot className="w-4 h-4 text-white" />
                                        }
                                    </div>
                                    <div className="flex flex-col space-y-1.5 min-w-0">
                                        <div className={`px-5 py-3.5 rounded-2xl text-sm leading-relaxed shadow-sm ${msg.role === "user"
                                                ? "bg-zinc-900 text-white dark:bg-zinc-800 rounded-tr-sm"
                                                : "bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-100 dark:border-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-tl-sm"
                                            }`}>
                                            <p className="whitespace-pre-wrap">{msg.content}</p>
                                        </div>
                                        <span className={`text-[10px] font-medium text-zinc-400 px-1 ${msg.role === "user" ? "text-right" : "text-left"}`}>
                                            {msg.timestamp}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className="flex justify-start animate-in fade-in duration-300">
                                <div className="bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-100 dark:border-zinc-800 rounded-2xl rounded-tl-sm px-5 py-3.5 shadow-sm">
                                    <span className="flex space-x-1.5 py-1">
                                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce"></span>
                                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce delay-75"></span>
                                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce delay-150"></span>
                                    </span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    <div className="p-6 bg-white dark:bg-zinc-950 border-t border-zinc-100 dark:border-zinc-900">
                        <div className="flex flex-wrap gap-2 mb-4">
                            {suggestions.map((s, i) => (
                                <button
                                    key={i}
                                    onClick={() => handleSend(s)}
                                    className="px-3 py-1.5 rounded-full text-xs font-medium bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400 hover:border-indigo-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-all flex items-center gap-1.5 shadow-sm"
                                >
                                    <MessageSquare className="w-3 h-3" />
                                    {s}
                                </button>
                            ))}
                        </div>
                        <form
                            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
                            className="relative"
                        >
                            <input
                                className="w-full pl-5 pr-14 py-4 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-zinc-900 dark:text-white placeholder-zinc-400 shadow-inner"
                                placeholder="Ask your AI CFO anything..."
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                disabled={isLoading}
                            />
                            <button
                                type="submit"
                                disabled={isLoading || !input.trim()}
                                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-indigo-600 text-white disabled:opacity-50 transition-all shadow-md shadow-indigo-100 dark:shadow-none hover:bg-indigo-500 active:scale-95"
                            >
                                <Send className="w-4 h-4" />
                            </button>
                        </form>
                    </div>
                </Card>
            </div>
        </div>
    );
}
