// src/components/auth/ProtectedRoute.jsx

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

// Wrap any authenticated-only page/layout with this. While AuthContext is
// still checking the refresh token it shows a loading state; once resolved,
// unauthenticated users are bounced to /login.
export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [loading, isAuthenticated, router]);

  if (loading || !isAuthenticated) {
    return (
      <div className="flex-1 min-h-screen flex items-center justify-center bg-bg">
        <div className="flex items-center gap-2 text-sm text-muted">
          <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
          Checking your session...
        </div>
      </div>
    );
  }

  return children;
}