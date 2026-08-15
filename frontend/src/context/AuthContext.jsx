// src/context/AuthContext.jsx

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import Cookies from "js-cookie";
import { jwtDecode } from "jwt-decode";
import { useRouter } from "next/navigation";
import api, { setAccessToken as setApiAccessToken } from "@/lib/api";

const AuthContext = createContext(undefined);

const COOKIE_NAME = "refresh_token";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [accessToken, setAccessTokenState] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const refreshAttempted = useRef(false);

  const applyToken = useCallback((token, explicitUser = null) => {
    setAccessTokenState(token);
    setApiAccessToken(token);

    if (!token) {
      setUser(null);
      return;
    }
    if (explicitUser) {
      setUser(explicitUser);
      return;
    }

    try {
      setUser(jwtDecode(token));
    } catch {
      setUser(null);
    }
  }, []);

  // Attempt refresh once on mount only — useRef guard prevents re-running
  // if applyToken reference ever changes, and prevents double-fire in
  // React Strict Mode which mounts components twice in development.
  useEffect(() => {
    if (refreshAttempted.current) return;
    refreshAttempted.current = true;

    api
      .post("/auth/refresh")
      .then((res) => applyToken(res.data.access_token, res.data.user))
      .catch(() => applyToken(null))
      .finally(() => setLoading(false));
  }, [applyToken]);

  const login = useCallback(
    async (email, password) => {
      const res = await api.post("/auth/login", { email, password });
      applyToken(res.data.access_token, res.data.user);
      return res.data;
    },
    [applyToken]
  );

  const signup = useCallback(
    async ({ name, email, password }) => {
      const res = await api.post("/auth/register", { name, email, password });
      // backend returns user only, no token — redirect to login
      router.push("/login");
      return res.data;
    },
    [router]
  );

  const logout = useCallback(async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      // ignore backend errors — log out locally regardless
    }
    Cookies.remove(COOKIE_NAME);
    applyToken(null);
    router.push("/login");
  }, [applyToken, router]);

  const value = {
    user,
    accessToken,
    isAuthenticated: Boolean(accessToken),
    loading,
    login,
    signup,
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