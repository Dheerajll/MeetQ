"use client";
import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useMeetingStore } from "@/lib/meetingStore"; // Import the global store
import LMATokenModal from "@/components/settings/LMATokenModal";
import {
  Home,
  MessageSquare,
  FileText,
  LogOut,
  PanelLeftClose,
  PanelLeft,
  Menu,
  X,
  Users,
  Key,
  Activity, // Icon for the active meeting indicator
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Home", icon: Home },
  { href: "/query", label: "Ask about meetings", icon: MessageSquare },
  { href: "/meetings", label: "Summaries", icon: FileText },
];

function SidebarContent({ collapsed, onNavigate }) {
  const pathname = usePathname();
  const { logout } = useAuth();
  const [tokenModalOpen, setTokenModalOpen] = useState(false);
  
  // Get global meeting state
  const { isMeetingActive } = useMeetingStore();
  const meetingActive = isMeetingActive();

  const handleLogout = async () => {
    onNavigate?.();
    await logout();
  };

  return (
    <>
      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              onClick={onNavigate}
              title={collapsed ? label : undefined}
              className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted hover:bg-bg hover:text-ink"
              }`}
            >
              <Icon size={18} className="shrink-0" />
              {!collapsed && <span className="truncate">{label}</span>}
            </Link>
          );
        })}

        {/* Active Meeting Indicator */}
        {/* Shows a pulsing indicator if a meeting is running and user is NOT on home page */}
        {meetingActive && pathname !== "/" && (
          <div 
            className={`mt-6 mx-1 p-2 rounded-md bg-primary/10 border border-primary/20 flex items-center gap-2 ${
              collapsed ? 'justify-center' : ''
            }`}
            title={collapsed ? "Meeting in progress" : undefined}
          >
            <Activity size={16} className="text-primary animate-pulse shrink-0" />
            {!collapsed && (
              <span className="text-xs font-medium text-primary truncate">
                Meeting in progress...
              </span>
            )}
          </div>
        )}
      </nav>

      {/* Footer */}
      <div className="px-3 py-4 border-t border-border space-y-1">
        {/* LMA Token button */}
        <button
          type="button"
          onClick={() => setTokenModalOpen(true)}
          title={collapsed ? "Get LMA Token" : undefined}
          className="flex items-center gap-3 w-full rounded-md px-3 py-2 text-sm font-medium text-muted hover:bg-bg hover:text-ink transition-colors"
        >
          <Key size={18} className="shrink-0" />
          {!collapsed && <span>Get LMA Token</span>}
        </button>

        {/* Logout button */}
        <button
          type="button"
          onClick={handleLogout}
          title={collapsed ? "Log out" : undefined}
          className="flex items-center gap-3 w-full rounded-md px-3 py-2 text-sm font-medium text-muted hover:bg-bg hover:text-danger transition-colors"
        >
          <LogOut size={18} className="shrink-0" />
          {!collapsed && <span>Log out</span>}
        </button>
      </div>

      {/* Token Modal */}
      <LMATokenModal
        isOpen={tokenModalOpen}
        onClose={() => setTokenModalOpen(false)}
      />
    </>
  );
}

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Mobile top bar */}
      <div className="md:hidden flex items-center gap-2 h-14 px-4 border-b border-border bg-surface sticky top-0 z-30">
        <button
          onClick={() => setMobileOpen(true)}
          aria-label="Open menu"
          className="p-2 -ml-2 rounded-md text-ink hover:bg-bg"
        >
          <Menu size={20} />
        </button>
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-7 h-7 rounded-md bg-primary text-white">
            <Users size={14} />
          </div>
          <span className="font-display font-semibold text-ink">Meet Q</span>
        </div>
      </div>

      {/* Mobile overlay drawer */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-40 flex">
          <div
            className="absolute inset-0 bg-ink/40"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="relative flex flex-col w-64 h-full bg-surface border-r border-border">
            <div className="flex items-center justify-between h-14 px-4 border-b border-border">
              <span className="font-display font-semibold text-ink">Meet Q</span>
              <button
                onClick={() => setMobileOpen(false)}
                aria-label="Close menu"
                className="p-1.5 rounded-md text-muted hover:bg-bg hover:text-ink"
              >
                <X size={18} />
              </button>
            </div>
            <SidebarContent collapsed={false} onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      {/* Desktop sidebar */}
      <aside
        className={`hidden md:flex flex-col shrink-0 h-screen sticky top-0 border-r border-border bg-surface transition-[width] duration-200 ${
          collapsed ? "w-16" : "w-64"
        }`}
      >
        {/* Header with logo and collapse button */}
        <div className="flex items-center h-16 px-4 border-b border-border">
          {collapsed ? (
            // When collapsed: just show the collapse button centered
            <button
              onClick={() => setCollapsed((c) => !c)}
              aria-label="Expand sidebar"
              className="w-full flex items-center justify-center p-1.5 rounded-md text-muted hover:bg-bg hover:text-ink transition-colors"
            >
              <PanelLeft size={18} className="shrink-0" />
            </button>
          ) : (
            // When expanded: show logo on left, collapse button on right
            <>
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <div className="flex items-center justify-center w-8 h-8 rounded-md bg-primary text-white shrink-0">
                  <Users size={16} />
                </div>
                <span className="font-display font-semibold text-ink truncate">
                  Meet Q
                </span>
              </div>
              <button
                onClick={() => setCollapsed((c) => !c)}
                aria-label="Collapse sidebar"
                className="p-1.5 rounded-md text-muted hover:bg-bg hover:text-ink transition-colors"
              >
                <PanelLeftClose size={18} className="shrink-0" />
              </button>
            </>
          )}
        </div>
        <SidebarContent collapsed={collapsed} />
      </aside>
    </>
  );
}