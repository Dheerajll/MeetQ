// src/app/(dashboard)/page.jsx

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {Type, Link2, Calendar, Clock, ArrowRight } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    // TODO: send { meetingLink, date, time } to the backend to register/queue the meeting
    const params = new URLSearchParams({
      title: meetingTitle,
      link: meetingLink,
      date,
      time,
    });
    router.push(`/query?${params.toString()}`);
  };

 return (
    <main className="flex-1 flex flex-col items-center justify-center px-4 py-12">
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

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 rounded-md bg-primary py-2.5 text-sm font-medium text-white hover:bg-primary-dark transition-colors disabled:opacity-60"
          >
            {loading ? "Submitting" : "Submit Link"}
            {!loading && <ArrowRight size={16} />}
          </button>
        </form>
      </div>
    </main>
  );
}