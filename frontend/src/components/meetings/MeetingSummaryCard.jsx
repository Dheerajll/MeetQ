// src/components/meetings/MeetingSummaryCard.jsx

"use client";

import { format, parseISO } from "date-fns";
import { ChevronDown, Users, ExternalLink, ListChecks } from "lucide-react";

export default function MeetingSummaryCard({ meeting, expanded, onToggle }) {
  const { title, link, date, time, participants = [], summary, actionItems = [] } = meeting;

  let formattedDate = date;
  try {
    formattedDate = format(parseISO(date), "MMM d, yyyy");
  } catch {
    // fall back to raw string if parsing fails
  }

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
            <span>
              {formattedDate}
              {time ? ` · ${time}` : ""}
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
          <p className="text-sm text-ink leading-relaxed">{summary}</p>

          {actionItems.length > 0 && (
            <div>
              <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-muted mb-2">
                <ListChecks size={14} />
                Action items
              </p>
              <ul className="space-y-1.5">
                {actionItems.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-ink">
                    <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {participants.length > 0 && (
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-muted mb-2">
                Participants
              </p>
              <div className="flex flex-wrap gap-1.5">
                {participants.map((p, i) => (
                  <span
                    key={i}
                    className="rounded-full bg-bg border border-border px-2.5 py-1 text-xs text-ink"
                  >
                    {p}
                  </span>
                ))}
              </div>
            </div>
          )}

          {link && (
            
              <a href={link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
            >
              Open meeting link
              <ExternalLink size={14} />
            </a>
          )}
        </div>
      )}
    </div>
  );
}