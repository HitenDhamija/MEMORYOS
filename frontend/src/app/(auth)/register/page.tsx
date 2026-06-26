/**
 * Register Page - Apple design language.
 */

"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

export default function RegisterPage() {
  const { register, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    try {
      await register(email, username, password, fullName);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed. Please try again.");
    }
  };

  return (
    <div className="w-full">
      <div className="mb-8">
        <h1 className="text-apple-display-md text-apple-ink mb-2">
          Create your account
        </h1>
        <p className="text-apple-body text-apple-ink-48">
          Start your AI-powered learning journey.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-apple-sm text-red-600 text-apple-caption animate-slide-down">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
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
            Username
          </label>
          <input
            type="text"
            name="username"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            minLength={3}
            className="apple-search-input"
            placeholder="johndoe"
            disabled={isLoading}
          />
        </div>

        <div>
          <label className="block text-apple-caption-strong text-apple-ink mb-2">
            Full Name <span className="text-apple-ink-48 font-normal">(optional)</span>
          </label>
          <input
            type="text"
            name="fullName"
            autoComplete="name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="apple-search-input"
            placeholder="John Doe"
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
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            className="apple-search-input"
            placeholder="Min. 8 characters"
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="apple-btn-primary w-full mt-2 disabled:opacity-50"
        >
          {isLoading ? "Creating account…" : "Create Account"}
        </button>
      </form>

      <div className="mt-6 pt-6 border-t border-apple-hairline">
        <p className="text-apple-caption text-apple-ink-48 text-center">
          Already have an account?{" "}
          <Link href="/login" className="apple-link">
            Sign in
          </Link>
        </p>
      </div>

      <p className="mt-6 text-apple-fine-print text-apple-ink-48 text-center">
        Free to start · No credit card · 100GB storage included
      </p>
    </div>
  );
}
