"""
Dashboard layout with navigation.
"""

"use client";

import React from "react";
import Navigation from "@/components/layout/Navigation";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="max-w-7xl mx-auto py-8 px-4">{children}</main>
    </div>
  );
}
