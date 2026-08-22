"use client";

import { useEffect, useMemo, useState } from "react";
import { Search, FileText, Loader2 } from "lucide-react";
import api from "@/lib/api";
import MeetingSummaryCard from "@/components/meetings/MeetingSummaryCard";

export default function MeetingsPage() {
  const [query, setQuery] = useState("");
  const [expandedId, setExpandedId] = useState(null);
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Fetch summaries on mount
  useEffect(() => {
    let cancelled = false;

    async function fetchSummaries() {
      try {
        const res = await api.get("/meetings/summaries");
        if (!cancelled) {
          setMeetings(res.data);
        }
      } catch (err) {
        if (!cancelled) {
          setError("Failed to load meeting summaries.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchSummaries();
    return () => { cancelled = true; };
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return meetings;
    return meetings.filter(
      (m) =>
        m.title.toLowerCase().includes(q) ||
        (m.overview || "").toLowerCase().includes(q)
    );
  }, [query, meetings]);

  const handleToggle = (id) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  if (loading) {
    return (
      <main className="flex-1 px-4 py-10 flex items-center justify-center">
        <Loader2 size={24} className="animate-spin text-muted" />
      </main>
    );
  }

  return (
    <main className="flex-1 px-4 py-10">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="font-display text-3xl font-semibold text-ink">
            Meeting summaries
          </h1>
          <p className="mt-1 text-sm text-muted">
            Everything your agent has caught up on so far.
          </p>
        </div>

        {error && (
          <div className="mb-6 rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-sm text-danger">
            {error}
          </div>
        )}

        <div className="relative mb-6">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search summaries…"
            className="w-full rounded-md border border-border bg-surface pl-9 pr-3 py-2 text-sm text-ink placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {filtered.length === 0 ? (
          <div className="text-center text-muted py-16">
            <FileText size={28} className="mx-auto mb-3 opacity-50" />
            <p className="text-sm">
              {meetings.length === 0
                ? "No summaries yet. Start a meeting from the home page."
                : "No summaries match your search."}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map((meeting) => (
              <MeetingSummaryCard
                key={meeting.id}
                meeting={meeting}
                expanded={expandedId === meeting.id}
                onToggle={() => handleToggle(meeting.id)}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}