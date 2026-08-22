"use client";

import { format, parseISO } from "date-fns";
import { ChevronDown, ExternalLink, ListChecks } from "lucide-react";

export default function MeetingSummaryCard({ meeting, expanded, onToggle }) {
  const {
    title,
    meeting_url,
    created_at,
    status,
    overview,
    action_items = [],
    key_topics = [],
    decisions = [],
  } = meeting;

  let formattedDate = "";
  try {
    formattedDate = format(parseISO(created_at), "MMM d, yyyy · h:mm a");
  } catch {
    formattedDate = created_at;
  }

  // Skip meetings that haven't been processed yet
  const isProcessed = status === "completed" && overview;

  return (
    <div className="bg-surface border border-border rounded-lg shadow-card overflow-hidden">
      <button
        onClick={onToggle}
        aria-expanded={expanded}
        className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left hover:bg-bg/60 transition-colors"
      >
        <div className="min-w-0">
          <p className="font-display font-semibold text-ink truncate">{title}</p>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
            <span>{formattedDate}</span>
            <span className={`px-1.5 py-0.5 rounded text-[10px] uppercase tracking-wide ${
              status === "completed"
                ? "bg-primary/10 text-primary"
                : "bg-border text-muted"
            }`}>
              {status}
            </span>
          </div>
        </div>
        <ChevronDown
          size={18}
          className={`shrink-0 text-muted transition-transform duration-200 ${
            expanded ? "rotate-180" : ""
          }`}
        />
      </button>

      {expanded && (
        <div className="px-5 pb-5 pt-1 border-t border-border space-y-4">
          {!isProcessed ? (
            <p className="text-sm text-muted italic">
              This meeting has not been processed yet.
            </p>
          ) : (
            <>
              <p className="text-sm text-ink leading-relaxed">{overview}</p>

              {key_topics.length > 0 && (
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-muted mb-2">
                    Key topics
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {key_topics.map((t, i) => (
                      <span
                        key={i}
                        className="rounded-full bg-bg border border-border px-2.5 py-1 text-xs text-ink"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {decisions.length > 0 && (
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-muted mb-2">
                    Decisions
                  </p>
                  <ul className="space-y-1.5">
                    {decisions.map((d, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-ink">
                        <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-accent shrink-0" />
                        {d}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {action_items.length > 0 && (
                <div>
                  <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-muted mb-2">
                    <ListChecks size={14} />
                    Action items
                  </p>
                  <ul className="space-y-1.5">
                    {action_items.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-ink">
                        <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}