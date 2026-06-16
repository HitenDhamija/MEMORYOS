"use client";

import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

export default function Navigation() {
  const { logout, user, isLoading } = useAuth();

  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <div className="flex items-center gap-8">
          <Link href="/dashboard" className="text-2xl font-bold text-blue-600">
            MemoryOS
          </Link>
          <div className="hidden md:flex gap-6">
            <Link href="/dashboard" className="text-gray-600 hover:text-gray-900 transition">
              Dashboard
            </Link>
            <Link href="/memories" className="text-gray-600 hover:text-gray-900 transition">
              Memory Library
            </Link>
            <Link href="/profile" className="text-gray-600 hover:text-gray-900 transition">
              Profile
            </Link>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-gray-600">
            {user?.full_name || user?.email}
          </div>
          <button
            onClick={logout}
            disabled={isLoading}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 transition"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
