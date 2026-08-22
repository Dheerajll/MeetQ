// src/app/(auth)/layout.jsx
import BrandPanel from "@/components/auth/BrandPanel";
import GuestRoute from "@/components/auth/GuestRoute";

export default function AuthLayout({ children }) {
  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-bg">
      <BrandPanel />
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <GuestRoute>{children}</GuestRoute>
        </div>
      </div>
    </div>
  );
}