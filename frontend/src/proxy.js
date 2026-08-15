// src/proxy.js

import { NextResponse } from "next/server";

const PROTECTED_PATHS = ["/query", "/meetings"];

// Note: guest-only pages (/login, /signup) are NOT redirected here based on
// cookie presence — the cookie's presence doesn't mean it's still valid, and
// bouncing on stale cookies here caused an infinite redirect loop with
// ProtectedRoute (which sends invalid-session users back to /login once the
// client-side refresh call fails). GuestRoute handles that redirect instead,
// using the real, validated auth state.
export function proxy(request) {
  const { pathname } = request.nextUrl;
  const hasRefreshToken = Boolean(request.cookies.get("refresh_token")?.value);

  const isProtected =
    pathname === "/" ||
    PROTECTED_PATHS.some((path) => pathname.startsWith(path));

  if (isProtected && !hasRefreshToken) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/query/:path*", "/meetings/:path*"],
};