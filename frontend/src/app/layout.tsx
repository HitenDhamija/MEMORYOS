/**
 * Root layout with Inter font and modern meta tags.
 */

import type { Metadata, Viewport } from "next";
import "./globals.css";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { SettingsProvider } from "@/context/SettingsContext";

export const metadata: Metadata = {
  title: "MemoryOS - AI-Powered Knowledge Operating System",
  description: "Your personal AI-powered knowledge operating system. Upload, organize, and discover knowledge with semantic search and intelligent insights.",
  keywords: ["knowledge management", "AI", "semantic search", "memory", "learning", "productivity"],
  authors: [{ name: "MemoryOS" }],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#030712" },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="bg-background text-foreground antialiased selection:bg-blue-500/20 selection:text-blue-900 dark:selection:text-blue-100">
        <SettingsProvider>
          <AuthProvider>{children}</AuthProvider>
        </SettingsProvider>
      </body>
    </html>
  );
}
