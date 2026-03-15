'use client';

import { useEffect, useRef, useState } from 'react';
import { useAppStore } from '@/lib/store';
import { useStreamingChat, loadChatHistory, generateSessionId } from '@/hooks/useChat';
import { parseMarkdownRanges, extractScenarioResult, formatRelativeTime } from '@/lib/utils';
import { X, Send, Loader, Plus, Sparkles, MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';

const QUICK_PROMPTS = [
  "What's our runway?",
  'Any spending alerts?',
  'What if we hire 2 engineers?',
  'Give me a financial overview',
];

export function ChatDrawer() {
  const {
    chatOpen,
    closeChat,
    chatMessages,
    addChatMessage,
    setChatMessages,
    sessionId,
    initSession,
    startNewConversation,
  } = useAppStore();
  const { sendMessage, streaming, currentResponse } = useStreamingChat();
  const [input, setInput] = useState('');
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [showQuickPrompts, setShowQuickPrompts] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Initialize session on mount
  useEffect(() => {
    const initializeSession = async () => {
      let sid = sessionId;

      // Load from localStorage if available
      if (!sid) {
        const storedSession = localStorage.getItem('cfo_session_id');
        if (storedSession) {
          sid = storedSession;
          initSession(sid);
        }
      }

      // If we have a session ID, load history
      if (sid && chatMessages.length === 0) {
        setIsLoadingHistory(true);
        try {
          const history = await loadChatHistory(sid);
          if (history?.messages && history.messages.length > 0) {
            setChatMessages(history.messages);
            setShowQuickPrompts(false);
          }
        } catch (error) {
          console.error('Failed to load chat history:', error);
        } finally {
          setIsLoadingHistory(false);
        }
      }

      // Generate new session if needed
      if (!sid) {
        sid = generateSessionId();
        localStorage.setItem('cfo_session_id', sid);
        initSession(sid);
      }
    };

    initializeSession();
  }, []);

  // Hide quick prompts after first message
  useEffect(() => {
    if (chatMessages.length > 0) {
      setShowQuickPrompts(false);
    }
  }, [chatMessages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages, currentResponse]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 120) + 'px';
    }
  }, [input]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || streaming) return;

    const message = input.trim();
    setInput('');
    setShowQuickPrompts(false);
    await sendMessage(message);
  };

  const handleQuickPrompt = async (prompt: string) => {
    setShowQuickPrompts(false);
    await sendMessage(prompt);
  };

  const handleNewConversation = () => {
    startNewConversation();
    localStorage.removeItem('cfo_session_id');
    setShowQuickPrompts(true);
  };

  return (
    <>
      {/* Drawer */}
      <aside
        className={cn(
          'fixed right-0 top-0 h-screen w-full max-w-md bg-cfo-surface border-l border-cfo-border flex flex-col transition-transform duration-300 z-40 shadow-2xl',
          chatOpen ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        {/* Header */}
        <div className="p-4 border-b border-cfo-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-white text-sm">AI CFO</h3>
              <p className="text-xs text-cfo-muted">Qwen3 via Groq</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleNewConversation}
              className="p-2 hover:bg-cfo-surface2 rounded-lg transition-colors text-cfo-muted hover:text-white"
              title="Start new conversation"
            >
              <Plus className="w-4 h-4" />
            </button>
            <button
              onClick={() => closeChat()}
              className="p-2 hover:bg-cfo-surface2 rounded-lg transition-colors text-cfo-muted hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 flex flex-col">
          {isLoadingHistory ? (
            <div className="flex items-center justify-center h-full">
              <Loader className="animate-spin text-cfo-accent" size={24} />
            </div>
          ) : chatMessages.length === 0 && !showQuickPrompts ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <MessageSquare className="w-12 h-12 text-cfo-muted mb-3 opacity-30" />
              <p className="text-cfo-muted mb-1 text-sm">Start a conversation</p>
              <p className="text-xs text-cfo-muted">Ask about your finances, anomalies, or scenarios</p>
            </div>
          ) : (
            <>
              {/* Chat Messages */}
              {chatMessages.map((msg, i) => (
                <ChatMessage key={i} message={msg} />
              ))}

              {/* Streaming Response */}
              {currentResponse && (
                <ChatMessage
                  message={{
                    role: 'assistant',
                    content: currentResponse,
                    timestamp: new Date().toISOString(),
                  }}
                  isStreaming
                />
              )}

              {/* Loading Indicator */}
              {streaming && !currentResponse && (
                <div className="flex justify-start">
                  <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-cfo-surface2">
                    <Loader className="animate-spin text-cfo-accent w-4 h-4" />
                    <span className="text-xs text-cfo-muted">Processing...</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}

          {/* Quick Prompts */}
          {showQuickPrompts && chatMessages.length === 0 && !isLoadingHistory && (
            <div className="space-y-2 mt-auto mb-4">
              <p className="text-xs text-cfo-muted px-2">Quick prompts:</p>
              {QUICK_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => handleQuickPrompt(prompt)}
                  className="w-full px-3 py-2 text-left text-sm rounded-lg bg-cfo-surface2 text-white hover:bg-cfo-border border border-cfo-border transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="p-4 border-t border-cfo-border space-y-3">
          <div className="flex gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e as React.FormEvent<HTMLTextAreaElement>);
                }
              }}
              placeholder="Ask about spending, runway, scenarios..."
              disabled={streaming}
              rows={1}
              className="flex-1 px-3 py-2 rounded-lg bg-cfo-surface2 border border-cfo-border text-white placeholder-cfo-muted focus:outline-none focus:border-cfo-accent text-sm disabled:opacity-50 resize-none"
            />
            <button
              type="submit"
              disabled={streaming || !input.trim()}
              className="px-3 py-2 rounded-lg bg-cfo-accent text-black hover:bg-opacity-90 disabled:opacity-50 transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-cfo-muted">Shift+Enter for new line</p>
        </form>
      </aside>

      {/* Overlay */}
      {chatOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30"
          onClick={() => closeChat()}
        />
      )}
    </>
  );
}

interface ChatMessageProps {
  message: {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
  };
  isStreaming?: boolean;
}

function ChatMessage({ message, isStreaming }: ChatMessageProps) {
  const scenarioResult = extractScenarioResult(message.content);

  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-xs px-4 py-3 rounded-xl text-sm bg-cfo-accent text-black rounded-tr-none">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start gap-2">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
        <Sparkles className="w-4 h-4 text-white" />
      </div>

      <div className="flex-1 space-y-2">
        {/* Message Bubble */}
        <div className="max-w-sm px-4 py-3 rounded-xl text-sm bg-cfo-surface2 text-white rounded-tl-none whitespace-pre-wrap break-words">
          <MarkdownRenderer text={message.content} />
        </div>

        {/* Scenario Result Card */}
        {scenarioResult && (
          <ScenarioCard result={scenarioResult} />
        )}

        {/* Timestamp */}
        <p className="text-xs text-cfo-muted px-4">{formatRelativeTime(message.timestamp)}</p>
      </div>
    </div>
  );
}

interface ScenarioCardProps {
  result: {
    title: string;
    metrics: Array<{ label: string; before: string; after: string }>;
  };
}

function ScenarioCard({ result }: ScenarioCardProps) {
  return (
    <div className="max-w-sm px-4 py-3 rounded-lg bg-cfo-surface border border-cfo-border border-l-4 border-l-cfo-accent">
      <p className="font-semibold text-white text-sm mb-2">{result.title}</p>
      <div className="space-y-1">
        {result.metrics.map((metric, i) => (
          <div key={i} className="flex items-center justify-between text-xs">
            <span className="text-cfo-muted">{metric.label}:</span>
            <div className="flex items-center gap-2">
              <span className="text-cfo-muted line-through">{metric.before}</span>
              <span className="text-cfo-accent font-semibold">→</span>
              <span className="text-white font-semibold">{metric.after}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

interface MarkdownRendererProps {
  text: string;
}

function MarkdownRenderer({ text }: MarkdownRendererProps) {
  const parts = parseMarkdownRanges(text);

  return (
    <>
      {parts.map((part, i) => {
        switch (part.type) {
          case 'bold':
            return <strong key={i}>{part.content}</strong>;
          case 'italic':
            return <em key={i}>{part.content}</em>;
          case 'code':
            return (
              <code key={i} className="bg-cfo-surface px-2 py-0.5 rounded text-xs font-mono">
                {part.content}
              </code>
            );
          default:
            return <span key={i}>{part.content}</span>;
        }
      })}
    </>
  );
}



