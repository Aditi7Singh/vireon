/**
 * Custom Hook for Agent Chat with Streaming Support
 * Uses fetch with ReadableStream for POST streaming
 */

import { useCallback, useEffect, useState } from 'react';
import { useAppStore } from '@/lib/store';
import { API, ChatHistory } from '@/lib/api';

const API_BASE =
  typeof window !== 'undefined'
    ? process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    : 'http://localhost:8000';

export function useStreamingChat() {
  const [streaming, setStreaming] = useState(false);
  const [currentResponse, setCurrentResponse] = useState('');
  const { sessionId, addChatMessage, setChatLoading } = useAppStore();

  const sendMessage = useCallback(
    async (query: string) => {
      // Add user message to history
      addChatMessage({
        role: 'user',
        content: query,
        timestamp: new Date().toISOString(),
      });

      setStreaming(true);
      setChatLoading(true);
      setCurrentResponse('');

      try {
        let fullResponse = '';

        const response = await fetch(`${API_BASE}/agent/chat/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query,
            session_id: sessionId,
          }),
        });

        if (!response.ok) {
          throw new Error(`Stream error: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error('No reader available');

        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              try {
                const json = JSON.parse(data);
                if (json.done) {
                  continue;
                }
                if (json.text) {
                  fullResponse += json.text;
                  setCurrentResponse(fullResponse);
                }
              } catch {
                // Skip invalid JSON
              }
            }
          }
        }

        // Add assistant message to history
        addChatMessage({
          role: 'assistant',
          content: fullResponse,
          timestamp: new Date().toISOString(),
        });
      } catch (error) {
        console.error('Chat error:', error);
        addChatMessage({
          role: 'assistant',
          content:
            'Sorry, I encountered an error. Please try again.',
          timestamp: new Date().toISOString(),
        });
      } finally {
        setStreaming(false);
        setChatLoading(false);
        setCurrentResponse('');
      }
    },
    [sessionId, addChatMessage, setChatLoading]
  );

  return {
    sendMessage,
    streaming,
    currentResponse,
  };
}

/**
 * Load chat history from server
 */
export async function loadChatHistory(sessionId: string): Promise<ChatHistory | null> {
  if (!sessionId) return null;
  return API.getHistory(sessionId);
}

/**
 * Generate new session ID
 */
export function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Hook to dismiss an alert
 */
export function useDismissAlert() {
  const [loading, setLoading] = useState(false);

  const dismissAlert = useCallback(async (alertId: string) => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/alerts/${alertId}/dismiss`,
        { method: 'PATCH' }
      );
      return response.ok;
    } catch {
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  return { dismissAlert, loading };
}


