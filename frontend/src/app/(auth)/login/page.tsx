/**
 * Login Page - Apple design language.
 */

"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

export default function LoginPage() {
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed. Please try again.");
    }
  };

  return (
    <div className="w-full">
      <div className="mb-8">
        <h1 className="text-apple-display-md text-apple-ink mb-2">
          Sign in to MemoryOS
        </h1>
        <p className="text-apple-body text-apple-ink-48">
          Welcome back. Enter your credentials to continue.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-apple-sm text-red-600 text-apple-caption animate-slide-down">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-apple-caption-strong text-apple-ink mb-2">
            Email
          </label>
          <input
            type="email"
            name="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="apple-search-input"
            placeholder="you@example.com"
            disabled={isLoading}
          />
        </div>

        <div>
          <label className="block text-apple-caption-strong text-apple-ink mb-2">
            Password
          </label>
          <input
            type="password"
            name="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="apple-search-input"
            placeholder="Enter your password"
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="apple-btn-primary w-full mt-2 disabled:opacity-50"
        >
          {isLoading ? "Signing in…" : "Sign In"}
        </button>
      </form>

      <div className="mt-8 pt-6 border-t border-apple-hairline">
        <p className="text-apple-caption text-apple-ink-48 text-center">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="apple-link">
            Create one for free
          </Link>
        </p>
      </div>
    </div>
  );
}
