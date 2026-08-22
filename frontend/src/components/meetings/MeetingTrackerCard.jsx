"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Loader2, Mic, Cpu, AlertCircle, ExternalLink, MessageSquare } from "lucide-react";
import api from "@/lib/api";

const STATUS_CONFIG = {
  pending:    { label: "Waiting for agent…",    icon: Loader2,     color: "text-muted",   spin: true },
  recording:  { label: "Recording meeting",     icon: Mic,         color: "text-danger",  spin: false },
  processing: { label: "Processing & summarizing", icon: Cpu,     color: "text-primary", spin: true },
  completed:  { label: "Summary ready",         icon: CheckCircle2, color: "text-primary", spin: false },
  failed:     { label: "Processing failed",     icon: AlertCircle, color: "text-danger",  spin: false },
};

export default function MeetingTrackerCard({ meeting, onStatusChange }) {
  const [current, setCurrent] = useState(meeting);

  // Poll until the meeting reaches a terminal state
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
        // Silently retry on network error
      }
    }, 3000);

    return () => clearInterval(poll);
  }, [current.id, current.status, onStatusChange]);

  const config = STATUS_CONFIG[current.status] || STATUS_CONFIG.pending;
  const StatusIcon = config.icon;

  const progressSteps = ["pending", "recording", "processing", "completed"];
  const currentStepIndex = progressSteps.indexOf(current.status);

  return (
    <div className="bg-surface border border-border rounded-lg shadow-card p-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-display font-semibold text-ink truncate">{current.title}</h3>
          <a
            href={current.meeting_url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-1 inline-flex items-center gap-1 text-xs text-primary hover:underline"
          >
            Open meeting link <ExternalLink size={12} />
          </a>
        </div>
        <div className={`flex items-center gap-1.5 text-sm font-medium ${config.color} shrink-0`}>
          <StatusIcon size={16} className={config.spin ? "animate-spin" : ""} />
          <span className="hidden sm:inline">{config.label}</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mt-4 flex items-center gap-1">
        {progressSteps.map((step, i) => (
          <div
            key={step}
            className={`h-1.5 flex-1 rounded-full transition-colors ${
              i <= currentStepIndex && current.status !== "failed"
                ? "bg-primary"
                : "bg-border"
            }`}
          />
        ))}
      </div>

      {/* Terminal state actions */}
      {current.status === "completed" && (
        <div className="mt-4 flex items-center gap-2">
          <a
            href={`/meetings`}
            className="flex-1 flex items-center justify-center gap-1.5 rounded-md bg-primary py-2 text-sm font-medium text-white hover:bg-primary-dark transition-colors"
          >
            View summary
          </a>
          <a
            href={`/query`}
            className="flex-1 flex items-center justify-center gap-1.5 rounded-md border border-border py-2 text-sm font-medium text-ink hover:bg-bg transition-colors"
          >
            <MessageSquare size={14} /> Ask questions
          </a>
        </div>
      )}

      {current.status === "failed" && (
        <p className="mt-4 text-sm text-danger">
          Something went wrong. The LMA agent may have disconnected or encountered an error.
        </p>
      )}
    </div>
  );
}