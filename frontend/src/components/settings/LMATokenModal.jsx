"use client";

import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { X, Copy, Check, Key } from "lucide-react";
import api from "@/lib/api";

export default function LMATokenModal({ isOpen, onClose }) {
  const [token, setToken] = useState(null);
  const [deviceName, setDeviceName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Ensure we're on the client side before using createPortal
  useEffect(() => {
    setMounted(true);
  }, []);

  // Lock body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return;
    const handleEsc = (e) => {
      if (e.key === "Escape") handleClose();
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [isOpen]);

  const handleGenerate = async () => {
    setError("");
    setLoading(true);

    try {
      const res = await api.post("/auth/lma-token", {
        device_name: deviceName.trim() || null,
      });
      setToken(res.data.token);
      setCopied(false);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to generate token.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!token) return;
    try {
      await navigator.clipboard.writeText(token);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = token;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleClose = () => {
    setToken(null);
    setDeviceName("");
    setError("");
    setCopied(false);
    onClose();
  };

  // Don't render anything on server or when closed
  if (!mounted || !isOpen) return null;

  // Use createPortal to render directly into document.body
  // This escapes any parent stacking context (sidebar, etc.)
  const modal = (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center"
      role="dialog"
      aria-modal="true"
    >
      {/* Backdrop — blocks ALL interaction behind the modal */}
      <div
        className="absolute inset-0 bg-ink/50 backdrop-blur-sm"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Modal content */}
      <div className="relative z-10 bg-surface border border-border rounded-lg shadow-card w-full max-w-md mx-4 p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Key size={18} className="text-primary" />
            <h3 className="font-display font-semibold text-ink">
              LMA Device Token
            </h3>
          </div>
          <button
            onClick={handleClose}
            className="p-1 rounded-md text-muted hover:bg-bg hover:text-ink transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {!token ? (
          /* ── Generation Form ── */
          <div className="space-y-4">
            <p className="text-sm text-muted">
              Generate a token for your Local Meeting Agent daemon.
              You&apos;ll use this to run{" "}
              <code className="font-mono text-xs bg-bg px-1.5 py-0.5 rounded">
                lma config set-token
              </code>
            </p>

            <div>
              <label className="block text-sm font-medium text-ink mb-1">
                Device name (optional)
              </label>
              <input
                type="text"
                value={deviceName}
                onChange={(e) => setDeviceName(e.target.value)}
                placeholder="e.g. MacBook Pro, Office Desktop"
                className="w-full rounded-md border border-border px-3 py-2 text-sm text-ink placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary"
                autoFocus
              />
            </div>

            {error && (
              <p className="text-sm text-danger">{error}</p>
            )}

            <button
              onClick={handleGenerate}
              disabled={loading}
              className="w-full rounded-md bg-primary py-2.5 text-sm font-medium text-white hover:bg-primary-dark transition-colors disabled:opacity-60"
            >
              {loading ? "Generating..." : "Generate Token"}
            </button>
          </div>
        ) : (
          /* ── Token Display ── */
          <div className="space-y-4">
            <div className="rounded-md border border-accent/30 bg-accent/5 px-3 py-2 text-xs text-ink">
              ⚠️ This token is shown <strong>only once</strong>. Copy it now
              and store it safely.
            </div>

            <div className="flex items-center gap-2">
              <code className="flex-1 font-mono text-xs bg-bg border border-border rounded-md px-3 py-2.5 break-all text-ink">
                {token}
              </code>
              <button
                onClick={handleCopy}
                className={`shrink-0 p-2.5 rounded-md border transition-colors ${
                  copied
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted hover:bg-bg hover:text-ink"
                }`}
                title={copied ? "Copied!" : "Copy to clipboard"}
              >
                {copied ? <Check size={16} /> : <Copy size={16} />}
              </button>
            </div>

            <div className="rounded-md bg-bg px-3 py-2.5">
              <p className="text-xs text-muted mb-1.5">Then run in your terminal:</p>
              <code className="font-mono text-xs text-ink">
                lma config set-token {token.slice(0, 12)}...
              </code>
            </div>

            <button
              onClick={handleClose}
              className="w-full rounded-md border border-border py-2.5 text-sm font-medium text-ink hover:bg-bg transition-colors"
            >
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );

  // Portal renders this directly into <body>, bypassing the sidebar's stacking context
  return createPortal(modal, document.body);
}