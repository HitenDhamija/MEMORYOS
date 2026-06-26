/**
 * Dashboard layout with Apple-style navigation.
 */

"use client";

import React from "react";
import Navigation from "@/components/layout/Navigation";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-apple-parchment">
      <Navigation />
      <main className="max-w-[980px] mx-auto py-apple-section px-6">{children}</main>
    </div>
  );
}
