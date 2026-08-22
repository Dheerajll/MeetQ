"use client";

import { useState } from "react";
import { Type, Link2, ArrowRight, Plus } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import MeetingTrackerCard from "@/components/meetings/MeetingTrackerCard";

export default function HomePage() {
  const { user } = useAuth();
  const [meetingTitle, setMeetingTitle] = useState("");
  const [meetingLink, setMeetingLink] = useState("");
  const [language, setLanguage] = useState("en");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeMeetings, setActiveMeetings] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await api.post("/meetings", {
        title: meetingTitle,
        meeting_url: meetingLink,
        language,
      });

      // Add to the front of the tracker list
      setActiveMeetings((prev) => [res.data, ...prev]);

      // Reset form
      setMeetingTitle("");
      setMeetingLink("");
      setLanguage("en");
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "string") {
        setError(detail);
      } else {
        setError("Failed to create meeting. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  // Update a meeting in the active list when its status changes
  const handleStatusChange = (updatedMeeting) => {
    setActiveMeetings((prev) =>
      prev.map((m) => (m.id === updatedMeeting.id ? updatedMeeting : m))
    );
  };

  return (
    <main className="flex-1 flex flex-col items-center px-4 py-12 overflow-y-auto">
      <div className="w-full max-w-lg">
        {/* Project name + quote */}
        <div className="text-center mb-10">
          {user?.name && (
            <p className="text-sm text-muted mb-2">Hi {user.name}</p>
          )}
          <h1 className="font-display text-4xl font-semibold text-ink">
            Meet Q
          </h1>
          <p className="mt-3 text-muted italic">
            &ldquo;The faintest note beats the sharpest memory.&rdquo;
          </p>
        </div>

        {/* Meeting form */}
        <form
          onSubmit={handleSubmit}
          className="bg-surface border border-border rounded-lg shadow-card p-6 sm:p-8 space-y-5"
        >
          <div>
            <label htmlFor="meetingTitle" className="block text-sm font-medium text-ink mb-1">
              Meeting title
            </label>
            <div className="relative">
              <Type size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
              <input
                id="meetingTitle"
                type="text"
                required
                value={meetingTitle}
                onChange={(e) => setMeetingTitle(e.target.value)}
                placeholder="Q3 Planning, Standup, Design Review…"
                className="w-full rounded-md border border-border pl-9 pr-3 py-2 text-sm text-ink placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          <div>
            <label htmlFor="meetingLink" className="block text-sm font-medium text-ink mb-1">
              Meeting link
            </label>
            <div className="relative">
              <Link2 size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
              <input
                id="meetingLink"
                type="url"
                required
                value={meetingLink}
                onChange={(e) => setMeetingLink(e.target.value)}
                placeholder="https://meet.google.com/abc-defg-hij"
                className="w-full rounded-md border border-border pl-9 pr-3 py-2 text-sm text-ink placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          <div>
            <label htmlFor="language" className="block text-sm font-medium text-ink mb-1">
              Language
            </label>
            <select
              id="language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full rounded-md border border-border px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary bg-white"
            >
              <option value="en">English</option>
              <option value="ne">Nepali / Mixed</option>
            </select>
          </div>

          {error && (
            <div className="rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-sm text-danger">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 rounded-md bg-primary py-2.5 text-sm font-medium text-white hover:bg-primary-dark transition-colors disabled:opacity-60"
          >
            {loading ? "Starting…" : (
              <>
                <Plus size={16} />
                Start meeting agent
              </>
            )}
          </button>
        </form>

        {/* Active meeting trackers */}
        {activeMeetings.length > 0 && (
          <div className="mt-8 space-y-3">
            <h2 className="font-display text-lg font-semibold text-ink">
              Active meetings
            </h2>
            {activeMeetings.map((m) => (
              <MeetingTrackerCard
                key={m.id}
                meeting={m}
                onStatusChange={handleStatusChange}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}