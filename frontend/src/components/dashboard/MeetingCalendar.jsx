"use client";

import { useState, useMemo } from "react";
import {
  format,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  isSameMonth,
  isSameDay,
  addMonths,
  subMonths,
  parseISO,
} from "date-fns";
import { ChevronLeft, ChevronRight, Clock, CheckCircle2 } from "lucide-react";
import Link from "next/link";

export default function MeetingCalendar({ meetings = [] }) {
  const [viewDate, setViewDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date());

  // Generate calendar days
  const calendarDays = useMemo(() => {
    const monthStart = startOfMonth(viewDate);
    const monthEnd = endOfMonth(monthStart);
    const startDate = startOfWeek(monthStart);
    const endDate = endOfWeek(monthEnd);

    return eachDayOfInterval({ start: startDate, end: endDate });
8
  }, [viewDate]);

  // Group meetings by date string (YYYY-MM-DD) for quick lookup
  const meetingsByDate = useMemo(() => {
    const grouped = {};
    meetings.forEach((m) => {
      const dateStr = format(parseISO(m.created_at), "yyyy-MM-dd");
      if (!grouped[dateStr]) grouped[dateStr] = [];
      grouped[dateStr].push(m);
    });
    return grouped;
  }, [meetings]);

  // Get density (number of dots) for a specific day
  const getDensity = (day) => {
    const dateStr = format(day, "yyyy-MM-dd");
    const count = meetingsByDate[dateStr]?.length || 0;
    if (count === 0) return 0;
    if (count === 1) return 1;
    if (count === 2) return 2;
    return 3; // 3+ meetings
  };

  const selectedDateStr = format(selectedDate, "yyyy-MM-dd");
  const daysMeetings = meetingsByDate[selectedDateStr] || [];

  const prevMonth = () => setViewDate(subMonths(viewDate, 1));
  const nextMonth = () => setViewDate(addMonths(viewDate, 1));

  return (
    <div className="bg-surface border border-border rounded-lg shadow-card overflow-hidden">
      {/* Calendar Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-border">
        <h2 className="font-display text-lg font-semibold text-ink">
          Meeting Activity
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={prevMonth}
            className="p-1.5 rounded-md hover:bg-bg text-muted hover:text-ink transition-colors"
          >
            <ChevronLeft size={18} />
          </button>
          <span className="text-sm font-medium text-ink min-w-[120px] text-center">
            {format(viewDate, "MMMM yyyy")}
          </span>
          <button
            onClick={nextMonth}
            className="p-1.5 rounded-md hover:bg-bg text-muted hover:text-ink transition-colors"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row">
        {/* Calendar Grid */}
        <div className="flex-1 p-6">
          {/* Days of Week */}
          <div className="grid grid-cols-7 mb-2">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
              <div
                key={day}
                className="text-center text-xs font-medium text-muted uppercase tracking-wide"
              >
                {day}
              </div>
            ))}
          </div>

          {/* Days */}
          <div className="grid grid-cols-7 gap-1">
            {calendarDays.map((day, dayIdx) => {
              const density = getDensity(day);
              const isSelected = isSameDay(day, selectedDate);
              const isCurrentMonth = isSameMonth(day, viewDate);

              return (
                <button
                  key={day.toString()}
                  onClick={() => setSelectedDate(day)}
                  className={`
                    relative flex flex-col items-center justify-start py-2 rounded-md text-sm transition-all
                    ${!isCurrentMonth ? "text-muted/40" : "text-ink"}
                    ${isSelected ? "bg-primary/10 text-primary font-semibold" : "hover:bg-bg"}
                  `}
                >
                  <span>{format(day, "d")}</span>
                  
                  {/* Density Dots */}
                  {density > 0 && (
                    <div className="flex gap-0.5 mt-1.5">
                      {[...Array(Math.min(density, 3))].map((_, i) => (
                        <span
                          key={i}
                          className={`h-1.5 w-1.5 rounded-full ${
                            isSelected ? "bg-primary" : "bg-primary/60"
                          }`}
                        />
                      ))}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Day Details Panel */}
        <div className="w-full lg:w-80 border-t lg:border-t-0 lg:border-l border-border bg-bg/30 p-6">
          <div className="mb-4">
            <p className="text-xs font-medium uppercase tracking-wide text-muted">
              Selected
            </p>
            <p className="font-display text-xl font-semibold text-ink mt-1">
              {format(selectedDate, "EEEE, MMMM d")}
            </p>
            <p className="text-sm text-muted mt-1">
              {daysMeetings.length} meeting{daysMeetings.length !== 1 ? "s" : ""}
            </p>
          </div>

          <div className="space-y-3">
            {daysMeetings.length === 0 ? (
              <p className="text-sm text-muted italic py-4">
                No meetings on this day.
              </p>
            ) : (
              daysMeetings.map((meeting) => (
                <div
                  key={meeting.id}
                  className="bg-surface border border-border rounded-md p-3 hover:border-primary/30 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="font-medium text-ink text-sm truncate">
                      {meeting.title}
                    </h4>
                    {meeting.status === "completed" && (
                      <CheckCircle2 size={14} className="text-primary shrink-0 mt-0.5" />
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 mt-2 text-xs text-muted">
                    <Clock size={12} />
                    <span>
                      {format(parseISO(meeting.created_at), "h:mm a")}
                    </span>
                  </div>
                  <Link
                    href="/meetings"
                    className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                  >
                    View details →
                  </Link>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}