// src/app/(dashboard)/layout.jsx

import Sidebar from "@/components/layout/Sidebar";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
export default function DashboardGroupLayout({ children }) {
  return (
    <ProtectedRoute>
      <div className="min-h-screen flex bg-bg">
        <Sidebar />
        <div className="flex-1 min-w-0 flex flex-col">{children}</div>
      </div>
    </ProtectedRoute>
  );
}