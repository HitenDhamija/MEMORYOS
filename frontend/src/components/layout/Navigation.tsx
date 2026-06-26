"use client";

import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { useState } from "react";
import { Brain, Menu, X } from "lucide-react";

export default function Navigation() {
  const { logout, user, isLoading } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="apple-global-nav">
      <div className="max-w-[1440px] w-full mx-auto px-6 flex justify-between items-center">
        <div className="flex items-center gap-8">
          <Link href="/dashboard" className="flex items-center gap-2.5 group">
            <Brain className="w-6 h-6 text-apple-body-dark" />
            <span className="text-[16px] font-semibold text-apple-body-dark tracking-tight">
              MemoryOS
            </span>
          </Link>
          <div className="hidden md:flex items-center gap-7">
            <Link
              href="/dashboard"
              className="text-[14px] text-apple-body-dark/80 hover:text-apple-body-dark transition-colors duration-200"
            >
              Dashboard
            </Link>
            <Link
              href="/memories"
              className="text-[14px] text-apple-body-dark/80 hover:text-apple-body-dark transition-colors duration-200"
            >
              Memories
            </Link>
            <Link
              href="/collections"
              className="text-[14px] text-apple-body-dark/80 hover:text-apple-body-dark transition-colors duration-200"
            >
              Collections
            </Link>
            <Link
              href="/ask"
              className="text-[14px] text-apple-body-dark/80 hover:text-apple-body-dark transition-colors duration-200"
            >
              Ask
            </Link>
            <Link
              href="/profile"
              className="text-[14px] text-apple-body-dark/80 hover:text-apple-body-dark transition-colors duration-200"
            >
              Profile
            </Link>
          </div>
        </div>
        <div className="hidden md:flex items-center gap-3">
          <div className="text-apple-body-dark/70 text-[13px]">
            {user?.full_name || user?.email}
          </div>
          <button
            onClick={logout}
            disabled={isLoading}
            className="apple-btn-dark text-[13px] disabled:opacity-50"
          >
            Logout
          </button>
        </div>
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="md:hidden text-apple-body-dark p-2"
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {mobileOpen && (
        <div className="md:hidden bg-apple-black border-t border-white/10 animate-slide-down">
          <div className="px-6 py-4 space-y-3">
            <Link href="/dashboard" onClick={() => setMobileOpen(false)} className="block text-apple-body-dark/80 hover:text-apple-body-dark py-2 transition-colors">
              Dashboard
            </Link>
            <Link href="/memories" onClick={() => setMobileOpen(false)} className="block text-apple-body-dark/80 hover:text-apple-body-dark py-2 transition-colors">
              Memories
            </Link>
            <Link href="/collections" onClick={() => setMobileOpen(false)} className="block text-apple-body-dark/80 hover:text-apple-body-dark py-2 transition-colors">
              Collections
            </Link>
            <Link href="/ask" onClick={() => setMobileOpen(false)} className="block text-apple-body-dark/80 hover:text-apple-body-dark py-2 transition-colors">
              Ask
            </Link>
            <Link href="/profile" onClick={() => setMobileOpen(false)} className="block text-apple-body-dark/80 hover:text-apple-body-dark py-2 transition-colors">
              Profile
            </Link>
            <button
              onClick={() => { logout(); setMobileOpen(false); }}
              disabled={isLoading}
              className="block text-red-400 hover:text-red-300 py-2 transition-colors disabled:opacity-50"
            >
              Logout
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
