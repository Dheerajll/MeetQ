// src/context/AuthContext.jsx
"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { jwtDecode } from "jwt-decode";
import { useRouter } from "next/navigation";
import api, { setAccessToken as setApiAccessToken } from "@/lib/api";

const AuthContext = createContext(undefined);
const SESSION_KEY = "meetq_session";

function readStoredSession() {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const session = JSON.parse(raw);
    const { exp } = jwtDecode(session.accessToken);
    if (!exp || exp * 1000 <= Date.now()) return null;
    return session;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [accessToken, setAccessTokenState] = useState(null);
  const [hasLmaToken, setHasLmaToken] = useState(false); // <-- NEW STATE
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const applyToken = useCallback((token, explicitUser = null) => {
    setAccessTokenState(token);
    setApiAccessToken(token);
    if (!token) {
      setUser(null);
      localStorage.removeItem(SESSION_KEY);
      return;
    }
    let resolvedUser = explicitUser;
    if (!resolvedUser) {
      try {
        resolvedUser = jwtDecode(token);
      } catch {
        resolvedUser = null;
      }
    }
    setUser(resolvedUser);
    localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({ accessToken: token, user: resolvedUser })
    );
  }, []);

  // Restore the session from localStorage on first load.
  useEffect(() => {
    const session = readStoredSession();
    if (session) {
      applyToken(session.accessToken, session.user);
    }
    setLoading(false);
  }, [applyToken]);

  // Fetch LMA token status whenever the access token changes
  useEffect(() => {
    if (accessToken) {
      api.get("/auth/lma-token/status")
        .then((res) => setHasLmaToken(res.data.has_active_token))
        .catch(() => setHasLmaToken(false));
    } else {
      setHasLmaToken(false);
    }
  }, [accessToken]);

  const logout = useCallback(async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      // ignore backend errors
    }
    applyToken(null);
    router.push("/login");
  }, [applyToken, router]);

  const value = {
    user,
    accessToken,
    hasLmaToken, // <-- EXPOSED TO APP
    isAuthenticated: Boolean(accessToken),
    loading,
    applyToken,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (ctx === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}