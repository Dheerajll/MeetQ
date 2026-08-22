// src/app/(dashboard)/dashboard/page.jsx

"use client";

import { useState, useRef, useEffect } from "react";
import { Send, FileText, ChevronDown } from "lucide-react";
import api from "@/lib/api";

function SourceList({ sources }) {
  const [open, setOpen] = useState(false);
  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1 text-xs font-medium text-muted hover:text-ink transition-colors"
      >
        <FileText size={12} />
        {sources.length} source{sources.length > 1 ? "s" : ""}
        <ChevronDown
          size={12}
          className={`transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div className="mt-2 space-y-2">
          {sources.map((source, i) => (
            <div
              key={i}
              className="rounded-md border border-border bg-bg px-3 py-2 text-xs text-muted"
            >
              <p className="text-ink leading-relaxed">{source.text}</p>
              <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-muted">
                {Object.entries(source.metadata || {}).map(([key, value]) => (
                  <span key={key}>
                    {key}: {String(value)}
                  </span>
                ))}
                {typeof source.score === "number" && (
                  <span>score: {source.score.toFixed(2)}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async () => {
    const query = input.trim();
    if (!query || loading) return;

    const userMessage = { role: "user", content: query };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.post("rag/query", { query, top_k: 5 });
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: res.data.answer,
          sources: res.data.sources,
        },
      ]);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            detail || "Something went wrong reaching the meeting agent. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full min-h-screen md:min-h-0 bg-bg">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-4 md:px-0">
        <div className="max-w-2xl mx-auto py-8 space-y-4">
          {messages.length === 0 && !loading && (
            <div className="text-center text-muted mt-24">
              <p className="font-display text-xl text-ink mb-2">Ask your meeting agent</p>
              <p className="text-sm">
                &ldquo;What did we decide about the Project Budget?&rdquo; or &ldquo;Summarize yesterday&apos;s standup.&rdquo;
              </p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-primary text-white"
                    : "bg-surface border border-border text-ink"
                }`}
              >
                {msg.content}
                {msg.role === "assistant" && <SourceList sources={msg.sources} />}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-surface border border-border rounded-lg px-4 py-3 flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          )}

          <div ref={scrollRef} />
        </div>
      </div>

      {/* Input box */}
      <div className="border-t border-border bg-surface px-4 md:px-0">
        <div className="max-w-2xl mx-auto py-4">
          <div className="flex items-end gap-2 border border-border rounded-lg px-3 py-2 focus-within:ring-2 focus-within:ring-primary">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              placeholder="Ask about a meeting..."
              className="flex-1 resize-none bg-transparent text-sm text-ink placeholder:text-muted focus:outline-none max-h-40"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="shrink-0 rounded-md bg-primary p-2 text-white hover:bg-primary-dark transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              aria-label="Send message"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}