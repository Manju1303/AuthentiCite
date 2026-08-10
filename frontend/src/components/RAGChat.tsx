'use client';

import React, { useState, useRef, useEffect } from 'react';
import { queryRAG, API_BASE_URL, RAGCitation } from '@/lib/api';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  citations?: RAGCitation[];
  isStreaming?: boolean;
}

interface RAGChatProps {
  paperId?: string;
  onCitationClick?: (sectionId: string, pageNumber: number) => void;
}

export const RAGChat: React.FC<RAGChatProps> = ({ paperId, onCitationClick }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Hello! I am your AuthentiCite RAG Assistant. Ask me anything about the document or research corpus.',
    },
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = inputQuery.trim();
    if (!query || isLoading) return;

    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `assistant-${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, sender: 'user', text: query },
      { id: assistantMsgId, sender: 'assistant', text: '', isStreaming: true, citations: [] },
    ]);

    setInputQuery('');
    setIsLoading(true);

    try {
      // Use SSE streaming endpoint
      const response = await fetch(`${API_BASE_URL}/api/v1/rag/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, paper_id: paperId, top_k: 4 }),
      });

      if (!response.body) {
        throw new Error('Streaming response body missing.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let streamedText = '';
      let extractedCitations: RAGCitation[] = [];

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim();
            if (!dataStr) continue;

            try {
              const data = JSON.parse(dataStr);

              if (data.type === 'metadata' && data.citations) {
                extractedCitations = data.citations;
              } else if (data.type === 'chunk' && data.text) {
                streamedText += data.text;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsgId
                      ? { ...msg, text: streamedText, citations: extractedCitations }
                      : msg
                  )
                );
              }
            } catch (err) {
              // Non-json chunk line
            }
          }
        }
      }

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId ? { ...msg, isStreaming: false } : msg
        )
      );
    } catch (err: any) {
      console.error('RAG query error, falling back to static query:', err);
      try {
        const res = await queryRAG(query, paperId);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? { ...msg, text: res.answer, citations: res.citations, isStreaming: false }
              : msg
          )
        );
      } catch (fallbackErr: any) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  text: 'Sorry, an error occurred while searching the document context.',
                  isStreaming: false,
                }
              : msg
          )
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 bg-slate-950/80 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 text-sm font-bold">
            🧠
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100">RAG Context Assistant</h3>
            <p className="text-[10px] text-slate-400 font-mono">Qdrant Hybrid Search & Reranker</p>
          </div>
        </div>
        <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          Live Citation
        </span>
      </div>

      {/* Message List */}
      <div className="flex-1 p-5 overflow-y-auto space-y-4 max-h-[500px]">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.sender === 'user' ? 'items-end' : 'items-start'
            }`}
          >
            <div
              className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-indigo-600 text-white rounded-br-none shadow-lg shadow-indigo-600/10'
                  : 'bg-slate-950/60 border border-slate-800 text-slate-200 rounded-bl-none'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>
              {msg.isStreaming && (
                <span className="inline-block ml-1 w-2 h-3 bg-indigo-400 animate-pulse" />
              )}

              {/* Interactive Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-2">
                  <span className="text-[9px] font-bold uppercase tracking-wider text-slate-400">
                    Source Citations:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {msg.citations.map((c) => (
                      <button
                        key={c.citation_id}
                        onClick={() =>
                          onCitationClick && onCitationClick(c.section_id, c.page_number)
                        }
                        className="px-2 py-1 bg-indigo-950/50 hover:bg-indigo-900/80 border border-indigo-500/30 hover:border-indigo-400 text-indigo-300 rounded-lg text-[10px] font-mono transition-all flex items-center space-x-1"
                        title={c.snippet}
                      >
                        <span>📌 [{c.citation_id}]</span>
                        <span className="text-slate-400">Page {c.page_number}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="p-4 bg-slate-950/90 border-t border-slate-800 flex space-x-3">
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder="Ask a question about this document..."
          className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-sans"
        />
        <button
          type="submit"
          disabled={isLoading || !inputQuery.trim()}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl transition-all flex items-center justify-center space-x-1 shadow-lg shadow-indigo-600/20"
        >
          <span>Send</span>
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </button>
      </form>
    </div>
  );
};
