// src/app/(auth)/login/page.jsx

const GOOGLE_LOGIN_URL = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/google`;

export default function LoginPage() {
  return (
    <div className="bg-surface border border-border rounded-lg shadow-card p-8">
      <h2 className="font-display text-2xl font-semibold text-ink">
        Welcome back
      </h2>
      <p className="mt-1 text-sm text-muted">Log in to see what you missed.</p>

      <a
        href={GOOGLE_LOGIN_URL}
        className="mt-6 flex w-full items-center justify-center gap-3 rounded-md border border-border bg-white py-2 text-sm font-medium text-ink hover:bg-zinc-50 transition-colors"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
          <path
            fill="#4285F4"
            d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.71v2.26h2.9c1.7-1.57 2.7-3.87 2.7-6.61z"
          />
          <path
            fill="#34A853"
            d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.9-2.26c-.81.54-1.85.86-3.06.86-2.35 0-4.34-1.59-5.05-3.72H.98v2.33A9 9 0 0 0 9 18z"
          />
          <path
            fill="#FBBC05"
            d="M3.95 10.7A5.4 5.4 0 0 1 3.67 9c0-.59.1-1.17.28-1.7V4.97H.98A9 9 0 0 0 0 9c0 1.45.35 2.83.98 4.03l2.97-2.33z"
          />
          <path
            fill="#EA4335"
            d="M9 3.58c1.32 0 2.51.46 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0A9 9 0 0 0 .98 4.97l2.97 2.33C4.66 5.17 6.65 3.58 9 3.58z"
          />
        </svg>
        Continue with Google
      </a>
    </div>
  );
}