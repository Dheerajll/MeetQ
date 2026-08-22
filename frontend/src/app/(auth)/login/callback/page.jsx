// src/app/(auth)/login/callback/page.jsx

"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import axios from "axios";
import { useAuth } from "@/context/AuthContext";

const GOOGLE_CALLBACK_URL = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/google/callback`;

function GoogleCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { applyToken } = useAuth();
  const [error, setError] = useState("");

  useEffect(() => {
    const code = searchParams.get("code");
    if (!code) {
      router.replace("/login");
      return;
    }

    axios
      .get(GOOGLE_CALLBACK_URL, { params: { code } })
      .then((res) => {
        applyToken(res.data.access_token, res.data.user);
        router.replace("/");
      })
      .catch(() => setError("Google sign-in failed. Please try again."));
    // The auth code is single-use — this must only run once per page load.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <p className="text-center text-sm text-muted">
      {error || "Signing you in…"}
    </p>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={null}>
      <GoogleCallback />
    </Suspense>
  );
}
