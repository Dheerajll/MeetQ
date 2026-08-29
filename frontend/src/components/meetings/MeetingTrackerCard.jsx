"use client";
import { useEffect, useState, useRef } from "react";
import { CheckCircle2, Loader2, Mic, Cpu, AlertCircle, ExternalLink, MessageSquare, Send, RotateCcw } from "lucide-react";
import api from "@/lib/api";

const STATUS_CONFIG = {
  pending:    { label: "Waiting for agent…",    icon: Loader2,     color: "text-muted",   spin: true },
  recording:  { label: "Recording meeting",     icon: Mic,         color: "text-danger",  spin: false },
  processing: { label: "Processing & summarizing", icon: Cpu,     color: "text-primary", spin: true },
  completed:  { label: "Summary ready",         icon: CheckCircle2, color: "text-primary", spin: false },
  failed:     { label: "Processing failed",     icon: AlertCircle, color: "text-danger",  spin: false },
};

export default function MeetingTrackerCard({ meeting, onStatusChange, onReset }) {
  const [current, setCurrent] = useState(meeting);
  
  // Chat State
  const [queryInput, setQueryInput] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [isQueryLoading, setIsQueryLoading] = useState(false);
  const scrollRef = useRef(null);

  // Poll until terminal state
  useEffect(() => {
    const isTerminal = current.status === "completed" || current.status === "failed";
    if (isTerminal) return;

    const poll = setInterval(async () => {
      try {
        const res = await api.get(`/meetings/${current.id}`);
        const updated = res.data;
        setCurrent(updated);
        onStatusChange?.(updated);
      } catch {
        // Retry silently
      }
    }, 3000);

    return () => clearInterval(poll);
  }, [current.id, current.status, onStatusChange]);

  // Auto-scroll chat
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, isQueryLoading]);

  const config = STATUS_CONFIG[current.status] || STATUS_CONFIG.pending;
  const StatusIcon = config.icon;
  const progressSteps = ["pending", "recording", "processing", "completed"];
  const currentStepIndex = progressSteps.indexOf(current.status);

  // Handle Chat Submit
  const handleQuerySubmit = async (e) => {
    e.preventDefault();
    if (!queryInput.trim() || isQueryLoading) return;

    const userMsg = { role: "user", content: queryInput };
    setChatMessages((prev) => [...prev, userMsg]);
    setQueryInput("");
    setIsQueryLoading(true);

    try {
      // Note: We assume the backend RAG endpoint can filter by meeting_id if we pass it, 
      // or we just rely on the global search. 
      // Ideally, pass meeting_id to scope the search.
      const res = await api.post("/rag/query", { 
        query: queryInput, 
        top_k: 5,
        // If your backend supports filtering by meeting_id in the payload, add it here:
        // meeting_id: current.id 
      });
      
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.data.answer }
      ]);
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Failed to get answer. Please try again." }
      ]);
    } finally {
      setIsQueryLoading(false);
    }
  };

  return (
    <div className="bg-surface border border-border rounded-lg shadow-card p-5 flex flex-col h-full max-h-[600px]">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="min-w-0">
          <h3 className="font-display font-semibold text-ink truncate">{current.title}</h3>
          <a href={current.meeting_url} target="_blank" rel="noopener noreferrer" className="mt-1 inline-flex items-center gap-1 text-xs text-primary hover:underline">
            Open meeting link <ExternalLink size={12} />
          </a>
        </div>
        <div className={`flex items-center gap-1.5 text-sm font-medium ${config.color} shrink-0`}>
          <StatusIcon size={16} className={config.spin ? "animate-spin" : ""} />
          <span className="hidden sm:inline">{config.label}</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="flex items-center gap-1 mb-6">
        {progressSteps.map((step, i) => (
          <div key={step} className={`h-1.5 flex-1 rounded-full transition-colors ${i <= currentStepIndex && current.status !== "failed" ? "bg-primary" : "bg-border"}`} />
        ))}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {current.status === "completed" ? (
          <div className="space-y-4">
            {/* Chat Interface */}
            <div className="border-t border-border pt-4">
              <h4 className="text-xs font-medium uppercase tracking-wide text-muted mb-3 flex items-center gap-2">
                <MessageSquare size={14} /> Ask about this meeting
              </h4>
              
              <div className="space-y-3 mb-3 max-h-48 overflow-y-auto pr-1">
                {chatMessages.length === 0 && (
                  <p className="text-xs text-muted italic text-center py-2">
                    Try asking: "What were the key decisions?"
                  </p>
                )}
                {chatMessages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-[85%] rounded-lg px-3 py-2 text-xs leading-relaxed ${msg.role === "user" ? "bg-primary text-white" : "bg-bg text-ink border border-border"}`}>
                      {msg.content}
                    </div>
                  </div>
                ))}
                {isQueryLoading && (
                  <div className="flex justify-start">
                    <div className="bg-bg border border-border rounded-lg px-3 py-2 flex gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce" />
                      <span className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce [animation-delay:150ms]" />
                      <span className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce [animation-delay:300ms]" />
                    </div>
                  </div>
                )}
                <div ref={scrollRef} />
              </div>

              <form onSubmit={handleQuerySubmit} className="flex gap-2">
                <input
                  type="text"
                  value={queryInput}
                  onChange={(e) => setQueryInput(e.target.value)}
                  placeholder="Ask a question..."
                  className="flex-1 rounded-md border border-border bg-bg px-3 py-2 text-xs text-ink focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <button type="submit" disabled={!queryInput.trim() || isQueryLoading} className="rounded-md bg-primary p-2 text-white hover:bg-primary-dark disabled:opacity-50 transition-colors">
                  <Send size={14} />
                </button>
              </form>
            </div>
            
            {/* View Full Summary Link */}
            <div className="pt-2 border-t border-border flex justify-center">
               <a href={`/meetings`} className="text-xs text-primary hover:underline font-medium">
                 View full summary & transcript →
               </a>
            </div>
          </div>
        ) : current.status === "failed" ? (
          <div className="text-center py-8">
            <p className="text-sm text-danger mb-4">Something went wrong. The LMA agent may have disconnected.</p>
            <button onClick={onReset} className="text-xs text-primary hover:underline">Try again</button>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-muted text-sm">
            <p>Agent is working...</p>
            <p className="text-xs mt-2 text-muted/70">Do not close this window.</p>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      {current.status === "completed" && (
        <div className="mt-4 pt-4 border-t border-border">
          <button onClick={onReset} className="w-full flex items-center justify-center gap-2 rounded-md border border-border py-2 text-sm font-medium text-ink hover:bg-bg transition-colors">
            <RotateCcw size={14} /> Start New Meeting
          </button>
        </div>
      )}
    </div>
  );
}