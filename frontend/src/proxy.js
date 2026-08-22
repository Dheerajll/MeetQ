// src/proxy.js

import { NextResponse } from "next/server";

// The access token now lives in localStorage only (no refresh_token cookie),
// which middleware can't read — route protection is handled client-side by
// ProtectedRoute/GuestRoute instead.
export function proxy() {
  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/query/:path*", "/meetings/:path*"],
};