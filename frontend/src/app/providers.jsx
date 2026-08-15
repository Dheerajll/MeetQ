// src/app/providers.jsx

"use client";

import { AuthProvider } from "@/context/AuthContext";

// layout.js is a Server Component, but Context needs a Client Component —
// this file is that boundary. Add any other app-wide providers here later.
export default function Providers({ children }) {
  return <AuthProvider>{children}</AuthProvider>;
}