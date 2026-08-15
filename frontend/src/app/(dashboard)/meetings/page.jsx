// src/app/(dashboard)/meetings/page.jsx

"use client";

import { useMemo, useState } from "react";
import { Search, FileText } from "lucide-react";
import MeetingSummaryCard from "@/components/meetings/MeetingSummaryCard";

// TODO: replace with a real fetch, e.g.
// const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/meetings/summaries`);
// const MOCK_MEETINGS = await res.json();
const MOCK_MEETINGS = [
  {
    id: "m1",
    title: "Q3 Roadmap Planning",
    link: "https://meet.google.com/abc-defg-hij",
    date: "2026-07-14",
    time: "10:00",
    summary:
      "The team aligned on three priorities for Q3: shipping the meeting-agent MVP, improving onboarding conversion, and starting discovery for the mobile app. Chris raised concerns about backend capacity and the team agreed to revisit staffing after the August review.",
    actionItems: [
      "Alice to draft the Q3 roadmap doc by Friday",
      "Bob to scope the onboarding experiment",
      "Chris to estimate backend headcount needs",
    ],
  },
  {
    id: "m2",
    title: "Weekly Standup",
    link: "https://meet.google.com/xyz-uvwx-rst",
    date: "2026-07-16",
    time: "09:30",
    summary:
      "Dana finished the login and signup flows and is starting on the dashboard chat UI. Alice is blocked on the summarization API contract and will sync with the backend team today.",
    actionItems: ["Alice to confirm the summarization API contract"],
  },
  {
    id: "m3",
    title: "Customer Feedback Review",
    link: "https://meet.google.com/lmn-opqr-stu",
    date: "2026-07-11",
    time: "14:00",
    summary:
      "Reviewed feedback from the last five customer calls. Common theme: users want automatic meeting-link detection from calendar invites rather than pasting links manually. Elena will explore a calendar integration as a follow-up feature.",
    actionItems: [
      "Elena to research calendar integration options",
      "Bob to prioritize this in the next planning cycle",
    ],
  },
];

export default function MeetingsPage() {
  const [query, setQuery] = useState("");
  const [expandedId, setExpandedId] = useState(null);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return MOCK_MEETINGS;
    return MOCK_MEETINGS.filter(
      (m) =>
        m.title.toLowerCase().includes(q) ||
        m.summary.toLowerCase().includes(q)
    );
  }, [query]);

  const handleToggle = (id) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

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

        <div className="relative mb-6">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-muted"
          />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search summaries..."
            className="w-full rounded-md border border-border bg-surface pl-9 pr-3 py-2 text-sm text-ink placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {filtered.length === 0 ? (
          <div className="text-center text-muted py-16">
            <FileText size={28} className="mx-auto mb-3 opacity-50" />
            <p className="text-sm">No summaries match your search.</p>
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