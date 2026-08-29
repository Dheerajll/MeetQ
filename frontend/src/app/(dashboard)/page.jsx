"use client";
import { useState, useEffect } from "react";
import { Type, Link2, ArrowRight, AlertCircle, Loader2, Languages } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import MeetingCalendar from "@/components/dashboard/MeetingCalendar";
import MeetingTrackerCard from "@/components/meetings/MeetingTrackerCard";
import { useMeetingStore } from "@/lib/meetingStore"; // Import the global store

export default function HomePage() {
  const { user } = useAuth();
  
  // Global State for Active Meeting
  const { activeMeeting, setActiveMeeting, clearActiveMeeting, isMeetingActive } = useMeetingStore();

  // Form state
  const [meetingTitle, setMeetingTitle] = useState("");
  const [meetingLink, setMeetingLink] = useState("");
  const [language, setLanguage] = useState("en"); // Default to English
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  // Calendar state
  const [allMeetings, setAllMeetings] = useState([]);

  // Fetch meetings for calendar on mount
  useEffect(() => {
    const fetchMeetings = async () => {
      try {
        const res = await api.get("/meetings");
        setAllMeetings(res.data);
      } catch (err) {
        console.error("Failed to fetch meetings for calendar", err);
      }
    };
    fetchMeetings();
  }, []);

  // Rehydrate active meeting if page was refreshed
  useEffect(() => {
    const checkActiveMeeting = async () => {
      if (!activeMeeting) {
        try {
          const res = await api.get("/meetings");
          // Find any meeting that is not completed or failed
          const active = res.data.find(m => 
            m.status === 'recording' || 
            m.status === 'processing' || 
            m.status === 'pending'
          );
          if (active) {
            setActiveMeeting(active);
          }
        } catch (e) {
          console.error("Error checking active meeting", e);
        }
      }
    };
    checkActiveMeeting();
  }, [activeMeeting, setActiveMeeting]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    // Prevent submission if a meeting is already running
    if (isMeetingActive()) {
      setError("A meeting is already in progress. Please wait for it to finish.");
      setLoading(false);
      return;
    }

    try {
      // 1. Check LMA Token
      const tokenCheck = await api.get("/auth/lma-token/status");
      if (!tokenCheck.data.has_active_token) {
        setError("You need to generate an LMA token first. Go to 'Get LMA Token' on the Left Sidebar.");
        setLoading(false);
        return;
      }

      // 2. Create Meeting via API
      const payload = {
        title: meetingTitle,
        meeting_url: meetingLink,
        language: language,
        notes: "", // Notes field kept for backend compatibility
      };

      const response = await api.post("/meetings", payload);
      
      // 3. Set Active Meeting in Global Store (Shows Tracker Card)
      setActiveMeeting(response.data);
      
      // 4. Refresh calendar list
      const updatedList = await api.get("/meetings");
      setAllMeetings(updatedList.data);

    } catch (err) {
      console.error("Meeting creation failed:", err);
      const detail = err.response?.data?.detail || "Failed to create meeting. Is the LMA daemon running?";
      setError(detail);
      setLoading(false);
    }
  };

  const handleReset = () => {
    clearActiveMeeting();
    setMeetingTitle("");
    setMeetingLink("");
    setLanguage("en");
    setLoading(false);
  };

  const meetingInProgress = isMeetingActive();

  return (
    <main className="flex-1 flex flex-col items-center px-4 py-8 md:py-12 overflow-y-auto">
      <div className="w-full max-w-5xl mx-auto space-y-10">
        
        {/* ─── SECTION 1: Conditional Rendering (Form OR Tracker) ─── */}
        <div className="w-full max-w-lg mx-auto">
          {!activeMeeting ? (
            // --- SHOW FORM ---
            <>
              <div className="text-center mb-8">
                <h1 className="font-display text-4xl font-semibold text-ink">Meet Q</h1>
                {user?.name && <p className="text-sm text-muted mt-2">Hi {user.name}</p>}
              </div>

              {meetingInProgress && (
                 <div className="mb-4 p-3 bg-accent/10 border border-accent/20 rounded-md flex items-center gap-2 text-sm text-accent">
                    <Loader2 size={16} className="animate-spin" />
                    <span>A meeting is currently in progress.</span>
                 </div>
              )}

              <form onSubmit={handleSubmit} className="bg-surface border border-border rounded-lg shadow-card p-6 sm:p-8 space-y-5">
                
                {/* Title Input */}
                <div>
                  <label htmlFor="meetingTitle" className="block text-sm font-medium text-ink mb-1">Meeting title</label>
                  <div className="relative">
                    <Type size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                    <input 
                      id="meetingTitle" 
                      type="text" 
                      required 
                      disabled={meetingInProgress}
                      value={meetingTitle} 
                      onChange={(e) => setMeetingTitle(e.target.value)} 
                      placeholder="Your Meeting Title" 
                      className="w-full rounded-md border border-border pl-9 pr-3 py-2 text-sm text-ink placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-bg disabled:cursor-not-allowed" 
                    />
                  </div>
                </div>

                {/* Link Input */}
                <div>
                  <label htmlFor="meetingLink" className="block text-sm font-medium text-ink mb-1">Meeting link</label>
                  <div className="relative">
                    <Link2 size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                    <input 
                      id="meetingLink" 
                      type="url" 
                      required 
                      disabled={meetingInProgress}
                      value={meetingLink} 
                      onChange={(e) => setMeetingLink(e.target.value)} 
                      placeholder="https://meet.google.com/abc-defg-hij" 
                      className="w-full rounded-md border border-border pl-9 pr-3 py-2 text-sm text-ink placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-bg disabled:cursor-not-allowed" 
                    />
                  </div>
                </div>

                {/* Language Selection (Replaces Date/Time) */}
                <div>
                  <label htmlFor="language" className="block text-sm font-medium text-ink mb-1">Language</label>
                  <div className="relative">
                    <Languages size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
                    <select
                      id="language"
                      value={language}
                      onChange={(e) => setLanguage(e.target.value)}
                      disabled={meetingInProgress}
                      className="w-full rounded-md border border-border pl-9 pr-3 py-2 text-sm text-ink bg-surface focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-bg disabled:cursor-not-allowed appearance-none"
                    >
                      <option value="en">English</option>
                      <option value="ne">Nepali (Code-Switched)</option>
                    </select>
                    {/* Custom dropdown arrow */}
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-muted">
                      <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                    </div>
                  </div>
                </div>

                {error && (
                  <div className="flex items-start gap-2 p-3 bg-danger/10 border border-danger/20 rounded-md">
                    <AlertCircle size={16} className="text-danger mt-0.5 shrink-0" />
                    <p className="text-sm text-danger">{error}</p>
                  </div>
                )}

                <button 
                  type="submit" 
                  disabled={loading || meetingInProgress} 
                  className="w-full flex items-center justify-center gap-2 rounded-md bg-primary py-2.5 text-sm font-medium text-white hover:bg-primary-dark transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {loading ? "Starting Agent..." : meetingInProgress ? "Meeting in Progress" : "Submit Link"}
                  {!loading && !meetingInProgress && <ArrowRight size={16} />}
                </button>
              </form>
            </>
          ) : (
            // --- SHOW TRACKER CARD ---
            <MeetingTrackerCard 
              meeting={activeMeeting} 
              onStatusChange={(updatedMeeting) => setActiveMeeting(updatedMeeting)}
              onReset={handleReset}
            />
          )}
        </div>

        {/* ─── SECTION 2: Meeting Activity Calendar ─── */}
        <div className="w-full">
          <MeetingCalendar meetings={allMeetings} />
        </div>
      </div>
    </main>
  );
}