// frontend/src/lib/meetingStore.js
import { create } from 'zustand';

export const useMeetingStore = create((set, get) => ({
  activeMeeting: null, // Holds the meeting object if one is running
  
  // Actions
  setActiveMeeting: (meeting) => set({ activeMeeting: meeting }),
  clearActiveMeeting: () => set({ activeMeeting: null }),
  
  // Helper to check if a meeting is currently active (not completed/failed)
  isMeetingActive: () => {
    const { activeMeeting } = get();
    if (!activeMeeting) return false;
    return !['completed', 'failed'].includes(activeMeeting.status);
  },
  
  // Update status locally (optimistic update)
  updateStatus: (status) => set((state) => ({
    activeMeeting: state.activeMeeting ? { ...state.activeMeeting, status } : null
  }))
}));