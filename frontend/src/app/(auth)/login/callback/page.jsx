// src/app/(auth)/login/callback/page.jsx
"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

function GoogleCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { applyToken } = useAuth();
  const [error, setError] = useState("");

  useEffect(() => {
    // Read the token from URL params (backend redirects here with ?token=JWT)
    const token = searchParams.get("token");
    
    if (!token) {
      setError("No token received from Google. Please try again.");
      // Give user a moment to see the error before redirecting
      setTimeout(() => router.replace("/login"), 2000);
      return;
    }

    // Apply the token (stores in memory + localStorage + sets user)
    applyToken(token);
    
    // Redirect to dashboard
    router.replace("/");
  }, [searchParams, applyToken, router]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg">
        <p className="text-center text-sm text-danger">{error}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg">
      <div className="flex items-center gap-2 text-sm text-muted">
        <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
        Signing you in…
      </div>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={null}>
      <GoogleCallback />
    </Suspense>
  );
}