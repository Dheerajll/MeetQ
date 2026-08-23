"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Type, Link2, Calendar, Clock, ArrowRight, AlertCircle } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";

function todayISO() {
  const d = new Date();
  const offset = d.getTimezoneOffset();
  const local = new Date(d.getTime() - offset * 60 * 1000);
  return local.toISOString().slice(0, 10);
}

function nowHHMM() {
  const d = new Date();
  return d.toTimeString().slice(0, 5);
}

export default function HomePage() {
  const router = useRouter();
  const { user } = useAuth();
  const [meetingTitle, setMeetingTitle] = useState("");
  const [meetingLink, setMeetingLink] = useState("");
  const [date, setDate] = useState(todayISO());
  const [time, setTime] = useState(nowHHMM());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // First, check if user has an active LMA token
      const tokenCheck = await api.get("/auth/lma-token/status");
      
      if (!tokenCheck.data.has_active_token) {
        setError("You need to generate an LMA token first. Go to Get LMA Token on Left Sidebar.");
        setLoading(false);
        return;
      }

      // Token exists, proceed with meeting creation
      const params = new URLSearchParams({
        title: meetingTitle,
        link: meetingLink,
        date,
        time,
      });
      router.push(`/query?${params.toString()}`);
    } catch (err) {
      setError("Failed to check LMA token status. Please try again.");
      setLoading(false);
    }
  };

  return (
    <main className="flex-1 flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg">
        {/* Project name + quote */}
        <div className="text-center mb-10">
          <h1 className="font-display text-4xl font-semibold text-ink">
            Meet Q
          </h1>
          {user?.name && (
            <p className="text-sm text-muted mb-2">Hi {user.name}</p>
          )}
        </div>

        {/* Meeting form */}
        <form
          onSubmit={handleSubmit}
          className="bg-surface border border-border rounded-lg shadow-card p-6 sm:p-8 space-y-5"
        >
          <div>
            <label
              htmlFor="meetingTitle"
              className="block text-sm font-medium text-ink mb-1"
            >
              Meeting title
            </label>
            <div className="relative">
              <Type
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-muted"
              />
              <input
                id="meetingTitle"
                type="text"
                required
                value={meetingTitle}
                onChange={(e) => setMeetingTitle(e.target.value)}
                placeholder="Your Meeting Title"
                className="w-full rounded-md border border-border pl-9 pr-3 py-2 text-sm text-ink placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="meetingLink"
              className="block text-sm font-medium text-ink mb-1"
            >
              Meeting link
            </label>
            <div className="relative">
              <Link2
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-muted"
              />
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

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="date"
                className="block text-sm font-medium text-ink mb-1"
              >
                Date
              </label>
              <div className="relative">
                <Calendar
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none"
                />
                <input
                  id="date"
                  type="date"
                  required
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full rounded-md border border-border pl-9 pr-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>
            <div>
              <label
                htmlFor="time"
                className="block text-sm font-medium text-ink mb-1"
              >
                Time
              </label>
              <div className="relative">
                <Clock
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none"
                />
                <input
                  id="time"
                  type="time"
                  required
                  value={time}
                  onChange={(e) => setTime(e.target.value)}
                  className="w-full rounded-md border border-border pl-9 pr-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>
          </div>

          {/* Error message */}
          {error && (
            <div className="flex items-start gap-2 p-3 bg-danger/10 border border-danger/20 rounded-md">
              <AlertCircle size={16} className="text-danger mt-0.5 shrink-0" />
              <p className="text-sm text-danger">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 rounded-md bg-primary py-2.5 text-sm font-medium text-white hover:bg-primary-dark transition-colors disabled:opacity-60"
          >
            {loading ? "Checking..." : "Submit Link"}
            {!loading && <ArrowRight size={16} />}
          </button>
        </form>
      </div>
    </main>
  );
}